'''
Load executable file and run it

Usage: python aldebaran.py <file>
'''

import argparse
import time

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


def main():
    '''
    Entry point of script
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        help='Aldebaran executable file'
    )
    # TODO: add verbosity
    args = parser.parse_args()
    boot_file = args.file
    loggers = config.loggers
    ioports = [
        device_controller.IOPort(ioport_number, loggers['device_controller'])
        for ioport_number in range(config.number_of_ioports)
    ]
    aldebaran = Aldebaran({
        'clock': Clock(config.clock_freq, loggers['clock']),
        'cpu': CPU(config.system_addresses, config.system_interrupts, INSTRUCTION_SET, loggers['user'], loggers['cpu']),
        'ram': RAM(config.ram_size, loggers['ram']),
        'interrupt_controller': interrupt_controller.InterruptController(loggers['interrupt_controller']),
        'device_controller': device_controller.DeviceController(
            config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port,
            config.system_addresses, config.system_interrupts,
            ioports,
            loggers['device_controller'],
        ),
        'timer': timer.Timer(config.timer_freq, loggers['timer']),
    }, loggers['aldebaran'])
    aldebaran.boot(boot_file)
    aldebaran.run()


class Aldebaran(utils.Hardware):
    '''
    Aldebaran
    '''

    def __init__(self, components, log=None):
        utils.Hardware.__init__(self, log)
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
        self.log.log('aldebaran', 'Loading boot file {}...'.format(boot_file))
        boot_loader = boot.BootLoader(self.ram)
        boot_image = config.create_boot_image()  # later it should be loaded from file
        boot_loader.load_image(0, boot_image)
        boot_exe = executable.Executable()
        boot_exe.load_from_file(boot_file)
        if boot_exe.version != 1:
            raise UnsupportedExecutableVersionError('Unsupported version: {}'.format(boot_exe.version))
        boot_loader.load_executable(config.system_addresses['entry_point'], boot_exe)
        self.log.log('aldebaran', 'Loaded.')

    def run(self):
        '''
        Start device controller, timer and clock
        '''
        self.log.log('aldebaran', 'Started.')
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
            self.log.log('aldebaran', 'Stopped after %s steps in %s sec (%s Hz).' % (
                self.clock.step_count,
                round(stop_time - start_time, 2),
                round(self.clock.step_count / (stop_time - start_time)),
            ))


# pylint: disable=missing-docstring

class AldebaranError(Exception):
    pass


class UnsupportedExecutableVersionError(AldebaranError):
    pass


if __name__ == '__main__':
    main()
