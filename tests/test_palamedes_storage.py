#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from palamedes_storage import ContentAddressedStore, inventory_storage


class PalamedesStorageTests(unittest.TestCase):
    def test_content_addressed_put_is_deduplicated_and_verified(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state = Path(tempdir) / ".palamedes"
            store = ContentAddressedStore(state)
            first = store.put_bytes(
                b"same evidence", media_type="text/plain", source_ids=["a"]
            )
            second = store.put_bytes(
                b"same evidence", media_type="text/plain", source_ids=["b"]
            )
            verification = store.verify(first)
            blob_count = len(
                [path for path in (state / "blobs").rglob("*") if path.is_file()]
            )
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertTrue(verification["valid"])
        self.assertEqual(blob_count, 1)

    def test_inventory_reports_duplicates_without_mutation(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state = Path(tempdir) / ".palamedes"
            (state / "chat").mkdir(parents=True)
            (state / "chat" / "a.jsonl").write_text("duplicate")
            (state / "chat" / "b.jsonl").write_text("duplicate")
            before = sorted(path.read_bytes() for path in (state / "chat").iterdir())
            inventory = inventory_storage(state)
            after = sorted(path.read_bytes() for path in (state / "chat").iterdir())
        self.assertTrue(inventory["read_only"])
        self.assertFalse(inventory["mutation_performed"])
        self.assertEqual(inventory["summary"]["duplicate_groups"], 1)
        self.assertEqual(
            inventory["summary"]["duplicate_reclaimable_bytes"], len(b"duplicate")
        )
        self.assertEqual(before, after)

    def test_immutable_ledger_has_non_destructive_retention_policy(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state = Path(tempdir) / ".palamedes"
            path = state / "missions" / "outcomes.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text("{}\n")
            inventory = inventory_storage(state)
        self.assertEqual(inventory["classification_counts"]["immutable_ledger"], 1)
        self.assertIn("never delete", inventory["retention"]["immutable_ledger"])


if __name__ == "__main__":
    unittest.main()
