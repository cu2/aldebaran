import unittest
from unittest.mock import Mock

from hardware.cpu.stack import (
    Stack,
    StackOverflowError, StackUnderflowError,
)


class TestStack(unittest.TestCase):

    def setUp(self):
        self.bottom_of_stack = 0x1234
        self.stack = Stack(self.bottom_of_stack)
        self.registers = Mock()
        self.ram = Mock()
        self.stack.register_architecture(self.registers, self.ram)

    def test_push_byte(self):
        sp = self.bottom_of_stack
        self.registers.get_register.return_value = sp
        self.stack.push_byte(0x12)
        self.assertTupleEqual(
            self.ram.write_byte.call_args_list[0][0],
            (sp, 0x12),
        )
        self.assertTupleEqual(
            self.registers.set_register.call_args_list[0][0],
            ('SP', sp - 1),
        )

    def test_push_byte_stack_overflow(self):
        self.registers.get_register.return_value = 0
        with self.assertRaises(StackOverflowError):
            self.stack.push_byte(0x12)

    def test_push_word(self):
        sp = self.bottom_of_stack
        self.registers.get_register.return_value = sp
        self.stack.push_word(0x1234)
        self.assertTupleEqual(
            self.ram.write_word.call_args_list[0][0],
            (sp - 1, 0x1234),
        )
        self.assertTupleEqual(
            self.registers.set_register.call_args_list[0][0],
            ('SP', sp - 2),
        )

    def test_push_word_stack_overflow(self):
        self.registers.get_register.return_value = 1
        with self.assertRaises(StackOverflowError):
            self.stack.push_word(0x1234)

    def test_pop_byte(self):
        sp = self.bottom_of_stack - 1
        self.registers.get_register.return_value = sp
        self.ram.read_byte.return_value = 0x12
        value = self.stack.pop_byte()
        self.assertEqual(value, 0x12)
        self.assertTupleEqual(
            self.ram.read_byte.call_args_list[0][0],
            (sp + 1,),
        )
        self.assertTupleEqual(
            self.registers.set_register.call_args_list[0][0],
            ('SP', sp + 1),
        )

    def test_pop_byte_stack_underflow(self):
        sp = self.bottom_of_stack
        self.registers.get_register.return_value = sp
        with self.assertRaises(StackUnderflowError):
            self.stack.pop_byte()

    def test_pop_word(self):
        sp = self.bottom_of_stack - 2
        self.registers.get_register.return_value = sp
        self.ram.read_word.return_value = 0x1234
        value = self.stack.pop_word()
        self.assertEqual(value, 0x1234)
        self.assertTupleEqual(
            self.ram.read_word.call_args_list[0][0],
            (sp + 1,),
        )
        self.assertTupleEqual(
            self.registers.set_register.call_args_list[0][0],
            ('SP', sp + 2),
        )

    def test_pop_word_stack_underflow(self):
        sp = self.bottom_of_stack - 1
        self.registers.get_register.return_value = sp
        with self.assertRaises(StackUnderflowError):
            self.stack.pop_word()

    def test_push_flags(self):
        sp = self.bottom_of_stack
        self.registers.get_register.return_value = sp
        self.registers.get_flag.return_value = 1
        self.stack.push_flags()
        self.assertEqual(self.registers.get_flag.call_count, 1)
        self.assertTupleEqual(
            self.registers.get_flag.call_args_list[0][0],
            ('interrupt',),
        )
        self.assertTupleEqual(
            self.ram.write_word.call_args_list[0][0],
            (sp - 1, 0x0001),
        )
        self.assertTupleEqual(
            self.registers.set_register.call_args_list[0][0],
            ('SP', sp - 2),
        )

    def test_pop_flags(self):
        sp = self.bottom_of_stack - 2
        self.registers.get_register.return_value = sp
        self.ram.read_word.return_value = 0x0001
        self.stack.pop_flags()
        self.assertEqual(self.registers.set_flag.call_count, 1)
        self.assertTupleEqual(
            self.registers.set_flag.call_args_list[0][0],
            ('interrupt', 1),
        )
        self.assertTupleEqual(
            self.ram.read_word.call_args_list[0][0],
            (sp + 1,),
        )
        self.assertTupleEqual(
            self.registers.set_register.call_args_list[0][0],
            ('SP', sp + 2),
        )
