from instructions.instructions import Instruction


class ADD(Instruction):
    '''Add: <op0> = <op1> + <op2>'''

    operand_count = 3

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(1) + self.get_signed_operand(2))


class SUB(Instruction):
    '''Substract: <op0> = <op1> - <op2>'''

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


class NEG(Instruction):
    '''Negate: <op0> = -<op1>'''

    operand_count = 2

    def do(self):
        self.set_signed_operand(0, -self.get_signed_operand(1))


class INC(Instruction):
    '''Increase: <op0> += <op1>'''

    operand_count = 2

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(0) + self.get_signed_operand(1))


class DEC(Instruction):
    '''Decrease: <op0> -= <op1>'''

    operand_count = 2

    def do(self):
        self.set_signed_operand(0, self.get_signed_operand(0) - self.get_signed_operand(1))
