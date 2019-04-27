import logging
import queue
import requests
import struct
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from utils import utils


logger = logging.getLogger(__name__)
logger_ioport = logging.getLogger(__name__ + '-ioport')


COMMAND_REGISTER = 0
COMMAND_UNREGISTER = 1
COMMAND_DATA = 2


class DeviceController:

    class RequestHandler(BaseHTTPRequestHandler):

        def _writeline(self, text):
            self.wfile.write(text.encode('utf-8'))
            self.wfile.write('\n'.encode('utf-8'))

        def do_POST(self):
            ioport_number = self.path.lstrip('/')
            logger.debug('Incoming signal to IOPort %s', ioport_number)
            try:
                ioport_number = int(ioport_number)
                if ioport_number < 0:
                    raise ValueError()
                if ioport_number >= len(self.server.ioports):
                    raise ValueError()
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
            '''
            Turn off logging of BaseHTTPRequestHandler
            '''

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
            logger.info('Registering device to IOPort %s...', ioport_number)
            logger.info(
                'Device type and ID: %s %s',
                utils.byte_to_str(device_type),
                ' '.join([utils.byte_to_str(device_id[i]) for i in range(3)],
            ))
            logger.info('Device host and port: %s:%s', device_host, device_port)
            self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number, device_type)
            for i in range(3):
                self.server.ram.write_byte(self.server.device_registry_address + 4 * ioport_number + 1 + i, device_id[i])
            self.server.ioports[ioport_number].register_device(device_host, device_port)
            self.server.interrupt_controller.send(self.server.system_interrupts['device_registered'])
            self.send_response(200)
            self.end_headers()
            self._writeline('Device registered to IOPort %s.' % ioport_number)
            logger.info('Device registered to IOPort %s.', ioport_number)

        def unregister_device(self, ioport_number):
            logger.info('Unregistering device from IOPort %s...', ioport_number)
            self.server.ram.write_word(self.server.device_registry_address + 4 * ioport_number, 0)
            self.server.ram.write_word(self.server.device_registry_address + 4 * ioport_number + 2, 0)
            self.server.ioports[ioport_number].unregister_device()
            self.server.interrupt_controller.send(self.server.system_interrupts['device_unregistered'])
            self.send_response(200)
            self.end_headers()
            self._writeline('Device unregistered from IOPort %s.' % ioport_number)
            logger.info('Device unregistered from IOPort %s.', ioport_number)

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, device_registry_address, ioports, request_handler, system_interrupts, interrupt_controller, ram):
            HTTPServer.__init__(self, server_address, request_handler)
            self.device_registry_address = device_registry_address
            self.ioports = ioports
            self.system_interrupts = system_interrupts
            self.interrupt_controller = interrupt_controller
            self.ram = ram
            self.daemon_threads = True

    def __init__(self, host, port, system_addresses, system_interrupts, ioports):
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
            logger.debug('Sending query to %s...', url)
            output_status = 1
            try:
                r = requests.post(
                    url=url,
                    data=data,
                    headers={'content-type': 'application/octet-stream'},
                )
                logger.debug('Response: %s', r.text)
                if r.status_code == 200:
                    output_status = 0
            except Exception as e:
                logger.debug('Error sending query: %s', e)
            if query == 'data':
                self.ram.write_word(self.device_status_table + ioport_number, output_status)
                self.interrupt_controller.send(self.system_interrupts['ioport_out'][ioport_number])

    def start(self):
        if not self.architecture_registered:
            logger.info('ERROR: Cannot run without registering architecture.')
            return 1
        logger.info('Starting...')
        self.server = self.Server(self.address, self.device_registry_address, self.ioports, self.RequestHandler, self.system_interrupts, self.interrupt_controller, self.ram)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.output_thread = threading.Thread(target=self.output_thread_run)
        self.output_thread.daemon = True
        self.output_thread.start()
        logger.info('Started.')
        return 0

    def stop(self):
        logger.info('Stopping...')
        self.server.shutdown()
        logger.info('Stopped.')


class IOPort:

    def __init__(self, ioport_number):
        self.ioport_number = ioport_number
        self.registered = False
        self.device_host = None
        self.device_port = None
        self.input_buffer = b''
        self.device_controller = None

    def register_architecture(self, device_controller):
        self.device_controller = device_controller

    def register_device(self, device_host, device_port):
        self.input_buffer = b''
        self.device_host = device_host
        self.device_port = device_port
        self.registered = True
        self._log_info('Device[%s:%s] registered.', self.device_host, self.device_port)

    def unregister_device(self):
        self._log_info('Device[%s:%s] unregistered.', self.device_host, self.device_port)
        self.input_buffer = b''
        self.device_host = None
        self.device_port = None
        self.registered = False

    def handle_input(self, command, argument):
        if command != COMMAND_DATA:
            return 400, 'ERROR: Unknown command.\n'
        self._log_debug('Command: DATA')
        self._log_debug('Argument: %s', utils.binary_to_str(argument))
        if len(self.input_buffer):
            self._log_debug('ERROR: Input buffer contains unread data.')
            return 400, 'ERROR: Input buffer contains unread data.\n'
        if len(argument) > 255:
            self._log_debug('ERROR: Cannot receive more than 255 bytes.')
            return 400, 'ERROR: Cannot receive more than 255 bytes.\n'
        self.input_buffer = argument
        self.device_controller.interrupt_controller.send(self.device_controller.system_interrupts['ioport_in'][self.ioport_number])
        return 200, 'Received: %s (%s bytes)\n' % (utils.binary_to_str(argument), len(argument))

    def read_input(self):
        value = self.input_buffer
        self.input_buffer = b''
        self._send_ack()
        return value

    def send_output(self, value):
        self._log_debug('Sending output...')
        self.device_controller.output_queue.put((
            self.ioport_number,
            self.device_host,
            self.device_port,
            'data',
            value,
        ))
        self._log_debug('Output sent.')
        return value

    def _send_ack(self):
        self._log_debug('Sending ACK...')
        self.device_controller.output_queue.put((
            self.ioport_number,
            self.device_host,
            self.device_port,
            'ack',
            b'ACK',
        ))
        self._log_debug('ACK sent.')

    def _log_info(self, message, *args):
        self._log(logging.INFO, message, *args)

    def _log_debug(self, message, *args):
        self._log(logging.DEBUG, message, *args)

    def _log(self, level, message, *args):
        full_message = '[IOPort {}] {}'.format(
            self.ioport_number,
            message,
        )
        logger_ioport.log(level, full_message, *args)
