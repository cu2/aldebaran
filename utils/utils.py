'''
Utils, like binary_to_number, set_low, set_high...
'''

import logging

from .errors import AldebaranError


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


def config_loggers(logconfig):
    '''
    Setup loggers
    '''
    for logname, details in logconfig.items():
        logger = logging.getLogger(logname)
        logger.propagate = False
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        if details['name']:
            name_prefix = '[{}] '.format(details['name'])
        else:
            name_prefix = ''
        if 'color' in details:
            format_string = '\033[{}m{}%(message)s\033[0m'.format(
                details['color'],
                name_prefix,
            )
        else:
            format_string = '{}%(message)s'.format(
                name_prefix,
            )
        handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(handler)
        if details['level'] == 'D':
            logger.setLevel(logging.DEBUG)
        elif details['level'] == 'I':
            logger.setLevel(logging.INFO)
        elif details['level'] == 'W':
            logger.setLevel(logging.WARNING)
        elif details['level'] == 'E':
            logger.setLevel(logging.ERROR)


# pylint: disable=missing-docstring

class OutOfRangeError(AldebaranError):
    pass


class WordOutOfRangeError(OutOfRangeError):
    pass


class ByteOutOfRangeError(OutOfRangeError):
    pass
