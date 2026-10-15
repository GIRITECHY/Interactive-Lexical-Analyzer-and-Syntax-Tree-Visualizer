"""
tests/test_lexer.py - Unit Tests for LexiTree Lexical Analyzer

Tests token recognition, line & column tracking, whitespace handling,
numeric literal formats (integers, floats, malformed numbers),
and invalid character detection.
"""

import unittest
from lexer import (
    Lexer,
    TOKEN_IDENTIFIER,
    TOKEN_NUMBER,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_STAR,
    TOKEN_SLASH,
    TOKEN_ASSIGN,
    TOKEN_LPAREN,
    TOKEN_RPAREN,
    TOKEN_SEMICOLON,
    TOKEN_EOF
)


class TestLexer(unittest.TestCase):
    """Test suite for Lexer tokenization and error handling."""

    def test_single_tokens(self):
        source = "+ - * / = ( ) ;"
        lexer = Lexer(source)
        tokens, errors = lexer.tokenize()

        self.assertEqual(len(errors), 0)
        types = [t.type for t in tokens]
        expected = [
            TOKEN_PLUS, TOKEN_MINUS, TOKEN_STAR, TOKEN_SLASH,
            TOKEN_ASSIGN, TOKEN_LPAREN, TOKEN_RPAREN, TOKEN_SEMICOLON,
            TOKEN_EOF
        ]
        self.assertEqual(types, expected)

    def test_identifiers_and_numbers(self):
        source = "count = 42; rate = 3.1415;"
        lexer = Lexer(source)
        tokens, errors = lexer.tokenize()

        self.assertEqual(len(errors), 0)
        self.assertEqual(tokens[0].type, TOKEN_IDENTIFIER)
        self.assertEqual(tokens[0].lexeme, "count")
        self.assertEqual(tokens[1].type, TOKEN_ASSIGN)
        self.assertEqual(tokens[2].type, TOKEN_NUMBER)
        self.assertEqual(tokens[2].value, 42)
        self.assertEqual(tokens[3].type, TOKEN_SEMICOLON)

        self.assertEqual(tokens[4].type, TOKEN_IDENTIFIER)
        self.assertEqual(tokens[4].lexeme, "rate")
        self.assertEqual(tokens[5].type, TOKEN_ASSIGN)
        self.assertEqual(tokens[6].type, TOKEN_NUMBER)
        self.assertAlmostEqual(tokens[6].value, 3.1415)
        self.assertEqual(tokens[7].type, TOKEN_SEMICOLON)

    def test_line_and_column_tracking(self):
        source = "a = 1;\n\nb = 2;"
        lexer = Lexer(source)
        tokens, errors = lexer.tokenize()

        self.assertEqual(len(errors), 0)
        # 'a' is at line 1, col 1
        self.assertEqual((tokens[0].line, tokens[0].column), (1, 1))
        # '=' is at line 1, col 3
        self.assertEqual((tokens[1].line, tokens[1].column), (1, 3))
        # 'b' is at line 3, col 1
        self.assertEqual((tokens[4].line, tokens[4].column), (3, 1))
        # '2' is at line 3, col 5
        self.assertEqual((tokens[6].line, tokens[6].column), (3, 5))

    def test_invalid_character_detection(self):
        source = "x = 10 @ 2;"
        lexer = Lexer(source)
        tokens, errors = lexer.tokenize()

        self.assertEqual(len(errors), 1)
        self.assertIn("@", errors[0].message)
        self.assertEqual(errors[0].line, 1)
        self.assertEqual(errors[0].column, 8)

        # Ensure valid tokens around '@' were still recognized
        lexemes = [t.lexeme for t in tokens if t.type != TOKEN_EOF]
        self.assertEqual(lexemes, ["x", "=", "10", "2", ";"])

    def test_malformed_numeric_literal_multiple_dots(self):
        source = "val = 12.34.56;"
        lexer = Lexer(source)
        tokens, errors = lexer.tokenize()

        self.assertEqual(len(errors), 1)
        self.assertIn("multiple decimal points", errors[0].message)

    def test_malformed_numeric_literal_trailing_dot(self):
        source = "val = 12.;"
        lexer = Lexer(source)
        tokens, errors = lexer.tokenize()

        self.assertEqual(len(errors), 1)
        self.assertIn("expected digit after decimal point", errors[0].message)

    def test_invalid_identifier_starting_with_digit(self):
        source = "val = 10abc;"
        lexer = Lexer(source)
        tokens, errors = lexer.tokenize()

        self.assertEqual(len(errors), 1)
        self.assertIn("identifiers cannot begin with numbers", errors[0].message)


if __name__ == "__main__":
    unittest.main()
