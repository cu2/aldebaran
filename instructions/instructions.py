'''
Base class for instructions
'''

import logging

from utils import utils
from .operands import parse_operand_buffer, get_operand_value, set_operand_value, OpLen


logger = logging.getLogger('hardware.cpu')


class Instruction:
    '''
    Base class for instructions

    operand_count: number of operands
    oplens:
        list of possible combinations of operand lengths
        examples:
        ['BB', 'WW'] means: it has 2 operands, either both are B or both are W
        ['*W'] means: first operand can be anything, second must be W
        None means: all operands can be anything
    '''

    operand_count = 0
    oplens = None

    def __init__(self, cpu, operand_buffer):
        self.cpu = cpu
        self.operands, self.operand_buffer_indices, self.opcode_length = parse_operand_buffer(operand_buffer, self.operand_count)
        self.ip = self.cpu.ip

    def __repr__(self):
        return self.__class__.__name__

    def run(self):
        '''Run instruction'''
        next_ip = self.do()
        if next_ip is None:
            next_ip = self.ip + self.opcode_length
        else:
            logger.debug('Jumped to %s', utils.word_to_str(next_ip))
        return next_ip

    def do(self):
        '''
        This method should be implemented in all subclasses, and do what the specific instruction does.

        If there's a jump, return the IP. Otherwise return None.
        '''
        raise NotImplementedError()

    def get_operand(self, opnum):
        '''
        Return value of operand
        '''
        operand = self.operands[opnum]
        return get_operand_value(operand, self.cpu, self.cpu.memory, self.ip)

    def set_operand(self, opnum, value):
        '''
        Set value of operand
        '''
        operand = self.operands[opnum]
        set_operand_value(operand, value, self.cpu, self.cpu.memory, self.ip)

    def get_signed_operand(self, opnum):
        '''
        Return value of operand as signed number
        '''
        operand = self.operands[opnum]
        raw_value = get_operand_value(operand, self.cpu, self.cpu.memory, self.ip)
        if operand.oplen == OpLen.BYTE:
            binary_value = utils.byte_to_binary(raw_value)
        else:
            binary_value = utils.word_to_binary(raw_value)
        return utils.binary_to_number(binary_value, signed=True)

    def set_signed_operand(self, opnum, value):
        '''
        Set value of operand as signed number
        '''
        operand = self.operands[opnum]
        if operand.oplen == OpLen.BYTE:
            binary_value = utils.byte_to_binary(value, signed=True)
        else:
            binary_value = utils.word_to_binary(value, signed=True)
        set_operand_value(operand, utils.binary_to_number(binary_value), self.cpu, self.cpu.memory, self.ip)
