"""
lexer.py - Custom Lexical Analyzer (Tokenizer) for LexiTree

Performs lexical analysis on source code input:
- Recognizes Identifiers, Numeric constants (integers and decimals),
  Arithmetic operators (+, -, *, /), Assignment operator (=),
  Delimiters ((, ), ;), and an EOF token.
- Tracks token type, lexeme, 1-based line number, and 1-based column number.
- Skips whitespace and tracks source positions accurately across newlines.
- Recovers gracefully from lexical errors (invalid characters, malformed numbers),
  collecting all errors without crashing so valid tokens remain inspectable.
- Language has no reserved keywords in this version; all valid words are identifiers.
"""

from typing import List, Tuple, Optional, Any, Dict


# Token Type Constants
TOKEN_IDENTIFIER = "IDENTIFIER"
TOKEN_NUMBER     = "NUMBER"
TOKEN_PLUS       = "PLUS"
TOKEN_MINUS      = "MINUS"
TOKEN_STAR       = "STAR"
TOKEN_SLASH      = "SLASH"
TOKEN_ASSIGN     = "ASSIGN"
TOKEN_LPAREN     = "LPAREN"
TOKEN_RPAREN     = "RPAREN"
TOKEN_SEMICOLON  = "SEMICOLON"
TOKEN_EOF        = "EOF"


class Token:
    """Represents a lexical token produced by the scanner."""

    def __init__(
        self,
        token_type: str,
        lexeme: str,
        line: int,
        column: int,
        value: Optional[Any] = None
    ):
        self.type = token_type
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.value = value if value is not None else lexeme

    def to_dict(self) -> Dict[str, Any]:
        """Convert token to JSON-serializable dictionary."""
        return {
            "type": self.type,
            "lexeme": self.lexeme,
            "line": self.line,
            "column": self.column,
            "value": self.value
        }

    def __repr__(self) -> str:
        return f"Token({self.type}, '{self.lexeme}', line={self.line}, col={self.column})"


class LexicalError:
    """Represents a lexical analysis error with diagnostic details and suggestions."""

    def __init__(self, message: str, line: int, column: int, suggestion: str = ""):
        self.message = message
        self.line = line
        self.column = column
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to JSON-serializable dictionary."""
        return {
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion
        }

    def __repr__(self) -> str:
        return f"LexicalError('{self.message}', line={self.line}, col={self.column})"


class Lexer:
    """
    Custom lexical scanner for the LexiTree language.
    """

    def __init__(self, source_code: str):
        self.source = source_code
        self.length = len(source_code)
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.errors: List[LexicalError] = []

    def _peek(self, offset: int = 0) -> str:
        """Look at character ahead without advancing."""
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return ""

    def _advance(self) -> str:
        """Consume and return the current character, updating line & column tracking."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def tokenize(self) -> Tuple[List[Token], List[LexicalError]]:
        """
        Scan the entire source code and return a tuple of (tokens, errors).
        Always appends an EOF token at the end.
        """
        while self.pos < self.length:
            ch = self._peek()

            # 1. Skip whitespace
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # 2. Delimiters and single-character operators
            if ch == "+":
                self._advance()
                self.tokens.append(Token(TOKEN_PLUS, "+", start_line, start_col))
            elif ch == "-":
                self._advance()
                self.tokens.append(Token(TOKEN_MINUS, "-", start_line, start_col))
            elif ch == "*":
                self._advance()
                self.tokens.append(Token(TOKEN_STAR, "*", start_line, start_col))
            elif ch == "/":
                self._advance()
                self.tokens.append(Token(TOKEN_SLASH, "/", start_line, start_col))
            elif ch == "=":
                self._advance()
                self.tokens.append(Token(TOKEN_ASSIGN, "=", start_line, start_col))
            elif ch == "(":
                self._advance()
                self.tokens.append(Token(TOKEN_LPAREN, "(", start_line, start_col))
            elif ch == ")":
                self._advance()
                self.tokens.append(Token(TOKEN_RPAREN, ")", start_line, start_col))
            elif ch == ";":
                self._advance()
                self.tokens.append(Token(TOKEN_SEMICOLON, ";", start_line, start_col))

            # 3. Numeric literals (integers and decimals)
            elif ch.isdigit():
                self._scan_number(start_line, start_col)

            # 4. Identifiers
            elif ch.isalpha() or ch == "_":
                self._scan_identifier(start_line, start_col)

            # 5. Invalid / Unrecognized characters
            else:
                invalid_char = self._advance()
                self.errors.append(
                    LexicalError(
                        message=f"Invalid character '{invalid_char}' found.",
                        line=start_line,
                        column=start_col,
                        suggestion="Remove this character. LexiTree supports letters, digits, underscores, operators (+, -, *, /), '=', and delimiters (;, (, ))."
                    )
                )

        # Append EOF token
        self.tokens.append(Token(TOKEN_EOF, "", self.line, self.column, value="<EOF>"))
        return self.tokens, self.errors

    def _scan_number(self, start_line: int, start_col: int):
        """Scans an integer or floating-point literal, checking for malformed patterns."""
        num_str = ""
        has_dot = False

        while self.pos < self.length:
            ch = self._peek()
            if ch.isdigit():
                num_str += self._advance()
            elif ch == ".":
                if has_dot:
                    # Multiple decimal points: e.g. 1.2.3
                    dot_col = self.column
                    num_str += self._advance()
                    # Consume any subsequent digits or dots to isolate the malformed token
                    while self.pos < self.length and (self._peek().isdigit() or self._peek() == "."):
                        num_str += self._advance()
                    self.errors.append(
                        LexicalError(
                            message=f"Malformed numeric constant '{num_str}': multiple decimal points.",
                            line=start_line,
                            column=start_col,
                            suggestion="Ensure numbers have at most one decimal point (e.g., '3.14')."
                        )
                    )
                    return
                else:
                    # Peek next char after the dot
                    next_ch = self._peek(1)
                    if not next_ch.isdigit():
                        # Trailing dot with no digits (e.g. "12.")
                        num_str += self._advance()
                        self.errors.append(
                            LexicalError(
                                message=f"Malformed numeric constant '{num_str}': expected digit after decimal point.",
                                line=start_line,
                                column=start_col,
                                suggestion="Add one or more digits after the decimal point (e.g., '12.0')."
                            )
                        )
                        return
                    has_dot = True
                    num_str += self._advance()
            else:
                break

        # Check if immediately followed by an identifier character (e.g., "10abc")
        if self.pos < self.length and (self._peek().isalpha() or self._peek() == "_"):
            # Consume the identifier characters to highlight the full illegal token
            illegal_part = ""
            while self.pos < self.length and (self._peek().isalnum() or self._peek() == "_"):
                illegal_part += self._advance()
            full_literal = num_str + illegal_part
            self.errors.append(
                LexicalError(
                    message=f"Invalid literal '{full_literal}': identifiers cannot begin with numbers.",
                    line=start_line,
                    column=start_col,
                    suggestion=f"Separate the number and variable (e.g., '{num_str} * {illegal_part}') or rename the identifier."
                )
            )
            return

        # Successfully parsed number
        parsed_val = float(num_str) if has_dot else int(num_str)
        self.tokens.append(
            Token(TOKEN_NUMBER, num_str, start_line, start_col, value=parsed_val)
        )

    def _scan_identifier(self, start_line: int, start_col: int):
        """Scans an identifier: starts with letter or _, followed by letters, digits, or _."""
        ident_str = ""
        while self.pos < self.length:
            ch = self._peek()
            if ch.isalnum() or ch == "_":
                ident_str += self._advance()
            else:
                break

        # LexiTree has no reserved keywords in this version
        self.tokens.append(
            Token(TOKEN_IDENTIFIER, ident_str, start_line, start_col, value=ident_str)
        )
