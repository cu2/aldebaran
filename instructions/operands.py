'''
Operand related stuff, like Operand, get_operand_opcode, parse_operand_buffer
'''

from collections import namedtuple
from enum import Enum

from utils import utils
from utils.tokenizer import TokenType


Operand = namedtuple('Operand', [
    'oplen',  # OpLen
    'optype',  # OpType
    'opreg',  # register | None
    'opvalue',  # byte | word | None
    'opbase',  # byte | word | None
    'opoffset',  # byte | None
])


class OpLen(Enum):
    '''
    Length of the operand's value
    Encoded in the first bit of the operand opcode
    '''
    BYTE = 0
    WORD = 1


class OpType(Enum):
    '''
    Operand type
    Encoded in the 2nd-4th bit of the operand opcode

    - value
        dd, dddd
        e.g. constants, interrupt and I/O numbers, absolute addresses
    - address
        ^dddd, ^-dddd
        e.g. relative addresses (labels) that must be absolutized (for jumps, calls)
    - register
        AX, AL
        e.g. temporary variables
    - absolute reference register
        [AX+dd], [AX-dd]
        e.g. params (BP+), local variables (BP-), structs with address in reg
    - relative reference word
        [dddd], [-dddd]
        e.g. global variables
    - relative reference word + byte
        [dddd+dd], [-dddd+dd]
        e.g. structs (address = global variable)
    - relative reference word + register
        [dddd+AX], [-dddd+AX]
        e.g. arrays (address = global variable)
    - extended
        the next byte specifies the optype
        not used yet
    '''
    VALUE = 0
    ADDRESS = 1
    REGISTER = 2
    ABS_REF_REG = 3
    REL_REF_WORD = 4
    REL_REF_WORD_BYTE = 5
    REL_REF_WORD_REG = 6
    EXTENDED = 7


WORD_REGISTERS = ['AX', 'BX', 'CX', 'DX', 'BP', 'SP', 'SI', 'DI']
BYTE_REGISTERS = ['AL', 'AH', 'BL', 'BH', 'CL', 'CH', 'DL', 'DH']


def get_operand_opcode(token):
    '''
    Return operand opcode for a token.
    Assembler uses it to generate opcode.
    '''
    if token.type == TokenType.WORD_LITERAL:
        return [
            _get_opbyte(OpLen.WORD, OpType.VALUE)
        ] + utils.word_to_binary(token.value)
    if token.type == TokenType.BYTE_LITERAL:
        return [
            _get_opbyte(OpLen.BYTE, OpType.VALUE)
        ] + utils.byte_to_binary(token.value)
    if token.type == TokenType.ADDRESS_WORD_LITERAL:
        return [
            _get_opbyte(OpLen.WORD, OpType.ADDRESS)
        ] + utils.word_to_binary(token.value, signed=True)  # ^-1234
    if token.type == TokenType.WORD_REGISTER:
        return [
            _get_opbyte(OpLen.WORD, OpType.REGISTER, token.value)
        ]
    if token.type == TokenType.BYTE_REGISTER:
        return [
            _get_opbyte(OpLen.BYTE, OpType.REGISTER, token.value)
        ]
    if token.type in {TokenType.ABS_REF_REG, TokenType.REL_REF_WORD, TokenType.REL_REF_WORD_BYTE, TokenType.REL_REF_WORD_REG}:
        ref = token.value
        oplen = {
            'B': OpLen.BYTE,
            'W': OpLen.WORD,
        }[ref.length]
        optype = {
            TokenType.ABS_REF_REG: OpType.ABS_REF_REG,
            TokenType.REL_REF_WORD: OpType.REL_REF_WORD,
            TokenType.REL_REF_WORD_BYTE: OpType.REL_REF_WORD_BYTE,
            TokenType.REL_REF_WORD_REG: OpType.REL_REF_WORD_REG,
        }[token.type]
        if token.type == TokenType.ABS_REF_REG:
            opreg = ref.base
            oprest = utils.byte_to_binary(ref.offset, signed=True)  # [AX-12]
        elif token.type == TokenType.REL_REF_WORD:
            opreg = None
            oprest = utils.word_to_binary(ref.base, signed=True)  # [-1234]
        elif token.type == TokenType.REL_REF_WORD_BYTE:
            opreg = None
            oprest = utils.word_to_binary(ref.base, signed=True) + utils.byte_to_binary(ref.offset)  # [-1234+56]
        elif token.type == TokenType.REL_REF_WORD_REG:
            opreg = ref.offset
            oprest = utils.word_to_binary(ref.base, signed=True)  # [-1234+AX]
        return [
            _get_opbyte(oplen, optype, opreg)
        ] + oprest
    raise InvalidTokenError(token)


def parse_operand_buffer(operand_buffer, operand_count):
    '''
    Return:
    - list of operands (type=Operand)
    - opcode_length (including instruction)
    from operand_buffer.
    Instructions use it when running.
    '''
    operands = []
    operand_buffer_idx = 0
    try:
        while True:
            if len(operands) >= operand_count:
                break
            opbyte = operand_buffer[operand_buffer_idx]
            operand_buffer_idx += 1
            oplen = OpLen(opbyte >> 7)
            optype = OpType((opbyte & 0x7F) >> 4)
            raw_opreg = opbyte & 0x0F
            opreg = None
            opvalue = None
            opbase = None
            opoffset = None
            if optype == OpType.VALUE:
                if oplen == OpLen.WORD:
                    opvalue = utils.binary_to_number([
                        operand_buffer[operand_buffer_idx+0],
                        operand_buffer[operand_buffer_idx+1],
                    ])
                    operand_buffer_idx += 2
                else:
                    opvalue = operand_buffer[operand_buffer_idx+0]
                    operand_buffer_idx += 1
            elif optype == OpType.ADDRESS:
                if oplen == OpLen.WORD:
                    opvalue = utils.binary_to_number([
                        operand_buffer[operand_buffer_idx+0],
                        operand_buffer[operand_buffer_idx+1],
                    ], signed=True)
                    operand_buffer_idx += 2
                else:
                    raise InvalidOperandError(operand_buffer, operand_buffer_idx)
            elif optype == OpType.REGISTER:
                opreg = _get_register_name_by_code(raw_opreg)
                if oplen == OpLen.WORD:
                    if opreg not in WORD_REGISTERS:
                        raise InvalidRegisterCodeError()
                else:
                    if opreg not in BYTE_REGISTERS:
                        raise InvalidRegisterCodeError()
            elif optype == OpType.ABS_REF_REG:
                opreg = _get_register_name_by_code(raw_opreg)
                if opreg not in WORD_REGISTERS:
                    raise InvalidRegisterCodeError()
                opoffset = utils.binary_to_number(
                    [operand_buffer[operand_buffer_idx+0]],
                    signed=True,
                )
                operand_buffer_idx += 1
            elif optype == OpType.REL_REF_WORD:
                opbase = utils.binary_to_number([
                    operand_buffer[operand_buffer_idx+0],
                    operand_buffer[operand_buffer_idx+1],
                ], signed=True)
                operand_buffer_idx += 2
            elif optype == OpType.REL_REF_WORD_BYTE:
                opbase = utils.binary_to_number([
                    operand_buffer[operand_buffer_idx+0],
                    operand_buffer[operand_buffer_idx+1],
                ], signed=True)
                opoffset = operand_buffer[operand_buffer_idx+2]
                operand_buffer_idx += 3
            elif optype == OpType.REL_REF_WORD_REG:
                opreg = _get_register_name_by_code(raw_opreg)
                if opreg not in WORD_REGISTERS:
                    raise InvalidRegisterCodeError()
                opbase = utils.binary_to_number([
                    operand_buffer[operand_buffer_idx+0],
                    operand_buffer[operand_buffer_idx+1],
                ], signed=True)
                operand_buffer_idx += 2
            else:
                raise InvalidOperandError(operand_buffer, operand_buffer_idx)
            operands.append(Operand(oplen, optype, opreg, opvalue, opbase, opoffset))
    except IndexError:
        raise InsufficientOperandBufferError(operand_buffer)
    return operands, 1 + operand_buffer_idx


def get_operand_value(operand, cpu, ram, ip):
    '''
    Get operand value (as unsigned) when executing an instruction
    '''
    if operand.optype == OpType.EXTENDED:
        raise InvalidOperandError('Extended optype not supported yet.')
    if operand.optype == OpType.VALUE:
        return operand.opvalue
    if operand.optype == OpType.ADDRESS:
        return ip + operand.opvalue
    if operand.optype == OpType.REGISTER:
        return cpu.get_register(operand.opreg)

    address = _get_reference_address(operand, cpu, ip)
    if operand.oplen == OpLen.BYTE:
        return ram.read_byte(address)
    else:
        return ram.read_word(address)


def set_operand_value(operand, value, cpu, ram, ip):
    '''
    Set operand value (as unsigned) when executing an instruction
    '''
    if operand.optype == OpType.EXTENDED:
        raise InvalidOperandError('Extended optype not supported yet.')
    if operand.optype == OpType.VALUE:
        raise InvalidWriteOperationError('Cannot set value type operand.')
    if operand.optype == OpType.ADDRESS:
        raise InvalidWriteOperationError('Cannot set address type operand.')
    if operand.optype == OpType.REGISTER:
        cpu.set_register(operand.opreg, value)
        return

    address = _get_reference_address(operand, cpu, ip)
    if operand.oplen == OpLen.BYTE:
        ram.write_byte(address, value)
    else:
        ram.write_word(address, value)


def _get_reference_address(operand, cpu, ip):
    if operand.optype == OpType.ABS_REF_REG:
        return cpu.get_register(operand.opreg) + operand.opoffset
    if operand.optype == OpType.REL_REF_WORD:
        return ip + operand.opbase
    if operand.optype == OpType.REL_REF_WORD_BYTE:
        return ip + operand.opbase + operand.opoffset
    if operand.optype == OpType.REL_REF_WORD_REG:
        return ip + operand.opbase + cpu.get_register(operand.opreg)
    raise InvalidOperandError('Cannot get reference address of {}'.format(operand))


def _get_opbyte(oplen, optype, opreg_name=None):
    '''
    Return first byte of operand opcode:
    - bit 0: OpLen
    - bits 1-3: OpType
    - bits 4-7: OpReg
    '''
    if opreg_name is None:
        opreg = 0
    else:
        opreg = _get_register_code_by_name(opreg_name)
    return (oplen.value << 7) + (optype.value << 4) + opreg


def _get_register_code_by_name(register_name):
    '''
    Return 4-bit register code by name
    '''
    try:
        return WORD_REGISTERS.index(register_name)
    except ValueError:
        try:
            return len(WORD_REGISTERS) + BYTE_REGISTERS.index(register_name)
        except ValueError:
            raise InvalidRegisterNameError(register_name)


def _get_register_name_by_code(register_code):
    '''
    Return register name by 4-bit code
    '''
    if register_code < 0 or register_code >= len(WORD_REGISTERS) + len(BYTE_REGISTERS):
        raise InvalidRegisterCodeError(register_code)
    if register_code < len(WORD_REGISTERS):
        return WORD_REGISTERS[register_code]
    return BYTE_REGISTERS[register_code - len(WORD_REGISTERS)]


# pylint: disable=missing-docstring

class RegisterError(Exception):
    pass


class InvalidRegisterNameError(RegisterError):
    pass


class InvalidRegisterCodeError(RegisterError):
    pass


class InvalidTokenError(Exception):
    pass


class InvalidOperandError(Exception):
    pass


class InvalidWriteOperationError(Exception):
    pass


class InsufficientOperandBufferError(Exception):
    pass
