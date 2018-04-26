import json
import logging

from google.cloud import pubsub_v1
from google.auth._default import _load_credentials_from_file

logger = logging.getLogger('gcp')

class GcpManager():

    config = None
    publisher = None
    project = None
    client = None

    def __init__(self, config):
        self.config = config
        if not 'gcp_cred' in config:
            logger.info('No gcp_cred credential specified in config')
            return
        cred_file = self.config['gcp_cred']
        logger.info('Loading gcp credentials from %s' % cred_file)
        (credentials, project) = _load_credentials_from_file(cred_file)
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        (self.project, self.client_name) = self.parse_creds(cred_file)
        logger.info('Initialized gcp publisher client %s:%s' % (self.project, self.client_name))

    def parse_creds(self, cred_file):
        with open(cred_file) as data_file:
            cred = json.load(data_file)
        project = cred['project_id']
        client_email = cred['client_email']
        (client, other) = client_email.split('@', 2)
        return (project, client)

    def publish_message(self, topic, message):
        if not self.publisher:
            logger.debug('Ignoring message publish: not configured')
            return
        if not 'encode' in message:
            message = json.dumps(message)
        logger.debug('Sending to topic_path %s/%s: %s' % (self.project, topic, message))
        topic_path = self.publisher.topic_path(self.project, topic)
        future = self.publisher.publish(topic_path, message.encode('utf-8'), origin=self.client_name)
        logger.debug('Publish future result %s' % future.result())
