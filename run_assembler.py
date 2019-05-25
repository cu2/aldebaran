'''
Assemble one or more source code files to executable files

Usage: python run_assembler.py <file>+
'''

import argparse
import logging

from assembler.assembler import Assembler
from instructions.instruction_set import INSTRUCTION_SET
from instructions.operands import WORD_REGISTERS, BYTE_REGISTERS
from utils import utils
from utils.errors import AldebaranError


logger = logging.getLogger(__name__)


def main():
    '''
    Entry point of script
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        nargs='+',
        help='ALD source code file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Verbosity'
    )
    args = parser.parse_args()
    _set_logging(args.verbose)
    try:
        assembler = Assembler(
            instruction_set=INSTRUCTION_SET,
            registers={
                'byte': BYTE_REGISTERS,
                'word': WORD_REGISTERS,
            },
        )
        for source_file in args.file:
            assembler.assemble_file(source_file)
    except AldebaranError as ex:
        logger.error(ex)


def _set_logging(verbosity):
    levels = {
        'asm': 'IDD',
        'tok': 'EED',
    }
    if verbosity > 2:
        verbosity = 2
    utils.config_loggers({
        'assembler.assembler': {
            'name': 'Assembler',
            'level': levels['asm'][verbosity],
        },
        'assembler.tokenizer': {
            'name': 'Tokenizer',
            'level': levels['tok'][verbosity],
            'color': '1;30',
        },
    })


if __name__ == '__main__':
    main()
