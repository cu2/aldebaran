import logging
from utils import utils


logger = logging.getLogger(__name__)


class RAM:

    def __init__(self, size):
        self.size = size
        self.mem = [0] * self.size
        logger.info('%d bytes initialized.', self.size)

    def read_byte(self, pos):
        pos = pos % self.size
        content = self.mem[pos]
        logger.debug('Read byte %s from %s.', utils.byte_to_str(content), utils.word_to_str(pos))
        return content

    def write_byte(self, pos, content):
        pos = pos % self.size
        self.mem[pos] = content
        logger.debug('Written byte %s to %s.', utils.byte_to_str(content), utils.word_to_str(pos))

    def read_word(self, pos):
        pos1 = pos % self.size
        pos2 = (pos + 1) % self.size
        content = (self.mem[pos1] << 8) + self.mem[pos2]
        logger.debug('Read word %s from %s.', utils.word_to_str(content), utils.word_to_str(pos1))
        return content

    def write_word(self, pos, content):
        pos1 = pos % self.size
        pos2 = (pos + 1) % self.size
        self.mem[pos1] = content >> 8
        self.mem[pos2] = content & 0x00FF
        logger.debug('Written word %s to %s.', utils.word_to_str(content), utils.word_to_str(pos1))
