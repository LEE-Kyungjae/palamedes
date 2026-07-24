#!/usr/bin/env python3
import argparse
import io
import json
from dataclasses import dataclass
from http.client import HTTPConnection
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Tuple
from urllib.parse import urlparse

from palamedes_server import PalamedesHandler


CONTRACTS_DIR = Path(__file__).resolve().parent / "tests" / "contracts"
MANIFEST_PATH = CONTRACTS_DIR / "manifest.json"


class Transport(Protocol):
    def __call__(self, method: str, path: str, body: Optional[Dict[str, Any]], headers: Optional[Dict[str, str]]) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
        raise NotImplementedError


@dataclass
class ContractAssertionError(AssertionError):
    case_id: str
    message: str

    def __str__(self) -> str:
        return f"{self.case_id}: {self.message}"


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_manifest() -> Dict[str, Any]:
    return load_json(MANIFEST_PATH)


def load_case(case_file: str) -> Dict[str, Any]:
    return load_json(CONTRACTS_DIR / case_file)


def get_value(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(path)
    return current


def resolve_reference(context: Dict[str, Dict[str, Any]], reference: str) -> Any:
    alias, path = reference.split(".", 1)
    return get_value(context[alias], path)


def assert_contains_all(haystack: Iterable[Any], needles: Iterable[Any]) -> None:
    values = list(haystack)
    for needle in needles:
        if needle not in values:
            raise AssertionError(f"missing expected value: {needle!r}")


def assert_contract_assertion(case_id: str, assertion: Dict[str, Any], context: Dict[str, Dict[str, Any]]) -> None:
    target = context[assertion["target"]]
    path = assertion["path"]
    op = assertion["op"]

    try:
        if op == "eq":
            expected = resolve_reference(context, assertion["value_from"]) if "value_from" in assertion else assertion["value"]
            if get_value(target, path) != expected:
                raise ContractAssertionError(case_id, f"{path} != {expected!r}")
            return
        if op == "ne":
            expected = resolve_reference(context, assertion["value_from"]) if "value_from" in assertion else assertion["value"]
            if get_value(target, path) == expected:
                raise ContractAssertionError(case_id, f"{path} unexpectedly equals {expected!r}")
            return
        if op == "gt":
            if not get_value(target, path) > assertion["value"]:
                raise ContractAssertionError(case_id, f"{path} <= {assertion['value']!r}")
            return
        if op == "len_eq":
            if len(get_value(target, path)) != assertion["value"]:
                raise ContractAssertionError(case_id, f"{path} length mismatch")
            return
        if op == "non_empty":
            if not get_value(target, path):
                raise ContractAssertionError(case_id, f"{path} is empty")
            return
        if op == "has_keys":
            value = get_value(target, path)
            if not isinstance(value, dict):
                raise ContractAssertionError(case_id, f"{path} is not an object")
            missing = [key for key in assertion["value"] if key not in value]
            if missing:
                raise ContractAssertionError(case_id, f"{path} missing keys {missing!r}")
            return
        if op == "contains":
            value = get_value(target, path)
            if not isinstance(value, list):
                raise ContractAssertionError(case_id, f"{path} is not a list")
            assert_contains_all(value, assertion["value"])
            return
        if op == "etag_matches_payload_fingerprint":
            etag = str(get_value(target, path))
            fingerprint = str(get_value(target, assertion["fingerprint_path"]))
            if etag != f'"{fingerprint}"':
                raise ContractAssertionError(case_id, f"{path} does not match {assertion['fingerprint_path']}")
            return
        if op == "quoted_equals_value_from":
            value_from = resolve_reference(context, assertion["value_from"])
            if str(get_value(target, path)) != f'"{value_from}"':
                raise ContractAssertionError(case_id, f"{path} does not equal quoted reference")
            return
    except KeyError as exc:
        raise ContractAssertionError(case_id, f"missing path {exc}") from exc

    raise ContractAssertionError(case_id, f"unsupported assertion op {op!r}")


def build_inprocess_transport() -> Transport:
    def transport(method: str, path: str, body: Optional[Dict[str, Any]], headers: Optional[Dict[str, str]]) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
        raw_body = json.dumps(body).encode("utf-8") if body is not None else b""
        handler = PalamedesHandler.__new__(PalamedesHandler)
        handler.command = method
        handler.path = path
        handler.headers = {"Content-Length": str(len(raw_body)), **(headers or {})}
        handler.rfile = io.BytesIO(raw_body)
        handler.wfile = io.BytesIO()
        handler._status = None
        handler._sent_headers = {}
        handler.send_response = lambda status, message=None: setattr(handler, "_status", status)
        handler.send_header = lambda key, value: handler._sent_headers.__setitem__(key, value)
        handler.end_headers = lambda: None
        if method == "GET":
            handler.do_GET()
        else:
            handler.do_POST()
        payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
        return handler._status, payload, handler._sent_headers

    return transport


def build_http_transport(base_url: str) -> Transport:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("base_url must use http or https")
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if parsed.scheme == "https":
        raise ValueError("https transport is not supported by the built-in runner")
    prefix = parsed.path.rstrip("/")

    def transport(method: str, path: str, body: Optional[Dict[str, Any]], headers: Optional[Dict[str, str]]) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
        connection = HTTPConnection(host, port, timeout=10.0)
        merged_headers = dict(headers or {})
        raw_body = None
        if body is not None:
            raw_body = json.dumps(body).encode("utf-8")
            merged_headers.setdefault("Content-Type", "application/json")
        connection.request(method, f"{prefix}{path}", body=raw_body, headers=merged_headers)
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        response_headers = dict(response.getheaders())
        connection.close()
        return response.status, payload, response_headers

    return transport


def run_request(transport: Transport, method: str, path: str, body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    status, payload, response_headers = transport(method, path, body, headers)
    return {
        "status": status,
        "payload": payload,
        "headers": response_headers,
    }


def run_case(transport: Transport, case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case["id"]
    context: Dict[str, Dict[str, Any]] = {}
    step_results: List[Dict[str, Any]] = []

    def record(name: str, capture: str, method: str, path: str, body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        result = run_request(transport, method, path, body=body, headers=headers)
        context[capture] = result
        step_results.append({"name": name, "capture": capture, "status": result["status"]})
        return result

    if case_id == "plan-envelope":
        record("read_plan", "plan", "GET", "/plan")
    elif case_id == "etag-fingerprint":
        before = record("read_plan", "before", "GET", "/plan")
        record(
            "write_plan",
            "after",
            "POST",
            "/plan",
            body=case["write_body"],
            headers={"Content-Type": "application/json", "If-Match": before["headers"]["ETag"]},
        )
    elif case_id == "stale-write-conflict":
        baseline = record("read_baseline", "baseline", "GET", "/plan")
        record(
            "fresh_write",
            "fresh",
            "POST",
            "/plan",
            body=case["fresh_write_body"],
            headers={"Content-Type": "application/json", "If-Match": baseline["headers"]["ETag"]},
        )
        record(
            "stale_write",
            "stale",
            "POST",
            "/plan",
            body=case["stale_write_body"],
            headers={"Content-Type": "application/json", "If-Match": baseline["headers"]["ETag"]},
        )
    elif case_id == "restore-roundtrip":
        record("seed_first", "seed_first", "POST", "/plan", body=case["seed_plan_first"], headers={"Content-Type": "application/json"})
        first = record("seed_second", "seed_second", "POST", "/plan", body=case["seed_plan_second"], headers={"Content-Type": "application/json"})
        current = record("read_plan", "current", "GET", "/plan")
        record("preview_restore", "preview", "POST", "/restore/preview", body={"previous": True}, headers={"Content-Type": "application/json"})
        record(
            "restore_previous",
            "restored",
            "POST",
            "/restore",
            body={"previous": True},
            headers={"Content-Type": "application/json", "If-Match": current["payload"]["fingerprint"]},
        )
    elif case_id == "idempotent-evidence-dedupe":
        record("first_evidence", "first", "POST", "/evidence", body=case["first_evidence_body"], headers={"Content-Type": "application/json"})
        record("second_evidence", "second", "POST", "/evidence", body=case["first_evidence_body"], headers={"Content-Type": "application/json"})
    else:
        raise ValueError(f"unsupported contract case: {case_id}")

    for assertion in case.get("assertions", []):
        assert_contract_assertion(case["id"], assertion, context)

    return {
        "id": case["id"],
        "description": case.get("description", ""),
        "ok": True,
        "steps": step_results,
    }


def run_manifest(transport: Transport, *, reset_state: Optional[Callable[[], None]] = None) -> Dict[str, Any]:
    manifest = load_manifest()
    cases = manifest.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("contracts manifest cases must be an array")

    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for entry in cases:
        case_file = str(entry["file"])
        case = load_case(case_file)
        try:
            if reset_state:
                reset_state()
            results.append(run_case(transport, case))
        except Exception as exc:
            failures.append(
                {
                    "id": case.get("id", case_file),
                    "description": case.get("description", ""),
                    "ok": False,
                    "error": str(exc),
                }
            )

    ok = not failures
    return {
        "ok": ok,
        "manifest_version": manifest.get("version", ""),
        "case_count": len(cases),
        "passed": len(results),
        "failed": len(failures),
        "results": results,
        "failures": failures,
    }


def build_transport(base_url: Optional[str] = None, in_process: bool = False) -> Transport:
    if base_url:
        return build_http_transport(base_url)
    if in_process or not base_url:
        return build_inprocess_transport()
    raise ValueError("either base_url or in_process must be selected")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Palamedes conformance runner")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--in-process", action="store_true")
    parser.add_argument("--json", action="store_true", default=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    transport = build_transport(base_url=args.base_url or None, in_process=bool(args.in_process or not args.base_url))
    report = run_manifest(transport)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
