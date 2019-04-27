'''
Module defining the Aldebaran executable format(s)

- bytes 0-6: signature
- byte 7: version
- bytes 8-9: entry point (offset from beginning of file to opcode)
- optional extra header
- opcode
'''

from utils import utils
from utils.errors import AldebaranError


ALDEBARAN_EXECUTABLE_SIGNATURE = [
    0x0A,
    ord('L'),  # 0x4C
    0xDE,
    0xBA,
    ord('R'),  # 0x52
    0x0A,
    ord('N'),  # 0x4E
]


class Executable:
    '''
    Container for an executable
    '''

    def __init__(self, version=0, opcode=None, extra_header=None):
        self.version = version
        if opcode:
            self.opcode = opcode
        else:
            self.opcode = []
        if extra_header:
            self.extra_header = extra_header
        else:
            self.extra_header = []
        self.entry_point = self._get_entry_point()

    @property
    def length(self):
        '''
        Get length of executable
        '''
        return len(self._get_header()) + len(self.opcode)

    def save_to_file(self, filename):
        '''
        Save executable to file
        '''
        with open(filename, 'wb') as output_file:
            output_file.write(bytes(self._get_header()))
            output_file.write(bytes(self.opcode))

    def load_from_file(self, filename):
        '''
        Load executable from file
        '''
        with open(filename, 'rb') as input_file:
            signature = input_file.read(len(ALDEBARAN_EXECUTABLE_SIGNATURE))
            if signature != bytes(ALDEBARAN_EXECUTABLE_SIGNATURE):
                raise CorruptFileError('Signature not valid')
            try:
                self.version = input_file.read(1)[0]
            except Exception:
                raise CorruptFileError('Version not valid')
            try:
                self.entry_point = utils.binary_to_number(list(input_file.read(2)))
            except Exception:
                raise CorruptFileError('Entry point not valid')
            extra_header_length = self.entry_point - len(ALDEBARAN_EXECUTABLE_SIGNATURE) - 3
            try:
                self.extra_header = list(input_file.read(extra_header_length))
            except Exception:
                raise CorruptFileError('Extra header not valid')
            self.opcode = list(input_file.read())

    def _get_entry_point(self):
        return len(ALDEBARAN_EXECUTABLE_SIGNATURE) + 3 + len(self.extra_header)

    def _get_header(self):
        return (
            ALDEBARAN_EXECUTABLE_SIGNATURE
            + [self.version]
            + utils.word_to_binary(self.entry_point)
            + self.extra_header
        )


# pylint: disable=missing-docstring

class ExecutableError(AldebaranError):
    pass


class CorruptFileError(ExecutableError):
    pass
