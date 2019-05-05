'''
IOPort within Device Controller
'''

import logging
import queue

from utils import utils

logger = logging.getLogger('hardware.device_controller-ioport')


class IOPort:
    '''
    IOPort
    '''

    def __init__(self, ioport_number):
        self.ioport_number = ioport_number
        self.registered = False
        self.device_host = None
        self.device_port = None
        self.input_queue = queue.Queue()
        self.input_buffer = b''
        self.device_controller = None

    def register_architecture(self, device_controller):
        '''
        Register other internal devices
        '''
        self.device_controller = device_controller

    def register_device(self, device_host, device_port):
        '''
        Register device to IOPort
        '''
        self.input_buffer = b''
        self.device_host = device_host
        self.device_port = device_port
        self.registered = True
        self._log_info('Device[%s:%s] registered.', self.device_host, self.device_port)

    def unregister_device(self):
        '''
        Unregister device from IOPort
        '''
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
        logger.log(level, full_message, *args)
