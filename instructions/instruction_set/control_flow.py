'''
Control flow instructions
'''

from instructions.instructions import Instruction


# JUMP

class JMP(Instruction):
    '''Jump to <op0>'''

    operand_count = 1
    oplens = ['W']

    def do(self):
        return self.get_operand(0)


class JZ(Instruction):
    '''Jump to <op1> if <op0> is zero'''

    operand_count = 2
    oplens = ['*W']

    def do(self):
        if self.get_operand(0) == 0:
            return self.get_operand(1)


class JNZ(Instruction):
    '''Jump to <op1> if <op0> is non-zero'''

    operand_count = 2
    oplens = ['*W']

    def do(self):
        if self.get_operand(0) != 0:
            return self.get_operand(1)


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


class JGT(Instruction):
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


class JLT(Instruction):
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


# SUBROUTINE

class CALL(Instruction):
    '''Call subroutine at address <op0>'''

    operand_count = 1
    oplens = ['W']

    def do(self):
        self.cpu.stack.push_word(self.ip + self.opcode_length)  # IP of next instruction
        return self.get_operand(0)


class ENTER(Instruction):
    '''Enter subroutine: set frame pointer and allocate <op0> bytes on stack for local variables'''
    # TODO: upgrade

    operand_count = 1

    def do(self):
        self.cpu.stack.push_word(self.cpu.registers.get_register('BP'))
        self.cpu.registers.set_register('BP', self.cpu.registers.get_register('SP'))
        self.cpu.registers.set_register('SP', self.cpu.registers.get_register('SP') - self.get_operand(0))


class LEAVE(Instruction):
    '''Leave subroutine: free stack allocated for local variables'''
    # TODO: upgrade

    def do(self):
        self.cpu.registers.set_register('SP', self.cpu.registers.get_register('BP'))
        self.cpu.registers.set_register('BP', self.cpu.stack.pop_word())


class RET(Instruction):
    '''Return from subroutine'''

    def do(self):
        return self.cpu.stack.pop_word()


class RETPOP(Instruction):
    '''Return from subroutine and pop <op0> bytes'''
    # TODO: upgrade

    operand_count = 1

    def do(self):
        next_ip = self.cpu.stack.pop_word()
        self.cpu.registers.set_register('SP', self.cpu.registers.get_register('SP') + self.get_operand(0))
        return next_ip


# INTERRUPT

class INT(Instruction):
    '''Call interrupt <op0>'''

    operand_count = 1
    oplens = ['B']

    def do(self):
        self.cpu.stack.push_flags()
        self.cpu.stack.push_word(self.ip + self.opcode_length)  # IP of next instruction
        interrupt_number = self.get_operand(0)
        return self.cpu.memory.read_word(self.cpu.system_addresses['IVT'] + 2 * interrupt_number)


class IRET(Instruction):
    '''Return from interrupt'''

    def do(self):
        next_ip = self.cpu.stack.pop_word()
        self.cpu.stack.pop_flags()
        return next_ip


class SETINT(Instruction):
    '''Set IVT[<op0>] to <op1>'''

    operand_count = 2
    oplens = ['BW']

    def do(self):
        interrupt_number = self.get_operand(0)
        self.cpu.memory.write_word(self.cpu.system_addresses['IVT'] + 2 * interrupt_number, self.get_operand(1))


class STI(Instruction):
    '''Enable interrupts'''

    def do(self):
        self.cpu.enable_interrupts()


class CLI(Instruction):
    '''Disable interrupts'''

    def do(self):
        self.cpu.disable_interrupts()
