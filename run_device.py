import argparse
import importlib
import logging
import sys

from utils import utils


logger = logging.getLogger(__name__)


def main():
    '''
    Entry point of script
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'device_name',
        help='Device name'
    )
    parser.add_argument(
        'ioport_number',
        type=int,
        help='IOPort number'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Verbosity'
    )
    args = parser.parse_args()
    _set_logging(args.verbose)
    device_name = args.device_name
    ioport_number = args.ioport_number
    device_args = []  # TODO: ???
    try:
        device_module = importlib.import_module('devices.%s' % device_name)
    except ImportError:
        logger.error('Could not import %s', device_name)
        return 1
    device = getattr(device_module, device_module.DEVICE_CLASS)(
        ioport_number=ioport_number,
        device_descriptor=(device_module.DEVICE_TYPE, device_module.DEVICE_ID),
    )
    retval = device.start()
    if retval != 0:
        logger.error('Could not start device')
        return retval
    retval = device.register()
    if retval != 0:
        logger.error('Could not register device')
        return retval
    retval = device.run(device_args)
    retval = device.unregister()
    if retval != 0:
        return retval
    return 0


def _set_logging(verbosity):
    levels = {
        'drn': 'EEE',
        'dev': 'EID',
    }
    if verbosity > 2:
        verbosity = 2
    utils.config_loggers({
        '__main__': {
            'name': 'DeviceRunner',
            'level': levels['drn'][verbosity],
            'color': '0;31',
        },
        'devices.device': {
            'name': 'Device',
            'level': levels['dev'][verbosity],
            'color': '1;30',
        },
    })


if __name__ == '__main__':
    main()
