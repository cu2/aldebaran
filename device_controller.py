import queue
import requests
import struct
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import aux


COMMAND_REGISTER = 0
COMMAND_UNREGISTER = 1
COMMAND_DATA = 2


class DeviceController(aux.Hardware):

    class RequestHandler(BaseHTTPRequestHandler):

        def _writeline(self, text):
            self.wfile.write(text.encode('utf-8'))
            self.wfile.write('\n'.encode('utf-8'))

        def do_POST(self):
            ioport_number = self.path.lstrip('/')
            self.server.log.log('device_controller', 'Incoming signal to IOPort %s' % ioport_number)
            try:
                ioport_number = int(ioport_number)
                if ioport_number < 0:
                    raise ValueError
                if ioport_number >= len(self.server.ioports):
                    raise ValueError
            except ValueError:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self._writeline('ERROR: IOPort number must be an integer between 0 and %s.' % (len(self.server.ioports) - 1))
                return
            try:
                request_body_length = int(self.headers.get('content-length'))
            except TypeError:
                self.send_response(411)  # Length Required
                self.end_headers()
                self._writeline('ERROR: Header "content-length" missing.')
                return
            try:
                request_body = self.rfile.read(request_body_length)
                command, argument = struct.unpack('B', request_body[:1])[0], request_body[1:]
            except Exception:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self._writeline('ERROR: Cannot parse request.')
                return
            if command == COMMAND_REGISTER:
                self.register_device(ioport_number, argument)
                return
            if command == COMMAND_UNREGISTER:
                self.unregister_device(ioport_number)
                return
            if not self.server.ioports[ioport_number].registered:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self._writeline('ERROR: IOPort %s is not yet registered.' % ioport_number)
                return
            response_code, response_text = self.server.ioports[ioport_number].handle_input(command, argument)
            self.send_response(response_code)
            self.end_headers()
            self.wfile.write(response_text.encode('utf-8'))

        def log_message(self, format, *args):
            return

        def register_device(self, ioport_number, argument):
            device_id = [0, 0, 0]
            try:
                device_type, device_id[0], device_id[1], device_id[2], device_host, device_port = struct.unpack('BBBB255pH', argument)
                device_host = device_host.decode('utf-8')
            except Exception:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self._writeline('ERROR: Cannot parse argument.')
                return
            self.server.log.log('device_controller', 'Registering device to IOPort %s...' % ioport_number)
            self.server.log.log('device_controller', 'Device type and ID: %s %s' % (
                aux.byte_to_str(device_type),
                ' '.join([aux.byte_to_str(device_id[i]) for i in range(3)])
            ))
            self.server.log.log('device_controller', 'Device host and port: %s:%s' % (device_host, device_port))
            self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number, device_type)
            for i in range(3):
                self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number + 1 + i, device_id[i])
            self.server.ioports[ioport_number].register_device(device_host, device_port)
            self.server.interrupt_controller.send(self.server.system_interrupts['device_registered'])
            self.send_response(200)
            self.end_headers()
            self._writeline('Device registered to IOPort %s.' % ioport_number)
            self.server.log.log('device_controller', 'Device registered to IOPort %s.' % ioport_number)

        def unregister_device(self, ioport_number):
            self.server.log.log('device_controller', 'Unregistering device from IOPort %s...' % ioport_number)
            self.server.ram.write_word(self.server.device_registry_address + 4 * ioport_number, 0)
            self.server.ram.write_word(self.server.device_registry_address + 4 * ioport_number + 2, 0)
            self.server.ioports[ioport_number].unregister_device()
            self.server.interrupt_controller.send(self.server.system_interrupts['device_unregistered'])
            self.send_response(200)
            self.end_headers()
            self._writeline('Device unregistered from IOPort %s.' % ioport_number)
            self.server.log.log('device_controller', 'Device unregistered from IOPort %s.' % ioport_number)

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, device_registry_address, ioports, request_handler, system_interrupts, interrupt_controller, ram, log):
            HTTPServer.__init__(self, server_address, request_handler)
            self.device_registry_address = device_registry_address
            self.ioports = ioports
            self.system_interrupts = system_interrupts
            self.interrupt_controller = interrupt_controller
            self.ram = ram
            self.log = log
            self.daemon_threads = True

    def __init__(self, host, port, system_addresses, system_interrupts, ioports, log=None):
        aux.Hardware.__init__(self, log)
        self.address = (host, port)
        self.device_status_table = system_addresses['device_status_table']
        self.device_registry_address = system_addresses['device_registry_address']
        self.ioports = ioports
        self.system_interrupts = system_interrupts
        self.output_queue = queue.Queue()
        self.interrupt_controller = None
        self.ram = None
        self.architecture_registered = False

    def register_architecture(self, interrupt_controller, ram):
        self.interrupt_controller = interrupt_controller
        self.ram = ram
        for ioport in self.ioports:
            ioport.register_architecture(self)
        self.architecture_registered = True

    def output_thread_run(self):
        while True:
            ioport_number, target_host, target_port, query, data = self.output_queue.get()
            url = 'http://%s:%s/%s' % (target_host, target_port, query)
            self.log.log('device_controller', 'Sending query to %s...' % url)
            output_status = 1
            try:
                r = requests.post(
                    url=url,
                    data=data,
                    headers={'content-type': 'application/octet-stream'},
                )
                self.log.log('device_controller', 'Response: %s' % r.text)
                if r.status_code == 200:
                    output_status = 0
            except Exception as e:
                self.log.log('device_controller', 'Error sending query: %s' % e)
            if query == 'data':
                self.ram.write_word(self.device_status_table + ioport_number, output_status)
                self.interrupt_controller.send(self.system_interrupts['ioport_out'][ioport_number])

    def start(self):
        if not self.architecture_registered:
            self.log.log('device_controller', 'ERROR: Cannot run without registering architecture.')
            return 1
        self.log.log('device_controller', 'Starting...')
        self.server = self.Server(self.address, self.device_registry_address, self.ioports, self.RequestHandler, self.system_interrupts, self.interrupt_controller, self.ram, self.log)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.output_thread = threading.Thread(target=self.output_thread_run)
        self.output_thread.daemon = True
        self.output_thread.start()
        self.log.log('device_controller', 'Started.')
        return 0

    def stop(self):
        self.log.log('device_controller', 'Stopping...')
        self.server.shutdown()
        self.log.log('device_controller', 'Stopped.')


class IOPort(aux.Hardware):

    def __init__(self, ioport_number, log=None):
        aux.Hardware.__init__(self, log)
        self.ioport_number = ioport_number
        self.registered = False
        self.device_host = None
        self.device_port = None
        self.input_buffer = b''
        self.device_controller = None
        self.log.log('ioport %s' % self.ioport_number, 'Created.')

    def register_architecture(self, device_controller):
        self.device_controller = device_controller
        self.log.log('ioport %s' % self.ioport_number, 'Registered.')

    def register_device(self, device_host, device_port):
        self.input_buffer = b''
        self.device_host = device_host
        self.device_port = device_port
        self.registered = True
        self.log.log('ioport %s' % self.ioport_number, 'Device[%s:%s] registered.' % (self.device_host, self.device_port))

    def unregister_device(self):
        self.log.log('ioport %s' % self.ioport_number, 'Device[%s:%s] unregistered.' % (self.device_host, self.device_port))
        self.input_buffer = b''
        self.device_host = None
        self.device_port = None
        self.registered = False

    def handle_input(self, command, argument):
        if command != COMMAND_DATA:
            return 400, 'ERROR: Unknown command.\n'
        self.log.log('ioport %s' % self.ioport_number, 'Command: DATA')
        self.log.log('ioport %s' % self.ioport_number, 'Argument: %s' % aux.binary_to_str(argument))
        if len(self.input_buffer):
            self.log.log('ioport %s' % self.ioport_number, 'ERROR: Input buffer contains unread data.')
            return 400, 'ERROR: Input buffer contains unread data.\n'
        if len(argument) > 255:
            self.log.log('ioport %s' % self.ioport_number, 'ERROR: Cannot receive more than 255 bytes.')
            return 400, 'ERROR: Cannot receive more than 255 bytes.\n'
        self.input_buffer = argument
        self.device_controller.interrupt_controller.send(self.device_controller.system_interrupts['ioport_in'][self.ioport_number])
        return 200, 'Received: %s (%s bytes)\n' % (aux.binary_to_str(argument), len(argument))

    def read_input(self):
        value = self.input_buffer
        self.input_buffer = b''
        self._send_ack()
        return value

    def send_output(self, value):
        self.log.log('ioport %s' % self.ioport_number, 'Sending output...')
        self.device_controller.output_queue.put((
            self.ioport_number,
            self.device_host,
            self.device_port,
            'data',
            value,
        ))
        self.log.log('ioport %s' % self.ioport_number, 'Output sent.')
        return value

    def _send_ack(self):
        self.log.log('ioport %s' % self.ioport_number, 'Sending ACK...')
        self.device_controller.output_queue.put((
            self.ioport_number,
            self.device_host,
            self.device_port,
            'ack',
            b'ACK',
        ))
        self.log.log('ioport %s' % self.ioport_number, 'ACK sent.')
