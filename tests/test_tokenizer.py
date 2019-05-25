import unittest
from unittest.mock import Mock

from assembler.tokenizer import Tokenizer, Token, Reference, TokenType,\
    UnexpectedCharacterError, InvalidStringLiteralError, UnknownMacroError
from instructions.operands import WORD_REGISTERS, BYTE_REGISTERS


class TestTokenizer(unittest.TestCase):

    def setUp(self):
        self.tokenizer = Tokenizer({
            'instruction_names': ['MOV', 'JMP'],
            'macro_names': ['DAT'],
            'word_registers': WORD_REGISTERS,
            'byte_registers': BYTE_REGISTERS,
        })

    def test_label_alone(self):
        tokens = self.tokenizer.tokenize('labelname:')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'labelname', 0),
        ])

    def test_code_alone(self):
        tokens = self.tokenizer.tokenize('mov ax 0x0100')
        self.assertListEqual(tokens, [
            Token(TokenType.INSTRUCTION, 'MOV', 0),
            Token(TokenType.WORD_REGISTER, 'AX', 4),
            Token(TokenType.WORD_LITERAL, 256, 7),
        ])

    def test_label_code_comment(self):
        tokens = self.tokenizer.tokenize('labelname: mov ax 0x0100  # comment text')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'labelname', 0),
            Token(TokenType.INSTRUCTION, 'MOV', 11),
            Token(TokenType.WORD_REGISTER, 'AX', 15),
            Token(TokenType.WORD_LITERAL, 256, 18),
            Token(TokenType.COMMENT, ' comment text', 26),
        ])

    def test_random_case(self):
        tokens = self.tokenizer.tokenize('LabeL: mOv aX 0x00fF')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'LabeL', 0),
            Token(TokenType.INSTRUCTION, 'MOV', 7),
            Token(TokenType.WORD_REGISTER, 'AX', 11),
            Token(TokenType.WORD_LITERAL, 255, 14),
        ])

    def test_random_whitespace(self):
        tokens = self.tokenizer.tokenize('			mov  	  ax      	   	    0x0100  			      ')
        self.assertListEqual(tokens, [
            Token(TokenType.INSTRUCTION, 'MOV', 3),
            Token(TokenType.WORD_REGISTER, 'AX', 11),
            Token(TokenType.WORD_LITERAL, 256, 28),
        ])

    def test_almost_keyword_identifiers(self):
        tokens = self.tokenizer.tokenize('MOVE AXE ALL BEEF FF')
        self.assertListEqual(tokens, [
            Token(TokenType.IDENTIFIER, 'MOVE', 0),
            Token(TokenType.IDENTIFIER, 'AXE', 5),
            Token(TokenType.IDENTIFIER, 'ALL', 9),
            Token(TokenType.IDENTIFIER, 'BEEF', 13),
            Token(TokenType.IDENTIFIER, 'FF', 18),
        ])

    def test_every_token_type(self):
        tokens = self.tokenizer.tokenize('label: other_label: MOV AX AL 0x1234 0x12 ^0x1234 ^label [AX] [AX+0x12]B [AX-0x12]B [0x1234]B [label]B [0x1234+0x56] [label+0x56] [0x1234+AX] [label+AX] JMP third_label .DAT "hello world with kinda # comment" $var $$system_var[abc]  # actual comment')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'label', 0),
            Token(TokenType.LABEL, 'other_label', 7),
            Token(TokenType.INSTRUCTION, 'MOV', 20),
            Token(TokenType.WORD_REGISTER, 'AX', 24),
            Token(TokenType.BYTE_REGISTER, 'AL', 27),
            Token(TokenType.WORD_LITERAL, 4660, 30),
            Token(TokenType.BYTE_LITERAL, 18, 37),
            Token(TokenType.ADDRESS_WORD_LITERAL, 4660, 42),
            Token(TokenType.ADDRESS_LABEL, 'label', 50),
            Token(TokenType.ABS_REF_REG, Reference('AX', 0, 'W'), 57),
            Token(TokenType.ABS_REF_REG, Reference('AX', 18, 'B'), 62),
            Token(TokenType.ABS_REF_REG, Reference('AX', -18, 'B'), 73),
            Token(TokenType.REL_REF_WORD, Reference(4660, None, 'B'), 84),
            Token(TokenType.REL_REF_LABEL, Reference('label', None, 'B'), 94),
            Token(TokenType.REL_REF_WORD_BYTE, Reference(4660, 86, 'W'), 103),
            Token(TokenType.REL_REF_LABEL_BYTE, Reference('label', 86, 'W'), 117),
            Token(TokenType.REL_REF_WORD_REG, Reference(4660, 'AX', 'W'), 130),
            Token(TokenType.REL_REF_LABEL_REG, Reference('label', 'AX', 'W'), 142),
            Token(TokenType.INSTRUCTION, 'JMP', 153),
            Token(TokenType.IDENTIFIER, 'third_label', 157),
            Token(TokenType.MACRO, 'DAT', 169),
            Token(TokenType.STRING_LITERAL, 'hello world with kinda # comment', 174),
            Token(TokenType.VARIABLE, '$var', 209),
            Token(TokenType.SYSTEM_VARIABLE, '$$system_var[abc]', 214),
            Token(TokenType.COMMENT, ' actual comment', 233),
        ])

    def test_error_unexpected_char(self):
        with self.assertRaises(UnexpectedCharacterError):
            self.tokenizer.tokenize('label: mov ?')

    def test_error_invalid_string_literal(self):
        with self.assertRaises(InvalidStringLiteralError):
            self.tokenizer.tokenize('label: mov \'single quote \\\' between single quotes\'')

    def test_error_unknown_macro(self):
        with self.assertRaises(UnknownMacroError):
            self.tokenizer.tokenize('label: .mac x')
