"""Wrapper for remote and local logging"""

import logging

try:
    from google.cloud.logging.handlers import CloudLoggingHandler
except ImportError:
    pass

LOGGERS = {}

def set_stackdriver_client(client, labels=None):
    """Sets stackdriver client"""
    stackdriver_client_name, stackdriver_client = client
    stackdriver_handler = CloudLoggingHandler(stackdriver_client,
                                              name=stackdriver_client_name,
                                              labels=labels)
    for name, logger in LOGGERS.items():
        # filters out root logger
        if name:
            logger.addHandler(stackdriver_handler)
    set_stackdriver_client.stackdriver_handler = stackdriver_handler

def get_logger(name=None):
    """Gets the named logger"""
    if name not in LOGGERS:
        LOGGERS[name] = logging.getLogger(name)
        if name and set_stackdriver_client.stackdriver_handler:
            LOGGERS[name].addHandler(set_stackdriver_client.stackdriver_handler)
    return LOGGERS[name]

def set_config(*args, **kwargs):
    """Sets config for all loggers"""
    return logging.basicConfig(*args, **kwargs)

set_stackdriver_client.stackdriver_handler = None
