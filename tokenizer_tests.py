import unittest
import tokenizer
from tokenizer import TokenType, Token


class TokenizerTests(unittest.TestCase):
    def test_assign(self):
        T = tokenizer.Tokenizer("A = B + 10 - C;")
        tokens = [
            Token(TokenType.NAME, "A"),
            Token(TokenType.OPERATOR, "="),
            Token(TokenType.NAME, "B"),
            Token(TokenType.OPERATOR, "+"),
            Token(TokenType.INT, 10),
            Token(TokenType.OPERATOR, "-"),
            Token(TokenType.NAME, "C"),
            Token(TokenType.SEMICOLON, ";")
        ]
        self.assertEqual(T.get_token_list(), tokens)

    def test_for(self):
        T = tokenizer.Tokenizer("for(x in array) { print(x); }")
        tokens = [
            Token(TokenType.KEYWORD, "for"),
            Token(TokenType.GROUP, "("),
            Token(TokenType.NAME, "x"),
            Token(TokenType.KEYWORD, "in"),
            Token(TokenType.NAME, "array"),
            Token(TokenType.GROUP, ")"),
            Token(TokenType.GROUP, "{"),
            Token(TokenType.NAME, "print"),
            Token(TokenType.GROUP, "("),
            Token(TokenType.NAME, "x"),
            Token(TokenType.GROUP, ")"),
            Token(TokenType.SEMICOLON, ";"),
            Token(TokenType.GROUP, "}")
        ]
        self.assertEqual(T.get_token_list(), tokens)

    def test_object(self):
        T = tokenizer.Tokenizer("array[10 * x].value = 2.5")
        tokens = [
            Token(TokenType.NAME, "array"),
            Token(TokenType.GROUP, "["),
            Token(TokenType.INT, 10),
            Token(TokenType.OPERATOR, "*"),
            Token(TokenType.NAME, "x"),
            Token(TokenType.GROUP, "]"),
            Token(TokenType.DOT, "."),
            Token(TokenType.NAME, "value"),
            Token(TokenType.OPERATOR, "="),
            Token(TokenType.FLOAT, 2.5)
        ]
        self.assertEqual(T.get_token_list(), tokens)

    def test_string(self):
        T = tokenizer.Tokenizer("print(\"Hello, World!\\n\")")
        tokens = [
            Token(TokenType.NAME, "print"),
            Token(TokenType.GROUP, "("),
            Token(TokenType.STRING, "Hello, World!\n"),
            Token(TokenType.GROUP, ")"),
        ]
        self.assertEqual(T.get_token_list(), tokens)


if __name__ == "__main__":
    unittest.main()
