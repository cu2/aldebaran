import datetime
import sys
import time

from instructions import *


class Log(object):

    def __init__(self, verbose=True):
        self.term_colors = True
        self.verbose = verbose
        self.part_colors = {
            'aldebaran': self.col('0;31'),
            'clock': self.col('1;30'),
            'cpu': self.col('0;32'),
            'ram': self.col('0;36'),
            'print': self.col('37;1'),
        }

    def col(self, colstr=None):
        if not self.term_colors:
            return ''
        if colstr is None:
            return '\033[0m'
        else:
            return '\033[%sm' % colstr

    def log(self, part, msg):
        if not self.verbose:
            return
        print '%s[%s] %s%s' % (
            self.part_colors.get(part, ''),
            part,
            msg,
            self.col(),
        )


class Hardware(object):

    def __init__(self, log=None):
        if log:
            self.log = log
        else:
            self.log = Log(False)


class Aldebaran(Hardware):

    def __init__(self, clock, cpu, ram, bios, log=None):
        Hardware.__init__(self, log)
        self.clock = clock
        self.cpu = cpu
        self.ram = ram
        self.bios = bios
        # architecture:
        self.cpu.ram = self.ram
        self.clock.cpu = self.cpu

    def load_bios(self):
        self.log.log('aldebaran', 'Loading BIOS...')
        for pos, content in enumerate(self.bios.content):
            if is_instruction(content):
                if content in self.cpu.instruction_set:
                    self.ram.write(pos, self.cpu.instruction_set.index(content))
                else:
                    self.log.log('aldebaran', 'Unknown instruction: %s at %s' % (content.instruction_name, pos))
                    return 1
                continue
            self.ram.write(pos, content)
        self.log.log('aldebaran', 'BIOS loaded.')
        return 0

    def run(self):
        self.log.log('aldebaran', 'Started.')
        self.clock.run()
        self.log.log('aldebaran', 'Stopped.')


class Clock(Hardware):

    def __init__(self, speed, log=None):
        Hardware.__init__(self, log)
        self.speed = speed
        self.start_time = None
        self.cpu = None

    def run(self):
        if self.cpu is None:
            self.log.log('clock', 'ERROR: Cannot run without CPU.')
            return
        self.log.log('clock', 'Started.')
        self.start_time = time.time()
        try:
            while True:
                self.log.log('clock', 'Beat %s' % datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11])
                self.cpu.step()
                self.sleep()
        except (KeyboardInterrupt, SystemExit):
            self.log.log('clock', 'Stopped.')

    def sleep(self):
        sleep_time = self.start_time + self.speed - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.start_time = time.time()


class CPU(Hardware):

    def __init__(self, instruction_set, log=None):
        Hardware.__init__(self, log)
        self.instruction_set = instruction_set
        self.ram = None
        self.registers = {
            'IP': 0,
        }

    def step(self):
        if self.ram is None:
            self.log.log('cpu', 'ERROR: Cannot run without RAM.')
            return
        self.log.log('cpu', 'IP=%s' % self.registers['IP'])
        current_instruction = self.instruction_set[self.ram.read(self.registers['IP'])]
        current_instruction_size = current_instruction.instruction_size
        if current_instruction_size > 1:
            arguments = [self.ram.read(self.registers['IP'] + i) for i in range(1, current_instruction_size)]
            inst = current_instruction(self.registers['IP'], self.log, arguments)
            self.log.log('cpu', '%s(%s)' % (current_instruction.instruction_name, ', '.join(map(str, arguments))))
        else:
            inst = current_instruction(self.registers['IP'], self.log)
            self.log.log('cpu', '%s' % current_instruction.instruction_name)
        inst.do()
        self.registers['IP'] = inst.next_ip() % self.ram.size


class RAM(Hardware):

    def __init__(self, size, log=None):
        Hardware.__init__(self, log)
        self.size = size
        self.mem = [0] * self.size

    def read(self, pos):
        pos = pos % self.size
        self.log.log('ram', 'Read %s from %s.' % (self.mem[pos], pos))
        return self.mem[pos]

    def write(self, pos, content):
        pos = pos % self.size
        self.mem[pos] = content
        self.log.log('ram', 'Written %s to %s.' % (content, pos))


class BIOS(Hardware):

    def __init__(self, content):
        Hardware.__init__(self)
        self.content = content


def main():
    # config:
    instruction_set = [
        InstHalt,
        InstPrint,
        InstJump,
    ]
    bios = BIOS([
        InstPrint, ord('H'),
        InstPrint, ord('e'),
        InstPrint, ord('l'),
        InstPrint, ord('l'),
        InstPrint, ord('o'),
        InstPrint, ord(' '),
        InstPrint, ord('w'),
        InstPrint, ord('o'),
        InstPrint, ord('r'),
        InstPrint, ord('l'),
        InstPrint, ord('d'),
        InstPrint, ord('!'),
        InstJump, 0,
    ])
    ram_size = 256
    clock_speed = 0.5
    # logging:
    primary_log = Log()
    seconday_log = Log(False)
    #
    clock = Clock(clock_speed, seconday_log)
    ram = RAM(ram_size, seconday_log)
    cpu = CPU(instruction_set, primary_log)
    aldebaran = Aldebaran(clock, cpu, ram, bios, primary_log)
    if 0 != aldebaran.load_bios():
        return 1
    aldebaran.run()
    print ''
    return 0


if __name__ == '__main__':
    sys.exit(main())
