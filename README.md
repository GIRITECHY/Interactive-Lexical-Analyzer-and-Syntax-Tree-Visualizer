# LexiTree – Interactive Compiler Design System

> **A Comprehensive Educational Compiler Suite**  
> Demonstrating Lexical Analysis (Scanning), Recursive-Descent Syntax Analysis, Concrete Parse Tree (CST) Visualization, Abstract Syntax Tree (AST) Construction, and Three-Address Code (TAC) Intermediate Code Generation.

---

## Table of Contents

1. [Project Overview & Capabilities](#1-project-overview--capabilities)
   - [Core Purpose](#core-purpose)
   - [5-Phase Compiler Pipeline](#5-phase-compiler-pipeline)
   - [Key Technical Features](#key-technical-features)
2. [Parse Tree vs. Abstract Syntax Tree (AST)](#2-parse-tree-vs-abstract-syntax-tree-ast)
   - [Conceptual Comparison Table](#conceptual-comparison-table)
   - [Grammar Structure & Derivation](#grammar-structure--derivation)
3. [Three-Address Code (TAC) Intermediate Representation](#3-three-address-code-tac-intermediate-representation)
   - [What is Three-Address Code?](#what-is-three-address-code)
   - [Evaluation Rules & Temporary Generation](#evaluation-rules--temporary-generation)
   - [Representative TAC Examples](#representative-tac-examples)
4. [How to Use the Application (Interactive User Manual)](#4-how-to-use-the-application-interactive-user-manual)
   - [Step 1: Accessing the Interface](#step-1-accessing-the-interface)
   - [Step 2: Editing Code & Using Presets](#step-2-editing-code--using-presets)
   - [Step 3: Analyzing Source Code](#step-3-analyzing-source-code)
   - [Step 4: Token Table Inspection](#step-4-token-table-inspection)
   - [Step 5: Toggling Syntax Tree Views (AST vs. CST)](#step-5-toggling-syntax-tree-views-ast-vs-cst)
   - [Step 6: Inspecting & Copying Three-Address Code](#step-6-inspecting--copying-three-address-code)
   - [Step 7: Compiler Error Diagnostics & Suggestions](#step-7-compiler-error-diagnostics--suggestions)
   - [Step 8: In-App Viva Reference Guide](#step-8-in-app-viva-reference-guide)
5. [Language Grammar Specification](#5-language-grammar-specification)
   - [Formal Context-Free Grammar (CFG)](#formal-context-free-grammar-cfg)
   - [Operator Precedence & Associativity](#operator-precedence--associativity)
6. [Compiler Engine Architecture & Implementation](#6-compiler-engine-architecture--implementation)
   - [Lexical Scanner (`lexer.py`)](#lexical-scanner-lexerpy)
   - [Recursive-Descent Parser (`parser.py`)](#recursive-descent-parser-parserpy)
   - [Parse Tree Representation (`parse_tree.py`)](#parse-tree-representation-parse_treepy)
   - [AST Representation (`ast_nodes.py`)](#ast-representation-ast_nodespy)
   - [Three-Address Code Generator (`intermediate_code.py`)](#three-address-code-generator-intermediate_codepy)
   - [Native SVG Visualizers (`ast-visualizer.js` & `parse-tree-visualizer.js`)](#native-svg-visualizers)
7. [Installation & Local Execution Guide](#7-installation--local-execution-guide)
   - [System Prerequisites](#system-prerequisites)
   - [Windows PowerShell Execution](#windows-powershell-execution)
   - [macOS / Linux Execution](#macos--linux-execution)
8. [Testing and Validation](#8-testing-and-validation)
   - [A. Automated Test Results](#a-automated-test-results)
   - [B. Chrome Browser Validation](#b-chrome-browser-validation)
   - [C. Test Case Results Matrix](#c-test-case-results-matrix)
   - [D. Bugs Discovered & Fixed](#d-bugs-discovered--fixed)
   - [E. Remaining Limitations](#e-remaining-limitations)
   - [F. How to Rerun Tests](#f-how-to-rerun-tests)
   - [G. Final Demonstration Example](#g-final-demonstration-example)
9. [REST API Documentation](#9-rest-api-documentation)
   - [`POST /api/analyze`](#post-apianalyze)
10. [Annotated Project Directory Structure](#10-annotated-project-directory-structure)
11. [College Viva Voce Q&A Reference](#11-college-viva-voce-qa-reference)
12. [Demonstration Script for Academic Evaluators](#12-demonstration-script-for-academic-evaluators)

---

## 1. Project Overview & Capabilities

### Core Purpose
**LexiTree** is an interactive, zero-external-compiler-dependency educational web application designed for compiler design laboratory coursework, viva voce examinations, and classroom demonstrations. It bridges abstract compiler theory and tangible visual understanding by executing every front-end and intermediate phase of a compiler in real time:

1. **Scanning (Lexical Analysis)** with exact 1-based character position tracking.
2. **Parsing (Syntax Analysis)** via a predictive recursive-descent parser.
3. **Parse Tree Generation (Concrete Syntax Tree - CST)** showing every grammatical expansion step and punctuation mark.
4. **Abstract Syntax Tree (AST)** construction condensing syntactic noise into semantic operations.
5. **Intermediate Code Generation** synthesizing **Three-Address Code (TAC)** instructions with deterministic temporaries.

---

### 5-Phase Compiler Pipeline

```text
┌─────────────────┐
│   Source Code   │ (Multistatement variable assignments and arithmetic expressions)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Lexical Scanner │ (lexer.py: character lookahead, token classification, position tracking)
└────────┬────────┘
         │  Tokens: [IDENTIFIER, ASSIGN, NUMBER, PLUS, STAR, SEMICOLON, EOF]
         ▼
┌─────────────────┐
│ Recursive-      ├───────────────────────────────┐
│ Descent Parser  │                               │
└────────┬────────┘                               ▼
         │                              ┌───────────────────┐
         │ (Simultaneous CST & AST)      │ Concrete Parse    │ (parse_tree.py: nonterminals,
         │                              │ Tree (CST)        │  terminals, rules, punctuation)
         ▼                              └─────────┬─────────┘
┌─────────────────┐                               │
│ Abstract Syntax │ (ast_nodes.py: Program,       │
│ Tree (AST)      │  Assignment, BinaryOp, etc.)  │
└────────┬────────┘                               │
         │                                        ▼
         ├───────────────────────────────>┌───────────────────┐
         │                                │ Native SVG Engine │ (Non-overlapping 2-pass
         ▼                                │ (Browser Canvas)  │  layout, zoom, pan, inspect)
┌─────────────────┐                       └───────────────────┘
│ Three-Address   │ (intermediate_code.py: AST traversal,
│ Code Generator  │  deterministic temporary allocation: t1, t2, ...)
└────────┬────────┘
         │  TAC: ["t1 = 3 * 4", "t2 = 2 + t1", "result = t2"]
         ▼
┌─────────────────┐
│ Monospace TAC   │ (Copyable instructions with line markers)
│ Panel           │
└─────────────────┘
```

---

### Key Technical Features

- **Pure Handwritten Compiler Phases:** Built strictly without compiler generator packages (no Lex, Yacc, PLY, ANTLR, or PyParsing) to ensure 100% transparent code suitable for viva explanation.
- **Native Browser SVG Engine:** Visualizes both AST and CST using standard browser DOM and SVG APIs without D3.js or Graphviz.
- **Dual Syntax Tree Views:** Instant tabbed switching between Abstract Syntax Tree and Concrete Parse Tree.
- **Real-Time TAC Synthesis:** Transforms high-level nested AST arithmetic expressions into linear intermediate instructions (`t1`, `t2`, ...).
- **Graceful Error Localization:** Pinpoints lexical anomalies (unrecognized characters, malformed numbers) and syntax violations (missing semicolons, unmatched parentheses, dangling operators) with actionable fixes.
- **Completely Offline:** Runs locally on `http://127.0.0.1:5000` with zero internet or cloud dependencies.

---

## 2. Parse Tree vs. Abstract Syntax Tree (AST)

A fundamental concept in compiler design is the architectural distinction between a **Concrete Syntax Tree (Parse Tree)** and an **Abstract Syntax Tree (AST)**. LexiTree visualizes both side-by-side.

### Conceptual Comparison Table

| Dimension | Concrete Parse Tree (CST) | Abstract Syntax Tree (AST) |
|---|---|---|
| **Definition** | Complete graphical representation of the formal grammar derivation steps. | Condensed semantic representation of the computation to be performed. |
| **Syntactic Noise** | Retains all delimiters, parentheses, semicolons, and assignment symbols (`=`, `;`, `(`, `)`). | Strips away all syntactic delimiters and punctuation; parentheses are represented implicitly by tree depth. |
| **Node Types** | Non-terminals (`program`, `statement`, `expression`, `term`, `unary`, `primary`) and terminals (`IDENTIFIER`, `NUMBER`, `PLUS`, etc.). | Object-oriented construct nodes (`Program`, `Assignment`, `BinaryOp`, `UnaryOp`, `Number`, `Identifier`). |
| **Purpose** | Verifies grammatical correctness according to formal language productions. | Serves as the primary data structure for semantic analysis, optimization, and code generation. |
| **Size & Density** | Significantly larger and deeper due to intermediate non-terminal chains (`expression -> term -> unary -> primary`). | Compact, direct, and memory-efficient. |

---

### Grammar Structure & Derivation

Given the input:
```text
result = (2 + 3) * 4;
```

#### 1. Concrete Parse Tree Structure (Grammar Derivation):
```text
program
└── statement (statement -> IDENTIFIER = expression ;)
    ├── IDENTIFIER: result
    ├── ASSIGN: =
    ├── expression (expression -> term)
    │   └── term (term -> unary * unary)
    │       ├── unary (unary -> primary)
    │       │   └── primary (primary -> ( expression ))
    │       │       ├── LPAREN: (
    │       │       ├── expression (expression -> term + term)
    │       │       │   ├── term -> unary -> primary -> NUMBER: 2
    │       │       │   ├── PLUS: +
    │       │       │   └── term -> unary -> primary -> NUMBER: 3
    │       │       └── RPAREN: )
    │       ├── STAR: *
    │       └── unary -> primary -> NUMBER: 4
    └── SEMICOLON: ;
```

#### 2. Abstract Syntax Tree Structure (Semantic Core):
```text
Assignment
├── Identifier: result
└── BinaryOp: *
    ├── BinaryOp: +
    │   ├── Number: 2
    │   └── Number: 3
    └── Number: 4
```

---

## 3. Three-Address Code (TAC) Intermediate Representation

### What is Three-Address Code?
**Three-Address Code (TAC)** is a linearized intermediate representation (IR) utilized in optimizing compilers. In TAC, each statement contains at most one operator and at most three address locations: two source operand addresses and one destination address.

General forms supported:
- Binary operation: `x = y op z`
- Unary operation: `x = -y`
- Direct assignment: `x = y`

---

### Evaluation Rules & Temporary Generation

1. **AST Traversal:** The `TACGenerator` performs a post-order traversal over the validated AST.
2. **Deterministic Temporaries:** Generates temporary identifiers `t1`, `t2`, `t3`, ... in sequential evaluation order.
3. **Counter Isolation:** The temporary numbering resets automatically at the start of each independent compilation pass.
4. **Left-to-Right Binary Evaluation:** Evaluates the left operand first, then the right operand, and emits a temporary assignment for the operator.
5. **Unary Operation Optimization:**
   - Unary minus (`-x`) emits `t{n} = -x`.
   - Unary plus (`+x`) retains the operand value directly without emitting an unnecessary temporary copy.
6. **Literal Preservation:** Numeric literals preserve their exact source formatting, preventing floating-point precision distortion.

---

### Representative TAC Examples

#### Example 1: Arithmetic Operator Precedence
**Source Code:**
```text
a = b + c * d;
```
**Generated TAC:**
```text
t1 = c * d
t2 = b + t1
a = t2
```

#### Example 2: Multiplication with Literal Constants
**Source Code:**
```text
result = 2 + 3 * 4;
```
**Generated TAC:**
```text
t1 = 3 * 4
t2 = 2 + t1
result = t2
```

#### Example 3: Parentheses Overriding Precedence
**Source Code:**
```text
result = (2 + 3) * 4;
```
**Generated TAC:**
```text
t1 = 2 + 3
t2 = t1 * 4
result = t2
```

#### Example 4: Unary Negation and Nested Expressions
**Source Code:**
```text
x = -5;
y = -(x + 3);
```
**Generated TAC:**
```text
t1 = -5
x = t1
t2 = x + 3
t3 = -t2
y = t3
```

#### Example 5: Multiple Assignment Statements
**Source Code:**
```text
a = b + c * d;
x = a - 5;
```
**Generated TAC:**
```text
t1 = c * d
t2 = b + t1
a = t2
t3 = a - 5
x = t3
```

---

## 4. How to Use the Application (Interactive User Manual)

### Step 1: Accessing the Interface
1. Launch the local web server (see [Installation & Local Execution Guide](#7-installation--local-execution-guide)).
2. Open your web browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```
3. The interface displays a responsive dual-column workbench:
   - **Left Panel:** Multiline Code Editor & Token Analysis Table.
   - **Right Panel:** Tabbed Tree Visualizer (AST / Parse Tree) & Three-Address Code Panel.

---

### Step 2: Editing Code & Using Presets
- **Custom Code Input:** Write variable assignment statements terminated by semicolons (e.g., `rate = 3.14 * (radius * radius);`).
- **Tab Indentation:** Pressing `Tab` inserts 4 spaces.
- **Synchronized Line Numbers:** Left gutter tracks cursor position and scroll offsets.
- **Example Presets Dropdown:** Select from pre-built programs illustrating operator precedence, parenthesization, unary minus, or deliberate syntax errors.
- **Quick Load Chips:** Click any chip (`2 + 3 * 4`, `(2 + 3) * 4`, `Multi-Statement`, `-(x + 3)`, `Missing ;`, `Invalid @`) for instant one-click execution.

---

### Step 3: Analyzing Source Code
1. Click the blue **Analyze Code** button in the editor footer.
2. The status indicator in the top header transitions to **Processing...** and then **Analysis Successful**.
3. All four analytical views update simultaneously:
   - Token Table
   - Abstract Syntax Tree (AST)
   - Concrete Parse Tree (CST)
   - Three-Address Code (TAC)

---

### Step 4: Token Table Inspection
The lower-left card displays all recognized lexical tokens:
- **Index (#):** Sequential token position.
- **Lexeme:** Literal character sequence (e.g., `result`, `=`, `42`, `<EOF>`).
- **Token Type:** Color-coded badges (`IDENTIFIER`, `NUMBER`, `PLUS`, `STAR`, `ASSIGN`, `SEMICOLON`, etc.).
- **Line & Column:** Exact source coordinates.
- **Live Search Filter:** Type in the search box to filter tokens in real time (e.g., filter by `NUMBER` or `*`).

---

### Step 5: Toggling Syntax Tree Views (AST vs. CST)
At the top of the tree visualizer card, click the view tabs to switch between trees:
- **Abstract Syntax Tree (AST):** Displays concise semantic operation nodes (`Assignment`, `BinaryOp`, `Number`, `Identifier`).
- **Parse Tree (CST):** Displays the full derivation tree distinguishing **Non-Terminals** (lavender cards with grammar symbols) and **Terminals** (emerald pills with exact lexemes).

#### Interactive Tree Controls
- **Zoom In / Zoom Out:** Use the `+` and `-` toolbar buttons or the mouse scroll wheel.
- **Pan Canvas:** Click and drag anywhere on the canvas to inspect large trees.
- **Reset View:** Click the reset button to restore default zoom and center the tree.
- **Node Inspector:** Hover or click on any node to view its syntactic properties in the bottom inspector bar:
  - Non-Terminals: Displays the grammar production rule (e.g., `statement -> IDENTIFIER = expression ;`).
  - Terminals: Displays the token category, lexeme, and source line/column coordinates.

---

### Step 6: Inspecting & Copying Three-Address Code
Located directly below the tree visualizer, the **Intermediate Code (Three-Address Code)** card displays generated TAC instructions:
- Clean monospaced layout with ordered line numbers (`1.`, `2.`, `3.`, ...).
- **Copy TAC Button:** Click **Copy TAC** in the card header to copy all instructions directly to your clipboard. The button provides immediate visual confirmation (`Copied!`).

---

### Step 7: Compiler Error Diagnostics & Suggestions
When an invalid program is analyzed:
1. LexiTree intercepts the error cleanly without crashing the server.
2. A red diagnostic alert banner displays:
   - **Error Category:** Distinctly badges `Lexical Error` vs. `Syntax Error`.
   - **Precise Location:** Shows exact line and column (e.g., `Line 1, Column 10`).
   - **Actionable Suggestion:** Provides instructional guidance (e.g., `"Provide a valid number, variable, or parenthesized sub-expression after the operator."`).
3. Stale syntax trees and TAC outputs are cleared automatically.

---

### Step 8: In-App Viva Reference Guide
Click the **Viva Guide** button in the header bar to open an interactive modal containing formal grammar equations, precedence tables, and standard viva voce questions and answers.

---

## 5. Language Grammar Specification

### Formal Context-Free Grammar (CFG)
LexiTree implements an unambiguous context-free grammar in Extended Backus-Naur Form (EBNF):

```text
program     -> statement*
statement   -> IDENTIFIER "=" expression ";"
expression  -> term (("+" | "-") term)*
term        -> unary (("*" | "/") unary)*
unary       -> ("+" | "-") unary | primary
primary     -> NUMBER | IDENTIFIER | "(" expression ")"
```

### Operator Precedence & Associativity

| Precedence | Level | Operators | Associativity | Grammar Production |
|:---:|:---:|:---:|:---:|:---|
| **1 (Highest)** | Parentheses | `( ... )` | Non-associative | `primary` |
| **2** | Unary Operators | `+`, `-` (prefix) | Right-to-Left (Prefix) | `unary` |
| **3** | Multiplication & Division | `*`, `/` | Left-to-Right | `term` |
| **4 (Lowest)** | Addition & Subtraction | `+`, `-` | Left-to-Right | `expression` |

---

## 6. Compiler Engine Architecture & Implementation

### Lexical Scanner (`lexer.py`)
- **Deterministic Scanner:** Implemented as a stateful character scanner.
- **Position Tracking:** Tracks 1-based line and column counters across spaces, tabs, and newline characters.
- **Numeric Scanner:** Distinguishes integer literals (`42`) and floating-point literals (`3.1415`). Flags malformed numbers (`12.34.56` or `12.`).
- **Resilient Scanning:** When encountering illegal characters (such as `@` or `$`), emits a structured `LexicalError` and continues scanning remaining characters.

### Recursive-Descent Parser (`parser.py`)
- **Simultaneous AST & CST Construction:** In a single parsing pass, each recursive function (`_statement`, `_expression`, `_term`, `_unary`, `_primary`) constructs both the AST node and the concrete `ParseTreeNode`.
- **Associativity by Iteration:** Uses `while` loops for left-associative operators (`+`, `-`, `*`, `/`), naturally avoiding left-recursion while producing correct left-heavy trees.
- **Diagnostic Raising:** Detects missing semicolons, unmatched parentheses, missing operands, and invalid statement starters, raising `ParserError` with actionable suggestions.

### Parse Tree Representation (`parse_tree.py`)
- Defines `ParseTreeNode` with attributes: `symbol`, `label`, `kind` (`nonterminal` / `terminal`), `children`, `lexeme`, `line`, `column`, `production`.
- Implements `to_dict()` for JSON serialization.
- Helper `make_terminal_node(token)` transforms lexical tokens into concrete tree leaves.

### AST Representation (`ast_nodes.py`)
- Object-oriented hierarchy: `Program`, `Assignment`, `BinaryOp`, `UnaryOp`, `Number`, `Identifier`.
- Implements `to_dict()` serializing semantic trees to JSON.

### Three-Address Code Generator (`intermediate_code.py`)
- Traverses AST nodes via post-order dispatch.
- Employs `_new_temp()` producing sequential temporaries (`t1`, `t2`, ...).
- Automatically resets temporary allocation on each call to `generate(ast)`.

### Native SVG Visualizers
- **`ast-visualizer.js`:** Computes two-pass subtree layout for AST nodes and renders color-coded cards with cubic bezier connecting curves.
  - **Interactive Branch Highlighting:** Hovering over any node dynamically illuminates its ancestor path and descendant subtree while softly dimming unrelated branches.
  - **Click-to-Pin Inspector Lock:** Clicking any node locks its selection with an active focus glow (`node-selected`), displaying pinned compiler metadata in the inspector.
  - **Source Coordinate Badges:** Cards display source position tags (`L1:C8`) alongside uppercase node-type pills.
  - **Rock-Solid Hover Stability:** Zero physical translation (`translateY`) or stroke-width boundary tampering, eliminating hover jitter ("dancing").
- **`parse-tree-visualizer.js`:** Specialized two-pass layout for Concrete Parse Trees.
  - **Non-Terminal vs Terminal Hierarchy:** Non-terminals render with indigo gradient headers and grammatical derivation brackets `⟨symbol⟩`; terminals render with emerald badges and scanned lexemes.
  - **Derivation Path Focus:** Interactive branch tracing up to the root `⟨program⟩` and down to concrete token leaves.
  - **Inspector Integration:** Clicking or hovering displays grammar derivation rules (e.g. `term -> unary ("*" unary)*`) and token attributes.

---

## 7. Installation & Local Execution Guide

### System Prerequisites
- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python:** Python 3.10, 3.11, or 3.12.
- **Web Browser:** Google Chrome, Microsoft Edge, Mozilla Firefox, or Brave.

---

### Windows PowerShell Execution

1. **Navigate to the project root:**
   ```powershell
   cd "c:\Users\girig\Desktop\CD MY PROJECT"
   ```

2. **Activate the virtual environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   > *Note:* If PowerShell reports a script execution restriction, run:
   > ```powershell
   > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   > ```

3. **Install dependencies:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

4. **Launch the Flask application:**
   ```powershell
   python app.py
   ```
   *Or direct execution via virtual environment binary:*
   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```

5. **Open in Browser:**
   Navigate to `http://127.0.0.1:5000`.

---

### macOS / Linux Execution

```bash
cd "/path/to/CD MY PROJECT"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

---

## 8. Testing and Validation

### A. Automated Test Results
- **Command Executed:**
  ```powershell
  .\.venv\Scripts\python.exe -m unittest discover tests -v
  ```
- **Python Environment:** Python 3.12.10 (64-bit) running in local virtual environment (`.venv`).
- **Total Tests Executed:** **69 automated tests**
- **Passed:** **69**
- **Failed:** **0**
- **Skipped:** **0**
- **Baseline Failures:** **0**
- **Unresolved Failures:** **0**
- **Execution Duration:** ~3.1 seconds across all suites.

---

### B. Chrome Browser Validation
- **Browser Tested:** Google Chrome Version 156.0.8078.49 (Official Build, 64-bit).
- **Application URL:** `http://127.0.0.1:5000/`.
- **Automation Protocol:** Chrome DevTools Protocol (CDP) WebSocket bridge ([tests/test_chrome_browser.py](file:///c:/Users/girig/Desktop/CD%20MY%20PROJECT/tests/test_chrome_browser.py)).
- **Page Load:** Verified successfully (Status 200, zero render blocking, all CSS/JS loaded).
- **Parse Tree Verification:** Verified tab toggle, SVG render, non-terminal/terminal card badges, and interactive inspector.
- **Tree Hover Stability & Branch Highlighting:** Verified rock-solid stationary hover feedback (no boundary jitter or dancing), bidirectional branch highlighting (ancestors + descendants + connecting links), and click-to-pin inspector locking on both AST and Parse Tree views (`test_i`).
- **Three-Address Code Verification:** Verified instruction ordering, deterministic temporaries (`t1`, `t2`), and clipboard copy functionality.
- **Valid & Invalid Input Suite:** Verified precedence (`2 + 3 * 4`), grouping (`(2 + 3) * 4`), multi-statement (`a = b + c * d;\nx = a - 5;`), syntax errors (`result = 2 + ;`, `result = (2 + 3;`, `result = ;`), and post-error recovery (`result = 10 / 2;`).
- **Regression Testing:** Verified editor line numbers, preset dropdown, quick chips, token live search filter, and Viva Guide modal.
- **Console Diagnostics:** Verified **0 unhandled JavaScript exceptions** and zero network resource errors.

---

### C. Test Case Results Matrix

| Test Area | Suite / Module | Result | Verified Observations |
|---|---|:---:|---|
| **Lexer (Scanner)** | `test_lexer.py` (7 tests) | `PASS` | Identifiers, integers, decimals, operators, whitespace, delimiters, malformed numbers, and 1-based line/col tracking. |
| **Parser & AST** | `test_parser.py` (14 tests) | `PASS` | Ambiguity-free recursive-descent parsing, operator precedence (`*` over `+`), left-associativity, unary ops, parentheses, and syntax error assertions. |
| **Parse Tree (CST)** | `test_parse_tree.py` (13 tests) | `PASS` | Concrete derivation hierarchy, non-terminals, terminal leaves in source order, preservation of `=`, `;`, `(`, `)`, and JSON serialization. |
| **TAC Generation** | `test_tac.py` (14 tests) | `PASS` | Post-order AST traversal, temporary variable generation (`t1`, `t2`), counter resets per analysis, float preservation, and multi-statement isolation. |
| **Flask REST API** | `test_api.py` (12 tests) | `PASS` | `GET /` serves HTML, `POST /api/analyze` returns all fields, HTTP 400 on malformed payloads, payload limit enforcement (>64 KB), and request state isolation. |
| **Google Chrome UI** | `test_chrome_browser.py` (8 tests) | `PASS` | Automated CDP browser testing covering initial render, view tabs, SVG layout, TAC list, copy button, error banners, recovery, and zero console errors. |
| **Regression Checks** | End-to-End Suite | `PASS` | Preset selector, quick load chips, live token table search filter, modal toggle, and responsive two-column grid. |

---

### D. Bugs Discovered & Fixed

1. **Asynchronous UI Synchronization in Browser Automation:**
   - *Issue:* During initial automated browser testing, rapid assertions evaluated the DOM immediately after clicking the "Analyze Code" button before the asynchronous `fetch('/api/analyze')` request completed, causing intermittent test failures.
   - *Fix:* Enhanced the browser test driver with `analyze_and_wait()` utilizing an asynchronous Promise that listens for `statusText` transitions from `"Analyzing..."` to final status before DOM assertions execute.
2. **Token Boundary Assertion in Regression Test:**
   - *Issue:* A test assertion expected 5 tokens after analyzing `result = 10 / 2;`, whereas the lexer correctly emits 7 tokens (`result`, `=`, `10`, `/`, `2`, `;`, `<EOF>`).
   - *Fix:* Corrected the boundary verification assertion in `test_chrome_browser.py` to assert the true 7-token stream.

---

### E. Remaining Limitations
- **Language Scope:** Language syntax is intentionally limited to variable assignments and arithmetic expressions. Conditional branches (`if`/`else`), loops (`while`), and custom functions are outside the designated project grammar.
- **Instruction Execution:** Three-Address Code is generated as an Intermediate Representation for compilation and academic inspection; it is not executed directly on physical CPU registers.

---

### F. How to Rerun Tests

Run all 68 automated unit, API, and Chrome browser tests using PowerShell:

```powershell
cd "c:\Users\girig\Desktop\CD MY PROJECT"

# 1. Run Complete Test Suite (Backend, Parse Tree, TAC, API & Chrome UI)
.\.venv\Scripts\python.exe -m unittest discover tests -v

# 2. Run Only Backend Compiler Tests
.\.venv\Scripts\python.exe -m unittest tests.test_lexer tests.test_parser tests.test_parse_tree tests.test_tac -v

# 3. Run Only API Integration Tests
.\.venv\Scripts\python.exe -m unittest tests.test_api -v

# 4. Run Only Automated Chrome Browser Tests
.\.venv\Scripts\python.exe -m unittest tests.test_chrome_browser -v
```

---

### G. Final Demonstration Example

#### Input Source Code:
```text
result = 2 + 3 * 4;
```

#### Verified Compiler Outputs:
- **Lexical Tokens (9 Tokens):**
  `IDENTIFIER(result)`, `ASSIGN(=)`, `NUMBER(2)`, `PLUS(+)`, `NUMBER(3)`, `STAR(*)`, `NUMBER(4)`, `SEMICOLON(;)`, `EOF(<EOF>)`.
- **Concrete Parse Tree:**
  `program` $\to$ `statement` (`result = expression ;`) $\to$ `expression` (`term + term`), where the second `term` derives `unary * unary` (`3 * 4`).
- **Abstract Syntax Tree (AST):**
  `Assignment(identifier=result, value=BinaryOp('+', left=2, right=BinaryOp('*', left=3, right=4)))`.
- **Generated Three-Address Code (TAC):**
  ```text
  t1 = 3 * 4
  t2 = 2 + t1
  result = t2
  ```

---

## 9. REST API Documentation

### `POST /api/analyze`

Executes the full lexical, syntax, AST, CST, and TAC generation pipeline.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Payload
```json
{
  "source_code": "result = 2 + 3 * 4;"
}
```

#### Successful JSON Response (`200 OK`)
```json
{
  "success": true,
  "tokens": [
    { "type": "IDENTIFIER", "lexeme": "result", "line": 1, "column": 1, "value": "result" },
    { "type": "ASSIGN", "lexeme": "=", "line": 1, "column": 8, "value": "=" },
    { "type": "NUMBER", "lexeme": "2", "line": 1, "column": 10, "value": 2 },
    { "type": "PLUS", "lexeme": "+", "line": 1, "column": 12, "value": "+" },
    { "type": "NUMBER", "lexeme": "3", "line": 1, "column": 14, "value": 3 },
    { "type": "STAR", "lexeme": "*", "line": 1, "column": 16, "value": "*" },
    { "type": "NUMBER", "lexeme": "4", "line": 1, "column": 18, "value": 4 },
    { "type": "SEMICOLON", "lexeme": ";", "line": 1, "column": 19, "value": ";" },
    { "type": "EOF", "lexeme": "", "line": 1, "column": 20, "value": "<EOF>" }
  ],
  "lexical_errors": [],
  "syntax_error": null,
  "ast": {
    "type": "Program",
    "statements": [
      {
        "type": "Assignment",
        "identifier": { "type": "Identifier", "name": "result", "line": 1, "column": 1 },
        "value": {
          "type": "BinaryOp",
          "operator": "+",
          "line": 1,
          "column": 12,
          "left": { "type": "Number", "value": 2, "raw": "2", "line": 1, "column": 10 },
          "right": {
            "type": "BinaryOp",
            "operator": "*",
            "line": 1,
            "column": 16,
            "left": { "type": "Number", "value": 3, "raw": "3", "line": 1, "column": 14 },
            "right": { "type": "Number", "value": 4, "raw": "4", "line": 1, "column": 18 }
          }
        },
        "line": 1,
        "column": 1
      }
    ]
  },
  "parse_tree": {
    "symbol": "program",
    "label": "program",
    "kind": "nonterminal",
    "production": "program -> statement*",
    "children": [
      {
        "symbol": "statement",
        "label": "statement",
        "kind": "nonterminal",
        "production": "statement -> IDENTIFIER = expression ;",
        "children": [
          { "symbol": "IDENTIFIER", "label": "result", "kind": "terminal", "lexeme": "result", "line": 1, "column": 1, "children": [] },
          { "symbol": "ASSIGN", "label": "=", "kind": "terminal", "lexeme": "=", "line": 1, "column": 8, "children": [] },
          { "symbol": "expression", "label": "expression", "kind": "nonterminal", "production": "expression -> term (('+' | '-') term)*", "children": [ ... ] },
          { "symbol": "SEMICOLON", "label": ";", "kind": "terminal", "lexeme": ";", "line": 1, "column": 19, "children": [] }
        ]
      },
      { "symbol": "EOF", "label": "EOF", "kind": "terminal", "lexeme": "<EOF>", "line": 1, "column": 20, "children": [] }
    ]
  },
  "intermediate_code": [
    "t1 = 3 * 4",
    "t2 = 2 + t1",
    "result = t2"
  ]
}
```

---

## 10. Annotated Project Directory Structure

```text
CD MY PROJECT/
│
├── app.py                      # Flask web application exposing UI and POST /api/analyze endpoint
├── lexer.py                    # Handcrafted Lexical Scanner (tokenization, line/column tracking)
├── parser.py                   # Recursive-Descent Parser constructing both AST and Parse Tree
├── ast_nodes.py                # Abstract Syntax Tree node definitions (Program, Assignment, etc.)
├── parse_tree.py               # Concrete Syntax Tree (Parse Tree) node definitions and helpers
├── intermediate_code.py        # Three-Address Code (TAC) Intermediate Code Generator
├── requirements.txt            # Python dependencies (Flask >= 3.0.0)
├── README.md                   # Complete academic documentation, user manual, and test report
├── .gitignore                  # Ignores virtual environments (.venv) and Python cache
│
├── templates/
│   └── index.html              # Responsive single-page UI with view tabs and TAC card
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern stylesheet with styles for AST, Parse Tree, and TAC
│   └── js/
│       ├── app.js              # Client orchestrator coordinating API calls, tabs, and copy
│       ├── editor.js           # Multiline editor, line numbers, Tab indent, presets
│       ├── ast-visualizer.js   # Native SVG renderer for Abstract Syntax Trees
│       └── parse-tree-visualizer.js # Native SVG renderer for Concrete Parse Trees
│
└── tests/
    ├── test_lexer.py           # 7 unit tests for lexical scanner
    ├── test_parser.py          # 14 unit tests for grammar and AST
    ├── test_parse_tree.py      # 13 unit tests for concrete parse tree construction
    ├── test_tac.py             # 14 unit tests for Three-Address Code generation
    ├── test_api.py             # 12 integration tests for Flask routing and API payload validation
    └── test_chrome_browser.py  # 8 automated end-to-end tests driving Google Chrome via CDP
```

---

## 11. College Viva Voce Q&A Reference

### Q1: What is the difference between a Concrete Parse Tree and an Abstract Syntax Tree?
**Ans:** A **Parse Tree (Concrete Syntax Tree)** represents the exact syntactic derivation steps based on the context-free grammar, explicitly retaining grammar non-terminals (`expression`, `term`) and terminal punctuation (`=`, `;`, `(`, `)`). An **Abstract Syntax Tree (AST)** retains only the semantic structure (operators, operands, identifiers) and strips out syntactic punctuation, making it compact and suitable for intermediate code generation.

### Q2: What is Three-Address Code (TAC) and why is it used?
**Ans:** Three-Address Code is an Intermediate Representation (IR) where each instruction has at most one operator and at most three operand addresses (e.g., `x = y + z`). It linearizes hierarchical nested syntax trees into a format that closely mirrors assembly language while remaining target-machine independent.

### Q3: How does LexiTree enforce operator precedence in Three-Address Code?
**Ans:** Because TAC is generated by traversing the **AST**, operator precedence is inherently preserved. In the AST, higher-precedence operations (such as `3 * 4`) sit lower in the tree than lower-precedence operations (`2 + ...`). Post-order traversal evaluates the lower subtree first, emitting `t1 = 3 * 4` before `t2 = 2 + t1`.

### Q4: Why must a Top-Down Recursive-Descent Parser eliminate Left-Recursion?
**Ans:** In a top-down parser, a grammar rule like $A \to A \alpha$ causes the function `A()` to immediately call itself recursively without consuming any token, resulting in an infinite loop and stack overflow. In LexiTree, left-recursion is eliminated by rewriting rules using EBNF repetition: $\text{expression} \to \text{term } ((\text{'+'} \mid \text{'-'}) \text{ term})^*$, which is implemented using iterative `while` loops.

### Q5: How are temporary variables managed during Three-Address Code generation?
**Ans:** The `TACGenerator` maintains a sequential temporary counter starting at `1` (`t1`, `t2`, `t3`). The counter resets at the beginning of each compilation pass to ensure deterministic, reproducible output.

---

## 12. Demonstration Script for Academic Evaluators

Follow this 5-minute structured sequence when demonstrating LexiTree to an examiner or professor:

1. **Architecture & Zero-Dependency Explanation (1 Minute):**
   - Highlight that the entire compiler pipeline (Scanner $\to$ Parser $\to$ AST $\to$ Parse Tree $\to$ TAC $\to$ SVG Visualizer) is handcrafted from scratch without external compiler or graph libraries.
   - Show [lexer.py](file:///c:/Users/girig/Desktop/CD%20MY%20PROJECT/lexer.py), [parser.py](file:///c:/Users/girig/Desktop/CD%20MY%20PROJECT/parser.py), [parse_tree.py](file:///c:/Users/girig/Desktop/CD%20MY%20PROJECT/parse_tree.py), and [intermediate_code.py](file:///c:/Users/girig/Desktop/CD%20MY%20PROJECT/intermediate_code.py).

2. **Automated Testing Verification (1 Minute):**
   - Run in PowerShell:
     ```powershell
     python -m unittest discover tests -v
     ```
   - Point out that **all 68 tests pass**, verifying the scanner, AST, concrete parse tree, TAC generator, REST API, and Chrome browser end-to-end suite.

3. **Live Demonstration: AST vs. Parse Tree (1.5 Minutes):**
   - Open `http://127.0.0.1:5000`.
   - Click preset chip **`2 + 3 * 4`**.
   - Show the **Abstract Syntax Tree (AST)** view: explain how `*` sits lower than `+`.
   - Switch to the **Parse Tree (CST)** tab: demonstrate the full derivation hierarchy (`expression -> term + term`, where the second term expands to `unary * unary`), showing exact terminals (`result`, `=`, `;`).
   - Click preset chip **`(2 + 3) * 4`**: show how parentheses invert the hierarchy in both trees.

4. **Intermediate Code Generation (TAC) Demonstration (1 Minute):**
   - Scroll to the **Three-Address Code** card:
     ```text
     t1 = 3 * 4
     t2 = 2 + t1
     result = t2
     ```
   - Explain how post-order AST traversal generates deterministic temporaries.
   - Click **Copy TAC** to show one-click clipboard copying.

5. **Error Diagnostics & Viva Reference (30 Seconds):**
   - Click **`Missing Operand`** (`x = 10 + ;`): Show exact line/column tracking and actionable suggestions.
   - Open the **Viva Guide** modal from the header to review context-free grammar equations and answers to viva questions.
