'''
Run device

Usage: python run_device.py <device_name> <ioport_number>
'''

import argparse
import importlib
import logging
import time

from utils import config
from utils import utils
from devices.device import DeviceError


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
    module_name = 'devices.{device_name}.{device_name}'.format(device_name=device_name)
    aldebaran_address = config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port
    device_address = config.device_host, config.device_base_port + ioport_number
    try:
        device_module = importlib.import_module(module_name)
    except ImportError:
        logger.error('Could not import %s', device_name)
        return
    device = getattr(device_module, device_module.DEVICE_CLASS)(
        ioport_number=ioport_number,
        device_descriptor=(device_module.DEVICE_TYPE, device_module.DEVICE_ID),
        aldebaran_address=aldebaran_address,
        device_address=device_address,
    )
    device.start()

    try:
        _register(device)
    except DeviceError as ex:
        device.stop()
        logger.error(ex)
        return
    except (KeyboardInterrupt, SystemExit):
        device.stop()
        return

    try:
        device.run(device_args)
    except DeviceError as ex:
        logger.error(ex)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        try:
            device.unregister()
        except DeviceError as ex:
            logger.error(ex)
        device.stop()


def _register(device):
    while True:
        try:
            device.register()
        except DeviceError:
            time.sleep(1)
        else:
            return


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
