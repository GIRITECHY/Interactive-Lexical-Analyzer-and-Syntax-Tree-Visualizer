"""
app.py - Flask Web Application for LexiTree

Provides local HTTP endpoints for:
- GET /              : Serves the interactive user interface.
- POST /api/analyze  : Analyzes submitted source code (lexical analysis + syntax parsing +
                       AST generation + Concrete Parse Tree generation + Three-Address Code generation).

Constraints:
- Binds strictly to 127.0.0.1:5000 (offline local use only).
- Enforces source code payload size limit.
- Separates compiler logic from Flask routing.
- Returns structured JSON responses without exposing raw Python tracebacks.
"""

import sys
from flask import Flask, request, jsonify, render_template
from lexer import Lexer
from parser import Parser, ParserError
from intermediate_code import TACGenerator

app = Flask(__name__)

# Maximum allowed source code size: 64 KB
MAX_SOURCE_SIZE = 64 * 1024


@app.route("/", methods=["GET"])
def index():
    """Serves the main single-page application interface."""
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Analyzes submitted source code.
    
    Request JSON:
        { "source_code": "x = 10;" }

    Response JSON:
        {
            "success": bool,
            "tokens": [ { "type": "...", "lexeme": "...", "line": 1, "column": 1, "value": ... }, ... ],
            "lexical_errors": [ { "message": "...", "line": 1, "column": 1, "suggestion": "..." }, ... ],
            "syntax_error": { "message": "...", "line": 1, "column": 1, "suggestion": "..." } or None,
            "ast": { "type": "Program", "statements": [ ... ] } or None,
            "parse_tree": { "symbol": "program", "label": "program", "kind": "nonterminal", "children": [ ... ] } or None,
            "intermediate_code": [ "t1 = ...", ... ]
        }
    """
    if not request.is_json:
        return jsonify({
            "success": False,
            "tokens": [],
            "lexical_errors": [],
            "syntax_error": {
                "message": "Invalid request: Content-Type must be application/json.",
                "line": 1,
                "column": 1,
                "suggestion": "Send request as JSON containing a 'source_code' field."
            },
            "ast": None,
            "parse_tree": None,
            "intermediate_code": []
        }), 400

    data = request.get_json(silent=True) or {}
    source_code = data.get("source_code", "")

    if not isinstance(source_code, str):
        return jsonify({
            "success": False,
            "tokens": [],
            "lexical_errors": [],
            "syntax_error": {
                "message": "Field 'source_code' must be a string.",
                "line": 1,
                "column": 1,
                "suggestion": "Check request payload format."
            },
            "ast": None,
            "parse_tree": None,
            "intermediate_code": []
        }), 400

    if len(source_code.encode("utf-8")) > MAX_SOURCE_SIZE:
        return jsonify({
            "success": False,
            "tokens": [],
            "lexical_errors": [],
            "syntax_error": {
                "message": f"Source code exceeds maximum allowed size of {MAX_SOURCE_SIZE // 1024} KB.",
                "line": 1,
                "column": 1,
                "suggestion": "Reduce source code size before analyzing."
            },
            "ast": None,
            "parse_tree": None,
            "intermediate_code": []
        }), 400

    try:
        # Phase 1: Lexical Analysis
        lexer = Lexer(source_code)
        tokens, lexical_errors = lexer.tokenize()
        token_dicts = [t.to_dict() for t in tokens]
        lex_err_dicts = [e.to_dict() for e in lexical_errors]

        # If lexical errors are found, return tokens and lexical errors without proceeding to parse
        if lexical_errors:
            return jsonify({
                "success": False,
                "tokens": token_dicts,
                "lexical_errors": lex_err_dicts,
                "syntax_error": None,
                "ast": None,
                "parse_tree": None,
                "intermediate_code": []
            })

        # Phase 2: Syntax Analysis, AST Construction & Parse Tree Construction
        parser = Parser(tokens)
        ast = parser.parse()
        parse_tree = parser.parse_tree

        # Phase 3: Intermediate Code Generation (Three-Address Code)
        tac_generator = TACGenerator()
        intermediate_code = tac_generator.generate(ast)

        return jsonify({
            "success": True,
            "tokens": token_dicts,
            "lexical_errors": [],
            "syntax_error": None,
            "ast": ast.to_dict(),
            "parse_tree": parse_tree.to_dict() if parse_tree else None,
            "intermediate_code": intermediate_code
        })

    except ParserError as pe:
        return jsonify({
            "success": False,
            "tokens": token_dicts,
            "lexical_errors": [],
            "syntax_error": pe.to_dict(),
            "ast": None,
            "parse_tree": None,
            "intermediate_code": []
        })

    except Exception as ex:
        # Graceful fallback without exposing internal stack traces
        return jsonify({
            "success": False,
            "tokens": [],
            "lexical_errors": [],
            "syntax_error": {
                "message": f"An unexpected analysis error occurred: {str(ex)}",
                "line": 1,
                "column": 1,
                "suggestion": "Verify program syntax or re-try with valid expressions."
            },
            "ast": None,
            "parse_tree": None,
            "intermediate_code": []
        }), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  LexiTree - Interactive Lexical Analyzer & Syntax Tree Visualizer")
    print("  Running locally on http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
