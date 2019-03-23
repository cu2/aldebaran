import requests
import struct
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import aux
import config
import device_controller


class Device(aux.Hardware):
    '''
    Generic device class

    Can:
    - register
    - unregister
    - send data to ALD
    - listen to "ack" and "data" signals from ALD

    Specific devices should subclass Device and
    - override run() to define main loop of device
    - use send_data() and send_text() for ALD-input
    - override handle_ack() for ack of ALD-input
    - override handle_data() for ALD-output
    '''

    class RequestHandler(BaseHTTPRequestHandler):

        def _writeline(self, text):
            self.wfile.write(text.encode('utf-8'))
            self.wfile.write('\n'.encode('utf-8'))

        def do_POST(self):
            command = self.path.lstrip('/')
            self.server.log.log('device', 'Req: %s' % command)
            try:
                request_body_length = int(self.headers.get('content-length'))
            except TypeError:
                self.send_response(411)  # Length Required
                self.end_headers()
                self._writeline('ERROR: Header "content-length" missing.')
                return
            try:
                request_body = self.rfile.read(request_body_length)
            except Exception:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self._writeline('ERROR: Cannot parse request.')
                return
            self.server.log.log('device', 'Request(%s): %s' % (request_body_length, request_body))
            response_code, response_text = self.server.device.handle_input(command, request_body)
            self.send_response(response_code)
            self.end_headers()
            self.wfile.write(response_text.encode('utf-8'))

        def log_message(self, format, *args):
            return

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, request_handler, device, log):
            HTTPServer.__init__(self, server_address, request_handler)
            self.device = device
            self.log = log
            self.daemon_threads = True

    def __init__(self, ioport_number, device_descriptor, aldebaran_address=None, device_address=None, log=None):
        aux.Hardware.__init__(self, log)
        self.ioport_number = ioport_number
        self.device_type, self.device_id = device_descriptor
        if aldebaran_address is None:
            self.aldebaran_host, self.aldebaran_device_controller_port = config.aldebaran_host, config.aldebaran_base_port + config.device_controller_port
        else:
            self.aldebaran_host, self.aldebaran_device_controller_port = aldebaran_address
        if device_address is None:
            self.device_host, self.device_port = config.device_host, config.device_base_port + ioport_number
        else:
            self.device_host, self.device_port = device_address
        self.aldebaran_url = 'http://%s:%s/%s' % (self.aldebaran_host, self.aldebaran_device_controller_port, self.ioport_number)
        self.log.log('device', 'Initialized.')

    def _send_request(self, command, data=None):
        if data is None:
            data = b''
        r = requests.post(
            self.aldebaran_url,
            data=struct.pack('B', command) + data,
            headers={'content-type': 'application/octet-stream'},
        )
        self.log.log('device', 'Request sent.')
        return r

    def register(self):
        self.log.log('device', 'Registering...')
        try:
            r = self._send_request(device_controller.COMMAND_REGISTER, struct.pack(
                'BBBB255pH',
                self.device_type,
                self.device_id >> 16, (self.device_id >> 8) & 0xFF, self.device_id & 0xFF,
                self.device_host.encode('utf-8'),
                self.device_port,
            ))
        except requests.exceptions.ConnectionError:
            self.log.log('device', 'ERROR: Cannot connect to ALD.')
            return 1
        if r.status_code != 200:
            self.log.log('device', 'ERROR %s: %s' % (r.status_code, r.text))
            return 2
        self.log.log('device', '[ALD] %s' % r.text)
        self.log.log('device', 'Registered.')
        return 0

    def unregister(self):
        self.log.log('device', 'Unregistering...')
        try:
            r = self._send_request(device_controller.COMMAND_UNREGISTER)
        except requests.exceptions.ConnectionError:
            self.log.log('device', 'ERROR: Disconnected from ALD.')
            return 1
        if r.status_code != 200:
            self.log.log('device', 'ERROR %s: %s' % (r.status_code, r.text))
            return 2
        self.log.log('device', '[ALD] %s' % r.text)
        self.log.log('device', 'Unregistered.')
        return 0

    def send_data(self, data):
        self.log.log('device', 'Sending data...')
        try:
            r = self._send_request(device_controller.COMMAND_DATA, data)
        except requests.exceptions.ConnectionError:
            self.log.log('device', 'ERROR: Disconnected from ALD.')
            return 1
        if r.status_code != 200:
            self.log.log('device', 'ERROR %s: %s' % (r.status_code, r.text))
            return 2
        self.log.log('device', '[ALD] %s' % r.text)
        self.log.log('device', 'Data sent.')
        return 0

    def send_text(self, text):
        return self.send_data(text.encode('utf-8'))

    def start(self):
        self.log.log('device', 'Starting...')
        self.server = self.Server((self.device_host, self.device_port), self.RequestHandler, self, self.log)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.log.log('device', 'Started.')
        return 0

    def stop(self):
        self.log.log('device', 'Stopping...')
        self.server.shutdown()
        self.log.log('device', 'Stopped.')

    def handle_input(self, command, data):
        if command == 'ack':
            return self.handle_ack()
        if command == 'data':
            return self.handle_data(data)
        self.log.log('device', 'ERROR: unknown command %s.' % command)
        return 400, 'Unknown command\n'

    def handle_ack(self):
        self.log.log('device', 'Acknowledged by ALD.')
        return 200, 'Ok\n'

    def handle_data(self, data):
        self.log.log('device', 'Data from ALD: %s' % data.decode('utf-8'))
        return 200, 'Ok\n'

    def run(self, args):
        pass
