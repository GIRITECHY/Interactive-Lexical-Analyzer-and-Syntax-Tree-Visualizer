# LexiTree – Interactive Lexical Analyzer & Syntax Tree Visualizer

A clean, modern, educational Compiler Design web application demonstrating **Lexical Analysis (Tokenization)**, **Recursive-Descent Syntax Analysis (Parsing)**, **Abstract Syntax Tree (AST) Construction**, and **Compiler Error Diagnostics**.

Designed specifically for college academic submissions, viva voce examinations, and practical compiler design demonstrations.

---

## 1. Project Abstract

**LexiTree** bridges theoretical compiler concepts and visual understanding. It ingests source code from an interactive editor, passes it through a custom-built Python lexical analyzer to extract tokens, parses the token stream using a predictive recursive-descent parser adhering to a context-free grammar, and dynamically constructs an Abstract Syntax Tree (AST). The generated AST is serialized to JSON and rendered natively in the browser as an interactive, non-overlapping SVG tree without relying on any third-party graph or compiler libraries.

---

## 2. Objectives

- Demystify the front-end phases of a compiler for students and educators.
- Demonstrate token classification, position tracking (line and column), and error recovery.
- Implement an unambiguous context-free grammar with strict operator precedence and associativity.
- Construct a logical Abstract Syntax Tree (AST) free from syntactic punctuation.
- Deliver an offline, standalone web interface with blue/indigo accents, smooth SVG tree rendering, and rich compiler error suggestions.

---

## 3. Problem Statement

Theoretical compiler design courses frequently teach lexical analysis (regular expressions, finite automata) and syntax analysis (CFGs, derivation trees, LL/LR parsing) using abstract mathematical notation. Students often struggle to visualize:
1. How individual characters transition into classified lexical tokens with exact line and column tracking.
2. How grammar rules and operator precedence dictate the hierarchical structure of expressions.
3. How syntax errors (e.g., missing operands, unbalanced parentheses, unclosed statements) are detected and localized.
4. How an Abstract Syntax Tree differs from a concrete parse tree.

Existing compiler visualization tools often rely on complex external dependencies (D3, Graphviz, external CLIs) or operate as black boxes, making them difficult to run offline on local Windows machines or explain during an academic viva.

---

## 4. Proposed Solution

**LexiTree** solves this by providing an end-to-end, zero-complex-dependency compiler simulation:
- **Zero Third-Party Compiler Libraries:** The scanner (`lexer.py`) and parser (`parser.py`) are handcrafted from scratch using pure Python.
- **Zero Third-Party Visualization Libraries:** The SVG visualizer (`ast-visualizer.js`) uses native browser DOM and SVG APIs with a deterministic subtree layout algorithm that prevents overlapping nodes.
- **Offline & Local Execution:** Runs locally via a lightweight Flask server on `127.0.0.1:5000` with no cloud APIs, database, or internet connectivity required.
- **Interactive Feedback:** Real-time token tables, actionable error suggestions, and node inspection.

---

## 5. Core Features

- **Source Code Editor:**
  - Multiline editor with synchronized line numbering.
  - Character and line counter.
  - Tab indentation support (4 spaces).
  - One-click clear and sample program loader.
- **Custom Lexical Analyzer (`lexer.py`):**
  - Tokenizes Identifiers, Numeric Constants (integers and decimals), Arithmetic Operators (`+`, `-`, `*`, `/`), Assignment (`=`), and Delimiters (`(`, `)`, `;`).
  - Tracks 1-based line and column positions across newlines.
  - Gracefully captures invalid characters and malformed numbers without crashing.
  - Emits `<EOF>` token for the parser.
- **Token Analysis Table:**
  - Displays Token #, Lexeme, Token Type (color-coded badge), Line, and Column.
  - Live search/filtering by lexeme or token type.
  - Remains visible even if syntax parsing fails.
- **Custom Recursive-Descent Parser (`parser.py`):**
  - Implements an unambiguous grammar supporting variable assignments and arithmetic expressions.
  - Operator precedence: Parentheses > Unary (`+`, `-`) > Multiplicative (`*`, `/`) > Additive (`+`, `-`).
  - Left-associativity for binary operators; right-associativity for unary operators.
- **Abstract Syntax Tree (AST):**
  - Object-oriented node hierarchy (`Program`, `Assignment`, `BinaryOp`, `UnaryOp`, `Number`, `Identifier`).
  - Serializes to standard JSON for visualization.
- **Custom SVG AST Visualizer (`ast-visualizer.js`):**
  - Pure SVG hierarchical tree layout arranged from top to bottom.
  - Proportional subtree layout guaranteeing zero node overlap.
  - Color-coded rectangular nodes per grammatical construct.
  - Zoom In, Zoom Out, Reset, and click-and-drag Canvas Panning.
  - Interactive Node Inspector: hover or click on any node to view its syntactic details.
- **Educational Compiler Error Diagnostics:**
  - Distinct classification between **Lexical Errors** and **Syntax Errors**.
  - Pinpoints line and column location with an actionable recommendation.

---

## 6. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.12, Flask | Lightweight HTTP routing and REST API (`/api/analyze`) |
| **Lexer** | Pure Python (`lexer.py`) | Hand-crafted deterministic scanner |
| **Parser** | Pure Python (`parser.py`) | Hand-crafted recursive-descent parser |
| **AST Model** | Pure Python (`ast_nodes.py`) | Structural tree classes and JSON serialization |
| **Testing** | Python `unittest` | Automated regression test suite |
| **Frontend UI** | HTML5, CSS3 | Clean, modern light theme with Indigo accents |
| **Visualizer** | Vanilla JavaScript & SVG | Native mathematical tree layout and SVG rendering |

---

## 7. Folder Structure

```text
CD MY PROJECT/
├── app.py                  # Flask server and REST API endpoints
├── lexer.py                # Custom Lexical Analyzer (Tokenizer)
├── parser.py               # Custom Recursive-Descent Parser
├── ast_nodes.py            # AST Node definitions (Program, Assignment, etc.)
├── requirements.txt        # Single dependency: Flask
├── README.md               # Complete academic documentation & viva guide
├── .gitignore              # Ignores virtual environment and python cache
├── templates/
│   └── index.html          # Single-page web application UI
├── static/
│   ├── css/
│   │   └── style.css       # Clean responsive styles and SVG tree styling
│   └── js/
│       ├── app.js          # Client orchestrator and API caller
│       ├── editor.js       # Line numbering, presets, and editor shortcuts
│       └── ast-visualizer.js # Custom SVG tree layout algorithm and zoom/pan
└── tests/
    ├── test_lexer.py       # Unit tests for tokenization & lexical error handling
    └── test_parser.py      # Unit tests for grammar rules, precedence, & AST
```

---

## 8. Supported Grammar Specification

The syntax analyzer strictly implements the following formal context-free grammar (CFG) in EBNF notation:

```text
program     -> statement*
statement   -> IDENTIFIER "=" expression ";"
expression  -> term (("+" | "-") term)*
term        -> unary (("*" | "/") unary)*
unary       -> ("+" | "-") unary | primary
primary     -> NUMBER | IDENTIFIER | "(" expression ")"
```

### Precedence & Associativity Table

| Precedence | Level | Operators | Associativity | Grammar Rule |
|:---:|:---:|:---:|:---:|:---|
| **1 (Highest)** | Parentheses | `( ... )` | Non-associative | `primary` |
| **2** | Unary Operators | `+`, `-` | Right-to-Left (Prefix) | `unary` |
| **3** | Multiplication / Division | `*`, `/` | Left-to-Right | `term` |
| **4 (Lowest)** | Addition / Subtraction | `+`, `-` | Left-to-Right | `expression` |

---

## 9. Lexer Implementation (`lexer.py`)

The lexer reads the raw input character by character:
1. **Whitespace Handling:** Spaces, tabs (`\t`), and carriage returns (`\r`) increment the column counter. Newline characters (`\n`) increment the line counter and reset the column counter to `1`.
2. **Numeric Constants:** Scans contiguous digits. If a decimal point (`.`) is encountered, checks that it is followed by digits. Malformed numbers such as `12.34.56` (multiple dots) or `12.` (trailing dot without digits) generate structured `LexicalError` objects.
3. **Identifiers:** Matches `[a-zA-Z_][a-zA-Z0-9_]*`. Note that LexiTree has no reserved keywords in this version; all alphanumeric names function as variable identifiers.
4. **Delimiters & Operators:** Individual symbols (`+`, `-`, `*`, `/`, `=`, `(`, `)`, `;`) are immediately matched and tagged with their exact 1-based start positions.
5. **Error Resilience:** When an illegal character (such as `@` or `$`) is encountered, the scanner records an error with line, column, and suggestion, then continues scanning subsequent characters so valid tokens are still presented to the user.

---

## 10. Parser Implementation (`parser.py`)

The recursive-descent parser consumes the token stream produced by the lexer:
- **Top-Down Predictive Parsing:** Each non-terminal in the grammar corresponds to a distinct method (`_statement`, `_expression`, `_term`, `_unary`, `_primary`).
- **No Backtracking:** The parser makes deterministic decisions based on the current token lookahead (`_peek()` and `_match()`).
- **Associativity by Iteration:** Left-associative binary operations (`+`, `-`, `*`, `/`) are parsed using `while` loops that bundle left operands into the `left` subtree of a new `BinaryOp` node.
- **Prefix Unary by Recursion:** Right-associative unary operations (`+`, `-`) recursively call `_unary()`.

---

## 11. Abstract Syntax Tree (AST) Explanation

The AST captures the **semantic essence** of the code, omitting syntactic noise like punctuation, parentheses, and semicolons.

For example, given:
```text
result = 2 + 3 * 4;
```

The logical tree constructed is:
```text
Assignment
├── Identifier: result
└── BinaryOp: +
    ├── Number: 2
    └── BinaryOp: *
        ├── Number: 3
        └── Number: 4
```

Notice:
- `3 * 4` sits lower in the tree than `+`, ensuring that multiplication evaluates before addition.
- In `(2 + 3) * 4`, parentheses force `2 + 3` into the subtree of `*`, accurately overriding default precedence.

---

## 12. Error Handling & Diagnostics

LexiTree classifies errors into two distinct categories:

| Error Category | Example Input | Detected Diagnostic | Actionable Suggestion |
|---|---|---|---|
| **Lexical Error** | `x = 10 @ 2;` | `Invalid character '@' found.` | `Remove this character. LexiTree supports letters, digits, underscores, operators (+, -, *, /), '=', and delimiters (;, (, )).` |
| **Lexical Error** | `val = 12.34.56;` | `Malformed numeric constant '12.34.56': multiple decimal points.` | `Ensure numbers have at most one decimal point (e.g., '3.14').` |
| **Syntax Error** | `x = 10 + ;` | `Missing operand before ';'.` | `Provide a valid number, variable, or parenthesized sub-expression after the operator.` |
| **Syntax Error** | `x = 10` | `Missing semicolon ';' after statement, found '<EOF>'.` | `Add a trailing semicolon ';' to terminate the statement.` |
| **Syntax Error** | `x = (10 + 5;` | `Unmatched opening parenthesis '(' from line 1, col 5.` | `Add a closing parenthesis ')' to properly close the sub-expression.` |
| **Syntax Error** | `x = 10 + 5);` | `Unmatched closing parenthesis ')' at line 1, col 11.` | `Remove the extraneous ')' or add a matching opening parenthesis '('.` |
| **Syntax Error** | `10 = 5;` | `Cannot assign to a numeric constant '10'.` | `Assignments must start with a variable identifier on the left-hand side (e.g., 'x = 10;').` |

---

## 13. Windows Installation & Execution Guide

### Prerequisites
- Windows 10 or Windows 11.
- Python 3.10+ installed.

### Step 1: Open PowerShell
Open Windows PowerShell and navigate to the project directory:
```powershell
cd "c:\Users\girig\Desktop\CD MY PROJECT"
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
> **Note on PowerShell Script Execution Policy:**
> If PowerShell displays an execution policy error, run this command once to permit local script execution:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> *Alternative:* You can run Python directly from the virtual environment without activating:
> ```powershell
> .\.venv\Scripts\python.exe app.py
> ```

### Step 4: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 5: Start the Application
```powershell
python app.py
```
Or directly:
```powershell
.\.venv\Scripts\python.exe app.py
```

### Step 6: Open in Browser
Open your favorite web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 14. Automated Unit Testing

LexiTree includes 21 automated unit tests covering both the lexical analyzer and recursive-descent parser.

To run the complete test suite:
```powershell
python -m unittest discover -s tests -v
```
Or using the virtual environment interpreter:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Test Coverage Highlights:
- Token recognition for all symbols and delimiters.
- Accurate line and column positioning across multiline scripts.
- Detection of invalid characters (`@`, `$`) and malformed floats.
- Correct AST construction for simple and multiple statements.
- Strict validation of operator precedence (`*` over `+`).
- Parenthesis grouping and precedence override.
- Left-associativity validation (`10 - 5 - 2`).
- Prefix unary operator evaluation (`x = -5; y = -(x + 3);`).
- Syntax error assertions for missing semicolons, missing operands, and unbalanced parentheses.

---

## 15. Example Inputs & Demonstrations

### Example 1: Operator Precedence
**Input:**
```text
result = 2 + 3 * 4;
```
**Outcome:**
`3 * 4` is grouped inside a child `BinaryOp(*)` node, and added to `2`.

### Example 2: Parentheses Override
**Input:**
```text
result = (2 + 3) * 4;
```
**Outcome:**
`2 + 3` forms a `BinaryOp(+)` node, which becomes the left child of `BinaryOp(*)`.

### Example 3: Multiple Statements
**Input:**
```text
a = 10;
b = 20;
total = a + b;
```
**Outcome:**
A `Program` root node containing three child `Assignment` subtrees.

### Example 4: Unary Operators
**Input:**
```text
x = -5;
y = -(x + 3);
```
**Outcome:**
Renders `UnaryOp(-)` applied directly to constant `5` and parenthesized expression `(x + 3)`.

---

## 16. College Viva Questions & Answers

### Q1: What are the phases of a classical compiler?
**Ans:** 
1. **Lexical Analysis (Scanner):** Converts characters into tokens.
2. **Syntax Analysis (Parser):** Verifies tokens against grammar and creates a Parse Tree / AST.
3. **Semantic Analysis:** Checks type consistency and variable declarations.
4. **Intermediate Code Generation (ICG):** Produces Three-Address Code (TAC) or quadruples.
5. **Code Optimization:** Improves execution speed or reduces memory footprint.
6. **Target Code Generation:** Produces assembly or machine code.
7. **Symbol Table & Error Handler:** Active across all phases.

### Q2: What is the difference between a Token, a Lexeme, and a Pattern?
**Ans:**
- **Lexeme:** The actual sequence of characters in the source code (e.g., `count`, `3.14`, `+`).
- **Token:** The classified category or tuple containing token type and attribute value (e.g., `<IDENTIFIER, "count">`, `<NUMBER, 3.14>`).
- **Pattern:** The descriptive rule (often a regular expression) that describes what forms a token can take (e.g., `[a-zA-Z_][a-zA-Z0-9_]*`).

### Q3: What is the difference between a Parse Tree and an Abstract Syntax Tree (AST)?
**Ans:**
A **Parse Tree (Concrete Syntax Tree)** represents every syntactic derivation step of the grammar, retaining delimiters like `;` and parentheses `( )`. An **Abstract Syntax Tree (AST)** is a condensed, semantic representation containing only operands and operators, discarding unnecessary punctuation.

### Q4: What is a Context-Free Grammar (CFG)?
**Ans:**
A CFG is a 4-tuple $G = (V_N, V_T, P, S)$ where:
- $V_N$: Set of non-terminal symbols.
- $V_T$: Set of terminal symbols (tokens).
- $P$: Production rules of the form $A \to \alpha$, where $A \in V_N$ and $\alpha \in (V_N \cup V_T)^*$.
- $S$: Start symbol ($S \in V_N$).

### Q5: Why is left-recursion problematic for top-down recursive-descent parsers?
**Ans:**
A production rule of the form $A \to A \alpha$ causes a recursive-descent parser to call the function for $A$ infinitely without consuming any input token, resulting in a stack overflow. In LexiTree, left-recursion is eliminated by rewriting rules iteratively: `expression -> term (("+" | "-") term)*`.

### Q6: How does the parser enforce operator precedence?
**Ans:**
By structuring the grammar in hierarchical layers. Operators with lower precedence (e.g., `+`, `-`) are placed higher up in the grammar call hierarchy (`_expression()`), while operators with higher precedence (e.g., `*`, `/`) are placed lower down (`_term()`). Because `_expression` calls `_term`, multiplication binds more tightly than addition.

---

## 17. Limitations & Future Enhancements

### Current Limitations:
- The mini-language supports variable assignments and arithmetic expressions, but does not yet include control flow (`if`/`else`, `while`).
- Type system is limited to integer and floating-point numeric evaluation.

### Future Enhancements:
- **Symbol Table Inspector:** Add a visual table tracking variable scopes, types, and assigned memory values.
- **Three-Address Code (TAC) Generator:** Add an Intermediate Code Generation tab to display generated TAC instructions (e.g., `t1 = 3 * 4; t2 = 2 + t1; result = t2;`).
- **Bytecode Virtual Machine:** A simple stack-based VM to execute the generated AST and display runtime evaluation step-by-step.

---

## 18. College Demonstration Guide

When presenting LexiTree to an evaluator or teacher:
1. **Show the Clean Architecture:**
   - Open `lexer.py` to explain regular character scanning and token classification.
   - Open `parser.py` to explain the recursive-descent functions matching the CFG grammar rules.
2. **Demonstrate Automated Testing:**
   - Run `python -m unittest discover -s tests -v` in the terminal to show that all 21 test cases pass.
3. **Interactive Visual Demo in Browser:**
   - Launch `python app.py` and navigate to `http://127.0.0.1:5000`.
   - Select **Preset 2 (Operator Precedence)** to show how `*` nests under `+`.
   - Select **Preset 3 (Parenthesized Expression)** to show how `(2 + 3)` moves `+` below `*`.
   - Select **Preset 4 (Multiple Statements)** to demonstrate multi-assignment program AST generation.
   - Select **Preset 6 (Missing Operand)** or **Preset 7 (Missing Semicolon)** to demonstrate accurate error line/column tracking and recommendation suggestions.
4. **Open the Viva Guide Modal:**
   - Click the **Viva Guide** button in the top right to walk through formal CFG definitions and standard viva answers directly from the UI.
