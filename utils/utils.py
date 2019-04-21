'''
Utils, like binary_to_number, set_low, set_high...
'''

def binary_to_number(binary, signed=False):
    '''
    Convert binary (list of bytes) to number
    '''
    return int.from_bytes(binary, 'big', signed=signed)


def word_to_binary(word, signed=False):
    '''
    Convert word-length number to binary (list of bytes)
    '''
    try:
        return list(word.to_bytes(2, 'big', signed=signed))
    except OverflowError:
        raise WordOutOfRangeError(hex(word))


def byte_to_binary(byte, signed=False):
    '''
    Convert byte-length number to binary (list of bytes)
    '''
    try:
        return list(byte.to_bytes(1, 'big', signed=signed))
    except OverflowError:
        raise ByteOutOfRangeError(hex(byte))


def byte_to_str(byte):
    '''
    Convert byte-length number to hex string
    '''
    return '{:02X}'.format(byte)


def word_to_str(word):
    '''
    Convert word-length number to hex string
    '''
    return '{:04X}'.format(word)


def binary_to_str(binary, padding=' '):
    '''
    Convert binary (list of bytes) to hex string
    '''
    return padding.join('{:02X}'.format(x) for x in binary)


def get_low(word):
    '''
    Return low byte of word
    '''
    return word & 0x00FF


def get_high(word):
    '''
    Return high byte of word
    '''
    return word >> 8


def set_low(word, value):
    '''
    Set low byte of word and return result
    '''
    return (word & 0xFF00) + value


def set_high(word, value):
    '''
    Set high byte of word and return result
    '''
    return (word & 0x00FF) + (value << 8)


class Log:

    def __init__(self):
        self.term_colors = True
        self.part_colors = {
            'aldebaran': self.col('0;31'),
            'clock': self.col('1;30'),
            'cpu': self.col('0;32'),
            'ram': self.col('0;36'),
            'print': self.col('37;1'),
        }

    def col(self, colstr=None):
        if not self.term_colors:
            return ''
        if colstr:
            return '\033[%sm' % colstr
        else:
            return '\033[0m'

    def log(self, part, msg):
        if part:
            print('%s[%s] %s%s' % (
                self.part_colors.get(part, ''),
                part,
                msg,
                self.col(),
            ))
        else:
            print(msg)


class SilentLog:

    def log(self, part, msg):
        pass


class Hardware:

    def __init__(self, log=None):
        if log:
            self.log = log
        else:
            self.log = SilentLog()


class OutOfRangeError(Exception):
    pass


class WordOutOfRangeError(OutOfRangeError):
    pass


class ByteOutOfRangeError(OutOfRangeError):
    pass
