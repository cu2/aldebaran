'''
Memory interface hiding RAM and Virtual RAM
'''

import logging

from utils import utils
from utils.errors import AldebaranError


logger = logging.getLogger('hardware.memory')


class Memory:
    '''
    Memory interface
    '''

    def __init__(self, ram_size):
        self.ram_size = ram_size
        self.ram = None
        self.virtual_ram = None
        self.architecture_registered = False

    def register_architecture(self, ram, virtual_ram):
        '''
        Register other internal devices
        '''
        self.ram = ram
        self.virtual_ram = virtual_ram
        self.architecture_registered = True

    def read_byte(self, pos, silent=False):
        '''
        Read byte at position `pos`
        '''
        if pos < self.ram_size:
            return self.ram.read_byte(pos, silent=silent)
        return self.virtual_ram.read_byte(pos, silent=silent)

    def write_byte(self, pos, value, silent=False):
        '''
        Write byte at position `pos`
        '''
        if pos < self.ram_size:
            self.ram.write_byte(pos, value, silent=silent)
        else:
            self.virtual_ram.write_byte(pos, value, silent=silent)

    def read_word(self, pos, silent=False):
        '''
        Read word at position `pos`
        '''
        if pos < self.ram_size - 1:
            return self.ram.read_word(pos, silent=silent)
        if pos == self.ram_size - 1:
            # cannot read word half from ram, half from virtual ram
            raise SegfaultError('Segmentation fault when trying to read word at {}'.format(utils.word_to_str(pos)))
        return self.virtual_ram.read_word(pos, silent=silent)

    def write_word(self, pos, value, silent=False):
        '''
        Write word at position `pos`
        '''
        if pos < self.ram_size - 1:
            self.ram.write_word(pos, value, silent=silent)
        elif pos == self.ram_size - 1:
            # cannot write word half to ram, half to virtual ram
            raise SegfaultError('Segmentation fault when trying to read word at {}'.format(utils.word_to_str(pos)))
        else:
            self.virtual_ram.write_word(pos, value, silent=silent)


# pylint: disable=missing-docstring

class AldMemoryError(AldebaranError):
    pass


class SegfaultError(AldMemoryError):
    pass
