import re
from enum import Enum
from typing import TypeVar, List


class TokenType(Enum):
    EOF = 0
    INT = 1
    FLOAT = 2
    OPERATOR = 3
    NAME = 4
    KEYWORD = 5
    STRING = 6
    COMMA = 7
    SEMICOLON = 8
    DOT = 9
    GROUP = 10
    RANGE = 11
    ELLIPSIS = 12
    COLON = 13
    QUESTION = 14


TokenValue = TypeVar("TokenValue", int, float, str)


class Token:
    def __init__(self, type: TokenType, value: TokenValue) -> None:
        self.type = type
        self.value = value

    def __eq__(self, other):
        return self.type == other.type and self.value == other.value

    def __repr__(self) -> str:
        return f"Token({str(self.type)}, {str(self.value)})"


int_regex = re.compile(r"^(\+|-)?[0-9]+")
float_regex = re.compile(r"^(\+|-)?[0-9]*\.[0-9]+")
name_regex = re.compile(r"^[\#A-Za-z_][A-Za-z_0-9]*")


class Tokenizer:

    operator_chars = [
        '+',
        '-',
        '*',
        '/',
        '^',
        '%',
        '<',
        '>',
        '=',
        '!'
    ]

    special_chars = {
        ',': TokenType.COMMA,
        ';': TokenType.SEMICOLON,
        '.': TokenType.DOT,
        ':': TokenType.COLON,
        '?': TokenType.QUESTION
    }

    keywords = [
        "for",
        "in",
        "if",
        "else",
        "return",
        "while",
        "function",
        "class",
        "extends",
        "new",
        "null",
        "break",
        "continue"
    ]

    named_operators = [
        "and",
        "or",
        "not",
        "xor"
    ]

    group_chars = [
        '(', ')',
        '[', ']',
        '{', '}'
    ]

    escape_chars = {
        '\\': '\\',
        '\'': '\'',
        '\"': '\"',
        'a': '\a',
        'b': '\b',
        'f': '\f',
        'n': '\n',
        'r': '\r',
        't': '\t',
        'v': '\v'
    }

    def __init__(self, input: str) -> None:
        self.text = input + '\0'
        self.pos = 0

    @property
    def char(self) -> str:
        return self.text[self.pos]

    @property
    def next_char(self) -> str:
        return self.text[self.pos + 1]

    def advance(self, amount: int = 1) -> None:
        self.pos += amount

    def skip_whitespace(self) -> None:
        while self.char != '\0' and self.char.isspace():
            self.advance()

    def get_string(self) -> str:
        result = ""
        self.advance()

        while self.char != '\"':
            if self.char == '\\':
                self.advance()
                result += Tokenizer.escape_chars[self.char]
            else:
                result += self.char
            self.advance()
        self.advance()

        return result

    def get_next_token(self) -> Token:
        while self.char != '\0':

            if self.char.isspace():
                self.skip_whitespace()
                continue

            if self.char == '"':
                return Token(TokenType.STRING, self.get_string())

            match = float_regex.match(self.text[self.pos:])
            if match is not None:
                start, end = match.span()
                assert(start == 0)
                result = Token(TokenType.FLOAT,
                               float(self.text[self.pos: self.pos + end]))
                self.advance(end)
                return result

            match = int_regex.match(self.text[self.pos:])
            if match is not None:
                start, end = match.span()
                result = Token(TokenType.INT,
                               int(self.text[self.pos:self.pos + end]))
                self.advance(end)
                return result

            match = name_regex.match(self.text[self.pos:])
            if match is not None:
                start, end = match.span()
                result = Token(TokenType.NAME,
                               self.text[self.pos:self.pos + end])
                if result.value in Tokenizer.keywords:
                    result.type = TokenType.KEYWORD
                elif result.value in Tokenizer.named_operators:
                    result.type = TokenType.OPERATOR
                self.advance(end)
                return result

            if self.char == self.next_char == self.text[self.pos + 2] == '.':
                self.advance(3)
                return Token(TokenType.ELLIPSIS)

            if self.char == self.next_char == '.':
                self.advance(2)
                return Token(TokenType.OPERATOR, '..')

            if self.char in Tokenizer.operator_chars:
                result = Token(TokenType.OPERATOR, self.char)
                if(self.char in ('<', '>', '!', '=', '+', '-', '*', '/', '%') and self.next_char == '=' or
                   self.char in ('+',) and self.next_char == self.char):
                    result.value += self.next_char
                    self.advance()
                self.advance()
                return result

            if self.char in Tokenizer.group_chars:
                result = Token(TokenType.GROUP, self.char)
                self.advance()
                return result

            if self.char in Tokenizer.special_chars.keys():
                result = Token(Tokenizer.special_chars[self.char], self.char)
                self.advance()
                return result

            raise SyntaxError(f"Unrecognized character: '{self.char}'")

        return Token(TokenType.EOF, '\0')

    def get_token_list(self) -> List[str]:
        result = []
        t = self.get_next_token()
        while t.type != TokenType.EOF:
            result.append(t)
            t = self.get_next_token()

        return result
