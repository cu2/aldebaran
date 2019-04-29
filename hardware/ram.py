'''
RAM to store data
'''

import logging

from utils import utils
from utils.errors import AldebaranError


logger = logging.getLogger(__name__)


class RAM:
    '''
    Random-access memory
    '''

    def __init__(self, size):
        self.size = size
        self._content = [0] * self.size
        logger.info('%d bytes initialized.', self.size)

    def read_byte(self, pos):
        '''
        Read byte from RAM at position `pos`
        '''
        if pos < 0 or pos > self.size - 1:
            raise SegfaultError('Segmentation fault when trying to read byte at {}'.format(utils.word_to_str(pos)))
        value = self._content[pos]
        logger.debug('Read byte %s from %s.', utils.byte_to_str(value), utils.word_to_str(pos))
        return value

    def write_byte(self, pos, value):
        '''
        Write byte to RAM at position `pos`
        '''
        if pos < 0 or pos > self.size - 1:
            raise SegfaultError('Segmentation fault when trying to write byte at {}'.format(utils.word_to_str(pos)))
        self._content[pos] = value
        logger.debug('Written byte %s to %s.', utils.byte_to_str(value), utils.word_to_str(pos))

    def read_word(self, pos):
        '''
        Read word from RAM at position `pos`
        '''
        if pos < 0 or pos > self.size - 2:
            raise SegfaultError('Segmentation fault when trying to read word at {}'.format(utils.word_to_str(pos)))
        value = (self._content[pos] << 8) + self._content[pos + 1]
        logger.debug('Read word %s from %s.', utils.word_to_str(value), utils.word_to_str(pos))
        return value

    def write_word(self, pos, value):
        '''
        Write word to RAM at position `pos`
        '''
        if pos < 0 or pos > self.size - 2:
            raise SegfaultError('Segmentation fault when trying to write word at {}'.format(utils.word_to_str(pos)))
        self._content[pos] = utils.get_high(value)
        self._content[pos + 1] = utils.get_low(value)
        logger.debug('Written word %s to %s.', utils.word_to_str(value), utils.word_to_str(pos))


# pylint: disable=missing-docstring

class RAMError(AldebaranError):
    pass


class SegfaultError(RAMError):
    pass
