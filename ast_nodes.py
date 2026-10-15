"""
ast_nodes.py - Abstract Syntax Tree (AST) Node Definitions for LexiTree

This module defines the node classes used to build the Abstract Syntax Tree (AST)
during syntax analysis. Each node corresponds to a grammatical construct in the
LexiTree mini-language and provides a `to_dict()` method for JSON serialization
to the frontend SVG visualizer.
"""

from typing import List, Union, Dict, Any


class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the AST node into a dictionary serializable to JSON."""
        raise NotImplementedError("Subclasses must implement to_dict()")


class Program(ASTNode):
    """
    Root node representing an entire program, consisting of zero or more statements.
    
    Grammar: program -> statement*
    """
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Program",
            "statements": [stmt.to_dict() for stmt in self.statements]
        }

    def __repr__(self) -> str:
        return f"Program(statements={self.statements})"


class Assignment(ASTNode):
    """
    Node representing a variable assignment statement.
    
    Grammar: statement -> IDENTIFIER "=" expression ";"
    """
    def __init__(self, identifier: "Identifier", value: ASTNode, line: int = 0, column: int = 0):
        self.identifier = identifier
        self.value = value
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Assignment",
            "identifier": self.identifier.to_dict(),
            "value": self.value.to_dict(),
            "line": self.line,
            "column": self.column
        }

    def __repr__(self) -> str:
        return f"Assignment({self.identifier} = {self.value})"


class BinaryOp(ASTNode):
    """
    Node representing a binary arithmetic operation (+, -, *, /).
    
    Left-associative binary operator with left and right subtrees.
    """
    def __init__(self, operator: str, left: ASTNode, right: ASTNode, line: int = 0, column: int = 0):
        self.operator = operator
        self.left = left
        self.right = right
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "BinaryOp",
            "operator": self.operator,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "line": self.line,
            "column": self.column
        }

    def __repr__(self) -> str:
        return f"BinaryOp({self.left} {self.operator} {self.right})"


class UnaryOp(ASTNode):
    """
    Node representing a unary arithmetic operation (+ or -).
    
    Right-recursive / prefix unary operator applied to an operand expression.
    """
    def __init__(self, operator: str, operand: ASTNode, line: int = 0, column: int = 0):
        self.operator = operator
        self.operand = operand
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "UnaryOp",
            "operator": self.operator,
            "operand": self.operand.to_dict(),
            "line": self.line,
            "column": self.column
        }

    def __repr__(self) -> str:
        return f"UnaryOp({self.operator}{self.operand})"


class Number(ASTNode):
    """
    Leaf node representing an integer or floating-point literal.
    """
    def __init__(self, value: Union[int, float], raw: str, line: int = 0, column: int = 0):
        self.value = value
        self.raw = raw
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Number",
            "value": self.value,
            "raw": self.raw,
            "line": self.line,
            "column": self.column
        }

    def __repr__(self) -> str:
        return f"Number({self.raw})"


class Identifier(ASTNode):
    """
    Leaf node representing a variable identifier.
    """
    def __init__(self, name: str, line: int = 0, column: int = 0):
        self.name = name
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Identifier",
            "name": self.name,
            "line": self.line,
            "column": self.column
        }

    def __repr__(self) -> str:
        return f"Identifier({self.name})"
