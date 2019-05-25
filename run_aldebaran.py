'''
Load executable file and run it

Usage: python run_aldebaran.py <file>
'''

import argparse
import logging
import sys

from hardware import (
    Aldebaran,
    Clock,
    Registers, Stack, CPU,
    Memory, RAM, VirtualRAM,
    InterruptController,
    IOPort, DeviceController,
    Timer,
)
from instructions.instruction_set import INSTRUCTION_SET
from utils import config
from utils import utils
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
            IOPort(ioport_number, config.input_buffer_size)
            for ioport_number in range(config.number_of_ioports)
        ]
        clock_freq = args.clock
        aldebaran = Aldebaran({
            'clock': Clock(clock_freq),
            'registers': Registers(config.system_addresses['bottom_of_stack']),
            'stack': Stack(config.system_addresses['bottom_of_stack']),
            'cpu': CPU(config.system_addresses, INSTRUCTION_SET, config.operand_buffer_size, config.cpu_halt_freq),
            'memory': Memory(config.ram_size),
            'ram': RAM(config.ram_size),
            'virtual_ram': VirtualRAM({
                'device_controller': {
                    'first': config.device_registry_address,
                    'last': config.device_status_table_address + config.device_status_table_size,
                },
            }),
            'interrupt_controller': InterruptController(),
            'device_controller': DeviceController(
                config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port,
                config.system_addresses, config.system_interrupts,
                ioports,
            ),
            'timer': Timer(config.timer_freq, config.number_of_subtimers),
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


def _set_logging(verbosity):
    levels = {
        'ald': 'IIDDDD',
        'usr': 'IIDDDD',
        'clk': 'EIIIID',  # clock signals only at -vvvvv
        'cpu': 'EIDDDD',
        'reg': 'EIIDDD',  # get/set registers from -vvv
        'stk': 'EIIDDD',  # push/pop from -vvv
        'ram': 'EIIDDD',  # read/write from -vvv
        'tim': 'EIIIDD',  # timer beats from -vvvv
        'ict': 'EIDDDD',
        'dct': 'EIDDDD',
    }
    if verbosity > 5:
        verbosity = 5
    utils.config_loggers({
        '__main__': {
            'name': 'Aldebaran',
            'level': levels['ald'][verbosity],
            'color': '0;31',
        },
        'hardware.aldebaran': {
            'name': 'Aldebaran',
            'level': levels['ald'][verbosity],
            'color': '0;31',
        },
        'hardware.aldebaran-crash-dump': {
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
            'color': '1;37',
            'stream': sys.stdout,
        },
        'hardware.cpu.registers': {
            'name': 'CPU',
            'level': levels['reg'][verbosity],
            'color': '1;32',
        },
        'hardware.cpu.stack': {
            'name': 'CPU',
            'level': levels['stk'][verbosity],
            'color': '1;32',
        },
        'hardware.memory': {
            'name': 'Memory',
            'level': levels['ram'][verbosity],
            'color': '0;34',
        },
        'hardware.memory.ram': {
            'name': 'RAM',
            'level': levels['ram'][verbosity],
            'color': '0;34',
        },
        'hardware.memory.virtual_ram': {
            'name': 'VirtualRAM',
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


if __name__ == '__main__':
    main()
