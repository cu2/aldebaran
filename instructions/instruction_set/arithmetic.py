'''
Arithmetic instructions
'''

from instructions.instructions import Instruction


class ADD(Instruction):
    '''Add (unsigned): <op0> = <op1> + <op2>'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) + self.get_operand(2))


class IADD(Instruction):
    '''Add (signed): <op0> = <op1> + <op2>'''

    operand_count = 3

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(1) + self.get_signed_operand(2))


class SUB(Instruction):
    '''Substract (unsigned): <op0> = <op1> - <op2>'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) - self.get_operand(2))


class ISUB(Instruction):
    '''Substract (signed): <op0> = <op1> - <op2>'''

    operand_count = 3

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(1) - self.get_signed_operand(2))


class MUL(Instruction):
    '''Multiply (unsigned): <op0> = <op1> * <op2>'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) * self.get_operand(2))


class IMUL(Instruction):
    '''Multiply (signed): <op0> = <op1> * <op2>'''

    operand_count = 3

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(1) * self.get_signed_operand(2))


class DIV(Instruction):
    '''Divide (unsigned): <op0> = <op1> / <op2>'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) // self.get_operand(2))


class IDIV(Instruction):
    '''Divide (signed): <op0> = <op1> / <op2>'''

    operand_count = 3

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(1) // self.get_signed_operand(2))


class MOD(Instruction):
    '''Modulo (unsigned): <op0> = <op1> % <op2>'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) % self.get_operand(2))


class IMOD(Instruction):
    '''Modulo (signed): <op0> = <op1> % <op2>'''

    operand_count = 3

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(1) % self.get_signed_operand(2))


class INC(Instruction):
    '''Increase (unsigned): <op0> += <op1>'''

    operand_count = 2

    def do(self):
        self.set_operand(0, self.get_operand(0) + self.get_operand(1))


class IINC(Instruction):
    '''Increase (signed): <op0> += <op1>'''

    operand_count = 2

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(0) + self.get_signed_operand(1))


class DEC(Instruction):
    '''Decrease (unsigned): <op0> -= <op1>'''

    operand_count = 2

    def do(self):
        self.set_operand(0, self.get_operand(0) - self.get_operand(1))


class IDEC(Instruction):
    '''Decrease (signed): <op0> -= <op1>'''

    operand_count = 2

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(0) - self.get_signed_operand(1))


class NEG(Instruction):
    '''Negate: <op0> = -<op1>'''

    operand_count = 2

    def do(self):
        self.set_signed_operand(0, -self.get_signed_operand(1))
