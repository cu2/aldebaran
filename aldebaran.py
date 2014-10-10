import datetime
import Queue
import sys
import threading
import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

import aux
from instructions import *


class Log(object):

    def __init__(self):
        self.term_colors = True
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
        if colstr:
            return '\033[%sm' % colstr
        else:
            return '\033[0m'

    def log(self, part, msg):
        print '%s[%s] %s%s' % (
            self.part_colors.get(part, ''),
            part,
            msg,
            self.col(),
        )


class SilentLog(object):

    def log(self, part, msg):
        pass


class Hardware(object):

    def __init__(self, log=None):
        if log:
            self.log = log
        else:
            self.log = SilentLog()


class Aldebaran(Hardware):

    def __init__(self, components, log=None):
        Hardware.__init__(self, log)
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
                if is_instruction(content):
                    if content in self.cpu.instruction_set:
                        self.ram.write_byte(pos, self.cpu.instruction_set.index(content))
                    else:
                        self.log.log('aldebaran', 'Unknown instruction: %s at %s' % (content.__name__, aux.word_to_str(pos)))
                        return 1
                    continue
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


class Clock(Hardware):

    def __init__(self, speed, log=None):
        Hardware.__init__(self, log)
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


class CPU(Hardware):

    def __init__(self, instruction_set, log=None):
        Hardware.__init__(self, log)
        self.instruction_set = instruction_set
        self.ram = None
        self.interrupt_queue = None
        self.registers = {
            'IP': 1024,
            'SP': 0,
        }

    def register_architecture(self, ram, interrupt_queue):
        self.ram = ram
        self.interrupt_queue = interrupt_queue
        self.registers['SP'] = self.ram.size - 1

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
                self.log.log('cpu', 'interrupt: %s' % interrupt_number)
                return
        self.log.log('cpu', 'IP=%s' % aux.word_to_str(self.registers['IP']))
        current_instruction = self.instruction_set[self.ram.read_byte(self.registers['IP'])]
        current_instruction_size = current_instruction.instruction_size
        if current_instruction_size > 1:
            arguments = [self.ram.read_byte(self.registers['IP'] + i) for i in range(1, current_instruction_size)]
            inst = current_instruction(self, arguments)
            self.log.log('cpu', '%s(%s)' % (current_instruction.__name__, ', '.join(map(aux.byte_to_str, arguments))))
        else:
            inst = current_instruction(self)
            self.log.log('cpu', '%s' % current_instruction.__name__)
        inst.do()
        self.registers['IP'] = inst.next_ip() % self.ram.size

    def stack_push_byte(self, value):
        if self.registers['SP'] < 1:
            raise Exception('Stack overflow')
        self.ram.write_byte(self.registers['SP'], value)
        self.log.log('cpu', 'pushed %s' % aux.byte_to_str(value))
        self.registers['SP'] -= 1

    def stack_pop_byte(self):
        if self.registers['SP'] >= self.ram.size - 1:
            raise Exception('Stack underflow')
        self.registers['SP'] += 1
        value = self.ram.read_byte(self.registers['SP'])
        self.log.log('cpu', 'popped %s' % aux.byte_to_str(value))
        return value

    def stack_push_word(self, value):
        if self.registers['SP'] < 2:
            raise Exception('Stack overflow')
        self.ram.write_word(self.registers['SP'], value)
        self.log.log('cpu', 'pushed %s' % aux.word_to_str(value))
        self.registers['SP'] -= 2

    def stack_pop_word(self):
        if self.registers['SP'] >= self.ram.size - 2:
            raise Exception('Stack underflow')
        self.registers['SP'] += 2
        value = self.ram.read_word(self.registers['SP'])
        self.log.log('cpu', 'popped %s' % aux.word_to_str(value))
        return value


class RAM(Hardware):

    def __init__(self, size, log=None):
        Hardware.__init__(self, log)
        self.size = size
        self.mem = [0] * self.size

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


class BIOS(Hardware):

    def __init__(self, contents):
        Hardware.__init__(self)
        self.contents = contents


class InterruptHandler(Hardware):

    class RequestHandler(BaseHTTPRequestHandler):

        def do_POST(self):
            interrupt_number = self.path.lstrip('/')
            self.server.log.log('interrupt_handler', 'Caught: %s' % interrupt_number)
            self.server.interrupt_queue.put(interrupt_number)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(interrupt_number)
            self.wfile.write('\n')

        def log_message(self, format, *args):
            return

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, request_handler, cpu, interrupt_queue, log):
            HTTPServer.__init__(self, server_address, request_handler)
            self.cpu = cpu
            self.interrupt_queue = interrupt_queue
            self.log = log
            self.daemon_threads = True

    def __init__(self, host, port, log=None):
        Hardware.__init__(self, log)
        self.address = (host, port)
        self.cpu = None
        self.interrupt_queue = None

    def register_architecture(self, cpu, interrupt_queue):
        self.cpu = cpu
        self.interrupt_queue = interrupt_queue

    def start(self):
        if not self.cpu:
            self.log.log('interrupt_handler', 'ERROR: Cannot run without CPU.')
            return 1
        if not self.interrupt_queue:
            self.log.log('interrupt_handler', 'ERROR: Cannot run without Interrupt Queue.')
            return 1
        self.log.log('interrupt_handler', 'Starting...')
        self.server = self.Server(self.address, self.RequestHandler, self.cpu, self.interrupt_queue, self.log)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.log.log('interrupt_handler', 'Started.')
        return 0

    def stop(self):
        self.log.log('interrupt_handler', 'Stopping...')
        self.server.shutdown()
        self.log.log('interrupt_handler', 'Stopped.')


def main():
    # config:
    instruction_set = [
        NOP,
        HALT,
        PRINT,
        JUMP,
        PUSH,
        POP,
    ]
    bios = BIOS({
        'start': (0x0400, [
            PUSH, 8, 0,
            POP, 4, 7,
            PRINT, ord('H'),
            NOP,
            PRINT, ord('e'),
            PRINT, ord('l'),
            PRINT, ord('l'),
            PRINT, ord('o'),
            PRINT, ord(' '),
            PRINT, ord('w'),
            PRINT, ord('o'),
            PRINT, ord('r'),
            PRINT, ord('l'),
            PRINT, ord('d'),
            PRINT, ord('!'),
            JUMP, 4, 6,
        ]),
        'something': (0x0800, [
            ord('Y'), NOP,
        ])
    })
    ram_size = 0x10000
    clock_speed = 0.5
    host = 'localhost'
    base_port = 35000
    #
    aldebaran = Aldebaran({
        'clock': Clock(clock_speed),
        'cpu': CPU(instruction_set, Log()),
        'ram': RAM(ram_size),
        'bios': bios,
        'interrupt_queue': Queue.Queue(),
        'interrupt_handler': InterruptHandler(host, base_port + 17, Log()),
    }, Log())
    retval = aldebaran.run()
    print ''
    return retval


if __name__ == '__main__':
    sys.exit(main())
