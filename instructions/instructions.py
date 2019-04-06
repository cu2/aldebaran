from utils import errors, utils
from .operands import parse_operand_buffer


def is_instruction(inst):
    '''Check if inst a subclass of Instruction, but not Instruction itself'''
    try:
        return issubclass(inst, Instruction) and inst != Instruction
    except TypeError:
        return False


def get_instruction_set():
    '''Return list and dict of all valid instructions'''
    # get automatic opcodes (for development):
    inst_list = []
    for key, value in globals().items():
        if is_instruction(value):
            inst_list.append(key)
    inst_list.sort()
    # fix opcodes (once it's fixed):
    # inst_list = [
    # ]
    inst_dict = {}
    for opcode, name in enumerate(inst_list):
        inst_dict[name] = opcode
    return inst_list, inst_dict


class Instruction:

    operand_count = 0
    oplens = None

    def __init__(self, cpu, operand_buffer):
        self.cpu = cpu
        self.operands, self.opcode_length = parse_operand_buffer(operand_buffer, self.operand_count)
        self.ip = self.cpu.registers['IP']

    def __repr__(self):
        return self.__class__.__name__

    def get_operand(self, opnum):
        '''Return value of operand'''
        oplen, optype, oprest = self.operands[opnum]
        if optype == OPTYPE_VALUE:
            return oprest[0]
        if optype == OPTYPE_REGISTER:
            return self.cpu.get_register(get_register_name_by_code(oprest[0]))
        if optype == OPTYPE_REL_REF_WORD:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(oprest[0])
            else:
                return self.cpu.ram.read_byte(oprest[0])
        if optype == OPTYPE_ABS_REF_REG:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(self.cpu.get_register(get_register_name_by_code(oprest[0])) + utils.byte_to_signed(oprest[1]))
            else:
                return self.cpu.ram.read_byte(self.cpu.get_register(get_register_name_by_code(oprest[0])) + utils.byte_to_signed(oprest[1]))
        if optype == OPTYPE_REL_REF_WORD_REG:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])))
            else:
                return self.cpu.ram.read_byte(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])))
        if optype == OPTYPE_REL_REF_WORD_BYTE:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(oprest[0] + oprest[1])
            else:
                return self.cpu.ram.read_byte(oprest[0] + oprest[1])
        raise errors.InvalidOperandError(self, self.operands[opnum])

    def set_operand(self, opnum, value):
        '''Set value of operand'''
        oplen, optype, oprest = self.operands[opnum]
        if optype == OPTYPE_VALUE:
            raise errors.InvalidWriteOperationError(self, self.operands[opnum])
        elif optype == OPTYPE_REGISTER:
            self.cpu.set_register(get_register_name_by_code(oprest[0]), value)
        elif optype == OPTYPE_REL_REF_WORD:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(oprest[0], value)
            else:
                self.cpu.ram.write_byte(oprest[0], value)
        elif optype == OPTYPE_ABS_REF_REG:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(self.cpu.get_register(get_register_name_by_code(oprest[0])) + utils.byte_to_signed(oprest[1]), value)
            else:
                self.cpu.ram.write_byte(self.cpu.get_register(get_register_name_by_code(oprest[0])) + utils.byte_to_signed(oprest[1]), value)
        elif optype == OPTYPE_REL_REF_WORD_REG:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])), value)
            else:
                self.cpu.ram.write_byte(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])), value)
        elif optype == OPTYPE_REL_REF_WORD_BYTE:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(oprest[0] + oprest[1], value)
            else:
                self.cpu.ram.write_byte(oprest[0] + oprest[1], value)
        else:
            raise errors.InvalidOperandError(self, self.operands[opnum])

    def get_signed_operand(self, opnum):
        oplen, optype, oprest = self.operands[opnum]
        if oplen == OPLEN_WORD:
            return utils.word_to_signed(self.get_operand(opnum))
        return utils.byte_to_signed(self.get_operand(opnum))

    def set_signed_operand(self, opnum, value):
        oplen, optype, oprest = self.operands[opnum]
        if oplen == OPLEN_WORD:
            mask = 0xFFFF
        else:
            mask = 0xFF
        self.set_operand(opnum, value & mask)

    def run(self):
        '''Run instruction'''
        next_ip = self.do()
        if next_ip is None:
            return self.ip + self.opcode_length
        return next_ip

    def do(self):
        '''
        This method should be implemented in all subclasses, and do what the specific instruction does.

        If there's a jump, return the IP. Otherwise return None.
        '''
        raise NotImplementedError
