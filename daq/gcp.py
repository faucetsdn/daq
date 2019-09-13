"""Class for working with GCP connections (e.g. Pub/Sub messages)"""

import datetime
import json
import logging
import sys

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import pubsub_v1
from google.cloud import storage
from google.auth import _default as google_auth
from grpc import StatusCode

import configurator

LOGGER = logging.getLogger('gcp')


def get_timestamp():
    """"Get a JSON-compatible formatted timestamp"""
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


class GcpManager:
    """Manager class for working with GCP"""

    REPORT_BUCKET_FORMAT = '%s.appspot.com'

    def __init__(self, config, callback_handler):
        self.config = config
        self._callback_handler = callback_handler
        if 'gcp_cred' not in config:
            LOGGER.info('No gcp_cred credential specified in config')
            self._pubber = None
            self._storage = None
            self._firestore = None
            return
        cred_file = self.config['gcp_cred']
        LOGGER.info('Loading gcp credentials from %s', cred_file)
        # Normal execution assumes default credentials.
        # pylint: disable=protected-access
        (self._credentials, self._project) = google_auth._load_credentials_from_file(cred_file)
        self._client_name = self._parse_creds(cred_file)
        self._pubber = pubsub_v1.PublisherClient(credentials=self._credentials)
        LOGGER.info('Initialized gcp pub/sub %s:%s', self._project, self._client_name)
        # TODO: Reinstate Firestore once it doesn't break Travis anymore.
        # self._firestore = self._initialize_firestore(cred_file)
        self._firestore = None
        self._storage = storage.Client(project=self._project, credentials=self._credentials)
        self._report_bucket_name = self.REPORT_BUCKET_FORMAT % self._project
        self._ensure_report_bucket()
        self._config_callbacks = {}
        LOGGER.info('Connection initialized at %s', get_timestamp())

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
                                      projectId=self._project, origin=self._client_name)
        LOGGER.debug('Publish future result %s', future.result())

    def _ensure_report_bucket(self):
        bucket_name = self._report_bucket_name
        if self._storage.lookup_bucket(bucket_name):
            LOGGER.info('Storage bucket %s already exists', bucket_name)
        else:
            LOGGER.info('Creating storage bucket %s', bucket_name)
            self._storage.create_bucket(bucket_name)

    def upload_report(self, report_file_name):
        """Uploads a report to a storage bucket."""
        if not self._storage:
            LOGGER.info('Ignoring report upload: not configured')
            return
        bucket = self._storage.get_bucket(self._report_bucket_name)
        blob = bucket.blob(report_file_name)
        blob.upload_from_filename(report_file_name)
        LOGGER.info('Uploaded test report to %s', report_file_name)

    def register_offenders(self):
        """Register any offenders: people who are not enabled to use the system"""
        if not self._firestore:
            LOGGER.error('Firestore not initialized.')
            return
        LOGGER.info('Registering offenders...')
        users = self._firestore.collection(u'users').get()
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

    def _query_user(self, message):
        reply = input(message)
        options = ['y', 'Y', 'yes', 'YES', 'Yes', 'sure']
        if reply in options:
            return True
        return False


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    CONFIGURATOR = configurator.Configurator()
    CONFIG = CONFIGURATOR.parse_args(sys.argv)
    GCP = GcpManager(CONFIG, None)
    if CONFIG.get('register_offenders'):
        GCP.register_offenders()
    else:
        print('Unknown command mode for gcp module.')
