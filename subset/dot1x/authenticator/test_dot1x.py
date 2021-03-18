from __future__ import absolute_import
import sys


def main():
    write_file = sys.argv[1]
    # TODO: Link with authentucation module once ready.
    # Currently simply writes an empty result into the file.
    result = 'Authentication for <mac> successful.'
    with open(write_file,  'w') as w_file:
        w_file.write(result)


if __name__ == '__main__':
    main()
