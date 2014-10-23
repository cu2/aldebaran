import aux
import errors


OPLEN_BYTE = 0
OPLEN_WORD = 1

OPTYPE_IMMEDIATE = 0        # dd, dddd      e.g. labels, interrupts, IO
OPTYPE_REGISTER = 1         # AX            e.g. temporary variables
OPTYPE_MEM_WORD = 2         # [dddd]        e.g. global variables
OPTYPE_MEM_REG_BYTE = 3     # [AX+dd]       e.g. params (BP+), local variables (SP+), structs with address in reg
OPTYPE_MEM_WORD_REG = 4     # [dddd+AX]     e.g. arrays (address = global variable)
OPTYPE_MEM_WORD_BYTE = 5    # [dddd+dd]     e.g. structs (address = global variable)

WORD_REGISTERS = ['AX', 'BX', 'CX', 'DX', 'BP', 'SP', 'SI', 'DI']
BYTE_REGISTERS = ['AL', 'AH', 'BL', 'BH', 'CL', 'CH', 'DL', 'DH']


def get_register_code(register_name):
    '''Return register code by name'''
    try:
        return WORD_REGISTERS.index(register_name)
    except ValueError:
        try:
            return len(WORD_REGISTERS) + BYTE_REGISTERS.index(register_name)
        except ValueError:
            raise errors.InvalidRegisterNameError(register_name)


def get_register_name_by_code(register_code):
    '''Return register name by code'''
    if register_code < len(WORD_REGISTERS):
        return WORD_REGISTERS[register_code]
    if register_code - len(WORD_REGISTERS) < len(BYTE_REGISTERS):
        return BYTE_REGISTERS[register_code - len(WORD_REGISTERS)]
    raise errors.InvalidRegisterCodeError(register_code)


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
    for key, value in globals().iteritems():
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


def encode_argument(arg):
    '''Return opcode of argument'''
    # OPTYPE_REGISTER
    if arg in WORD_REGISTERS:
        return [
            (OPLEN_WORD << 7) + (OPTYPE_REGISTER << 4) + get_register_code(arg),
        ]
    if arg in BYTE_REGISTERS:
        return [
            (OPLEN_BYTE << 7) + (OPTYPE_REGISTER << 4) + get_register_code(arg),
        ]
    # OPTYPE_IMMEDIATE
    if arg[0] != '[':
        if len(arg) == 4:
            return [
                (OPLEN_WORD << 7) + (OPTYPE_IMMEDIATE << 4),
            ] + list(aux.word_to_bytes(aux.str_to_int(arg)))
        return [
            (OPLEN_BYTE << 7) + (OPTYPE_IMMEDIATE << 4),
            aux.str_to_int(arg),
        ]
    # OPTYPE_MEM_*
    if arg[-1] == ']':
        oplen = OPLEN_WORD
        arg = arg[1:-1]
    else:
        if arg[-1] == 'B':
            oplen = OPLEN_BYTE
        else:
            oplen = OPLEN_WORD
        arg = arg[1:-2]
    # OPTYPE_MEM_WORD
    if '+' not in arg:
        return [
            (oplen << 7) + (OPTYPE_MEM_WORD << 4),
        ] + list(aux.word_to_bytes(aux.str_to_int(arg)))
    arg1, arg2 = arg.split('+')
    # OPTYPE_MEM_REG_BYTE
    if arg1 in WORD_REGISTERS:
        return [
            (oplen << 7) + (OPTYPE_MEM_REG_BYTE << 4) + get_register_code(arg1),
            aux.str_to_int(arg2),
        ]
    # OPTYPE_MEM_WORD_REG
    if arg2 in WORD_REGISTERS:
        return [
            (oplen << 7) + (OPTYPE_MEM_WORD_REG << 4) + get_register_code(arg2),
        ] + list(aux.word_to_bytes(aux.str_to_int(arg1)))
    # OPTYPE_MEM_WORD_BYTE
    return [
        (oplen << 7) + (OPTYPE_MEM_WORD_BYTE << 4),
    ] + list(aux.word_to_bytes(aux.str_to_int(arg1))) + [
        aux.str_to_int(arg2),
    ]


class Instruction(object):

    operand_count = 0

    def __init__(self, cpu, operand_buffer):
        self.cpu = cpu
        self.operands, self.opcode_length = self._parse_operand_buffer(operand_buffer)
        self.ip = self.cpu.registers['IP']

    def __repr__(self):
        return self.__class__.__name__

    def _parse_operand_buffer(self, operand_buffer):
        '''Return operands as (oplen, optype, oprest) tuples from operand_buffer'''
        operands = []
        operand_buffer_idx = 0
        try:
            while True:
                if len(operands) >= self.operand_count:
                    break
                opbyte = operand_buffer[operand_buffer_idx]
                operand_buffer_idx += 1
                oplen = opbyte >> 7
                optype = (opbyte & 0x7F) >> 4
                opreg = opbyte & 0x0F
                if optype == OPTYPE_IMMEDIATE:
                    if oplen == OPLEN_WORD:
                        operand = (oplen, optype, [
                            aux.bytes_to_word(operand_buffer[operand_buffer_idx+0], operand_buffer[operand_buffer_idx+1])
                        ])
                        operand_buffer_idx += 2
                    else:
                        operand = (oplen, optype, [
                            operand_buffer[operand_buffer_idx+0]
                        ])
                        operand_buffer_idx += 1
                elif optype == OPTYPE_REGISTER:
                    operand = (oplen, optype, [
                        opreg
                    ])
                elif optype == OPTYPE_MEM_WORD:
                    operand = (oplen, optype, [
                        aux.bytes_to_word(operand_buffer[operand_buffer_idx+0], operand_buffer[operand_buffer_idx+1])
                    ])
                    operand_buffer_idx += 2
                elif optype == OPTYPE_MEM_REG_BYTE:
                    operand = (oplen, optype, [
                        opreg,
                        operand_buffer[operand_buffer_idx+0]
                    ])
                    operand_buffer_idx += 1
                elif optype == OPTYPE_MEM_WORD_REG:
                    operand = (oplen, optype, [
                        aux.bytes_to_word(operand_buffer[operand_buffer_idx+0], operand_buffer[operand_buffer_idx+1]),
                        opreg
                    ])
                    operand_buffer_idx += 2
                elif optype == OPTYPE_MEM_WORD_BYTE:
                    operand = (oplen, optype, [
                        aux.bytes_to_word(operand_buffer[operand_buffer_idx+0], operand_buffer[operand_buffer_idx+1]),
                        operand_buffer[operand_buffer_idx+2]
                    ])
                    operand_buffer_idx += 3
                else:
                    raise errors.InvalidOperandError(self, operand_buffer, operand_buffer_idx)
                operands.append(operand)
        except IndexError:
            raise errors.InsufficientOperandBufferError(self, operand_buffer)
        return operands, 1 + operand_buffer_idx

    def get_operand(self, opnum):
        '''Return value of operand'''
        oplen, optype, oprest = self.operands[opnum]
        if optype == OPTYPE_IMMEDIATE:
            return oprest[0]
        if optype == OPTYPE_REGISTER:
            return self.cpu.get_register(get_register_name_by_code(oprest[0]))
        if optype == OPTYPE_MEM_WORD:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(oprest[0])
            else:
                return self.cpu.ram.read_byte(oprest[0])
        if optype == OPTYPE_MEM_REG_BYTE:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(self.cpu.get_register(get_register_name_by_code(oprest[0])) + oprest[1])
            else:
                return self.cpu.ram.read_byte(self.cpu.get_register(get_register_name_by_code(oprest[0])) + oprest[1])
        if optype == OPTYPE_MEM_WORD_REG:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])))
            else:
                return self.cpu.ram.read_byte(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])))
        if optype == OPTYPE_MEM_WORD_BYTE:
            if oplen == OPLEN_WORD:
                return self.cpu.ram.read_word(oprest[0] + oprest[1])
            else:
                return self.cpu.ram.read_byte(oprest[0] + oprest[1])
        raise errors.InvalidOperandError(self, self.operands[opnum])

    def set_operand(self, opnum, value):
        '''Set value of operand'''
        oplen, optype, oprest = self.operands[opnum]
        if optype == OPTYPE_IMMEDIATE:
            raise errors.InvalidWriteOperationError(self, self.operands[opnum])
        elif optype == OPTYPE_REGISTER:
            self.cpu.set_register(get_register_name_by_code(oprest[0]), value)
        elif optype == OPTYPE_MEM_WORD:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(oprest[0], value)
            else:
                self.cpu.ram.write_byte(oprest[0], value)
        elif optype == OPTYPE_MEM_REG_BYTE:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(self.cpu.get_register(get_register_name_by_code(oprest[0])) + oprest[1], value)
            else:
                self.cpu.ram.write_byte(self.cpu.get_register(get_register_name_by_code(oprest[0])) + oprest[1], value)
        elif optype == OPTYPE_MEM_WORD_REG:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])), value)
            else:
                self.cpu.ram.write_byte(oprest[0] + self.cpu.get_register(get_register_name_by_code(oprest[1])), value)
        elif optype == OPTYPE_MEM_WORD_BYTE:
            if oplen == OPLEN_WORD:
                self.cpu.ram.write_word(oprest[0] + oprest[1], value)
            else:
                self.cpu.ram.write_byte(oprest[0] + oprest[1], value)
        else:
            raise errors.InvalidOperandError(self, self.operands[opnum])

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
        pass


class NOP(Instruction):
    '''No operation'''
    pass


class HALT(Instruction):
    '''Halt CPU'''

    def do(self):
        self.cpu.halt = True
        self.cpu.log.log('cpu', 'Halted')
        return self.ip


class SHUTDOWN(Instruction):
    '''Shut down Aldebaran'''

    def do(self):
        self.cpu.shutdown = True
        self.cpu.log.log('cpu', 'Shut down')
        return self.ip


class PRINT(Instruction):
    '''Print int to CPU log'''

    operand_count = 1

    def do(self):
        self.cpu.user_log.log('print', aux.word_to_str(self.get_operand(0)))


class PRINTCHAR(Instruction):
    '''Print char to CPU log'''

    operand_count = 1

    def do(self):
        self.cpu.user_log.log('print', chr(self.get_operand(0)))


class MOV(Instruction):
    '''Transfer data from reg/mem/immediate value to reg/mem'''

    operand_count = 2

    def do(self):
        self.set_operand(0, self.get_operand(1))


class ADD(Instruction):
    '''Add'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) + self.get_operand(2))


class SUB(Instruction):
    '''Substract'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) - self.get_operand(2))


class MUL(Instruction):
    '''Multiply'''

    operand_count = 3

    def do(self):
        self.set_operand(0, self.get_operand(1) * self.get_operand(2))


class INC(Instruction):
    '''Increase'''

    operand_count = 2

    def do(self):
        self.set_operand(0, self.get_operand(0) + self.get_operand(1))


class DEC(Instruction):
    '''Decrease'''

    operand_count = 2

    def do(self):
        self.set_operand(0, self.get_operand(0) - self.get_operand(1))


class JUMP(Instruction):
    '''Jump'''

    operand_count = 1

    def do(self):
        return self.get_operand(0)


class JZ(Instruction):
    '''Jump if zero'''

    operand_count = 2

    def do(self):
        if self.get_operand(0) == 0:
            return self.get_operand(1)


class JNZ(Instruction):
    '''Jump if non-zero'''

    operand_count = 2

    def do(self):
        if self.get_operand(0) != 0:
            return self.get_operand(1)


class JEQ(Instruction):
    '''Jump if equal'''

    operand_count = 3

    def do(self):
        if self.get_operand(0) == self.get_operand(1):
            return self.get_operand(2)


class JNE(Instruction):
    '''Jump if not equal'''

    operand_count = 3

    def do(self):
        if self.get_operand(0) != self.get_operand(1):
            return self.get_operand(2)


class JGT(Instruction):
    '''Jump if greater'''

    operand_count = 3

    def do(self):
        if self.get_operand(0) > self.get_operand(1):
            return self.get_operand(2)


class JGE(Instruction):
    '''Jump if greater or equal'''

    operand_count = 3

    def do(self):
        if self.get_operand(0) >= self.get_operand(1):
            return self.get_operand(2)


class JLT(Instruction):
    '''Jump if less'''

    operand_count = 3

    def do(self):
        if self.get_operand(0) < self.get_operand(1):
            return self.get_operand(2)


class JLE(Instruction):
    '''Jump if less or equal'''

    operand_count = 3

    def do(self):
        if self.get_operand(0) <= self.get_operand(1):
            return self.get_operand(2)


class PUSH(Instruction):
    '''Push to stack'''

    operand_count = 1

    def do(self):
        oplen, optype, oprest = self.operands[0]
        if oplen == OPLEN_WORD:
            self.cpu.stack_push_word(self.get_operand(0))
        else:
            self.cpu.stack_push_byte(self.get_operand(0))


class POP(Instruction):
    '''Pop from stack'''

    operand_count = 1

    def do(self):
        oplen, optype, oprest = self.operands[0]
        if oplen == OPLEN_WORD:
            self.set_operand(0, self.cpu.stack_pop_word())
        else:
            self.set_operand(0, self.cpu.stack_pop_byte())


class PUSHF(Instruction):
    '''Push FLAGS to stack'''

    def do(self):
        self.cpu.stack_push_flags()


class POPF(Instruction):
    '''Pop flags from stack'''

    def do(self):
        self.cpu.stack_pop_flags()


class CALL(Instruction):
    '''Call subroutine'''

    operand_count = 1

    def do(self):
        self.cpu.stack_push_word(self.ip + self.opcode_length)  # IP of next instruction
        return self.get_operand(0)


class RET(Instruction):
    '''Return from subroutine'''

    def do(self):
        return self.cpu.stack_pop_word()


class INT(Instruction):
    '''Call interrupt'''

    operand_count = 1

    def do(self):
        self.cpu.stack_push_flags()
        self.cpu.stack_push_word(self.ip + self.opcode_length)  # IP of next instruction
        interrupt_number = self.get_operand(0)
        return self.cpu.ram.read_word(self.cpu.system_addresses['IVT'] + 2 * interrupt_number)


class IRET(Instruction):
    '''Return from interrupt'''

    def do(self):
        next_ip = self.cpu.stack_pop_word()
        self.cpu.stack_pop_flags()
        return next_ip


class SETINT(Instruction):
    '''Set IVT'''

    operand_count = 2

    def do(self):
        interrupt_number = self.get_operand(0)
        self.cpu.ram.write_word(self.cpu.system_addresses['IVT'] + 2 * interrupt_number, self.get_operand(1))


class STI(Instruction):
    '''Enable interrupts'''

    def do(self):
        self.cpu.enable_interrupts()


class CLI(Instruction):
    '''Disable interrupts'''

    def do(self):
        self.cpu.disable_interrupts()


class IN(Instruction):
    '''Transfer input data from IOPort into memory, set CX to length and send ACK'''

    operand_count = 2

    def do(self):
        ioport_number = self.get_operand(0)
        pos = self.get_operand(1)
        input_data = self.cpu.device_controller.ioports[ioport_number].read_input()
        for idx, value in enumerate(input_data):
            self.cpu.ram.write_byte(pos + idx, ord(value))
        self.cpu.log.log('cpu', 'Input data from IOPort %s: %s (%s bytes)' % (ioport_number, aux.binary_to_str(input_data), len(input_data)))
        self.cpu.set_register('CX', len(input_data))


class OUT(Instruction):
    '''Transfer output data (CX bytes) from memory to IOPort and set CX'''

    operand_count = 2

    def do(self):
        ioport_number = self.get_operand(0)
        pos = self.get_operand(1)
        cx = self.cpu.get_register('CX')
        output_data = self.cpu.device_controller.ioports[ioport_number].send_output(''.join([
            chr(self.cpu.ram.read_byte(pos + idx)) for idx in xrange(cx)
        ]))
        self.cpu.log.log('cpu', 'Output data to IOPort %s: %s (%s bytes)' % (ioport_number, aux.binary_to_str(output_data), cx))
        self.cpu.set_register('CX', 0)  # is it required?
