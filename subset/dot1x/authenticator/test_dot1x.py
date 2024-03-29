from __future__ import absolute_import
from authenticator import Authenticator
import sys
from utils import get_logger


def main():

    TEST_NAME = "connection.dot1x.authentication"

    LOGGER = get_logger('test_dot1x')
    arg_length = len(sys.argv)
    if arg_length > 1:
        write_file = sys.argv[1]
    else:
        write_file = '/tmp/dot1x_result.txt'
    if arg_length > 2:
        config_file = sys.argv[2]
    else:
        config_file = '/config/device/module_config.json'

    # TODO: Link with authentucation module once ready.
    # Currently simply writes an empty result into the file.
    LOGGER.info('Initialising authenticator')
    authenticator = Authenticator(config_file)
    LOGGER.info('Running auth test')
    result_summary, test_result = authenticator.run_authentication_test()
    result_line = "RESULT %s %s %s" % (test_result, TEST_NAME, result_summary)
    with open(write_file,  'w') as w_file:
        w_file.write(result_line)


if __name__ == '__main__':
    main()
