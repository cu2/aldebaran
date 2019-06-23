'''
Control flow instructions
'''

from instructions.instructions import Instruction


# SUBROUTINE

class CALL(Instruction):
    '''Call subroutine at address <op0>'''

    operand_count = 1
    oplens = ['W']

    def do(self):
        self.cpu.stack.push_word(self.ip + self.opcode_length)  # IP of next instruction
        return self.get_operand(0)


class RET(Instruction):
    '''Return from subroutine'''

    def do(self):
        return self.cpu.stack.pop_word()


class ENTER(Instruction):
    '''
    Enter subroutine: set frame pointer and allocate <op1> bytes on stack for local variables

    - <op0> = byte count of parameters (allocated by PUSH instructions in caller)
    - <op1> = byte count of local variables (allocated by ENTER instruction in callee)
    '''

    operand_count = 2
    oplens = ['BB']

    def do(self):
        self.cpu.stack.push_byte(self.get_operand(0))
        self.cpu.stack.push_byte(self.get_operand(1))
        self.cpu.stack.push_word(self.cpu.registers.get_register('BP'))
        self.cpu.registers.set_register('BP', self.cpu.registers.get_register('SP'))
        self.cpu.registers.set_register('SP', self.cpu.registers.get_register('SP') - self.get_operand(1))


class LVRET(Instruction):
    '''Leave subroutine and return from it: free stack allocated for local variables and parameters'''

    def do(self):
        self.cpu.registers.set_register('SP', self.cpu.registers.get_register('BP'))
        self.cpu.registers.set_register('BP', self.cpu.stack.pop_word())
        self.cpu.stack.pop_byte()  # byte count of local variables
        byte_count_of_parameters = self.cpu.stack.pop_byte()
        next_ip = self.cpu.stack.pop_word()
        self.cpu.registers.set_register('SP', self.cpu.registers.get_register('SP') + byte_count_of_parameters)
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
