from collections import namedtuple

from utils import utils
from utils.tokenizer import TokenType, UnknownTokenError


Operand = namedtuple('Operand', ['oplen', 'optype', 'opreg', 'opvalue', 'opbase', 'opoffset'])


class RegisterError(Exception):
    pass


class InvalidRegisterNameError(RegisterError):
    pass


class InvalidRegisterCodeError(RegisterError):
    pass


class InvalidTokenLengthError(Exception):
    pass


class InvalidOperandError(Exception):
    pass


class InsufficientOperandBufferError(Exception):
    pass


OPLEN_BYTE = 0
OPLEN_WORD = 1


OPTYPE_VALUE = 0
# dd, dddd
# e.g. constants, interrupt and I/O numbers, absolute addresses

OPTYPE_ADDRESS = 1
# ^dddd
# e.g. relative addresses (labels) that must be absolutized (for jumps, calls)

OPTYPE_REGISTER = 2
# AX, AL
# e.g. temporary variables

OPTYPE_ABS_REF_REG = 3
# [AX+dd]
# e.g. params (BP+), local variables (BP-), structs with address in reg

OPTYPE_REL_REF_WORD = 4
# [dddd]
# e.g. global variables

OPTYPE_REL_REF_WORD_BYTE = 5
# [dddd+dd]
# e.g. structs (address = global variable)

OPTYPE_REL_REF_WORD_REG = 6
# [dddd+AX]
# e.g. arrays (address = global variable)

OPTYPE_EXTENDED = 7
# the next byte specifies the optype
# not used yet


WORD_REGISTERS = ['AX', 'BX', 'CX', 'DX', 'BP', 'SP', 'SI', 'DI']
BYTE_REGISTERS = ['AL', 'AH', 'BL', 'BH', 'CL', 'CH', 'DL', 'DH']


def get_register_code_by_name(register_name):
    '''Return register code by name'''
    try:
        return WORD_REGISTERS.index(register_name)
    except ValueError:
        try:
            return len(WORD_REGISTERS) + BYTE_REGISTERS.index(register_name)
        except ValueError:
            raise InvalidRegisterNameError(register_name)


def get_register_name_by_code(register_code):
    '''Return register name by code'''
    if register_code < 0 or register_code >= len(WORD_REGISTERS) + len(BYTE_REGISTERS):
        raise InvalidRegisterCodeError(register_code)
    if register_code < len(WORD_REGISTERS):
        return WORD_REGISTERS[register_code]
    return BYTE_REGISTERS[register_code - len(WORD_REGISTERS)]


def get_opbyte(oplen, optype, opreg_name=None):
    if opreg_name is None:
        opreg = 0
    else:
        opreg = get_register_code_by_name(opreg_name)
    return (oplen << 7) + (optype << 4) + opreg


def get_operand_opcode(token):
    '''Return opcode of operand'''
    if token.type == TokenType.WORD_LITERAL:
        return [
            get_opbyte(OPLEN_WORD, OPTYPE_VALUE)
        ] + utils.word_to_bytes(token.value)
    if token.type == TokenType.BYTE_LITERAL:
        return [
            get_opbyte(OPLEN_BYTE, OPTYPE_VALUE)
        ] + utils.byte_to_bytes(token.value)
    if token.type == TokenType.ADDRESS_WORD_LITERAL:
        return [
            get_opbyte(OPLEN_WORD, OPTYPE_ADDRESS)
        ] + utils.word_to_bytes(token.value)
    if token.type == TokenType.WORD_REGISTER:
        return [
            get_opbyte(OPLEN_WORD, OPTYPE_REGISTER, token.value)
        ]
    if token.type == TokenType.BYTE_REGISTER:
        return [
            get_opbyte(OPLEN_BYTE, OPTYPE_REGISTER, token.value)
        ]
    if token.type in {TokenType.ABS_REF_REG, TokenType.REL_REF_WORD, TokenType.REL_REF_WORD_BYTE, TokenType.REL_REF_WORD_REG}:
        if token.value.length == 'B':
            oplen = OPLEN_BYTE
        elif token.value.length == 'W':
            oplen = OPLEN_WORD
        else:
            raise InvalidTokenLengthError()
        optype = {
            TokenType.ABS_REF_REG: OPTYPE_ABS_REF_REG,
            TokenType.REL_REF_WORD: OPTYPE_REL_REF_WORD,
            TokenType.REL_REF_WORD_BYTE: OPTYPE_REL_REF_WORD_BYTE,
            TokenType.REL_REF_WORD_REG: OPTYPE_REL_REF_WORD_REG,
        }[token.type]
        if token.type == TokenType.ABS_REF_REG:
            opreg = token.value.base
        elif token.type == TokenType.REL_REF_WORD_REG:
            opreg = token.value.offset
        else:
            opreg = None
        if token.type == TokenType.ABS_REF_REG:
            oprest = utils.byte_to_bytes(token.value.offset)
        elif token.type == TokenType.REL_REF_WORD:
            oprest = utils.word_to_bytes(token.value.base)
        elif token.type == TokenType.REL_REF_WORD_BYTE:
            oprest = utils.word_to_bytes(token.value.base) + utils.byte_to_bytes(token.value.offset)
        elif token.type == TokenType.REL_REF_WORD_REG:
            oprest = utils.word_to_bytes(token.value.base)
        return [
            get_opbyte(oplen, optype, opreg)
        ] + oprest
    raise UnknownTokenError()


def parse_operand_buffer(operand_buffer, operand_count):
    '''Return opcode_length (including instruction) and list of operands as Operand(oplen, optype, opreg, oprest) tuples from operand_buffer'''
    operands = []
    operand_buffer_idx = 0
    try:
        while True:
            if len(operands) >= operand_count:
                break
            opbyte = operand_buffer[operand_buffer_idx]
            operand_buffer_idx += 1
            oplen = opbyte >> 7
            optype = (opbyte & 0x7F) >> 4
            raw_opreg = opbyte & 0x0F
            opreg = None
            opvalue = None
            opbase = None
            opoffset = None
            if optype == OPTYPE_VALUE:
                if oplen == OPLEN_WORD:
                    opvalue = utils.bytes_to_word(
                        operand_buffer[operand_buffer_idx+0],
                        operand_buffer[operand_buffer_idx+1],
                    )
                    operand_buffer_idx += 2
                else:
                    opvalue = operand_buffer[operand_buffer_idx+0]
                    operand_buffer_idx += 1
            elif optype == OPTYPE_ADDRESS:
                if oplen == OPLEN_WORD:
                    opvalue = utils.bytes_to_word(
                        operand_buffer[operand_buffer_idx+0],
                        operand_buffer[operand_buffer_idx+1],
                    )
                    operand_buffer_idx += 2
                else:
                    raise InvalidOperandError(operand_buffer, operand_buffer_idx)
            elif optype == OPTYPE_REGISTER:
                opreg = get_register_name_by_code(raw_opreg)
                if oplen == OPLEN_WORD:
                    if opreg not in WORD_REGISTERS:
                        raise InvalidRegisterCodeError()
                else:
                    if opreg not in BYTE_REGISTERS:
                        raise InvalidRegisterCodeError()
            elif optype == OPTYPE_ABS_REF_REG:
                opreg = get_register_name_by_code(raw_opreg)
                if opreg not in WORD_REGISTERS:
                    raise InvalidRegisterCodeError()
                opoffset = operand_buffer[operand_buffer_idx+0]
                operand_buffer_idx += 1
            elif optype == OPTYPE_REL_REF_WORD:
                opbase = utils.bytes_to_word(
                    operand_buffer[operand_buffer_idx+0],
                    operand_buffer[operand_buffer_idx+1],
                )
                operand_buffer_idx += 2
            elif optype == OPTYPE_REL_REF_WORD_BYTE:
                opbase = utils.bytes_to_word(
                    operand_buffer[operand_buffer_idx+0],
                    operand_buffer[operand_buffer_idx+1],
                )
                opoffset = operand_buffer[operand_buffer_idx+2]
                operand_buffer_idx += 3
            elif optype == OPTYPE_REL_REF_WORD_REG:
                opreg = get_register_name_by_code(raw_opreg)
                if opreg not in WORD_REGISTERS:
                    raise InvalidRegisterCodeError()
                opbase = utils.bytes_to_word(
                    operand_buffer[operand_buffer_idx+0],
                    operand_buffer[operand_buffer_idx+1],
                )
                operand_buffer_idx += 2
            else:
                raise InvalidOperandError(operand_buffer, operand_buffer_idx)
            operands.append(Operand(oplen, optype, opreg, opvalue, opbase, opoffset))
    except IndexError:
        raise InsufficientOperandBufferError(operand_buffer)
    return operands, 1 + operand_buffer_idx
