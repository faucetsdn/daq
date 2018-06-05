"""Class for working with GCP connections (e.g. Pub/Sub messages)"""

import json
import logging

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import pubsub_v1
from google.auth._default import _load_credentials_from_file

LOGGER = logging.getLogger('gcp')

class GcpManager(object):
    """Manager class for working with GCP"""

    config = None
    project = None
    client_name = None
    pubber = None
    firestore = None
    credentials = None
    cred_file = None

    def __init__(self, config):
        self.config = config
        if 'gcp_cred' not in config:
            LOGGER.info('No gcp_cred credential specified in config')
            return
        self.cred_file = self.config['gcp_cred']
        LOGGER.info('Loading gcp credentials from %s', self.cred_file)
        (self.credentials, self.project) = _load_credentials_from_file(self.cred_file)
        self.client_name = self._parse_creds()
        self._initialize_pubsub()
        self._initialize_firestore()

    def _initialize_pubsub(self):
        self.pubber = pubsub_v1.PublisherClient(credentials=self.credentials)
        LOGGER.info('Initialized gcp pub/sub %s:%s', self.project, self.client_name)

    def _initialize_firestore(self):
        cred = firebase_admin.credentials.Certificate(self.cred_file)
        firebase_admin.initialize_app(cred)
        self.firestore = firestore.client()
        LOGGER.info('Initialized gcp firestore %s:%s', self.project, self.client_name)

    def _message_callback(self, topic, message, callback):
        LOGGER.info('Received topic %s message: %s', topic, message)
        callback(message)
        message.ack()

    def _parse_creds(self):
        """Parse JSON credential file"""
        with open(self.cred_file) as data_file:
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
