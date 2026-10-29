"""
tests/test_tac.py - Unit Tests for LexiTree Three-Address Code (TAC) Generator

Tests:
1. Simple assignment (x = 10; -> x = 10).
2. Addition (x = a + b;).
3. Multiplication (x = a * b;).
4. Operator precedence (result = 2 + 3 * 4; -> t1 = 3 * 4, t2 = 2 + t1, result = t2).
5. Parentheses changing evaluation order (result = (2 + 3) * 4; -> t1 = 2 + 3, t2 = t1 * 4, result = t2).
6. Unary minus (x = -5; -> t1 = -5, x = t1; y = -(x + 3); -> t1 = x + 3, t2 = -t1, y = t2).
7. Unary plus (x = +5; safe handling without redundant temporary).
8. Multiple statements (sequential instruction generation).
9. Deterministic temporary variable numbering (t1, t2, t3).
10. Resetting temporary numbering between distinct compile passes.
11. Numeric literal preservation (floats and integers).
12. Invalid syntax prevents code generation (ParserError).
13. Correct instruction order matching evaluation semantics.
14. Correct final assignment to target variable.
"""

import unittest
from lexer import Lexer
from parser import Parser, ParserError
from intermediate_code import TACGenerator


def generate_tac_from_code(code: str):
    lexer = Lexer(code)
    tokens, errors = lexer.tokenize()
    if errors:
        raise ValueError(f"Lexical errors: {errors}")
    parser = Parser(tokens)
    ast = parser.parse()
    gen = TACGenerator()
    return gen.generate(ast)


class TestTACGenerator(unittest.TestCase):
    """Test suite for Three-Address Code (TAC) generation."""

    def test_simple_assignment(self):
        tac = generate_tac_from_code("x = 10;")
        self.assertEqual(tac, ["x = 10"])

    def test_simple_addition(self):
        tac = generate_tac_from_code("x = a + b;")
        self.assertEqual(tac, [
            "t1 = a + b",
            "x = t1"
        ])

    def test_simple_multiplication(self):
        tac = generate_tac_from_code("x = a * b;")
        self.assertEqual(tac, [
            "t1 = a * b",
            "x = t1"
        ])

    def test_multiplication_precedence_over_addition(self):
        # result = 2 + 3 * 4;
        tac = generate_tac_from_code("result = 2 + 3 * 4;")
        self.assertEqual(tac, [
            "t1 = 3 * 4",
            "t2 = 2 + t1",
            "result = t2"
        ])

    def test_parentheses_override_precedence(self):
        # result = (2 + 3) * 4;
        tac = generate_tac_from_code("result = (2 + 3) * 4;")
        self.assertEqual(tac, [
            "t1 = 2 + 3",
            "t2 = t1 * 4",
            "result = t2"
        ])

    def test_prompt_acceptance_example(self):
        # a = b + c * d;
        tac = generate_tac_from_code("a = b + c * d;")
        self.assertEqual(tac, [
            "t1 = c * d",
            "t2 = b + t1",
            "a = t2"
        ])

    def test_unary_minus(self):
        # x = -5;
        tac1 = generate_tac_from_code("x = -5;")
        self.assertEqual(tac1, [
            "t1 = -5",
            "x = t1"
        ])

        # y = -(x + 3);
        tac2 = generate_tac_from_code("y = -(x + 3);")
        self.assertEqual(tac2, [
            "t1 = x + 3",
            "t2 = -t1",
            "y = t2"
        ])

    def test_unary_plus(self):
        # x = +5; Unary plus does not negate; should not generate redundant temporary
        tac = generate_tac_from_code("x = +5;")
        self.assertEqual(tac, ["x = 5"])

    def test_multiple_statements(self):
        code = "a = 10;\nb = 20;\ntotal = a + b;"
        tac = generate_tac_from_code(code)
        self.assertEqual(tac, [
            "a = 10",
            "b = 20",
            "t1 = a + b",
            "total = t1"
        ])

    def test_deterministic_temporary_numbering(self):
        code = "x = 1 + 2 + 3 + 4;"
        # ((1 + 2) + 3) + 4
        tac = generate_tac_from_code(code)
        self.assertEqual(tac, [
            "t1 = 1 + 2",
            "t2 = t1 + 3",
            "t3 = t2 + 4",
            "x = t3"
        ])

    def test_temporary_counter_resets_between_runs(self):
        gen = TACGenerator()
        lexer1 = Lexer("x = 1 + 2;")
        t1, _ = lexer1.tokenize()
        ast1 = Parser(t1).parse()
        tac1 = gen.generate(ast1)

        lexer2 = Lexer("y = 3 + 4;")
        t2, _ = lexer2.tokenize()
        ast2 = Parser(t2).parse()
        tac2 = gen.generate(ast2)

        self.assertEqual(tac1[0], "t1 = 1 + 2")
        self.assertEqual(tac2[0], "t1 = 3 + 4")  # Counter reset to t1

    def test_float_literal_preservation(self):
        tac = generate_tac_from_code("rate = 3.14159;")
        self.assertEqual(tac, ["rate = 3.14159"])

    def test_syntax_error_prevents_tac_generation(self):
        with self.assertRaises(ParserError):
            generate_tac_from_code("x = 10 + ;")

    def test_correct_final_assignment(self):
        tac = generate_tac_from_code("ans = a / b - c * d;")
        # Left associativity: (a / b) - (c * d)
        self.assertEqual(tac, [
            "t1 = a / b",
            "t2 = c * d",
            "t3 = t1 - t2",
            "ans = t3"
        ])


if __name__ == "__main__":
    unittest.main()

