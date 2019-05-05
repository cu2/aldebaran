'''
Device class
'''

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from utils.errors import AldebaranError


logger = logging.getLogger(__name__)


class Device:
    '''
    Generic device class

    Can:
    - register
    - unregister
    - send data to ALD
    - listen to "data" signals from ALD

    Specific devices should subclass Device and
    - override run() to define main loop of device
    - use send_data() and send_text() for ALD-input
    - override handle_data() for ALD-output
    '''

    def __init__(self, ioport_number, device_descriptor, aldebaran_address, device_address):
        self.ioport_number = ioport_number
        self.device_type, self.device_id = device_descriptor
        self.aldebaran_host, self.aldebaran_device_controller_port = aldebaran_address
        self.device_host, self.device_port = device_address
        self._server = Server((self.device_host, self.device_port), RequestHandler, self)
        self._input_thread = threading.Thread(target=self._server.serve_forever)

    def start(self):
        '''
        Start input and output threads
        '''
        logger.info('Starting...')
        self._input_thread.start()
        logger.info('Started.')

    def stop(self):
        '''
        Stop input and output threads
        '''
        logger.info('Stopping...')
        self._server.shutdown()
        self._server.server_close()
        self._input_thread.join()
        logger.info('Stopped.')

    def register(self):
        '''
        Register device to IOPort
        '''
        logger.info('Registering...')
        response = self._send_request('register', 'application/json', json.dumps({
            'type': hex(self.device_type),
            'id': hex(self.device_id),
            'host': self.device_host,
            'port': self.device_port,
        }))
        if response.status_code != 200:
            raise RegistrationError('Could not register: {}'.format(response.text))
        logger.debug('[ALD] %s', response.json()['message'])
        logger.info('Registered.')
        return 0

    def unregister(self):
        '''
        Unregister device from IOPort
        '''
        logger.info('Unregistering...')
        response = self._send_request('unregister')
        if response.status_code != 200:
            raise RegistrationError('Could not unregister: {}'.format(response.text))
        logger.debug('[ALD] %s', response.json()['message'])
        logger.info('Unregistered.')
        return 0

    def send_data(self, data):
        '''
        Send data to IOPort
        '''
        logger.debug('Sending data...')
        response = self._send_request('data', data=data)
        if response.status_code != 200:
            raise RegistrationError('Could not send data: {}'.format(response.text))
        logger.debug('[ALD] %s', response.json()['message'])
        logger.debug('Data sent.')
        return 0

    def send_text(self, text):
        '''
        Send text (encoded as UTF-8) to IOPort
        '''
        return self.send_data(text.encode('utf-8'))

    def handle_input(self, command, data):
        '''
        Handle request from Aldebaran
        '''
        if command == 'data':
            return self.handle_data(data)
        logger.debug('ERROR: unknown command %s.', command)
        return 400, 'Unknown command\n'

    def handle_data(self, data):
        '''
        Handle data coming from Aldebaran
        '''
        raise NotImplementedError()

    def run(self, args):
        '''
        Main loop
        '''
        raise NotImplementedError()

    def _send_request(self, command, content_type='application/octet-stream', data=None):
        if data is None:
            data = b''
        try:
            response = requests.post(
                'http://{}:{}/{}/{}'.format(
                    self.aldebaran_host,
                    self.aldebaran_device_controller_port,
                    self.ioport_number,
                    command,
                ),
                data=data,
                headers={'Content-Type': content_type},
            )
        except requests.exceptions.ConnectionError:
            raise DeviceConnectionError('Could not connect to Aldebaran.')
        logger.debug('Request sent.')
        return response


class RequestHandler(BaseHTTPRequestHandler):
    '''
    Device's request handler
    '''

    def _writeline(self, text):
        self.wfile.write(text.encode('utf-8'))
        self.wfile.write('\n'.encode('utf-8'))

    def do_POST(self):
        '''
        Handle incoming request from Aldebaran
        '''
        command = self.path.lstrip('/')
        logger.debug('Req: %s', command)
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
        logger.debug('Request(%d): %s', request_body_length, request_body)
        response_code, response_text = self.server.device.handle_input(command, request_body)
        self.send_response(response_code)
        self.end_headers()
        self.wfile.write(response_text.encode('utf-8'))

    def log_message(self, format, *args):
        '''
        Turn off logging of BaseHTTPRequestHandler
        '''


class Server(HTTPServer):
    '''
    Device's server
    '''

    def __init__(self, server_address, request_handler, device):
        HTTPServer.__init__(self, server_address, request_handler)
        self.device = device


# pylint: disable=missing-docstring

class DeviceError(AldebaranError):
    pass


class DeviceConnectionError(DeviceError):
    pass


class RegistrationError(DeviceError):
    pass
