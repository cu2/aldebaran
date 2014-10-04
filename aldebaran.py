import datetime
import time


TERM_COLORS = True


def log(part, msg, c=None):

    def col(c=None):
        if not TERM_COLORS:
            return ''
        if c is None:
            return '\033[0m'
        else:
            return '\033[%s;%sm' % c

    part_colours = {
        'aldebaran': col((0, 31)),
        'clock': col((1, 30)),
        'cpu': col((0, 32)),
        'ram': col((0, 36)),
        'print': col((0, 41)),
    }

    if c:
        pre_msg = col(c)
    else:
        pre_msg = part_colours.get(part, '')
    print '%s[%s] %s%s' % (
        pre_msg,
        part,
        msg,
        col(),
    )


class Aldebaran(object):

    def __init__(self, clock, cpu, ram):
        self.clock = clock
        self.cpu = cpu
        self.ram = ram
        self.set_verbosity(True)
        # architecture:
        self.cpu.ram = self.ram
        self.clock.cpu = self.cpu

    def set_verbosity(self, verbose):
        self.verbose = verbose
        self.clock.set_verbosity(verbose)
        self.cpu.set_verbosity(verbose)
        self.ram.set_verbosity(verbose)

    def run(self):
        if self.verbose: log('aldebaran', 'started')
        self.clock.run()
        if self.verbose: log('aldebaran', 'stopped')


class Clock(object):

    def __init__(self, speed):
        self.speed = speed
        self.cpu = None

    def set_verbosity(self, verbose):
        self.verbose = verbose

    def run(self):
        if self.verbose: log('clock', 'started')
        self.start_time = time.time()
        try:
            while True:
                if self.verbose: log('clock', 'beat %s' % datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11])
                self.cpu.step()
                self.sleep()
        except (KeyboardInterrupt, SystemExit):
            if self.verbose: log('clock', 'stopped')

    def sleep(self):
        sleep_time = self.start_time + self.speed - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.start_time = time.time()


class Instruction(object):

    def __init__(self, ip, arguments=None):
        self.ip = ip
        self.arguments = arguments

    def do(self):
        pass

    def next_ip(self):
        return self.ip + self.instruction_size


class InstHalt(Instruction):

    instruction_name = 'halt'
    instruction_size = 1

    def next_ip(self):
        return self.ip


class InstPrint(Instruction):

    instruction_name = 'print'
    instruction_size = 2

    def do(self):
        log('print', chr(self.arguments[0]))


class InstJump(Instruction):

    instruction_name = 'jump'
    instruction_size = 2

    def next_ip(self):
        return self.arguments[0]


class CPU(object):

    def __init__(self):
        self.ram = None
        self.registers = {
            'IP': 0,
        }
        self.instruction_set = [
            InstHalt,
            InstPrint,
            InstJump,
        ]

    def set_verbosity(self, verbose):
        self.verbose = verbose

    def step(self):
        if self.verbose: log('cpu', 'step (IP=%s)' % self.registers['IP'])
        current_instruction = self.instruction_set[self.ram.read(self.registers['IP'])]
        current_instruction_size = current_instruction.instruction_size
        if current_instruction_size > 1:
            arguments = [self.ram.read(self.registers['IP'] + i) for i in range(1, current_instruction_size)]
            inst = current_instruction(self.registers['IP'], arguments)
            if self.verbose: log('cpu', '%s(%s)' % (current_instruction.instruction_name, ', '.join(map(str, arguments))))
        else:
            inst = current_instruction(self.registers['IP'])
            if self.verbose: log('cpu', '%s' % current_instruction.instruction_name)
        inst.do()
        self.registers['IP'] = inst.next_ip() % self.ram.size


class RAM(object):

    def __init__(self, size):
        self.size = size
        self.mem = [0] * self.size

    def set_verbosity(self, verbose):
        self.verbose = verbose

    def read(self, pos):
        pos = pos % self.size
        if self.verbose: log('ram', 'read @ %s: %s' % (pos, self.mem[pos]))
        return self.mem[pos]


def main():
    clock = Clock(1)
    cpu = CPU()
    ram = RAM(64)
    bios = [
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
    ]
    for pos, content in enumerate(bios):
        try:
            if issubclass(content, Instruction):
                if content in cpu.instruction_set:
                    ram.mem[pos] = cpu.instruction_set.index(content)
                else:
                    print 'Unknown instruction: %s at %s' % (content(0).instruction_name, pos)
                    return 1
                continue
        except TypeError:
            pass
        ram.mem[pos] = content
    aldebaran = Aldebaran(clock, cpu, ram)
    # aldebaran.set_verbosity(False)
    aldebaran.run()
    print ''
    return 0


if __name__ == '__main__':
    main()
