'''
Registers and flags within the CPU
'''

import logging

from instructions.operands import BYTE_REGISTERS
from utils import utils
from .cpu import CPUError


logger = logging.getLogger('hardware.cpu.registers')


FLAGS = ['interrupt']


class Registers:
    '''
    Registers and flags
    '''

    def __init__(self, bottom_of_stack):
        self._registers = {
            'AX': 0,
            'BX': 0,
            'CX': 0,
            'DX': 0,
            'SI': 0,
            'DI': 0,
            'SP': bottom_of_stack,
            'BP': 0,
        }
        self._flags = {
            'interrupt': 1,
        }

    def get_register(self, register_name, silent=False):
        '''
        Get register value
        '''
        value = None
        hex_value = None
        if register_name in self._registers:
            value = self._registers[register_name]
            hex_value = utils.word_to_str(value)
        elif register_name in {'AL', 'BL', 'CL', 'DL'}:
            value = utils.get_low(self._registers[register_name[0] + 'X'])
            hex_value = utils.byte_to_str(value)
        elif register_name in {'AH', 'BH', 'CH', 'DH'}:
            value = utils.get_high(self._registers[register_name[0] + 'X'])
            hex_value = utils.byte_to_str(value)
        else:
            raise InvalidRegisterNameError('Invalid register name: {}'.format(register_name))
        if not silent:
            logger.debug('Get register %s = %s', register_name, hex_value)
        return value

    def set_register(self, register_name, value, silent=False):
        '''
        Set register value
        '''
        try:
            value = int(value)
        except ValueError:
            raise InvalidRegisterValueError('Invalid register value: {}'.format(value))

        if register_name in self._registers:
            self._set_word_register(register_name, value, silent=silent)
        elif register_name in BYTE_REGISTERS:
            self._set_byte_register(register_name, value, silent=silent)
        else:
            raise InvalidRegisterNameError('Invalid register name: {}'.format(register_name))

    def _set_word_register(self, register_name, value, silent=False):
        if value < 0x0000 or value > 0xFFFF:
            raise InvalidRegisterValueError('Invalid register value: {}'.format(value))
        self._registers[register_name] = value
        if not silent:
            logger.debug('Set register %s = %s', register_name, utils.word_to_str(value))

    def _set_byte_register(self, register_name, value, silent=False):
        if value < 0x00 or value > 0xFF:
            raise InvalidRegisterValueError('Invalid register value: {}'.format(value))
        if register_name in {'AL', 'BL', 'CL', 'DL'}:
            self._registers[register_name[0] + 'X'] = utils.set_low(self._registers[register_name[0] + 'X'], value)
        else:
            self._registers[register_name[0] + 'X'] = utils.set_high(self._registers[register_name[0] + 'X'], value)
        if not silent:
            logger.debug('Set register %s = %s', register_name, utils.byte_to_str(value))

    def get_flag(self, flag_name, silent=False):
        '''
        Get flag value
        '''
        try:
            value = self._flags[flag_name]
        except KeyError:
            raise InvalidFlagNameError('Invalid flag name: {}'.format(flag_name))
        if not silent:
            logger.debug('Get flag %s = %s', flag_name, value)
        return value

    def set_flag(self, flag_name, value, silent=False):
        '''
        Set flag value
        '''
        if flag_name not in self._flags:
            raise InvalidFlagNameError('Invalid flag name: {}'.format(flag_name))
        if value not in {0, 1}:
            raise InvalidFlagValueError('Invalid flag value: {}'.format(value))
        self._flags[flag_name] = value
        if not silent:
            logger.debug('Set flag %s = %s', flag_name, value)


# pylint: disable=missing-docstring

class RegisterError(CPUError):
    pass


class InvalidRegisterNameError(RegisterError):
    pass


class InvalidRegisterValueError(RegisterError):
    pass


class InvalidFlagNameError(RegisterError):
    pass


class InvalidFlagValueError(RegisterError):
    pass
