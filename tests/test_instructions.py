import unittest
from unittest.mock import Mock

from instructions.instruction_set.data_transfer import MOV
from instructions.operands import get_operand_opcode, InvalidWriteOperationError
from utils.tokenizer import Token, TokenType


class TestGetOperand(unittest.TestCase):

    def setUp(self):
        self.cpu = Mock()
        self.cpu.ip = 0x1234

    def test_word(self):
        self.cpu.registers.get_register.return_value = 0xFFFF
        opcode = (
            get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', 0))
            + get_operand_opcode(Token(TokenType.WORD_LITERAL, 0xFFFE, 0))
        )
        inst = MOV(self.cpu, opcode)
        self.assertEqual(inst.get_operand(0), 65535)
        self.assertEqual(inst.get_signed_operand(0), -1)
        self.assertEqual(inst.get_operand(1), 65534)
        self.assertEqual(inst.get_signed_operand(1), -2)

    def test_byte(self):
        self.cpu.registers.get_register.return_value = 0xFF
        opcode = (
            get_operand_opcode(Token(TokenType.BYTE_REGISTER, 'AL', 0))
            + get_operand_opcode(Token(TokenType.BYTE_LITERAL, 0xFE, 0))
        )
        inst = MOV(self.cpu, opcode)
        self.assertEqual(inst.get_operand(0), 255)
        self.assertEqual(inst.get_signed_operand(0), -1)
        self.assertEqual(inst.get_operand(1), 254)
        self.assertEqual(inst.get_signed_operand(1), -2)


class TestSetOperand(unittest.TestCase):

    def setUp(self):
        self.cpu = Mock()
        self.cpu.ip = 0x1234
        self.cpu.registers.set_register = Mock()

    def test_unsigned_word(self):
        opcode = (
            get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', 0))
            + get_operand_opcode(Token(TokenType.WORD_LITERAL, 0xABCD, 0))
        )
        inst = MOV(self.cpu, opcode)
        inst.set_operand(0, 0x3344)
        self.assertEqual(self.cpu.registers.set_register.call_count, 1)
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][1], 0x3344)
        with self.assertRaises(InvalidWriteOperationError):
            inst.set_operand(1, 0x3344)

    def test_unsigned_byte(self):
        self.cpu.registers.get_register.return_value = 0xFF
        opcode = (
            get_operand_opcode(Token(TokenType.BYTE_REGISTER, 'AL', 0))
            + get_operand_opcode(Token(TokenType.BYTE_LITERAL, 0xAB, 0))
        )
        inst = MOV(self.cpu, opcode)
        inst.set_operand(0, 0x33)
        self.assertEqual(self.cpu.registers.set_register.call_count, 1)
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][0], 'AL')
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][1], 0x33)
        with self.assertRaises(InvalidWriteOperationError):
            inst.set_operand(1, 0x33)

    def test_signed_word(self):
        opcode = (
            get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', 0))
            + get_operand_opcode(Token(TokenType.WORD_LITERAL, 0xABCD, 0))
        )
        inst = MOV(self.cpu, opcode)
        inst.set_signed_operand(0, -1)
        self.assertEqual(self.cpu.registers.set_register.call_count, 1)
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][1], 0xFFFF)
        with self.assertRaises(InvalidWriteOperationError):
            inst.set_signed_operand(1, -1)

    def test_signed_byte(self):
        self.cpu.registers.get_register.return_value = 0xFF
        opcode = (
            get_operand_opcode(Token(TokenType.BYTE_REGISTER, 'AL', 0))
            + get_operand_opcode(Token(TokenType.BYTE_LITERAL, 0xAB, 0))
        )
        inst = MOV(self.cpu, opcode)
        inst.set_signed_operand(0, -1)
        self.assertEqual(self.cpu.registers.set_register.call_count, 1)
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][0], 'AL')
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][1], 0xFF)
        with self.assertRaises(InvalidWriteOperationError):
            inst.set_signed_operand(1, -1)


class TestDo(unittest.TestCase):

    def setUp(self):
        self.cpu = Mock()
        self.cpu.ip = 0x1234
        self.cpu.registers.set_register = Mock()

    def test_word(self):
        opcode = (
            get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', 0))
            + get_operand_opcode(Token(TokenType.WORD_LITERAL, 0xABCD, 0))
        )
        inst = MOV(self.cpu, opcode)
        inst.do()
        self.assertEqual(self.cpu.registers.set_register.call_count, 1)
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][0], 'AX')
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][1], 0xABCD)

    def test_byte(self):
        opcode = (
            get_operand_opcode(Token(TokenType.BYTE_REGISTER, 'AL', 0))
            + get_operand_opcode(Token(TokenType.BYTE_LITERAL, 0xAB, 0))
        )
        inst = MOV(self.cpu, opcode)
        inst.do()
        self.assertEqual(self.cpu.registers.set_register.call_count, 1)
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][0], 'AL')
        self.assertEqual(self.cpu.registers.set_register.call_args_list[0][0][1], 0xAB)

    def test_invalid(self):
        opcode = (
            get_operand_opcode(Token(TokenType.WORD_LITERAL, 0xABCD, 0))
            + get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', 0))
        )
        inst = MOV(self.cpu, opcode)
        with self.assertRaises(InvalidWriteOperationError):
            inst.do()
