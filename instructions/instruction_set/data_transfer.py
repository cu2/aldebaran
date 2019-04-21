'''
Data transfer instructions
'''

from instructions.instructions import Instruction
from instructions.operands import OpLen
from utils import utils


# GENERAL

class MOV(Instruction):
    '''Move data so that <op0> = <op1>'''

    operand_count = 2
    oplens = ['BB', 'WW']

    def do(self):
        self.set_operand(0, self.get_operand(1))


# STACK

class PUSH(Instruction):
    '''Push <op0> to stack'''

    operand_count = 1

    def do(self):
        if self.operands[0].oplen == OpLen.WORD:
            self.cpu.stack_push_word(self.get_operand(0))
        else:
            self.cpu.stack_push_byte(self.get_operand(0))


class POP(Instruction):
    '''Pop <op0> from stack'''

    operand_count = 1

    def do(self):
        if self.operands[0].oplen == OpLen.WORD:
            self.set_operand(0, self.cpu.stack_pop_word())
        else:
            self.set_operand(0, self.cpu.stack_pop_byte())


class PUSHF(Instruction):
    '''Push FLAGS to stack'''

    def do(self):
        self.cpu.stack_push_flags()


class POPF(Instruction):
    '''Pop FLAGS from stack'''

    def do(self):
        self.cpu.stack_pop_flags()


# I/O

class IN(Instruction):
    '''Transfer input data from IOPort <op0>B into memory at address <op1>W, set CX to its length and send ACK'''

    operand_count = 2
    oplens = ['BW']

    def do(self):
        ioport_number = self.get_operand(0)
        pos = self.get_operand(1)
        input_data = self.cpu.device_controller.ioports[ioport_number].read_input()
        for idx, value in enumerate(input_data):
            self.cpu.ram.write_byte(pos + idx, value)
        self.cpu.log.log('cpu', 'Input data from IOPort %s: %s (%s bytes)' % (ioport_number, utils.binary_to_str(input_data), len(input_data)))
        self.cpu.set_register('CX', len(input_data))


class OUT(Instruction):
    '''Transfer output data (CX bytes) from memory at address <op1>W to IOPort <op0>B'''

    operand_count = 2
    oplens = ['BW']

    def do(self):
        ioport_number = self.get_operand(0)
        pos = self.get_operand(1)
        cx = self.cpu.get_register('CX')
        output_data = self.cpu.device_controller.ioports[ioport_number].send_output(
            bytes([self.cpu.ram.read_byte(pos + idx) for idx in range(cx)])
        )
        self.cpu.log.log('cpu', 'Output data to IOPort %s: %s (%s bytes)' % (ioport_number, utils.binary_to_str(output_data), cx))
