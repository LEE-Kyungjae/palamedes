#!/usr/bin/env python3
import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from typing import Any, Dict, List, Optional

from palamedes_agent import execute_tool, list_tools, natural_language_to_tool
from palamedes_host_contract import host_action_contract
from palamedes import (
    CONTRACT_VERSION,
    IMPLEMENTATION_VERSION,
    PlanConflictError,
    contracts_catalog,
    cycle_snapshot,
    doctor_report,
    normalize_fingerprint,
)


class PalamedesHandler(BaseHTTPRequestHandler):
    server_version = "PalamedesHTTP/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/health":
            result = execute_tool("get_health", {})
            status = HTTPStatus.OK if result.get("status") == "ok" else HTTPStatus.SERVICE_UNAVAILABLE if result.get("status") == "error" else HTTPStatus.OK
            self._write_json(status, result)
            return
        if path == "/doctor":
            result = doctor_report()
            status = HTTPStatus.OK if result.get("status") == "ok" else HTTPStatus.SERVICE_UNAVAILABLE if result.get("status") == "error" else HTTPStatus.OK
            self._write_json(status, result)
            return
        if path == "/plan":
            result = execute_tool("get_plan", {})
            self._write_json(HTTPStatus.OK, result, extra_headers={"ETag": self._format_etag(result["fingerprint"])})
            return
        if path == "/qa":
            self._write_json(HTTPStatus.OK, execute_tool("get_qa", {}))
            return
        if path == "/cycle":
            try:
                history_limit = int(query.get("limit", ["10"])[0])
            except ValueError:
                self._write_error(HTTPStatus.BAD_REQUEST, "limit must be an integer", operation="cycle_snapshot", step="query")
                return
            if history_limit < 0:
                self._write_error(HTTPStatus.BAD_REQUEST, "limit must be non-negative", operation="cycle_snapshot", step="query")
                return
            result = cycle_snapshot(history_limit=history_limit)
            self._write_json(HTTPStatus.OK, result, extra_headers={"ETag": self._format_etag(result["fingerprint"])})
            return
        if path == "/history":
            self._write_json(HTTPStatus.OK, execute_tool("get_history", {}))
            return
        if path == "/reviews":
            payload: Dict[str, Any] = {}
            for key in ["status", "scope", "assigned_to", "sort_by", "order"]:
                value = str(query.get(key, [""])[0]).strip()
                if value:
                    payload[key] = value
            if "limit" in query:
                try:
                    payload["limit"] = int(query.get("limit", ["20"])[0])
                except ValueError:
                    self._write_error(HTTPStatus.BAD_REQUEST, "limit must be an integer", operation="list_reviews", step="query")
                    return
            self._write_json(HTTPStatus.OK, execute_tool("list_reviews", payload))
            return
        if path == "/reviews/inbox":
            payload: Dict[str, Any] = {
                "status": "open",
                "sort_by": "priority",
                "order": "desc",
            }
            assignee = str(query.get("assignee", [""])[0]).strip()
            if assignee:
                payload["assigned_to"] = assignee
            if "limit" in query:
                try:
                    payload["limit"] = int(query.get("limit", ["20"])[0])
                except ValueError:
                    self._write_error(HTTPStatus.BAD_REQUEST, "limit must be an integer", operation="list_reviews", step="query")
                    return
            self._write_json(HTTPStatus.OK, execute_tool("list_reviews", payload))
            return
        if path.startswith("/reviews/"):
            request_id = path.split("/", 2)[2].strip()
            if not request_id:
                self._write_error(HTTPStatus.NOT_FOUND, "not_found", kind="not_found")
                return
            try:
                self._write_json(HTTPStatus.OK, execute_tool("get_review", {"request_id": request_id}))
            except ValueError as exc:
                self._write_error(HTTPStatus.NOT_FOUND, str(exc), kind="not_found", operation="get_review", step="lookup")
            return
        if path == "/validate":
            self._write_json(HTTPStatus.OK, execute_tool("validate_plan", {}))
            return
        if path == "/tools":
            self._write_json(HTTPStatus.OK, self._tool_catalog_response())
            return
        if path.startswith("/tools/"):
            tool_name = path.split("/", 2)[2].strip()
            tool = self._tool_schema(tool_name)
            if not tool:
                self._write_error(HTTPStatus.NOT_FOUND, f"unknown tool: {tool_name}", operation=tool_name or "tool_lookup", step="lookup")
                return
            self._write_json(HTTPStatus.OK, self._tool_detail_response(tool))
            return
        if path == "/contracts":
            self._write_json(HTTPStatus.OK, contracts_catalog())
            return
        if path == "/host/action-contract":
            role = str(query.get("role", ["planner"])[0]).strip() or "planner"
            try:
                contract = host_action_contract(role)
            except ValueError as exc:
                self._write_error(HTTPStatus.BAD_REQUEST, str(exc), operation="host_action_contract", step="lookup")
                return
            self._write_json(HTTPStatus.OK, contract)
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:
        payload = self._read_json()
        if payload is None:
            return
        path = urlparse(self.path).path
        expected_fingerprint = self._expected_fingerprint()

        if path == "/plan":
            self._execute_tool_json("update_plan", payload, expected_fingerprint)
            return

        if path == "/evidence":
            self._execute_tool_json("add_evidence", payload, expected_fingerprint)
            return

        if path.startswith("/reviews/"):
            request_id = path.split("/", 2)[2].strip()
            if not request_id:
                self._write_error(HTTPStatus.NOT_FOUND, "not_found", kind="not_found")
                return
            if "request_id" not in payload:
                payload["request_id"] = request_id
            elif str(payload.get("request_id", "")).strip() != request_id:
                self._write_error(HTTPStatus.BAD_REQUEST, "request_id must match review resource", operation="update_review", step="input")
                return
            self._execute_tool_json("update_review", payload, expected_fingerprint)
            return

        if path == "/replan":
            self._execute_tool_json("replan", payload, expected_fingerprint)
            return

        if path == "/restore/preview":
            self._execute_tool_json("preview_restore", payload, None)
            return

        if path == "/restore":
            self._execute_tool_json("restore_revision", payload, expected_fingerprint)
            return

        if path == "/agent/act":
            prompt = str(payload.get("input", "")).strip()
            if not prompt:
                self._write_error(HTTPStatus.BAD_REQUEST, "input is required", operation="agent_act", step="input")
                return
            try:
                tool_name, tool_input = natural_language_to_tool(prompt)
                self._merge_expected_fingerprint(tool_input, expected_fingerprint)
                result = execute_tool(tool_name, tool_input)
            except PlanConflictError as exc:
                self._write_error(
                    HTTPStatus.PRECONDITION_FAILED,
                    str(exc),
                    current_fingerprint=exc.current_fingerprint,
                    operation=tool_name,
                    step="mutation",
                )
                return
            except ValueError as exc:
                self._write_error(HTTPStatus.BAD_REQUEST, str(exc), operation="agent_act", step="dispatch")
                return
            except Exception as exc:
                self._write_error(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    str(exc),
                    kind="internal_error",
                    operation="agent_act",
                    step="dispatch",
                )
                return
            headers = self._etag_headers(result.get("fingerprint"))
            self._write_json(HTTPStatus.OK, {"tool": tool_name, "input": tool_input, "result": result}, extra_headers=headers)
            return

        if path == "/tools/execute":
            tool_name = str(payload.get("tool", "")).strip()
            tool_input = payload.get("input", {})
            if not tool_name:
                self._write_error(HTTPStatus.BAD_REQUEST, "tool is required", operation="tool_execute", step="input")
                return
            if not isinstance(tool_input, dict):
                self._write_error(HTTPStatus.BAD_REQUEST, "tool input must be a JSON object", operation=tool_name, step="input")
                return
            self._merge_expected_fingerprint(tool_input, expected_fingerprint)
            self._execute_tool_request(tool_name, tool_input)
            return

        if path.startswith("/tools/"):
            tool_name = path.split("/", 2)[2].strip()
            tool_input = payload.get("input", payload)
            if not isinstance(tool_input, dict):
                self._write_error(HTTPStatus.BAD_REQUEST, "tool input must be a JSON object", operation=tool_name, step="input")
                return
            self._merge_expected_fingerprint(tool_input, expected_fingerprint)
            self._execute_tool_request(tool_name, tool_input)
            return

        self._write_error(HTTPStatus.NOT_FOUND, "not_found", kind="not_found")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> Optional[Dict[str, Any]]:
        length = self.headers.get("Content-Length", "0")
        try:
            raw_length = int(length)
        except ValueError:
            self._write_error(HTTPStatus.BAD_REQUEST, "invalid_content_length", operation="request_body", step="read")
            return None

        if raw_length <= 0:
            self._write_error(HTTPStatus.BAD_REQUEST, "empty_body", operation="request_body", step="read")
            return None

        body = self.rfile.read(raw_length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._write_error(HTTPStatus.BAD_REQUEST, "invalid_json", operation="request_body", step="decode")
            return None
        if not isinstance(payload, dict):
            self._write_error(HTTPStatus.BAD_REQUEST, "json_body_must_be_object", operation="request_body", step="decode")
            return None
        return payload

    def _expected_fingerprint(self) -> Optional[str]:
        header = self.headers.get("If-Match", "")
        normalized = normalize_fingerprint(header)
        return normalized or None

    def _merge_expected_fingerprint(self, payload: Dict[str, Any], expected_fingerprint: Optional[str]) -> None:
        if expected_fingerprint and "expected_fingerprint" not in payload:
            payload["expected_fingerprint"] = expected_fingerprint

    def _format_etag(self, fingerprint: str) -> str:
        return f'"{fingerprint}"'

    def _etag_headers(self, fingerprint: Optional[str]) -> Dict[str, str]:
        if not fingerprint:
            return {}
        return {"ETag": self._format_etag(str(fingerprint))}

    def _write_error(
        self,
        status: HTTPStatus,
        message: str,
        *,
        kind: str = "error",
        current_fingerprint: Optional[str] = None,
        error_code: str = "",
        operation: str = "",
        step: str = "",
        retryable: Optional[bool] = None,
    ) -> None:
        resolved_error_code = error_code or self._error_code_for(status, kind, message)
        payload: Dict[str, Any] = {
            "error": message,
            "type": kind,
            "error_code": resolved_error_code,
            "retryable": retryable if retryable is not None else self._retryable_for(status, resolved_error_code),
        }
        if operation:
            payload["operation"] = operation
        if step:
            payload["step"] = step
        if current_fingerprint:
            payload["current_fingerprint"] = current_fingerprint
        self._write_json(status, payload, extra_headers=self._etag_headers(current_fingerprint))

    def _execute_tool_json(self, tool_name: str, payload: Dict[str, Any], expected_fingerprint: Optional[str]) -> None:
        self._merge_expected_fingerprint(payload, expected_fingerprint)
        try:
            result = execute_tool(tool_name, payload)
        except PlanConflictError as exc:
            self._write_error(
                HTTPStatus.PRECONDITION_FAILED,
                str(exc),
                current_fingerprint=exc.current_fingerprint,
                operation=tool_name,
                step="mutation",
            )
            return
        except ValueError as exc:
            self._write_error(HTTPStatus.BAD_REQUEST, str(exc), operation=tool_name, step="mutation")
            return
        except Exception as exc:
            self._write_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                str(exc),
                kind="internal_error",
                operation=tool_name,
                step="mutation",
            )
            return
        self._write_json(HTTPStatus.OK, result, extra_headers=self._etag_headers(result.get("fingerprint")))

    def _execute_tool_request(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        try:
            result = execute_tool(tool_name, tool_input)
        except PlanConflictError as exc:
            self._write_error(
                HTTPStatus.PRECONDITION_FAILED,
                str(exc),
                current_fingerprint=exc.current_fingerprint,
                operation=tool_name,
                step="mutation",
            )
            return
        except ValueError as exc:
            self._write_error(HTTPStatus.BAD_REQUEST, str(exc), operation=tool_name, step="mutation")
            return
        except Exception as exc:
            self._write_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                str(exc),
                kind="internal_error",
                operation=tool_name,
                step="mutation",
            )
            return
        headers = self._etag_headers(result.get("fingerprint"))
        self._write_json(HTTPStatus.OK, {"tool": tool_name, "input": tool_input, "result": result}, extra_headers=headers)

    def _tool_catalog_response(self) -> Dict[str, Any]:
        tools = list_tools()
        mutation_tool_count = sum(1 for tool in tools if self._tool_kind(tool) == "mutation")
        read_tool_count = len(tools) - mutation_tool_count
        return {
            "ok": True,
            "result_type": "tool_catalog",
            "contract_version": CONTRACT_VERSION,
            "implementation_version": IMPLEMENTATION_VERSION,
            "catalog": {
                "authoritative": True,
                "transport": "http",
                "list_endpoint": "/tools",
                "detail_endpoint_template": "/tools/{tool_name}",
                "execute_endpoint": "/tools/execute",
                "legacy_execute_endpoint_template": "/tools/{tool_name}",
                "tool_count": len(tools),
                "read_tool_count": read_tool_count,
                "mutation_tool_count": mutation_tool_count,
            },
            "tools": [self._tool_descriptor(tool) for tool in tools],
        }

    def _tool_detail_response(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ok": True,
            "result_type": "tool_detail",
            "contract_version": CONTRACT_VERSION,
            "implementation_version": IMPLEMENTATION_VERSION,
            "tool": self._tool_descriptor(tool),
        }

    def _tool_descriptor(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        descriptor = dict(tool)
        descriptor["kind"] = self._tool_kind(tool)
        descriptor["execute_via"] = {
            "generic": "/tools/execute",
            "legacy_wrapper": f"/tools/{tool['name']}",
        }
        return descriptor

    def _tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        if not tool_name:
            return None
        for tool in list_tools():
            if tool.get("name") == tool_name:
                return tool
        return None

    def _tool_kind(self, tool: Dict[str, Any]) -> str:
        properties = tool.get("input_schema", {}).get("properties", {})
        return "mutation" if "expected_fingerprint" in properties else "read"

    def _error_code_for(self, status: HTTPStatus, kind: str, message: str) -> str:
        if status == HTTPStatus.PRECONDITION_FAILED and message == "plan fingerprint mismatch":
            return "plan_fingerprint_mismatch"
        if status == HTTPStatus.NOT_FOUND:
            return "not_found"
        if status == HTTPStatus.INTERNAL_SERVER_ERROR or kind == "internal_error":
            return "internal_error"
        if message in {"invalid_content_length", "empty_body", "invalid_json", "json_body_must_be_object"}:
            return message
        return "invalid_request"

    def _retryable_for(self, status: HTTPStatus, error_code: str) -> bool:
        if error_code == "plan_fingerprint_mismatch":
            return True
        return status >= HTTPStatus.INTERNAL_SERVER_ERROR

    def _write_json(self, status: HTTPStatus, payload: Dict[str, Any], extra_headers: Optional[Dict[str, str]] = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(encoded)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Palamedes minimal HTTP service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    server = ThreadingHTTPServer((args.host, args.port), PalamedesHandler)
    print(f"Palamedes service listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
