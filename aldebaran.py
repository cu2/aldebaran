#!/usr/bin/env python

import datetime
import sys
import time
import traceback

import assembler
import aux
import config
import device_controller
import errors
import instructions
import interrupt_controller
import timer


class Aldebaran(aux.Hardware):

    def __init__(self, components, log=None):
        aux.Hardware.__init__(self, log)
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
        for key, (start_pos, contents) in self.bios.contents.iteritems():
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


class Clock(aux.Hardware):

    def __init__(self, freq, log=None):
        aux.Hardware.__init__(self, log)
        if freq:
            self.speed = 1.0 / freq
        else:
            self.speed = 0
        self.start_time = None
        self.cpu = None
        self.step_count = 0

    def register_architecture(self, cpu):
        self.cpu = cpu

    def run(self):
        if not self.cpu:
            self.log.log('clock', 'ERROR: Cannot run without CPU.')
            return 1
        self.log.log('clock', 'Started.')
        self.start_time = time.time()
        shutdown = False
        try:
            while not shutdown:
                self.log.log('clock', 'Beat %s' % datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11])
                shutdown = self.cpu.step()
                self.step_count += 1
                self.sleep()
        except (KeyboardInterrupt, SystemExit):
            self.log.log('clock', 'Stopped.')
        return 0

    def sleep(self):
        sleep_time = self.start_time + self.speed - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.start_time = time.time()


class CPU(aux.Hardware):

    def __init__(self, system_addresses, system_interrupts, inst_list, user_log=None, log=None):
        aux.Hardware.__init__(self, log)
        self.system_addresses = system_addresses
        self.system_interrupts = system_interrupts
        self.inst_list = inst_list
        self.user_log = user_log
        self.ram = None
        self.interrupt_controller = None
        self.timer = None
        self.registers = {
            'IP': self.system_addresses['entry_point'],
            'SP': self.system_addresses['SP'],
            'AX': 0x0000,
            'BX': 0x0000,
            'CX': 0x0000,
            'DX': 0x0000,
            'BP': 0x0000,
            'SI': 0x0000,
            'DI': 0x0000,
        }
        self.flags = {
            'interrupt': 1,
        }
        self.operand_buffer_size = 16
        self.halt = False
        self.shutdown = False

    def register_architecture(self, ram, interrupt_controller, device_controller, timer):
        self.ram = ram
        self.interrupt_controller = interrupt_controller
        self.device_controller = device_controller
        self.timer = timer

    def step(self):
        if not self.ram:
            self.log.log('cpu', 'ERROR: Cannot run without RAM.')
            return
        if self.interrupt_controller and self.flags['interrupt']:
            interrupt_number = self.interrupt_controller.check()
            if interrupt_number is not None:
                self.call_int(interrupt_number)
                return
        if self.halt:
            return
        self.mini_debugger()
        inst_opcode = self.ram.read_byte(self.registers['IP'])
        try:
            inst_name = self.inst_list[inst_opcode]
        except IndexError:
            raise errors.UnknownOpcodeError(inst_opcode)
        operand_buffer = [self.ram.read_byte(self.registers['IP'] + i) for i in range(1, self.operand_buffer_size + 1)]
        current_instruction = getattr(instructions, inst_name)(self, operand_buffer)
        self.log.log('cpu', '%s %s' % (inst_name, current_instruction.operands))
        next_ip = current_instruction.run()
        self.registers['IP'] = next_ip % self.ram.size
        self.log.log('', '')
        return self.shutdown

    def mini_debugger(self):
        if not isinstance(self.log, aux.SilentLog):
            ram_page = (self.registers['IP'] / 16) * 16
            rel_sp = self.system_addresses['SP'] - self.registers['SP']
            stack_page = self.system_addresses['SP'] - 11 - (rel_sp / 12) * 12
            self.log.log('cpu', 'IP=%s AX/BX/CX/DX=%s/%s/%s/%s RAM[%s]:%s ST[%s/%s]:%s' % (
                aux.word_to_str(self.registers['IP']),
                aux.word_to_str(self.registers['AX']),
                aux.word_to_str(self.registers['BX']),
                aux.word_to_str(self.registers['CX']),
                aux.word_to_str(self.registers['DX']),
                aux.word_to_str(ram_page),
                ''.join([('>' if idx == self.registers['IP'] else ' ') + aux.byte_to_str(self.ram.mem[idx]) for idx in xrange(ram_page, ram_page + 16)]),
                aux.word_to_str(stack_page),
                aux.word_to_str(rel_sp / 12),
                ''.join([aux.byte_to_str(self.ram.mem[idx]) + (
                        (
                            '<{' if idx == self.registers['BP'] else '< '
                        ) if idx == self.registers['SP'] else (
                            '{ ' if idx == self.registers['BP'] else '  '
                        )
                    ) for idx in xrange(stack_page, stack_page + 16)]),
            ))

    def get_register(self, register_name):
        value = None
        hex_value = None
        if register_name in self.registers:
            value = self.registers[register_name]
            hex_value = aux.word_to_str(value)
        elif register_name in ['AL', 'BL', 'CL', 'DL']:
            value = aux.get_low(self.registers[register_name[0] + 'X'])
            hex_value = aux.byte_to_str(value)
        elif register_name in ['AH', 'BH', 'CH', 'DH']:
            value = aux.get_high(self.registers[register_name[0] + 'X'])
            hex_value = aux.byte_to_str(value)
        else:
            raise errors.InvalidRegisterNameError(register_name)
        self.log.log('cpu', 'get_reg(%s) = %s' % (register_name, hex_value))
        return value

    def set_register(self, register_name, value):
        if register_name in self.registers:
            self.registers[register_name] = value
            self.log.log('cpu', 'set_reg(%s) = %s' % (register_name, aux.word_to_str(value)))
            return
        if register_name in ['AL', 'BL', 'CL', 'DL']:
            self.registers[register_name[0] + 'X'] = aux.set_low(self.registers[register_name[0] + 'X'], value)
        elif register_name in ['AH', 'BH', 'CH', 'DH']:
            self.registers[register_name[0] + 'X'] = aux.set_high(self.registers[register_name[0] + 'X'], value)
        else:
            raise errors.InvalidRegisterNameError(register_name)
        self.log.log('cpu', 'set_reg(%s) = %s' % (register_name, aux.byte_to_str(value)))

    def stack_push_byte(self, value):
        if self.registers['SP'] < 1:
            raise errors.StackOverflowError()
        self.ram.write_byte(self.registers['SP'], value)
        self.log.log('cpu', 'pushed byte %s' % aux.byte_to_str(value))
        self.registers['SP'] -= 1

    def stack_pop_byte(self):
        if self.registers['SP'] >= self.system_addresses['SP']:
            raise errors.StackUnderflowError()
        self.registers['SP'] += 1
        value = self.ram.read_byte(self.registers['SP'])
        self.log.log('cpu', 'popped byte %s' % aux.byte_to_str(value))
        return value

    def stack_push_word(self, value):
        if self.registers['SP'] < 2:
            raise errors.StackOverflowError()
        self.ram.write_word(self.registers['SP'] - 1, value)
        self.log.log('cpu', 'pushed word %s' % aux.word_to_str(value))
        self.registers['SP'] -= 2

    def stack_pop_word(self):
        if self.registers['SP'] >= self.system_addresses['SP'] - 1:
            raise errors.StackUnderflowError()
        self.registers['SP'] += 2
        value = self.ram.read_word(self.registers['SP'] - 1)
        self.log.log('cpu', 'popped word %s' % aux.word_to_str(value))
        return value

    def stack_push_flags(self):
        flag_word = 0x0000
        for idx, name in enumerate(['interrupt']):
            flag_word += self.flags[name] << idx
        self.stack_push_word(flag_word)
        self.log.log('cpu', 'pushed FLAGS')

    def stack_pop_flags(self):
        flag_word = self.stack_pop_word()
        for idx, name in enumerate(['interrupt']):
            self.flags[name] = (flag_word >> idx) & 0x0001
        self.log.log('cpu', 'popped FLAGS')

    def enable_interrupts(self):
        self.flags['interrupt'] = True
        self.log.log('cpu', 'interrupts enabled')

    def disable_interrupts(self):
        self.flags['interrupt'] = False
        self.log.log('cpu', 'interrupts disabled')

    def call_int(self, interrupt_number):
        self.log.log('cpu', 'calling interrupt: %s' % aux.byte_to_str(interrupt_number))
        self.halt = False
        self.stack_push_flags()
        self.disable_interrupts()
        self.stack_push_word(self.registers['IP'])
        self.registers['IP'] = self.ram.read_word(self.system_addresses['IVT'] + 2 * interrupt_number) % self.ram.size


class RAM(aux.Hardware):

    def __init__(self, size, log=None):
        aux.Hardware.__init__(self, log)
        self.size = size
        self.mem = [0] * self.size
        self.log.log('ram', '%s bytes initialized.' % self.size)

    def read_byte(self, pos):
        pos = pos % self.size
        content = self.mem[pos]
        self.log.log('ram', 'Read byte %s from %s.' % (aux.byte_to_str(content), aux.word_to_str(pos)))
        return content

    def write_byte(self, pos, content):
        pos = pos % self.size
        self.mem[pos] = content
        self.log.log('ram', 'Written byte %s to %s.' % (aux.byte_to_str(content), aux.word_to_str(pos)))

    def read_word(self, pos):
        pos1 = pos % self.size
        pos2 = (pos + 1) % self.size
        content = (self.mem[pos1] << 8) + self.mem[pos2]
        self.log.log('ram', 'Read word %s from %s.' % (aux.word_to_str(content), aux.word_to_str(pos1)))
        return content

    def write_word(self, pos, content):
        pos1 = pos % self.size
        pos2 = (pos + 1) % self.size
        self.mem[pos1] = content >> 8
        self.mem[pos2] = content & 0x00FF
        self.log.log('ram', 'Written word %s to %s.' % (aux.word_to_str(content), aux.word_to_str(pos1)))


class BIOS(aux.Hardware):

    def __init__(self, contents):
        aux.Hardware.__init__(self)
        self.contents = contents


def main(args):
    # logging
    minimal_loggers = {
        'aldebaran': aux.Log(),
        'clock': None,
        'cpu': None,
        'user': aux.Log(),
        'ram': None,
        'interrupt_controller': None,
        'device_controller': None,
        'timer': None,
    }
    normal_loggers = {
        'aldebaran': aux.Log(),
        'clock': None,
        'cpu': aux.Log(),
        'user': aux.Log(),
        'ram': None,
        'interrupt_controller': aux.Log(),
        'device_controller': aux.Log(),
        'timer': None,
    }
    full_loggers = {
        'aldebaran': aux.Log(),
        'clock': aux.Log(),
        'cpu': aux.Log(),
        'user': aux.Log(),
        'ram': aux.Log(),
        'interrupt_controller': aux.Log(),
        'device_controller': aux.Log(),
        'timer': aux.Log(),
    }
    loggers = normal_loggers  # choose verbosity
    # bios
    inst_list, inst_dict = instructions.get_instruction_set()
    if len(args):
        start_program_filename = args[0]
    else:
        start_program_filename = 'examples/hello.ald'
    try:
        asm = assembler.Assembler(inst_dict)
        asm.load_file(start_program_filename)
        start_program = asm.assemble(config.system_addresses['entry_point'])
    except errors.UnknownInstructionError as e:
        print 'errors.UnknownInstructionError: %s' % e
        return 1
    bios = BIOS({
        'start': (config.system_addresses['entry_point'], start_program),
        'default_interrupt_handler': (config.system_addresses['default_interrupt_handler'], [inst_dict['IRET']]),
        'IVT': (config.system_addresses['IVT'], list(aux.word_to_bytes(config.system_addresses['default_interrupt_handler'])) * config.number_of_interrupts),
    })
    # start
    aldebaran = Aldebaran({
        'clock': Clock(config.clock_freq, loggers['clock']),
        'cpu': CPU(config.system_addresses, config.system_interrupts, inst_list, loggers['user'], loggers['cpu']),
        'ram': RAM(config.ram_size, loggers['ram']),
        'bios': bios,
        'interrupt_controller': interrupt_controller.InterruptController(loggers['interrupt_controller']),
        'device_controller': device_controller.DeviceController(
            config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port,
            config.system_addresses, config.system_interrupts,
            [device_controller.IOPort(ioport_number, loggers['device_controller']) for ioport_number in xrange(config.number_of_ioports)],
            loggers['device_controller'],
        ),
        'timer': timer.Timer(config.timer_freq, loggers['timer']),
    }, loggers['aldebaran'])
    retval = aldebaran.run()
    print ''
    return retval


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
