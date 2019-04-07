import unittest
from unittest.mock import Mock

from utils.tokenizer import Tokenizer, Token, Reference, TokenType,\
    UnexpectedCharacterError, InvalidStringLiteralError
from instructions.operands import WORD_REGISTERS, BYTE_REGISTERS


class TestTokenizer(unittest.TestCase):

    def setUp(self):
        self.tokenizer = Tokenizer({
            'instruction_names': ['MOV', 'JMP'],
            'macro_names': ['DEF'],
            'word_registers': WORD_REGISTERS,
            'byte_registers': BYTE_REGISTERS,
        })
        self.tokenizer._log_error = Mock()

    def test_label_alone(self):
        tokens = self.tokenizer.tokenize('labelname:')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'labelname', 0),
        ])
        self.assertEqual(self.tokenizer._log_error.call_count, 0)

    def test_code_alone(self):
        tokens = self.tokenizer.tokenize('mov ax 0100')
        self.assertListEqual(tokens, [
            Token(TokenType.INSTRUCTION, 'MOV', 0),
            Token(TokenType.WORD_REGISTER, 'AX', 4),
            Token(TokenType.WORD_LITERAL, 256, 7),
        ])

    def test_label_code_comment(self):
        tokens = self.tokenizer.tokenize('labelname: mov ax 0100  # comment text')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'labelname', 0),
            Token(TokenType.INSTRUCTION, 'MOV', 11),
            Token(TokenType.WORD_REGISTER, 'AX', 15),
            Token(TokenType.WORD_LITERAL, 256, 18),
            Token(TokenType.COMMENT, ' comment text', 24),
        ])

    def test_random_case(self):
        tokens = self.tokenizer.tokenize('LabeL: mOv aX 00fF')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'LabeL', 0),
            Token(TokenType.INSTRUCTION, 'MOV', 7),
            Token(TokenType.WORD_REGISTER, 'AX', 11),
            Token(TokenType.WORD_LITERAL, 255, 14),
        ])

    def test_random_whitespace(self):
        tokens = self.tokenizer.tokenize('			mov  	  ax      	   	    0100  			      ')
        self.assertListEqual(tokens, [
            Token(TokenType.INSTRUCTION, 'MOV', 3),
            Token(TokenType.WORD_REGISTER, 'AX', 11),
            Token(TokenType.WORD_LITERAL, 256, 28),
        ])

    def test_every_token_type(self):
        tokens = self.tokenizer.tokenize('label: other_label: MOV AX AL 1234 12 ^1234 ^label [AX] [AX+12]B [AX-12]B [1234]B [label]B [1234+56] [label+56] [1234+AX] [label+AX] JMP third_label DEF "hello world with kinda # comment"  # actual comment')
        self.assertListEqual(tokens, [
            Token(TokenType.LABEL, 'label', 0),
            Token(TokenType.LABEL, 'other_label', 7),
            Token(TokenType.INSTRUCTION, 'MOV', 20),
            Token(TokenType.WORD_REGISTER, 'AX', 24),
            Token(TokenType.BYTE_REGISTER, 'AL', 27),
            Token(TokenType.WORD_LITERAL, 4660, 30),
            Token(TokenType.BYTE_LITERAL, 18, 35),
            Token(TokenType.ADDRESS_WORD_LITERAL, 4660, 38),
            Token(TokenType.ADDRESS_LABEL, 'label', 44),
            Token(TokenType.ABS_REF_REG, Reference('AX', None, 'W'), 51),
            Token(TokenType.ABS_REF_REG, Reference('AX', 18, 'B'), 56),
            Token(TokenType.ABS_REF_REG, Reference('AX', -18, 'B'), 65),
            Token(TokenType.REL_REF_WORD, Reference(4660, None, 'B'), 74),
            Token(TokenType.REL_REF_LABEL, Reference('label', None, 'B'), 82),
            Token(TokenType.REL_REF_WORD_BYTE, Reference(4660, 86, 'W'), 91),
            Token(TokenType.REL_REF_LABEL_BYTE, Reference('label', 86, 'W'), 101),
            Token(TokenType.REL_REF_WORD_REG, Reference(4660, 'AX', 'W'), 112),
            Token(TokenType.REL_REF_LABEL_REG, Reference('label', 'AX', 'W'), 122),
            Token(TokenType.INSTRUCTION, 'JMP', 133),
            Token(TokenType.IDENTIFIER, 'third_label', 137),
            Token(TokenType.MACRO, 'DEF', 149),
            Token(TokenType.STRING_LITERAL, 'hello world with kinda # comment', 153),
            Token(TokenType.COMMENT, ' actual comment', 189)
        ])

    def test_error_unexpected_char(self):
        with self.assertRaises(UnexpectedCharacterError):
            self.tokenizer.tokenize('label: mov ?')
        self.assertEqual(self.tokenizer._log_error.call_count, 1)

    def test_error_invalid_string_literal(self):
        with self.assertRaises(InvalidStringLiteralError):
            self.tokenizer.tokenize('label: mov \'single quote \\\' between single quotes\'')
        self.assertEqual(self.tokenizer._log_error.call_count, 1)
