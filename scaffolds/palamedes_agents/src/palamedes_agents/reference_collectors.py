#!/usr/bin/env python3
"""Reference corpus collectors for JSON, JSONL, text, and HTTP(S) sources."""

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import Request, urlopen

from palamedes_agents.reference_rag import normalize_reference_pattern


class _ReadableHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self.title_parts: List[str] = []
        self._ignored = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored:
            self._ignored -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text or self._ignored:
            return
        self.parts.append(text)
        if self._in_title:
            self.title_parts.append(text)


def _stable_id(value: str) -> str:
    return "ref_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def collect_file(path: Path, *, source_type: str = "other") -> List[Dict[str, Any]]:
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(raw)
        items = payload if isinstance(payload, list) else [payload]
        if not all(isinstance(item, dict) for item in items):
            raise ValueError("JSON reference input must be an object or array of objects")
        return [normalize_reference_pattern(item, index) for index, item in enumerate(items)]
    if suffix == ".jsonl":
        items = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if not all(isinstance(item, dict) for item in items):
            raise ValueError("JSONL reference input must contain one object per line")
        return [normalize_reference_pattern(item, index) for index, item in enumerate(items)]
    clean = " ".join(raw.split())
    if not clean:
        raise ValueError("reference text file is empty")
    return [
        normalize_reference_pattern(
            {
                "reference_id": _stable_id(str(path.resolve())),
                "source": path.name,
                "source_type": source_type,
                "context": f"Collected from local file {path.name}",
                "content": clean,
                "confidence": 50,
            }
        )
    ]


def collect_url(url: str, *, source_type: str = "other", timeout: int = 20, max_chars: int = 50000) -> Dict[str, Any]:
    if not isinstance(url, str) or not re.match(r"^https?://", url.strip(), re.IGNORECASE):
        raise ValueError("reference URL must use http or https")
    request = Request(url.strip(), headers={"User-Agent": "Palamedes-Reference-Collector/1.0"})
    with urlopen(request, timeout=timeout) as response:
        media_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset() or "utf-8"
        raw = response.read(max_chars * 4).decode(charset, errors="replace")
    title = url.strip()
    if media_type == "text/html":
        parser = _ReadableHTML()
        parser.feed(raw)
        content = " ".join(parser.parts)
        if parser.title_parts:
            title = " ".join(parser.title_parts)
    else:
        content = " ".join(raw.split())
    content = content[:max_chars].strip()
    if not content:
        raise ValueError("reference URL returned no readable content")
    return normalize_reference_pattern(
        {
            "reference_id": _stable_id(url.strip()),
            "source": title,
            "source_url": url.strip(),
            "source_type": source_type,
            "context": f"Collected from {url.strip()}",
            "content": content,
            "confidence": 50,
        }
    )
