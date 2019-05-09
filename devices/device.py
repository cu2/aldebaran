'''
Device class
'''

import json
import logging
import queue
import threading
from http import HTTPStatus

import requests

from utils.errors import AldebaranError
from utils.utils import GenericRequestHandler, GenericServer


logger = logging.getLogger(__name__)


class Device:
    '''
    Generic device class

    Can:
    - register
    - unregister
    - send data to Aldebaran
    - listen to data signals from Aldebaran

    Specific devices should subclass Device and
    - override run() to define main loop of device
    - use send_data() and send_text() to send data/text to Aldebaran
    - override handle_data() to handle data coming from Aldebaran
    '''

    def __init__(self, ioport_number, device_descriptor, aldebaran_address, device_address):
        self.ioport_number = ioport_number
        self.device_type, self.device_id = device_descriptor
        self.aldebaran_host, self.aldebaran_device_controller_port = aldebaran_address
        self.device_host, self.device_port = device_address
        self._server = GenericServer((self.device_host, self.device_port), GenericRequestHandler, self._handle_incoming_request)
        self._input_thread = threading.Thread(target=self._server.serve_forever)
        self._output_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._output_thread = threading.Thread(target=self._output_thread_run)

    def start(self):
        '''
        Start input and output threads
        '''
        logger.info('Starting...')
        self._input_thread.start()
        self._output_thread.start()
        logger.info('Started.')

    def stop(self):
        '''
        Stop input and output threads
        '''
        logger.info('Stopping...')
        self._server.shutdown()
        self._server.server_close()
        self._input_thread.join()
        self._stop_event.set()
        self._output_thread.join()
        logger.info('Stopped.')

    def register(self):
        '''
        Register device to IOPort
        '''
        logger.info('Registering...')
        response = self._send_request('register', json.dumps({
            'type': hex(self.device_type),
            'id': hex(self.device_id),
            'host': self.device_host,
            'port': self.device_port,
        }), 'application/json')
        if response.status_code != 200:
            raise RegistrationError('Could not register: {}'.format(response.text))
        logger.debug('[Aldebaran] %s', response.json()['message'])
        logger.info('Registered.')

    def unregister(self):
        '''
        Unregister device from IOPort
        '''
        logger.info('Unregistering...')
        response = self._send_request('unregister')
        if response.status_code != 200:
            raise RegistrationError('Could not unregister: {}'.format(response.text))
        logger.debug('[Aldebaran] %s', response.json()['message'])
        logger.info('Unregistered.')

    def send_data(self, data):
        '''
        Send data to IOPort
        '''
        self._output_queue.put(data)

    def send_text(self, text):
        '''
        Send text (encoded as UTF-8) to IOPort
        '''
        self.send_data(text.encode('utf-8'))

    def _handle_incoming_request(self, path, headers, rfile):
        '''
        Handle incoming request from Aldebaran, called by GenericRequestHandler
        '''
        command = path.lstrip('/')
        try:
            request_body_length = int(headers.get('Content-Length'))
        except TypeError:
            return (HTTPStatus.LENGTH_REQUIRED, None)
        data = rfile.read(request_body_length)
        return self._handle_input(command, data)

    def _handle_input(self, command, data):
        '''
        Handle command from Aldebaran
        '''
        logger.debug('Incoming command: %s', command)
        if command == 'ping':
            return (
                HTTPStatus.OK,
                {
                    'message': 'pong',
                }
            )
        if command == 'data':
            return self.handle_data(data)
        return (
            HTTPStatus.BAD_REQUEST,
            {
                'error': 'Unknown command: {}'.format(command),
            }
        )

    def handle_data(self, data):
        '''
        Handle data coming from Aldebaran

        Return (HttpStatus, json) tuple
        '''
        raise NotImplementedError()

    def run(self, args):
        '''
        Main loop
        '''
        raise NotImplementedError()

    def _output_thread_run(self):
        while True:
            try:
                data = self._output_queue.get(timeout=0.1)
            except queue.Empty:
                if self._stop_event.wait(0):
                    break
                continue
            logger.debug('Sending data...')
            response = self._send_request('data', data)
            if response.status_code != 200:
                raise CommunicationError('Could not send data: {}'.format(response.text))
            logger.debug('[Aldebaran] %s', response.json()['message'])
            logger.debug('Data sent.')

    def _send_request(self, command, data=None, content_type='application/octet-stream'):
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


# pylint: disable=missing-docstring

class DeviceError(AldebaranError):
    pass


class DeviceConnectionError(DeviceError):
    pass


class RegistrationError(DeviceError):
    pass


class CommunicationError(DeviceError):
    pass
