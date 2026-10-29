/**
 * parse-tree-visualizer.js - Custom Native SVG Parse Tree (Concrete Syntax Tree) Visualizer
 *
 * Renders the Concrete Syntax Tree produced during recursive-descent parsing.
 * Features:
 * - Distinct visual representation for non-terminals vs terminals.
 * - Displays grammar symbols, actual lexemes, productions, and source positions.
 * - Guaranteed non-overlapping hierarchical top-to-bottom SVG layout.
 * - Advanced branch & derivation path highlighting on hover (ancestor + subtree focus).
 * - Click-to-pin inspector locking with active visual aura.
 * - Rock-solid stationary hover feedback (no boundary jitter / dancing).
 * - Zoom in / Zoom out / Pan / Reset view controls.
 */

const ParseTreeVisualizer = (() => {
    // Layout Constants
    const NODE_WIDTH = 132;
    const NODE_HEIGHT = 50;
    const H_GAP = 24;
    const V_GAP = 60;
    const PADDING_X = 40;
    const PADDING_Y = 40;

    // Visual Palette for Parse Tree
    const COLOR_NONTERMINAL = {
        fill: "#f8fafc",
        headerGrad: "grad-pt-nonterminal",
        stroke: "#6366f1",
        title: "#4338ca",
        val: "#1e1b4b"
    };

    const COLOR_TERMINAL = {
        fill: "#f0fdf4",
        headerGrad: "grad-pt-terminal",
        stroke: "#10b981",
        title: "#047857",
        val: "#064e3b"
    };

    let svgElement, emptyStateElement, containerElement, inspectorInfo;
    let currentScale = 1.0;
    let translateX = 0;
    let translateY = 0;
    let isPanning = false;
    let startPanX = 0;
    let startPanY = 0;
    let currentTreeRoot = null;

    let allNodes = [];
    let allLinks = [];
    let selectedNode = null;

    function init() {
        svgElement = document.getElementById("parseTreeSvg");
        emptyStateElement = document.getElementById("parseTreeEmptyState");
        containerElement = document.getElementById("parseTreeContainer");
        inspectorInfo = document.getElementById("inspectorInfo");

        if (!svgElement || !containerElement) return;

        // Container mouse drag panning
        containerElement.addEventListener("mousedown", handleMouseDown);
        window.addEventListener("mousemove", handleMouseMove);
        window.addEventListener("mouseup", handleMouseUp);
        containerElement.addEventListener("wheel", handleWheel, { passive: false });

        // Canvas background click unpins
        svgElement.addEventListener("click", (e) => {
            if (e.target === svgElement || e.target.id === "parseTreeTransformGroup") {
                deselectNode();
            }
        });
    }

    function clear() {
        if (!svgElement) return;
        svgElement.innerHTML = "";
        svgElement.classList.add("hidden");
        if (emptyStateElement) emptyStateElement.classList.remove("hidden");
        currentTreeRoot = null;
        allNodes = [];
        allLinks = [];
        selectedNode = null;
    }

    /**
     * Converts JSON Parse Tree node into visual tree structure.
     */
    function buildVisualTree(node, parent = null) {
        if (!node) return null;

        const isTerminal = node.kind === "terminal";
        let displayTitle = node.symbol;
        let displayVal = "";
        let details = "";
        let line = node.line || 1;
        let column = node.column || 1;

        if (isTerminal) {
            displayVal = node.lexeme !== undefined ? node.lexeme : node.label;
            details = `Terminal '${displayVal}' (Token: ${node.symbol}) at line ${line}, col ${column}.`;
        } else {
            displayVal = `⟨${node.symbol}⟩`;
            const prod = node.production ? ` | Rule: ${node.production}` : "";
            details = `Non-Terminal: ⟨${node.symbol}⟩${prod}`;
        }

        const visualNode = {
            id: null,
            symbol: node.symbol,
            label: node.label,
            kind: node.kind,
            isTerminal,
            title: displayTitle,
            val: displayVal,
            details,
            lexeme: node.lexeme,
            line,
            column,
            production: node.production,
            rawNode: node,
            parent: parent,
            children: [],
            parentLink: null,
            domElement: null,
            x: 0,
            y: 0,
            subtreeWidth: 0
        };

        visualNode.children = (node.children || []).map(child => buildVisualTree(child, visualNode)).filter(Boolean);

        return visualNode;
    }

    /**
     * Bottom-up layout pass: compute required subtree widths.
     */
    function computeSubtreeWidth(node) {
        if (!node.children || node.children.length === 0) {
            node.subtreeWidth = NODE_WIDTH;
            return node.subtreeWidth;
        }

        let sumChildren = 0;
        node.children.forEach((child, idx) => {
            sumChildren += computeSubtreeWidth(child);
            if (idx > 0) sumChildren += H_GAP;
        });

        node.subtreeWidth = Math.max(NODE_WIDTH, sumChildren);
        return node.subtreeWidth;
    }

    /**
     * Top-down layout pass: assign (x, y) coordinates.
     */
    function assignPositions(node, leftBound, depth) {
        node.y = PADDING_Y + depth * (NODE_HEIGHT + V_GAP);

        if (!node.children || node.children.length === 0) {
            node.x = leftBound + (node.subtreeWidth - NODE_WIDTH) / 2;
            return;
        }

        let sumChildrenWidth = 0;
        node.children.forEach((child, idx) => {
            sumChildrenWidth += child.subtreeWidth;
            if (idx > 0) sumChildrenWidth += H_GAP;
        });

        let currentLeft = leftBound + Math.max(0, (node.subtreeWidth - sumChildrenWidth) / 2);
        node.children.forEach((child) => {
            assignPositions(child, currentLeft, depth + 1);
            currentLeft += child.subtreeWidth + H_GAP;
        });

        // Center parent over the midpoint of its first and last child
        const firstChild = node.children[0];
        const lastChild = node.children[node.children.length - 1];
        node.x = (firstChild.x + lastChild.x) / 2;
    }

    /**
     * Collect nodes and connecting links for rendering.
     */
    function collectGraph(node, nodesOut, linksOut) {
        node.id = "pt-node-" + nodesOut.length;
        nodesOut.push(node);
        node.children.forEach(child => {
            const linkObj = {
                source: node,
                target: child,
                x1: node.x + NODE_WIDTH / 2,
                y1: node.y + NODE_HEIGHT,
                x2: child.x + NODE_WIDTH / 2,
                y2: child.y,
                isChildTerminal: child.isTerminal,
                domElement: null
            };
            child.parentLink = linkObj;
            linksOut.push(linkObj);
            collectGraph(child, nodesOut, linksOut);
        });
    }

    // -------------------------------------------------------------------------
    // Advanced Branch & Derivation Highlighting
    // -------------------------------------------------------------------------

    function highlightBranch(targetNode) {
        if (!targetNode) return;
        const activeNodes = new Set();
        const activeLinks = new Set();

        // 1. Derivation ancestors up to root
        let curr = targetNode;
        while (curr) {
            activeNodes.add(curr);
            if (curr.parentLink) activeLinks.add(curr.parentLink);
            curr = curr.parent;
        }

        // 2. Subtree descendants
        function addDescendants(n) {
            activeNodes.add(n);
            if (n.children) {
                n.children.forEach(c => {
                    if (c.parentLink) activeLinks.add(c.parentLink);
                    addDescendants(c);
                });
            }
        }
        addDescendants(targetNode);

        // Apply classes
        allNodes.forEach(n => {
            if (n.domElement) {
                if (activeNodes.has(n)) {
                    n.domElement.classList.add("node-highlighted");
                    n.domElement.classList.remove("node-dimmed");
                } else {
                    n.domElement.classList.remove("node-highlighted");
                    n.domElement.classList.add("node-dimmed");
                }
            }
        });

        allLinks.forEach(l => {
            if (l.domElement) {
                if (activeLinks.has(l)) {
                    l.domElement.classList.add("link-highlighted");
                    l.domElement.classList.remove("link-dimmed");
                } else {
                    l.domElement.classList.remove("link-highlighted");
                    l.domElement.classList.add("link-dimmed");
                }
            }
        });
    }

    function clearHighlight() {
        if (selectedNode) {
            highlightBranch(selectedNode);
            return;
        }
        allNodes.forEach(n => {
            if (n.domElement) n.domElement.classList.remove("node-highlighted", "node-dimmed");
        });
        allLinks.forEach(l => {
            if (l.domElement) l.domElement.classList.remove("link-highlighted", "link-dimmed");
        });
    }

    function updateInspector(node, isPinned = false) {
        if (!inspectorInfo) return;
        if (!node) {
            inspectorInfo.textContent = "Hover or click on any Parse Tree node (non-terminal or terminal) to inspect grammar details.";
            return;
        }

        const pinBadge = isPinned ? `<span class="inspector-badge badge-pinned">PINNED</span> ` : "";
        if (node.isTerminal) {
            const termBadge = `<span class="inspector-badge badge-terminal">TERMINAL</span>`;
            const posBadge = `<span class="inspector-pos">L${node.line}:C${node.column}</span>`;
            inspectorInfo.innerHTML = `${pinBadge}${termBadge} <strong>'${node.val}'</strong> (Token: ${node.symbol}) ${posBadge} &mdash; Scanned concrete terminal symbol.`;
        } else {
            const nontermBadge = `<span class="inspector-badge badge-nonterminal">NON-TERMINAL</span>`;
            const prod = node.production ? ` &mdash; Rule: <code>${node.production}</code>` : "";
            inspectorInfo.innerHTML = `${pinBadge}${nontermBadge} <strong>⟨${node.symbol}⟩</strong>${prod}`;
        }
    }

    function deselectNode() {
        if (selectedNode && selectedNode.domElement) {
            selectedNode.domElement.classList.remove("node-selected");
        }
        selectedNode = null;
        clearHighlight();
        updateInspector(null);
    }

    /**
     * Render Parse Tree into SVG.
     */
    function render(parseTree) {
        if (!parseTree) {
            clear();
            return;
        }

        const visualRoot = buildVisualTree(parseTree);
        if (!visualRoot) {
            clear();
            return;
        }

        currentTreeRoot = visualRoot;
        computeSubtreeWidth(visualRoot);
        assignPositions(visualRoot, PADDING_X, 0);

        allNodes = [];
        allLinks = [];
        selectedNode = null;
        collectGraph(visualRoot, allNodes, allLinks);

        // Calculate bounding box
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        allNodes.forEach(n => {
            minX = Math.min(minX, n.x);
            maxX = Math.max(maxX, n.x + NODE_WIDTH);
            minY = Math.min(minY, n.y);
            maxY = Math.max(maxY, n.y + NODE_HEIGHT);
        });

        const totalWidth = Math.max(650, maxX + PADDING_X);
        const totalHeight = Math.max(480, maxY + PADDING_Y);

        // Hide empty state, reveal SVG
        if (emptyStateElement) emptyStateElement.classList.add("hidden");
        svgElement.classList.remove("hidden");
        svgElement.innerHTML = "";

        svgElement.setAttribute("viewBox", `0 0 ${totalWidth} ${totalHeight}`);
        svgElement.setAttribute("width", totalWidth);
        svgElement.setAttribute("height", totalHeight);

        // Gradients and filter definitions
        const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        defs.innerHTML = `
            <filter id="ptShadow" x="-15%" y="-15%" width="130%" height="135%">
                <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#1e1b4b" flood-opacity="0.08" />
            </filter>
            <linearGradient id="grad-pt-nonterminal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#4f46e5" />
                <stop offset="100%" stop-color="#6366f1" />
            </linearGradient>
            <linearGradient id="grad-pt-terminal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#059669" />
                <stop offset="100%" stop-color="#10b981" />
            </linearGradient>
        `;
        svgElement.appendChild(defs);

        // Master transformation group for zoom/pan
        const gMaster = document.createElementNS("http://www.w3.org/2000/svg", "g");
        gMaster.id = "parseTreeTransformGroup";
        svgElement.appendChild(gMaster);

        // 1. Render connecting links
        allLinks.forEach(link => {
            const gLink = document.createElementNS("http://www.w3.org/2000/svg", "g");
            gLink.setAttribute("class", "ast-link-group");
            link.domElement = gLink;

            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            const dy = (link.y2 - link.y1) * 0.55;
            const d = `M ${link.x1} ${link.y1} C ${link.x1} ${link.y1 + dy}, ${link.x2} ${link.y2 - dy}, ${link.x2} ${link.y2}`;
            path.setAttribute("d", d);
            path.setAttribute("stroke", link.isChildTerminal ? "#34d399" : "#818cf8");
            path.setAttribute("stroke-width", "2.0");
            path.setAttribute("fill", "none");
            gLink.appendChild(path);

            // Starting dot
            const dot1 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            dot1.setAttribute("cx", link.x1);
            dot1.setAttribute("cy", link.y1);
            dot1.setAttribute("r", "3.0");
            dot1.setAttribute("fill", "#6366f1");
            gLink.appendChild(dot1);

            // Ending dot
            const dot2 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            dot2.setAttribute("cx", link.x2);
            dot2.setAttribute("cy", link.y2);
            dot2.setAttribute("r", "3.0");
            dot2.setAttribute("fill", link.isChildTerminal ? "#10b981" : "#6366f1");
            gLink.appendChild(dot2);

            gMaster.appendChild(gLink);
        });

        // 2. Render tree nodes (Rock-solid stationary hover feedback)
        allNodes.forEach(node => {
            const gNode = document.createElementNS("http://www.w3.org/2000/svg", "g");
            gNode.setAttribute("class", `ast-node pt-node ${node.isTerminal ? 'pt-node-terminal' : 'pt-node-nonterminal'}`);
            gNode.setAttribute("transform", `translate(${node.x}, ${node.y})`);
            node.domElement = gNode;

            const colors = node.isTerminal ? COLOR_TERMINAL : COLOR_NONTERMINAL;

            // Card Base Rectangle with constant stroke width (NO hover jitter)
            const cardBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            cardBg.setAttribute("class", "card-bg");
            cardBg.setAttribute("width", NODE_WIDTH);
            cardBg.setAttribute("height", NODE_HEIGHT);
            cardBg.setAttribute("fill", colors.fill);
            cardBg.setAttribute("stroke", colors.stroke);
            cardBg.setAttribute("stroke-width", "2");
            cardBg.setAttribute("rx", node.isTerminal ? "10" : "8");
            cardBg.setAttribute("ry", node.isTerminal ? "10" : "8");
            cardBg.setAttribute("filter", "url(#ptShadow)");
            gNode.appendChild(cardBg);

            // Top Header Accent Strip
            const headerClip = document.createElementNS("http://www.w3.org/2000/svg", "path");
            headerClip.setAttribute("d", `M 0 ${node.isTerminal ? '10' : '8'} Q 0 0 ${node.isTerminal ? '10' : '8'} 0 L ${NODE_WIDTH - (node.isTerminal ? 10 : 8)} 0 Q ${NODE_WIDTH} 0 ${NODE_WIDTH} ${node.isTerminal ? '10' : '8'} L ${NODE_WIDTH} 16 L 0 16 Z`);
            headerClip.setAttribute("fill", `url(#${colors.headerGrad})`);
            gNode.appendChild(headerClip);

            // Header text: Tag (Non-Terminal vs Terminal)
            const typeText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            typeText.setAttribute("x", node.isTerminal ? 10 : NODE_WIDTH / 2);
            typeText.setAttribute("y", "12");
            typeText.setAttribute("text-anchor", node.isTerminal ? "start" : "middle");
            typeText.setAttribute("fill", "#ffffff");
            typeText.setAttribute("font-size", "8.5px");
            typeText.setAttribute("font-weight", "700");
            typeText.setAttribute("letter-spacing", "0.06em");
            typeText.textContent = node.isTerminal ? "TERMINAL" : "NON-TERMINAL";
            gNode.appendChild(typeText);

            // Terminal Coordinate Badge
            if (node.isTerminal) {
                const posText = document.createElementNS("http://www.w3.org/2000/svg", "text");
                posText.setAttribute("x", NODE_WIDTH - 8);
                posText.setAttribute("y", "12");
                posText.setAttribute("text-anchor", "end");
                posText.setAttribute("fill", "rgba(255, 255, 255, 0.90)");
                posText.setAttribute("font-size", "8px");
                posText.setAttribute("font-weight", "600");
                posText.setAttribute("font-family", "'Fira Code', monospace");
                posText.textContent = `L${node.line}:C${node.column}`;
                gNode.appendChild(posText);
            }

            // Node main label
            const labelText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            labelText.setAttribute("x", NODE_WIDTH / 2);
            labelText.setAttribute("y", "36");
            labelText.setAttribute("text-anchor", "middle");
            labelText.setAttribute("fill", colors.val);
            labelText.setAttribute("font-family", node.isTerminal ? "'Fira Code', monospace" : "inherit");
            labelText.setAttribute("font-size", node.isTerminal ? "12px" : "11.5px");
            labelText.setAttribute("font-weight", "600");
            
            // Format display text
            let safeLabel = node.val;
            if (safeLabel.length > 14) {
                safeLabel = safeLabel.substring(0, 12) + "…";
            }
            labelText.textContent = safeLabel;
            gNode.appendChild(labelText);

            // Hover and click inspection (Stable hover, no stroke-width tampering)
            gNode.addEventListener("mouseenter", () => {
                if (!selectedNode) {
                    highlightBranch(node);
                    updateInspector(node, false);
                }
            });

            gNode.addEventListener("mouseleave", () => {
                if (!selectedNode) {
                    clearHighlight();
                    updateInspector(null);
                }
            });

            gNode.addEventListener("click", (e) => {
                e.stopPropagation();
                if (selectedNode === node) {
                    deselectNode();
                } else {
                    if (selectedNode && selectedNode.domElement) {
                        selectedNode.domElement.classList.remove("node-selected");
                    }
                    selectedNode = node;
                    gNode.classList.add("node-selected");
                    highlightBranch(node);
                    updateInspector(node, true);
                }
            });

            gMaster.appendChild(gNode);
        });

        resetView();
    }

    /**
     * Zoom control.
     */
    function zoom(delta) {
        currentScale = Math.min(Math.max(0.3, currentScale + delta), 2.5);
        applyTransform();
    }

    /**
     * Resets pan and zoom.
     */
    function resetView() {
        currentScale = 1.0;
        translateX = 0;
        translateY = 0;
        applyTransform();
    }

    function applyTransform() {
        const gMaster = document.getElementById("parseTreeTransformGroup");
        if (gMaster) {
            gMaster.setAttribute("transform", `translate(${translateX}, ${translateY}) scale(${currentScale})`);
        }
    }

    function handleMouseDown(e) {
        if (e.button !== 0) return;
        isPanning = true;
        startPanX = e.clientX - translateX;
        startPanY = e.clientY - translateY;
        if (containerElement) containerElement.style.cursor = "grabbing";
    }

    function handleMouseMove(e) {
        if (!isPanning) return;
        translateX = e.clientX - startPanX;
        translateY = e.clientY - startPanY;
        applyTransform();
    }

    function handleMouseUp() {
        isPanning = false;
        if (containerElement) containerElement.style.cursor = "grab";
    }

    function handleWheel(e) {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.08 : -0.08;
        zoom(delta);
    }

    return {
        init,
        render,
        clear,
        zoom,
        resetView,
        deselectNode
    };
})();
