'''
Token related stuff, like Token, TokenType, Tokenizer
'''

import ast
import re
from collections import namedtuple
from enum import Enum


Token = namedtuple('Token', [
    'type',  # TokenType
    'value',  # int, string, Reference
    'pos',  # int
])


Reference = namedtuple('Reference', [
    'base',  # register, label, int
    'offset',  # register, byte, signed byte
    'length',  # 'B' | 'W'
])


TokenType = Enum('TokenType', [  # pylint: disable=C0103
    'LABEL',
    'STRING_LITERAL',
    'COMMENT',
    'INSTRUCTION',
    'MACRO',
    'WORD_REGISTER',
    'BYTE_REGISTER',
    'ADDRESS_WORD_LITERAL',
    'ADDRESS_LABEL',
    'WORD_LITERAL',
    'BYTE_LITERAL',
    'ABS_REF_REG',
    'REL_REF_WORD_REG',
    'REL_REF_LABEL_REG',
    'REL_REF_WORD_BYTE',
    'REL_REF_LABEL_BYTE',
    'REL_REF_WORD',
    'REL_REF_LABEL',
    'IDENTIFIER',
    'WHITESPACE',
    'UNEXPECTED',
])


ARGUMENT_TYPES = {
    TokenType.STRING_LITERAL,
    TokenType.WORD_REGISTER,
    TokenType.BYTE_REGISTER,
    TokenType.ADDRESS_WORD_LITERAL,
    TokenType.ADDRESS_LABEL,
    TokenType.WORD_LITERAL,
    TokenType.BYTE_LITERAL,
    TokenType.ABS_REF_REG,
    TokenType.REL_REF_WORD_REG,
    TokenType.REL_REF_LABEL_REG,
    TokenType.REL_REF_WORD_BYTE,
    TokenType.REL_REF_LABEL_BYTE,
    TokenType.REL_REF_WORD,
    TokenType.REL_REF_LABEL,
    TokenType.IDENTIFIER,
}


LABEL_REFERENCE_TYPES = {
    TokenType.ADDRESS_LABEL,
    TokenType.IDENTIFIER,
    TokenType.REL_REF_LABEL_REG,
    TokenType.REL_REF_LABEL_BYTE,
    TokenType.REL_REF_LABEL,
}


class Tokenizer:
    '''
    Tokenizer based on: https://docs.python.org/3/library/re.html#writing-a-tokenizer
    '''

    def __init__(self, keywords):
        self.keywords = keywords
        self.token_rules = self._get_token_rules()
        self.tokenizer_regex = re.compile(r'|'.join(
            r'(?P<{}>{})'.format(token_rule.case, token_rule.regex)
            for token_rule in self.token_rules
        ))

    def tokenize(self, code):
        '''
        Tokenize a single line of assembly code
        '''
        tokens = []
        for match in self.tokenizer_regex.finditer(code.upper()):
            case_name = match.lastgroup
            case_handler = CaseHandler(code, match, self.keywords, self._raise_error)
            token = case_handler.handle_case(case_name)
            if token is None:
                continue
            tokens.append(token)
        return tokens

    def _get_token_rules(self):
        # NOTE: code.upper() is matched against these regex patterns
        basic_patterns = {
            'identifier': r'[A-Z_][A-Z0-9_]*',
            'word_literal': r'0X[\dA-F]{4}',
            'byte_literal': r'0X[\dA-F]{2}',
            'word_reg': r'({})'.format(r'|'.join(self.keywords['word_registers'])),
            'byte_reg': r'({})'.format(r'|'.join(self.keywords['byte_registers'])),
        }
        token_rules = [
            Rule(
                r'(?P<label_value>{}):'.format(basic_patterns['identifier']),
                'label'
            ),
            Rule(
                r'''("(?:[^\"]|\.)*"|'(?:[^\']|\.)*')''',  # TODO: make it match '\''
                'string_literal'
            ),
            Rule(
                r'\#(?P<comment_value>.*)',
                'comment'
            ),
            Rule(
                r'\.{}'.format(basic_patterns['identifier']),
                'macro'
            ),
            Rule(
                r'\^{}'.format(basic_patterns['word_literal']),
                'address_word_literal'
            ),
            Rule(
                r'\^(?P<address_label_value>{})'.format(basic_patterns['identifier']),
                'address_label'
            ),
            Rule(
                basic_patterns['word_literal'],
                'word_literal'
            ),
            Rule(
                basic_patterns['byte_literal'],
                'byte_literal'
            ),
            Rule(
                r'\[(?P<base_abs_reg>{})((?P<offset_sign_abs_reg>[+-])(?P<offset_abs_reg>{}))?\](?P<length_abs_reg>B?)'.format(
                    basic_patterns['word_reg'], basic_patterns['byte_literal']
                ),
                'ref__abs_reg'
            ),
            Rule(
                r'\[(?P<base_word_reg>{})\+(?P<offset_word_reg>{})\](?P<length_word_reg>B?)'.format(
                    basic_patterns['word_literal'], basic_patterns['word_reg']
                ),
                'ref__word_reg'
            ),
            Rule(
                r'\[(?P<base_label_reg>{})\+(?P<offset_label_reg>{})\](?P<length_label_reg>B?)'.format(
                    basic_patterns['identifier'], basic_patterns['word_reg']
                ),
                'ref__label_reg'
            ),
            Rule(
                r'\[(?P<base_word_byte>{})\+(?P<offset_word_byte>{})\](?P<length_word_byte>B?)'.format(
                    basic_patterns['word_literal'], basic_patterns['byte_literal']
                ),
                'ref__word_byte'
            ),
            Rule(
                r'\[(?P<base_label_byte>{})\+(?P<offset_label_byte>{})\](?P<length_label_byte>B?)'.format(
                    basic_patterns['identifier'], basic_patterns['byte_literal']
                ),
                'ref__label_byte'
            ),
            Rule(
                r'\[(?P<base_word>{})\](?P<length_word>B?)'.format(basic_patterns['word_literal']),
                'ref__word'
            ),
            Rule(
                r'\[(?P<base_label>{})\](?P<length_label>B?)'.format(basic_patterns['identifier']),
                'ref__label'
            ),
            Rule(
                basic_patterns['identifier'],
                'identifier'
            ),
            Rule(
                r'\s+',
                'whitespace'
            ),
            Rule(
                r'.',
                'unexpected'
            ),
        ]
        return token_rules

    def _log_error(self, code, pos, error_message):
        # TODO: log instead of print
        print('ERROR:', error_message)
        print(code)
        print(' ' * pos + '^')

    def _raise_error(self, code, pos, error_message, exception):
        self._log_error(code, pos, error_message)
        raise exception(error_message)


Rule = namedtuple('Rule', [
    'regex',  # raw string (regex)
    'case',  # string (casename or casename__subcasename of CaseHandler)
])


class CaseHandler:
    '''
    Handle cases of the tokenizer regex
    '''

    def __init__(self, code, match, keywords, _raise_error):
        self.code = code
        self.match = match
        self.raw_value = match.group()
        self.original_value = code[match.start():match.end()]
        self.instruction_names = set(keywords['instruction_names'])
        self.macro_names = set(keywords['macro_names'])
        self.word_registers = set(keywords['word_registers'])
        self.byte_registers = set(keywords['byte_registers'])
        self.tokenizer_raise_error = _raise_error

    def handle_case(self, case_name):
        '''
        Return token for a given case
        '''
        if '__' in case_name:
            case_name, subcase_name = case_name.split('__', 1)
            case = getattr(self, '_case_{}'.format(case_name))(subcase_name)
        else:
            case = getattr(self, '_case_{}'.format(case_name))()
        if case is None:
            return None
        return Token(
            case.token_type,
            case.value,
            self.match.start(),
        )

    def _case_label(self):
        return Case(
            TokenType.LABEL,
            self._get_subgroup_value('label_value'),
        )

    def _case_string_literal(self):
        return Case(
            TokenType.STRING_LITERAL,
            self._get_string_literal_value(),
        )

    def _case_comment(self):
        return Case(
            TokenType.COMMENT,
            self._get_subgroup_value('comment_value'),
        )

    def _case_macro(self):
        macro_name = self.raw_value[1:]
        if macro_name not in self.macro_names:
            self._raise_error(
                'Unknown macro: {}'.format(macro_name),
                UnknownMacroError,
            )
        return Case(
            TokenType.MACRO,
            macro_name,
        )

    def _case_address_word_literal(self):
        return Case(
            TokenType.ADDRESS_WORD_LITERAL,
            self._get_address_hex_literal_value(),
        )

    def _case_address_label(self):
        return Case(
            TokenType.ADDRESS_LABEL,
            self._get_subgroup_value('address_label_value'),
        )

    def _case_word_literal(self):
        return Case(
            TokenType.WORD_LITERAL,
            self._get_hex_literal_value(),
        )

    def _case_byte_literal(self):
        return Case(
            TokenType.BYTE_LITERAL,
            self._get_hex_literal_value(),
        )

    def _case_ref(self, subcase_name):
        token_type = {
            'abs_reg': TokenType.ABS_REF_REG,
            'word_reg': TokenType.REL_REF_WORD_REG,
            'label_reg': TokenType.REL_REF_LABEL_REG,
            'word_byte': TokenType.REL_REF_WORD_BYTE,
            'label_byte': TokenType.REL_REF_LABEL_BYTE,
            'word': TokenType.REL_REF_WORD,
            'label': TokenType.REL_REF_LABEL,
        }[subcase_name]
        return Case(
            token_type,
            self._get_ref_value(subcase_name),
        )

    def _case_identifier(self):
        if self.raw_value in self.instruction_names:
            token_type = TokenType.INSTRUCTION
        elif self.raw_value in self.word_registers:
            token_type = TokenType.WORD_REGISTER
        elif self.raw_value in self.byte_registers:
            token_type = TokenType.BYTE_REGISTER
        else:
            token_type = TokenType.IDENTIFIER
        if token_type == TokenType.IDENTIFIER:
            token_value = self.original_value
        else:
            token_value = self.raw_value
        return Case(
            token_type,
            token_value,
        )

    def _case_whitespace(self):
        return None

    def _case_unexpected(self):
        self._raise_error(
            'Unexpected character "{}"'.format(self.original_value),
            UnexpectedCharacterError,
        )

    def _get_subgroup_value(self, subgroup):
        return self.code[self.match.start(subgroup):self.match.end(subgroup)]

    def _get_string_literal_value(self):
        try:
            value = ast.literal_eval(self.original_value)
        except Exception:
            self._raise_error(
                'Invalid string literal: {}'.format(self.original_value),
                InvalidStringLiteralError,
            )
        return value

    def _get_address_hex_literal_value(self):
        return int(self.raw_value[1:], 16)

    def _get_hex_literal_value(self):
        return int(self.raw_value, 16)

    def _get_ref_value(self, ref_type):
        base_subgroup_name = 'base_{}'.format(ref_type)
        base = self.match.group(base_subgroup_name)
        try:
            offset = self.match.group('offset_{}'.format(ref_type))
        except Exception:
            offset = None
        try:
            offset_sign = self.match.group('offset_sign_{}'.format(ref_type))
        except Exception:
            offset_sign = None
        length = 'B' if self.match.group('length_{}'.format(ref_type)) == 'B' else 'W'
        if ref_type == 'abs_reg':
            if offset is None:
                offset = 0
            else:
                if offset_sign == '+':
                    offset = int(offset, 16)
                else:
                    offset = -int(offset, 16)
        elif ref_type == 'word_reg':
            base = int(base, 16)
        elif ref_type == 'word_byte':
            base = int(base, 16)
            offset = int(offset, 16)
        elif ref_type == 'word':
            base = int(base, 16)
        elif ref_type == 'label_reg':
            base = self._get_subgroup_value(base_subgroup_name)
        elif ref_type == 'label_byte':
            base = self._get_subgroup_value(base_subgroup_name)
            offset = int(offset, 16)
        elif ref_type == 'label':
            base = self._get_subgroup_value(base_subgroup_name)
        else:
            self._raise_error(
                'Unknown reference type: {}'.format(ref_type),
                UnknownReferenceTypeError,
            )
        return Reference(base, offset, length)

    def _raise_error(self, error_message, exception):
        return self.tokenizer_raise_error(
            self.code,
            self.match.start(),
            error_message,
            exception,
        )



Case = namedtuple('Case', [
    'token_type',  # TokenType
    'value',  # same as Token.value
])


class TokenizerError(Exception):
    pass


class UnexpectedCharacterError(TokenizerError):
    pass


class InvalidStringLiteralError(TokenizerError):
    pass


class UnknownTokenError(TokenizerError):
    pass


class UnknownReferenceTypeError(TokenizerError):
    pass


class UnknownMacroError(TokenizerError):
    pass
