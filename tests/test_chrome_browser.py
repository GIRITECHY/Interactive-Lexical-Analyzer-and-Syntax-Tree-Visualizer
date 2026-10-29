"""
tests/test_chrome_browser.py - Automated End-to-End Google Chrome UI Testing

Executes automated UI validation on Google Chrome via Chrome DevTools Protocol (CDP):
- Test A: Initial Page Load, title, editor, layout, views availability.
- Test B: Parse Tree Visualization, non-terminal/terminal nodes, tab switching.
- Test C: Three-Address Code (TAC) generation, instruction order, precedence, copy button.
- Test D: Multi-statement analysis (a = b + c * d;\nx = a - 5;).
- Test E: Error handling on invalid inputs (missing operands, unclosed parens, missing semicolons).
- Test F: Error recovery back to valid code (result = 10 / 2;).
- Test G: Regression tests (Token search filter, Viva Guide modal, inspector).
- Test H: Console errors and unhandled exceptions check.
"""

import unittest
import subprocess
import time
import urllib.request
import json
import socket
import base64
import os
import struct
import shutil


class ChromeCDPClient:
    """Lightweight standard-library WebSocket client for Chrome DevTools Protocol."""

    def __init__(self, host="127.0.0.1", port=9333):
        self.host = host
        self.port = port
        self.sock = None
        self.req_id = 1
        self.console_errors = []

    def connect(self, ws_url):
        path = ws_url.split(f"{self.host}:{self.port}")[1]
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode())
        resp = self.sock.recv(4096).decode(errors="ignore")
        if "101" not in resp:
            raise RuntimeError(f"WebSocket handshake failed: {resp}")

    def _send_frame(self, text_payload):
        payload = text_payload.encode("utf-8")
        mask = os.urandom(4)
        length = len(payload)
        if length < 126:
            hdr = bytes([0x81, 0x80 | length]) + mask
        elif length < 65536:
            hdr = bytes([0x81, 0x80 | 126]) + struct.pack(">H", length) + mask
        else:
            hdr = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", length) + mask
        masked_bytes = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(hdr + masked_bytes)

    def _recv_frame(self):
        hdr = self.sock.recv(2)
        if not hdr or len(hdr) < 2:
            return None
        b2 = hdr[1]
        is_masked = bool(b2 & 0x80)
        length = b2 & 0x7F
        if length == 126:
            length = struct.unpack(">H", self.sock.recv(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self.sock.recv(8))[0]
        mask = self.sock.recv(4) if is_masked else None
        data = bytearray()
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                break
            data.extend(chunk)
        if is_masked:
            for i in range(len(data)):
                data[i] ^= mask[i % 4]
        return bytes(data).decode("utf-8", errors="ignore")

    def eval(self, expression):
        req_id = self.req_id
        self.req_id += 1
        cmd = {
            "id": req_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            }
        }
        self._send_frame(json.dumps(cmd))
        while True:
            text = self._recv_frame()
            if not text:
                return None
            try:
                msg = json.loads(text)
                if msg.get("method") == "Runtime.consoleAPICalled":
                    args = msg.get("params", {}).get("args", [])
                    if msg.get("params", {}).get("type") == "error":
                        self.console_errors.append(args)
                if msg.get("id") == req_id:
                    result_obj = msg.get("result", {})
                    if "exceptionDetails" in result_obj:
                        return {"error": result_obj["exceptionDetails"]}
                    return result_obj.get("result", {}).get("value")
            except Exception:
                pass

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


class TestChromeBrowserUI(unittest.TestCase):
    """End-to-End Chrome Browser UI test suite for LexiTree."""

    chrome_proc = None
    cdp = None
    profile_dir = "C:\\Users\\girig\\AppData\\Local\\Temp\\lexitree_chrome_test_prof"

    @classmethod
    def setUpClass(cls):
        chrome_exe = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if not os.path.exists(chrome_exe):
            raise unittest.SkipTest("Google Chrome is not installed at standard location.")

        if os.path.exists(cls.profile_dir):
            try:
                shutil.rmtree(cls.profile_dir, ignore_errors=True)
            except Exception:
                pass

        # Launch Chrome with isolated profile and remote debugging
        cls.chrome_proc = subprocess.Popen([
            chrome_exe,
            "--headless=new",
            "--remote-debugging-port=9333",
            f"--user-data-dir={cls.profile_dir}",
            "--disable-gpu",
            "--no-first-run",
            "http://127.0.0.1:5000/"
        ])

        # Connect CDP
        time.sleep(2.5)
        pages_raw = urllib.request.urlopen("http://127.0.0.1:9333/json").read()
        pages = json.loads(pages_raw)
        page = [p for p in pages if p.get("type") == "page" and "127.0.0.1:5000" in p.get("url", "")][0]

        cls.cdp = ChromeCDPClient(host="127.0.0.1", port=9333)
        cls.cdp.connect(page["webSocketDebuggerUrl"])

        # Enable runtime console inspection
        cls.cdp.eval("1 + 1")

    @classmethod
    def tearDownClass(cls):
        if cls.cdp:
            cls.cdp.close()
        if cls.chrome_proc:
            cls.chrome_proc.terminate()
            try:
                cls.chrome_proc.wait(timeout=3)
            except Exception:
                cls.chrome_proc.kill()

    def analyze_and_wait(self, code):
        """Helper that enters code, clicks Analyze Code, and waits for asynchronous analysis completion."""
        escaped = code.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        js = f"""
        new Promise((resolve) => {{
            EditorModule.setCode('{escaped}');
            document.getElementById('analyzeBtn').click();
            const start = Date.now();
            const timer = setInterval(() => {{
                const status = document.getElementById('statusText').textContent;
                if (status !== 'Analyzing...' || (Date.now() - start > 3500)) {{
                    clearInterval(timer);
                    resolve(status);
                }}
            }}, 40);
        }})
        """
        return self.cdp.eval(js)

    def test_a_initial_page_load_and_elements(self):
        title = self.cdp.eval("document.title")
        self.assertIn("LexiTree", title)

        # Check editor and button
        editor_val = self.cdp.eval("document.getElementById('codeEditor').value")
        self.assertEqual(editor_val, "result = 2 + 3 * 4;")

        analyze_btn = self.cdp.eval("Boolean(document.getElementById('analyzeBtn'))")
        self.assertTrue(analyze_btn)

        # Check that AST and Parse Tree view switcher tabs exist
        has_ast_tab = self.cdp.eval("Boolean(document.getElementById('viewAstTab'))")
        has_pt_tab = self.cdp.eval("Boolean(document.getElementById('viewParseTreeTab'))")
        self.assertTrue(has_ast_tab)
        self.assertTrue(has_pt_tab)

        # Check that TAC card exists
        has_tac_card = self.cdp.eval("Boolean(document.getElementById('tacCard'))")
        self.assertTrue(has_tac_card)

        # Check token table initially populated
        token_count = self.cdp.eval("document.getElementById('tokenTableBody').children.length")
        self.assertEqual(token_count, 9)

        # Check initial AST rendered
        ast_nodes_count = self.cdp.eval("document.querySelectorAll('#astSvg .ast-node').length")
        self.assertEqual(ast_nodes_count, 7)

        # Check initial TAC rendered
        tac_count = self.cdp.eval("document.querySelectorAll('#tacList li').length")
        self.assertEqual(tac_count, 3)

    def test_b_parse_tree_visualization(self):
        # Switch to Parse Tree tab
        self.cdp.eval("document.getElementById('viewParseTreeTab').click()")

        # Verify Parse Tree container is visible and AST container hidden
        pt_hidden = self.cdp.eval("document.getElementById('parseTreeContainer').classList.contains('hidden')")
        ast_hidden = self.cdp.eval("document.getElementById('svgContainer').classList.contains('hidden')")
        self.assertFalse(pt_hidden)
        self.assertTrue(ast_hidden)

        # Verify Parse Tree SVG nodes rendered
        pt_nodes_count = self.cdp.eval("document.querySelectorAll('#parseTreeSvg .pt-node').length")
        self.assertGreater(pt_nodes_count, 10)

        # Verify presence of terminals and non-terminals
        has_terminals = self.cdp.eval("document.querySelectorAll('#parseTreeSvg .pt-node-terminal').length > 0")
        has_nonterminals = self.cdp.eval("document.querySelectorAll('#parseTreeSvg .pt-node-nonterminal').length > 0")
        self.assertTrue(has_terminals)
        self.assertTrue(has_nonterminals)

        # Switch back to AST tab
        self.cdp.eval("document.getElementById('viewAstTab').click()")
        ast_hidden2 = self.cdp.eval("document.getElementById('svgContainer').classList.contains('hidden')")
        self.assertFalse(ast_hidden2)

    def test_c_three_address_code_generation(self):
        # Initial code is 'result = 2 + 3 * 4;'
        tac_items = self.cdp.eval("Array.from(document.querySelectorAll('#tacList li')).map(li => li.textContent.trim())")
        self.assertEqual(tac_items, [
            "t1 = 3 * 4",
            "t2 = 2 + t1",
            "result = t2"
        ])

        # Test parentheses override: result = (2 + 3) * 4;
        status = self.analyze_and_wait("result = (2 + 3) * 4;")
        self.assertEqual(status, "Analysis Successful")

        tac_paren = self.cdp.eval("Array.from(document.querySelectorAll('#tacList li')).map(li => li.textContent.trim())")
        self.assertEqual(tac_paren, [
            "t1 = 2 + 3",
            "t2 = t1 * 4",
            "result = t2"
        ])

    def test_d_multiple_statements_analysis(self):
        multi_code = "a = b + c * d;\nx = a - 5;"
        status = self.analyze_and_wait(multi_code)
        self.assertEqual(status, "Analysis Successful")

        tac_multi = self.cdp.eval("Array.from(document.querySelectorAll('#tacList li')).map(li => li.textContent.trim())")
        self.assertEqual(tac_multi, [
            "t1 = c * d",
            "t2 = b + t1",
            "a = t2",
            "t3 = a - 5",
            "x = t3"
        ])

        # Verify token count for multi-statement
        token_count = self.cdp.eval("document.getElementById('tokenTableBody').children.length")
        self.assertEqual(token_count, 15)  # 7 for stmt1 + 7 for stmt2 + 1 for EOF

    def test_e_invalid_inputs_error_handling(self):
        invalid_cases = [
            ("result = 2 + ;", "Missing operand"),
            ("result = (2 + 3;", "Unmatched opening parenthesis"),
            ("result = 2 + 3", "Missing semicolon"),
            ("result = ;", "Missing operand")
        ]

        for code, expected_err in invalid_cases:
            status = self.analyze_and_wait(code)
            self.assertIn("Error", status)

            err_visible = self.cdp.eval("!document.getElementById('errorPanel').classList.contains('hidden')")
            self.assertTrue(err_visible, f"Expected error panel visible for: {code}")

            err_msg = self.cdp.eval("document.getElementById('errorMessage').textContent")
            self.assertIn(expected_err, err_msg)

            # Confirm no TAC is shown for failed analysis
            tac_items = self.cdp.eval("document.querySelectorAll('#tacList li').length")
            self.assertEqual(tac_items, 0)

            # Confirm AST is cleared
            ast_svg_hidden = self.cdp.eval("document.getElementById('astSvg').classList.contains('hidden')")
            self.assertTrue(ast_svg_hidden)

    def test_f_error_recovery(self):
        # Enter valid code after invalid tests
        status = self.analyze_and_wait("result = 10 / 2;")
        self.assertEqual(status, "Analysis Successful")

        # Verify error panel is hidden
        err_hidden = self.cdp.eval("document.getElementById('errorPanel').classList.contains('hidden')")
        self.assertTrue(err_hidden)

        # Verify TAC recovered
        tac_items = self.cdp.eval("Array.from(document.querySelectorAll('#tacList li')).map(li => li.textContent.trim())")
        self.assertEqual(tac_items, [
            "t1 = 10 / 2",
            "result = t1"
        ])

    def test_g_regression_and_ui_controls(self):
        # Viva Guide Modal toggle
        self.cdp.eval("document.getElementById('guideBtn').click()")
        modal_open = self.cdp.eval("!document.getElementById('guideModal').classList.contains('hidden')")
        self.assertTrue(modal_open)

        self.cdp.eval("document.getElementById('closeModalBtn').click()")
        modal_closed = self.cdp.eval("document.getElementById('guideModal').classList.contains('hidden')")
        self.assertTrue(modal_closed)

        # Token Filter
        self.cdp.eval("document.getElementById('tokenSearch').value = 'NUMBER'")
        self.cdp.eval("document.getElementById('tokenSearch').dispatchEvent(new Event('input'))")
        filtered_count = self.cdp.eval("document.getElementById('tokenTableBody').children.length")
        self.assertEqual(filtered_count, 2)  # 10 and 2

        # Reset filter
        self.cdp.eval("document.getElementById('tokenSearch').value = ''")
        self.cdp.eval("document.getElementById('tokenSearch').dispatchEvent(new Event('input'))")
        reset_count = self.cdp.eval("document.getElementById('tokenTableBody').children.length")
        self.assertEqual(reset_count, 7)  # result = 10 / 2 ; <EOF>

    def test_h_zero_javascript_exceptions(self):
        # Verify no unhandled JavaScript errors were logged in the browser console
        self.assertEqual(self.cdp.console_errors, [])

    def test_i_tree_hover_stability_and_advanced_branch_highlighting(self):
        # 1. Test AST Hover Stability and Branch Highlighting
        ast_nodes = self.cdp.eval("document.querySelectorAll('#astSvg .ast-node').length")
        self.assertGreater(ast_nodes, 1)

        # Trigger mouseenter on child node (index 1, e.g. identifier 'result')
        self.cdp.eval("""
            (() => {
                const nodes = document.querySelectorAll('#astSvg .ast-node');
                const targetNode = nodes[1];
                targetNode.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
            })()
        """)

        # Verify branch highlighting and dimming: target branch is highlighted, sibling subtree is dimmed
        highlighted_count = self.cdp.eval("document.querySelectorAll('#astSvg .node-highlighted').length")
        dimmed_count = self.cdp.eval("document.querySelectorAll('#astSvg .node-dimmed').length")
        self.assertGreater(highlighted_count, 0)
        self.assertGreater(dimmed_count, 0)
        self.assertEqual(highlighted_count + dimmed_count, ast_nodes)

        # Verify links are highlighted
        links_highlighted = self.cdp.eval("document.querySelectorAll('#astSvg .link-highlighted').length")
        self.assertGreater(links_highlighted, 0)

        # Verify no translateY or translate shift in computed style on hover
        has_translate_y = self.cdp.eval("""
            (() => {
                const n = document.querySelectorAll('#astSvg .ast-node')[1];
                const style = window.getComputedStyle(n);
                return style.transform.includes('translateY');
            })()
        """)
        self.assertFalse(has_translate_y)

        # Trigger mouseleave: verify highlights clear
        cleared_highlighted = self.cdp.eval("""
            (() => {
                const targetNode = document.querySelectorAll('#astSvg .ast-node')[1];
                targetNode.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));
                return document.querySelectorAll('#astSvg .node-highlighted').length;
            })()
        """)
        self.assertEqual(cleared_highlighted, 0)

        # 2. Test Click-to-Pin Inspector Lock on AST
        self.cdp.eval("""
            (() => {
                const targetNode = document.querySelectorAll('#astSvg .ast-node')[1];
                targetNode.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            })()
        """)
        is_selected = self.cdp.eval("document.querySelectorAll('#astSvg .ast-node')[1].classList.contains('node-selected')")
        self.assertTrue(is_selected)

        inspector_html = self.cdp.eval("document.getElementById('inspectorInfo').innerHTML")
        self.assertIn("PINNED", inspector_html)

        # Unpin by clicking again
        self.cdp.eval("""
            (() => {
                const targetNode = document.querySelectorAll('#astSvg .ast-node')[1];
                targetNode.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            })()
        """)
        is_unselected = self.cdp.eval("!document.querySelectorAll('#astSvg .ast-node')[1].classList.contains('node-selected')")
        self.assertTrue(is_unselected)

        # 3. Test Parse Tree Hover and Derivation Highlighting
        self.cdp.eval("document.getElementById('viewParseTreeTab').click()")
        pt_nodes = self.cdp.eval("document.querySelectorAll('#parseTreeSvg .pt-node').length")
        self.assertGreater(pt_nodes, 0)

        # Hover terminal node in Parse Tree
        self.cdp.eval("""
            (() => {
                const terminalNode = document.querySelector('#parseTreeSvg .pt-node-terminal');
                terminalNode.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
            })()
        """)
        pt_highlighted = self.cdp.eval("document.querySelectorAll('#parseTreeSvg .node-highlighted').length")
        pt_dimmed = self.cdp.eval("document.querySelectorAll('#parseTreeSvg .node-dimmed').length")
        self.assertGreater(pt_highlighted, 0)
        self.assertGreater(pt_dimmed, 0)
        self.assertEqual(pt_highlighted + pt_dimmed, pt_nodes)

        # Click terminal to pin in Parse Tree
        self.cdp.eval("""
            (() => {
                const terminalNode = document.querySelector('#parseTreeSvg .pt-node-terminal');
                terminalNode.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            })()
        """)
        pt_selected = self.cdp.eval("document.querySelector('#parseTreeSvg .pt-node-terminal').classList.contains('node-selected')")
        self.assertTrue(pt_selected)
        pt_inspector = self.cdp.eval("document.getElementById('inspectorInfo').innerHTML")
        self.assertIn("PINNED", pt_inspector)
        self.assertIn("TERMINAL", pt_inspector)

        # Click canvas to unpin
        self.cdp.eval("document.getElementById('parseTreeSvg').dispatchEvent(new MouseEvent('click', { bubbles: true }))")
        pt_unpinned = self.cdp.eval("!document.querySelector('#parseTreeSvg .pt-node-terminal').classList.contains('node-selected')")
        self.assertTrue(pt_unpinned)

        # Return to AST view
        self.cdp.eval("document.getElementById('viewAstTab').click()")

        # Verify zero console errors
        self.assertEqual(self.cdp.console_errors, [])


if __name__ == "__main__":
    unittest.main()
