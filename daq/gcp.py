"""Class for working with GCP connections (e.g. Pub/Sub messages)"""

import json
import logging

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import pubsub_v1
from google.cloud import storage
from google.auth import _default as google_auth

LOGGER = logging.getLogger('gcp')


class GcpManager:
    """Manager class for working with GCP"""

    REPORT_BUCKET_FORMAT = '%s.appspot.com'

    def __init__(self, config):
        self.config = config
        if 'gcp_cred' not in config:
            LOGGER.info('No gcp_cred credential specified in config')
            self._pubber = None
            self._storage = None
            return
        cred_file = self.config['gcp_cred']
        LOGGER.info('Loading gcp credentials from %s', cred_file)
        # Normal execution assumes default credentials.
        # pylint: disable=protected-access
        (self._credentials, self._project) = google_auth._load_credentials_from_file(cred_file)
        self._client_name = self._parse_creds(cred_file)
        self._pubber = pubsub_v1.PublisherClient(credentials=self._credentials)
        LOGGER.info('Initialized gcp pub/sub %s:%s', self._project, self._client_name)
        self.firestore = self._initialize_firestore(cred_file)
        self._storage = storage.Client(project=self._project, credentials=self._credentials)
        self._report_bucket_name = self.REPORT_BUCKET_FORMAT % self._project
        self._ensure_report_bucket()

    def _initialize_firestore(self, cred_file):
        cred = credentials.Certificate(cred_file)
        firebase_admin.initialize_app(cred)
        LOGGER.info('Initialized gcp firestore %s:%s', self._project, self._client_name)
        dashboard_url = 'https://%s.firebaseapp.com/?origin=%s' % (self._project, self._client_name)
        LOGGER.info('Dashboard at %s', dashboard_url)
        return firestore.client()

    @staticmethod
    def _message_callback(topic, message, callback):
        LOGGER.info('Received topic %s message: %s', topic, message)
        callback(message)
        message.ack()

    def _parse_creds(self, cred_file):
        """Parse JSON credential file"""
        with open(cred_file) as data_file:
            cred = json.load(data_file)
        project = cred['project_id']
        assert project == self._project, 'inconsistent credential projects'
        client_email = cred['client_email']
        (client, dummy_other) = client_email.split('@', 2)
        return client

    def publish_message(self, topic, message):
        """Publish a message to pub/sub topic"""
        if not self._pubber:
            LOGGER.debug('Ignoring message publish: not configured')
            return
        if 'encode' not in message:
            message = json.dumps(message)
        LOGGER.debug('Sending to topic_path %s/%s: %s', self._project, topic, message)
        # pylint: disable=no-member
        topic_path = self._pubber.topic_path(self._project, topic)
        future = self._pubber.publish(topic_path, message.encode('utf-8'),
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
