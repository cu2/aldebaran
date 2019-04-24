from utils import errors, utils


class StackError(Exception):
    pass


class StackOverflowError(StackError):
    pass


class StackUnderflowError(StackError):
    pass


class CPU(utils.Hardware):

    def __init__(self, system_addresses, system_interrupts, instruction_set, user_log=None, log=None):
        utils.Hardware.__init__(self, log)
        self.system_addresses = system_addresses
        self.system_interrupts = system_interrupts
        self.instruction_opcode_mapping = {
            opcode: inst
            for opcode, inst in instruction_set
        }
        self.user_log = user_log
        self.ram = None
        self.interrupt_controller = None
        self.timer = None
        self.registers = {
            'IP': self.system_addresses['entry_point'],
            'SP': self.system_addresses['SP'],
            'AX': 0x0000,
            'BX': 0x0000,
            'CX': 0x0000,
            'DX': 0x0000,
            'BP': 0x0000,
            'SI': 0x0000,
            'DI': 0x0000,
        }
        self.flags = {
            'interrupt': 1,
        }
        self.operand_buffer_size = 16
        self.halt = False
        self.shutdown = False

    def register_architecture(self, ram, interrupt_controller, device_controller, timer):
        self.ram = ram
        self.interrupt_controller = interrupt_controller
        self.device_controller = device_controller
        self.timer = timer

    def step(self):
        if not self.ram:
            self.log.log('cpu', 'ERROR: Cannot run without RAM.')
            return
        if self.interrupt_controller and self.flags['interrupt']:
            interrupt_number = self.interrupt_controller.check()
            if interrupt_number is not None:
                self.call_int(interrupt_number)
                return
        if self.halt:
            return
        self.mini_debugger()
        inst_opcode = self.ram.read_byte(self.registers['IP'])
        try:
            inst_class = self.instruction_opcode_mapping[inst_opcode]
        except KeyError:
            raise errors.UnknownOpcodeError(utils.byte_to_str(inst_opcode))
        operand_buffer = [self.ram.read_byte(self.registers['IP'] + i) for i in range(1, self.operand_buffer_size + 1)]
        current_instruction = inst_class(self, operand_buffer)
        self.log.log('cpu', '%s %s' % (inst_class.__name__, current_instruction.operands))
        next_ip = current_instruction.run()
        self.registers['IP'] = next_ip % self.ram.size
        self.log.log('', '')
        return self.shutdown

    def mini_debugger(self):
        if not isinstance(self.log, utils.SilentLog):
            ram_page = (self.registers['IP'] // 16) * 16
            rel_sp = self.system_addresses['SP'] - self.registers['SP']
            stack_page = self.system_addresses['SP'] - 11 - (rel_sp // 12) * 12
            self.log.log('cpu', 'IP=%s AX/BX/CX/DX=%s/%s/%s/%s RAM[%s]:%s ST[%s/%s]:%s' % (
                utils.word_to_str(self.registers['IP']),
                utils.word_to_str(self.registers['AX']),
                utils.word_to_str(self.registers['BX']),
                utils.word_to_str(self.registers['CX']),
                utils.word_to_str(self.registers['DX']),
                utils.word_to_str(ram_page),
                ''.join([('>' if idx == self.registers['IP'] else ' ') + utils.byte_to_str(self.ram.mem[idx]) for idx in range(ram_page, ram_page + 16)]),
                utils.word_to_str(stack_page),
                utils.word_to_str(rel_sp // 12),
                ''.join([utils.byte_to_str(self.ram.mem[idx]) + (
                        (
                            '<{' if idx == self.registers['BP'] else '< '
                        ) if idx == self.registers['SP'] else (
                            '{ ' if idx == self.registers['BP'] else '  '
                        )
                    ) for idx in range(stack_page, stack_page + 16)]),
            ))

    def get_register(self, register_name):
        value = None
        hex_value = None
        if register_name in self.registers:
            value = self.registers[register_name]
            hex_value = utils.word_to_str(value)
        elif register_name in ['AL', 'BL', 'CL', 'DL']:
            value = utils.get_low(self.registers[register_name[0] + 'X'])
            hex_value = utils.byte_to_str(value)
        elif register_name in ['AH', 'BH', 'CH', 'DH']:
            value = utils.get_high(self.registers[register_name[0] + 'X'])
            hex_value = utils.byte_to_str(value)
        else:
            raise errors.InvalidRegisterNameError(register_name)
        self.log.log('cpu', 'get_reg(%s) = %s' % (register_name, hex_value))
        return value

    def set_register(self, register_name, value):
        if register_name in self.registers:
            self.registers[register_name] = value
            self.log.log('cpu', 'set_reg(%s) = %s' % (register_name, utils.word_to_str(value)))
            return
        if register_name in ['AL', 'BL', 'CL', 'DL']:
            self.registers[register_name[0] + 'X'] = utils.set_low(self.registers[register_name[0] + 'X'], value)
        elif register_name in ['AH', 'BH', 'CH', 'DH']:
            self.registers[register_name[0] + 'X'] = utils.set_high(self.registers[register_name[0] + 'X'], value)
        else:
            raise errors.InvalidRegisterNameError(register_name)
        self.log.log('cpu', 'set_reg(%s) = %s' % (register_name, utils.byte_to_str(value)))

    def stack_push_byte(self, value):
        if self.registers['SP'] < 1:
            raise StackOverflowError()
        self.ram.write_byte(self.registers['SP'], value)
        self.log.log('cpu', 'pushed byte %s' % utils.byte_to_str(value))
        self.registers['SP'] -= 1

    def stack_pop_byte(self):
        if self.registers['SP'] >= self.system_addresses['SP']:
            raise StackUnderflowError()
        self.registers['SP'] += 1
        value = self.ram.read_byte(self.registers['SP'])
        self.log.log('cpu', 'popped byte %s' % utils.byte_to_str(value))
        return value

    def stack_push_word(self, value):
        if self.registers['SP'] < 2:
            raise StackOverflowError()
        self.ram.write_word(self.registers['SP'] - 1, value)
        self.log.log('cpu', 'pushed word %s' % utils.word_to_str(value))
        self.registers['SP'] -= 2

    def stack_pop_word(self):
        if self.registers['SP'] >= self.system_addresses['SP'] - 1:
            raise StackUnderflowError()
        self.registers['SP'] += 2
        value = self.ram.read_word(self.registers['SP'] - 1)
        self.log.log('cpu', 'popped word %s' % utils.word_to_str(value))
        return value

    def stack_push_flags(self):
        flag_word = 0x0000
        for idx, name in enumerate(['interrupt']):
            flag_word += self.flags[name] << idx
        self.stack_push_word(flag_word)
        self.log.log('cpu', 'pushed FLAGS')

    def stack_pop_flags(self):
        flag_word = self.stack_pop_word()
        for idx, name in enumerate(['interrupt']):
            self.flags[name] = (flag_word >> idx) & 0x0001
        self.log.log('cpu', 'popped FLAGS')

    def enable_interrupts(self):
        self.flags['interrupt'] = True
        self.log.log('cpu', 'interrupts enabled')

    def disable_interrupts(self):
        self.flags['interrupt'] = False
        self.log.log('cpu', 'interrupts disabled')

    def call_int(self, interrupt_number):
        self.log.log('cpu', 'calling interrupt: %s' % utils.byte_to_str(interrupt_number))
        self.halt = False
        self.stack_push_flags()
        self.disable_interrupts()
        self.stack_push_word(self.registers['IP'])
        self.registers['IP'] = self.ram.read_word(self.system_addresses['IVT'] + 2 * interrupt_number) % self.ram.size
