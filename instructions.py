import aux


def is_instruction(inst):
    try:
        return issubclass(inst, Instruction)
    except TypeError:
        return False


class Instruction(object):

    instruction_size = 1

    def __init__(self, cpu, arguments=None):
        self.cpu = cpu
        self.arguments = arguments
        self.ip = self.cpu.registers['IP']

    def do(self):
        pass

    def next_ip(self):
        return self.ip + self.instruction_size


class NOP(Instruction):
    pass


class HALT(Instruction):

    def next_ip(self):
        return self.ip


class PRINT(Instruction):

    instruction_size = 2

    def do(self):
        char = self.arguments[0]
        self.cpu.log.log('print', chr(char))


class JUMP(Instruction):

    instruction_size = 3

    def next_ip(self):
        pos = aux.bytes_to_word(*self.arguments)
        return pos


class PUSH(Instruction):

    instruction_size = 3

    def do(self):
        pos = aux.bytes_to_word(*self.arguments)
        self.cpu.stack_push_word(self.cpu.ram.read_word(pos))


class POP(Instruction):

    instruction_size = 3

    def do(self):
        pos = aux.bytes_to_word(*self.arguments)
        content = self.cpu.stack_pop_word()
        self.cpu.ram.write_word(pos, content)


class INT(Instruction):

    instruction_size = 2

    def do(self):
        self.cpu.stack_push_word(self.ip)

    def next_ip(self):
        interrupt_number = self.arguments[0]
        return self.cpu.ram.read_word(2 * interrupt_number)


class IRET(Instruction):

    instruction_size = 1

    def next_ip(self):
        return self.cpu.stack_pop_word()


class CALL(Instruction):

    instruction_size = 3

    def do(self):
        self.cpu.stack_push_word(self.ip + self.instruction_size)

    def next_ip(self):
        pos = aux.bytes_to_word(*self.arguments)
        return pos


class RET(Instruction):

    instruction_size = 1

    def next_ip(self):
        return self.cpu.stack_pop_word()
