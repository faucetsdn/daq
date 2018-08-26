"""Class for working with GCP connections (e.g. Pub/Sub messages)"""

import json
import logging

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import pubsub_v1
from google.auth import _default as google_auth

LOGGER = logging.getLogger('gcp')

class GcpManager():
    """Manager class for working with GCP"""

    def __init__(self, config):
        self.config = config
        if 'gcp_cred' not in config:
            LOGGER.info('No gcp_cred credential specified in config')
            self.pubber = None
            return
        cred_file = self.config['gcp_cred']
        LOGGER.info('Loading gcp credentials from %s', cred_file)
        # Normal execution assumes default credentials. pylint: disable=protected-access
        (self.credentials, self.project) = google_auth._load_credentials_from_file(cred_file)
        self.client_name = self._parse_creds(cred_file)
        self.pubber = pubsub_v1.PublisherClient(credentials=self.credentials)
        LOGGER.info('Initialized gcp pub/sub %s:%s', self.project, self.client_name)
        self.firestore = self._initialize_firestore(cred_file)

    def _initialize_firestore(self, cred_file):
        cred = credentials.Certificate(cred_file)
        firebase_admin.initialize_app(cred)
        LOGGER.info('Initialized gcp firestore %s:%s', self.project, self.client_name)
        return firestore.client()

    def _message_callback(self, topic, message, callback):
        LOGGER.info('Received topic %s message: %s', topic, message)
        callback(message)
        message.ack()

    def _parse_creds(self, cred_file):
        """Parse JSON credential file"""
        with open(cred_file) as data_file:
            cred = json.load(data_file)
        project = cred['project_id']
        assert project == self.project, 'inconsistent credential projects'
        client_email = cred['client_email']
        (client, dummy_other) = client_email.split('@', 2)
        return client

    def publish_message(self, topic, message):
        """Publish a message to pub/sub topic"""
        if not self.pubber:
            LOGGER.debug('Ignoring message publish: not configured')
            return
        if 'encode' not in message:
            message = json.dumps(message)
        LOGGER.debug('Sending to topic_path %s/%s: %s', self.project, topic, message)
        #pylint: disable=no-member
        topic_path = self.pubber.topic_path(self.project, topic)
        future = self.pubber.publish(topic_path, message.encode('utf-8'),
                                     origin=self.client_name)
        LOGGER.debug('Publish future result %s', future.result())
