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

Generates:
    1. Abstract Syntax Tree (AST) constructed from ast_nodes.py
    2. Concrete Syntax Tree (Parse Tree) constructed from parse_tree.py

Reports comprehensive syntax error diagnostics with line, column, and suggestions.
"""

from typing import List, Optional, Tuple
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
from parse_tree import ParseTreeNode, make_terminal_node


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
    Produces both an Abstract Syntax Tree (AST) and a Concrete Syntax Tree (Parse Tree).
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.ast: Optional[Program] = None
        self.parse_tree: Optional[ParseTreeNode] = None

    def parse(self) -> Program:
        """
        Parses the token stream into a Program AST node and constructs the corresponding Parse Tree.
        Sets self.ast and self.parse_tree.
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

        statements_ast: List[ASTNode] = []
        statements_cst: List[ParseTreeNode] = []

        while not self._is_at_end():
            stmt_ast, stmt_cst = self._statement()
            statements_ast.append(stmt_ast)
            statements_cst.append(stmt_cst)

        self.ast = Program(statements=statements_ast)

        # Build root Parse Tree node
        cst_children = list(statements_cst)
        if self._check(TOKEN_EOF) and self.current < len(self.tokens):
            cst_children.append(make_terminal_node(self.tokens[self.current]))

        self.parse_tree = ParseTreeNode(
            symbol="program",
            label="program",
            kind="nonterminal",
            children=cst_children,
            production="program -> statement*"
        )

        return self.ast

    def get_parse_tree(self) -> Optional[ParseTreeNode]:
        """Returns the Parse Tree generated during the most recent parse pass."""
        return self.parse_tree

    def parse_all(self) -> Tuple[Program, Optional[ParseTreeNode]]:
        """Convenience method returning both AST and Parse Tree."""
        ast = self.parse()
        return ast, self.parse_tree

    # -------------------------------------------------------------------------
    # Grammar Rules
    # -------------------------------------------------------------------------

    def _statement(self) -> Tuple[Assignment, ParseTreeNode]:
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
        ident_cst = make_terminal_node(ident_token)

        # 2. Assignment Operator "="
        if not self._check(TOKEN_ASSIGN):
            next_tok = self._peek()
            raise ParserError(
                message=f"Expected assignment operator '=' after identifier '{ident_token.lexeme}', found '{next_tok.lexeme}'.",
                line=next_tok.line,
                column=next_tok.column,
                suggestion=f"Insert '=' after the variable name (e.g., '{ident_token.lexeme} = ...;')."
            )
        assign_token = self._advance()  # consume "="
        assign_cst = make_terminal_node(assign_token)

        # 3. Expression
        expr_ast, expr_cst = self._expression()

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
        semi_token = self._advance()  # consume ";"
        semi_cst = make_terminal_node(semi_token)

        ast_node = Assignment(
            identifier=target,
            value=expr_ast,
            line=ident_token.line,
            column=ident_token.column
        )

        cst_node = ParseTreeNode(
            symbol="statement",
            label="statement",
            kind="nonterminal",
            children=[ident_cst, assign_cst, expr_cst, semi_cst],
            production="statement -> IDENTIFIER = expression ;",
            line=ident_token.line,
            column=ident_token.column
        )

        return ast_node, cst_node

    def _expression(self) -> Tuple[ASTNode, ParseTreeNode]:
        """
        expression -> term (("+" | "-") term)*
        Left-associative binary addition and subtraction.
        """
        node_ast, node_cst = self._term()
        cst_children = [node_cst]
        has_ops = False

        while self._match(TOKEN_PLUS, TOKEN_MINUS):
            has_ops = True
            op_token = self._previous()
            op_cst = make_terminal_node(op_token)
            right_ast, right_cst = self._term()
            node_ast = BinaryOp(
                operator=op_token.lexeme,
                left=node_ast,
                right=right_ast,
                line=op_token.line,
                column=op_token.column
            )
            cst_children.extend([op_cst, right_cst])

        production = "expression -> term (('+' | '-') term)*" if has_ops else "expression -> term"
        cst_node = ParseTreeNode(
            symbol="expression",
            label="expression",
            kind="nonterminal",
            children=cst_children,
            production=production,
            line=cst_children[0].line if cst_children else None,
            column=cst_children[0].column if cst_children else None
        )

        return node_ast, cst_node

    def _term(self) -> Tuple[ASTNode, ParseTreeNode]:
        """
        term -> unary (("*" | "/") unary)*
        Left-associative binary multiplication and division.
        """
        node_ast, node_cst = self._unary()
        cst_children = [node_cst]
        has_ops = False

        while self._match(TOKEN_STAR, TOKEN_SLASH):
            has_ops = True
            op_token = self._previous()
            op_cst = make_terminal_node(op_token)
            right_ast, right_cst = self._unary()
            node_ast = BinaryOp(
                operator=op_token.lexeme,
                left=node_ast,
                right=right_ast,
                line=op_token.line,
                column=op_token.column
            )
            cst_children.extend([op_cst, right_cst])

        production = "term -> unary (('*' | '/') unary)*" if has_ops else "term -> unary"
        cst_node = ParseTreeNode(
            symbol="term",
            label="term",
            kind="nonterminal",
            children=cst_children,
            production=production,
            line=cst_children[0].line if cst_children else None,
            column=cst_children[0].column if cst_children else None
        )

        return node_ast, cst_node

    def _unary(self) -> Tuple[ASTNode, ParseTreeNode]:
        """
        unary -> ("+" | "-") unary | primary
        Right-recursive prefix unary plus and minus.
        """
        if self._match(TOKEN_PLUS, TOKEN_MINUS):
            op_token = self._previous()
            op_cst = make_terminal_node(op_token)
            operand_ast, operand_cst = self._unary()
            ast_node = UnaryOp(
                operator=op_token.lexeme,
                operand=operand_ast,
                line=op_token.line,
                column=op_token.column
            )
            cst_node = ParseTreeNode(
                symbol="unary",
                label="unary",
                kind="nonterminal",
                children=[op_cst, operand_cst],
                production=f"unary -> {op_token.lexeme} unary",
                line=op_token.line,
                column=op_token.column
            )
            return ast_node, cst_node

        prim_ast, prim_cst = self._primary()
        cst_node = ParseTreeNode(
            symbol="unary",
            label="unary",
            kind="nonterminal",
            children=[prim_cst],
            production="unary -> primary",
            line=prim_cst.line,
            column=prim_cst.column
        )
        return prim_ast, cst_node

    def _primary(self) -> Tuple[ASTNode, ParseTreeNode]:
        """
        primary -> NUMBER | IDENTIFIER | "(" expression ")"
        """
        curr = self._peek()

        # Number literal
        if self._match(TOKEN_NUMBER):
            num_tok = self._previous()
            ast_node = Number(
                value=num_tok.value,
                raw=num_tok.lexeme,
                line=num_tok.line,
                column=num_tok.column
            )
            num_cst = make_terminal_node(num_tok)
            cst_node = ParseTreeNode(
                symbol="primary",
                label="primary",
                kind="nonterminal",
                children=[num_cst],
                production="primary -> NUMBER",
                line=num_tok.line,
                column=num_tok.column
            )
            return ast_node, cst_node

        # Identifier
        if self._match(TOKEN_IDENTIFIER):
            ident_tok = self._previous()
            ast_node = Identifier(
                name=ident_tok.lexeme,
                line=ident_tok.line,
                column=ident_tok.column
            )
            ident_cst = make_terminal_node(ident_tok)
            cst_node = ParseTreeNode(
                symbol="primary",
                label="primary",
                kind="nonterminal",
                children=[ident_cst],
                production="primary -> IDENTIFIER",
                line=ident_tok.line,
                column=ident_tok.column
            )
            return ast_node, cst_node

        # Parenthesized expression "(" expression ")"
        if self._match(TOKEN_LPAREN):
            lparen_tok = self._previous()
            lparen_cst = make_terminal_node(lparen_tok)
            expr_ast, expr_cst = self._expression()
            if not self._match(TOKEN_RPAREN):
                curr = self._peek()
                raise ParserError(
                    message=f"Unmatched opening parenthesis '(' from line {lparen_tok.line}, col {lparen_tok.column}.",
                    line=curr.line,
                    column=curr.column,
                    suggestion="Add a closing parenthesis ')' to properly close the sub-expression."
                )
            rparen_tok = self._previous()
            rparen_cst = make_terminal_node(rparen_tok)

            cst_node = ParseTreeNode(
                symbol="primary",
                label="primary",
                kind="nonterminal",
                children=[lparen_cst, expr_cst, rparen_cst],
                production="primary -> ( expression )",
                line=lparen_tok.line,
                column=lparen_tok.column
            )
            return expr_ast, cst_node

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
