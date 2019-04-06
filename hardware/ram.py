from utils import utils


class RAM(utils.Hardware):

    def __init__(self, size, log=None):
        utils.Hardware.__init__(self, log)
        self.size = size
        self.mem = [0] * self.size
        self.log.log('ram', '%s bytes initialized.' % self.size)

    def read_byte(self, pos):
        pos = pos % self.size
        content = self.mem[pos]
        self.log.log('ram', 'Read byte %s from %s.' % (utils.byte_to_str(content), utils.word_to_str(pos)))
        return content

    def write_byte(self, pos, content):
        pos = pos % self.size
        self.mem[pos] = content
        self.log.log('ram', 'Written byte %s to %s.' % (utils.byte_to_str(content), utils.word_to_str(pos)))

    def read_word(self, pos):
        pos1 = pos % self.size
        pos2 = (pos + 1) % self.size
        content = (self.mem[pos1] << 8) + self.mem[pos2]
        self.log.log('ram', 'Read word %s from %s.' % (utils.word_to_str(content), utils.word_to_str(pos1)))
        return content

    def write_word(self, pos, content):
        pos1 = pos % self.size
        pos2 = (pos + 1) % self.size
        self.mem[pos1] = content >> 8
        self.mem[pos2] = content & 0x00FF
        self.log.log('ram', 'Written word %s to %s.' % (utils.word_to_str(content), utils.word_to_str(pos1)))
