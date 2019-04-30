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
logger_crash_dump = logging.getLogger(__name__ + '-crash-dump')


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
        '-c', '--clock',
        type=int,
        default=0,
        help='Clock frequency; default = 0 (meaning TURBO mode)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Verbosity'
    )
    args = parser.parse_args()
    _set_logging(args.verbose)

    try:
        boot_file = args.file
        ioports = [
            device_controller.IOPort(ioport_number)
            for ioport_number in range(config.number_of_ioports)
        ]
        clock_freq = args.clock
        aldebaran = Aldebaran({
            'clock': Clock(clock_freq),
            'cpu': CPU(config.system_addresses, config.system_interrupts, INSTRUCTION_SET),
            'ram': RAM(config.ram_size),
            'interrupt_controller': interrupt_controller.InterruptController(),
            'device_controller': device_controller.DeviceController(
                config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port,
                config.system_addresses, config.system_interrupts,
                ioports,
            ),
            'timer': timer.Timer(config.timer_freq, config.number_of_subtimers),
        })
        aldebaran.boot(boot_file)
    except AldebaranError as ex:
        logger.error(ex)
        return
    except (KeyboardInterrupt, SystemExit):
        return

    try:
        aldebaran.run()
    except AldebaranError as ex:
        logger.error(ex)
        aldebaran.crash_dump()
    except (KeyboardInterrupt, SystemExit):
        pass


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
        self.timer.start()
        start_time = time.time()
        try:
            self.clock.run()
        finally:
            stop_time = time.time()
            self.timer.stop()
            self.device_controller.stop()
            self._print_stats(start_time, stop_time)

    def _print_stats(self, start_time, stop_time):
        full_time = stop_time - start_time
        sleep_time = self.clock.sleep_time
        run_time = full_time - sleep_time
        logger.info(
            'Stopped after %s cycles in %s sec (%d Hz).',
            self.clock.cycle_count,
            round(full_time, 2),
            round(self.clock.cycle_count / full_time),
        )
        if self.clock.cycle_count > 0:
            logger.info(
                'Average runtime/sleeptime/cycletime: %s / %s / %s us',
                round(run_time / self.clock.cycle_count * 1000000, 2),
                round(sleep_time / self.clock.cycle_count * 1000000, 2),
                round(full_time / self.clock.cycle_count * 1000000, 2),
            )
        logger.info(
            'Total runtime/sleeptime/cycletime: %s / %s / %s sec',
            round(run_time, 2),
            round(sleep_time, 2),
            round(full_time, 2),
        )

    def crash_dump(self):
        '''
        Print crash dump
        '''
        logger_crash_dump.error('### CRASH DUMP ###')
        # ip
        ip = self.cpu.registers['IP']
        logger_crash_dump.error('')
        logger_crash_dump.error('IP=%s', utils.word_to_str(ip))
        logger_crash_dump.error('Entry point=%s', utils.word_to_str(self.cpu.system_addresses['entry_point']))
        # ram
        ram_page_size = 16
        ram_page = (ip // ram_page_size) * ram_page_size
        logger_crash_dump.error('')
        logger_crash_dump.error('RAM:')
        for page_offset in range(-2, 3):
            offset = page_offset * ram_page_size
            if offset + ram_page < 0:
                continue
            if offset + ram_page + ram_page_size - 1 > self.ram.size:
                continue
            logger_crash_dump.error(
                '%s: %s',
                utils.word_to_str(offset + ram_page),
                ''.join([
                    ('>' if idx == ip else ' ') + utils.byte_to_str(self.ram.read_byte(idx))
                    for idx in range(offset + ram_page, offset + ram_page + ram_page_size)
                ]),
            )
        # stack
        sp = self.cpu.registers['SP']
        bp = self.cpu.registers['BP']
        logger_crash_dump.error('')
        logger_crash_dump.error('SP=%s', utils.word_to_str(sp))
        logger_crash_dump.error('BP=%s', utils.word_to_str(bp))
        logger_crash_dump.error('Bottom of stack=%s', utils.word_to_str(self.cpu.system_addresses['SP']))
        logger_crash_dump.error('')
        logger_crash_dump.error('Stack:')
        stack_page_size = 16
        stack_page = (sp // stack_page_size) * stack_page_size
        if stack_page < 0:
            stack_page = 0
        for page_offset in range(-1, 4):
            offset = page_offset * stack_page_size
            if offset + stack_page < 0:
                continue
            if offset + stack_page + stack_page_size - 1 > self.ram.size:
                continue
            logger_crash_dump.error(
                '%s:  %s',
                utils.word_to_str(offset + stack_page),
                ''.join([utils.byte_to_str(self.ram.read_byte(idx)) + (
                    (
                        '{' if idx == bp else '<'
                    ) if idx == sp else (
                        '[' if idx == bp else ' '
                    )
                ) for idx in range(offset + stack_page, offset + stack_page + stack_page_size)]),
            )
        # registers
        logger_crash_dump.error('')
        logger_crash_dump.error('Registers:')
        for reg in ['AX', 'BX', 'CX', 'DX', 'SI', 'DI']:
            logger_crash_dump.error('%s=%s', reg, utils.word_to_str(self.cpu.registers[reg]))


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
        '__main__-crash-dump': {
            'name': '',
            'level': levels['ald'][verbosity],
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
        'hardware.device_controller-ioport': {
            'name': '',
            'level': levels['dct'][verbosity],
        },
    })


# pylint: disable=missing-docstring

class UnsupportedExecutableVersionError(AldebaranError):
    pass


if __name__ == '__main__':
    main()
