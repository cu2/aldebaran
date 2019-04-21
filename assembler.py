#!/usr/bin/env python

import argparse
from enum import Enum
import os

from instructions.instruction_set import INSTRUCTION_SET
from instructions.operands import WORD_REGISTERS, BYTE_REGISTERS, get_operand_opcode
from utils.executable import Executable
from utils.tokenizer import Tokenizer, Token, TokenType, Reference, ARGUMENT_TYPES, LABEL_REFERENCE_TYPES
from utils import utils


ParserState = Enum('ParserState', [
    'LABEL',
    'INSTRUCTION',
    'MACRO',
    'ARGUMENTS',
])


class AssemblerError(Exception):
    pass


class LabelError(AssemblerError):
    pass


class ParserError(AssemblerError):
    pass


class MacroError(AssemblerError):
    pass


class OperandError(AssemblerError):
    pass


class Assembler:

    def __init__(self, instruction_set, registers):
        self.instruction_names = [
            inst.__name__
            for opcode, inst in instruction_set
        ]
        self.instruction_mapping = {
            inst.__name__: (opcode, inst)
            for opcode, inst in instruction_set
        }
        self.macro_names = ['DAT', 'DATN']
        self.word_registers = registers['word']
        self.byte_registers = registers['byte']
        self.tokenizer = Tokenizer({
            'instruction_names': self.instruction_names,
            'macro_names': self.macro_names,
            'word_registers': self.word_registers,
            'byte_registers': self.byte_registers,
        })
        self.keywords = set(self.instruction_names + self.macro_names + self.word_registers + self.byte_registers)
        self._reset_state()

    def _reset_state(self):
        self.source_code = ''
        self.labels = {}
        self.opcode = []
        self.augmented_opcode = []

    def _log_error(self, code, line_number, pos, error_message):
        # TODO: log instead of print
        print('ERROR in line {}: {}'.format(line_number, error_message))
        print(code)
        if pos is not None:
            print(' ' * pos + '^')

    def _raise_error(self, code, line_number, pos, error_message, exception):
        self._log_error(code, line_number, pos, error_message)
        raise exception(error_message)

    def _tokenize(self):
        tokenized_code = []
        for idx, source_line in enumerate(self.source_code.split('\n')):
            meaningful_tokens = [
                token
                for token in self.tokenizer.tokenize(source_line)
                if token.type != TokenType.COMMENT
            ]
            tokenized_code.append((
                idx + 1,
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
                        self._raise_error(source_line, line_number, token.pos, 'Label already defined', LabelError)
                    if label_name in self.keywords:
                        self._raise_error(source_line, line_number, token.pos, 'Label name cannot be keyword', LabelError)
                    self.labels[label_name] = 0

    def _substitute_label(self, arg, source_line, line_number, opcode_pos):
        assert arg.type in LABEL_REFERENCE_TYPES
        if arg.type == TokenType.ADDRESS_LABEL or arg.type == TokenType.IDENTIFIER:
            label_name = arg.value
        else:
            label_name = arg.value.base
        try:
            label_address = self.labels[label_name]
        except KeyError:
            self._raise_error(source_line, line_number, arg.pos, 'Unknown label reference: {}'.format(arg.value), LabelError)
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

    def _parse_operands(self, args, source_line, line_number, opcode_pos):
        operands = []
        for arg in args:
            if arg.type == TokenType.STRING_LITERAL:
                self._raise_error(source_line, line_number, arg.pos, 'String literal cannot be instruction operand: {}'.format(arg.value), OperandError)
            if arg.type in LABEL_REFERENCE_TYPES:
                arg = self._substitute_label(arg, source_line, line_number, opcode_pos)
            try:
                operands.append(get_operand_opcode(arg))
            except Exception:
                self._raise_error(source_line, line_number, arg.pos, 'Could not parse operand: {}'.format(arg), OperandError)
        return operands

    def _parse_instruction(self, inst_name, args, source_line, line_number, opcode_pos):
        inst_opcode, inst = self.instruction_mapping[inst_name]
        operands = self._parse_operands(args, source_line, line_number, opcode_pos)
        if len(operands) < inst.operand_count:
            self._raise_error(source_line, line_number, None, 'Not enough operands: {} instead of {}'.format(len(operands), inst.operand_count), OperandError)
        if len(operands) > inst.operand_count:
            self._raise_error(source_line, line_number, None, 'Too many operands: {} instead of {}'.format(len(operands), inst.operand_count), OperandError)
        # TODO: check inst.oplens
        # if None: no check
        # otherwise list of B|W|BW
        opcode = [inst_opcode]
        for operand_opcode in operands:
            opcode += operand_opcode
        return opcode

    def _parse_macro(self, macro_name, args, source_line, line_number, opcode_pos):
        if macro_name == 'DAT':
            opcode = []
            for arg in args:
                if arg.type == TokenType.STRING_LITERAL:
                    opcode += utils.string_to_bytes(arg.value)
                elif arg.type == TokenType.BYTE_LITERAL:
                    opcode.append(arg.value)
                elif arg.type == TokenType.WORD_LITERAL:
                    opcode += utils.word_to_bytes(arg.value)
                else:
                    self._raise_error(source_line, line_number, arg.pos, 'Unknown macro parameter: {}'.format(arg), MacroError)
            return opcode
        if macro_name == 'DATN':
            if len(args) != 2:
                self._raise_error(source_line, line_number, arg.pos, 'Macro DATN requires exactly 2 parameters, not {}'.format(len(args)), MacroError)
            repeat_arg, value_arg = args
            if repeat_arg.type not in {TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL}:
                self._raise_error(source_line, line_number, arg.pos, 'The first parameter of macro DATN must be a byte or word literal, not {}'.format(repeat_arg.type), MacroError)
            repeat_number = repeat_arg.value
            if value_arg.type not in {TokenType.BYTE_LITERAL, TokenType.WORD_LITERAL, TokenType.STRING_LITERAL}:
                self._raise_error(source_line, line_number, arg.pos, 'The second parameter of macro DATN must be a byte, word or string literal, not {}'.format(value_arg.type), MacroError)
            opcode = []
            for _ in range(repeat_number):
                if value_arg.type == TokenType.STRING_LITERAL:
                    opcode += utils.string_to_bytes(value_arg.value)
                elif value_arg.type == TokenType.BYTE_LITERAL:
                    opcode.append(value_arg.value)
                else:
                    opcode += utils.word_to_bytes(value_arg.value)
            return opcode
        # TODO: add more macros
        self._raise_error(source_line, line_number, None, 'Unknown macro: {}'.format(macro_name), MacroError)

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
                    self._raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            elif state == ParserState.INSTRUCTION:
                if token.type in ARGUMENT_TYPES:
                    args.append(token)
                else:
                    self._raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            elif state == ParserState.MACRO:
                if token.type in ARGUMENT_TYPES:
                    args.append(token)
                else:
                    self._raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            elif state == ParserState.ARGUMENTS:
                if token.type in ARGUMENT_TYPES:
                    args.append(token)
                else:
                    self._raise_error(source_line, line_number, token.pos, 'Unexpected token: {}'.format(token.value), ParserError)
            else:
                self._raise_error(source_line, line_number, token.pos, 'Unknown parser state: {}'.format(state), ParserError)
        if inst_name is not None:
            line_opcode = self._parse_instruction(inst_name, args, source_line, line_number, opcode_pos)
        elif macro_name is not None:
            line_opcode = self._parse_macro(macro_name, args, source_line, line_number, opcode_pos)
        else:
            line_opcode = []
        return line_opcode

    def _generate_opcode(self, tokenized_code):
        self.opcode = []
        self.augmented_opcode = []
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

    def assemble_code(self, source_code):
        self._reset_state()
        self.source_code = source_code
        tokenized_code = self._tokenize()
        self._collect_labels(tokenized_code)
        self._generate_opcode(tokenized_code)  # generate opcode first time: label addresses not yet good
        self._generate_opcode(tokenized_code)  # generate opcode second time: label addresses good
        print('===CODE===')
        for line_number, opcode_pos, line_opcode, source_line, tokens in self.augmented_opcode:
            line_label_names = [token.value for token in tokens if token.type == TokenType.LABEL]
            if len(line_label_names) == 0 and len(line_opcode) == 0:
                continue
            print(
                '{:4}'.format(line_number),
                utils.word_to_str(opcode_pos),
                ' '.join([utils.byte_to_str(op) for op in line_opcode]),
                '   ' * (10 - len(line_opcode)),
                source_line,
            )
        return self.opcode

    def assemble_file(self, filename):
        print('Assembling {}...'.format(filename))
        source_code = ''
        with open(filename, 'rt') as f:
            source_code = f.read()
        opcode = self.assemble_code(source_code)
        binary_filename = os.path.splitext(filename)[0]
        exe = Executable(1, opcode)
        exe.save_to_file(binary_filename)
        print('Assembled {} ({} bytes).'.format(binary_filename, exe.length))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        nargs='+',
        help='ALD source code file'
    )
    # TODO: add verbosity
    args = parser.parse_args()
    assembler = Assembler(
        instruction_set=INSTRUCTION_SET,
        registers={
            'byte': BYTE_REGISTERS,
            'word': WORD_REGISTERS,
        },
    )
    for source_file in args.file:
        assembler.assemble_file(source_file)
