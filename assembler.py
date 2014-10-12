import sys

import aux
import errors
import instructions


class Assembler(aux.Hardware):

    def __init__(self, log=None):
        aux.Hardware.__init__(self, log)
        self.source = ''

    def load_file(self, filename):
        self.source = ''
        with open(filename, 'r') as f:
            self.source = f.read()

    def load_string(self, string):
        self.source = string

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

    def assemble(self, starting_ip):
        self.log.log('assembler', 'Assembling...')
        labels = {}
        program = []

        self.log.log('assembler', 'Collecting labels...')
        for linenum, label, code in self.get_lines():
            if label:
                labels[label] = 0

        self.log.log('assembler', 'Getting label addresses...')
        ip = starting_ip
        for linenum, label, code in self.get_lines():
            if label:
                labels[label] = ip
            if code == '':
                continue
            self.log.log('assembler', code)
            tokens = code.split()
            instruction_code = tokens[0].upper()
            arguments = tokens[1:]
            if not hasattr(instructions, instruction_code):
                raise errors.UnknownInstructionError('[line %s] %s %s' % (linenum + 1, instruction_code, ' '.join(arguments)))
            instruction = getattr(instructions, instruction_code)
            if not instructions.is_instruction(instruction):
                raise errors.UnknownInstructionError('[line %s] %s %s' % (linenum + 1, instruction_code, ' '.join(arguments)))
            opcodes = instruction.assemble(ip, labels, arguments)  # opcode length is correct, labels are not necessarily
            ip += len(opcodes)

        self.log.log('assembler', 'Generating machine code...')
        ip = starting_ip
        for linenum, label, code in self.get_lines():
            if code == '':
                continue
            tokens = code.split()
            instruction_code = tokens[0].upper()
            arguments = tokens[1:]
            instruction = getattr(instructions, instruction_code)
            opcodes = instruction.assemble(ip, labels, arguments)  # finally even labels are correct
            self.log.log('assembler', '%s: %s %s # %s %s' % (
                aux.word_to_str(ip),
                ' '.join([aux.byte_to_str(opcode) for opcode in opcodes]),
                ' ' * (30 - 3 * len(opcodes)),
                instructions.get_instruction_by_opcode(opcodes[0])[0].__name__,
                ' '.join(arguments),
            ))
            program += opcodes
            ip += len(opcodes)

        self.log.log('assembler', 'Finished assembling.')
        return program


if __name__ == '__main__':
    starting_ip = 0x0000
    filename = 'examples/hello.ald'
    assembler = Assembler(aux.Log())
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
