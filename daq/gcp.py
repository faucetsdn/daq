"""Class for working with GCP connections (e.g. Pub/Sub messages)"""

import json
import logging

from google.cloud import pubsub_v1
from google.auth._default import _load_credentials_from_file

LOGGER = logging.getLogger('gcp')

class GcpManager(object):
    """Manager class for working with GCP"""

    config = None
    publisher = None
    project = None
    client = None

    def __init__(self, config):
        self.config = config
        if 'gcp_cred' not in config:
            LOGGER.info('No gcp_cred credential specified in config')
            return
        cred_file = self.config['gcp_cred']
        LOGGER.info('Loading gcp credentials from %s', cred_file)
        (credentials, self.project) = _load_credentials_from_file(cred_file)
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.client_name = self.parse_creds(cred_file)
        LOGGER.info('Initialized gcp publisher client %s:%s', self.project, self.client_name)

    def parse_creds(self, cred_file):
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
        if not self.publisher:
            LOGGER.debug('Ignoring message publish: not configured')
            return
        if 'encode' not in message:
            message = json.dumps(message)
        LOGGER.debug('Sending to topic_path %s/%s: %s', self.project, topic, message)
        topic_path = self.publisher.topic_path(self.project, topic)
        future = self.publisher.publish(topic_path, message.encode('utf-8'),
                                        origin=self.client_name)
        LOGGER.debug('Publish future result %s', future.result())
