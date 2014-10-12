import aux
import errors


ADDRESSING_MODE_REGISTER = 0  # e.g. AX
ADDRESSING_MODE_ABSOLUTE = 1  # e.g. 0000

OPERAND_TYPE_REGISTER_DIRECT = 0
OPERAND_TYPE_REGISTER_INDIRECT = 1
OPERAND_TYPE_VALUE_DIRECT = 2
OPERAND_TYPE_VALUE_INDIRECT = 3

WORD_REGISTERS = ['AX', 'BX']
BYTE_REGISTERS = ['AL', 'AH', 'BL', 'BH']


def get_register_code(register_name):
    try:
        return WORD_REGISTERS.index(register_name)
    except IndexError:
        try:
            return len(WORD_REGISTERS) + BYTE_REGISTERS.index(register_name)
        except IndexError:
            raise errors.InvalidRegisterCodeError(register_name)


def is_indirect_word_register(register_name):
    return (len(register_name) >= 3 and register_name[0] == '[' and register_name[-1] == ']' and register_name[1:-1] in WORD_REGISTERS)


def is_indirect_byte_register(register_name):
    return (len(register_name) >= 3 and register_name[0] == '[' and register_name[-1] == ']' and register_name[1:-1] in BYTE_REGISTERS)


def get_address(pos, labels, ip):
    '''Return addressing mode and address operand from address argument'''
    if pos in labels:
        pos1, pos2 = aux.word_to_bytes(labels[pos])
        return (ADDRESSING_MODE_ABSOLUTE, [pos1, pos2])
    if pos in WORD_REGISTERS:
        return (ADDRESSING_MODE_REGISTER, [get_register_code(pos)])
    if pos in BYTE_REGISTERS:
        raise errors.InvalidAddressError(pos)
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
    opcode2 = opcode / 4
    for key, value in globals().iteritems():
        if is_instruction(value):
            try:
                if value.opcode == opcode2:
                    return value, subtype
            except AttributeError:
                pass
    raise errors.UnknownOpcodeError(opcode)


class Instruction(object):

    instruction_size = 1

    def __init__(self, cpu, subtype, operands=None):
        self.cpu = cpu
        self.subtype = subtype
        self.operands = operands
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

    opcode = 0x00


class HALT(Instruction):

    opcode = 0x01

    def next_ip(self):
        return self.ip


class PRINT(Instruction):

    opcode = 0x02
    instruction_size = 2

    @classmethod
    def assemble(cls, ip, labels, arguments):
        try:
            char = arguments[0]
        except IndexError:
            char = ' '
        return [cls.real_opcode(), ord(char)]

    def do(self):
        char = self.operands[0]
        self.cpu.log.log('print', chr(char))


class JUMP(OneAddressInstruction):

    opcode = 0x03

    def next_ip(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            pos = self.cpu.registers[get_register_code(self.operands[0])]
        else:
            pos = aux.bytes_to_word(*self.operands)
        return pos


class PUSH(OneAddressInstruction):

    opcode = 0x04
    instruction_size = 3

    def do(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            self.cpu.stack_push_word(self.cpu.registers[get_register_code(self.operands[0])])
        else:
            pos = aux.bytes_to_word(*self.operands)
            self.cpu.stack_push_word(self.cpu.ram.read_word(pos))


class POP(OneAddressInstruction):

    opcode = 0x05
    instruction_size = 3

    def do(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            content = self.cpu.stack_pop_word()
            self.cpu.registers[get_register_code(self.operands[0])] = content
        else:
            pos = aux.bytes_to_word(*self.operands)
            content = self.cpu.stack_pop_word()
            self.cpu.ram.write_word(pos, content)


class INT(Instruction):

    opcode = 0x06
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
            interrupt_number = self.operands[0]
        return self.cpu.ram.read_word(self.cpu.system_addresses['IV'] + 2 * interrupt_number)


class IRET(Instruction):

    opcode = 0x07
    instruction_size = 1

    def next_ip(self):
        return self.cpu.stack_pop_word()


class CALL(OneAddressInstruction):

    opcode = 0x08

    def do(self):
        self.cpu.stack_push_word(self.ip + self.real_instruction_size)  # IP of next instruction

    def next_ip(self):
        if self.subtype == ADDRESSING_MODE_REGISTER:
            pos = self.cpu.registers[get_register_code(self.operands[0])]
        else:
            pos = aux.bytes_to_word(*self.operands)
        return pos


class RET(Instruction):

    opcode = 0x09
    instruction_size = 1

    def next_ip(self):
        return self.cpu.stack_pop_word()


class MOV(Instruction):

    opcode = 0x0A

    def __repr__(self):
        if self.subtype == OPERAND_TYPE_REGISTER_DIRECT:
            return '%s[reg/direct]' % self.__class__.__name__
        elif self.subtype == OPERAND_TYPE_REGISTER_INDIRECT:
            return '%s[reg/indirect]' % self.__class__.__name__
        elif self.subtype == OPERAND_TYPE_VALUE_DIRECT:
            return '%s[value/direct]' % self.__class__.__name__
        return '%s[value/indirect]' % self.__class__.__name__

    @classmethod
    def assemble(cls, ip, labels, arguments):
        if arguments[0] in WORD_REGISTERS:  # WR
            opcode_offset = 4
        elif arguments[0] in BYTE_REGISTERS:  # BR
            opcode_offset = 5
        else:  # WM/BM
            if arguments[1] in WORD_REGISTERS:  # WM
                opcode_offset = 2
            elif arguments[1] in ['AL', 'AH']:  # BM
                opcode_offset = 3
            elif arguments[1].startswith('['):  # WM (otherwise use MOVB)
                opcode_offset = 2
            elif len(arguments[1]) == 4:  # WM
                opcode_offset = 2
            else:  # BM
                opcode_offset = 3
        real_instruction, real_instruction_subtype = get_instruction_by_opcode(cls.real_opcode() + 4 * opcode_offset)
        return real_instruction.assemble(ip, labels, arguments)

    def do(self):
        raise errors.InvalidInstructionError()


class MOVB(Instruction):

    opcode = 0x0B

    def __repr__(self):
        if self.subtype == OPERAND_TYPE_REGISTER_DIRECT:
            return '%s[reg/direct]' % self.__class__.__name__
        elif self.subtype == OPERAND_TYPE_REGISTER_INDIRECT:
            return '%s[reg/indirect]' % self.__class__.__name__
        elif self.subtype == OPERAND_TYPE_VALUE_DIRECT:
            return '%s[value/direct]' % self.__class__.__name__
        return '%s[value/indirect]' % self.__class__.__name__

    @classmethod
    def assemble(cls, ip, labels, arguments):
        if arguments[0] in WORD_REGISTERS:  # WR
            raise errors.InvalidInstructionError()
        elif arguments[0] in BYTE_REGISTERS:  # BR
            opcode_offset = 4
        elif arguments[1].startswith('['):  # BM (otherwise use MOV)
            opcode_offset = 2
        elif len(arguments[1]) == 4:  # WM
            raise errors.InvalidInstructionError()
        else:  # BM
            opcode_offset = 2
        real_instruction, real_instruction_subtype = get_instruction_by_opcode(cls.real_opcode() + 4 * opcode_offset)
        return real_instruction.assemble(ip, labels, arguments)

    def do(self):
        raise errors.InvalidInstructionError()


class MOVWM(MOV):
    '''Move word into memory'''

    opcode = 0x0C
    instruction_size = 5

    @classmethod
    def assemble(cls, ip, labels, arguments):
        if arguments[1] in WORD_REGISTERS:
            subtype = OPERAND_TYPE_REGISTER_DIRECT
            arg_code = [get_register_code(arguments[1])]
        elif is_indirect_word_register(arguments[1]):
            subtype = OPERAND_TYPE_REGISTER_INDIRECT
            arg_code = [get_register_code(arguments[1][1:-1])]
        elif arguments[1].startswith('['):
            subtype = OPERAND_TYPE_VALUE_INDIRECT
            arg_code = list(aux.word_to_bytes(aux.str_to_int(arguments[1][1:-1])))
        else:
            subtype = OPERAND_TYPE_VALUE_DIRECT
            arg_code = [aux.str_to_int(arguments[1])]
        return [cls.real_opcode(subtype)] + list(aux.word_to_bytes(aux.str_to_int(arguments[0]))) + arg_code

    def do(self):
        target = aux.bytes_to_word(self.operands[0], self.operands[1])
        if self.subtype == OPERAND_TYPE_REGISTER_DIRECT:
            source = self.cpu.registers[get_register_code(self.operands[1])]
        elif self.subtype == OPERAND_TYPE_REGISTER_INDIRECT:
            source = self.cpu.ram.read_word(self.cpu.registers[get_register_code(self.operands[1])])
        elif self.subtype == OPERAND_TYPE_VALUE_DIRECT:
            source = self.operands[1]
        else:
            source = self.cpu.ram.read_word(self.operands[1])
        self.cpu.ram.write_word(self.operands[0], source)


class MOVBM(MOV):
    '''Move byte into memory'''

    opcode = 0x0D
    instruction_size = 4

    @classmethod
    def get_instruction_size(cls, subtype):
        if subtype == OPERAND_TYPE_VALUE_INDIRECT:
            return cls.instruction_size + 1
        return cls.instruction_size

    @classmethod
    def assemble(cls, ip, labels, arguments):
        if arguments[1] in BYTE_REGISTERS:
            subtype = OPERAND_TYPE_REGISTER_DIRECT
            arg_code = get_register_code(arguments[1])
        elif is_indirect_byte_register(arguments[1]):
            subtype = OPERAND_TYPE_REGISTER_INDIRECT
            arg_code = get_register_code(arguments[1])
        elif arguments[1].startswith('['):
            subtype = OPERAND_TYPE_VALUE_INDIRECT
            arg_code = aux.str_to_int(arguments[1][1:-1])
        else:
            subtype = OPERAND_TYPE_VALUE_DIRECT
            arg_code = aux.str_to_int(arguments[1])
        return [cls.real_opcode(subtype)] + list(aux.word_to_bytes(aux.str_to_int(arguments[0]))) + [arg_code]

    def do(self):
        target = aux.bytes_to_word(self.operands[0], self.operands[1])
        if self.subtype == OPERAND_TYPE_REGISTER_DIRECT:
            source = self.cpu.registers[get_register_code(self.operands[2])]
        elif self.subtype == OPERAND_TYPE_REGISTER_INDIRECT:
            source = self.cpu.ram.read_byte(self.cpu.registers[get_register_code(self.operands[2])])
        elif self.subtype == OPERAND_TYPE_VALUE_DIRECT:
            source = self.operands[2]
        else:
            source = self.cpu.ram.read_byte(self.operands[2])
        self.cpu.ram.write_byte(target, source)


class MOVWR(MOV):
    '''Move word into register'''

    opcode = 0x0E
    instruction_size = 4

    @classmethod
    def assemble(cls, ip, labels, arguments):
        if arguments[1] in WORD_REGISTERS:
            subtype = OPERAND_TYPE_REGISTER_DIRECT
            arg_code = [get_register_code(arguments[1])]
        elif is_indirect_word_register(arguments[1]):
            subtype = OPERAND_TYPE_REGISTER_INDIRECT
            arg_code = [get_register_code(arguments[1])]
        elif arguments[1] in BYTE_REGISTERS:
            raise errors.InvalidInstructionError()
        elif is_indirect_byte_register(arguments[1]):
            raise errors.InvalidInstructionError()
        elif arguments[1].startswith('['):
            subtype = OPERAND_TYPE_VALUE_INDIRECT
            arg_code = list(aux.word_to_bytes(aux.str_to_int(arguments[1][1:-1])))
        else:
            subtype = OPERAND_TYPE_VALUE_DIRECT
            arg_code = [aux.str_to_int(arguments[1])]
        return [cls.real_opcode(subtype) + get_register_code(arguments[0])] + arg_code

    def do(self):
        raise errors.InvalidInstructionError()


class MOVBR(MOV):
    '''Move byte into register'''

    opcode = 0x0F
    instruction_size = 3

    @classmethod
    def get_instruction_size(cls, subtype):
        if subtype == OPERAND_TYPE_VALUE_INDIRECT:
            return cls.instruction_size + 1
        return cls.instruction_size

    @classmethod
    def assemble(cls, ip, labels, arguments):
        if arguments[1] in BYTE_REGISTERS:
            subtype = OPERAND_TYPE_REGISTER_DIRECT
            arg_code = get_register_code(arguments[1])
        elif is_indirect_byte_register(arguments[1]):
            subtype = OPERAND_TYPE_REGISTER_INDIRECT
            arg_code = get_register_code(arguments[1])
        elif arguments[1].startswith('['):
            subtype = OPERAND_TYPE_VALUE_INDIRECT
            arg_code = aux.str_to_int(arguments[1][1:-1])
        else:
            subtype = OPERAND_TYPE_VALUE_DIRECT
            arg_code = aux.str_to_int(arguments[1])
        return [cls.real_opcode(subtype)] + list(aux.word_to_bytes(aux.str_to_int(arguments[0]))) + [arg_code]

    def do(self):
        raise errors.InvalidInstructionError()
