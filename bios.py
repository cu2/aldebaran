import aux
from instructions import *


class BIOS(aux.Hardware):

    def __init__(self, contents):
        aux.Hardware.__init__(self)
        self.contents = contents


instruction_set = [
    NOP,
    HALT,
    PRINT,
    JUMP,
    PUSH,
    POP,
    INT,
    IRET,
    CALL,
    RET,
]


example_bios = BIOS({
    'IV': (0x0000, [
        9, 0,  # an_interrupt_handler
        0, 0,
        0, 0,
        0, 0,
    ]),
    'start': (0x0400, [
        PUSH, 8, 0,  # var1
        POP, 4, 7,
        PRINT, ord('H'),  # label1
        NOP,
        PRINT, ord('e'),
        PRINT, ord('l'),
        PUSH, 8, 2,  # var2
        CALL, 0x0A, 0,  # a_subroutine
        PRINT, ord('l'),
        PRINT, ord('o'),
        PRINT, ord(' '),
        PRINT, ord('w'),
        PRINT, ord('o'),
        PRINT, ord('r'),
        PRINT, ord('l'),
        PRINT, ord('d'),
        PRINT, ord('!'),
        JUMP, 4, 6,  # goto label1
    ]),
    'var1': (0x0800, [
        ord('Y'), NOP,
    ]),
    'var2': (0x0802, [
        PRINT, ord('@'),
    ]),
    'an_interrupt_handler': (0x0900, [
        PRINT, ord('I'),
        PRINT, ord('N'),
        PRINT, ord('T'),
        IRET,
    ]),
    'a_subroutine': (0x0A00, [
        POP, 0x0B, 0,  # old IP
        POP, 0x0A, 0x0B,
        PUSH, 0x0B, 0,  # old IP
        PRINT, ord('S'),
        NOP, NOP,
        PRINT, ord('U'),
        PRINT, ord('B'),
        RET,
    ]),
})
