'''
Debugger to show Aldebaran's internal state
'''

import logging
import threading
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs

from instructions.operands import WORD_REGISTERS
from utils import utils
from utils.errors import ArchitectureError
from utils.utils import GenericRequestHandler, GenericServer


logger = logging.getLogger(__name__)


class Debugger:
    '''
    Debugger

    API endpoints:
        GET /cpu
        GET /memory?offset=&length=
        GET /stack
    '''

    def __init__(self, host, port):
        self._server = GenericServer((host, port), GenericRequestHandler, self._handle_incoming_request, None)
        self._input_thread = threading.Thread(target=self._server.serve_forever)

        self.cpu = None
        self.memory = None
        self.architecture_registered = False

    def register_architecture(self, cpu, memory):
        '''
        Register other internal devices
        '''
        self.cpu = cpu
        self.memory = memory
        self.architecture_registered = True

    def start(self):
        '''
        Start input thread
        '''
        if not self.architecture_registered:
            raise ArchitectureError('Debugger cannot run without registering architecture')
        logger.info('Starting...')
        self._input_thread.start()
        logger.info('Started.')

    def stop(self):
        '''
        Stop input thread
        '''
        logger.info('Stopping...')
        self._server.shutdown()
        self._server.server_close()
        self._input_thread.join()
        logger.info('Stopped.')

    def _handle_incoming_request(self, path):
        '''
        Handle incoming request from Debugger frontend, called by GenericRequestHandler
        '''
        parse_result = urlparse(path)
        path = parse_result.path
        query = parse_qs(parse_result.query)
        if path == '/cpu':
            return self._get_cpu_status()
        if path == '/memory':
            try:
                offset = int(query.get('offset')[0], 16)
            except Exception:
                offset = 0
            try:
                length = int(query.get('length')[0], 16)
            except Exception:
                length = 256
            return self._get_memory(offset, length)
        if path == '/stack':
            return self._get_stack()

        return (
            HTTPStatus.BAD_REQUEST,
            {
                'error': 'Unknown path',
            }
        )

    def _get_cpu_status(self):
        status = {
            name: utils.word_to_str(self.cpu.registers.get_register(name, silent=True))
            for name in WORD_REGISTERS
        }
        status['IP'] = utils.word_to_str(self.cpu.ip)
        status['entry_point'] = utils.word_to_str(self.cpu.system_addresses['entry_point'])
        return (
            HTTPStatus.OK,
            status
        )

    def _get_memory(self, offset, length):
        first_address = offset
        return (
            HTTPStatus.OK,
            {
                'first_address': utils.word_to_str(first_address),
                'last_address': utils.word_to_str(first_address + length - 1),
                'memory': [
                    utils.byte_to_str(self.memory.read_byte(first_address + idx))
                    for idx in range(length)
                ],
            }
        )

    def _get_stack(self):
        sp = self.cpu.registers.get_register('SP', silent=True)
        bp = self.cpu.registers.get_register('BP', silent=True)
        bottom_of_stack = self.cpu.system_addresses['bottom_of_stack']
        first_address = max(sp - 7, 0)
        length = bottom_of_stack - first_address + 1
        return (
            HTTPStatus.OK,
            {
                'first_address': utils.word_to_str(first_address),
                'last_address': utils.word_to_str(bottom_of_stack),
                'SP': utils.word_to_str(sp),
                'BP': utils.word_to_str(bp),
                'stack': [
                    utils.byte_to_str(self.memory.read_byte(first_address + idx))
                    for idx in range(length)
                ],
            }
        )
