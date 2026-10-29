/**
 * app.js - Main Client Application Orchestrator for LexiTree
 * Coordinates Editor, Token Table, AST Visualizer, Parse Tree Visualizer,
 * Three-Address Code Generator display, and Flask API calls.
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Visualizer & Editor Components
    EditorModule.init();
    AstVisualizer.init();
    ParseTreeVisualizer.init();

    // 2. DOM Elements
    const analyzeBtn = document.getElementById("analyzeBtn");
    const clearBtn = document.getElementById("clearBtn");
    const tokenTableBody = document.getElementById("tokenTableBody");
    const tokenCountBadge = document.getElementById("tokenCountBadge");
    const tokenSearch = document.getElementById("tokenSearch");

    const statusBadge = document.getElementById("statusBadge");
    const statusText = document.getElementById("statusText");

    const errorPanel = document.getElementById("errorPanel");
    const errorTypeBadge = document.getElementById("errorTypeBadge");
    const errorLocation = document.getElementById("errorLocation");
    const errorMessage = document.getElementById("errorMessage");
    const errorSuggestion = document.getElementById("errorSuggestion");
    const dismissErrorBtn = document.getElementById("dismissErrorBtn");

    // Tree View Switcher Elements
    const viewAstTab = document.getElementById("viewAstTab");
    const viewParseTreeTab = document.getElementById("viewParseTreeTab");
    const astLegend = document.getElementById("astLegend");
    const parseTreeLegend = document.getElementById("parseTreeLegend");
    const astContainer = document.getElementById("svgContainer");
    const parseTreeContainer = document.getElementById("parseTreeContainer");
    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const resetZoomBtn = document.getElementById("resetZoomBtn");
    const inspectorInfo = document.getElementById("inspectorInfo");

    // Three-Address Code (TAC) Elements
    const tacCountBadge = document.getElementById("tacCountBadge");
    const tacEmptyState = document.getElementById("tacEmptyState");
    const tacContent = document.getElementById("tacContent");
    const tacList = document.getElementById("tacList");
    const copyTacBtn = document.getElementById("copyTacBtn");
    const copyTacBtnText = document.getElementById("copyTacBtnText");

    // State Variables
    let currentTokens = [];
    let currentTac = [];
    let activeTreeView = "ast"; // "ast" or "parse-tree"

    // 3. Event Bindings
    analyzeBtn.addEventListener("click", runAnalysis);
    clearBtn.addEventListener("click", handleClearAll);
    tokenSearch.addEventListener("input", filterTokenTable);
    dismissErrorBtn.addEventListener("click", () => errorPanel.classList.add("hidden"));

    // View Switcher Tabs
    if (viewAstTab && viewParseTreeTab) {
        viewAstTab.addEventListener("click", () => switchTreeView("ast"));
        viewParseTreeTab.addEventListener("click", () => switchTreeView("parse-tree"));
    }

    // Zoom & Pan Unified Controls
    if (zoomInBtn) {
        zoomInBtn.addEventListener("click", () => {
            if (activeTreeView === "ast") {
                AstVisualizer.zoom(0.15);
            } else {
                ParseTreeVisualizer.zoom(0.15);
            }
        });
    }

    if (zoomOutBtn) {
        zoomOutBtn.addEventListener("click", () => {
            if (activeTreeView === "ast") {
                AstVisualizer.zoom(-0.15);
            } else {
                ParseTreeVisualizer.zoom(-0.15);
            }
        });
    }

    if (resetZoomBtn) {
        resetZoomBtn.addEventListener("click", () => {
            if (activeTreeView === "ast") {
                AstVisualizer.resetView();
            } else {
                ParseTreeVisualizer.resetView();
            }
        });
    }

    // Copy TAC Button
    if (copyTacBtn) {
        copyTacBtn.addEventListener("click", handleCopyTac);
    }

    // Auto-run analysis on page load with initial default starter code
    runAnalysis();

    /**
     * Switches between AST and Parse Tree views.
     */
    function switchTreeView(view) {
        activeTreeView = view;
        if (view === "ast") {
            viewAstTab.classList.add("active");
            viewAstTab.setAttribute("aria-selected", "true");
            viewParseTreeTab.classList.remove("active");
            viewParseTreeTab.setAttribute("aria-selected", "false");

            astLegend.classList.remove("hidden");
            parseTreeLegend.classList.add("hidden");

            astContainer.classList.remove("hidden");
            parseTreeContainer.classList.add("hidden");

            if (inspectorInfo) {
                inspectorInfo.textContent = "Hover or click on any AST node to inspect its properties.";
            }
        } else {
            viewParseTreeTab.classList.add("active");
            viewParseTreeTab.setAttribute("aria-selected", "true");
            viewAstTab.classList.remove("active");
            viewAstTab.setAttribute("aria-selected", "false");

            parseTreeLegend.classList.remove("hidden");
            astLegend.classList.add("hidden");

            parseTreeContainer.classList.remove("hidden");
            astContainer.classList.add("hidden");

            if (inspectorInfo) {
                inspectorInfo.textContent = "Hover or click on any Parse Tree node (non-terminal or terminal) to inspect grammar details.";
            }
        }
    }

    /**
     * Executes the lexical, syntax, AST, CST, and TAC analysis pipeline via the backend API.
     */
    async function runAnalysis() {
        const sourceCode = EditorModule.getCode();
        setSystemStatus("processing", "Analyzing...");

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ source_code: sourceCode })
            });

            const data = await response.json();

            // 1. Populate Token Table (Always retain available tokens)
            currentTokens = data.tokens || [];
            renderTokenTable(currentTokens);

            // 2. Handle Lexical Errors
            if (data.lexical_errors && data.lexical_errors.length > 0) {
                const firstErr = data.lexical_errors[0];
                showError("Lexical Error", firstErr.message, firstErr.line, firstErr.column, firstErr.suggestion);
                setSystemStatus("error", `Lexical Error at ${firstErr.line}:${firstErr.column}`);
                AstVisualizer.clear();
                ParseTreeVisualizer.clear();
                renderTac([]);
                return;
            }

            // 3. Handle Syntax Errors
            if (data.syntax_error) {
                const err = data.syntax_error;
                showError("Syntax Error", err.message, err.line, err.column, err.suggestion);
                setSystemStatus("error", `Syntax Error at ${err.line}:${err.column}`);
                AstVisualizer.clear();
                ParseTreeVisualizer.clear();
                renderTac([]);
                return;
            }

            // 4. Handle Successful Analysis
            if (data.success && data.ast) {
                hideError();
                setSystemStatus("success", "Analysis Successful");

                // Render Abstract Syntax Tree (AST)
                AstVisualizer.render(data.ast);

                // Render Concrete Parse Tree (CST)
                if (data.parse_tree) {
                    ParseTreeVisualizer.render(data.parse_tree);
                } else {
                    ParseTreeVisualizer.clear();
                }

                // Render Three-Address Code (TAC)
                currentTac = data.intermediate_code || [];
                renderTac(currentTac);

            } else {
                showError("Analysis Error", "Failed to construct syntax tree.", 1, 1, "Verify expression syntax.");
                setSystemStatus("error", "Analysis Incomplete");
                AstVisualizer.clear();
                ParseTreeVisualizer.clear();
                renderTac([]);
            }

        } catch (err) {
            console.error("Analysis network error:", err);
            showError("Network Error", "Unable to connect to local Flask server.", 1, 1, "Ensure the server is running on http://127.0.0.1:5000");
            setSystemStatus("error", "Server Disconnected");
            AstVisualizer.clear();
            ParseTreeVisualizer.clear();
            renderTac([]);
        }
    }

    /**
     * Renders Three-Address Code instructions into the TAC card.
     */
    function renderTac(instructions) {
        currentTac = instructions || [];
        tacCountBadge.textContent = `${currentTac.length} instr`;

        if (currentTac.length === 0) {
            tacEmptyState.classList.remove("hidden");
            tacContent.classList.add("hidden");
            tacList.innerHTML = "";
            return;
        }

        tacEmptyState.classList.add("hidden");
        tacContent.classList.remove("hidden");
        tacList.innerHTML = "";

        currentTac.forEach((instr) => {
            const li = document.createElement("li");
            li.textContent = instr;
            tacList.appendChild(li);
        });
    }

    /**
     * Copies Three-Address Code instructions to system clipboard.
     */
    async function handleCopyTac() {
        if (!currentTac || currentTac.length === 0) {
            return;
        }

        const fullText = currentTac.join("\n");
        try {
            await navigator.clipboard.writeText(fullText);
            const originalText = copyTacBtnText.textContent;
            copyTacBtnText.textContent = "Copied!";
            copyTacBtn.classList.add("btn-success");

            setTimeout(() => {
                copyTacBtnText.textContent = originalText;
                copyTacBtn.classList.remove("btn-success");
            }, 1800);
        } catch (err) {
            console.error("Clipboard copy failed:", err);
        }
    }

    /**
     * Renders tokens into the token table.
     */
    function renderTokenTable(tokens) {
        tokenCountBadge.textContent = tokens.length;
        tokenTableBody.innerHTML = "";

        if (tokens.length === 0) {
            const row = document.createElement("tr");
            row.className = "empty-row";
            row.innerHTML = `
                <td colspan="5" class="empty-state">
                    <div class="empty-box">
                        <p>No tokens recognized</p>
                    </div>
                </td>
            `;
            tokenTableBody.appendChild(row);
            return;
        }

        tokens.forEach((tok, idx) => {
            const tr = document.createElement("tr");

            // # Index
            const tdIndex = document.createElement("td");
            tdIndex.textContent = idx + 1;
            tr.appendChild(tdIndex);

            // Lexeme
            const tdLexeme = document.createElement("td");
            const lexSpan = document.createElement("span");
            lexSpan.className = "lexeme-cell";
            lexSpan.textContent = tok.lexeme === "" ? "<EOF>" : tok.lexeme;
            tdLexeme.appendChild(lexSpan);
            tr.appendChild(tdLexeme);

            // Token Type Pill
            const tdType = document.createElement("td");
            const typePill = document.createElement("span");
            typePill.className = `token-pill ${tok.type}`;
            typePill.textContent = tok.type;
            tdType.appendChild(typePill);
            tr.appendChild(tdType);

            // Line
            const tdLine = document.createElement("td");
            tdLine.textContent = tok.line;
            tr.appendChild(tdLine);

            // Column
            const tdCol = document.createElement("td");
            tdCol.textContent = tok.column;
            tr.appendChild(tdCol);

            tokenTableBody.appendChild(tr);
        });
    }

    /**
     * Filters token table by query string.
     */
    function filterTokenTable() {
        const query = tokenSearch.value.trim().toLowerCase();
        if (!query) {
            renderTokenTable(currentTokens);
            return;
        }

        const filtered = currentTokens.filter(tok => 
            tok.type.toLowerCase().includes(query) ||
            tok.lexeme.toLowerCase().includes(query)
        );
        renderTokenTable(filtered);
    }

    /**
     * Shows the error banner with details and suggestion.
     */
    function showError(type, message, line, column, suggestion) {
        errorTypeBadge.textContent = type;
        errorLocation.textContent = `Line ${line}, Column ${column}`;
        errorMessage.textContent = message;

        if (suggestion) {
            errorSuggestion.classList.remove("hidden");
            errorSuggestion.querySelector("span").textContent = suggestion;
        } else {
            errorSuggestion.classList.add("hidden");
        }

        errorPanel.classList.remove("hidden");
    }

    /**
     * Hides the error banner.
     */
    function hideError() {
        errorPanel.classList.add("hidden");
    }

    /**
     * Updates top navigation status badge.
     */
    function setSystemStatus(state, text) {
        statusBadge.className = `status-badge status-${state}`;
        statusText.textContent = text;
    }

    /**
     * Resets all panels to pristine empty state.
     */
    function handleClearAll() {
        hideError();
        setSystemStatus("idle", "System Ready");
        currentTokens = [];
        currentTac = [];
        tokenCountBadge.textContent = "0";
        tokenTableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5" class="empty-state">
                    <div class="empty-box">
                        <p>No tokens generated yet</p>
                        <small>Click "Analyze Code" to scan source code</small>
                    </div>
                </td>
            </tr>
        `;
        AstVisualizer.clear();
        ParseTreeVisualizer.clear();
        renderTac([]);
        if (inspectorInfo) {
            inspectorInfo.textContent = "Hover or click on any node to inspect its properties.";
        }
    }
});
