import unittest

from hardware.memory.ram import RAM, SegfaultError


class TestRAM(unittest.TestCase):

    def test_read_byte_ok(self):
        ram = RAM(4)
        ram._content = [1, 2, 3, 4]
        self.assertEqual(ram.read_byte(0), 1)
        self.assertEqual(ram.read_byte(1), 2)
        self.assertEqual(ram.read_byte(2), 3)
        self.assertEqual(ram.read_byte(3), 4)

    def test_read_byte_segfault(self):
        ram = RAM(4)
        with self.assertRaises(SegfaultError):
            ram.read_byte(-1)
        with self.assertRaises(SegfaultError):
            ram.read_byte(4)

    def test_read_word_ok(self):
        ram = RAM(4)
        ram._content = [0x12, 0x34, 0x56, 0x78]
        self.assertEqual(ram.read_word(0), 0x1234)
        self.assertEqual(ram.read_word(1), 0x3456)
        self.assertEqual(ram.read_word(2), 0x5678)

    def test_read_word_segfault(self):
        ram = RAM(4)
        with self.assertRaises(SegfaultError):
            ram.read_word(-1)
        with self.assertRaises(SegfaultError):
            ram.read_word(3)

    def test_write_byte_ok(self):
        ram = RAM(4)
        self.assertListEqual(ram._content, [0, 0, 0, 0])
        ram.write_byte(2, 0xFF)
        self.assertListEqual(ram._content, [0, 0, 0xFF, 0])

    def test_write_byte_segfault(self):
        ram = RAM(4)
        with self.assertRaises(SegfaultError):
            ram.write_byte(-1, 0xFF)
        with self.assertRaises(SegfaultError):
            ram.write_byte(4, 0xFF)

    def test_write_word_ok(self):
        ram = RAM(4)
        self.assertListEqual(ram._content, [0, 0, 0, 0])
        ram.write_word(1, 0x1234)
        self.assertListEqual(ram._content, [0, 0x12, 0x34, 0])

    def test_write_word_segfault(self):
        ram = RAM(4)
        with self.assertRaises(SegfaultError):
            ram.write_word(-1, 0x1234)
        with self.assertRaises(SegfaultError):
            ram.write_word(3, 0x1234)
