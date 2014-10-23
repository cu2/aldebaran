#!/usr/bin/env python

import importlib
import sys


def main(args):
    if len(args) < 1:
        print 'Usage: ./run_device.py <device_name> [<args_for_device>]'
        return 1
    device_name = args[0]
    device_args = args[1:]
    try:
        device = importlib.import_module('devices.%s' % device_name)
    except ImportError:
        print 'ERROR: could not import %s' % device_name
        return 1
    return device.main(device_args)


if __name__ == '__main__':
    main(sys.argv[1:])
