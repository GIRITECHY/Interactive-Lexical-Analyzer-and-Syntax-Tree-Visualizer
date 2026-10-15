"""
parser.py - Custom Recursive-Descent Parser for LexiTree

Implements a recursive-descent parser adhering strictly to the grammar:

    program     -> statement*
    statement   -> IDENTIFIER "=" expression ";"
    expression  -> term (("+" | "-") term)*
    term        -> unary (("*" | "/") unary)*
    unary       -> ("+" | "-") unary | primary
    primary     -> NUMBER | IDENTIFIER | "(" expression ")"

Operator precedence implemented:
    1. Parentheses: ( ... )
    2. Unary operators: + - (right-associative / prefix)
    3. Multiplicative: * / (left-associative)
    4. Additive: + - (left-associative)

Generates an Abstract Syntax Tree (AST) constructed from ast_nodes.py.
Reports comprehensive syntax error diagnostics with line, column, and suggestions.
"""

from typing import List, Optional
from lexer import (
    Token,
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
from ast_nodes import (
    ASTNode,
    Program,
    Assignment,
    BinaryOp,
    UnaryOp,
    Number,
    Identifier
)


class ParserError(Exception):
    """
    Raised when syntax analysis fails.
    Contains error message, line number, column number, and a suggested fix.
    """
    def __init__(self, message: str, line: int, column: int, suggestion: str = ""):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.suggestion = suggestion

    def to_dict(self):
        return {
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion
        }

    def __repr__(self) -> str:
        return f"ParserError('{self.message}', line={self.line}, col={self.column})"


class Parser:
    """
    Recursive-descent syntax analyzer for LexiTree.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        """
        Parses the token stream into a Program AST node.
        Raises ParserError on any grammatical violation.
        """
        # Empty input check (only EOF token present)
        if len(self.tokens) == 0 or (len(self.tokens) == 1 and self.tokens[0].type == TOKEN_EOF):
            raise ParserError(
                message="Source code is empty.",
                line=1,
                column=1,
                suggestion="Enter at least one assignment statement, e.g., 'x = 10;'."
            )

        statements: List[ASTNode] = []
        while not self._is_at_end():
            statements.append(self._statement())

        return Program(statements=statements)

    # -------------------------------------------------------------------------
    # Grammar Rules
    # -------------------------------------------------------------------------

    def _statement(self) -> Assignment:
        """
        statement -> IDENTIFIER "=" expression ";"
        """
        curr = self._peek()

        # Check for missing identifier or invalid starting token
        if not self._check(TOKEN_IDENTIFIER):
            if self._check(TOKEN_NUMBER):
                raise ParserError(
                    message=f"Cannot assign to a numeric constant '{curr.lexeme}'.",
                    line=curr.line,
                    column=curr.column,
                    suggestion="Assignments must start with a variable identifier on the left-hand side (e.g., 'x = 10;')."
                )
            elif self._check(TOKEN_ASSIGN):
                raise ParserError(
                    message="Missing variable identifier before assignment operator '='.",
                    line=curr.line,
                    column=curr.column,
                    suggestion="Specify a variable name before '=' (e.g., 'total = 10;')."
                )
            elif self._check(TOKEN_SEMICOLON):
                raise ParserError(
                    message="Unexpected empty statement with lone semicolon ';'.",
                    line=curr.line,
                    column=curr.column,
                    suggestion="Remove the extra semicolon or provide a valid assignment statement."
                )
            else:
                raise ParserError(
                    message=f"Expected variable identifier at start of statement, found '{curr.lexeme}'.",
                    line=curr.line,
                    column=curr.column,
                    suggestion="Each statement must begin with a variable name (e.g., 'result = 2 + 3;')."
                )

        # 1. Target Identifier
        ident_token = self._advance()
        target = Identifier(name=ident_token.lexeme, line=ident_token.line, column=ident_token.column)

        # 2. Assignment Operator "="
        if not self._check(TOKEN_ASSIGN):
            next_tok = self._peek()
            raise ParserError(
                message=f"Expected assignment operator '=' after identifier '{ident_token.lexeme}', found '{next_tok.lexeme}'.",
                line=next_tok.line,
                column=next_tok.column,
                suggestion=f"Insert '=' after the variable name (e.g., '{ident_token.lexeme} = ...;')."
            )
        self._advance()  # consume "="

        # 3. Expression
        expr_value = self._expression()

        # 4. Semicolon ";"
        if not self._check(TOKEN_SEMICOLON):
            next_tok = self._peek()
            if next_tok.type == TOKEN_RPAREN:
                raise ParserError(
                    message=f"Unmatched closing parenthesis ')' at line {next_tok.line}, col {next_tok.column}.",
                    line=next_tok.line,
                    column=next_tok.column,
                    suggestion="Remove the extraneous ')' or add a matching opening parenthesis '('."
                )
            raise ParserError(
                message=f"Missing semicolon ';' after statement, found '{next_tok.lexeme if not self._is_at_end() else '<EOF>'}'.",
                line=next_tok.line,
                column=next_tok.column,
                suggestion="Add a trailing semicolon ';' to terminate the statement."
            )
        self._advance()  # consume ";"

        return Assignment(
            identifier=target,
            value=expr_value,
            line=ident_token.line,
            column=ident_token.column
        )

    def _expression(self) -> ASTNode:
        """
        expression -> term (("+" | "-") term)*
        Left-associative binary addition and subtraction.
        """
        node = self._term()

        while self._match(TOKEN_PLUS, TOKEN_MINUS):
            op_token = self._previous()
            right = self._term()
            node = BinaryOp(
                operator=op_token.lexeme,
                left=node,
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return node

    def _term(self) -> ASTNode:
        """
        term -> unary (("*" | "/") unary)*
        Left-associative binary multiplication and division.
        """
        node = self._unary()

        while self._match(TOKEN_STAR, TOKEN_SLASH):
            op_token = self._previous()
            right = self._unary()
            node = BinaryOp(
                operator=op_token.lexeme,
                left=node,
                right=right,
                line=op_token.line,
                column=op_token.column
            )

        return node

    def _unary(self) -> ASTNode:
        """
        unary -> ("+" | "-") unary | primary
        Right-recursive prefix unary plus and minus.
        """
        if self._match(TOKEN_PLUS, TOKEN_MINUS):
            op_token = self._previous()
            operand = self._unary()
            return UnaryOp(
                operator=op_token.lexeme,
                operand=operand,
                line=op_token.line,
                column=op_token.column
            )

        return self._primary()

    def _primary(self) -> ASTNode:
        """
        primary -> NUMBER | IDENTIFIER | "(" expression ")"
        """
        curr = self._peek()

        # Number literal
        if self._match(TOKEN_NUMBER):
            num_tok = self._previous()
            return Number(
                value=num_tok.value,
                raw=num_tok.lexeme,
                line=num_tok.line,
                column=num_tok.column
            )

        # Identifier
        if self._match(TOKEN_IDENTIFIER):
            ident_tok = self._previous()
            return Identifier(
                name=ident_tok.lexeme,
                line=ident_tok.line,
                column=ident_tok.column
            )

        # Parenthesized expression "(" expression ")"
        if self._match(TOKEN_LPAREN):
            lparen_tok = self._previous()
            expr = self._expression()
            if not self._match(TOKEN_RPAREN):
                curr = self._peek()
                raise ParserError(
                    message=f"Unmatched opening parenthesis '(' from line {lparen_tok.line}, col {lparen_tok.column}.",
                    line=curr.line,
                    column=curr.column,
                    suggestion="Add a closing parenthesis ')' to properly close the sub-expression."
                )
            return expr

        # Unmatched closing parenthesis
        if self._check(TOKEN_RPAREN):
            raise ParserError(
                message=f"Unmatched closing parenthesis ')' at line {curr.line}, col {curr.column}.",
                line=curr.line,
                column=curr.column,
                suggestion="Remove the superfluous ')' or check for missing open parenthesis '('."
            )

        # Missing operand before delimiter or EOF
        if self._check(TOKEN_SEMICOLON) or self._is_at_end():
            raise ParserError(
                message=f"Missing operand before '{curr.lexeme if not self._is_at_end() else '<EOF>'}'.",
                line=curr.line,
                column=curr.column,
                suggestion="Provide a valid number, variable, or parenthesized sub-expression after the operator."
            )

        # Unexpected token
        raise ParserError(
            message=f"Unexpected token '{curr.lexeme}' in expression.",
            line=curr.line,
            column=curr.column,
            suggestion="Expected a number, variable name, or '('."
        )

    # -------------------------------------------------------------------------
    # Helper Inspection and Navigation Methods
    # -------------------------------------------------------------------------

    def _match(self, *types: str) -> bool:
        """Check if current token matches any given type, and advance if so."""
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, token_type: str) -> bool:
        """Check if current token matches token_type without advancing."""
        if self._is_at_end():
            return token_type == TOKEN_EOF
        return self._peek().type == token_type

    def _advance(self) -> Token:
        """Advance cursor and return previous token."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        """Return the current token without advancing."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Return the token immediately preceding the current position."""
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        """Return True if reached EOF token or end of list."""
        return self.current >= len(self.tokens) or self.tokens[self.current].type == TOKEN_EOF
