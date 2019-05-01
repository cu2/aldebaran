import unittest
from unittest.mock import Mock

from instructions.operands import (
    OpLen, OpType,
    Operand,
    _get_opbyte,
)
from hardware.ram import RAM
from hardware.cpu.cpu import (
    CPU, UnknownOpcodeError,
)


class TestStack(unittest.TestCase):

    def setUp(self):
        self.instruction_class_1 = Mock()
        self.instruction_class_1.__name__ = 'INST1'
        self.instruction_object_1 = Mock()
        self.instruction_class_1.return_value = self.instruction_object_1
        self.instruction_object_1.operands = [
            Operand(OpLen.WORD, OpType.VALUE, None, 0xAABB, None, None),
        ]

        self.instruction_class_2 = Mock()
        self.instruction_class_2.__name__ = 'INST2'
        self.instruction_object_2 = Mock()
        self.instruction_class_2.return_value = self.instruction_object_2
        self.instruction_object_2.operands = [
            Operand(OpLen.BYTE, OpType.REGISTER, 'AH', None, None, None),
        ]

        self.instruction_set = [
            (0x01, self.instruction_class_1),
            (0x02, self.instruction_class_2),
        ]

        self.program = []
        self.program += [
            self.instruction_set[0][0],
            _get_opbyte(OpLen.WORD, OpType.VALUE),
            0xAA, 0xBB,
        ]
        self.program += [
            self.instruction_set[1][0],
            _get_opbyte(OpLen.BYTE, OpType.REGISTER, 'AH'),
        ]

        self.system_addresses = {
            'entry_point': 0x1234,
            'bottom_of_stack': 0xABCD,
            'IVT': 0xF000,
        }
        self.operand_buffer_size = 16
        self.cpu = CPU(self.system_addresses, self.instruction_set, self.operand_buffer_size)
        self.registers = Mock()
        self.ram = RAM(0x10000)
        for idx, opcode in enumerate(self.program):
            self.ram.write_byte(self.system_addresses['entry_point'] + idx, opcode)
        self.stack = Mock()
        self.interrupt_controller = Mock()
        self.device_controller = Mock()
        self.timer = Mock()
        self.cpu.register_architecture(
            self.registers, self.stack, self.ram,
            self.interrupt_controller,
            self.device_controller,
            self.timer,
        )

    def test_instructions(self):
        self.instruction_object_1.run.return_value = self.cpu.ip + 4
        self.instruction_object_2.run.return_value = self.cpu.ip + 4 + 2
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'])
        self.cpu.step()
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'] + 4)
        self.cpu.step()
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'] + 4 + 2)
        with self.assertRaises(UnknownOpcodeError):
            self.cpu.step()

        self.assertEqual(self.instruction_class_1.call_count, 1)
        self.assertEqual(self.instruction_class_1.call_args_list[0][0][0], self.cpu)
        self.assertListEqual(
            self.instruction_class_1.call_args_list[0][0][1],
            self.ram._content[self.system_addresses['entry_point'] + 1:][:self.operand_buffer_size],
        )
        self.assertEqual(self.instruction_object_1.run.call_count, 1)

        self.assertEqual(self.instruction_class_2.call_count, 1)
        self.assertEqual(self.instruction_class_2.call_args_list[0][0][0], self.cpu)
        self.assertListEqual(
            self.instruction_class_2.call_args_list[0][0][1],
            self.ram._content[self.system_addresses['entry_point'] + 4 + 1:][:self.operand_buffer_size],
        )
        self.assertEqual(self.instruction_object_2.run.call_count, 1)

    def test_jump(self):
        self.instruction_object_1.run.return_value = self.cpu.ip
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'])
        self.cpu.step()
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'])
        self.cpu.step()
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'])

        self.assertEqual(self.instruction_class_1.call_count, 2)
        self.assertEqual(self.instruction_class_1.call_args_list[0][0][0], self.cpu)
        self.assertListEqual(
            self.instruction_class_1.call_args_list[0][0][1],
            self.ram._content[self.system_addresses['entry_point'] + 1:][:self.operand_buffer_size],
        )
        self.assertEqual(self.instruction_class_1.call_args_list[1][0][0], self.cpu)
        self.assertListEqual(
            self.instruction_class_1.call_args_list[1][0][1],
            self.ram._content[self.system_addresses['entry_point'] + 1:][:self.operand_buffer_size],
        )
        self.assertEqual(self.instruction_object_1.run.call_count, 2)

        self.assertEqual(self.instruction_class_2.call_count, 0)
        self.assertEqual(self.instruction_object_2.run.call_count, 0)

    def test_halt(self):
        self.instruction_object_1.run.return_value = self.cpu.ip + 4
        self.instruction_object_2.run.return_value = self.cpu.ip + 4 + 2
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'])
        self.cpu.step()
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'] + 4)
        self.cpu.halt = True
        self.cpu.step()
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'] + 4)
        self.cpu.step()
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'] + 4)

        self.assertEqual(self.instruction_class_1.call_count, 1)
        self.assertEqual(self.instruction_class_1.call_args_list[0][0][0], self.cpu)
        self.assertListEqual(
            self.instruction_class_1.call_args_list[0][0][1],
            self.ram._content[self.system_addresses['entry_point'] + 1:][:self.operand_buffer_size],
        )
        self.assertEqual(self.instruction_object_1.run.call_count, 1)

        self.assertEqual(self.instruction_class_2.call_count, 0)
        self.assertEqual(self.instruction_object_2.run.call_count, 0)

    def test_interrupt(self):
        self.instruction_object_1.run.return_value = self.cpu.ip + 4
        self.instruction_object_2.run.return_value = self.cpu.ip + 4 + 2
        self.assertEqual(self.cpu.ip, self.system_addresses['entry_point'])
        self.interrupt_controller.check.return_value = 0xFF
        self.ram.write_word(self.system_addresses['IVT'] + 2 * 0xFF, 0x4321)
        self.registers.get_flag.return_value = 1
        self.cpu.halt = True
        self.cpu.step()
        self.assertEqual(self.stack.push_flags.call_count, 1)
        self.assertEqual(self.registers.set_flag.call_count, 1)
        self.assertTupleEqual(
            self.registers.set_flag.call_args_list[0][0],
            ('interrupt', 0),
        )
        self.assertEqual(self.stack.push_word.call_count, 1)
        self.assertTupleEqual(
            self.stack.push_word.call_args_list[0][0],
            (self.system_addresses['entry_point'],),
        )
        self.assertEqual(self.cpu.ip, 0x4321)
        self.assertFalse(self.cpu.halt)

        self.assertEqual(self.instruction_class_1.call_count, 0)
        self.assertEqual(self.instruction_object_1.run.call_count, 0)
        self.assertEqual(self.instruction_class_2.call_count, 0)
        self.assertEqual(self.instruction_object_2.run.call_count, 0)
