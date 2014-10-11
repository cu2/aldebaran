import sys

import aux
import instructions


class UnknownInstructionError(Exception):
    pass


class Assembler(aux.Hardware):

    def __init__(self, log=None):
        aux.Hardware.__init__(self, log)

    def load(self, starting_ip, filename):
        labels = {}
        program = []
        with open(filename, 'r') as f:
            # 1. collect labels
            for line in f.read().split('\n'):
                line = line.strip()
                if '#' in line:
                    line = line[:line.index('#')].strip()
                if line == '':
                    continue
                if ':' in line:
                    label, code = line.split(':', 1)
                    label = label.strip().upper()
                    code = code.strip()
                    if label:
                        labels[label] = 0
            # 2. get label addresses
            ip = starting_ip
            f.seek(0)
            for linenum, line in enumerate(f.read().split('\n')):
                line = line.strip()
                if '#' in line:
                    line = line[:line.index('#')].strip()
                if line == '':
                    continue
                if ':' in line:
                    label, code = line.split(':', 1)
                    label = label.strip().upper()
                    code = code.strip()
                    if label:
                        labels[label] = ip
                else:
                    code = line
                if code == '':
                    continue
                tokens = code.split()
                instruction_code = tokens[0].upper()
                arguments = tokens[1:]
                if not hasattr(instructions, instruction_code):
                    raise UnknownInstructionError('UNKNOWN INSTRUCTION IN LINE %s: %s %s' % (linenum + 1, instruction_code, arguments))
                instruction = getattr(instructions, instruction_code)
                if not instructions.is_instruction(instruction):
                    raise UnknownInstructionError('UNKNOWN INSTRUCTION IN LINE %s: %s %s' % (linenum + 1, instruction_code, arguments))
                opcodes = instruction.assemble(ip, labels, arguments)
                ip += len(opcodes)
            # 3. fix labels
            ip = starting_ip
            f.seek(0)
            for line in f.read().split('\n'):
                line = line.strip()
                if '#' in line:
                    line = line[:line.index('#')].strip()
                if line == '':
                    continue
                if ':' in line:
                    label, code = line.split(':', 1)
                    label = label.strip().upper()
                    code = code.strip()
                    if label:
                        labels[label] = ip
                else:
                    code = line
                if code == '':
                    continue
                tokens = code.split()
                instruction_code = tokens[0].upper()
                arguments = tokens[1:]
                instruction = getattr(instructions, instruction_code)
                opcodes = instruction.assemble(ip, labels, arguments)
                self.log.log('assembler', '%s: %s %s # %s %s' % (
                    aux.word_to_str(ip),
                    ' '.join([aux.byte_to_str(opcode) for opcode in opcodes]),
                    ' ' * (30 - 3 * len(opcodes)),
                    instruction.__name__,
                    ' '.join(arguments),
                ))
                program += opcodes
                ip += len(opcodes)
        return program


if __name__ == '__main__':
    starting_ip = 0x0400
    filename = 'examples/hello.ald'
    assembler = Assembler(aux.Log())
    try:
        program = assembler.load(starting_ip, filename)
    except UnknownInstructionError as e:
        print e
        program = None
    if program:
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
