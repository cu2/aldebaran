'''
Assembler
'''

from enum import Enum
import logging
import os

from instructions.operands import get_operand_opcode
from utils import utils
from utils.errors import AldebaranError
from utils.executable import Executable
from .macros import MACRO_SET, MacroError, VariableError
from .tokenizer import Tokenizer, Token, TokenType, Reference, ARGUMENT_TYPES, LABEL_REFERENCE_TYPES


logger = logging.getLogger(__name__)


class Assembler:
    '''
    Assembler
    '''

    def __init__(self, instruction_set, registers):
        self.instruction_names = [
            inst.__name__
            for opcode, inst in instruction_set
        ]
        self.instruction_mapping = {
            inst.__name__: (opcode, inst)
            for opcode, inst in instruction_set
        }
        self.macro_names = list(MACRO_SET.keys())
        self.word_registers = registers['word']
        self.byte_registers = registers['byte']
        self.keywords = set(self.instruction_names + self.macro_names + self.word_registers + self.byte_registers)
        self.tokenizer = Tokenizer({
            'instruction_names': self.instruction_names,
            'macro_names': self.macro_names,
            'word_registers': self.word_registers,
            'byte_registers': self.byte_registers,
        })
        self._reset_state()

    def assemble_file(self, filename):
        '''
        Assemble source code file and write to executable file
        '''
        logger.info('Assembling %s...', filename)
        source_code = ''
        with open(filename, 'rt') as input_file:
            source_code = input_file.read()
        opcode = self.assemble_code(source_code)
        binary_filename = os.path.splitext(filename)[0]
        exe = Executable(1, opcode)
        exe.save_to_file(binary_filename)
        logger.info('Assembled %s (%d bytes).', binary_filename, exe.length)

    def assemble_code(self, source_code):
        '''
        Assemble source code and return opcode
        '''
        self._reset_state()
        self.source_code = source_code
        logger.debug('Tokenizing...')
        tokenized_code = self._tokenize()
        logger.debug('Tokenized.')
        logger.debug('Collecting labels...')
        self._collect_labels(tokenized_code)
        logger.debug('Collected.')
        logger.debug('Generating opcode...')
        self._generate_opcode(tokenized_code)  # generate opcode first time: label addresses not yet good
        self._generate_opcode(tokenized_code)  # generate opcode second time: label addresses good
        logger.debug('Generated.')
        self._log_code()
        return self.opcode

    def _log_code(self):
        logger.debug('===CODE===')
        max_line_opcode_length = max(
            len(line_opcode)
            for line_number, opcode_pos, line_opcode, source_line, tokens in self.augmented_opcode
        )
        if max_line_opcode_length > MAX_LINE_OPCODE_LENGTH:
            max_line_opcode_length = MAX_LINE_OPCODE_LENGTH
        for line_number, opcode_pos, line_opcode, source_line, tokens in self.augmented_opcode:
            line_label_names = [token.value for token in tokens if token.type == TokenType.LABEL]
            if not line_label_names and not line_opcode:
                continue
            logger.debug(
                ' '.join([
                    '{:4}'.format(line_number),
                    utils.word_to_str(opcode_pos),
                    ' '.join([utils.byte_to_str(op) for op in line_opcode]),
                    ' ' if line_opcode else '',
                    '   ' * (max_line_opcode_length - len(line_opcode)),
                    source_line,
                ])
            )

    def _reset_state(self):
        self.source_code = ''
        self.labels = {}
        self.opcode = []
        self.augmented_opcode = []
        self.consts = {}

    def _tokenize(self):
        tokenized_code = []
        for idx, source_line in enumerate(self.source_code.split('\n')):
            line_number = idx + 1
            try:
                meaningful_tokens = [
                    token
                    for token in self.tokenizer.tokenize(source_line)
                    if token.type != TokenType.COMMENT
                ]
            except AldebaranError as ex:
                msg, pos = ex.args
                _raise_error(source_line, line_number, pos, str(msg), ex.__class__)
            tokenized_code.append((
                line_number,
                source_line,
                meaningful_tokens,
            ))
        return tokenized_code

    def _collect_labels(self, tokenized_code):
        for line_number, source_line, tokens in tokenized_code:
            for token in tokens:
                if token.type == TokenType.LABEL:
                    label_name = token.value
                    if label_name in self.labels:
                        _raise_error(source_line, line_number, token.pos, 'Label already defined', LabelError)
                    if label_name in self.keywords:
                        _raise_error(source_line, line_number, token.pos, 'Label name cannot be keyword', LabelError)
                    self.labels[label_name] = 0

    def _generate_opcode(self, tokenized_code):
        self.opcode = []
        self.augmented_opcode = []
        self.consts = {}
        opcode_pos = 0
        for line_number, source_line, tokens in tokenized_code:
            line_opcode = self._parse_line(line_number, source_line, tokens, opcode_pos)
            self.opcode += line_opcode
            self.augmented_opcode.append((
                line_number,
                opcode_pos,
                line_opcode,
                source_line,
                tokens,
            ))
            opcode_pos += len(line_opcode)

    def _parse_line(self, line_number, source_line, tokens, opcode_pos):
        state = ParserState.LABEL
        inst_name = None
        macro_name = None
        args = []
        for token in tokens:
            if state == ParserState.LABEL:
                if token.type == TokenType.LABEL:
                    self.labels[token.value] = opcode_pos
                elif token.type == TokenType.INSTRUCTION:
                    state = ParserState.INSTRUCTION
                    inst_name = token.value
                elif token.type == TokenType.MACRO:
                    state = ParserState.MACRO
                    macro_name = token.value
                else:
                    _raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            elif state == ParserState.INSTRUCTION:
                if token.type in ARGUMENT_TYPES:
                    args.append(token)
                else:
                    _raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            elif state == ParserState.MACRO:
                if token.type in ARGUMENT_TYPES:
                    args.append(token)
                else:
                    _raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            elif state == ParserState.ARGUMENTS:
                if token.type in ARGUMENT_TYPES:
                    args.append(token)
                else:
                    _raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            else:
                _raise_error(source_line, line_number, token.pos, 'Unknown parser state: {}'.format(state), ParserError)
        if inst_name is not None:
            line_opcode = self._parse_instruction(inst_name, args, source_line, line_number, opcode_pos)
        elif macro_name is not None:
            line_opcode = self._parse_macro(macro_name, args, source_line, line_number)
        else:
            line_opcode = []
        return line_opcode

    def _parse_instruction(self, inst_name, args, source_line, line_number, opcode_pos):
        inst_opcode, inst = self.instruction_mapping[inst_name]
        operands = self._parse_operands(args, source_line, line_number, opcode_pos)
        if len(operands) < inst.operand_count:
            _raise_error(source_line, line_number, None, 'Not enough operands: {} instead of {}'.format(len(operands), inst.operand_count), OperandError)
        if len(operands) > inst.operand_count:
            _raise_error(source_line, line_number, None, 'Too many operands: {} instead of {}'.format(len(operands), inst.operand_count), OperandError)
        # TODO: check inst.oplens
        # if None: no check
        # otherwise list of strings of B|W|*
        opcode = [inst_opcode]
        for operand_opcode in operands:
            opcode += operand_opcode
        return opcode

    def _parse_macro(self, macro_name, args, source_line, line_number):
        try:
            macro_class = MACRO_SET[macro_name]
        except KeyError:
            _raise_error(source_line, line_number, None, 'Unknown macro: {}'.format(macro_name), MacroError)
        macro = macro_class(self, source_line, line_number)
        return macro.run(args)

    def _parse_operands(self, args, source_line, line_number, opcode_pos):
        operands = []
        for arg in args:
            if arg.type == TokenType.STRING_LITERAL:
                _raise_error(source_line, line_number, arg.pos, 'String literal cannot be instruction operand: {}'.format(arg.value), OperandError)
            if arg.type == TokenType.VARIABLE:
                arg = self.substitute_variable(arg, source_line, line_number)
            if arg.type in LABEL_REFERENCE_TYPES:
                arg = self._substitute_label(arg, source_line, line_number, opcode_pos)
            try:
                operands.append(get_operand_opcode(arg))
            except AldebaranError as ex:
                orig_msg = '{}({})'.format(
                    ex.__class__.__name__,
                    str(ex),
                )
                arg_name = '{}({})'.format(
                    arg.type.name,
                    arg.value,
                )
                _raise_error(
                    source_line,
                    line_number,
                    arg.pos,
                    'Could not parse operand {} due to {}'.format(arg_name, orig_msg),
                    OperandError,
                )
        return operands

    def _substitute_label(self, arg, source_line, line_number, opcode_pos):
        assert arg.type in LABEL_REFERENCE_TYPES
        if arg.type == TokenType.ADDRESS_LABEL or arg.type == TokenType.IDENTIFIER:
            label_name = arg.value
        else:
            label_name = arg.value.base
        try:
            label_address = self.labels[label_name]
        except KeyError:
            _raise_error(source_line, line_number, arg.pos, 'Unknown label reference: {}'.format(arg.value), LabelError)
        relative_address = label_address - opcode_pos
        new_type = {
            TokenType.ADDRESS_LABEL: TokenType.ADDRESS_WORD_LITERAL,
            TokenType.IDENTIFIER: TokenType.ADDRESS_WORD_LITERAL,
            TokenType.REL_REF_LABEL_REG: TokenType.REL_REF_WORD_REG,
            TokenType.REL_REF_LABEL_BYTE: TokenType.REL_REF_WORD_BYTE,
            TokenType.REL_REF_LABEL: TokenType.REL_REF_WORD,
        }[arg.type]
        if arg.type == TokenType.ADDRESS_LABEL or arg.type == TokenType.IDENTIFIER:
            new_value = relative_address
        else:
            new_value = Reference(relative_address, arg.value.offset, arg.value.length)
        return Token(
            new_type,
            new_value,
            arg.pos,
        )

    def substitute_variable(self, arg, source_line, line_number):
        '''
        Substitute variable with its value (token)
        '''
        assert arg.type == TokenType.VARIABLE
        try:
            new_token = self.consts[arg.value]
        except KeyError:
            _raise_error(source_line, line_number, arg.pos, 'Unknown variable reference: {}'.format(arg.value), VariableError)
        return Token(
            new_token.type,
            new_token.value,
            arg.pos,
        )

    def substitute_variables(self, args, source_line, line_number):
        '''
        Substitute variables in a list of argument tokens
        '''
        return [
            self.substitute_variable(arg, source_line, line_number) if arg.type == TokenType.VARIABLE else arg
            for arg in args
        ]


ParserState = Enum('ParserState', [  # pylint: disable=invalid-name
    'LABEL',
    'INSTRUCTION',
    'MACRO',
    'ARGUMENTS',
])


MAX_LINE_OPCODE_LENGTH = 15


def _raise_error(code, line_number, pos, error_message, exception):
    logger.error('ERROR in line %d:', line_number)
    logger.error(code)
    if pos is not None:
        logger.error(' ' * pos + '^')
    raise exception(error_message)


# pylint: disable=missing-docstring

class AssemblerError(AldebaranError):
    pass


class LabelError(AssemblerError):
    pass


class ParserError(AssemblerError):
    pass


class OperandError(AssemblerError):
    pass
