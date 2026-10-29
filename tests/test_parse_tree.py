"""
tests/test_parse_tree.py - Unit Tests for LexiTree Concrete Syntax Tree (Parse Tree)

Tests:
1. Single assignment statement grammar structure.
2. Basic addition expression hierarchy.
3. Operator precedence representation in the parse tree.
4. Parenthesized expression grammar expansion.
5. Unary minus grammar production.
6. Multiple statements in a single program.
7. Correct terminal ordering (IDENTIFIER, '=', expr, ';').
8. Correct grammar-symbol hierarchy (program -> statement -> expression -> term -> unary -> primary).
9. Presence of punctuation terminals ('=', ';', '(', ')').
10. Nested arithmetic expressions.
11. Source locations (line and column) preserved on terminal and non-terminal nodes.
12. Parser errors prevent parse tree creation.
13. JSON serialization (to_dict()) validation.
"""

import unittest
from lexer import Lexer
from parser import Parser, ParserError
from parse_tree import ParseTreeNode


def parse_to_tree(code: str) -> ParseTreeNode:
    lexer = Lexer(code)
    tokens, errors = lexer.tokenize()
    if errors:
        raise ValueError(f"Lexical errors: {errors}")
    parser = Parser(tokens)
    parser.parse()
    return parser.get_parse_tree()


class TestParseTree(unittest.TestCase):
    """Test suite for Concrete Syntax Tree (Parse Tree) construction and verification."""

    def test_single_assignment(self):
        cst = parse_to_tree("x = 10;")
        self.assertIsNotNone(cst)
        self.assertEqual(cst.symbol, "program")
        self.assertEqual(cst.kind, "nonterminal")

        # Expect statement child
        statements = [c for c in cst.children if c.symbol == "statement"]
        self.assertEqual(len(statements), 1)

        stmt = statements[0]
        child_symbols = [c.symbol for c in stmt.children]
        # statement -> IDENTIFIER "=" expression ";"
        self.assertEqual(child_symbols, ["IDENTIFIER", "ASSIGN", "expression", "SEMICOLON"])

    def test_basic_addition(self):
        cst = parse_to_tree("val = 10 + 20;")
        stmt = [c for c in cst.children if c.symbol == "statement"][0]
        expr = [c for c in stmt.children if c.symbol == "expression"][0]

        # expression -> term + term
        expr_child_symbols = [c.symbol for c in expr.children]
        self.assertEqual(expr_child_symbols, ["term", "PLUS", "term"])

    def test_operator_precedence(self):
        # result = 2 + 3 * 4;
        # In grammar: expression has 'term' and 'term' around PLUS.
        # The second term contains 'unary * unary'
        cst = parse_to_tree("result = 2 + 3 * 4;")
        stmt = [c for c in cst.children if c.symbol == "statement"][0]
        expr = [c for c in stmt.children if c.symbol == "expression"][0]

        # expression has term '+' term
        self.assertEqual([c.symbol for c in expr.children], ["term", "PLUS", "term"])

        # Second term should have STAR
        second_term = expr.children[2]
        self.assertEqual([c.symbol for c in second_term.children], ["unary", "STAR", "unary"])

    def test_parenthesized_expression(self):
        # result = (2 + 3) * 4;
        cst = parse_to_tree("result = (2 + 3) * 4;")
        stmt = [c for c in cst.children if c.symbol == "statement"][0]
        expr = [c for c in stmt.children if c.symbol == "expression"][0]
        term = expr.children[0]

        # term -> unary * unary
        self.assertEqual([c.symbol for c in term.children], ["unary", "STAR", "unary"])

        # First unary -> primary -> LPAREN expression RPAREN
        first_unary = term.children[0]
        first_primary = first_unary.children[0]
        self.assertEqual([c.symbol for c in first_primary.children], ["LPAREN", "expression", "RPAREN"])

    def test_unary_minus(self):
        cst = parse_to_tree("x = -5;")
        stmt = [c for c in cst.children if c.symbol == "statement"][0]
        expr = [c for c in stmt.children if c.symbol == "expression"][0]
        term = expr.children[0]
        unary = term.children[0]

        # unary -> MINUS unary
        self.assertEqual([c.symbol for c in unary.children], ["MINUS", "unary"])
        self.assertEqual(unary.children[0].lexeme, "-")

    def test_multiple_statements(self):
        code = "a = 1;\nb = 2;\nc = a + b;"
        cst = parse_to_tree(code)
        statements = [c for c in cst.children if c.symbol == "statement"]
        self.assertEqual(len(statements), 3)

    def test_terminal_ordering(self):
        cst = parse_to_tree("alpha = 99;")
        stmt = [c for c in cst.children if c.symbol == "statement"][0]
        terminals = [c for c in stmt.children if c.kind == "terminal"]

        self.assertEqual(terminals[0].lexeme, "alpha")
        self.assertEqual(terminals[1].lexeme, "=")
        self.assertEqual(terminals[2].lexeme, ";")

    def test_grammar_symbol_hierarchy(self):
        # Complete hierarchy check: program -> statement -> expression -> term -> unary -> primary -> NUMBER
        cst = parse_to_tree("x = 42;")
        self.assertEqual(cst.symbol, "program")
        stmt = cst.children[0]
        self.assertEqual(stmt.symbol, "statement")
        expr = stmt.children[2]
        self.assertEqual(expr.symbol, "expression")
        term = expr.children[0]
        self.assertEqual(term.symbol, "term")
        unary = term.children[0]
        self.assertEqual(unary.symbol, "unary")
        primary = unary.children[0]
        self.assertEqual(primary.symbol, "primary")
        num_terminal = primary.children[0]
        self.assertEqual(num_terminal.symbol, "NUMBER")
        self.assertEqual(num_terminal.lexeme, "42")
        self.assertEqual(num_terminal.kind, "terminal")

    def test_presence_of_syntax_symbols(self):
        # Semicolons and assignment symbols are retained in CST
        cst = parse_to_tree("foo = bar;")
        stmt = [c for c in cst.children if c.symbol == "statement"][0]
        lexemes = [c.lexeme for c in stmt.children if c.kind == "terminal"]
        self.assertIn("=", lexemes)
        self.assertIn(";", lexemes)

    def test_nested_expressions(self):
        cst = parse_to_tree("x = (a + (b * c));")
        self.assertIsNotNone(cst)
        stmt = cst.children[0]
        expr = stmt.children[2]
        self.assertEqual(expr.symbol, "expression")

    def test_source_locations_preserved(self):
        cst = parse_to_tree("x = 100;")
        stmt = cst.children[0]
        ident = stmt.children[0]
        self.assertEqual(ident.line, 1)
        self.assertEqual(ident.column, 1)

    def test_invalid_syntax_raises_error(self):
        with self.assertRaises(ParserError):
            parse_to_tree("x = 10 + ;")

    def test_json_serialization(self):
        cst = parse_to_tree("x = 10;")
        cst_dict = cst.to_dict()
        self.assertIsInstance(cst_dict, dict)
        self.assertEqual(cst_dict["symbol"], "program")
        self.assertEqual(cst_dict["kind"], "nonterminal")
        self.assertIsInstance(cst_dict["children"], list)
        self.assertGreater(len(cst_dict["children"]), 0)


if __name__ == "__main__":
    unittest.main()

