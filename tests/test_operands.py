import unittest

from instructions.operands import get_register_code_by_name, get_register_name_by_code,\
    InvalidRegisterNameError, InvalidRegisterCodeError,\
    get_opbyte,\
    get_operand_opcode, OPLEN_BYTE, OPLEN_WORD,\
    OPTYPE_VALUE, OPTYPE_ADDRESS, OPTYPE_REGISTER, OPTYPE_ABS_REF_REG,\
    OPTYPE_REL_REF_WORD, OPTYPE_REL_REF_WORD_BYTE, OPTYPE_REL_REF_WORD_REG,\
    InvalidTokenLengthError,\
    parse_operand_buffer, InvalidOperandError, InsufficientOperandBufferError
from utils.tokenizer import Token, Reference, UnknownTokenError
from utils.utils import WordOutOfRangeError, ByteOutOfRangeError


class TestRegisters(unittest.TestCase):

    def test_get_register_code_by_name(self):
        self.assertEqual(get_register_code_by_name('AX'), 0)
        self.assertEqual(get_register_code_by_name('AL'), 8)
        self.assertEqual(get_register_code_by_name('AH'), 9)
        with self.assertRaises(InvalidRegisterNameError):
            get_register_code_by_name('XX')

    def test_get_register_name_by_code(self):
        self.assertEqual(get_register_name_by_code(0), 'AX')
        self.assertEqual(get_register_name_by_code(8), 'AL')
        self.assertEqual(get_register_name_by_code(9), 'AH')
        with self.assertRaises(InvalidRegisterCodeError):
            get_register_name_by_code(-1)
        with self.assertRaises(InvalidRegisterCodeError):
            get_register_name_by_code(16)


class TestGetOpbyte(unittest.TestCase):

    def test(self):
        self.assertEqual(get_opbyte(OPLEN_BYTE, OPTYPE_VALUE), 0)
        self.assertEqual(get_opbyte(OPLEN_WORD, OPTYPE_VALUE), 128)
        self.assertEqual(get_opbyte(OPLEN_BYTE, OPTYPE_VALUE, 'AX'), 0)
        self.assertEqual(get_opbyte(OPLEN_WORD, OPTYPE_VALUE, 'AX'), 128)
        self.assertEqual(get_opbyte(OPLEN_BYTE, OPTYPE_VALUE, 'BX'), 1)
        self.assertEqual(get_opbyte(OPLEN_WORD, OPTYPE_VALUE, 'BX'), 129)


class TestGetOperandOpcode(unittest.TestCase):

    def test_literal(self):
        self.assertListEqual(get_operand_opcode(Token('WORD_LITERAL', 65535, 0)), [
            get_opbyte(OPLEN_WORD, OPTYPE_VALUE),
            0xFF, 0xFF,
        ])
        with self.assertRaises(WordOutOfRangeError):
            get_operand_opcode(Token('WORD_LITERAL', 65536, 0))
        self.assertListEqual(get_operand_opcode(Token('BYTE_LITERAL', 255, 0)), [
            get_opbyte(OPLEN_BYTE, OPTYPE_VALUE),
            0xFF,
        ])
        with self.assertRaises(ByteOutOfRangeError):
            get_operand_opcode(Token('BYTE_LITERAL', -1, 0))
        self.assertListEqual(get_operand_opcode(Token('ADDRESS_WORD_LITERAL', 65535, 0)), [
            get_opbyte(OPLEN_WORD, OPTYPE_ADDRESS),
            0xFF, 0xFF,
        ])

    def test_register(self):
        self.assertListEqual(get_operand_opcode(Token('WORD_REGISTER', 'AX', 0)), [
            get_opbyte(OPLEN_WORD, OPTYPE_REGISTER, 'AX'),
        ])
        self.assertListEqual(get_operand_opcode(Token('BYTE_REGISTER', 'AL', 0)), [
            get_opbyte(OPLEN_BYTE, OPTYPE_REGISTER, 'AL'),
        ])
        self.assertListEqual(get_operand_opcode(Token('BYTE_REGISTER', 'AH', 0)), [
            get_opbyte(OPLEN_BYTE, OPTYPE_REGISTER, 'AH'),
        ])
        with self.assertRaises(InvalidRegisterNameError):
            get_operand_opcode(Token('WORD_REGISTER', 'XX', 0))

    def test_abs_ref(self):
        self.assertListEqual(get_operand_opcode(Token('ABS_REF_REG', Reference('BX', 0, 'B'), 0)), [
            get_opbyte(OPLEN_BYTE, OPTYPE_ABS_REF_REG, 'BX'),
            0x00,
        ])
        self.assertListEqual(get_operand_opcode(Token('ABS_REF_REG', Reference('BX', 255, 'W'), 0)), [
            get_opbyte(OPLEN_WORD, OPTYPE_ABS_REF_REG, 'BX'),
            0xFF,
        ])
        with self.assertRaises(InvalidRegisterNameError):
            get_operand_opcode(Token('ABS_REF_REG', Reference('XX', 0, 'W'), 0))
        with self.assertRaises(ByteOutOfRangeError):
            get_operand_opcode(Token('ABS_REF_REG', Reference('BX', 256, 'W'), 0))
        with self.assertRaises(InvalidTokenLengthError):
            get_operand_opcode(Token('ABS_REF_REG', Reference('AX', 0, '?'), 0))

    def test_rel_ref(self):
        self.assertListEqual(get_operand_opcode(Token('REL_REF_WORD', Reference(65535, 0, 'B'), 0)), [
            get_opbyte(OPLEN_BYTE, OPTYPE_REL_REF_WORD),
            0xFF, 0xFF,
        ])
        with self.assertRaises(WordOutOfRangeError):
            get_operand_opcode(Token('REL_REF_WORD', Reference(65536, 0, 'B'), 0))
        self.assertListEqual(get_operand_opcode(Token('REL_REF_WORD_BYTE', Reference(65535, 255, 'B'), 0)), [
            get_opbyte(OPLEN_BYTE, OPTYPE_REL_REF_WORD_BYTE),
            0xFF, 0xFF, 0xFF,
        ])
        self.assertListEqual(get_operand_opcode(Token('REL_REF_WORD_REG', Reference(65535, 'BX', 'B'), 0)), [
            get_opbyte(OPLEN_BYTE, OPTYPE_REL_REF_WORD_REG, 'BX'),
            0xFF, 0xFF,
        ])
        with self.assertRaises(InvalidRegisterNameError):
            get_operand_opcode(Token('REL_REF_WORD_REG', Reference(65535, 'XX', 'B'), 0))

    def test_other(self):
        with self.assertRaises(UnknownTokenError):
            get_operand_opcode(Token('unknown', 0, 0))


class TestParseOperandBuffer(unittest.TestCase):

    def test_value(self):
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_VALUE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_VALUE)
        self.assertIsNone(operands[0].opreg)
        self.assertEqual(operands[0].opvalue, 65535)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_BYTE, OPTYPE_VALUE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_BYTE)
        self.assertEqual(operands[0].optype, OPTYPE_VALUE)
        self.assertIsNone(operands[0].opreg)
        self.assertEqual(operands[0].opvalue, 255)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 3)

    def test_address(self):
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_ADDRESS),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_ADDRESS)
        self.assertIsNone(operands[0].opreg)
        self.assertEqual(operands[0].opvalue, 65535)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)
        with self.assertRaises(InvalidOperandError):
            parse_operand_buffer([
                get_opbyte(OPLEN_BYTE, OPTYPE_ADDRESS),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_register(self):
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_REGISTER, 'BX'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_REGISTER)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 2)
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_BYTE, OPTYPE_REGISTER, 'AH'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_BYTE)
        self.assertEqual(operands[0].optype, OPTYPE_REGISTER)
        self.assertEqual(operands[0].opreg, 'AH')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 2)
        with self.assertRaises(InvalidRegisterCodeError):
            parse_operand_buffer([
                get_opbyte(OPLEN_BYTE, OPTYPE_REGISTER, 'BX'),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_abs_ref(self):
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_ABS_REF_REG, 'BX'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_ABS_REF_REG)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertEqual(operands[0].opoffset, 255)
        self.assertEqual(opcode_length, 3)
        with self.assertRaises(InvalidRegisterCodeError):
            parse_operand_buffer([
                get_opbyte(OPLEN_WORD, OPTYPE_ABS_REF_REG, 'AH'),
                0xFF, 0xFF, 0xFF, 0xFF,
            ], 1)

    def test_rel_ref(self):
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_REL_REF_WORD),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_REL_REF_WORD)
        self.assertIsNone(operands[0].opreg)
        self.assertIsNone(operands[0].opvalue)
        self.assertEqual(operands[0].opbase, 65535)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)

        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_REL_REF_WORD_BYTE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_REL_REF_WORD_BYTE)
        self.assertIsNone(operands[0].opreg)
        self.assertIsNone(operands[0].opvalue)
        self.assertEqual(operands[0].opbase, 65535)
        self.assertEqual(operands[0].opoffset, 255)
        self.assertEqual(opcode_length, 5)

        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_REL_REF_WORD_REG, 'BX'),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 1)
        self.assertEqual(len(operands), 1)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_REL_REF_WORD_REG)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertEqual(operands[0].opbase, 65535)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(opcode_length, 4)

    def test_multiple_operands(self):
        operands, opcode_length = parse_operand_buffer([
            get_opbyte(OPLEN_WORD, OPTYPE_REGISTER, 'BX'),
            get_opbyte(OPLEN_WORD, OPTYPE_VALUE),
            0xFF, 0xFF, 0xFF, 0xFF,
        ], 2)
        self.assertEqual(len(operands), 2)
        self.assertEqual(operands[0].oplen, OPLEN_WORD)
        self.assertEqual(operands[0].optype, OPTYPE_REGISTER)
        self.assertEqual(operands[0].opreg, 'BX')
        self.assertIsNone(operands[0].opvalue)
        self.assertIsNone(operands[0].opbase)
        self.assertIsNone(operands[0].opoffset)
        self.assertEqual(operands[1].oplen, OPLEN_WORD)
        self.assertEqual(operands[1].optype, OPTYPE_VALUE)
        self.assertIsNone(operands[1].opreg)
        self.assertEqual(operands[1].opvalue, 65535)
        self.assertIsNone(operands[1].opbase)
        self.assertIsNone(operands[1].opoffset)
        self.assertEqual(opcode_length, 5)

    def test_not_enough_buffer(self):
        with self.assertRaises(InsufficientOperandBufferError):
            parse_operand_buffer([
                get_opbyte(OPLEN_WORD, OPTYPE_VALUE),
                0xFF,
            ], 1)
