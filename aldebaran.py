import datetime
import Queue
import sys
import threading
import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

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
        for pos, content in enumerate(self.bios.content):
            if is_instruction(content):
                if content in self.cpu.instruction_set:
                    self.ram.write(pos, self.cpu.instruction_set.index(content))
                else:
                    self.log.log('aldebaran', 'Unknown instruction: %s at %s' % (content.__name__, pos))
                    return 1
                continue
            self.ram.write(pos, content)
        self.log.log('aldebaran', 'BIOS loaded.')
        return 0

    def run(self):
        self.log.log('aldebaran', 'Started.')
        retval = self.load_bios()
        if retval == 0:
            retval = self.interrupt_handler.start()
            if retval == 0:
                retval = self.clock.run()
                self.interrupt_handler.stop()
        self.log.log('aldebaran', 'Stopped.')
        return retval


class Clock(Hardware):

    def __init__(self, speed, log=None):
        Hardware.__init__(self, log)
        self.speed = speed
        self.start_time = None
        self.cpu = None

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
            'IP': 0,
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
                self.log.log('cpu', 'interrupt: %s' % interrupt_number)
                return
        self.log.log('cpu', 'IP=%s' % self.registers['IP'])
        current_instruction = self.instruction_set[self.ram.read(self.registers['IP'])]
        current_instruction_size = current_instruction.instruction_size
        if current_instruction_size > 1:
            arguments = [self.ram.read(self.registers['IP'] + i) for i in range(1, current_instruction_size)]
            inst = current_instruction(self.registers['IP'], self.log, arguments)
            self.log.log('cpu', '%s(%s)' % (current_instruction.__name__, ', '.join(map(str, arguments))))
        else:
            inst = current_instruction(self.registers['IP'], self.log)
            self.log.log('cpu', '%s' % current_instruction.__name__)
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


class InterruptHandler(Hardware):

    class RequestHandler(BaseHTTPRequestHandler):

        def do_POST(self):
            interrupt_number = self.path.lstrip('/')
            self.server.interrupt_queue.put(interrupt_number)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(interrupt_number)
            self.wfile.write('\n')

        def log_message(self, format, *args):
            return

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, request_handler, cpu, interrupt_queue):
            HTTPServer.__init__(self, server_address, request_handler)
            self.cpu = cpu
            self.interrupt_queue = interrupt_queue
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
        self.server = self.Server(self.address, self.RequestHandler, self.cpu, self.interrupt_queue)
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
    ]
    bios = BIOS([
        NOP,
        PRINT, ord('H'),
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
        JUMP, 0,
    ])
    ram_size = 256
    clock_speed = 1
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
