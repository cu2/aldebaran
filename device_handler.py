import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

import aux


class DeviceHandler(aux.Hardware):

    class RequestHandler(BaseHTTPRequestHandler):

        def do_POST(self):
            ioport_number = self.path.lstrip('/')
            self.server.log.log('device_handler', 'Caught: %s' % ioport_number)
            try:
                ioport_number = int(ioport_number)
                if ioport_number < 0:
                    raise ValueError
                if ioport_number >= len(self.server.ioports):
                    raise ValueError
            except ValueError:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self.wfile.write('ERROR: IOPort number must be an integer between 0 and %s.' % (len(self.server.ioports) - 1))
                self.wfile.write('\n')
                return
            try:
                request_body_length = int(self.headers.getheader('content-length'))
            except TypeError:
                self.send_response(411)  # Length Required
                self.end_headers()
                self.wfile.write('ERROR: Header "content-length" missing.')
                self.wfile.write('\n')
                return
            try:
                request_body = self.rfile.read(request_body_length)
                command, argument = request_body[:4], request_body[4:]
            except Exception:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self.wfile.write('ERROR: Cannot parse request.')
                self.wfile.write('\n')
                return
            if command == 'HELO':
                self.register_device(ioport_number, argument)
                return
            if command == 'BYE!':
                self.unregister_device(ioport_number)
                return
            if not self.server.ioports[ioport_number].registered:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self.wfile.write('ERROR: IOPort %s is not yet registered.' % ioport_number)
                self.wfile.write('\n')
                return
            response_code, response = self.server.ioports[ioport_number].handle_input(command, argument)
            self.send_response(response_code)
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, format, *args):
            return

        def register_device(self, ioport_number, argument):
            try:
                device_type, device_id, device_host, device_port = argument.split(',')
                device_type = int(device_type)
                device_id = int(device_id)
                device_port = int(device_port)
            except Exception:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self.wfile.write('ERROR: Cannot parse argument.')
                self.wfile.write('\n')
                return
            try:
                if device_type < 1 or device_type > 255:  # device type 0 means no device
                    raise ValueError
                if device_id < 0 or device_id > 0x1000000 - 1:
                    raise ValueError
            except ValueError:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self.wfile.write('ERROR: Device type must be between 1 and 255, device ID must be between 0 and %s.' % (0x1000000 - 1))
                self.wfile.write('\n')
                return
            self.server.log.log('device_handler', 'Registering device to IOPort %s...' % ioport_number)
            self.server.log.log('device_handler', 'Device type and ID: %s/%s' % (device_type, device_id))
            self.server.log.log('device_handler', 'Device host and port: %s:%s' % (device_host, device_port))
            self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number, device_type)
            self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number + 1, device_id >> 16)
            self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number + 2, (device_id >> 8) & 0xFF)
            self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number + 3, device_id & 0xFF)
            self.server.ioports[ioport_number].register_device(device_host, device_port)
            self.server.interrupt_queue.put(self.server.cpu.system_interrupts['device_registered'])
            self.send_response(200)
            self.end_headers()
            self.wfile.write('Device registered to IOPort %s.' % ioport_number)
            self.wfile.write('\n')
            self.server.log.log('device_handler', 'Device registered to IOPort %s.' % ioport_number)

        def unregister_device(self, ioport_number):
            self.server.log.log('device_handler', 'Unregistering device from IOPort %s...' % ioport_number)
            self.server.ram.write_word(self.server.device_registry_address + 4 * ioport_number, 0)
            self.server.ram.write_word(self.server.device_registry_address + 4 * ioport_number + 2, 0)
            self.server.ioports[ioport_number].unregister_device()
            self.server.interrupt_queue.put(self.server.cpu.system_interrupts['device_unregistered'])
            self.send_response(200)
            self.end_headers()
            self.wfile.write('Device unregistered from IOPort %s.' % ioport_number)
            self.wfile.write('\n')
            self.server.log.log('device_handler', 'Device unregistered from IOPort %s.' % ioport_number)

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, device_registry_address, ioports, request_handler, cpu, interrupt_queue, ram, log):
            HTTPServer.__init__(self, server_address, request_handler)
            self.device_registry_address = device_registry_address
            self.ioports = ioports
            self.cpu = cpu
            self.interrupt_queue = interrupt_queue
            self.ram = ram
            self.log = log
            self.daemon_threads = True

    def __init__(self, host, port, device_registry_address, ioports, log=None):
        aux.Hardware.__init__(self, log)
        self.address = (host, port)
        self.device_registry_address = device_registry_address
        self.ioports = ioports
        self.cpu = None
        self.interrupt_queue = None
        self.ram = None

    def register_architecture(self, cpu, interrupt_queue, ram):
        self.cpu = cpu
        self.interrupt_queue = interrupt_queue
        self.ram = ram
        for ioport in self.ioports:
            ioport.register_architecture(self)

    def start(self):
        if not self.cpu:
            self.log.log('device_handler', 'ERROR: Cannot run without CPU.')
            return 1
        if not self.interrupt_queue:
            self.log.log('device_handler', 'ERROR: Cannot run without Interrupt Queue.')
            return 1
        if not self.ram:
            self.log.log('device_handler', 'ERROR: Cannot run without RAM.')
            return 1
        self.log.log('device_handler', 'Starting...')
        self.server = self.Server(self.address, self.device_registry_address, self.ioports, self.RequestHandler, self.cpu, self.interrupt_queue, self.ram, self.log)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.log.log('device_handler', 'Started.')
        return 0

    def stop(self):
        self.log.log('device_handler', 'Stopping...')
        self.server.shutdown()
        self.log.log('device_handler', 'Stopped.')


class IOPort(aux.Hardware):

    def __init__(self, ioport_number, log=None):
        aux.Hardware.__init__(self, log)
        self.ioport_number = ioport_number
        self.registered = False
        self.device_host = None
        self.device_port = None
        self.input_buffer = ''
        self.output_buffer = ''
        self.device_handler = None
        self.log.log('ioport %s' % self.ioport_number, 'Created.')

    def register_architecture(self, device_handler):
        self.device_handler = device_handler
        self.log.log('ioport %s' % self.ioport_number, 'Registered.')

    def register_device(self, device_host, device_port):
        self.input_buffer = ''
        self.output_buffer = ''
        self.device_host = device_host
        self.device_port = device_port
        self.registered = True
        self.log.log('ioport %s' % self.ioport_number, 'Device[%s:%s] registered.' % (self.device_host, self.device_port))

    def unregister_device(self):
        self.log.log('ioport %s' % self.ioport_number, 'Device[%s:%s] unregistered.' % (self.device_host, self.device_port))
        self.input_buffer = ''
        self.output_buffer = ''
        self.device_host = None
        self.device_port = None
        self.registered = False

    def handle_input(self, command, argument):
        self.log.log('ioport %s' % self.ioport_number, 'Command: %s' % command)
        self.log.log('ioport %s' % self.ioport_number, 'Argument: %s' % argument)
        if command != 'DATA':
            return 400, 'ERROR: Unknown command.\n'
        if len(self.input_buffer):
            return 400, 'ERROR: Input buffer contains unread data.\n'
        if len(argument) > 6:
            return 400, 'ERROR: Cannot receive more than 256 bytes.\n'
        self.input_buffer = argument
        self.device_handler.interrupt_queue.put(self.device_handler.cpu.system_interrupts['ioport_in'][self.ioport_number])
        return 200, 'Received: %s\n' % argument
