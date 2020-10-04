"""Gateway module for device testing"""
from __future__ import absolute_import

import logger
from container_gateway import ContainerGateway

LOGGER = logger.get_logger('external_gateway')


class ExternalGateway(ContainerGateway):
    """Gateway collection class for managing testing services"""
    # TODO
