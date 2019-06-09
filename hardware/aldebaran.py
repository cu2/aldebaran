'''
Aldebaran
'''

import time
import logging

from utils import boot
from utils import config
from utils import utils
from utils import executable
from utils.errors import AldebaranError


logger = logging.getLogger(__name__)
logger_crash_dump = logging.getLogger(__name__ + '-crash-dump')


class Aldebaran:
    '''
    Aldebaran
    '''

    def __init__(self, components):
        self.clock = components['clock']
        self.registers = components['registers']
        self.stack = components['stack']
        self.cpu = components['cpu']
        self.memory = components['memory']
        self.ram = components['ram']
        self.virtual_ram = components['virtual_ram']
        self.interrupt_controller = components['interrupt_controller']
        self.device_controller = components['device_controller']
        self.timer = components['timer']
        self.debugger = components['debugger']
        # architecture:
        self.cpu.register_architecture(
            self.registers,
            self.stack,
            self.memory,
            self.interrupt_controller,
            self.device_controller,
            self.timer,
            self.debugger,
        )
        self.clock.register_architecture(self.cpu)
        self.device_controller.register_architecture(self.interrupt_controller)
        self.timer.register_architecture(self.interrupt_controller)
        self.memory.register_architecture(self.ram, self.virtual_ram)
        self.virtual_ram.register_architecture(self.device_controller)
        if self.debugger:
            self.debugger.register_architecture(self.cpu, self.clock, self.memory)

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
        if self.debugger:
            self.debugger.start()
        self.device_controller.start()
        self.timer.start()
        start_time = time.time()
        try:
            self.clock.run(bool(self.debugger))
        finally:
            stop_time = time.time()
            self.timer.stop()
            self.device_controller.stop()
            if self.debugger:
                self.debugger.stop()
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
        ip = self.cpu.ip
        logger_crash_dump.error('')
        logger_crash_dump.error('IP=%s', utils.word_to_str(ip))
        logger_crash_dump.error('Entry point=%s', utils.word_to_str(self.cpu.system_addresses['entry_point']))
        logger_crash_dump.error('Halt=%s', self.cpu.halt)
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
                    ('>' if idx == ip else ' ') + utils.byte_to_str(self.ram.read_byte(idx, silent=True))
                    for idx in range(offset + ram_page, offset + ram_page + ram_page_size)
                ]),
            )
        # stack
        sp = self.cpu.registers.get_register('SP', silent=True)
        bp = self.cpu.registers.get_register('BP', silent=True)
        logger_crash_dump.error('')
        logger_crash_dump.error('SP=%s', utils.word_to_str(sp))
        logger_crash_dump.error('BP=%s', utils.word_to_str(bp))
        logger_crash_dump.error('Bottom of stack=%s', utils.word_to_str(self.cpu.system_addresses['bottom_of_stack']))
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
                ''.join([utils.byte_to_str(self.ram.read_byte(idx, silent=True)) + (
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
            logger_crash_dump.error('%s=%s', reg, utils.word_to_str(self.cpu.registers.get_register(reg, silent=True)))


# pylint: disable=missing-docstring

class UnsupportedExecutableVersionError(AldebaranError):
    pass
