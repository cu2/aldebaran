class OutOfRangeError(Exception):
    pass


class WordOutOfRangeError(OutOfRangeError):
    pass


class ByteOutOfRangeError(OutOfRangeError):
    pass


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


def bytes_to_word(high, low):
    return (high << 8) + low


def word_to_bytes(word, signed=False):
    if signed:
        if word < -32768 or word > 32767:
            raise WordOutOfRangeError(hex(word))
        return list(word.to_bytes(2, 'big', signed=True))
    if word < 0 or word > 65535:
        raise WordOutOfRangeError(hex(word))
    return [
        word >> 8,
        word & 0x00FF,
    ]


def byte_to_bytes(byte, signed=False):
    if signed:
        if byte < -128 or byte > 127:
            raise ByteOutOfRangeError(hex(byte))
        return list(byte.to_bytes(1, 'big', signed=True))
    if byte < 0 or byte > 255:
        raise ByteOutOfRangeError(hex(byte))
    return [
        byte,
    ]


def string_to_bytes(s):
    opcode = []
    for char in s:
        for byte in char.encode('utf-8'):
            opcode.append(byte)
    return opcode


def byte_to_str(byte, signed=False):
    if signed:
        if byte < -128 or byte > 127:
            raise ByteOutOfRangeError(hex(byte))
        return '{:02X}'.format(byte & 0xFF)  # TODO: fix
    if byte < 0 or byte > 255:
        raise ByteOutOfRangeError(hex(byte))
    return '{:02X}'.format(byte)


def word_to_str(word, signed=False):
    if signed:
        if word < -32768 or word > 32767:
            raise WordOutOfRangeError(hex(word))
        return '{:04X}'.format(word & 0xFFFF)  # TODO: fix
    if word < 0 or word > 65535:
        raise WordOutOfRangeError(hex(word))
    return '{:04X}'.format(word)


def binary_to_str(binary, padding=' '):
    return padding.join('{:02X}'.format(x) for x in binary)


def str_to_int(str):
    return int(str, 16)


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
        raise ByteOutOfRangeError(hex(byte))
    if byte > 127:
        return byte - 256
    return byte


def word_to_signed(word):
    if word < 0 or word > 65535:
        raise WordOutOfRangeError(hex(word))
    if word > 32767:
        return word - 65536
    return word
