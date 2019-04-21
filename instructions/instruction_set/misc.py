'''
Misc instructions
'''

from instructions.instructions import Instruction
from utils import utils


class NOP(Instruction):
    '''No operation'''
    pass


class HLT(Instruction):
    '''Halt CPU so it's inactive until a hardware interrupt occurs'''

    def do(self):
        self.cpu.halt = True
        self.cpu.log.log('cpu', 'Halted')


class SHUTDOWN(Instruction):
    '''Shut down Aldebaran'''

    def do(self):
        self.cpu.shutdown = True
        self.cpu.log.log('cpu', 'Shut down')


class PRINT(Instruction):
    '''Print <op0> as word to CPU log'''

    operand_count = 1
    oplens = ['W']

    def do(self):
        self.cpu.user_log.log('print', utils.word_to_str(self.get_operand(0)))


class PRINTCHAR(Instruction):
    '''Print <op0> as char to CPU log'''

    operand_count = 1
    oplens = ['B']

    def do(self):
        self.cpu.user_log.log('print', chr(self.get_operand(0)))


class SETTMR(Instruction):
    '''Set subtimer <op0> of Timer to mode=<op1>, speed=<op2>, phase=<op3>, interrupt_number=<op4>'''

    operand_count = 5
    oplens = ['BBWWB']

    def do(self):
        subtimer_number = self.get_operand(0)
        self.cpu.timer.set_subtimer(subtimer_number, {
            'mode': self.get_operand(1),
            'speed': self.get_operand(2),
            'phase': self.get_operand(3),
            'interrupt_number': self.get_operand(4),
        })
        self.cpu.log.log('cpu', 'Subtimer %s set.' % utils.byte_to_str(subtimer_number))
