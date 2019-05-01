import unittest

from hardware.cpu.registers import (
    Registers,
    InvalidRegisterNameError, InvalidRegisterValueError,
    InvalidFlagNameError, InvalidFlagValueError,
)


class TestRegisters(unittest.TestCase):

    def setUp(self):
        self.bottom_of_stack = 0x1234
        self.registers = Registers(self.bottom_of_stack)

    def test_get_register_ok(self):
        self.registers._registers['AX'] = 0x1234
        self.assertEqual(self.registers.get_register('AX'), 0x1234)
        self.assertEqual(self.registers.get_register('BX'), 0)
        self.assertEqual(self.registers.get_register('AL'), 0x34)
        self.assertEqual(self.registers.get_register('AH'), 0x12)
        self.assertEqual(self.registers.get_register('SP'), self.bottom_of_stack)

    def test_get_register_error(self):
        with self.assertRaises(InvalidRegisterNameError):
            self.registers.get_register('unknown')

    def test_set_register_ok(self):
        self.assertEqual(self.registers._registers['AX'], 0)
        self.assertEqual(self.registers._registers['BX'], 0)
        self.registers.set_register('AX', 0x1234)
        self.registers.set_register('BL', 0x78)
        self.registers.set_register('BH', 0x56)
        self.assertEqual(self.registers._registers['AX'], 0x1234)
        self.assertEqual(self.registers._registers['BX'], 0x5678)

    def test_set_register_error(self):
        with self.assertRaises(InvalidRegisterNameError):
            self.registers.set_register('unknown', 0x1234)
        with self.assertRaises(InvalidRegisterValueError):
            self.registers.set_register('AX', 'invalid')
        with self.assertRaises(InvalidRegisterValueError):
            self.registers.set_register('AX', -1)
        with self.assertRaises(InvalidRegisterValueError):
            self.registers.set_register('AX', 0x10000)
        with self.assertRaises(InvalidRegisterValueError):
            self.registers.set_register('AL', -1)
        with self.assertRaises(InvalidRegisterValueError):
            self.registers.set_register('AL', 0x100)


class TestFlags(unittest.TestCase):

    def setUp(self):
        self.bottom_of_stack = 0x1234
        self.registers = Registers(self.bottom_of_stack)

    def test_get_flag_ok(self):
        self.assertEqual(self.registers.get_flag('interrupt'), 1)
        self.registers._flags['interrupt'] = 0
        self.assertEqual(self.registers.get_flag('interrupt'), 0)

    def test_get_flag_error(self):
        with self.assertRaises(InvalidFlagNameError):
            self.registers.get_flag('unknown')

    def test_set_flag_ok(self):
        self.assertEqual(self.registers._flags['interrupt'], 1)
        self.registers.set_flag('interrupt', 0)
        self.assertEqual(self.registers._flags['interrupt'], 0)
        self.registers.set_flag('interrupt', 1)
        self.assertEqual(self.registers._flags['interrupt'], 1)

    def test_set_flag_error(self):
        with self.assertRaises(InvalidFlagNameError):
            self.registers.set_flag('unknown', 0)
        with self.assertRaises(InvalidFlagValueError):
            self.registers.set_flag('interrupt', 'invalid')
        with self.assertRaises(InvalidFlagValueError):
            self.registers.set_flag('interrupt', 2)
