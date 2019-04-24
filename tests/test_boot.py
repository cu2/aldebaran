import unittest
from unittest.mock import Mock, patch

from utils import boot
from utils import executable


class TestBootImage(unittest.TestCase):

    def setUp(self):
        self.mock_mgr = Mock()
        self.mock_mgr.__enter__ = Mock()
        self.mock_mgr.__exit__ = Mock()

    def test_write_byte(self):
        boot_image = boot.BootImage(4)
        self.assertListEqual(boot_image.content, [0, 0, 0, 0])
        boot_image.write_byte(2, 0xFF)
        self.assertListEqual(boot_image.content, [0, 0, 0xFF, 0])

    def test_write_word(self):
        boot_image = boot.BootImage(4)
        self.assertListEqual(boot_image.content, [0, 0, 0, 0])
        boot_image.write_word(1, 0x1234)
        self.assertListEqual(boot_image.content, [0, 0x12, 0x34, 0])

    @patch('builtins.open')
    def test_save(self, mock_open):
        mock_file = MockFile([])
        self.mock_mgr.__enter__.return_value = mock_file
        mock_open.return_value = self.mock_mgr
        boot_image = boot.BootImage(4)
        boot_image.content = [0, 1, 2, 3]
        self.assertListEqual(mock_file.new_content, [])
        boot_image.save('nofile')
        self.assertListEqual(mock_file.new_content, [0, 1, 2, 3])
        self.assertTupleEqual(self.mock_mgr.__exit__.call_args_list[0][0], (None, None, None))

    @patch('builtins.open')
    def test_load(self, mock_open):
        mock_file = MockFile([4, 5, 6, 7])
        self.mock_mgr.__enter__.return_value = mock_file
        mock_open.return_value = self.mock_mgr
        boot_image = boot.BootImage(2)
        self.assertEqual(boot_image.size, 2)
        self.assertListEqual(boot_image.content, [0, 0])
        boot_image.load('nofile')
        self.assertEqual(boot_image.size, 4)
        self.assertListEqual(boot_image.content, [4, 5, 6, 7])
        self.assertTupleEqual(self.mock_mgr.__exit__.call_args_list[0][0], (None, None, None))


class TestBootLoader(unittest.TestCase):

    def setUp(self):
        self.ram = Mock()

    def test_load_image(self):
        boot_image = boot.BootImage(8)
        boot_image.write_word(0, 0x0123)
        boot_image.write_word(2, 0x4567)
        boot_image.write_word(4, 0x89AB)
        boot_image.write_word(6, 0xCDEF)
        boot_loader = boot.BootLoader(self.ram)
        boot_loader.load_image(5, boot_image)

        self.assertEqual(self.ram.write_byte.call_count, 8)
        write_byte_calls = self.ram.write_byte.call_args_list
        self.assertTupleEqual(write_byte_calls[0][0], (5, 0x01))
        self.assertTupleEqual(write_byte_calls[1][0], (6, 0x23))
        self.assertTupleEqual(write_byte_calls[2][0], (7, 0x45))
        self.assertTupleEqual(write_byte_calls[3][0], (8, 0x67))
        self.assertTupleEqual(write_byte_calls[4][0], (9, 0x89))
        self.assertTupleEqual(write_byte_calls[5][0], (10, 0xAB))
        self.assertTupleEqual(write_byte_calls[6][0], (11, 0xCD))
        self.assertTupleEqual(write_byte_calls[7][0], (12, 0xEF))

    def test_load_executable(self):
        boot_exe = executable.Executable(
            version=1,
            opcode=[0x12, 0x34, 0x56],
        )
        boot_loader = boot.BootLoader(self.ram)
        boot_loader.load_executable(5, boot_exe)

        self.assertEqual(self.ram.write_byte.call_count, 3)
        write_byte_calls = self.ram.write_byte.call_args_list
        self.assertTupleEqual(write_byte_calls[0][0], (5, 0x12))
        self.assertTupleEqual(write_byte_calls[1][0], (6, 0x34))
        self.assertTupleEqual(write_byte_calls[2][0], (7, 0x56))


class MockFile:

    def __init__(self, content):
        self.content = content
        self.new_content = []

    def read(self):
        return bytes(self.content)

    def write(self, new_content_bytes):
        self.new_content = list(new_content_bytes)
