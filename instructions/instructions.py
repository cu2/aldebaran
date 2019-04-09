from .operands import parse_operand_buffer, get_operand_value, set_operand_value


class Instruction:

    operand_count = 0
    oplens = None

    def __init__(self, cpu, operand_buffer):
        self.cpu = cpu
        self.operands, self.opcode_length = parse_operand_buffer(operand_buffer, self.operand_count)
        self.ip = self.cpu.registers['IP']

    def __repr__(self):
        return self.__class__.__name__

    def get_operand(self, opnum):
        '''Return value of operand'''
        operand = self.operands[opnum]
        return get_operand_value(operand, self.cpu, self.cpu.ram, self.ip)

    def set_operand(self, opnum, value):
        '''Set value of operand'''
        operand = self.operands[opnum]
        set_operand_value(operand, value, self.cpu, self.cpu.ram, self.ip)

    def get_signed_operand(self, opnum):
        # TODO: fix
        return self.get_operand(opnum)

    def set_signed_operand(self, opnum, value):
        # TODO: fix
        self.set_operand(opnum, value)

    def run(self):
        '''Run instruction'''
        next_ip = self.do()
        if next_ip is None:
            return self.ip + self.opcode_length
        return next_ip

    def do(self):
        '''
        This method should be implemented in all subclasses, and do what the specific instruction does.

        If there's a jump, return the IP. Otherwise return None.
        '''
        raise NotImplementedError
