'''
Assembler macros
'''

import logging

from instructions.operands import get_operand_opcode
from utils import utils
from utils.errors import AldebaranError
from .tokenizer import Token, TokenType, Reference


logger = logging.getLogger(__name__)


class Macro:
    '''
    Macro base class
    '''

    param_count = (None, None)
    substitute_variables_in_params = None
    param_types = None
    param_type_list = None

    def __init__(self, assembler, source_line, line_number):
        self.assembler = assembler
        self.source_line = source_line
        self.line_number = line_number
        self.name = self.__class__.__name__

    def run(self, params):
        '''
        Validate parameters, run macro, return generated opcode
        '''
        # validate parameter count
        if self.param_count[0] is not None and self.param_count[0] == self.param_count[1]:
            if len(params) != self.param_count[0]:
                self._raise_macro_error(None, 'Macro {} requires exactly {}, not {}'.format(
                    self.name,
                    _param_count_string(self.param_count[0]),
                    len(params),
                ))
        else:
            if self.param_count[0] is not None:
                if len(params) < self.param_count[0]:
                    self._raise_macro_error(None, 'Macro {} requires at least {}'.format(
                        self.name,
                        _param_count_string(self.param_count[0]),
                    ))
            if self.param_count[1] is not None:
                if len(params) > self.param_count[1]:
                    self._raise_macro_error(None, 'Macro {} requires at most {}'.format(
                        self.name,
                        _param_count_string(self.param_count[1]),
                    ))
        # substitute variables
        if self.substitute_variables_in_params is not None:
            if self.substitute_variables_in_params == 'all':
                params = self.assembler.substitute_variables(params, self.source_line, self.line_number)
            else:
                for param_number in self.substitute_variables_in_params:
                    param_idx = param_number - 1
                    if params[param_idx].type == TokenType.VARIABLE:
                        params[param_idx] = self.assembler.substitute_variable(params[param_idx], self.source_line, self.line_number)
        # validate parameter types
        if self.param_types is not None:
            for param_idx, param_type_list in enumerate(self.param_types):
                param_number = param_idx + 1
                self._validate_parameter(params[param_idx], param_type_list, param_number)
        if self.param_type_list is not None:
            for param in params:
                self._validate_parameter(param, self.param_type_list)

        return self.do(params)

    def do(self, params):
        '''
        Run macro, return generated opcode
        '''
        raise NotImplementedError()

    def _validate_parameter(self, param, param_type_list, param_number=None):
        if param.type not in param_type_list:
            if param_number is None:
                error_message = 'All parameters of macro {} must be {}, not {}'.format(
                    self.name,
                    ' or '.join(param_type.name for param_type in param_type_list),
                    param.type.name,
                )
            else:
                error_message = 'Parameter {} of macro {} must be {}, not {}'.format(
                    param_number,
                    self.name,
                    ' or '.join(param_type.name for param_type in param_type_list),
                    param.type.name,
                )
            self._raise_macro_error(param.pos, error_message)

    def _raise_macro_error(self, pos, error_message):
        self._raise_error(pos, error_message, MacroError)

    def _raise_error(self, pos, error_message, exception):
        _raise_error(self.source_line, self.line_number, pos, error_message, exception)


class DAT(Macro):
    '''
    .DAT <param>+

    Insert byte, word and string literals
    '''

    param_count = (1, None)
    substitute_variables_in_params = 'all'
    param_type_list = [TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL, TokenType.STRING_LITERAL]

    def do(self, params):
        opcode = []
        for param in params:
            if param.type == TokenType.STRING_LITERAL:
                opcode += list(param.value.encode('utf-8'))
            elif param.type == TokenType.BYTE_LITERAL:
                opcode.append(param.value)
            else:
                opcode += utils.word_to_binary(param.value)
        return opcode


class DATN(Macro):
    '''
    .DATN <repeat> <value>

    Insert byte, word and string literal multiple times
    '''

    param_count = (2, 2)
    substitute_variables_in_params = 'all'
    param_types = [
        [TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL],
        [TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL, TokenType.STRING_LITERAL],
    ]

    def do(self, params):
        repeat_param, value_param = params
        if value_param.type == TokenType.STRING_LITERAL:
            opcode_to_repeat = list(value_param.value.encode('utf-8'))
        elif value_param.type == TokenType.BYTE_LITERAL:
            opcode_to_repeat = [value_param.value]
        else:
            opcode_to_repeat = utils.word_to_binary(value_param.value)
        return repeat_param.value * opcode_to_repeat


class CONST(Macro):
    '''
    .CONST <name> <value>

    Define variable
    '''

    param_count = (2, 2)
    substitute_variables_in_params = [2]
    param_types = [
        [TokenType.VARIABLE],
        [TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL, TokenType.STRING_LITERAL],
    ]

    def do(self, params):
        name_param, value_param = params
        if self.assembler.is_variable_defined(name_param.value):
            self._raise_error(name_param.pos, 'Variable {} already defined'.format(name_param.value), VariableError)
        self.assembler.consts[name_param.value] = value_param
        return []


class PARAM(Macro):
    '''
    .PARAM <name>

    Define word parameter in a scope
    '''

    param_count = (1, 1)
    length = 2
    param_types = [
        [TokenType.VARIABLE],
    ]

    def do(self, params):
        if self.assembler.current_scope is None:
            self._raise_macro_error(None, 'Macro {} must be in a scope'.format(self.name))
        name_param = params[0]
        if self.assembler.is_variable_defined(name_param.value):
            self._raise_error(name_param.pos, 'Variable {} already defined'.format(name_param.value), VariableError)

        try:
            self.assembler.current_scope.add_parameter(name_param.value, self.length)
        except ScopeError as ex:
            self._raise_error(None, str(ex), ScopeError)
        return []


class PARAMB(PARAM):
    '''
    .PARAMB <name>

    Define byte parameter in a scope
    '''

    param_count = (1, 1)
    length = 1


class VAR(Macro):
    '''
    .VAR <name> [default_value]

    Define local word variable in a scope (with optional default value)
    '''

    param_count = (1, 2)
    length = 2
    param_types = [
        [TokenType.VARIABLE],
    ]

    def do(self, params):
        if self.assembler.current_scope is None:
            self._raise_macro_error(None, 'Macro {} must be in a scope'.format(self.name))
        if len(params) == 1:
            name_param = params[0]
            default_value_param = None
        else:
            name_param, default_value_param = params
            if default_value_param.type == TokenType.VARIABLE:
                default_value_param = self.assembler.substitute_variable(default_value_param, self.source_line, self.line_number)
            self._validate_parameter(default_value_param, [TokenType.WORD_LITERAL if self.length == 2 else TokenType.BYTE_LITERAL], 2)

        if self.assembler.is_variable_defined(name_param.value):
            self._raise_error(name_param.pos, 'Variable {} already defined'.format(name_param.value), VariableError)

        try:
            self.assembler.current_scope.add_variable(name_param.value, self.length)
        except ScopeError as ex:
            self._raise_error(None, str(ex), ScopeError)

        if default_value_param is not None:
            # MOV $var default_value
            inst_opcode, _ = self.assembler.instruction_mapping['MOV']
            opcode = [inst_opcode]
            opcode += get_operand_opcode(self.assembler.current_scope.get_value(name_param.value))
            opcode += get_operand_opcode(Token(
                default_value_param.type,
                default_value_param.value,
                None,
            ))
            return opcode
        return []


class VARB(VAR):
    '''
    .VARB <name> [default_value]

    Define local byte variable in a scope (with optional default value)
    '''

    param_count = (1, 2)
    length = 1


MACRO_SET = {
    'DAT': DAT,
    'DATN': DATN,
    'CONST': CONST,
    'PARAM': PARAM,
    'PARAMB': PARAMB,
    'VAR': VAR,
    'VARB': VARB,
}


def _raise_error(code, line_number, pos, error_message, exception):
    logger.error('ERROR in line %d:', line_number)
    logger.error(code)
    if pos is not None:
        logger.error(' ' * pos + '^')
    raise exception(error_message)


def _param_count_string(cnt):
    if cnt > 1:
        return '{} parameters'.format(cnt)
    return '{} parameter'.format(cnt)


# pylint: disable=missing-docstring

class MacroError(AldebaranError):
    pass


class VariableError(MacroError):
    pass


class ScopeError(MacroError):
    pass
