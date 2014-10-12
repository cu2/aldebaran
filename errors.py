class UnknownOpcodeError(Exception):
    pass


class InvalidInstructionError(Exception):
    pass


class InvalidArgumentError(Exception):
    pass


class InvalidOperandError(Exception):
    pass


class InvalidRegisterNameError(Exception):
    pass


class InvalidRegisterCodeError(Exception):
    pass


class InvalidAddressError(Exception):
    pass


class UnknownInstructionError(Exception):
    pass


class StackOverflowError(Exception):
    pass


class StackUnderflowError(Exception):
    pass


class WordOutOfRangeError(Exception):
    pass


class ByteOutOfRangeError(Exception):
    pass
