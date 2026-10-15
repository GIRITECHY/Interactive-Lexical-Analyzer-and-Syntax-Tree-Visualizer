"""
tests/test_parser.py - Unit Tests for LexiTree Recursive-Descent Parser

Tests valid assignments, multiple statements, operator precedence,
associativity, unary operators, parenthesized expressions,
and comprehensive syntax error handling (missing semicolons, unmatched parentheses,
missing operands, invalid statement structure).
"""

import unittest
from lexer import Lexer
from parser import Parser, ParserError
from ast_nodes import Assignment, BinaryOp, UnaryOp, Number, Identifier


def parse_code(code: str):
    lexer = Lexer(code)
    tokens, errors = lexer.tokenize()
    if errors:
        raise ValueError(f"Lexical errors: {errors}")
    parser = Parser(tokens)
    return parser.parse()


class TestParser(unittest.TestCase):
    """Test suite for Recursive-Descent Parser and AST Construction."""

    def test_simple_assignment(self):
        ast = parse_code("x = 10;")
        self.assertEqual(len(ast.statements), 1)
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, Assignment)
        self.assertEqual(stmt.identifier.name, "x")
        self.assertIsInstance(stmt.value, Number)
        self.assertEqual(stmt.value.value, 10)

    def test_multiple_statements(self):
        code = "a = 10;\nb = 20;\ntotal = a + b;"
        ast = parse_code(code)
        self.assertEqual(len(ast.statements), 3)
        self.assertEqual(ast.statements[0].identifier.name, "a")
        self.assertEqual(ast.statements[1].identifier.name, "b")
        self.assertEqual(ast.statements[2].identifier.name, "total")

    def test_operator_precedence_multiplication_over_addition(self):
        # result = 2 + 3 * 4;
        # AST should be BinaryOp('+', Number(2), BinaryOp('*', Number(3), Number(4)))
        ast = parse_code("result = 2 + 3 * 4;")
        stmt = ast.statements[0]
        self.assertIsInstance(stmt.value, BinaryOp)
        self.assertEqual(stmt.value.operator, "+")
        self.assertIsInstance(stmt.value.left, Number)
        self.assertEqual(stmt.value.left.value, 2)
        self.assertIsInstance(stmt.value.right, BinaryOp)
        self.assertEqual(stmt.value.right.operator, "*")
        self.assertEqual(stmt.value.right.left.value, 3)
        self.assertEqual(stmt.value.right.right.value, 4)

    def test_parentheses_override_precedence(self):
        # result = (2 + 3) * 4;
        # AST should be BinaryOp('*', BinaryOp('+', Number(2), Number(3)), Number(4))
        ast = parse_code("result = (2 + 3) * 4;")
        stmt = ast.statements[0]
        self.assertIsInstance(stmt.value, BinaryOp)
        self.assertEqual(stmt.value.operator, "*")
        self.assertIsInstance(stmt.value.left, BinaryOp)
        self.assertEqual(stmt.value.left.operator, "+")
        self.assertEqual(stmt.value.left.left.value, 2)
        self.assertEqual(stmt.value.left.right.value, 3)
        self.assertIsInstance(stmt.value.right, Number)
        self.assertEqual(stmt.value.right.value, 4)

    def test_left_associativity(self):
        # x = 10 - 5 - 2; -> ((10 - 5) - 2)
        ast = parse_code("x = 10 - 5 - 2;")
        stmt = ast.statements[0]
        self.assertIsInstance(stmt.value, BinaryOp)
        self.assertEqual(stmt.value.operator, "-")
        self.assertIsInstance(stmt.value.left, BinaryOp)
        self.assertEqual(stmt.value.left.operator, "-")
        self.assertEqual(stmt.value.left.left.value, 10)
        self.assertEqual(stmt.value.left.right.value, 5)
        self.assertEqual(stmt.value.right.value, 2)

    def test_unary_operators(self):
        # x = -5; y = -(x + 3);
        code = "x = -5;\ny = -(x + 3);"
        ast = parse_code(code)
        stmt1 = ast.statements[0]
        self.assertIsInstance(stmt1.value, UnaryOp)
        self.assertEqual(stmt1.value.operator, "-")
        self.assertEqual(stmt1.value.operand.value, 5)

        stmt2 = ast.statements[1]
        self.assertIsInstance(stmt2.value, UnaryOp)
        self.assertEqual(stmt2.value.operator, "-")
        self.assertIsInstance(stmt2.value.operand, BinaryOp)

    def test_missing_semicolon(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("x = 10")
        self.assertIn("Missing semicolon", ctx.exception.message)

    def test_missing_operand(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("x = 10 + ;")
        self.assertIn("Missing operand", ctx.exception.message)

    def test_unmatched_open_parenthesis(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("x = (10 + 5;")
        self.assertIn("Unmatched opening parenthesis", ctx.exception.message)

    def test_unmatched_close_parenthesis(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("x = 10 + 5);")
        self.assertIn("Unmatched closing parenthesis", ctx.exception.message)

    def test_invalid_statement_structure_missing_identifier(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("= 10;")
        self.assertIn("Missing variable identifier", ctx.exception.message)

    def test_invalid_statement_assign_to_number(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("10 = 5;")
        self.assertIn("Cannot assign to a numeric constant", ctx.exception.message)

    def test_missing_assignment_operator(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("x 10;")
        self.assertIn("Expected assignment operator '='", ctx.exception.message)

    def test_empty_input(self):
        with self.assertRaises(ParserError) as ctx:
            parse_code("   \n\t  ")
        self.assertIn("Source code is empty", ctx.exception.message)


if __name__ == "__main__":
    unittest.main()
