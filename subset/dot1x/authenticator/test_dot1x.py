from __future__ import absolute_import
from authenticator import Authenticator
import sys
from utils import get_logger


def main():
    LOGGER = get_logger('test_dot1x')
    write_file = sys.argv[1]
    # TODO: Link with authentucation module once ready.
    # Currently simply writes an empty result into the file.
    LOGGER.info('Initialising authenticator')
    authenticator = Authenticator('/root/dot1x_config.yaml')
    LOGGER.info('Running auth test')
    result = authenticator.run_authentication_test()
    with open(write_file,  'w') as w_file:
        w_file.write(result)


if __name__ == '__main__':
    main()
