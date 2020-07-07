"""Class for working with GCP connections (e.g. Pub/Sub messages)"""

import datetime
import json
import os
import sys

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import pubsub_v1
from google.cloud import storage
from google.cloud import logging
from google.auth import _default as google_auth
from grpc import StatusCode

import logger
import configurator

LOGGER = logger.get_logger('gcp')
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
DEFAULT_LIMIT = 100
# pylint: disable=no-member
DESCENDING = firestore.Query.DESCENDING

def get_timestamp():
    """"Get a JSON-compatible formatted timestamp"""
    return to_timestamp(datetime.datetime.now(datetime.timezone.utc))


def to_timestamp(timestamp):
    """"Get a JSON-compatible formatted timestamp"""
    return timestamp.strftime(TIMESTAMP_FORMAT)[:-3] + 'Z'


def parse_timestamp(timestamp_str):
    """Parses a timestamp generated from get_timestamp"""
    return datetime.datetime.strptime(timestamp_str, TIMESTAMP_FORMAT + 'Z')


class GcpManager:
    """Manager class for working with GCP"""

    REPORT_BUCKET_FORMAT = '%s.appspot.com'

    def __init__(self, config, callback_handler):
        self.config = config
        self._callback_handler = callback_handler
        cred_file = self.config.get('gcp_cred')
        if not cred_file:
            LOGGER.info('No gcp_cred filr specified in config, disabling gcp use.')
            self._pubber = None
            self._storage = None
            self._firestore = None
            self._client_name = None
            return
        LOGGER.info('Loading gcp credentials from %s', cred_file)
        # Normal execution assumes default credentials.
        (self._credentials, self._project) = google_auth.load_credentials_from_file(cred_file)
        self._client_name = self._parse_creds(cred_file)
        self._site_name = self._get_site_name()
        self._pubber = pubsub_v1.PublisherClient(credentials=self._credentials)
        LOGGER.info('Initialized gcp pub/sub %s:%s:%s', self._project,
                    self._client_name, self._site_name)
        self._firestore = self._initialize_firestore(cred_file)
        self._report_bucket_name = self.REPORT_BUCKET_FORMAT % self._project
        self._storage = storage.Client(project=self._project, credentials=self._credentials)
        self._bucket = self._ensure_report_bucket()
        self._config_callbacks = {}
        self._logging = logging.Client(credentials=self._credentials, project=self._project)

        LOGGER.info('Connection initialized at %s', get_timestamp())

    def get_logging_client(self):
        """Gets the stackdriver client"""
        return (self._client_name, self._logging) if self._client_name else None

    def _initialize_firestore(self, cred_file):
        cred = credentials.Certificate(cred_file)
        firebase_admin.initialize_app(cred)
        LOGGER.info('Initialized gcp firestore %s:%s', self._project, self._client_name)
        dashboard_url = 'https://%s.firebaseapp.com/?origin=%s' % (self._project, self._client_name)
        LOGGER.info('Dashboard at %s', dashboard_url)
        return firestore.client()

    def _on_snapshot(self, callback, doc_snapshot, immediate):
        def handler():
            for doc in doc_snapshot:
                doc_data = doc.to_dict()
                timestamp = doc_data['timestamp']
                if immediate or doc_data['saved'] != timestamp:
                    callback(doc_data['config'])
                    doc.reference.update({
                        'saved': timestamp
                    })
        self._callback_handler(handler)

    def register_config(self, path, config, callback=None, immediate=False):
        """Register a config blob with callback"""
        if not self._firestore:
            return

        assert path, 'empty config path'
        full_path = 'origin/%s/%s/config/definition' % (self._client_name, path)

        if full_path in self._config_callbacks:
            LOGGER.info('Unsubscribe callback %s', path)
            self._config_callbacks[full_path]['future'].unsubscribe()
            del self._config_callbacks[full_path]

        config_doc = self._firestore.document(full_path)
        if config is not None:
            timestamp = get_timestamp()
            LOGGER.info('Registering %s', full_path)
            config_doc.set({
                'config': config,
                'saved': timestamp,
                'timestamp': timestamp
            })
        else:
            LOGGER.info('Releasing %s', full_path)
            config_doc.delete()

        if callback:
            assert config is not None, 'callback defined when deleting config??!?!'
            on_snapshot = lambda doc_snapshot, changed, read_time:\
                          self._on_snapshot(callback, doc_snapshot, immediate)
            self._register_callback(config_doc, full_path, on_snapshot)

    def _register_callback(self, config_doc, full_path, on_snapshot):
        snapshot_future = config_doc.on_snapshot(on_snapshot)
        self._config_callbacks[full_path] = {
            'future': snapshot_future,
            'config_doc': config_doc,
            'on_snapshot': on_snapshot
        }
        self._apply_callback_hack(full_path, snapshot_future)

    def _wrap_callback(self, callbacks, reason):
        for callback in callbacks:
            try:
                callback(reason)
            except Exception as e:
                LOGGER.error('Capturing RPC error: %s', str(e))

    def _hack_recv(self, rpc, path):
        # pylint: disable=protected-access
        try:
            return rpc._recoverable(rpc._recv) # Erp.
        except Exception as e:
            LOGGER.error('Error intercepted at %s, %s for %s', get_timestamp(),
                         rpc.call._state.code, path)
            if rpc.call._state.code == StatusCode.INTERNAL:
                self._restart_callback(path)
            raise e

    def _restart_callback(self, path):
        LOGGER.warning('Restarting callback %s', path)
        callback = self._config_callbacks[path]
        self._register_callback(callback['config_doc'], path, callback['on_snapshot'])

    def _apply_callback_hack(self, path, snapshot_future):
        # pylint: disable=protected-access
        rpc = snapshot_future._rpc
        rpc.recv = lambda: self._hack_recv(rpc, path)
        callbacks = rpc._callbacks
        LOGGER.info('Patching recv callback for %s with %s', path, len(callbacks))
        wrapped_handler = lambda reason: self._wrap_callback(callbacks, reason)
        rpc._callbacks = [wrapped_handler]

    def release_config(self, path):
        """Release a config blob and remove it from the live data system"""
        self.register_config(path, None)

    def _get_site_name(self):
        site_path = self.config['site_path']
        cloud_config = os.path.join(site_path, 'cloud_iot_config.json')
        if not os.path.isfile(cloud_config):
            LOGGER.warning('Site cloud config file %s not found, using %s instead',
                           cloud_config, self._client_name)
            return self._client_name
        with open(cloud_config) as config_file:
            return json.load(config_file)['site_name']

    def _parse_creds(self, cred_file):
        """Parse JSON credential file"""
        with open(cred_file) as data_file:
            cred = json.load(data_file)
        project = cred['project_id']
        assert project == self._project, 'inconsistent credential projects'
        client_email = cred['client_email']
        (client, dummy_other) = client_email.split('@', 2)
        return client

    def publish_message(self, topic, message_type, message):
        """Publish a message to pub/sub topic"""
        if not self._pubber:
            LOGGER.debug('Ignoring message publish: not configured')
            return
        envelope = {
            'type': message_type,
            'timestamp': get_timestamp(),
            'payload': message
        }
        message_str = json.dumps(envelope)
        LOGGER.debug('Sending to topic_path %s/%s: %s', self._project, topic, message_str)
        # pylint: disable=no-member
        topic_path = self._pubber.topic_path(self._project, topic)
        future = self._pubber.publish(topic_path, message_str.encode('utf-8'),
                                      projectId=self._project, origin=self._client_name,
                                      site_name=self._site_name)
        LOGGER.debug('Publish future result %s', future.result())

    def _ensure_report_bucket(self):
        bucket_name = self._report_bucket_name
        if self._storage.lookup_bucket(bucket_name):
            LOGGER.info('Storage bucket %s already exists', bucket_name)
        else:
            LOGGER.info('Creating storage bucket %s', bucket_name)
            self._storage.create_bucket(bucket_name)
        return self._storage.get_bucket(bucket_name)

    def upload_file(self, file_name, destination_file_name=None):
        """Uploads a report to a storage bucket."""
        if not self._storage:
            LOGGER.debug('Ignoring %s upload: not configured' % file_name)
            return None
        destination_file_name = os.path.join('origin', self._client_name or "other",
                                             destination_file_name or file_name)
        blob = self._bucket.blob(destination_file_name)
        blob.upload_from_filename(file_name)
        LOGGER.info('Uploaded %s' % destination_file_name)
        return destination_file_name

    def register_offenders(self):
        """Register any offenders: people who are not enabled to use the system"""
        if not self._firestore:
            LOGGER.error('Firestore not initialized.')
            return
        LOGGER.info('Registering offenders...')
        users = self._firestore.collection(u'users').stream()
        for user in users:
            permissions = self._firestore.collection(u'permissions').document(user.id).get()
            user_email = user.to_dict().get('email')
            enabled = permissions.to_dict() and permissions.to_dict().get('enabled')
            if enabled:
                LOGGER.info('Access already enabled for %s', user_email)
            elif self._query_user('Enable access for %s? (N/y) ' % user_email):
                LOGGER.info('Enabling access for %s', user_email)
                self._firestore.collection(u'permissions').document(user.id).set({
                    'enabled': True
                })
            else:
                LOGGER.info('Ignoring user %s', user_email)

    def _get_json_report(self, runid):
        doc = runid.reference.collection('test').document('terminate').get().to_dict()
        report_blob = doc.get('report_path.json') if doc else None
        if not report_blob:
            return None
        LOGGER.info('Downloading report %s', report_blob)
        blob = self._bucket.blob(report_blob)
        return json.loads(str(blob.download_as_string(), 'utf-8'))

    def get_reports_from_date_range(self, device: str, start=None, end=None, count=None):
        """Combine test results from reports within a date range"""
        if not self._firestore:
            LOGGER.error('Firestore not initialized.')
            return
        LOGGER.info('Looking for reports...')
        limit_count = count if count else DEFAULT_LIMIT
        origin = self._firestore.collection(u'origin').document(self._client_name).get()
        query = origin.reference.collection('runid').where('deviceId', '==', device)
        if start:
            query = query.where('updated', '>=', to_timestamp(start))
        if end:
            query = query.where('updated', '<=', to_timestamp(end))
        runids = query.order_by(u'updated', direction=DESCENDING).limit(limit_count).stream()
        for runid in runids:
            json_report = self._get_json_report(runid)
            if json_report:
                yield json_report

    def _query_user(self, message):
        reply = input(message)
        options = set(('y', 'Y', 'yes', 'YES', 'Yes', 'sure'))
        if reply in options:
            return True
        return False


if __name__ == '__main__':
    logger.set_config(format='%(levelname)s:%(message)s', level="INFO")
    CONFIGURATOR = configurator.Configurator()
    CONFIG = CONFIGURATOR.parse_args(sys.argv)
    GCP = GcpManager(CONFIG, None)
    if CONFIG.get('register_offenders'):
        GCP.register_offenders()
    else:
        print('Unknown command mode for gcp module.')
