import unittest
from unittest.mock import Mock

from instructions.operands import _get_register_code_by_name, _get_register_name_by_code,\
    InvalidRegisterNameError, InvalidRegisterCodeError,\
    _get_opbyte,\
    get_operand_opcode, OpLen, OpType,\
    InvalidTokenLengthError, InvalidTokenError,\
    parse_operand_buffer, InvalidOperandError, InsufficientOperandBufferError,\
    _get_reference_address, Operand
from utils.tokenizer import Token, Reference, TokenType
from utils.utils import WordOutOfRangeError, ByteOutOfRangeError


class TestGetOperandOpcode(unittest.TestCase):

    def test_literal(self):
        self.assertListEqual(get_operand_opcode(Token(TokenType.WORD_LITERAL, 65535, 0)), [
            _get_opbyte(OpLen.WORD, OpType.VALUE),
            0xFF, 0xFF,
        ])
        with self.assertRaises(WordOutOfRangeError):
            get_operand_opcode(Token(TokenType.WORD_LITERAL, 65536, 0))
        self.assertListEqual(get_operand_opcode(Token(TokenType.BYTE_LITERAL, 255, 0)), [
            _get_opbyte(OpLen.BYTE, OpType.VALUE),
            0xFF,
        ])
        with self.assertRaises(ByteOutOfRangeError):
            get_operand_opcode(Token(TokenType.BYTE_LITERAL, -1, 0))
        self.assertListEqual(get_operand_opcode(Token(TokenType.ADDRESS_WORD_LITERAL, -1, 0)), [
            _get_opbyte(OpLen.WORD, OpType.ADDRESS),
            0xFF, 0xFF,
        ])

    def test_register(self):
        self.assertListEqual(get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', 0)), [
            _get_opbyte(OpLen.WORD, OpType.REGISTER, 'AX'),
        ])
        self.assertListEqual(get_operand_opcode(Token(TokenType.BYTE_REGISTER, 'AL', 0)), [
            _get_opbyte(OpLen.BYTE, OpType.REGISTER, 'AL'),
        ])
        self.assertListEqual(get_operand_opcode(Token(TokenType.BYTE_REGISTER, 'AH', 0)), [
            _get_opbyte(OpLen.BYTE, OpType.REGISTER, 'AH'),
        ])
        with self.assertRaises(InvalidRegisterNameError):
            get_operand_opcode(Token(TokenType.WORD_REGISTER, 'XX', 0))

    def test_abs_ref(self):
        self.assertListEqual(get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('BX', 0, 'B'), 0)), [
            _get_opbyte(OpLen.BYTE, OpType.ABS_REF_REG, 'BX'),
            0x00,
        ])
        self.assertListEqual(get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('BX', -1, 'W'), 0)), [
            _get_opbyte(OpLen.WORD, OpType.ABS_REF_REG, 'BX'),
            0xFF,
        ])
        with self.assertRaises(InvalidRegisterNameError):
            get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('XX', 0, 'W'), 0))
        with self.assertRaises(ByteOutOfRangeError):
            get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('BX', 256, 'W'), 0))
        with self.assertRaises(InvalidTokenLengthError):
            get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('AX', 0, '?'), 0))

    def test_rel_ref(self):
        self.assertListEqual(get_operand_opcode(Token(TokenType.REL_REF_WORD, Reference(-1, 0, 'B'), 0)), [
            _get_opbyte(OpLen.BYTE, OpType.REL_REF_WORD),
            0xFF, 0xFF,
        ])
        with self.assertRaises(WordOutOfRangeError):
            get_operand_opcode(Token(TokenType.REL_REF_WORD, Reference(35000, 0, 'B'), 0))
        with self.assertRaises(WordOutOfRangeError):
            get_operand_opcode(Token(TokenType.REL_REF_WORD, Reference(-35000, 0, 'B'), 0))
        self.assertListEqual(get_operand_opcode(Token(TokenType.REL_REF_WORD_BYTE, Reference(-1, 255, 'B'), 0)), [
            _get_opbyte(OpLen.BYTE, OpType.REL_REF_WORD_BYTE),
            0xFF, 0xFF, 0xFF,
        ])
        self.assertListEqual(get_operand_opcode(Token(TokenType.REL_REF_WORD_REG, Reference(-1, 'BX', 'B'), 0)), [
            _get_opbyte(OpLen.BYTE, OpType.REL_REF_WORD_REG, 'BX'),
            0xFF, 0xFF,
        ])
        with self.assertRaises(InvalidRegisterNameError):
            get_operand_opcode(Token(TokenType.REL_REF_WORD_REG, Reference(12000, 'XX', 'B'), 0))

    def test_other(self):
        with self.assertRaises(InvalidTokenError):
            get_operand_opcode(Token(TokenType.STRING_LITERAL, 0, 0))
        with self.assertRaises(InvalidTokenError):
            get_operand_opcode(Token('unknown', 0, 0))


class TestParseOperandBuffer(unittest.TestCase):

    def test_value(self):
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.VALUE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.VALUE)
        self.assertIsNone(operands[0].opreg)
        self.assertEqual(operands[0].opvalue, 65535)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.BYTE, OpType.VALUE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.BYTE)
        self.assertEqual(operands[0].optype, OpType.VALUE)
        self.assertIsNone(operands[0].opreg)
        self.assertEqual(operands[0].opvalue, 255)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 3)

    def test_address(self):
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.ADDRESS),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.ADDRESS)
        self.assertIsNone(operands[0].opreg)
        self.assertEqual(operands[0].opvalue, -1)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)
        with self.assertRaises(InvalidOperandError):
            parse_operand_buffer([
                _get_opbyte(OpLen.BYTE, OpType.ADDRESS),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_register(self):
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.REGISTER, 'BX'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.REGISTER)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 2)
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.BYTE, OpType.REGISTER, 'AH'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.BYTE)
        self.assertEqual(operands[0].optype, OpType.REGISTER)
        self.assertEqual(operands[0].opreg, 'AH')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 2)
        with self.assertRaises(InvalidRegisterCodeError):
            parse_operand_buffer([
                _get_opbyte(OpLen.BYTE, OpType.REGISTER, 'BX'),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_abs_ref(self):
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.ABS_REF_REG, 'BX'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.ABS_REF_REG)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertEqual(operands[0].opoffset, -1)
        self.assertEqual(opcode_length, 3)
        with self.assertRaises(InvalidRegisterCodeError):
            parse_operand_buffer([
                _get_opbyte(OpLen.WORD, OpType.ABS_REF_REG, 'AH'),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_rel_ref(self):
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.REL_REF_WORD),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.REL_REF_WORD)
        self.assertIsNone(operands[0].opreg)
        self.assertIsNone(operands[0].opvalue)
        self.assertEqual(operands[0].opbase, -1)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)

        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.REL_REF_WORD_BYTE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.REL_REF_WORD_BYTE)
        self.assertIsNone(operands[0].opreg)
        self.assertIsNone(operands[0].opvalue)
        self.assertEqual(operands[0].opbase, -1)
        self.assertEqual(operands[0].opoffset, 0xFF)
        self.assertEqual(opcode_length, 5)

        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.REL_REF_WORD_REG, 'BX'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.REL_REF_WORD_REG)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertEqual(operands[0].opbase, -1)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)

    def test_multiple_operands(self):
        operands, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.REGISTER, 'BX'),
            _get_opbyte(OpLen.WORD, OpType.VALUE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 2)
        self.assertEqual(len(operands), 2)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.REGISTER)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(operands[1].oplen, OpLen.WORD)
        self.assertEqual(operands[1].optype, OpType.VALUE)
        self.assertIsNone(operands[1].opreg)
        self.assertEqual(operands[1].opvalue, 65535)
        self.assertIsNone(operands[1].opbase)
        self.assertIsNone(operands[1].opoffset)
        self.assertEqual(opcode_length, 5)

    def test_not_enough_buffer(self):
        with self.assertRaises(InsufficientOperandBufferError):
            parse_operand_buffer([
                _get_opbyte(OpLen.WORD, OpType.VALUE),
                0xFF,
            ], 1)


class TestGetReferenceAddress(unittest.TestCase):

    def setUp(self):
        self.cpu = Mock()

    def test_abs_ref_reg(self):
        self.cpu.get_register = Mock()
        self.cpu.get_register.return_value = 0xA0B0
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.ABS_REF_REG, 'AX', None, None, 0x01),
            self.cpu,
            0x1234,
        ), 0xA0B1)
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.ABS_REF_REG, 'AX', None, None, -0x01),
            self.cpu,
            0x1234,
        ), 0xA0AF)

    def test_rel_ref_word(self):
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD, None, None, 0x1111, None),
            self.cpu,
            0x1234,
        ), 0x2345)
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD, None, None, -0x1111, None),
            self.cpu,
            0x1234,
        ), 0x0123)

    def test_rel_ref_word_byte(self):
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_BYTE, None, None, 0x1111, 0x22),
            self.cpu,
            0x1234,
        ), 0x2367)
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_BYTE, None, None, -0x1111, 0x22),
            self.cpu,
            0x1234,
        ), 0x0145)

    def test_rel_ref_word_reg(self):
        self.cpu.get_register = Mock()
        self.cpu.get_register.return_value = 0xA0B0
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_REG, 'AX', None, 0x1111, None),
            self.cpu,
            0x1234,
        ), 0xC3F5)
        self.assertEqual(_get_reference_address(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_REG, 'AX', None, -0x1111, None),
            self.cpu,
            0x1234,
        ), 0xA1D3)


class TestGetOpbyte(unittest.TestCase):

    def test(self):
        self.assertEqual(_get_opbyte(OpLen.BYTE, OpType.VALUE), 0x00)
        self.assertEqual(_get_opbyte(OpLen.WORD, OpType.VALUE), 0x80)
        self.assertEqual(_get_opbyte(OpLen.BYTE, OpType.VALUE, 'AX'), 0x00)
        self.assertEqual(_get_opbyte(OpLen.WORD, OpType.VALUE, 'AX'), 0x80)
        self.assertEqual(_get_opbyte(OpLen.BYTE, OpType.VALUE, 'BX'), 0x01)
        self.assertEqual(_get_opbyte(OpLen.WORD, OpType.VALUE, 'BX'), 0x81)
        self.assertEqual(_get_opbyte(OpLen.BYTE, OpType.EXTENDED), 0x70)
        self.assertEqual(_get_opbyte(OpLen.WORD, OpType.EXTENDED), 0xF0)
        self.assertEqual(_get_opbyte(OpLen.BYTE, OpType.EXTENDED, 'AX'), 0x70)
        self.assertEqual(_get_opbyte(OpLen.WORD, OpType.EXTENDED, 'AX'), 0xF0)
        self.assertEqual(_get_opbyte(OpLen.BYTE, OpType.EXTENDED, 'BX'), 0x71)
        self.assertEqual(_get_opbyte(OpLen.WORD, OpType.EXTENDED, 'BX'), 0xF1)


class TestRegisters(unittest.TestCase):

    def test_get_register_code_by_name(self):
        self.assertEqual(_get_register_code_by_name('AX'), 0)
        self.assertEqual(_get_register_code_by_name('AL'), 8)
        self.assertEqual(_get_register_code_by_name('AH'), 9)
        with self.assertRaises(InvalidRegisterNameError):
            _get_register_code_by_name('XX')

    def test_get_register_name_by_code(self):
        self.assertEqual(_get_register_name_by_code(0), 'AX')
        self.assertEqual(_get_register_name_by_code(8), 'AL')
        self.assertEqual(_get_register_name_by_code(9), 'AH')
        with self.assertRaises(InvalidRegisterCodeError):
            _get_register_name_by_code(-1)
        with self.assertRaises(InvalidRegisterCodeError):
            _get_register_name_by_code(16)
