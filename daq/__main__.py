""" Entry point for DAQ"""

import argparse
import os
import sys

from daq.daq import _execute
from daq.__version__ import __version__


def parse_args(raw_args):
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog='daq', description='Device Automated Qualification for IoT Devices')
    parser.add_argument('-V', '--version', action='store_true', help='print version and exit')
    parsed = parser.parse_args(raw_args)
    return parsed


def main():
    """Main program"""
    args = parse_args(sys.argv[1:])

    if args.version:
        print(f'DAQ {__version__}')
        sys.exit()

    assert os.getuid() == 0, 'Must run DAQ as root.'
    sys.exit(_execute())


if __name__ == '__main__':
    main()
