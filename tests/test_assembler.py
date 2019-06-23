import logging
import unittest

from assembler.assembler import Assembler, AssemblerError, Scope, ScopeError
from assembler.macros import MacroError, VariableError
from assembler.tokenizer import Token, TokenType, Reference
from instructions import instruction_set
from instructions.operands import WORD_REGISTERS, BYTE_REGISTERS, get_operand_opcode


class TestAssembler(unittest.TestCase):

    def setUp(self):
        self.instruction_set = [
            (0x12, instruction_set.arithmetic.ADD),
            (0x34, instruction_set.data_transfer.MOV),
            (0x56, instruction_set.jump.JMP),
            (0x78, instruction_set.misc.NOP),
            (0x9A, instruction_set.misc.SHUTDOWN),
            (0xBC, instruction_set.control_flow.ENTER),
        ]
        self.assembler = Assembler(
            instruction_set=self.instruction_set,
            registers={
                'byte': BYTE_REGISTERS,
                'word': WORD_REGISTERS,
            },
        )
        logging.getLogger('assembler').setLevel(logging.CRITICAL)

    def test_instructions(self):
        opcode = self.assembler.assemble_code('''
        NOP
        NOP
        SHUTDOWN
        ''')
        expected_opcode = [
            0x78,
            0x78,
            0x9A,
        ]
        self.assertListEqual(opcode, expected_opcode)

    def test_operands(self):
        opcode = self.assembler.assemble_code('''
        MOV AX 0x1234
        NOP
        SHUTDOWN
        ''')
        expected_opcode = [0x34]
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', None))
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_LITERAL, 0x1234, None))
        expected_opcode += [0x78]
        expected_opcode += [0x9A]
        self.assertListEqual(opcode, expected_opcode)

    def test_label_ok(self):
        opcode = self.assembler.assemble_code('''
        loop:
        NOP
        JMP loop
        SHUTDOWN
        ''')
        expected_opcode = [0x78]
        expected_opcode += [0x56]
        expected_opcode += get_operand_opcode(Token(TokenType.ADDRESS_WORD_LITERAL, -1, None))
        expected_opcode += [0x9A]
        self.assertListEqual(opcode, expected_opcode)

    def test_label_error(self):
        with self.assertRaises(AssemblerError):
            self.assembler.assemble_code('''
            loop:
            NOP
            JMP other_loop
            SHUTDOWN
            ''')

    def test_macro_dat_and_datn(self):
        opcode = self.assembler.assemble_code('''
        MOV AX [stuff]
        NOP
        SHUTDOWN
        stuff: .DAT 0x1234 0x56 'ABC'
        .DATN 0x05 0xFF
        .DATN 0x03 0x1234
        .DATN 0x02 'ABC'
        ''')
        expected_opcode = [0x34]
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', None))
        expected_opcode += get_operand_opcode(Token(
            TokenType.REL_REF_WORD,
            Reference(7, None, 'W'),
            None,
        ))
        expected_opcode += [0x78]
        expected_opcode += [0x9A]
        expected_opcode += [0x12, 0x34, 0x56, 0x41, 0x42, 0x43]
        expected_opcode += [0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        expected_opcode += [0x12, 0x34, 0x12, 0x34, 0x12, 0x34]
        expected_opcode += [0x41, 0x42, 0x43, 0x41, 0x42, 0x43]
        self.assertListEqual(opcode, expected_opcode)

    def test_macro_dat_and_datn_error(self):
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DAT
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DAT a
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 0x00 0x00 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN a 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 'a' 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .DATN 0x00 a
            ''')

    def test_macro_const(self):
        opcode = self.assembler.assemble_code('''
        .CONST $stuff 0x1234
        .CONST $other_stuff $stuff
        MOV AX $other_stuff
        NOP
        SHUTDOWN
        ''')
        expected_opcode = [0x34]
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', None))
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_LITERAL, 0x1234, None))
        expected_opcode += [0x78]
        expected_opcode += [0x9A]
        self.assertListEqual(opcode, expected_opcode)

    def test_macro_const_error(self):
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST $x
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST a 0x00
            ''')
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .CONST $x a
            ''')
        with self.assertRaises(VariableError):
            self.assembler.assemble_code('''
            .CONST $x $y
            ''')
        with self.assertRaises(VariableError):
            self.assembler.assemble_code('''
            .CONST $x 0x00
            .CONST $x 0x01
            ''')

    def test_macro_param_and_var(self):
        opcode = self.assembler.assemble_code('''
        ENTER 0x02 0x04
        .CONST $default_value 0x1234
        .PARAM $p
        .VAR $v1
        .VAR $v2 $default_value
        MOV AX $p
        MOV AX $v1
        MOV AX $v2
        NOP
        SHUTDOWN
        ''')
        expected_opcode = [0xBC]
        expected_opcode += get_operand_opcode(Token(TokenType.BYTE_LITERAL, 0x02, None))
        expected_opcode += get_operand_opcode(Token(TokenType.BYTE_LITERAL, 0x04, None))

        expected_opcode += [0x34]
        expected_opcode += get_operand_opcode(Token(
            TokenType.ABS_REF_REG,
            Reference('BP', -3, 'W'),
            None,
        ))
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_LITERAL, 0x1234, None))

        expected_opcode += [0x34]
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', None))
        expected_opcode += get_operand_opcode(Token(
            TokenType.ABS_REF_REG,
            Reference('BP', 7, 'W'),
            None,
        ))

        expected_opcode += [0x34]
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', None))
        expected_opcode += get_operand_opcode(Token(
            TokenType.ABS_REF_REG,
            Reference('BP', -1, 'W'),
            None,
        ))

        expected_opcode += [0x34]
        expected_opcode += get_operand_opcode(Token(TokenType.WORD_REGISTER, 'AX', None))
        expected_opcode += get_operand_opcode(Token(
            TokenType.ABS_REF_REG,
            Reference('BP', -3, 'W'),
            None,
        ))

        expected_opcode += [0x78]
        expected_opcode += [0x9A]
        self.assertListEqual(opcode, expected_opcode)

    def test_macro_param_and_var_error(self):
        with self.assertRaises(MacroError):
            self.assembler.assemble_code('''
            .PARAM $p
            ''')
        with self.assertRaises(ScopeError):
            self.assembler.assemble_code('''
            ENTER 0x02 0x00
            .PARAM $p1
            .PARAM $p2
            ''')
        with self.assertRaises(VariableError):
            self.assembler.assemble_code('''
            ENTER 0x04 0x00
            .PARAM $p
            .PARAM $p
            ''')


class TestScope(unittest.TestCase):

    def test_params_error_too_many(self):
        scope = _create_scope(0, 0)
        with self.assertRaises(ScopeError):
            scope.add_parameter('$p', 2)

    def test_params_error_wrong_size(self):
        scope = _create_scope(4, 0)
        with self.assertRaises(ScopeError):
            scope.add_parameter('$p', 3)

    def test_params_error_duplicate(self):
        scope = _create_scope(4, 0)
        scope.add_parameter('$p', 2)
        with self.assertRaises(ScopeError):
            scope.add_parameter('$p', 2)

    def test_params_byte_ok(self):
        param_bytes = _get_param_bytes([1, 1, 1, 1, 1])
        self.assertListEqual(param_bytes[0], [11, 11])
        self.assertListEqual(param_bytes[1], [10, 10])
        self.assertListEqual(param_bytes[2], [9, 9])
        self.assertListEqual(param_bytes[3], [8, 8])
        self.assertListEqual(param_bytes[4], [7, 7])

    def test_params_word_ok(self):
        param_bytes = _get_param_bytes([2, 2, 2, 2, 2])
        self.assertListEqual(param_bytes[0], [15, 16])
        self.assertListEqual(param_bytes[1], [13, 14])
        self.assertListEqual(param_bytes[2], [11, 12])
        self.assertListEqual(param_bytes[3], [9, 10])
        self.assertListEqual(param_bytes[4], [7, 8])

    def test_params_mixed_ok(self):
        param_bytes = _get_param_bytes([1, 1, 2, 1, 2])
        self.assertListEqual(param_bytes[0], [13, 13])
        self.assertListEqual(param_bytes[1], [12, 12])
        self.assertListEqual(param_bytes[2], [10, 11])
        self.assertListEqual(param_bytes[3], [9, 9])
        self.assertListEqual(param_bytes[4], [7, 8])

    def test_vars_error_too_many(self):
        scope = _create_scope(0, 0)
        with self.assertRaises(ScopeError):
            scope.add_variable('$v', 2)

    def test_vars_error_wrong_size(self):
        scope = _create_scope(0, 4)
        with self.assertRaises(ScopeError):
            scope.add_variable('$v', 3)

    def test_vars_byte_ok(self):
        var_bytes = _get_var_bytes([1, 1, 1, 1, 1])
        self.assertListEqual(var_bytes[0], [0, 0])
        self.assertListEqual(var_bytes[1], [-1, -1])
        self.assertListEqual(var_bytes[2], [-2, -2])
        self.assertListEqual(var_bytes[3], [-3, -3])
        self.assertListEqual(var_bytes[4], [-4, -4])

    def test_vars_word_ok(self):
        var_bytes = _get_var_bytes([2, 2, 2, 2, 2])
        self.assertListEqual(var_bytes[0], [-1, 0])
        self.assertListEqual(var_bytes[1], [-3, -2])
        self.assertListEqual(var_bytes[2], [-5, -4])
        self.assertListEqual(var_bytes[3], [-7, -6])
        self.assertListEqual(var_bytes[4], [-9, -8])

    def test_vars_mixed_ok(self):
        var_bytes = _get_var_bytes([1, 1, 2, 1, 2])
        self.assertListEqual(var_bytes[0], [0, 0])
        self.assertListEqual(var_bytes[1], [-1, -1])
        self.assertListEqual(var_bytes[2], [-3, -2])
        self.assertListEqual(var_bytes[3], [-4, -4])
        self.assertListEqual(var_bytes[4], [-6, -5])

    def test_params_and_vars_error_duplicate(self):
        scope = _create_scope(2, 2)
        scope.add_parameter('$x', 2)
        with self.assertRaises(ScopeError):
            scope.add_variable('$x', 2)

    def test_params_and_vars_ok(self):
        scope = _create_scope(2, 2)
        scope.add_parameter('$p', 2)
        scope.add_variable('$v', 2)
        self.assertEqual(scope.get_value('$p').value.offset, 7)
        self.assertEqual(scope.get_value('$v').value.offset, -1)
        with self.assertRaises(ScopeError):
            scope.get_value('$x')


def _create_scope(bc_params, bc_vars):
    return Scope([
        Token(TokenType.BYTE_LITERAL, bc_params, None),
        Token(TokenType.BYTE_LITERAL, bc_vars, None),
    ])

def _get_param_bytes(param_sizes):
    scope = _create_scope(sum(param_sizes), 0)
    for param_idx, param_size in enumerate(param_sizes):
        param_name = '$p{}'.format(param_idx + 1)
        scope.add_parameter(param_name, param_size)
    param_bytes = []
    for param_idx, param_size in enumerate(param_sizes):
        param_name = '$p{}'.format(param_idx + 1)
        param_bytes.append([
            scope.get_value(param_name).value.offset,
            scope.get_value(param_name).value.offset + param_size - 1,
        ])
    return param_bytes

def _get_var_bytes(var_sizes):
    scope = _create_scope(0, sum(var_sizes))
    for param_idx, var_size in enumerate(var_sizes):
        var_name = '$v{}'.format(param_idx + 1)
        scope.add_variable(var_name, var_size)
    var_bytes = []
    for param_idx, var_size in enumerate(var_sizes):
        var_name = '$v{}'.format(param_idx + 1)
        var_bytes.append([
            scope.get_value(var_name).value.offset,
            scope.get_value(var_name).value.offset + var_size - 1,
        ])
    return var_bytes
