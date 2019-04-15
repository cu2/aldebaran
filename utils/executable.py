from utils import utils


ALDEBARAN_EXECUTABLE_SIGNATURE = [
    0x0A,
    ord('L'),  # 0x4C
    0xDE,
    0xBA,
    ord('R'),  # 0x52
    0x0A,
    ord('N'),  # 0x4E
]


class ExecutableError(Exception):
    pass


class CorruptFileError(ExecutableError):
    pass


class Executable:

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

    def _get_entry_point(self):
        return len(ALDEBARAN_EXECUTABLE_SIGNATURE) + 3 + len(self.extra_header)

    def _get_header(self):
        return (
            ALDEBARAN_EXECUTABLE_SIGNATURE
            + [self.version]
            + utils.word_to_bytes(self.entry_point)
            + self.extra_header
        )

    @property
    def length(self):
        return len(self._get_header()) + len(self.opcode)

    def save_to_file(self, filename):
        with open(filename, 'wb') as f:
            f.write(bytes(self._get_header()))
            f.write(bytes(self.opcode))

    def load_from_file(self, filename):
        with open(filename, 'rb') as f:
            signature = f.read(len(ALDEBARAN_EXECUTABLE_SIGNATURE))
            if signature != bytes(ALDEBARAN_EXECUTABLE_SIGNATURE):
                raise CorruptFileError('Signature not vaid')
            try:
                self.version = f.read(1)[0]
            except Exception:
                raise CorruptFileError('Version not valid')
            try:
                self.entry_point = utils.bytes_to_word(*f.read(2))
            except Exception:
                raise CorruptFileError('Entry point not valid')
            extra_header_length = self.entry_point - len(ALDEBARAN_EXECUTABLE_SIGNATURE) - 3
            try:
                self.extra_header = list(f.read(extra_header_length))
            except Exception:
                raise CorruptFileError('Extra header not valid')
            self.opcode = list(f.read())
