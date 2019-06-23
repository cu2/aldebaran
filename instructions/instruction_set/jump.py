'''
Jump instructions
'''

from instructions.instructions import Instruction


class JMP(Instruction):
    '''Jump to <op0>'''

    operand_count = 1
    oplens = ['W']

    def do(self):
        return self.get_operand(0)


class JE(Instruction):
    '''Jump to <op2> if <op0> = <op1>'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_operand(0) == self.get_operand(1):
            return self.get_operand(2)


class JNE(Instruction):
    '''Jump to <op2> if <op0> != <op1>'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_operand(0) != self.get_operand(1):
            return self.get_operand(2)


class JG(Instruction):
    '''Jump to <op2> if <op0> > <op1> (signed)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_signed_operand(0) > self.get_signed_operand(1):
            return self.get_operand(2)


class JGE(Instruction):
    '''Jump to <op2> if <op0> >= <op1> (signed)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_signed_operand(0) >= self.get_signed_operand(1):
            return self.get_operand(2)


class JL(Instruction):
    '''Jump to <op2> if <op0> < <op1> (signed)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_signed_operand(0) < self.get_signed_operand(1):
            return self.get_operand(2)


class JLE(Instruction):
    '''Jump to <op2> if <op0> <= <op1> (signed)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_signed_operand(0) <= self.get_signed_operand(1):
            return self.get_operand(2)


class JA(Instruction):
    '''Jump to <op2> if <op0> > <op1> (unsigned)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_operand(0) > self.get_operand(1):
            return self.get_operand(2)


class JAE(Instruction):
    '''Jump to <op2> if <op0> >= <op1> (unsigned)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_operand(0) >= self.get_operand(1):
            return self.get_operand(2)


class JB(Instruction):
    '''Jump to <op2> if <op0> < <op1> (unsigned)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_operand(0) < self.get_operand(1):
            return self.get_operand(2)


class JBE(Instruction):
    '''Jump to <op2> if <op0> <= <op1> (unsigned)'''

    operand_count = 3
    oplens = ['BBW', 'WWW']

    def do(self):
        if self.get_operand(0) <= self.get_operand(1):
            return self.get_operand(2)
