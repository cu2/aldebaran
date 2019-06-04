'''
CPU
'''

import logging
import time

from instructions import operands
from utils import utils
from utils.errors import AldebaranError


logger = logging.getLogger('hardware.cpu')
logger_user = logging.getLogger('hardware.cpu-user')


class CPU:
    '''
    CPU
    '''

    def __init__(self, system_addresses, instruction_set, operand_buffer_size, halt_freq):
        self.system_addresses = system_addresses
        self.instruction_opcode_mapping = {
            opcode: inst
            for opcode, inst in instruction_set
        }
        self.ip = self.system_addresses['entry_point']
        self.operand_buffer_size = operand_buffer_size
        self.halt_freq = halt_freq
        self.halt = False
        self.shutdown = False
        self.last_ip = None
        self.last_instruction = None

        self.registers = None
        self.stack = None
        self.memory = None
        self.interrupt_controller = None
        self.device_controller = None
        self.timer = None
        self.architecture_registered = False

    def register_architecture(self, registers, stack, memory, interrupt_controller, device_controller, timer):
        '''
        Register other internal devices
        '''
        self.registers = registers
        self.stack = stack
        self.stack.register_architecture(registers, memory)
        self.memory = memory
        self.interrupt_controller = interrupt_controller
        self.device_controller = device_controller
        self.timer = timer
        self.architecture_registered = True

    def step(self):
        '''
        Main loop:
        - check and call hardware interrupts
        - parse and execute instructions
        - handle IP
        '''
        if self._check_hardware_interrupts():
            return
        if self.halt:
            time.sleep(1 / self.halt_freq)  # so it doesn't burn the host machine's CPU in turbo mode
            return
        self._mini_debugger()
        inst_opcode = self.memory.read_byte(self.ip, silent=True)
        operand_buffer = [
            self.memory.read_byte(self.ip + idx, silent=True)
            for idx in range(1, self.operand_buffer_size + 1)
        ]
        self.last_ip = self.ip
        self.last_instruction = self._parse_instruction(inst_opcode, operand_buffer)
        next_ip = self.last_instruction.run()
        self.ip = next_ip

    def user_log(self, message, *args):
        '''
        Log message to user log
        '''
        logger_user.info(message, *args)

    def cpu_log(self, message, *args):
        '''
        Log message to CPU log
        '''
        logger.info(message, *args)

    def enable_interrupts(self):
        '''
        Enable hardware interrupts
        '''
        self.registers.set_flag('interrupt', 1, silent=True)
        logger.debug('Hardware interrupts enabled')

    def disable_interrupts(self):
        '''
        Disable hardware interrupts
        '''
        self.registers.set_flag('interrupt', 0, silent=True)
        logger.debug('Hardware interrupts disabled')

    def _parse_instruction(self, inst_opcode, operand_buffer):
        try:
            inst_class = self.instruction_opcode_mapping[inst_opcode]
        except KeyError:
            raise UnknownOpcodeError('Unknown opcode: {}'.format(utils.byte_to_str(inst_opcode)))
        instruction = inst_class(self, operand_buffer)
        logger.info('Instruction: %s %s', inst_class.__name__, ' '.join([
            operands.operand_to_str(op)
            for op in instruction.operands
        ]))
        return instruction

    def _check_hardware_interrupts(self):
        if self.interrupt_controller and self.registers.get_flag('interrupt', silent=True) == 1:
            interrupt_number = self.interrupt_controller.check()
            if interrupt_number is not None:
                self._mini_debugger()
                self._call_hardware_interrupt(interrupt_number)
                return True
        return False

    def _call_hardware_interrupt(self, interrupt_number):
        logger.debug('Calling hardware interrupt: %s', utils.byte_to_str(interrupt_number))
        self.halt = False
        self.stack.push_flags()
        self.disable_interrupts()
        self.stack.push_word(self.ip)
        self.ip = self.memory.read_word(self.system_addresses['IVT'] + 2 * interrupt_number)

    def _mini_debugger(self):
        if logger.level != logging.DEBUG:
            return
        ram_page_size = 16
        stack_page_size = 32
        sp = self.registers.get_register('SP', silent=True)
        bp = self.registers.get_register('BP', silent=True)
        ram_page = (self.ip // ram_page_size) * ram_page_size
        rel_sp = self.system_addresses['bottom_of_stack'] - sp
        stack_page = self.system_addresses['bottom_of_stack'] - (stack_page_size - 1) - (rel_sp // stack_page_size) * stack_page_size
        if stack_page < 0:
            stack_page = 0
        logger.debug(
            'IP=%s         RAM   %s-%s: %s',
            utils.word_to_str(self.ip),
            utils.word_to_str(ram_page),
            utils.word_to_str(ram_page + ram_page_size - 1),
            ''.join([
                ('>' if idx == self.ip else ' ') + utils.byte_to_str(self.memory.read_byte(idx, silent=True))
                for idx in range(ram_page, ram_page + ram_page_size)
            ]),
        )
        logger.debug(
            'SP=%s BP=%s Stack %s-%s:  %s',
            utils.word_to_str(sp),
            utils.word_to_str(bp),
            utils.word_to_str(stack_page),
            utils.word_to_str(stack_page + stack_page_size - 1),
            ''.join([utils.byte_to_str(self.memory.read_byte(idx, silent=True)) + (
                (
                    '{' if idx == bp else '<'
                ) if idx == sp else (
                    '[' if idx == bp else ' '
                )
            ) for idx in range(stack_page, stack_page + stack_page_size)]),
        )
        logger.debug(
            'AX/BX/CX/DX=%s/%s/%s/%s SI/DI=%s/%s',
            utils.word_to_str(self.registers.get_register('AX', silent=True)),
            utils.word_to_str(self.registers.get_register('BX', silent=True)),
            utils.word_to_str(self.registers.get_register('CX', silent=True)),
            utils.word_to_str(self.registers.get_register('DX', silent=True)),
            utils.word_to_str(self.registers.get_register('SI', silent=True)),
            utils.word_to_str(self.registers.get_register('DI', silent=True)),
        )


# pylint: disable=missing-docstring

class CPUError(AldebaranError):
    pass


class UnknownOpcodeError(CPUError):
    pass
