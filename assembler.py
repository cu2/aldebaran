#!/usr/bin/env python

import ast
import sys

import aux
import errors
import instructions


class Assembler(aux.Hardware):

    def __init__(self, inst_dict, log=None):
        aux.Hardware.__init__(self, log)
        self.inst_dict = inst_dict
        self.source = ''

    def load_file(self, filename):
        self.log.log('assembler', 'Loading file %s...' % filename)
        self.source = ''
        with open(filename, 'r') as f:
            self.source = f.read()
        self.log.log('assembler', 'Loaded file %s.' % filename)

    def load_string(self, string):
        self.log.log('assembler', 'Loading string...')
        self.source = string
        self.log.log('assembler', 'Loaded string.')

    def get_lines(self):
        for linenum, line in enumerate(self.source.split('\n')):
            line = line.strip()
            if '#' in line:
                line = line[:line.index('#')].strip()
            if line == '':
                continue
            if ':' in line:
                label, code = line.split(':', 1)
                label = label.strip().upper()
                code = code.strip()
            else:
                label, code = None, line
            yield linenum, label, code

    def substitute_labels(self, orig_arguments, labels):  # TODO: don't substitute in string literals
        arguments = []
        sorted_labels = sorted([key for key in labels], key=lambda x: (-len(x), x))  # to avoid substr substitution
        for arg in orig_arguments:
            arg = arg.strip()
            if arg[0] == "'" or arg[0] == '"':
                arguments.append(arg)
                continue
            canonic_arg = arg.upper()
            for label_name in sorted_labels:
                if label_name in canonic_arg:
                    canonic_arg = canonic_arg.replace(label_name, labels[label_name])
            arguments.append(canonic_arg)
        return arguments

    def tokenize(self, code):  # TODO: don't break on spaces in string literals
        return code.split()

    def assemble(self, starting_ip):
        # TODO: refactor to less copy paste
        # TODO: add macros: CONST
        self.log.log('assembler', 'Assembling...')
        labels = {}
        program = []

        self.log.log('assembler', 'Collecting labels...')
        for linenum, label, code in self.get_lines():
            if label:
                labels[label] = '0000'

        self.log.log('assembler', 'Getting label addresses...')
        ip = starting_ip
        for linenum, label, code in self.get_lines():
            if label:
                labels[label] = aux.word_to_str(ip)
            if code == '':
                continue
            self.log.log('assembler', code)
            tokens = self.tokenize(code)
            instruction_name = tokens[0].upper()
            arguments = self.substitute_labels(tokens[1:], labels)
            if instruction_name in ['DAT', 'DATN']:
                if instruction_name == 'DATN':
                    args = arguments[1:]
                    repeat = aux.str_to_int(arguments[0])
                else:
                    args = arguments
                    repeat = 1
                if repeat < 0 or repeat > 255:
                    raise errors.ByteOutOfRangeError(hex(repeat))
                for _ in xrange(repeat):
                    for arg in args:
                        if arg[0] == "'" or arg[0] == '"':
                            real_arg = ast.literal_eval(arg)
                            ip += len(real_arg)
                        elif len(arg) == 2:
                            ip += 1
                        else:
                            ip += 2
                continue
            if instruction_name not in self.inst_dict:
                raise errors.UnknownInstructionError('[line %s] %s %s' % (linenum + 1, instruction_name, ' '.join(arguments)))
            instruction_opcode = self.inst_dict[instruction_name]
            operand_count = getattr(instructions, instruction_name).operand_count
            if operand_count != len(arguments):
                raise errors.ArgumentCountError('[line %s] %s %s' % (linenum + 1, instruction_name, ' '.join(arguments)))
            opcodes = [instruction_opcode]
            for arg in arguments:
                opcodes += instructions.encode_argument(arg)  # labels are not okay, but len(opcodes) is
            self.log.log('assembler', '%s: %s %s # %s %s' % (
                aux.word_to_str(ip),
                ' '.join([aux.byte_to_str(opcode) for opcode in opcodes]),
                ' ' * (30 - 3 * len(opcodes)),
                instruction_name,
                ' '.join(arguments),
            ))
            ip += len(opcodes)

        self.log.log('assembler', 'Generating machine code...')
        ip = starting_ip
        for linenum, label, code in self.get_lines():
            if code == '':
                continue
            tokens = self.tokenize(code)
            instruction_name = tokens[0].upper()
            arguments = self.substitute_labels(tokens[1:], labels)
            if instruction_name in ['DAT', 'DATN']:
                if instruction_name == 'DATN':
                    args = arguments[1:]
                    repeat = aux.str_to_int(arguments[0])
                else:
                    args = arguments
                    repeat = 1
                for _ in xrange(repeat):
                    for arg in args:
                        if arg[0] == "'" or arg[0] == '"':
                            real_arg = ast.literal_eval(arg)
                            for char in real_arg:
                                program.append(ord(char))
                            ip += len(real_arg)
                        elif len(arg) == 2:
                            program.append(aux.str_to_int(arg))
                            ip += 1
                        else:
                            program += list(aux.word_to_bytes(aux.str_to_int(arg)))
                            ip += 2
                continue
            instruction_opcode = self.inst_dict[instruction_name]
            opcodes = [instruction_opcode]
            for arg in arguments:
                opcodes += instructions.encode_argument(arg)  # finally even labels are correct
            self.log.log('assembler', '%s: %s %s # %s %s' % (
                aux.word_to_str(ip),
                ' '.join([aux.byte_to_str(opcode) for opcode in opcodes]),
                ' ' * (30 - 3 * len(opcodes)),
                instruction_name,
                ' '.join(arguments),
            ))
            program += opcodes
            ip += len(opcodes)

        self.log.log('assembler', 'Finished assembling.')
        return program


def main(args):
    starting_ip = 0x0000
    if len(args):
        filename = args[0]
    else:
        filename = 'examples/hello.ald'
    inst_list, inst_dict = instructions.get_instruction_set()
    assembler = Assembler(inst_dict, aux.Log())
    assembler.load_file(filename)
    program = assembler.assemble(starting_ip)
    sys.stdout.write('\n')
    sys.stdout.write('     |')
    for idx in xrange(16):
        sys.stdout.write(' %s' % aux.byte_to_str(idx))
    sys.stdout.write('\n')
    sys.stdout.write('-----+')
    for idx in xrange(16):
        sys.stdout.write('---')
    sys.stdout.write('-')
    for idx, opcode in enumerate(program):
        ip = starting_ip + idx
        if ip % 16 == 0:
            sys.stdout.write('\n')
            sys.stdout.write(aux.word_to_str(ip))
            sys.stdout.write(' |')
        sys.stdout.write(' %s' % aux.byte_to_str(opcode))
    sys.stdout.write('\n')


if __name__ == '__main__':
    main(sys.argv[1:])
