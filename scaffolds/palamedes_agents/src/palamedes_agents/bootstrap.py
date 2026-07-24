#!/usr/bin/env python3
import io
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from palamedes_client import PalamedesClient
from palamedes_server import PalamedesHandler


def _build_handler(method: str, path: str, body: bytes = b"", headers: Optional[Dict[str, str]] = None) -> PalamedesHandler:
    handler = PalamedesHandler.__new__(PalamedesHandler)
    handler.command = method
    handler.path = path
    handler.headers = {"Content-Length": str(len(body)), **(headers or {})}
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    handler._status = None
    handler._sent_headers = {}
    handler.send_response = lambda status, message=None: setattr(handler, "_status", status)
    handler.send_header = lambda key, value: handler._sent_headers.__setitem__(key, value)
    handler.end_headers = lambda: None
    return handler


def in_process_transport(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
    raw_body = json.dumps(body).encode("utf-8") if body is not None else b""
    handler = _build_handler(method, path, body=raw_body, headers=headers)
    if method == "GET":
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()
    else:
        raise ValueError(f"unsupported method: {method}")
    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    return int(handler._status), payload, dict(handler._sent_headers)


@dataclass
class ClientConfig:
    mode: str = "in-process"
    base_url: str = ""
    history_limit: int = 5
    require_healthy_writes: bool = True


def parse_http_base_url(base_url: str) -> Tuple[str, int]:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("base URL must start with http:// or https://")
    if parsed.scheme == "https":
        raise ValueError("PalamedesClient currently supports plain HTTP transport")
    if not parsed.hostname:
        raise ValueError("base URL host is required")
    return parsed.hostname, int(parsed.port or 80)


def build_client(config: ClientConfig) -> PalamedesClient:
    if config.mode == "http":
        host, port = parse_http_base_url(config.base_url)
        return PalamedesClient.from_http(host=host, port=port)
    if config.mode == "in-process":
        import palamedes

        palamedes.ensure_state()
        return PalamedesClient(transport=in_process_transport)
    raise ValueError(f"unknown client mode: {config.mode}")
