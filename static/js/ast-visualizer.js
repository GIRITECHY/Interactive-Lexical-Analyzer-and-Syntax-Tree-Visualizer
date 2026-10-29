/**
 * ast-visualizer.js - Custom Native SVG Syntax Tree Visualizer for LexiTree
 * 
 * Renders Abstract Syntax Trees using native SVG elements without any
 * third-party visualization libraries.
 * Features:
 * - Guaranteed non-overlapping hierarchical top-to-bottom layout.
 * - Multi-statement program support.
 * - Advanced branch & path highlighting on hover (ancestor + subtree focus).
 * - Click-to-pin inspector locking with active visual aura.
 * - Sleek card design with coordinate badges (L:C) and type indicators.
 * - Rock-solid stationary hover feedback (no boundary jitter / dancing).
 * - Zoom in / Zoom out / Pan / Reset controls.
 */

const AstVisualizer = (() => {
    // Layout Constants
    const NODE_WIDTH = 136;
    const NODE_HEIGHT = 52;
    const H_GAP = 28;
    const V_GAP = 64;
    const PADDING_X = 40;
    const PADDING_Y = 40;

    // Node Type Color Palette
    const COLOR_SCHEMES = {
        Program:    { fill: "#e0e7ff", stroke: "#6366f1", label: "PROGRAM" },
        Assignment: { fill: "#eff6ff", stroke: "#3b82f6", label: "ASSIGN" },
        BinaryOp:   { fill: "#f0fdf4", stroke: "#10b981", label: "BINARY OP" },
        UnaryOp:    { fill: "#fffbeb", stroke: "#f59e0b", label: "UNARY OP" },
        Identifier: { fill: "#faf5ff", stroke: "#8b5cf6", label: "ID" },
        Number:     { fill: "#fff1f2", stroke: "#f43f5e", label: "NUMBER" }
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
        svgElement = document.getElementById("astSvg");
        emptyStateElement = document.getElementById("astEmptyState");
        containerElement = document.getElementById("svgContainer");
        inspectorInfo = document.getElementById("inspectorInfo");

        // Pan and Zoom controls
        const zoomIn = document.getElementById("zoomInBtn");
        const zoomOut = document.getElementById("zoomOutBtn");
        const resetBtn = document.getElementById("resetZoomBtn");

        if (zoomIn) zoomIn.addEventListener("click", () => zoom(0.15));
        if (zoomOut) zoomOut.addEventListener("click", () => zoom(-0.15));
        if (resetBtn) resetBtn.addEventListener("click", resetView);

        // Container mouse drag panning
        if (containerElement) {
            containerElement.addEventListener("mousedown", handleMouseDown);
            window.addEventListener("mousemove", handleMouseMove);
            window.addEventListener("mouseup", handleMouseUp);
            containerElement.addEventListener("wheel", handleWheel, { passive: false });
        }

        // Clicking on canvas background unpins any active selection
        if (svgElement) {
            svgElement.addEventListener("click", (e) => {
                if (e.target === svgElement || e.target.id === "astTransformGroup") {
                    deselectNode();
                }
            });
        }
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
        if (inspectorInfo) {
            inspectorInfo.textContent = "Hover or click on any AST node to inspect its properties.";
        }
    }

    /**
     * Converts JSON AST into visual tree structure with parent links.
     */
    function buildVisualTree(node, parent = null) {
        if (!node) return null;

        let type = node.type;
        let title = type;
        let val = "";
        let details = "";
        let line = node.line || 1;
        let column = node.column || 1;

        switch (type) {
            case "Program":
                title = "Program";
                val = `${node.statements.length} stmt${node.statements.length === 1 ? '' : 's'}`;
                details = `Program root containing ${node.statements.length} statement(s).`;
                break;

            case "Assignment":
                title = "Assignment";
                val = "=";
                details = `Variable '${node.identifier.name}' assigned at line ${line}, col ${column}.`;
                break;

            case "BinaryOp":
                title = "BinaryOp";
                val = node.operator;
                details = `Binary Operation '${node.operator}' at line ${line}, col ${column}.`;
                break;

            case "UnaryOp":
                title = "UnaryOp";
                val = node.operator;
                details = `Unary Operator '${node.operator}' at line ${line}, col ${column}.`;
                break;

            case "Number":
                title = "Number";
                val = String(node.raw !== undefined ? node.raw : node.value);
                details = `Literal Constant ${val} (numeric value: ${node.value}) at line ${line}, col ${column}.`;
                break;

            case "Identifier":
                title = "Identifier";
                val = node.name;
                details = `Variable Identifier '${node.name}' at line ${line}, col ${column}.`;
                break;

            default:
                val = "?";
                details = `Unknown node ${type}`;
        }

        const visualNode = {
            id: null,
            type,
            title,
            val,
            details,
            line,
            column,
            rawNode: node,
            parent: parent,
            children: [],
            parentLink: null,
            domElement: null,
            x: 0,
            y: 0,
            subtreeWidth: 0
        };

        if (type === "Program") {
            visualNode.children = (node.statements || []).map(s => buildVisualTree(s, visualNode)).filter(Boolean);
        } else if (type === "Assignment") {
            visualNode.children = [
                buildVisualTree(node.identifier, visualNode),
                buildVisualTree(node.value, visualNode)
            ].filter(Boolean);
        } else if (type === "BinaryOp") {
            visualNode.children = [
                buildVisualTree(node.left, visualNode),
                buildVisualTree(node.right, visualNode)
            ].filter(Boolean);
        } else if (type === "UnaryOp") {
            visualNode.children = [
                buildVisualTree(node.operand, visualNode)
            ].filter(Boolean);
        }

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
     * Collect all nodes and connecting links for rendering.
     */
    function collectGraph(node, nodesOut, linksOut) {
        node.id = "ast-node-" + nodesOut.length;
        nodesOut.push(node);
        node.children.forEach(child => {
            const linkObj = {
                source: node,
                target: child,
                x1: node.x + NODE_WIDTH / 2,
                y1: node.y + NODE_HEIGHT,
                x2: child.x + NODE_WIDTH / 2,
                y2: child.y,
                domElement: null
            };
            child.parentLink = linkObj;
            linksOut.push(linkObj);
            collectGraph(child, nodesOut, linksOut);
        });
    }

    // -------------------------------------------------------------------------
    // Advanced Branch & Path Highlighting
    // -------------------------------------------------------------------------

    function highlightBranch(targetNode) {
        if (!targetNode) return;
        const activeNodes = new Set();
        const activeLinks = new Set();

        // 1. Ancestor chain to root
        let curr = targetNode;
        while (curr) {
            activeNodes.add(curr);
            if (curr.parentLink) activeLinks.add(curr.parentLink);
            curr = curr.parent;
        }

        // 2. Descendant subtree
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
            inspectorInfo.textContent = "Hover or click on any AST node to inspect its properties.";
            return;
        }

        const pinBadge = isPinned ? `<span class="inspector-badge badge-pinned">PINNED</span> ` : "";
        const typeBadge = `<span class="inspector-badge badge-ast">${node.title}</span>`;
        const posBadge = (node.line !== undefined && node.column !== undefined)
            ? `<span class="inspector-pos">L${node.line}:C${node.column}</span>`
            : "";
        inspectorInfo.innerHTML = `${pinBadge}${typeBadge} <strong>${node.val}</strong> &mdash; ${node.details} ${posBadge}`;
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
     * Main entry: Render AST into SVG.
     */
    function render(ast) {
        if (!ast) {
            clear();
            return;
        }

        // Determine effective root
        let rootNodeToRender = ast;
        if (ast.type === "Program" && ast.statements && ast.statements.length === 1) {
            rootNodeToRender = ast.statements[0];
        }

        const visualRoot = buildVisualTree(rootNodeToRender);
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

        const totalWidth = Math.max(600, maxX + PADDING_X);
        const totalHeight = Math.max(450, maxY + PADDING_Y);

        // Hide empty state, reveal SVG
        if (emptyStateElement) emptyStateElement.classList.add("hidden");
        svgElement.classList.remove("hidden");
        svgElement.innerHTML = "";

        svgElement.setAttribute("viewBox", `0 0 ${totalWidth} ${totalHeight}`);
        svgElement.setAttribute("width", totalWidth);
        svgElement.setAttribute("height", totalHeight);

        // SVG Gradients & Drop Shadows
        const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        defs.innerHTML = `
            <filter id="nodeCardShadow" x="-15%" y="-15%" width="130%" height="135%">
                <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#1e1b4b" flood-opacity="0.10" />
            </filter>
            <linearGradient id="grad-Program" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#4f46e5" />
                <stop offset="100%" stop-color="#6366f1" />
            </linearGradient>
            <linearGradient id="grad-Assignment" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#2563eb" />
                <stop offset="100%" stop-color="#3b82f6" />
            </linearGradient>
            <linearGradient id="grad-BinaryOp" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#059669" />
                <stop offset="100%" stop-color="#10b981" />
            </linearGradient>
            <linearGradient id="grad-UnaryOp" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#d97706" />
                <stop offset="100%" stop-color="#f59e0b" />
            </linearGradient>
            <linearGradient id="grad-Identifier" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#7c3aed" />
                <stop offset="100%" stop-color="#a855f7" />
            </linearGradient>
            <linearGradient id="grad-Number" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#e11d48" />
                <stop offset="100%" stop-color="#fb7185" />
            </linearGradient>
        `;
        svgElement.appendChild(defs);

        // Master transformation group for zoom/pan
        const gMaster = document.createElementNS("http://www.w3.org/2000/svg", "g");
        gMaster.id = "astTransformGroup";
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
            path.setAttribute("class", "ast-link");
            path.setAttribute("stroke", "#818cf8");
            path.setAttribute("stroke-width", "2.2");
            path.setAttribute("fill", "none");
            gLink.appendChild(path);

            // Starting junction dot
            const dot1 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            dot1.setAttribute("cx", link.x1);
            dot1.setAttribute("cy", link.y1);
            dot1.setAttribute("r", "3.2");
            dot1.setAttribute("fill", "#6366f1");
            gLink.appendChild(dot1);

            // Ending junction dot
            const dot2 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            dot2.setAttribute("cx", link.x2);
            dot2.setAttribute("cy", link.y2);
            dot2.setAttribute("r", "3.2");
            dot2.setAttribute("fill", "#6366f1");
            gLink.appendChild(dot2);

            gMaster.appendChild(gLink);
        });

        // 2. Render tree nodes
        allNodes.forEach(node => {
            const gNode = document.createElementNS("http://www.w3.org/2000/svg", "g");
            gNode.setAttribute("class", "ast-node");
            gNode.setAttribute("transform", `translate(${node.x}, ${node.y})`);
            node.domElement = gNode;

            const colors = COLOR_SCHEMES[node.type] || COLOR_SCHEMES.Assignment;

            // Card Base Rectangle with drop shadow & stable 2px stroke
            const cardBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            cardBg.setAttribute("class", "card-bg");
            cardBg.setAttribute("width", NODE_WIDTH);
            cardBg.setAttribute("height", NODE_HEIGHT);
            cardBg.setAttribute("fill", "#ffffff");
            cardBg.setAttribute("stroke", colors.stroke);
            cardBg.setAttribute("stroke-width", "2");
            cardBg.setAttribute("rx", "10");
            cardBg.setAttribute("ry", "10");
            cardBg.setAttribute("filter", "url(#nodeCardShadow)");
            gNode.appendChild(cardBg);

            // Top Header Accent Banner with gradient fill
            const headerBanner = document.createElementNS("http://www.w3.org/2000/svg", "path");
            const w = NODE_WIDTH;
            const r = 10;
            const hHeader = 20;
            const bannerPath = `M 0 ${r} A ${r} ${r} 0 0 1 ${r} 0 L ${w - r} 0 A ${r} ${r} 0 0 1 ${w} ${r} L ${w} ${hHeader} L 0 ${hHeader} Z`;
            headerBanner.setAttribute("d", bannerPath);
            headerBanner.setAttribute("fill", `url(#grad-${node.type})`);
            gNode.appendChild(headerBanner);

            // Node Type Text (left/center header)
            const textType = document.createElementNS("http://www.w3.org/2000/svg", "text");
            textType.setAttribute("x", (node.line !== undefined && node.column !== undefined) ? 10 : NODE_WIDTH / 2);
            textType.setAttribute("y", 14);
            textType.setAttribute("text-anchor", (node.line !== undefined && node.column !== undefined) ? "start" : "middle");
            textType.setAttribute("fill", "#ffffff");
            textType.setAttribute("class", "node-text-type");
            textType.setAttribute("font-size", "9.5");
            textType.setAttribute("font-weight", "700");
            textType.setAttribute("letter-spacing", "0.06em");
            textType.textContent = (colors.label || node.title).toUpperCase();
            gNode.appendChild(textType);

            // Source Coordinate Badge (top right of banner)
            if (node.line !== undefined && node.column !== undefined && node.type !== "Program") {
                const textPos = document.createElementNS("http://www.w3.org/2000/svg", "text");
                textPos.setAttribute("x", NODE_WIDTH - 8);
                textPos.setAttribute("y", 14);
                textPos.setAttribute("text-anchor", "end");
                textPos.setAttribute("fill", "rgba(255, 255, 255, 0.88)");
                textPos.setAttribute("font-size", "8.5");
                textPos.setAttribute("font-weight", "600");
                textPos.setAttribute("font-family", "'Fira Code', Consolas, monospace");
                textPos.textContent = `L${node.line}:C${node.column}`;
                gNode.appendChild(textPos);
            }

            // Node Value Text (bottom body)
            const textVal = document.createElementNS("http://www.w3.org/2000/svg", "text");
            textVal.setAttribute("x", NODE_WIDTH / 2);
            textVal.setAttribute("y", 39);
            textVal.setAttribute("text-anchor", "middle");
            textVal.setAttribute("fill", "#0f172a");
            textVal.setAttribute("class", "node-text-val");
            textVal.setAttribute("font-size", "13");
            textVal.setAttribute("font-weight", "600");
            textVal.setAttribute("font-family", "'Fira Code', Consolas, monospace");
            const displayVal = node.val.length > 13 ? node.val.substring(0, 11) + "..." : node.val;
            textVal.textContent = displayVal;
            gNode.appendChild(textVal);

            // Hover and Click events (Zero boundary oscillation)
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
                    // Toggle unpin
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

    // -------------------------------------------------------------------------
    // Pan & Zoom Controls
    // -------------------------------------------------------------------------

    function updateTransform() {
        const gMaster = document.getElementById("astTransformGroup");
        if (gMaster) {
            gMaster.setAttribute(
                "transform",
                `translate(${translateX}, ${translateY}) scale(${currentScale})`
            );
        }
    }

    function zoom(delta) {
        const newScale = Math.min(2.5, Math.max(0.4, currentScale + delta));
        currentScale = parseFloat(newScale.toFixed(2));
        updateTransform();
    }

    function resetView() {
        currentScale = 1.0;
        translateX = 0;
        translateY = 0;
        updateTransform();
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
        updateTransform();
    }

    function handleMouseUp() {
        isPanning = false;
        if (containerElement) containerElement.style.cursor = "grab";
    }

    function handleWheel(e) {
        if (e.ctrlKey) {
            e.preventDefault();
            const delta = e.deltaY < 0 ? 0.1 : -0.1;
            zoom(delta);
        }
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
