import logging
import unittest

from assembler.assembler import Assembler, AssemblerError
from assembler.macros import MacroError, VariableError
from assembler.tokenizer import Token, TokenType, Reference
from instructions import instruction_set
from instructions.operands import WORD_REGISTERS, BYTE_REGISTERS, get_operand_opcode


class TestAssembler(unittest.TestCase):

    def setUp(self):
        self.instruction_set = [
            (0x12, instruction_set.arithmetic.ADD),
            (0x34, instruction_set.data_transfer.MOV),
            (0x56, instruction_set.control_flow.JMP),
            (0x78, instruction_set.misc.NOP),
            (0x9A, instruction_set.misc.SHUTDOWN),
        ]
        self.assembler = Assembler(
            instruction_set=self.instruction_set,
            registers={
                'byte': BYTE_REGISTERS,
                'word': WORD_REGISTERS,
            },
        )
        logging.getLogger('assembler').setLevel(logging.CRITICAL)

    def test_instructions(self):
        opcode = self.assembler.assemble_code('''
        NOP
        NOP
        SHUTDOWN
        ''')
        expected_opcode = [
            0x78,
            0x78,
            0x9A,
        ]
        self.assertListEqual(opcode, expected_opcode)

    def test_operands(self):
        opcode = self.assembler.assemble_code('''
        MOV AX 0x1234
        NOP
        SHUTDOWN
        ''')
        expected_opcode = [0x34]
        expected_opcode += get_operand_opcode(Token(
            TokenType.WORD_REGISTER,
            'AX',
            None,
        ))
        expected_opcode += get_operand_opcode(Token(
            TokenType.WORD_LITERAL,
            0x1234,
            None,
        ))
        expected_opcode += [0x78]
        expected_opcode += [0x9A]
        self.assertListEqual(opcode, expected_opcode)

    def test_label_ok(self):
        opcode = self.assembler.assemble_code('''
        loop:
        NOP
        JMP loop
        SHUTDOWN
        ''')
        expected_opcode = [0x78]
        expected_opcode += [0x56]
        expected_opcode += get_operand_opcode(Token(
            TokenType.ADDRESS_WORD_LITERAL,
            -1,
            None,
        ))
        expected_opcode += [0x9A]
        self.assertListEqual(opcode, expected_opcode)

    def test_label_error(self):
        with self.assertRaises(AssemblerError):
            self.assembler.assemble_code('''
            loop:
            NOP
            JMP other_loop
            SHUTDOWN
            ''')

    def test_macro_dat_and_datn(self):
        opcode = self.assembler.assemble_code('''
        MOV AX [stuff]
        NOP
        SHUTDOWN
        stuff: .DAT 0x1234 0x56 'ABC'
        .DATN 0x05 0xFF
        .DATN 0x03 0x1234
        .DATN 0x02 'ABC'
        ''')
        expected_opcode = [0x34]
        expected_opcode += get_operand_opcode(Token(
            TokenType.WORD_REGISTER,
            'AX',
            None,
        ))
        expected_opcode += get_operand_opcode(Token(
            TokenType.REL_REF_WORD,
            Reference(7, None, 'W'),
            None,
        ))
        expected_opcode += [0x78]
        expected_opcode += [0x9A]
        expected_opcode += [0x12, 0x34, 0x56, 0x41, 0x42, 0x43]
        expected_opcode += [0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        expected_opcode += [0x12, 0x34, 0x12, 0x34, 0x12, 0x34]
        expected_opcode += [0x41, 0x42, 0x43, 0x41, 0x42, 0x43]
        self.assertListEqual(opcode, expected_opcode)

    def test_macro_dat_and_datn_error(self):
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DAT
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DAT a
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 0x00 0x00 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN a 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 'a' 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 0x00 a
            ''')

    def test_macro_const(self):
        opcode = self.assembler.assemble_code('''
        .CONST $stuff 0x1234
        .CONST $other_stuff $stuff
        MOV AX $other_stuff
        NOP
        SHUTDOWN
        ''')
        expected_opcode = [0x34]
        expected_opcode += get_operand_opcode(Token(
            TokenType.WORD_REGISTER,
            'AX',
            None,
        ))
        expected_opcode += get_operand_opcode(Token(
            TokenType.WORD_LITERAL,
            0x1234,
            None,
        ))
        expected_opcode += [0x78]
        expected_opcode += [0x9A]
        self.assertListEqual(opcode, expected_opcode)

    def test_macro_const_error(self):
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST $x
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST a 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST $x a
            ''')
        with self.assertRaises(VariableError):
            self.assembler.assemble_code('''
            .CONST $x $y
            ''')
        with self.assertRaises(VariableError):
            self.assembler.assemble_code('''
            .CONST $x 0x00
            .CONST $x 0x01
            ''')
