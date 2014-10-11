import aux


ADDRESSING_MODE_REGISTER = 0  # e.g. AX
ADDRESSING_MODE_ABSOLUTE = 1  # e.g. 0000


def get_address(pos, labels, ip):
    if pos in labels:
        pos1, pos2 = aux.word_to_bytes(labels[pos])
        return (ADDRESSING_MODE_ABSOLUTE, [pos1, pos2])
    if pos in ['AX']:
        return (ADDRESSING_MODE_REGISTER, [1])
    if pos.startswith('+'):
        pos1, pos2 = aux.word_to_bytes(ip + aux.str_to_int(pos[1:]))
        return (ADDRESSING_MODE_ABSOLUTE, [pos1, pos2])
    if pos.startswith('-'):
        pos1, pos2 = aux.word_to_bytes(ip - aux.str_to_int(pos[1:]))
        return (ADDRESSING_MODE_ABSOLUTE, [pos1, pos2])
    pos1, pos2 = aux.word_to_bytes(aux.str_to_int(pos))
    return (ADDRESSING_MODE_ABSOLUTE, [pos1, pos2])


def is_instruction(inst):
    try:
        return issubclass(inst, Instruction)
    except TypeError:
        return False


def get_instruction_by_opcode(opcode):
    subtype = opcode % 4
    opcode /= 4
    for key, value in globals().iteritems():
        if is_instruction(value):
            try:
                if value.opcode == opcode:
                    return value, subtype
            except AttributeError:
                pass
    raise Exception('Unknown opcode: %s' % opcode)


class Instruction(object):

    instruction_size = 1

    def __init__(self, cpu, subtype, arguments=None):
        self.cpu = cpu
        self.subtype = subtype
        self.arguments = arguments
        self.ip = self.cpu.registers['IP']

    def __repr__(self):
        return self.__class__.__name__

    @classmethod
    def get_instruction_size(cls, subtype):
        return cls.instruction_size

    @classmethod
    def real_opcode(cls, subtype=0):
        return 4 * cls.opcode + subtype

    @classmethod
    def assemble(cls, ip, labels, arguments):
        return [cls.real_opcode()]

    @property
    def real_instruction_size(self):
        return self.__class__.get_instruction_size(self.subtype)

    def do(self):
        pass

    def next_ip(self):
        return self.ip + self.real_instruction_size


class OneAddressInstruction(Instruction):

    instruction_size = 3

    def __repr__(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            return '%s[reg]' % self.__class__.__name__
        return '%s[abs]' % self.__class__.__name__

    @classmethod
    def get_instruction_size(cls, subtype):
        if subtype == ADDRESSING_MODE_REGISTER:
            return 2
        return cls.instruction_size

    @classmethod
    def assemble(cls, ip, labels, arguments):
        pos = arguments[0]
        subtype, operands = get_address(pos, labels, ip)
        return [cls.real_opcode(subtype)] + operands


class NOP(Instruction):

    opcode = 0


class HALT(Instruction):

    opcode = 1

    def next_ip(self):
        return self.ip


class PRINT(Instruction):

    opcode = 2
    instruction_size = 2

    @classmethod
    def assemble(cls, ip, labels, arguments):
        try:
            char = arguments[0]
        except IndexError:
            char = ' '
        return [cls.real_opcode(), ord(char)]

    def do(self):
        char = self.arguments[0]
        self.cpu.log.log('print', chr(char))


class JUMP(OneAddressInstruction):

    opcode = 3

    def next_ip(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            pos = self.cpu.registers['AX']
        else:
            pos = aux.bytes_to_word(*self.arguments)
        return pos


class PUSH(OneAddressInstruction):

    opcode = 4
    instruction_size = 3

    def do(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            self.cpu.stack_push_word(self.cpu.registers['AX'])
        else:
            pos = aux.bytes_to_word(*self.arguments)
            self.cpu.stack_push_word(self.cpu.ram.read_word(pos))


class POP(OneAddressInstruction):

    opcode = 5
    instruction_size = 3

    def do(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            content = self.cpu.stack_pop_word()
            self.cpu.registers['AX'] = content
        else:
            pos = aux.bytes_to_word(*self.arguments)
            content = self.cpu.stack_pop_word()
            self.cpu.ram.write_word(pos, content)


class INT(Instruction):

    opcode = 6
    instruction_size = 2

    @classmethod
    def get_instruction_size(cls, subtype):
        if subtype == 1:
            return 1
        return cls.instruction_size

    @classmethod
    def assemble(cls, ip, labels, arguments):
        if len(arguments):
            interrupt_number = aux.str_to_int(arguments[0])
            return [cls.real_opcode(), interrupt_number]
        return [cls.real_opcode(1)]  # default interrupt (one byte opcode)


    def do(self):
        self.cpu.stack_push_word(self.ip + self.real_instruction_size)  # IP of next instruction

    def next_ip(self):
        if self.subtype == 1:
            interrupt_number = 0  # default interrupt number
        else:
            interrupt_number = self.arguments[0]
        return self.cpu.ram.read_word(self.cpu.system_addresses['IV'] + 2 * interrupt_number)


class IRET(Instruction):

    opcode = 7
    instruction_size = 1

    def next_ip(self):
        return self.cpu.stack_pop_word()


class CALL(OneAddressInstruction):

    opcode = 8

    def do(self):
        self.cpu.stack_push_word(self.ip + self.real_instruction_size)  # IP of next instruction

    def next_ip(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            pos = self.cpu.registers['AX']
        else:
            pos = aux.bytes_to_word(*self.arguments)
        return pos


class RET(Instruction):

    opcode = 9
    instruction_size = 1

    def next_ip(self):
        return self.cpu.stack_pop_word()
