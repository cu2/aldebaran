import unittest
from unittest.mock import Mock, patch

from utils import executable


class TestExecutable(unittest.TestCase):

    def setUp(self):
        self.mock_mgr = Mock()
        self.mock_mgr.__enter__ = Mock()
        self.mock_mgr.__exit__ = Mock()
        self.extra_header = [0xAA, 0xBB, 0xCC]
        self.opcode = [0x12, 0x34]

    @patch('builtins.open')
    def test_load_file_invalid_signature(self, mock_open):
        mock_file = MockFile(
            [0, 0, 0, 0, 0, 0, 0]
            + [1, 0, 13]
            + self.extra_header
            + self.opcode
        )
        self.mock_mgr.__enter__.return_value = mock_file
        mock_open.return_value = self.mock_mgr
        exe = executable.Executable()
        exe.load_from_file('nofile')
        self.assertEqual(exe.length, 10)
        self.assertEqual(exe.version, 0)
        self.assertEqual(exe.entry_point, 10)
        self.assertListEqual(exe.extra_header, [])
        self.assertListEqual(exe.opcode, [])
        self.assertEqual(self.mock_mgr.__exit__.call_args_list[0][0][0], executable.CorruptFileError)
        self.assertEqual(str(self.mock_mgr.__exit__.call_args_list[0][0][1]), 'Signature not valid')

    @patch('builtins.open')
    def test_load_file_ok(self, mock_open):
        mock_file = MockFile(
            executable.ALDEBARAN_EXECUTABLE_SIGNATURE
            + [1, 0, 13]
            + self.extra_header
            + self.opcode
        )
        self.mock_mgr.__enter__.return_value = mock_file
        mock_open.return_value = self.mock_mgr
        exe = executable.Executable()
        exe.load_from_file('nofile')
        self.assertEqual(exe.length, 15)
        self.assertEqual(exe.version, 1)
        self.assertEqual(exe.entry_point, 13)
        self.assertListEqual(exe.extra_header, self.extra_header)
        self.assertListEqual(exe.opcode, self.opcode)
        self.assertTupleEqual(self.mock_mgr.__exit__.call_args_list[0][0], (None, None, None))

    @patch('builtins.open')
    def test_save_file_ok(self, mock_open):
        mock_file = Mock()
        self.mock_mgr.__enter__.return_value = mock_file
        mock_open.return_value = self.mock_mgr
        exe = executable.Executable(
            version=1,
            opcode=self.opcode,
            extra_header=self.extra_header,
        )
        exe.save_to_file('nofile')
        first_write = list(mock_file.write.call_args_list[0][0][0])
        second_write = list(mock_file.write.call_args_list[1][0][0])
        self.assertListEqual(first_write, (
            executable.ALDEBARAN_EXECUTABLE_SIGNATURE
            + [1, 0, 13]
            + self.extra_header
        ))
        self.assertListEqual(second_write, self.opcode)


class MockFile:

    def __init__(self, content):
        self.content = content
        self.idx = 0
    
    def read(self, size=None):
        if size is None:
            size = len(self.content) - self.idx
        return_value = []
        for _ in range(size):
            return_value.append(self.content[self.idx])
            self.idx += 1
        return bytes(return_value)
