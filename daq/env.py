"""DAQ installion environment"""

from __future__ import absolute_import
import os


def _os_getenv(key):
    var = os.getenv(key)
    assert var, '%s not defined in environment' % key
    return var


DAQ_LIB_DIR = _os_getenv('DAQ_LIB')
DAQ_CONF_DIR = _os_getenv('DAQ_CONF')
DAQ_RUN_DIR = _os_getenv('DAQ_RUN')
