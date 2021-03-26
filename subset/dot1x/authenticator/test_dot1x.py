from __future__ import absolute_import
from authenticator import Authenticator
import sys


def main():
    write_file = sys.argv[1]
    # TODO: Link with authentucation module once ready.
    # Currently simply writes an empty result into the file.
    authenticator = Authenticator()
    result = authenticator.run_authentication_test()
    with open(write_file,  'w') as w_file:
        w_file.write(result)


if __name__ == '__main__':
    main()
