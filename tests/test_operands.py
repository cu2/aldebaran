import unittest
from unittest.mock import Mock

from instructions.operands import (
    Operand, OpLen, OpType,
    get_operand_opcode, parse_operand_buffer,
    get_operand_value, set_operand_value,
    _get_reference_address, _get_opbyte,
    _get_register_code_by_name, _get_register_name_by_code,
    InvalidRegisterNameError, InvalidRegisterCodeError,
    InvalidTokenError,
    InvalidOperandError, InvalidWriteOperationError, InsufficientOperandBufferError,
)
from assembler.tokenizer import Token, Reference, TokenType
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
        with self.assertRaises(WordOutOfRangeError):
            get_operand_opcode(Token(TokenType.ADDRESS_WORD_LITERAL, 35000, 0))

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
        self.assertListEqual(get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('BX', 1, 'B'), 0)), [
            _get_opbyte(OpLen.BYTE, OpType.ABS_REF_REG, 'BX'),
            0x01,
        ])
        self.assertListEqual(get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('BX', -1, 'W'), 0)), [
            _get_opbyte(OpLen.WORD, OpType.ABS_REF_REG, 'BX'),
            0xFF,
        ])
        with self.assertRaises(InvalidRegisterNameError):
            get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('XX', 0, 'W'), 0))
        with self.assertRaises(ByteOutOfRangeError):
            get_operand_opcode(Token(TokenType.ABS_REF_REG, Reference('BX', 150, 'W'), 0))

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
        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [3])
        self.assertEqual(opcode_length, 4)

        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [2])
        self.assertEqual(opcode_length, 3)

    def test_address(self):
        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [3])
        self.assertEqual(opcode_length, 4)

        with self.assertRaises(InvalidOperandError):
            parse_operand_buffer([
                _get_opbyte(OpLen.BYTE, OpType.ADDRESS),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_register(self):
        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [1])
        self.assertEqual(opcode_length, 2)

        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [1])
        self.assertEqual(opcode_length, 2)

        with self.assertRaises(InvalidRegisterCodeError):
            parse_operand_buffer([
                _get_opbyte(OpLen.BYTE, OpType.REGISTER, 'BX'),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)
        with self.assertRaises(InvalidRegisterNameError):
            parse_operand_buffer([
                _get_opbyte(OpLen.WORD, OpType.REGISTER, 'XX'),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_abs_ref(self):
        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [2])
        self.assertEqual(opcode_length, 3)

        with self.assertRaises(InvalidRegisterCodeError):
            parse_operand_buffer([
                _get_opbyte(OpLen.WORD, OpType.ABS_REF_REG, 'AH'),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_rel_ref(self):
        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [3])
        self.assertEqual(opcode_length, 4)

        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
            _get_opbyte(OpLen.WORD, OpType.REL_REF_WORD_BYTE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OpLen.WORD)
        self.assertEqual(operands[0].optype, OpType.REL_REF_WORD_BYTE)
        self.assertIsNone(operands[0].opreg)
        self.assertIsNone(operands[0].opvalue)
        self.assertEqual(operands[0].opbase, -1)
        self.assertEqual(operands[0].opoffset, 255)
        self.assertListEqual(operand_buffer_indices, [4])
        self.assertEqual(opcode_length, 5)

        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [3])
        self.assertEqual(opcode_length, 4)

    def test_multiple_operands(self):
        operands, operand_buffer_indices, opcode_length = parse_operand_buffer([
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
        self.assertListEqual(operand_buffer_indices, [1, 4])
        self.assertEqual(opcode_length, 5)

    def test_not_enough_buffer(self):
        with self.assertRaises(InsufficientOperandBufferError):
            parse_operand_buffer([
                _get_opbyte(OpLen.WORD, OpType.VALUE),
                0xFF,
            ], 1)


class TestGetOperandValue(unittest.TestCase):

    def setUp(self):
        self.cpu = Mock()
        self.ram = Mock()
        self.cpu.registers.get_register.return_value = 0xA0B0
        self.ram.read_byte = Mock()
        self.ram.read_byte.return_value = 0xCC
        self.ram.read_word = Mock()
        self.ram.read_word.return_value = 0xCCDD

    def test_value(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.BYTE, OpType.VALUE, None, 255, None, None),
            self.cpu, self.ram, 0x1234,
        ), 255)
        self.assertEqual(get_operand_value(
            Operand(OpLen.WORD, OpType.VALUE, None, 65535, None, None),
            self.cpu, self.ram, 0x1234,
        ), 65535)
        self.assertEqual(self.cpu.registers.get_register.call_count, 0)
        self.assertEqual(self.ram.read_byte.call_count, 0)
        self.assertEqual(self.ram.read_word.call_count, 0)

    def test_address(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.WORD, OpType.ADDRESS, None, 1, None, None),
            self.cpu, self.ram, 0x1234,
        ), 0x1235)
        self.assertEqual(get_operand_value(
            Operand(OpLen.WORD, OpType.ADDRESS, None, -1, None, None),
            self.cpu, self.ram, 0x1234,
        ), 0x1233)
        self.assertEqual(self.cpu.registers.get_register.call_count, 0)
        self.assertEqual(self.ram.read_byte.call_count, 0)
        self.assertEqual(self.ram.read_word.call_count, 0)

    def test_register(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.WORD, OpType.REGISTER, 'AX', 1, None, None),
            self.cpu, self.ram, 0x1234,
        ), 0xA0B0)
        self.assertEqual(self.cpu.registers.get_register.call_count, 1)
        self.assertEqual(self.cpu.registers.get_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.ram.read_byte.call_count, 0)
        self.assertEqual(self.ram.read_word.call_count, 0)

    def test_abs_ref_reg_b(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.BYTE, OpType.ABS_REF_REG, 'AX', None, None, 0x01),
            self.cpu, self.ram, 0x1234,
        ), 0xCC)
        self.assertEqual(self.cpu.registers.get_register.call_count, 1)
        self.assertEqual(self.cpu.registers.get_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.ram.read_byte.call_count, 1)
        self.assertEqual(self.ram.read_byte.call_args_list[0][0][0], 0xA0B1)
        self.assertEqual(self.ram.read_word.call_count, 0)

    def test_abs_ref_reg_w(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.WORD, OpType.ABS_REF_REG, 'AX', None, None, 0x01),
            self.cpu, self.ram, 0x1234,
        ), 0xCCDD)
        self.assertEqual(self.cpu.registers.get_register.call_count, 1)
        self.assertEqual(self.cpu.registers.get_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.ram.read_byte.call_count, 0)
        self.assertEqual(self.ram.read_word.call_count, 1)
        self.assertEqual(self.ram.read_word.call_args_list[0][0][0], 0xA0B1)

    def test_rel_ref_word(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD, None, None, -0x1111, None),
            self.cpu, self.ram, 0x1234,
        ), 0xCC)
        self.assertEqual(self.cpu.registers.get_register.call_count, 0)
        self.assertEqual(self.ram.read_byte.call_count, 1)
        self.assertEqual(self.ram.read_byte.call_args_list[0][0][0], 0x0123)
        self.assertEqual(self.ram.read_word.call_count, 0)

    def test_rel_ref_word_byte(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_BYTE, None, None, -0x1111, 0x22),
            self.cpu, self.ram, 0x1234,
        ), 0xCC)
        self.assertEqual(self.cpu.registers.get_register.call_count, 0)
        self.assertEqual(self.ram.read_byte.call_count, 1)
        self.assertEqual(self.ram.read_byte.call_args_list[0][0][0], 0x0145)
        self.assertEqual(self.ram.read_word.call_count, 0)

    def test_rel_ref_word_reg(self):
        self.assertEqual(get_operand_value(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_REG, 'AX', None, -0x1111, None),
            self.cpu, self.ram, 0x1234,
        ), 0xCC)
        self.assertEqual(self.cpu.registers.get_register.call_count, 1)
        self.assertEqual(self.cpu.registers.get_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.ram.read_byte.call_count, 1)
        self.assertEqual(self.ram.read_byte.call_args_list[0][0][0], 0xA1D3)
        self.assertEqual(self.ram.read_word.call_count, 0)


class TestSetOperandValue(unittest.TestCase):

    def setUp(self):
        self.cpu = Mock()
        self.ram = Mock()
        self.cpu.registers.get_register.return_value = 0xA0B0
        self.cpu.registers.set_register = Mock()
        self.ram.write_byte = Mock()
        self.ram.write_word = Mock()

    def test_readonly(self):
        with self.assertRaises(InvalidWriteOperationError):
            set_operand_value(
                Operand(OpLen.BYTE, OpType.VALUE, None, 255, None, None),
                0x44,
                self.cpu, self.ram, 0x1234,
            )
        with self.assertRaises(InvalidWriteOperationError):
            set_operand_value(
                Operand(OpLen.WORD, OpType.ADDRESS, None, -1, None, None),
                0x3344,
                self.cpu, self.ram, 0x1234,
            )

    def test_register(self):
        set_operand_value(
            Operand(OpLen.WORD, OpType.REGISTER, 'AX', 1, None, None),
            0x3344,
            self.cpu, self.ram, 0x1234,
        )
        self.assertEqual(self.cpu.registers.get_register.call_count, 0)
        self.assertEqual(self.cpu.registers.set_register.call_count, 1)
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][1], 0x3344)
        self.assertEqual(self.ram.write_byte.call_count, 0)
        self.assertEqual(self.ram.write_word.call_count, 0)

    def test_abs_ref_reg_b(self):
        set_operand_value(
            Operand(OpLen.BYTE, OpType.ABS_REF_REG, 'AX', None, None, 0x01),
            0x33,
            self.cpu, self.ram, 0x1234,
        )
        self.assertEqual(self.cpu.registers.get_register.call_count, 1)
        self.assertEqual(self.cpu.registers.get_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.ram.write_byte.call_count, 1)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][0], 0xA0B1)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][1], 0x33)
        self.assertEqual(self.ram.write_word.call_count, 0)

    def test_abs_ref_reg_w(self):
        set_operand_value(
            Operand(OpLen.WORD, OpType.ABS_REF_REG, 'AX', None, None, 0x01),
            0x3344,
            self.cpu, self.ram, 0x1234,
        )
        self.assertEqual(self.cpu.registers.get_register.call_count, 1)
        self.assertEqual(self.cpu.registers.get_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.ram.write_byte.call_count, 0)
        self.assertEqual(self.ram.write_word.call_count, 1)
        self.assertEqual(self.ram.write_word.call_args_list[0][0][0], 0xA0B1)
        self.assertEqual(self.ram.write_word.call_args_list[0][0][1], 0x3344)

    def test_rel_ref_word(self):
        set_operand_value(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD, None, None, -0x1111, None),
            0x33,
            self.cpu, self.ram, 0x1234,
        )
        self.assertEqual(self.cpu.registers.get_register.call_count, 0)
        self.assertEqual(self.ram.write_byte.call_count, 1)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][0], 0x0123)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][1], 0x33)
        self.assertEqual(self.ram.write_word.call_count, 0)

    def test_rel_ref_word_byte(self):
        set_operand_value(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_BYTE, None, None, -0x1111, 0x22),
            0x33,
            self.cpu, self.ram, 0x1234,
        )
        self.assertEqual(self.cpu.registers.get_register.call_count, 0)
        self.assertEqual(self.ram.write_byte.call_count, 1)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][0], 0x0145)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][1], 0x33)
        self.assertEqual(self.ram.write_word.call_count, 0)

    def test_rel_ref_word_reg(self):
        set_operand_value(
            Operand(OpLen.BYTE, OpType.REL_REF_WORD_REG, 'AX', None, -0x1111, None),
            0x33,
            self.cpu, self.ram, 0x1234,
        )
        self.assertEqual(self.cpu.registers.get_register.call_count, 1)
        self.assertEqual(self.cpu.registers.get_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.ram.write_byte.call_count, 1)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][0], 0xA1D3)
        self.assertEqual(self.ram.write_byte.call_args_list[0][0][1], 0x33)
        self.assertEqual(self.ram.write_word.call_count, 0)


class TestGetReferenceAddress(unittest.TestCase):

    def setUp(self):
        self.cpu = Mock()

    def test_abs_ref_reg(self):
        self.cpu.registers.get_register.return_value = 0xA0B0
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
        self.cpu.registers.get_register.return_value = 0xA0B0
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
