'''
Load executable file and run it

Usage: python aldebaran.py <file>
'''

import argparse
import time
import logging

from instructions.instruction_set import INSTRUCTION_SET
from hardware import device_controller
from hardware import interrupt_controller
from hardware import timer
from hardware.clock import Clock
from hardware.cpu import CPU
from hardware.ram import RAM
from utils import boot
from utils import config
from utils import utils
from utils import executable
from utils.errors import AldebaranError


logger = logging.getLogger(__name__)


def main():
    '''
    Entry point of script
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        help='Aldebaran executable file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Verbosity'
    )
    args = parser.parse_args()
    _set_logging(args.verbose)
    boot_file = args.file
    ioports = [
        device_controller.IOPort(ioport_number)
        for ioport_number in range(config.number_of_ioports)
    ]
    aldebaran = Aldebaran({
        'clock': Clock(config.clock_freq),
        'cpu': CPU(config.system_addresses, config.system_interrupts, INSTRUCTION_SET),
        'ram': RAM(config.ram_size),
        'interrupt_controller': interrupt_controller.InterruptController(),
        'device_controller': device_controller.DeviceController(
            config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port,
            config.system_addresses, config.system_interrupts,
            ioports,
        ),
        'timer': timer.Timer(config.timer_freq),
    })
    aldebaran.boot(boot_file)
    aldebaran.run()


class Aldebaran:
    '''
    Aldebaran
    '''

    def __init__(self, components):
        self.clock = components['clock']
        self.cpu = components['cpu']
        self.ram = components['ram']
        self.interrupt_controller = components['interrupt_controller']
        self.device_controller = components['device_controller']
        self.timer = components['timer']
        # architecture:
        self.cpu.register_architecture(self.ram, self.interrupt_controller, self.device_controller, self.timer)
        self.clock.register_architecture(self.cpu)
        self.device_controller.register_architecture(self.interrupt_controller, self.ram)
        self.timer.register_architecture(self.interrupt_controller)

    def boot(self, boot_file):
        '''
        Load boot image and boot file
        '''
        logger.info('Loading boot file %s...', boot_file)
        boot_loader = boot.BootLoader(self.ram)
        boot_image = config.create_boot_image()  # later it should be loaded from file
        boot_loader.load_image(0, boot_image)
        boot_exe = executable.Executable()
        boot_exe.load_from_file(boot_file)
        if boot_exe.version != 1:
            raise UnsupportedExecutableVersionError('Unsupported version: {}'.format(boot_exe.version))
        boot_loader.load_executable(config.system_addresses['entry_point'], boot_exe)
        logger.info('Loaded.')

    def run(self):
        '''
        Start device controller, timer and clock
        '''
        logger.info('Started.')
        retval = self.device_controller.start()
        if retval != 0:
            raise AldebaranError('Could not start Device Controller')
        retval = self.timer.start()
        if retval != 0:
            raise AldebaranError('Could not start Timer')
        start_time = time.time()
        try:
            retval = self.clock.run()
            if retval != 0:
                raise AldebaranError('Could not start Clock')
        finally:
            stop_time = time.time()
            self.timer.stop()
            self.device_controller.stop()
            logger.info(
                'Stopped after %s cycles in %s sec (%d Hz).',
                self.clock.cycle_count,
                round(stop_time - start_time, 2),
                round(self.clock.cycle_count / (stop_time - start_time)),
            )


def _set_logging(verbosity):
    levels = {
        'ald': 'IIDDD',
        'usr': 'IIDDD',
        'clk': 'EIIID',  # clock signals only at -vvvv
        'cpu': 'EIDDD',
        'ram': 'EIIII',  # DEBUG is basically uselessly verbose
        'tim': 'EIIDD',  # timer beats from -vvv
        'ict': 'EIDDD',
        'dct': 'EIDDD',
    }
    if verbosity > 4:
        verbosity = 4
    utils.config_loggers({
        '__main__': {
            'name': 'Aldebaran',
            'level': levels['ald'][verbosity],
            'color': '0;31',
        },
        'hardware.clock': {
            'name': 'Clock',
            'level': levels['clk'][verbosity],
            'color': '1;30',
        },
        'hardware.cpu': {
            'name': 'CPU',
            'level': levels['cpu'][verbosity],
            'color': '0;32',
        },
        'hardware.cpu-user': {
            'name': '',
            'level': levels['usr'][verbosity],
            'color': '37;1',
        },
        'hardware.ram': {
            'name': 'RAM',
            'level': levels['ram'][verbosity],
            'color': '0;34',
        },
        'hardware.timer': {
            'name': 'Timer',
            'level': levels['tim'][verbosity],
            'color': '0;33',
        },
        'hardware.interrupt_controller': {
            'name': 'IntCont',
            'level': levels['ict'][verbosity],
            'color': '0;35',
        },
        'hardware.device_controller': {
            'name': 'DevCont',
            'level': levels['dct'][verbosity],
        },
    })


# pylint: disable=missing-docstring

class UnsupportedExecutableVersionError(AldebaranError):
    pass


if __name__ == '__main__':
    main()
