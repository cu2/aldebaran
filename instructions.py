def is_instruction(inst):
    try:
        return issubclass(inst, Instruction)
    except TypeError:
        return False


class Instruction(object):

    instruction_size = 1

    def __init__(self, ip, log, arguments=None):
        self.ip = ip
        self.log = log
        self.arguments = arguments

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
        self.log.log('print', chr(char))


class JUMP(Instruction):

    instruction_size = 2

    def next_ip(self):
        pos = self.arguments[0]
        return pos
