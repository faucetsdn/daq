#!/usr/bin/env python3

"""Configuraiton manager class for daqy-things."""

import re
import sys

FLAG_MAP = {
    'b': 'build_tests',
    'c': 'use_console',
    'd': 'debug_mode',
    'e': 'event_trigger',
    'f': 'fail_mode',
    'h': 'show_help',
    'k': 'keep_hold',
    'l': 'result_linger',
    'n': 'no_test',
    's': 'single_shot'
}

def show_help():
    """Show help information on the console output."""
    print("Common run options:")
    for option in FLAG_MAP:
        print("  -%s: %s" % (option, FLAG_MAP[option]))
    print("See misc/system.conf for a detailed accounting of potential options.")

def print_config(config):
    """Dump config info as key=value to console out."""
    config_list = []
    for key in sorted(config.keys()):
        value = config[key]
        quote = '"' if ' ' in str(value) else ''
        config_list.append("%s=%s%s%s" % (key, quote, config[key], quote))
    print(*config_list, sep='\n')

class Configurator():
    """Manager class for system configuration."""

    def __init__(self, verbose=False):
        self._verbose = verbose

    def _log(self, message):
        if self._verbose:
            print(message)

    def _read_config_into(self, filename, config):
        self._log('Reading config from %s' % filename)
        with open(filename) as file:
            line = file.readline()
            while line:
                parts = re.sub(r'#.*', '', line).strip().split('=')
                entry = parts[0].split() if parts else None
                if len(parts) == 2:
                    config[parts[0].strip()] = parts[1].strip().strip('"').strip("'")
                elif len(entry) == 2 and entry[0] == 'source':
                    self._read_config_into(entry[1], config)
                elif parts and parts[0]:
                    raise Exception('Unknown config entry: %s' % line)
                line = file.readline()

    def parse_args(self, args):
        """Parse command line arguments"""
        config = {}
        for arg in args[1:]:
            if arg:
                self._log('processing arg: %s' % arg)
                if arg[0] == '-':
                    if arg[1:] in FLAG_MAP:
                        config[FLAG_MAP[arg[1:]]] = True
                    else:
                        raise Exception('Unknown command line arg %s' % arg)
                elif '=' in arg:
                    parts = arg.split('=', 1)
                    config[parts[0]] = parts[1]
                else:
                    self._read_config_into(arg, config)
        return config

if __name__ == '__main__':
    CONFIG = Configurator()
    print_config(CONFIG.parse_args(sys.argv))
