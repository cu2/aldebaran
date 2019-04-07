import ast
import re
from collections import namedtuple
from enum import Enum


Token = namedtuple('Token', ['type', 'value', 'pos'])
TokenRule = namedtuple('TokenRule', ['token_type', 'regex', 'value'])
Reference = namedtuple('Reference', ['base', 'offset', 'length'])


TokenType = Enum('TokenType', [
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
        self.token_rules = self._get_token_rules()
        self.token_rule_dict = {
            token_rule.token_type.name: token_rule
            for token_rule in self.token_rules
        }
        self.tokenizer_regex = re.compile(r'|'.join(
            r'(?P<{}>{})'.format(token_rule.token_type.name, token_rule.regex)
            for token_rule in self.token_rules
        ))

    def _log_error(self, code, pos, error_message):
        # TODO: log instead of print
        print('ERROR:', error_message)
        print(code)
        print(' ' * pos + '^')

    def _raise_error(self, code, pos, error_message, exception):
        self._log_error(code, pos, error_message)
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
        base_subgroup_name = 'base_{}'.format(ref_type)
        base = m.group(base_subgroup_name)
        try:
            offset = m.group('offset_{}'.format(ref_type))
        except Exception:
            offset = None
        try:
            offset_sign = m.group('offset_sign_{}'.format(ref_type))
        except Exception:
            offset_sign = None
        length = 'B' if m.group('length_{}'.format(ref_type)) == 'B' else 'W'
        if ref_type == 'abs_reg':
            if offset is not None:
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
            base = self._get_subgroup_value(code, m, base_subgroup_name)
        elif ref_type == 'label_byte':
            base = self._get_subgroup_value(code, m, base_subgroup_name)
            offset = int(offset, 16)
        elif ref_type == 'label':
            base = self._get_subgroup_value(code, m, base_subgroup_name)
        else:
            self._raise_error(
                code, m.start(),
                'Unknown reference type: {}'.format(ref_type),
                UnknownReferenceType,
            )
        return Reference(base, offset, length)

    def _get_token_rules(self):
        basic_patterns = {
            'identifier': r'[A-Za-z][a-zA-Z0-9_]*',
            'word_literal': r'[\da-fA-F]{4}',
            'byte_literal': r'[\da-fA-F]{2}',
            'word_reg': r'({})'.format(r'|'.join(self.word_registers)),
            'byte_reg': r'({})'.format(r'|'.join(self.byte_registers)),
        }
        token_rules = [
            TokenRule(
                TokenType.LABEL,
                r'(?P<label_value>{}):'.format(basic_patterns['identifier']),
                lambda code, m: self._get_subgroup_value(code, m, 'label_value'),
            ),
            TokenRule(
                TokenType.STRING_LITERAL,
                r'''("(?:[^\"]|\.)*"|'(?:[^\']|\.)*')''',  # TODO: make it match '\''
                self._get_string_literal_value,
            ),
            TokenRule(
                TokenType.COMMENT,
                r'\#(?P<comment_value>.*)',
                lambda code, m: self._get_subgroup_value(code, m, 'comment_value'),
            ),
            TokenRule(
                TokenType.INSTRUCTION,
                r'({})'.format(r'|'.join(self.instruction_names)),
                self._get_raw_token_value,
            ),
            TokenRule(
                TokenType.MACRO,
                r'({})'.format(r'|'.join(self.macro_names)),
                self._get_raw_token_value,
            ),
            TokenRule(
                TokenType.WORD_REGISTER,
                basic_patterns['word_reg'],
                self._get_raw_token_value,
            ),
            TokenRule(
                TokenType.BYTE_REGISTER,
                basic_patterns['byte_reg'],
                self._get_raw_token_value,
            ),
            TokenRule(
                TokenType.ADDRESS_WORD_LITERAL,
                r'\^{}'.format(basic_patterns['word_literal']),
                self._get_address_hex_literal_value,
            ),
            TokenRule(
                TokenType.ADDRESS_LABEL,
                r'\^(?P<address_label_value>{})'.format(basic_patterns['identifier']),
                lambda code, m: self._get_subgroup_value(code, m, 'address_label_value'),
            ),
            TokenRule(
                TokenType.WORD_LITERAL,
                basic_patterns['word_literal'],
                self._get_hex_literal_value,
            ),
            TokenRule(
                TokenType.BYTE_LITERAL,
                basic_patterns['byte_literal'],
                self._get_hex_literal_value,
            ),
            TokenRule(
                TokenType.ABS_REF_REG,
                r'\[(?P<base_abs_reg>{})((?P<offset_sign_abs_reg>[+-])(?P<offset_abs_reg>{}))?\](?P<length_abs_reg>B?)'.format(basic_patterns['word_reg'], basic_patterns['byte_literal']),
                lambda code, m: self._get_ref_value(code, m, 'abs_reg'),
            ),
            TokenRule(
                TokenType.REL_REF_WORD_REG,
                r'\[(?P<base_word_reg>{})\+(?P<offset_word_reg>{})\](?P<length_word_reg>B?)'.format(basic_patterns['word_literal'], basic_patterns['word_reg']),
                lambda code, m: self._get_ref_value(code, m, 'word_reg'),
            ),
            TokenRule(
                TokenType.REL_REF_LABEL_REG,
                r'\[(?P<base_label_reg>{})\+(?P<offset_label_reg>{})\](?P<length_label_reg>B?)'.format(basic_patterns['identifier'], basic_patterns['word_reg']),
                lambda code, m: self._get_ref_value(code, m, 'label_reg'),
            ),
            TokenRule(
                TokenType.REL_REF_WORD_BYTE,
                r'\[(?P<base_word_byte>{})\+(?P<offset_word_byte>{})\](?P<length_word_byte>B?)'.format(basic_patterns['word_literal'], basic_patterns['byte_literal']),
                lambda code, m: self._get_ref_value(code, m, 'word_byte'),
            ),
            TokenRule(
                TokenType.REL_REF_LABEL_BYTE,
                r'\[(?P<base_label_byte>{})\+(?P<offset_label_byte>{})\](?P<length_label_byte>B?)'.format(basic_patterns['identifier'], basic_patterns['byte_literal']),
                lambda code, m: self._get_ref_value(code, m, 'label_byte'),
            ),
            TokenRule(
                TokenType.REL_REF_WORD,
                r'\[(?P<base_word>{})\](?P<length_word>B?)'.format(basic_patterns['word_literal']),
                lambda code, m: self._get_ref_value(code, m, 'word'),
            ),
            TokenRule(
                TokenType.REL_REF_LABEL,
                r'\[(?P<base_label>{})\](?P<length_label>B?)'.format(basic_patterns['identifier']),
                lambda code, m: self._get_ref_value(code, m, 'label'),
            ),
            TokenRule(
                TokenType.IDENTIFIER,
                basic_patterns['identifier'],
                self._get_original_token_value,
            ),
            TokenRule(
                TokenType.WHITESPACE,
                r'\s+',
                lambda code, m: None,
            ),
            TokenRule(
                TokenType.UNEXPECTED,
                r'.',
                lambda code, m: None,
            ),
        ]
        return token_rules

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
            if token_type_name not in self.token_rule_dict:
                self._raise_error(
                    code, m.start(),
                    'Unknown token: {}'.format(token_type_name),
                    UnknownTokenError,
                )
            token_rule = self.token_rule_dict[token_type_name]
            token_value = token_rule.value(code, m)
            tokens.append(Token(token_rule.token_type, token_value, m.start()))
        return tokens
