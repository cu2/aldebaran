'''
Device Controller to handle devices
'''

import json
import logging
import queue
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from utils import utils
from utils.errors import AldebaranError, ArchitectureError
from hardware.memory.memory import SegfaultError


logger = logging.getLogger('hardware.device_controller')


class DeviceController:
    '''
    Device Controller
    '''

    def __init__(self, host, port, system_addresses, system_interrupts, ioports):
        self.system_addresses = system_addresses
        self.system_interrupts = system_interrupts
        self._device_registry = [0] * system_addresses['device_registry_size']
        self._device_status_table = [0] * system_addresses['device_status_table_size']
        self.output_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._server = Server((host, port), RequestHandler, self)
        self._input_thread = threading.Thread(target=self._server.serve_forever)
        self._output_thread = threading.Thread(target=self._output_thread_run)

        self.ioports = ioports
        self.interrupt_controller = None
        self.architecture_registered = False

    def register_architecture(self, interrupt_controller):
        '''
        Register other internal devices
        '''
        self.interrupt_controller = interrupt_controller
        for ioport in self.ioports:
            ioport.register_architecture(self)
        self.architecture_registered = True

    def start(self):
        '''
        Start input and output threads
        '''
        if not self.architecture_registered:
            raise ArchitectureError('Device Controller cannot run without registering architecture')
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

    def read_byte(self, pos, silent=False):
        '''
        Read byte from device registry or device status table
        '''
        if self.system_addresses['device_registry_address'] <= pos < self.system_addresses['device_registry_address'] + self.system_addresses['device_registry_size']:
            value = self._device_registry[pos - self.system_addresses['device_registry_address']]
        elif self.system_addresses['device_status_table_address'] <= pos < self.system_addresses['device_status_table_address'] + self.system_addresses['device_status_table_size']:
            value = self._device_status_table[pos - self.system_addresses['device_status_table_address']]
        else:
            raise SegfaultError('Segmentation fault when trying to read byte at {}'.format(utils.word_to_str(pos)))
        if not silent:
            logger.debug('Read byte %s from %s.', utils.byte_to_str(value), utils.word_to_str(pos))
        return value

    def write_byte(self, pos, value, silent=False):
        '''
        Cannot write to device registry device status table
        '''
        raise SegfaultError('Segmentation fault when trying to write byte at {}'.format(utils.word_to_str(pos)))

    def read_word(self, pos, silent=False):
        '''
        Read word from device registry or device status table
        '''
        if self.system_addresses['device_registry_address'] <= pos < self.system_addresses['device_registry_address'] + self.system_addresses['device_registry_size'] - 1:
            relative_pos = pos - self.system_addresses['device_registry_address']
            value = (self._device_registry[relative_pos] << 8) + self._device_registry[relative_pos + 1]
        elif self.system_addresses['device_status_table_address'] <= pos < self.system_addresses['device_status_table_address'] + self.system_addresses['device_status_table_size'] - 1:
            relative_pos = pos - self.system_addresses['device_status_table_address']
            value = (self._device_status_table[relative_pos] << 8) + self._device_status_table[relative_pos + 1]
        else:
            raise SegfaultError('Segmentation fault when trying to read word at {}'.format(utils.word_to_str(pos)))
        if not silent:
            logger.debug('Read word %s from %s.', utils.word_to_str(value), utils.word_to_str(pos))
        return value

    def write_word(self, pos, value, silent=False):
        '''
        Cannot write to device registry device status table
        '''
        raise SegfaultError('Segmentation fault when trying to write word at {}'.format(utils.word_to_str(pos)))

    def _output_thread_run(self):
        while True:
            try:
                ioport_number, device_host, device_port, command, data = self.output_queue.get(timeout=1)
            except queue.Empty:
                if self._stop_event.wait(0):
                    break
                continue
            logger.debug('Command "%s" from IOPort %s', command, ioport_number)
            if command == 'data':
                response = self._send_request(device_host, device_port, 'data', data=data)
                if response.status_code != 200:
                    raise DeviceError('Could not send data: {}'.format(response.text))
                logger.debug('[Device] %s', response.json()['message'])
            else:
                logger.error('Unknown command')

    def _send_request(self, device_host, device_port, command, content_type='application/octet-stream', data=None):
        if data is None:
            data = b''
        try:
            response = requests.post(
                'http://{}:{}/{}'.format(
                    device_host,
                    device_port,
                    command,
                ),
                data=data,
                headers={'Content-Type': content_type},
            )
        except requests.exceptions.ConnectionError:
            raise DeviceControllerConnectionError('Could not connect to Aldebaran.')
        logger.debug('Request sent.')
        return response

    def handle_input(self, ioport_number, command, data):
        '''
        Handle request from device
        '''
        logger.debug('Incoming command "%s" to IOPort %s', command, ioport_number)
        if command == 'register':
            return self._register_device(ioport_number, data)
        if command == 'unregister':
            return self._unregister_device(ioport_number)
        if command == 'ping':
            return (
                HTTPStatus.OK,
                {
                    'message': 'pong',
                }
            )
        if command == 'data':
            return self._send_data_to_ioport(ioport_number, data)
        return (
            HTTPStatus.BAD_REQUEST,
            {
                'error': 'Unknown command: {}'.format(command),
            }
        )

    def _send_data_to_ioport(self, ioport_number, data):
        if not self.ioports[ioport_number].registered:
            logger.info('No device is registered to IOPort %s.', ioport_number)
            return (
                HTTPStatus.FORBIDDEN,
                {
                    'error': 'No device is registered to this IOPort.',
                }
            )
        if len(data) > self.ioports[ioport_number].input_buffer_size:
            logger.info('Too much data sent to IOPort %s.', ioport_number)
            return (
                HTTPStatus.FORBIDDEN,
                {
                    'error': 'Too much data sent.',
                }
            )

        self.ioports[ioport_number].input_queue.put(data)
        logger.info('Delivered data to IOPort %s.', ioport_number)
        self.interrupt_controller.send(self.system_interrupts['ioport_in'][ioport_number])
        return (
            HTTPStatus.OK,
            {
                'message': 'Received data: {}'.format(utils.binary_to_str(data)),
            }
        )

    def _register_device(self, ioport_number, data):
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    'error': 'Could not parse data.',
                }
            )
        for field_name in {'type', 'id', 'host', 'port'}:
            if field_name not in data:
                return (
                    HTTPStatus.BAD_REQUEST,
                    {
                        'error': 'Field "{}" missing.'.format(field_name),
                    }
                )
        try:
            device_type = int(data['type'], 16)
            if device_type < 0x00 or device_type > 0xFF:
                raise ValueError()
        except ValueError:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    'error': 'Device type must be a 1-byte hex number.',
                }
            )
        try:
            device_id = int(data['id'], 16)
            if device_id < 0x00 or device_id > 0xFFFFFF:
                raise ValueError()
            device_id = list(device_id.to_bytes(3, 'big'))
        except ValueError:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    'error': 'Device ID must be a 1-byte hex number.',
                }
            )
        device_host, device_port = data['host'], data['port']
        if self.ioports[ioport_number].registered:
            logger.info('A device is already registered to IOPort %s.', ioport_number)
            return (
                HTTPStatus.FORBIDDEN,
                {
                    'error': 'A device is already registered to this IOPort.',
                }
            )
        if self.ioports[ioport_number].input_queue.qsize() > 0:
            logger.info('IOPort %s input queue not empty.', ioport_number)
            return (
                HTTPStatus.FORBIDDEN,
                {
                    'error': 'IOPort input queue not empty.',
                }
            )

        logger.info('Registering device to IOPort %s...', ioport_number)
        logger.info(
            'Device type and ID: %s %s',
            utils.byte_to_str(device_type),
            ' '.join(utils.byte_to_str(device_id[i]) for i in range(3)),
        )
        logger.info('Device host and port: %s:%s', device_host, device_port)
        self._device_registry[4 * ioport_number] = device_type
        for idx in range(3):
            self._device_registry[4 * ioport_number + 1 + idx] = device_id[idx]
        self._device_status_table[ioport_number] = 0
        self.ioports[ioport_number].register_device(device_host, device_port)
        self.interrupt_controller.send(self.system_interrupts['device_registered'])
        logger.info('Device registered to IOPort %s.', ioport_number)
        return (
            HTTPStatus.OK,
            {
                'message': 'Device registered.',
            }
        )

    def _unregister_device(self, ioport_number):
        if not self.ioports[ioport_number].registered:
            logger.info('No device is registered to IOPort %s.', ioport_number)
            return (
                HTTPStatus.FORBIDDEN,
                {
                    'error': 'No device is registered to this IOPort.',
                }
            )

        logger.info('Unregistering device from IOPort %s...', ioport_number)
        for idx in range(4):
            self._device_registry[4 * ioport_number + idx] = 0
        self._device_status_table[ioport_number] = 0
        self.ioports[ioport_number].unregister_device()
        self.interrupt_controller.send(self.system_interrupts['device_unregistered'])
        logger.info('Device unregistered from IOPort %s.', ioport_number)
        return (
            HTTPStatus.OK,
            {
                'message': 'Device unregistered.',
            }
        )


class RequestHandler(BaseHTTPRequestHandler):
    '''
    Device Controller's request handler
    '''

    def do_POST(self):
        '''
        Handle incoming request from devices
        '''
        max_ioport_number = len(self.server.device_controller.ioports) - 1
        path = self.path.lstrip('/')
        if '/' not in path:
            self._send_json(HTTPStatus.BAD_REQUEST, {
                'error': 'Path must be /ioport/command',
            })
            return
        ioport_number, command = path.split('/', 1)
        try:
            ioport_number = int(ioport_number)
            if ioport_number < 0:
                raise ValueError()
            if ioport_number > max_ioport_number:
                raise ValueError()
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {
                'error': 'IOPort number must be an integer between 0 and {}.'.format(max_ioport_number)
            })
            return
        try:
            request_body_length = int(self.headers.get('Content-Length'))
        except TypeError:
            self._send_json(HTTPStatus.LENGTH_REQUIRED)
            return
        data = self.rfile.read(request_body_length)
        status, json_response = self.server.device_controller.handle_input(ioport_number, command, data)
        self._send_json(status, json_response)

    def log_message(self, format, *args):
        '''
        Turn off logging of BaseHTTPRequestHandler
        '''

    def _send_json(self, status, json_response=None):
        self.send_response(status.value)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        if json_response is not None:
            self.wfile.write(json.dumps(json_response).encode('utf-8'))
            self.wfile.write(b'\n')


class Server(HTTPServer):
    '''
    Device Controller's server
    '''

    def __init__(self, server_address, request_handler, device_controller):
        HTTPServer.__init__(self, server_address, request_handler)
        self.device_controller = device_controller


# pylint: disable=missing-docstring

class DeviceControllerError(AldebaranError):
    pass


class DeviceControllerConnectionError(DeviceControllerError):
    pass


class DeviceError(DeviceControllerError):
    pass