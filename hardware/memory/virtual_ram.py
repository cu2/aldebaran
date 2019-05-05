'''
Virtual RAM to handle virtual memory
'''

import logging

from utils import utils
from .memory import SegfaultError


logger = logging.getLogger('hardware.memory.virtual_ram')


class VirtualRAM:
    '''
    Virtual RAM
    '''

    def __init__(self, addresses):
        self.addresses = addresses
        self.device_controller = None
        self.architecture_registered = False

    def register_architecture(self, device_controller):
        '''
        Register other internal devices
        '''
        self.device_controller = device_controller
        self.architecture_registered = True

    def read_byte(self, pos, silent=False):
        '''
        Read byte from Virtual RAM at position `pos`
        '''
        if pos < self.addresses['device_controller']['first'] or pos > self.addresses['device_controller']['last']:
            raise SegfaultError('Segmentation fault when trying to read byte at {}'.format(utils.word_to_str(pos)))
        value = self.device_controller.read_byte(pos, silent=silent)
        if not silent:
            logger.debug('Read byte %s from %s.', utils.byte_to_str(value), utils.word_to_str(pos))
        return value

    def write_byte(self, pos, value, silent=False):
        '''
        Write byte to Virtual RAM at position `pos`
        '''
        if pos < self.addresses['device_controller']['first'] or pos > self.addresses['device_controller']['last']:
            raise SegfaultError('Segmentation fault when trying to write byte at {}'.format(utils.word_to_str(pos)))
        self.device_controller.write_byte(pos, value, silent=silent)
        if not silent:
            logger.debug('Written byte %s to %s.', utils.byte_to_str(value), utils.word_to_str(pos))

    def read_word(self, pos, silent=False):
        '''
        Read word from Virtual RAM at position `pos`
        '''
        if pos < self.addresses['device_controller']['first'] or pos > self.addresses['device_controller']['last'] - 1:
            raise SegfaultError('Segmentation fault when trying to read word at {}'.format(utils.word_to_str(pos)))
        value = self.device_controller.read_word(pos, silent=silent)
        if not silent:
            logger.debug('Read word %s from %s.', utils.word_to_str(value), utils.word_to_str(pos))
        return value

    def write_word(self, pos, value, silent=False):
        '''
        Write word to Virtual RAM at position `pos`
        '''
        if pos < self.addresses['device_controller']['first'] or pos > self.addresses['device_controller']['last'] - 1:
            raise SegfaultError('Segmentation fault when trying to write word at {}'.format(utils.word_to_str(pos)))
        self.device_controller.write_word(pos, value, silent=silent)
        if not silent:
            logger.debug('Written word %s to %s.', utils.word_to_str(value), utils.word_to_str(pos))
