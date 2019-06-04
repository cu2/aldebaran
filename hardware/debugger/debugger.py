'''
Debugger to show Aldebaran's internal state
'''

import json
import logging
import threading
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs

from instructions.operands import WORD_REGISTERS, operand_to_str
from utils import config
from utils import utils
from utils.errors import ArchitectureError
from utils.utils import GenericRequestHandler, GenericServer
from hardware.memory.memory import SegfaultError


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
        self._server = GenericServer((host, port), GenericRequestHandler, self._handle_get, self._handle_post)
        self._input_thread = threading.Thread(target=self._server.serve_forever)

        self.cpu = None
        self.clock = None
        self.memory = None
        self.architecture_registered = False

    def register_architecture(self, cpu, clock, memory):
        '''
        Register other internal devices
        '''
        self.cpu = cpu
        self.clock = clock
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

    def _handle_get(self, path):
        '''
        Handle incoming GET request from Debugger frontend, called by GenericRequestHandler
        '''
        parse_result = urlparse(path)
        path = parse_result.path
        query = parse_qs(parse_result.query)
        if path == '/api/internal':
            return self._get_internal_state()
        if path == '/api/memory':
            try:
                offset = int(query.get('offset')[0], 16)
            except Exception:
                offset = 0
            try:
                length = int(query.get('length')[0], 16)
            except Exception:
                length = 256
            return self._get_memory(offset, length)

        return (
            HTTPStatus.BAD_REQUEST,
            {
                'error': 'Unknown path',
            }
        )

    def _get_internal_state(self):
        registers = {
            name: utils.word_to_str(self.cpu.registers.get_register(name, silent=True))
            for name in WORD_REGISTERS
        }
        registers['IP'] = utils.word_to_str(self.cpu.ip)
        registers['entry_point'] = utils.word_to_str(self.cpu.system_addresses['entry_point'])
        if self.cpu.last_ip is not None:
            last_ip = utils.word_to_str(self.cpu.last_ip)
            last_instruction = {
                'name': self.cpu.last_instruction.__class__.__name__,
                'operands': [
                    operand_to_str(op)
                    for op in self.cpu.last_instruction.operands
                ],
            }
        else:
            last_ip = None
            last_instruction = None
        return (
            HTTPStatus.OK,
            {
                'registers': registers,
                'stack': self._get_stack(),
                'cpu': {
                    'halt': self.cpu.halt,
                    'shutdown': self.cpu.shutdown,
                    'last_instruction': last_instruction,
                    'last_ip': last_ip,
                },
                'clock': {
                    'cycle_count': self.clock.cycle_count,
                }
            }
        )

    def _get_memory(self, offset, length):
        if offset >= config.memory_size or offset < 0:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    'error': 'Cannot access memory beyond 0000-{}'.format(utils.word_to_str(config.memory_size - 1)),
                }
            )
        if offset + length > config.memory_size:
            length = config.memory_size - offset

        first_address = offset
        content = []
        for idx in range(length):
            try:
                content.append(utils.byte_to_str(self.memory.read_byte(first_address + idx)))
            except SegfaultError:
                content.append(None)
        return (
            HTTPStatus.OK,
            {
                'first_address': utils.word_to_str(first_address),
                'last_address': utils.word_to_str(first_address + length - 1),
                'content': content,
            }
        )

    def _get_stack(self):
        bottom_of_stack = self.cpu.system_addresses['bottom_of_stack']
        first_address = max(self.cpu.registers.get_register('SP', silent=True) - 7, 0)
        length = bottom_of_stack - first_address + 1
        return {
            'first_address': utils.word_to_str(first_address),
            'last_address': utils.word_to_str(bottom_of_stack),
            'content': [
                utils.byte_to_str(self.memory.read_byte(first_address + idx))
                for idx in range(length)
            ],
        }

    def _handle_post(self, path, headers, rfile):
        '''
        Handle incoming POST request from Debugger frontend, called by GenericRequestHandler
        '''
        parse_result = urlparse(path)
        path = parse_result.path
        try:
            request_body_length = int(headers.get('Content-Length'))
        except TypeError:
            return (HTTPStatus.LENGTH_REQUIRED, None)
        data = rfile.read(request_body_length)
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    'error': 'Could not parse data.',
                }
            )
        if path == '/api/cpu/step':
            self.clock.debugger_queue.put({
                'action': 'step',
                'data': data,
            })
            return (
                HTTPStatus.OK,
                {}
            )
