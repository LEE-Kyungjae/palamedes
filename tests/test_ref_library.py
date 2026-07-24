import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ref_library.py"
SPEC = importlib.util.spec_from_file_location("ref_library", MODULE_PATH)
assert SPEC and SPEC.loader
ref_library = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ref_library
SPEC.loader.exec_module(ref_library)


class RefLibraryTests(unittest.TestCase):
    def test_normalize_remote_unifies_common_github_forms(self):
        expected = "https://github.com/openclaw/openclaw"
        self.assertEqual(ref_library.normalize_remote("https://github.com/OpenClaw/OpenClaw.git"), expected)
        self.assertEqual(ref_library.normalize_remote("git@github.com:openclaw/openclaw.git"), expected)

    def test_duplicate_groups_uses_normalized_remote(self):
        first = ref_library.RepoState(
            "/a",
            "https://github.com/org/repo.git",
            "https://github.com/org/repo",
            "main",
            "a",
            "origin/main",
            0,
            0,
            0,
        )
        second = ref_library.RepoState(
            "/b",
            "git@github.com:org/repo.git",
            "https://github.com/org/repo",
            "main",
            "b",
            "origin/main",
            0,
            0,
            0,
        )
        groups = ref_library.duplicate_groups([first, second])
        self.assertEqual([item.path for item in groups["https://github.com/org/repo"]], ["/a", "/b"])

    def test_discover_and_inspect_repository(self):
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir) / "sample"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "README.md").write_text("agent loop with permission and eval", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "initial"], check=True)

            self.assertEqual(ref_library.discover_git_repos(Path(tempdir)), [repo])
            state = ref_library.inspect_repo(repo)
            self.assertEqual(state.branch, "main")
            self.assertEqual(state.dirty, 0)
            catalog = ref_library.catalog_repo(state)
            self.assertIn("agent_loop", catalog["patterns"])
            self.assertIn("permissions", catalog["patterns"])
            self.assertIn("evaluation", catalog["patterns"])


if __name__ == "__main__":
    unittest.main()
