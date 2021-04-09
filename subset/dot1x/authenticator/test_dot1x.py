from __future__ import absolute_import
from authenticator import Authenticator
import sys
from utils import get_logger


def main():

    TEST_NAME = "dot1x.dot1x"

    LOGGER = get_logger('test_dot1x')
    write_file = sys.argv[1]
    # TODO: Link with authentucation module once ready.
    # Currently simply writes an empty result into the file.
    LOGGER.info('Initialising authenticator')
    authenticator = Authenticator('/config/device/module_config.json')
    LOGGER.info('Running auth test')
    result_summary, test_result = authenticator.run_authentication_test()
    result_line = "RESULT %s %s %s" % (test_result, TEST_NAME, result_summary)
    with open(write_file,  'w') as w_file:
        w_file.write(result_line)


if __name__ == '__main__':
    main()
