'''
IOPort within Device Controller
'''

import logging
import queue

logger = logging.getLogger('hardware.device_controller-ioport')


class IOPort:
    '''
    IOPort
    '''

    def __init__(self, ioport_number, input_buffer_size):
        self.ioport_number = ioport_number
        self.input_buffer_size = input_buffer_size
        self.registered = False
        self.device_host = None
        self.device_port = None
        self.input_queue = queue.Queue()
        self.device_controller = None
        self.architecture_registered = False

    def register_architecture(self, device_controller):
        '''
        Register other internal devices
        '''
        self.device_controller = device_controller
        self.architecture_registered = True

    def register_device(self, device_host, device_port):
        '''
        Register device to IOPort
        '''
        self.device_host = device_host
        self.device_port = device_port
        self.registered = True
        self._log_info('Device[%s:%s] registered.', self.device_host, self.device_port)

    def unregister_device(self):
        '''
        Unregister device from IOPort
        '''
        self._log_info('Device[%s:%s] unregistered.', self.device_host, self.device_port)  # log before emptying values
        self.device_host = None
        self.device_port = None
        self.registered = False

    def read_input(self):
        '''
        Read data from input buffer
        '''
        try:
            return self.input_queue.get_nowait()
        except queue.Empty:
            self._log_info('Reading input from empty buffer.')
            return b''

    def send_data(self, data):
        '''
        Send data to device
        '''
        if not self.registered:
            self._log_error('No device registered to IOPort %s', self.ioport_number)
            return
        self._log_debug('Sending data...')
        self.device_controller.output_queue.put((
            self.ioport_number,
            self.device_host,
            self.device_port,
            'data',
            data,
        ))
        self._log_debug('Data sent.')

    def _log_error(self, message, *args):
        self._log(logging.ERROR, message, *args)

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
