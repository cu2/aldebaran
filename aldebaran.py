import datetime
import Queue
import sys
import time

import assembler
import aux
import errors
import instructions
import interrupt_handler


class Aldebaran(aux.Hardware):

    def __init__(self, components, log=None):
        aux.Hardware.__init__(self, log)
        self.clock = components['clock']
        self.cpu = components['cpu']
        self.ram = components['ram']
        self.bios = components['bios']
        self.interrupt_queue = components['interrupt_queue']
        self.interrupt_handler = components['interrupt_handler']
        # architecture:
        self.cpu.register_architecture(self.ram, self.interrupt_queue)
        self.clock.register_architecture(self.cpu)
        self.interrupt_handler.register_architecture(self.cpu, self.interrupt_queue)

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
        start_time = time.time()
        retval = self.load_bios()
        if retval == 0:
            retval = self.interrupt_handler.start()
            if retval == 0:
                retval = self.clock.run()
                self.interrupt_handler.stop()
        stop_time = time.time()
        self.log.log('aldebaran', 'Stopped after %s steps in %s sec (%s Hz).' % (
            self.clock.step_count,
            round(stop_time - start_time, 2),
            int(self.clock.step_count / (stop_time - start_time))
        ))
        return retval


class Clock(aux.Hardware):

    def __init__(self, speed, log=None):
        aux.Hardware.__init__(self, log)
        self.speed = speed
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
        try:
            while True:
                self.log.log('clock', 'Beat %s' % datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11])
                self.cpu.step()
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

    def __init__(self, system_addresses, log=None):
        aux.Hardware.__init__(self, log)
        self.system_addresses = system_addresses
        self.ram = None
        self.interrupt_queue = None
        self.registers = {
            'IP': self.system_addresses['entry_point'],
            'SP': self.system_addresses['SP'],
            'AX': 0,
        }

    def register_architecture(self, ram, interrupt_queue):
        self.ram = ram
        self.interrupt_queue = interrupt_queue

    def step(self):
        if not self.ram:
            self.log.log('cpu', 'ERROR: Cannot run without RAM.')
            return
        if self.interrupt_queue:
            interrupt_number = None
            try:
                interrupt_number = self.interrupt_queue.get_nowait()
            except Queue.Empty:
                pass
            if interrupt_number:
                try:
                    interrupt_number = int(interrupt_number)
                except ValueError:
                    self.log.log('cpu', 'illegal interrupt: %s' % interrupt_number)
                    return
                self.log.log('cpu', 'calling interrupt: %s' % aux.byte_to_str(interrupt_number))
                self.call_int(interrupt_number)
                return
        self.mini_debugger()
        current_instruction, current_subtype = instructions.get_instruction_by_opcode(self.ram.read_byte(self.registers['IP']))
        current_instruction_size = current_instruction.get_instruction_size(current_subtype)
        if current_instruction_size > 1:
            arguments = [self.ram.read_byte(self.registers['IP'] + i) for i in range(1, current_instruction_size)]
            inst = current_instruction(self, current_subtype, arguments)
            self.log.log('cpu', '%s(%s)' % (inst, ', '.join(map(aux.byte_to_str, arguments))))
        else:
            inst = current_instruction(self, current_subtype)
            self.log.log('cpu', '%s' % inst)
        inst.do()
        self.registers['IP'] = inst.next_ip() % self.ram.size

    def mini_debugger(self):
        if not isinstance(self.log, aux.SilentLog):
            ram_page = (self.registers['IP'] / 16) * 16
            self.log.log('cpu', 'IP=%s    RAM[%s]: %s    STACK: %s' % (
                aux.word_to_str(self.registers['IP']),
                aux.word_to_str(ram_page),
                ''.join([('>' if idx == self.registers['IP'] else ' ') + aux.byte_to_str(self.ram.mem[idx]) for idx in xrange(ram_page, ram_page + 16)]),
                ''.join([aux.byte_to_str(self.ram.mem[idx]) + ('<' if idx == self.registers['SP'] else ' ') for idx in xrange(self.system_addresses['SP'] - 15, self.system_addresses['SP'] + 1)]),
            ))

    def stack_push_byte(self, value):
        if self.registers['SP'] < 1:
            raise errors.StackOverflowError()
        self.ram.write_byte(self.registers['SP'], value)
        self.log.log('cpu', 'pushed %s' % aux.byte_to_str(value))
        self.registers['SP'] -= 1

    def stack_pop_byte(self):
        if self.registers['SP'] >= self.system_addresses['SP']:
            raise errors.StackUnderflowError()
        self.registers['SP'] += 1
        value = self.ram.read_byte(self.registers['SP'])
        self.log.log('cpu', 'popped %s' % aux.byte_to_str(value))
        return value

    def stack_push_word(self, value):
        if self.registers['SP'] < 2:
            raise errors.StackOverflowError()
        self.ram.write_word(self.registers['SP'] - 1, value)
        self.log.log('cpu', 'pushed %s' % aux.word_to_str(value))
        self.registers['SP'] -= 2

    def stack_pop_word(self):
        if self.registers['SP'] >= self.system_addresses['SP'] - 1:
            raise errors.StackUnderflowError()
        self.registers['SP'] += 2
        value = self.ram.read_word(self.registers['SP'] - 1)
        self.log.log('cpu', 'popped %s' % aux.word_to_str(value))
        return value

    def call_int(self, interrupt_number):
        self.stack_push_word(self.registers['IP'])
        self.registers['IP'] = self.ram.read_word(self.system_addresses['IV'] + 2 * interrupt_number) % self.ram.size


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
        content = 256 * self.mem[pos1] + self.mem[pos2]
        self.log.log('ram', 'Read word %s from %s.' % (aux.word_to_str(content), aux.word_to_str(pos1)))
        return content

    def write_word(self, pos, content):
        pos1 = pos % self.size
        pos2 = (pos + 1) % self.size
        self.mem[pos1] = content / 256
        self.mem[pos2] = content % 256
        self.log.log('ram', 'Written word %s to %s.' % (aux.word_to_str(content), aux.word_to_str(pos1)))


class BIOS(aux.Hardware):

    def __init__(self, contents):
        aux.Hardware.__init__(self)
        self.contents = contents


def main():
    # config:
    ram_size = 0x10000
    system_addresses = {
        'entry_point': 0x0000,
        'SP': 0xFDFE,
        'default_interrupt_handler': 0xFDFF,
        'IV': 0xFE00,
    }
    start_program_filename = 'examples/hello.ald'
    try:
        asm = assembler.Assembler()
        asm.load_file(start_program_filename)
        start_program = asm.assemble(system_addresses['entry_point'])
    except errors.UnknownInstructionError as e:
        print e
        return 1
    bios = BIOS({
        'start': (system_addresses['entry_point'], start_program),
        'default_interrupt_handler': (system_addresses['default_interrupt_handler'], [4 * instructions.IRET.opcode]),
        'IV': (system_addresses['IV'], list(aux.word_to_bytes(system_addresses['default_interrupt_handler'])) * 256),
    })
    clock_speed = 0.5
    host = 'localhost'
    base_port = 35000
    #
    aldebaran = Aldebaran({
        'clock': Clock(clock_speed),
        'cpu': CPU(system_addresses, aux.Log()),
        'ram': RAM(ram_size, aux.Log()),
        'bios': bios,
        'interrupt_queue': Queue.Queue(),
        'interrupt_handler': interrupt_handler.InterruptHandler(host, base_port + 17, aux.Log()),
    }, aux.Log())
    retval = aldebaran.run()
    print ''
    return retval


if __name__ == '__main__':
    sys.exit(main())
