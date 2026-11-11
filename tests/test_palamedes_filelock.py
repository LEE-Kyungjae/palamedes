import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path

from palamedes_filelock import exclusive_lock


def _append_rows(path: str, worker: int, count: int) -> None:
    for index in range(count):
        with open(path, "a+", encoding="utf-8") as handle, exclusive_lock(handle):
            handle.seek(0)
            seen = sum(1 for _ in handle)
            handle.write(json.dumps({"worker": worker, "index": index, "seen": seen}) + "\n")


class ExclusiveLockTest(unittest.TestCase):
    def test_lock_allows_read_and_append_on_same_handle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_text('{"event_id": "a"}\n', encoding="utf-8")
            with path.open("a+", encoding="utf-8") as handle, exclusive_lock(handle):
                handle.seek(0)
                self.assertEqual([json.loads(line) for line in handle], [{"event_id": "a"}])
                handle.write('{"event_id": "b"}\n')
            self.assertEqual(
                path.read_text(encoding="utf-8").splitlines(),
                ['{"event_id": "a"}', '{"event_id": "b"}'],
            )

    def test_unlocked_reader_can_read_while_lock_is_held(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_text("existing\n", encoding="utf-8")
            with path.open("a+", encoding="utf-8") as handle, exclusive_lock(handle):
                self.assertEqual(path.read_text(encoding="utf-8"), "existing\n")

    def test_lock_is_released_after_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            with self.assertRaises(RuntimeError):
                with path.open("a+", encoding="utf-8") as handle, exclusive_lock(handle):
                    raise RuntimeError("boom")
            with path.open("a+", encoding="utf-8") as handle, exclusive_lock(handle):
                handle.write("after\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "after\n")

    def test_concurrent_processes_serialize_appends(self) -> None:
        workers, count = 4, 25
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.touch()
            context = multiprocessing.get_context("spawn")
            processes = [
                context.Process(target=_append_rows, args=(str(path), worker, count))
                for worker in range(workers)
            ]
            for process in processes:
                process.start()
            for process in processes:
                process.join(60)
                self.assertEqual(process.exitcode, 0)
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), workers * count)
            # Each writer counted the rows already present while holding the
            # lock, so the counts form an unbroken 0..N-1 sequence.
            self.assertEqual(sorted(row["seen"] for row in rows), list(range(workers * count)))


if __name__ == "__main__":
    unittest.main()
