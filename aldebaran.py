#!/usr/bin/env python

import argparse
import sys
import time
import traceback

import assembler
from instructions.instruction_set import INSTRUCTION_SET

from utils import config, errors, utils

from hardware import device_controller
from hardware import interrupt_controller
from hardware import timer

from hardware.clock import Clock
from hardware.cpu import CPU
from hardware.ram import RAM


class Aldebaran(utils.Hardware):

    def __init__(self, components, log=None):
        utils.Hardware.__init__(self, log)
        self.clock = components['clock']
        self.cpu = components['cpu']
        self.ram = components['ram']
        self.bios = components['bios']
        self.interrupt_controller = components['interrupt_controller']
        self.device_controller = components['device_controller']
        self.timer = components['timer']
        # architecture:
        self.cpu.register_architecture(self.ram, self.interrupt_controller, self.device_controller, self.timer)
        self.clock.register_architecture(self.cpu)
        self.device_controller.register_architecture(self.interrupt_controller, self.ram)
        self.timer.register_architecture(self.interrupt_controller)

    def load_bios(self):
        self.log.log('aldebaran', 'Loading BIOS...')
        for key, (start_pos, contents) in self.bios.contents.items():
            for rel_pos, content in enumerate(contents):
                pos = start_pos + rel_pos
                self.ram.write_byte(pos, content)
        self.log.log('aldebaran', 'BIOS loaded.')
        return 0

    def run(self):
        self.log.log('aldebaran', 'Started.')
        retval = self.load_bios()
        if retval != 0:
            return retval
        retval = self.device_controller.start()
        if retval != 0:
            return retval
        retval = self.timer.start()
        if retval != 0:
            return retval
        start_time = time.time()
        try:
            retval = self.clock.run()
        except Exception:
            tb = traceback.format_exc()
            self.log.log('aldebaran', 'EXCEPTION: %s' % tb)
            retval = 1
        stop_time = time.time()
        self.timer.stop()
        self.device_controller.stop()
        self.log.log('aldebaran', 'Stopped after %s steps in %s sec (%s Hz).' % (
            self.clock.step_count,
            round(stop_time - start_time, 2),
            int(round(self.clock.step_count / (stop_time - start_time)))
        ))
        return retval


class BIOS(utils.Hardware):

    def __init__(self, contents):
        utils.Hardware.__init__(self)
        self.contents = contents


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        help='ALDB binary file'
    )
    # TODO: add verbosity
    args = parser.parse_args()
    # logging
    loggers = config.loggers
    # bios
    with open(args.file, 'rb') as f:
        start_program = f.read()
    instruction_mapping = {
        inst.__name__: (opcode, inst)
        for opcode, inst in INSTRUCTION_SET
    }
    bios = BIOS({
        'start': (config.system_addresses['entry_point'], start_program),
        'default_interrupt_handler': (config.system_addresses['default_interrupt_handler'], [instruction_mapping['IRET'][0]]),
        'IVT': (config.system_addresses['IVT'], utils.word_to_bytes(config.system_addresses['default_interrupt_handler']) * config.number_of_interrupts),
    })
    # start
    aldebaran = Aldebaran({
        'clock': Clock(config.clock_freq, loggers['clock']),
        'cpu': CPU(config.system_addresses, config.system_interrupts, INSTRUCTION_SET, loggers['user'], loggers['cpu']),
        'ram': RAM(config.ram_size, loggers['ram']),
        'bios': bios,
        'interrupt_controller': interrupt_controller.InterruptController(loggers['interrupt_controller']),
        'device_controller': device_controller.DeviceController(
            config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port,
            config.system_addresses, config.system_interrupts,
            [device_controller.IOPort(ioport_number, loggers['device_controller']) for ioport_number in range(config.number_of_ioports)],
            loggers['device_controller'],
        ),
        'timer': timer.Timer(config.timer_freq, loggers['timer']),
    }, loggers['aldebaran'])
    retval = aldebaran.run()
    print()
    sys.exit(retval)
