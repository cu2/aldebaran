import unittest

from utils.tokenizer import Tokenizer, Token, Reference
from instructions.operands import WORD_REGISTERS, BYTE_REGISTERS


class TestTokenizer(unittest.TestCase):

    def setUp(self):
        self.tokenizer = Tokenizer({
            'instruction_names': ['MOV', 'JMP'],
            'macro_names': ['DEF'],
            'word_registers': WORD_REGISTERS,
            'byte_registers': BYTE_REGISTERS,
        })

    def test_label_alone(self):
        tokens = self.tokenizer.tokenize('labelname:')
        self.assertListEqual(tokens, [
            Token('LABEL', 'labelname'),
        ])

    def test_code_alone(self):
        tokens = self.tokenizer.tokenize('mov ax 0100')
        self.assertListEqual(tokens, [
            Token('INSTRUCTION', 'MOV'),
            Token('WORD_REGISTER', 'AX'),
            Token('WORD_LITERAL', 256),
        ])

    def test_label_code_comment(self):
        tokens = self.tokenizer.tokenize('labelname: mov ax 0100  # comment text')
        self.assertListEqual(tokens, [
            Token('LABEL', 'labelname'),
            Token('INSTRUCTION', 'MOV'),
            Token('WORD_REGISTER', 'AX'),
            Token('WORD_LITERAL', 256),
            Token('COMMENT', ' comment text'),
        ])

    def test_random_case(self):
        tokens = self.tokenizer.tokenize('LabeL: mOv aX 00fF')
        self.assertListEqual(tokens, [
            Token('LABEL', 'LabeL'),
            Token('INSTRUCTION', 'MOV'),
            Token('WORD_REGISTER', 'AX'),
            Token('WORD_LITERAL', 255),
        ])

    def test_random_whitespace(self):
        tokens = self.tokenizer.tokenize('			mov  	  ax      	   	    0100  			      ')
        self.assertListEqual(tokens, [
            Token('INSTRUCTION', 'MOV'),
            Token('WORD_REGISTER', 'AX'),
            Token('WORD_LITERAL', 256),
        ])

    def test_every_token_type(self):
        tokens = self.tokenizer.tokenize('label: other_label: MOV AX AL 1234 12 ^1234 [AX] [AX+12]B [1234]B [1234+56] [1234+AX] JMP third_label DEF "hello world with kinda # comment"  # actual comment')
        self.assertListEqual(tokens, [
            Token('LABEL', 'label'),
            Token('LABEL', 'other_label'),
            Token('INSTRUCTION', 'MOV'),
            Token('WORD_REGISTER', 'AX'),
            Token('BYTE_REGISTER', 'AL'),
            Token('WORD_LITERAL', 4660),
            Token('BYTE_LITERAL', 18),
            Token('ADDRESS_WORD_LITERAL', 4660),
            Token('ABS_REF_REG', Reference('AX', None, 'W')),
            Token('ABS_REF_REG', Reference('AX', 18, 'B')),
            Token('REL_REF_WORD', Reference(4660, None, 'B')),
            Token('REL_REF_WORD_BYTE', Reference(4660, 86, 'W')),
            Token('REL_REF_WORD_REG', Reference(4660, 'AX', 'W')),
            Token('INSTRUCTION', 'JMP'),
            Token('IDENTIFIER', 'third_label'),
            Token('MACRO', 'DEF'),
            Token('STRING_LITERAL', 'hello world with kinda # comment'),
            Token('COMMENT', ' actual comment')
        ])
