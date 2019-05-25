'''
Assembler macros
'''

import logging

from utils import utils
from utils.errors import AldebaranError
from .tokenizer import TokenType


logger = logging.getLogger(__name__)


class Macro:

    def __init__(self, assembler, args, source_line, line_number, opcode_pos):
        self.assembler = assembler
        self.args = args
        self.source_line = source_line
        self.line_number = line_number
        self.opcode_pos = opcode_pos

    def run(self):
        '''
        Run macro, return generated opcode
        '''
        raise NotImplementedError()

    def _raise_error(self, pos, error_message, exception):
        _raise_error(self.source_line, self.line_number, pos, error_message, exception)


class DAT(Macro):

    def run(self):
        opcode = []
        args = self.assembler.substitute_variables(self.args, self.source_line, self.line_number)
        for arg in args:
            if arg.type == TokenType.STRING_LITERAL:
                opcode += list(arg.value.encode('utf-8'))
            elif arg.type == TokenType.BYTE_LITERAL:
                opcode.append(arg.value)
            elif arg.type == TokenType.WORD_LITERAL:
                opcode += utils.word_to_binary(arg.value)
            else:
                self._raise_error(arg.pos, 'Parameter of macro DAT must be a byte, word or string literal, not {}'.format(arg.type), MacroError)
        return opcode


class DATN(Macro):

    def run(self):
        if len(self.args) != 2:
            self._raise_error(None, 'Macro DATN requires exactly 2 parameters, not {}'.format(len(self.args)), MacroError)
        args = self.assembler.substitute_variables(self.args, self.source_line, self.line_number)
        repeat_arg, value_arg = args
        if repeat_arg.type not in {TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL}:
            self._raise_error(repeat_arg.pos, 'The first parameter of macro DATN must be a byte or word literal, not {}'.format(repeat_arg.type), MacroError)
        repeat_number = repeat_arg.value
        if value_arg.type not in {TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL, TokenType.STRING_LITERAL}:
            self._raise_error(value_arg.pos, 'The second parameter of macro DATN must be a byte, word or string literal, not {}'.format(value_arg.type), MacroError)
        opcode = []
        for _ in range(repeat_number):
            if value_arg.type == TokenType.STRING_LITERAL:
                opcode += list(value_arg.value.encode('utf-8'))
            elif value_arg.type == TokenType.BYTE_LITERAL:
                opcode.append(value_arg.value)
            else:
                opcode += utils.word_to_binary(value_arg.value)
        return opcode


class CONST(Macro):

    def run(self):
        if len(self.args) != 2:
            self._raise_error(None, 'Macro CONST requires exactly 2 parameters, not {}'.format(len(self.args)), MacroError)
        var_arg, value_arg = self.args
        if var_arg.type != TokenType.VARIABLE:
            self._raise_error(var_arg.pos, 'The first parameter of macro CONST must be a variable, not {}'.format(var_arg.type), MacroError)
        var_name = var_arg.value
        if var_name in self.assembler.consts:
            self._raise_error(var_arg.pos, 'Variable {} already defined as {}.'.format(var_name, self.assembler.consts[var_name]), VariableError)

        if value_arg.type == TokenType.VARIABLE:
            value_arg = self.assembler.substitute_variable(value_arg, self.source_line, self.line_number)
        if value_arg.type not in {TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL, TokenType.STRING_LITERAL}:
            self._raise_error(value_arg.pos, 'The second parameter of macro CONST must be a byte, word or string literal, not {}'.format(value_arg.type), MacroError)

        self.assembler.consts[var_name] = value_arg
        return []


MACRO_SET = {
    'DAT': DAT,
    'DATN': DATN,
    'CONST': CONST,
}


def _raise_error(code, line_number, pos, error_message, exception):
    logger.error('ERROR in line %d:', line_number)
    logger.error(code)
    if pos is not None:
        logger.error(' ' * pos + '^')
    raise exception(error_message)


# pylint: disable=missing-docstring

class MacroError(AldebaranError):
    pass


class VariableError(MacroError):
    pass
