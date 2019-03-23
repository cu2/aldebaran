import errors


class Log(object):

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


class SilentLog(object):

    def log(self, part, msg):
        pass


class Hardware(object):

    def __init__(self, log=None):
        if log:
            self.log = log
        else:
            self.log = SilentLog()


def bytes_to_word(high, low):
    return (high << 8) + low


def word_to_bytes(word):
    if word > 65535:
        raise errors.WordOutOfRangeError(hex(word))
    return (
        word >> 8,
        word & 0x00FF,
    )


def byte_to_str(byte, signed=False):
    if signed:
        if byte < -128 or byte > 127:
            raise errors.ByteOutOfRangeError(hex(byte))
        return '%02X' % (byte & 0xFF)
    if byte < 0 or byte > 255:
        raise errors.ByteOutOfRangeError(hex(byte))
    return '%02X' % byte


def word_to_str(word, signed=False):
    if signed:
        if word < -32768 or word > 32767:
            raise errors.WordOutOfRangeError(hex(word))
        return '%04X' % (word & 0xFFFF)
    if word < 0 or word > 65535:
        raise errors.WordOutOfRangeError(hex(word))
    return '%04X' % word


def binary_to_str(binary, padding=' '):
    return padding.join('{:02X}'.format(x) for x in binary)


def str_to_int(str):
    return int(str, 16)


def int_to_str(integer, length):
    if integer > 0x100**length - 1:
        raise errors.OutOfRangeError(hex(integer))
    return ('%0{0}X'.format(length)) % integer


def get_low(word):
    return word & 0x00FF


def get_high(word):
    return word >> 8


def set_low(word, value):
    return (word & 0xFF00) + value


def set_high(word, value):
    return (word & 0x00FF) + (value << 8)


def byte_to_signed(byte):
    if byte < 0 or byte > 255:
        raise errors.ByteOutOfRangeError(hex(byte))
    if byte > 127:
        return byte - 256
    return byte


def word_to_signed(word):
    if word < 0 or word > 65535:
        raise errors.WordOutOfRangeError(hex(word))
    if word > 32767:
        return word - 65536
    return word
