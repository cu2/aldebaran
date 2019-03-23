#!/usr/bin/env python

import importlib
import sys


def main(args):
    if len(args) < 2:
        print('Usage: ./run_device.py <device_name> <ioport_number> [<optional_arguments_for_device>]')
        return 1
    device_name = args[0]
    ioport_number = int(args[1])
    device_args = args[2:]
    try:
        device_module = importlib.import_module('devices.%s' % device_name)
    except ImportError:
        print('ERROR: could not import %s' % device_name)
        return 1
    print()
    device = getattr(device_module, device_module.DEVICE_CLASS)(
        ioport_number=ioport_number,
        device_descriptor=(device_module.DEVICE_TYPE, device_module.DEVICE_ID),
    )
    retval = device.start()
    if retval != 0:
        print('Could not start device')
        return retval
    retval = device.register()
    if retval != 0:
        print('Could not register device')
        return retval
    retval = device.run(device_args)
    print()
    retval = device.unregister()
    if retval != 0:
        return retval
    return 0


if __name__ == '__main__':
    main(sys.argv[1:])
