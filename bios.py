import aux
from instructions import *


class BIOS(aux.Hardware):

    def __init__(self, contents):
        aux.Hardware.__init__(self)
        self.contents = contents


example_bios = BIOS({
    'start': (0x0400, [
        PUSH, 8, 0,
        POP, 4, 7,
        PRINT, ord('H'),
        NOP,
        PRINT, ord('e'),
        PRINT, ord('l'),
        PRINT, ord('l'),
        PRINT, ord('o'),
        PRINT, ord(' '),
        PRINT, ord('w'),
        PRINT, ord('o'),
        PRINT, ord('r'),
        PRINT, ord('l'),
        PRINT, ord('d'),
        PRINT, ord('!'),
        JUMP, 4, 6,
    ]),
    'something': (0x0800, [
        ord('Y'), NOP,
    ])
})
