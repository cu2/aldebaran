def is_instruction(inst):
    try:
        return issubclass(inst, Instruction)
    except TypeError:
        return False


class Instruction(object):

    instruction_name = ''
    instruction_size = 1

    def __init__(self, ip, log, arguments=None):
        self.ip = ip
        self.log = log
        self.arguments = arguments

    def do(self):
        pass

    def next_ip(self):
        return self.ip + self.instruction_size


class InstHalt(Instruction):

    instruction_name = 'halt'
    instruction_size = 1

    def next_ip(self):
        return self.ip


class InstPrint(Instruction):

    instruction_name = 'print'
    instruction_size = 2

    def do(self):
        self.log.log('print', chr(self.arguments[0]))


class InstJump(Instruction):

    instruction_name = 'jump'
    instruction_size = 2

    def next_ip(self):
        return self.arguments[0]
