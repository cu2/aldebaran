import requests
import struct
import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

import aux
import device_handler


class Device(aux.Hardware):

    def __init__(self, aldebaran_address, ioport_number, device_descriptor, device_address, log=None):
        aux.Hardware.__init__(self, log)
        self.aldebaran_host, self.aldebaran_device_handler_port = aldebaran_address
        self.ioport_number = ioport_number
        self.device_type, self.device_id = device_descriptor
        self.device_host, self.device_port = device_address
        self.aldebaran_url = 'http://%s:%s/%s' % (self.aldebaran_host, self.aldebaran_device_handler_port, self.ioport_number)
        self.log.log('device', 'Initialized.')

    def _send_request(self, command, data=None):
        if data is None:
            data = ''
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
            r = self._send_request(device_handler.COMMAND_REGISTER, struct.pack(
                'BBBB255pH',
                self.device_type,
                self.device_id >> 16, (self.device_id >> 8) & 0xFF, self.device_id & 0xFF,
                self.device_host,
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
            r = self._send_request(device_handler.COMMAND_UNREGISTER)
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
            r = self._send_request(device_handler.COMMAND_DATA, data)
        except requests.exceptions.ConnectionError:
            self.log.log('device', 'ERROR: Disconnected from ALD.')
            return 1
        if r.status_code != 200:
            self.log.log('device', 'ERROR %s: %s' % (r.status_code, r.text))
            return 2
        self.log.log('device', '[ALD] %s' % r.text)
        self.log.log('device', 'Data sent.')
        return 0


class OutputDevice(Device):

    class RequestHandler(BaseHTTPRequestHandler):

        def do_POST(self):
            command = self.path.lstrip('/')
            self.server.log.log('device', 'Req: %s' % command)
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
            except Exception:
                self.send_response(400)  # Bad Request
                self.end_headers()
                self.wfile.write('ERROR: Cannot parse request.')
                self.wfile.write('\n')
                return
            self.server.log.log('device', 'Request(%s): %s' % (request_body_length, request_body))
            response_code, response = self.server.device.handle_input(command, request_body)
            self.send_response(response_code)
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, format, *args):
            return

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, request_handler, device, log):
            HTTPServer.__init__(self, server_address, request_handler)
            self.device = device
            self.log = log
            self.daemon_threads = True

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
        return 200, 'Ok\n'
