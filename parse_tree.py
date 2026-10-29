"""
parse_tree.py - Concrete Syntax Tree (Parse Tree) Data Structures for LexiTree

Represents concrete syntax tree nodes that reflect the exact formal grammar productions,
retaining terminals (with lexemes, lines, columns) and non-terminals in their original
derivation order.
"""

from typing import List, Optional, Dict, Any


class ParseTreeNode:
    """
    Represents a node in the Concrete Syntax Tree (Parse Tree).
    
    Attributes:
        symbol: Grammar symbol (e.g., 'program', 'statement', 'expression', 'term', 'unary', 'primary',
                or terminal token type such as 'IDENTIFIER', 'ASSIGN', 'PLUS', 'NUMBER', 'SEMICOLON').
        label: Human-readable display label for SVG node rendering.
        kind: Node category - either 'nonterminal' or 'terminal'.
        children: Ordered list of child ParseTreeNode instances representing grammar expansion.
        lexeme: Actual source code substring for terminal nodes.
        line: 1-based source code line number.
        column: 1-based source code column number.
        production: Grammar production rule string used to expand this non-terminal.
    """

    def __init__(
        self,
        symbol: str,
        label: str,
        kind: str,
        children: Optional[List["ParseTreeNode"]] = None,
        lexeme: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        production: Optional[str] = None
    ):
        self.symbol = symbol
        self.label = label
        self.kind = kind  # 'nonterminal' or 'terminal'
        self.children = children if children is not None else []
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.production = production

    def to_dict(self) -> Dict[str, Any]:
        """Convert Parse Tree node into a JSON-serializable dictionary."""
        node_dict: Dict[str, Any] = {
            "symbol": self.symbol,
            "label": self.label,
            "kind": self.kind,
            "children": [child.to_dict() for child in self.children]
        }
        if self.lexeme is not None:
            node_dict["lexeme"] = self.lexeme
        if self.line is not None:
            node_dict["line"] = self.line
        if self.column is not None:
            node_dict["column"] = self.column
        if self.production is not None:
            node_dict["production"] = self.production
        return node_dict

    def __repr__(self) -> str:
        lex_str = f", lexeme='{self.lexeme}'" if self.lexeme is not None else ""
        return f"ParseTreeNode({self.symbol}, kind='{self.kind}'{lex_str}, children={len(self.children)})"


def make_terminal_node(token) -> ParseTreeNode:
    """
    Helper function to construct a terminal ParseTreeNode from a Token object.
    """
    display_label = token.lexeme if token.lexeme else token.type
    return ParseTreeNode(
        symbol=token.type,
        label=display_label,
        kind="terminal",
        children=[],
        lexeme=token.lexeme if token.lexeme else "<EOF>",
        line=token.line,
        column=token.column,
        production=None
    )

