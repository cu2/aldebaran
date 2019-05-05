'''
Stack within the CPU
'''

import logging

from utils import utils
from .cpu import CPUError
from .registers import FLAGS


logger = logging.getLogger('hardware.cpu.stack')


class Stack:

    def __init__(self, bottom_of_stack):
        self._bottom_of_stack = bottom_of_stack
        self._registers = None
        self._ram = None
        self.architecture_registered = False

    def register_architecture(self, registers, memory):
        '''
        Register other internal devices
        '''
        self._registers = registers
        self._ram = memory
        self.architecture_registered = True

    def push_byte(self, value):
        '''
        Push byte on stack
        '''
        sp = self._registers.get_register('SP', silent=True)
        if sp < 1:
            raise StackOverflowError('Stack overflow: {}'.format(utils.word_to_str(sp)))
        self._ram.write_byte(sp, value, silent=True)
        logger.debug('Pushed byte %s', utils.byte_to_str(value))
        self._registers.set_register('SP', sp - 1, silent=True)

    def pop_byte(self):
        '''
        Pop byte from stack
        '''
        sp = self._registers.get_register('SP', silent=True)
        if sp >= self._bottom_of_stack:
            raise StackUnderflowError('Stack underflow: {}'.format(utils.word_to_str(sp)))
        self._registers.set_register('SP', sp + 1, silent=True)
        value = self._ram.read_byte(sp + 1, silent=True)
        logger.debug('Popped byte %s', utils.byte_to_str(value))
        return value

    def push_word(self, value, silent=False):
        '''
        Push word on stack
        '''
        sp = self._registers.get_register('SP', silent=True)
        if sp < 2:
            raise StackOverflowError('Stack overflow: {}'.format(utils.word_to_str(sp)))
        self._ram.write_word(sp - 1, value, silent=True)
        if not silent:
            logger.debug('Pushed word %s', utils.word_to_str(value))
        self._registers.set_register('SP', sp - 2, silent=True)

    def pop_word(self, silent=False):
        '''
        Pop word from stack
        '''
        sp = self._registers.get_register('SP', silent=True)
        if sp >= self._bottom_of_stack - 1:
            raise StackUnderflowError('Stack underflow: {}'.format(utils.word_to_str(sp)))
        self._registers.set_register('SP', sp + 2, silent=True)
        value = self._ram.read_word(sp + 2 - 1, silent=True)
        if not silent:
            logger.debug('Popped word %s', utils.word_to_str(value))
        return value

    def push_flags(self):
        '''
        Push flags on stack
        '''
        flag_word = 0x0000
        for idx, name in enumerate(FLAGS):
            flag_word += self._registers.get_flag(name, silent=True) << idx
        self.push_word(flag_word, silent=True)
        logger.debug('Pushed FLAGS')

    def pop_flags(self):
        '''
        Pop flags from stack
        '''
        flag_word = self.pop_word(silent=True)
        for idx, name in enumerate(FLAGS):
            self._registers.set_flag(name, (flag_word >> idx) & 0x0001, silent=True)
        logger.debug('Popped FLAGS')


# pylint: disable=missing-docstring

class StackError(CPUError):
    pass


class StackOverflowError(StackError):
    pass


class StackUnderflowError(StackError):
    pass
