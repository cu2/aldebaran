'''
Interrupt Controller to handle hardware interrupts
'''

import logging
import queue

from utils import utils
from utils.errors import AldebaranError


logger = logging.getLogger(__name__)


class InterruptController:
    '''
    Interrupt Controller

    Currently a simple FIFO queue. Later it can change to something that handles e.g. priorities.
    '''

    def __init__(self):
        self._interrupt_queue = queue.Queue()

    def check(self):
        '''
        Get interrupt, if there's any
        '''
        try:
            interrupt_number = self._interrupt_queue.get_nowait()
        except queue.Empty:
            return None
        logger.info('Forwarded IRQ to CPU: %s', utils.byte_to_str(interrupt_number))
        logger.debug('Interrupt queue length: %d', self._interrupt_queue.qsize())
        return interrupt_number

    def send(self, interrupt_number):
        '''
        Send interrupt
        '''
        try:
            interrupt_number = int(interrupt_number)
        except ValueError:
            raise InvalidInterruptError('Invalid interrupt: {}'.format(interrupt_number))
        if interrupt_number < 0 or interrupt_number > 255:
            raise InvalidInterruptError('Invalid interrupt: {}'.format(interrupt_number))
        self._interrupt_queue.put(interrupt_number)
        logger.info('Received IRQ: %s', utils.byte_to_str(interrupt_number))
        logger.debug('Interrupt queue length: %d', self._interrupt_queue.qsize())


# pylint: disable=missing-docstring

class InterruptError(AldebaranError):
    pass


class InvalidInterruptError(InterruptError):
    pass
