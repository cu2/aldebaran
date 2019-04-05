import ast
import re
from collections import namedtuple


Token = namedtuple('Token', ['type', 'value'])
TokenType = namedtuple('TokenType', ['name', 'regex', 'value'])
Reference = namedtuple('Reference', ['base', 'offset', 'length'])


class TokenizerError(Exception):
    pass


class UnexpectedCharacterError(TokenizerError):
    pass


class InvalidStringLiteralError(TokenizerError):
    pass


class UnknownTokenError(TokenizerError):
    pass


class UnknownReferenceType(TokenizerError):
    pass


class Tokenizer:
    '''
    Based on: https://docs.python.org/3/library/re.html#writing-a-tokenizer
    '''

    def __init__(self, keywords):
        self.instruction_names = set(keywords['instruction_names'])
        self.macro_names = set(keywords['macro_names'])
        self.word_registers = set(keywords['word_registers'])
        self.byte_registers = set(keywords['byte_registers'])
        self.token_types = self._get_token_types()
        self.token_type_dict = {
            token_type.name: token_type
            for token_type in self.token_types
        }
        self.tokenizer_regex = re.compile(r'|'.join(r'(?P<{}>{})'.format(token_type.name, token_type.regex) for token_type in self.token_types))

    def _raise_error(self, code, pos, error_message, exception):
        # TODO: log instead of print
        print('ERROR:', error_message)
        print(code)
        print(' ' * pos + '^')
        raise exception(error_message)

    def _get_raw_token_value(self, code, m):
        return m.group()

    def _get_original_token_value(self, code, m):
        return code[m.start():m.end()]

    def _get_subgroup_value(self, code, m, subgroup):
        return code[m.start(subgroup):m.end(subgroup)]

    def _get_string_literal_value(self, code, m):
        raw_value = code[m.start():m.end()]
        try:
            value = ast.literal_eval(raw_value)
        except Exception:
            self._raise_error(
                code, m.start(),
                'Invalid string literal: {}'.format(raw_value),
                InvalidStringLiteralError,
            )
        return value

    def _get_hex_literal_value(self, code, m):
        return int(m.group(), 16)

    def _get_address_hex_literal_value(self, code, m):
        return int(m.group()[1:], 16)

    def _get_ref_value(self, code, m, ref_type):
        base = m.group('base_{}'.format(ref_type))
        try:
            offset = m.group('offset_{}'.format(ref_type))
        except Exception:
            offset = None
        length = 'B' if m.group('length_{}'.format(ref_type)) == 'B' else 'W'
        if ref_type == 'abs_reg':
            if offset is not None:
                offset=int(offset, 16)
        elif ref_type == 'word_reg':
            base=int(base, 16)
        elif ref_type == 'word_byte':
            base=int(base, 16)
            offset=int(offset, 16)
        elif ref_type == 'word':
            base=int(base, 16)
        else:
            self._raise_error(
                code, m.start(),
                'Unknown reference type: {}'.format(ref_type),
                UnknownReferenceType,
            )
        return Reference(base, offset, length)

    def _get_token_types(self):
        basic_patterns = {
            'word_literal': r'[\da-fA-F]{4}',
            'byte_literal': r'[\da-fA-F]{2}',
            'word_reg': r'({})'.format(r'|'.join(self.word_registers)),
            'byte_reg': r'({})'.format(r'|'.join(self.byte_registers)),
        }
        token_types = [
            TokenType(
                'LABEL',
                r'(?P<label_value>[A-Za-z][a-zA-Z0-9_\-]*):',
                lambda code, m: self._get_subgroup_value(code, m, 'label_value'),
            ),
            TokenType(
                'STRING_LITERAL',
                r'''("(?:[^\"]|\.)*"|'(?:[^\']|\.)*')''',  # TODO: make it match '\''
                self._get_string_literal_value,
            ),
            TokenType(
                'COMMENT',
                r'\#(?P<comment_value>.*)',
                lambda code, m: self._get_subgroup_value(code, m, 'comment_value'),
            ),
            TokenType(
                'INSTRUCTION',
                r'({})'.format(r'|'.join(self.instruction_names)),
                self._get_raw_token_value,
            ),
            TokenType(
                'MACRO',
                r'({})'.format(r'|'.join(self.macro_names)),
                self._get_raw_token_value,
            ),
            TokenType(
                'WORD_REGISTER',
                basic_patterns['word_reg'],
                self._get_raw_token_value,
            ),
            TokenType(
                'BYTE_REGISTER',
                basic_patterns['byte_reg'],
                self._get_raw_token_value,
            ),
            TokenType(
                'ADDRESS_WORD_LITERAL',
                r'\^{}'.format(basic_patterns['word_literal']),
                self._get_address_hex_literal_value,
            ),
            TokenType(
                'WORD_LITERAL',
                basic_patterns['word_literal'],
                self._get_hex_literal_value,
            ),
            TokenType(
                'BYTE_LITERAL',
                basic_patterns['byte_literal'],
                self._get_hex_literal_value,
            ),
            TokenType(
                'ABS_REF_REG',
                r'\[(?P<base_abs_reg>{})(\+(?P<offset_abs_reg>{}))?\](?P<length_abs_reg>B?)'.format(basic_patterns['word_reg'], basic_patterns['byte_literal']),
                lambda code, m: self._get_ref_value(code, m, 'abs_reg'),
            ),
            TokenType(
                'REL_REF_WORD_REG',
                r'\[(?P<base_word_reg>{})\+(?P<offset_word_reg>{})\](?P<length_word_reg>B?)'.format(basic_patterns['word_literal'], basic_patterns['word_reg']),
                lambda code, m: self._get_ref_value(code, m, 'word_reg'),
            ),
            TokenType(
                'REL_REF_WORD_BYTE',
                r'\[(?P<base_word_byte>{})\+(?P<offset_word_byte>{})\](?P<length_word_byte>B?)'.format(basic_patterns['word_literal'], basic_patterns['byte_literal']),
                lambda code, m: self._get_ref_value(code, m, 'word_byte'),
            ),
            TokenType(
                'REL_REF_WORD',
                r'\[(?P<base_word>{})\](?P<length_word>B?)'.format(basic_patterns['word_literal']),
                lambda code, m: self._get_ref_value(code, m, 'word'),
            ),
            TokenType(
                'IDENTIFIER',
                r'[A-Za-z][A-Za-z0-9_\-]*',
                self._get_original_token_value,
            ),
            TokenType(
                'WHITESPACE',
                r'\s+',
                lambda code, m: None,
            ),
            TokenType(
                'UNEXPECTED',
                r'.',
                lambda code, m: None,
            ),
        ]
        return token_types

    def tokenize(self, code):
        tokens = []
        for m in self.tokenizer_regex.finditer(code.upper()):
            token_type_name = m.lastgroup
            if token_type_name == 'UNEXPECTED':
                self._raise_error(
                    code, m.start(),
                    'Unexpected character "{}"'.format(m.group()),
                    UnexpectedCharacterError,
                )
            if token_type_name == 'WHITESPACE':
                continue
            if token_type_name not in self.token_type_dict:
                self._raise_error(
                    code, m.start(),
                    'Unknown token: {}'.format(token_type_name),
                    UnknownTokenError,
                )
            token_type = self.token_type_dict[token_type_name]
            token_value = token_type.value(code, m)
            tokens.append(Token(token_type_name, token_value))
        return tokens
