#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from deepplan_agents.reference_collectors import collect_file, collect_url
from deepplan_agents.reference_store import ReferenceStore


class ReferenceStoreTests(unittest.TestCase):
    def test_store_persists_updates_and_deduplicates_content(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ReferenceStore(Path(directory) / "references.sqlite3")
            original = {
                "reference_id": "case-1",
                "source": "Case",
                "source_type": "success_case",
                "problem": "Generic ideas",
                "mechanism": "Decision gate",
            }
            self.assertEqual(store.upsert(original)["status"], "created")
            self.assertEqual(store.upsert(original)["status"], "unchanged")
            duplicate = dict(original, reference_id="case-copy")
            result = store.upsert(duplicate)
            self.assertEqual(result["status"], "duplicate")
            self.assertEqual(result["reference_id"], "case-1")
            changed = dict(original, mechanism="Evidence-backed decision gate")
            self.assertEqual(store.upsert(changed)["status"], "updated")
            self.assertEqual(store.count(), 1)
            self.assertEqual(store.get("case-1")["mechanism"], "Evidence-backed decision gate")
            health = store.health()
            self.assertEqual(health["status"], "ok")
            self.assertEqual(health["reference_count"], 1)

    def test_store_filters_by_source_type(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ReferenceStore(Path(directory) / "references.sqlite3")
            store.ingest(
                [
                    {"reference_id": "success", "source": "S", "source_type": "success_case"},
                    {"reference_id": "failure", "source": "F", "source_type": "failure_case"},
                ]
            )
            self.assertEqual([item["reference_id"] for item in store.list(source_type="failure_case")], ["failure"])

    def test_collect_json_jsonl_and_text_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            json_path = root / "references.json"
            json_path.write_text(json.dumps([{"reference_id": "json-1", "source": "JSON"}]), encoding="utf-8")
            jsonl_path = root / "references.jsonl"
            jsonl_path.write_text(json.dumps({"reference_id": "jsonl-1", "source": "JSONL"}) + "\n", encoding="utf-8")
            text_path = root / "notes.txt"
            text_path.write_text("Users abandon generic dashboards after the first report.", encoding="utf-8")

            self.assertEqual(collect_file(json_path)[0]["reference_id"], "json-1")
            self.assertEqual(collect_file(jsonl_path)[0]["reference_id"], "jsonl-1")
            text_pattern = collect_file(text_path, source_type="review")[0]
            self.assertEqual(text_pattern["source_type"], "review")
            self.assertIn("generic dashboards", text_pattern["content"])

    def test_collect_url_extracts_readable_html_and_provenance(self):
        class Headers:
            @staticmethod
            def get_content_type():
                return "text/html"

            @staticmethod
            def get_content_charset():
                return "utf-8"

        class Response:
            headers = Headers()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            @staticmethod
            def read(_: int):
                return b"<html><head><title>Founder Postmortem</title><script>ignore()</script></head><body>Users did not return after the first report.</body></html>"

        with patch("deepplan_agents.reference_collectors.urlopen", return_value=Response()):
            pattern = collect_url("https://example.com/postmortem", source_type="failure_case")

        self.assertEqual(pattern["source"], "Founder Postmortem")
        self.assertEqual(pattern["source_url"], "https://example.com/postmortem")
        self.assertNotIn("ignore", pattern["content"])
        self.assertIn("Users did not return", pattern["content"])


if __name__ == "__main__":
    unittest.main()
