'''
Generate docs for instruction set
'''

import html
import textwrap

from instructions.instruction_set import INSTRUCTION_SET, INSTRUCTION_GROUPS


def main():
    '''
    Entry point of script
    '''
    groups = {}
    for opcode, inst in INSTRUCTION_SET:
        module_name = inst.__module__
        group_name = module_name.split('.')[-1]
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append((opcode, inst))
    print('# Instruction set')
    print()
    print('NOTE 1: this documentation is far from finished.')
    print()
    print('NOTE 2: the instruction set is even further.')
    for group_name, group_full_name in INSTRUCTION_GROUPS:
        print()
        print()
        print('## {}'.format(group_full_name))
        for opcode, inst in groups[group_name]:
            operands = ['`<op{}>`'.format(opidx) for opidx in range(inst.operand_count)]
            title = ' '.join([inst.__name__] + operands)
            print()
            print('### {}'.format(title))
            print(html.escape(textwrap.dedent(inst.__doc__)))


if __name__ == '__main__':
    main()
