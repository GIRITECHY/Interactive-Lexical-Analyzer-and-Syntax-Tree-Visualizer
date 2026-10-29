"""
tests/test_api.py - Integration and API Endpoint Tests for LexiTree

Tests:
1. GET /: Serves main interface (200 OK).
2. POST /api/analyze: Valid single assignment.
3. POST /api/analyze: Operator precedence arithmetic (result = 2 + 3 * 4;).
4. POST /api/analyze: Parentheses precedence override (result = (2 + 3) * 4;).
5. POST /api/analyze: Multi-statement TAC and Parse Tree (a = b + c * d;\nx = a - 5;).
6. POST /api/analyze: Syntax error handling (result = 2 + ;).
7. POST /api/analyze: Lexical error handling (x = 10 @ 2;).
8. POST /api/analyze: Empty source code input.
9. POST /api/analyze: Missing source_code field or non-string payload.
10. POST /api/analyze: Content-Type validation (requires application/json).
11. POST /api/analyze: State isolation across consecutive requests.
12. POST /api/analyze: Payload size limit enforcement (> 64 KB).
"""

import unittest
import json
from app import app


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for LexiTree Flask routing and API responses."""

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_get_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LexiTree", response.data)
        self.assertIn(b"parseTreeSvg", response.data)
        self.assertIn(b"tacCard", response.data)

    def test_analyze_simple_assignment(self):
        payload = {"source_code": "x = 10;"}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["ast"])
        self.assertIsNotNone(data["parse_tree"])
        self.assertEqual(data["intermediate_code"], ["x = 10"])
        self.assertEqual(len(data["lexical_errors"]), 0)
        self.assertIsNone(data["syntax_error"])

    def test_analyze_operator_precedence(self):
        # result = 2 + 3 * 4;
        payload = {"source_code": "result = 2 + 3 * 4;"}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["intermediate_code"], [
            "t1 = 3 * 4",
            "t2 = 2 + t1",
            "result = t2"
        ])
        self.assertEqual(data["parse_tree"]["symbol"], "program")

    def test_analyze_parentheses_override(self):
        # result = (2 + 3) * 4;
        payload = {"source_code": "result = (2 + 3) * 4;"}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["intermediate_code"], [
            "t1 = 2 + 3",
            "t2 = t1 * 4",
            "result = t2"
        ])

    def test_analyze_multi_statement(self):
        # a = b + c * d;\nx = a - 5;
        payload = {"source_code": "a = b + c * d;\nx = a - 5;"}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["intermediate_code"], [
            "t1 = c * d",
            "t2 = b + t1",
            "a = t2",
            "t3 = a - 5",
            "x = t3"
        ])
        self.assertEqual(len(data["ast"]["statements"]), 2)

    def test_analyze_syntax_error(self):
        # result = 2 + ;
        payload = {"source_code": "result = 2 + ;"}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIsNotNone(data["syntax_error"])
        self.assertIn("Missing operand", data["syntax_error"]["message"])
        self.assertIsNone(data["ast"])
        self.assertIsNone(data["parse_tree"])
        self.assertEqual(data["intermediate_code"], [])

    def test_analyze_lexical_error(self):
        # x = 10 @ 2;
        payload = {"source_code": "x = 10 @ 2;"}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertGreater(len(data["lexical_errors"]), 0)
        self.assertIn("@", data["lexical_errors"][0]["message"])
        self.assertIsNone(data["ast"])
        self.assertIsNone(data["parse_tree"])
        self.assertEqual(data["intermediate_code"], [])

    def test_analyze_empty_source(self):
        payload = {"source_code": "   \n\t  "}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIsNotNone(data["syntax_error"])
        self.assertIn("Source code is empty", data["syntax_error"]["message"])

    def test_analyze_invalid_content_type(self):
        response = self.client.post(
            "/api/analyze",
            data="not a json",
            content_type="text/plain"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_analyze_non_string_source_code(self):
        payload = {"source_code": 12345}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_analyze_payload_too_large(self):
        oversized = "x = 1;\n" * 15000  # > 64 KB
        payload = {"source_code": oversized}
        response = self.client.post(
            "/api/analyze",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("maximum allowed size", data["syntax_error"]["message"])

    def test_state_isolation_between_requests(self):
        # Request 1
        res1 = self.client.post(
            "/api/analyze",
            data=json.dumps({"source_code": "a = 1 + 2;"}),
            content_type="application/json"
        ).get_json()
        # Request 2
        res2 = self.client.post(
            "/api/analyze",
            data=json.dumps({"source_code": "b = 3 + 4;"}),
            content_type="application/json"
        ).get_json()

        self.assertEqual(res1["intermediate_code"][0], "t1 = 1 + 2")
        self.assertEqual(res2["intermediate_code"][0], "t1 = 3 + 4")


if __name__ == "__main__":
    unittest.main()

