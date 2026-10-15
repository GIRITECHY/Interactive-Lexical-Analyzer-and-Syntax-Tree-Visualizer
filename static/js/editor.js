/**
 * editor.js - Source Code Editor Controller for LexiTree
 * Handles line numbering, example presets, character/line counts,
 * Tab-key indentation, and modal dialog toggles.
 */

const EditorModule = (() => {
    // Example Programs Catalog
    const EXAMPLES = {
        ex1: "x = 10;",
        ex2: "result = 2 + 3 * 4;",
        ex3: "result = (2 + 3) * 4;",
        ex4: "a = 10;\nb = 20;\ntotal = a + b;",
        ex5: "x = -5;\ny = -(x + 3);",
        err1: "x = 10 + ;",
        err2: "x = 10",
        err3: "x = (10 + 5;",
        err4: "x = 10 @ 2;"
    };

    let editor, lineNumbers, charCount, lineCount, exampleSelector, clearBtn;
    let guideModal, guideBtn, closeModalBtn, closeModalFooterBtn;

    function init() {
        editor = document.getElementById("codeEditor");
        lineNumbers = document.getElementById("lineNumbers");
        charCount = document.getElementById("charCount");
        lineCount = document.getElementById("lineCount");
        exampleSelector = document.getElementById("exampleSelector");
        clearBtn = document.getElementById("clearBtn");

        guideModal = document.getElementById("guideModal");
        guideBtn = document.getElementById("guideBtn");
        closeModalBtn = document.getElementById("closeModalBtn");
        closeModalFooterBtn = document.getElementById("closeModalFooterBtn");

        // Event listeners
        editor.addEventListener("input", updateEditorStats);
        editor.addEventListener("scroll", syncScroll);
        editor.addEventListener("keydown", handleKeydown);

        exampleSelector.addEventListener("change", handleExampleSelect);
        clearBtn.addEventListener("click", handleClear);

        // Quick Preset Chips
        document.querySelectorAll(".preset-chip").forEach(chip => {
            chip.addEventListener("click", () => {
                const presetKey = chip.getAttribute("data-preset");
                if (EXAMPLES[presetKey]) {
                    editor.value = EXAMPLES[presetKey];
                    exampleSelector.value = presetKey;
                    updateEditorStats();
                    // Trigger analyze automatically for fast interaction
                    const analyzeBtn = document.getElementById("analyzeBtn");
                    if (analyzeBtn) analyzeBtn.click();
                }
            });
        });

        // Modal triggers
        guideBtn.addEventListener("click", () => guideModal.classList.remove("hidden"));
        closeModalBtn.addEventListener("click", () => guideModal.classList.add("hidden"));
        closeModalFooterBtn.addEventListener("click", () => guideModal.classList.add("hidden"));
        guideModal.addEventListener("click", (e) => {
            if (e.target === guideModal) guideModal.classList.add("hidden");
        });

        // Set default starter code
        editor.value = "result = 2 + 3 * 4;";
        updateEditorStats();
    }

    function updateEditorStats() {
        const text = editor.value;
        const lines = text.split("\n");
        const count = lines.length;

        // Generate line numbers
        const numArr = [];
        for (let i = 1; i <= count; i++) {
            numArr.push(i);
        }
        lineNumbers.innerText = numArr.join("\n");

        // Update stats
        charCount.innerText = `${text.length} chars`;
        lineCount.innerText = `${count} ${count === 1 ? 'line' : 'lines'}`;
    }

    function syncScroll() {
        lineNumbers.scrollTop = editor.scrollTop;
    }

    function handleKeydown(e) {
        // Tab key support for 4 spaces
        if (e.key === "Tab") {
            e.preventDefault();
            const start = editor.selectionStart;
            const end = editor.selectionEnd;
            const spaces = "    ";
            editor.value = editor.value.substring(0, start) + spaces + editor.value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + 4;
            updateEditorStats();
        }
    }

    function handleExampleSelect(e) {
        const key = e.target.value;
        if (EXAMPLES[key]) {
            editor.value = EXAMPLES[key];
            updateEditorStats();
        }
    }

    function handleClear() {
        editor.value = "";
        exampleSelector.value = "";
        updateEditorStats();
        editor.focus();
    }

    function getCode() {
        return editor.value;
    }

    function setCode(code) {
        editor.value = code;
        updateEditorStats();
    }

    return {
        init,
        getCode,
        setCode
    };
})();
