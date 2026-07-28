#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import palamedes
from palamedes_workspace import WorkspaceRegistry


class WorkspaceRegistryTests(unittest.TestCase):
    def test_register_resolve_and_remove_preserve_project_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project-a"
            state = project / ".palamedes"
            state.mkdir(parents=True)
            plan = state / "plan.json"
            plan.write_text('{"goal":"preserve me"}\n', encoding="utf-8")
            registry = WorkspaceRegistry(root / "global-home")

            record = registry.register("alpha", project)
            self.assertEqual(record["path"], str(project.resolve()))
            self.assertEqual(registry.resolve("alpha"), project.resolve())
            self.assertEqual(registry.resolve(str(project)), project.resolve())
            metadata = json.loads((state / "workspace.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["workspace_id"], record["workspace_id"])

            registry.remove("alpha")
            self.assertEqual(plan.read_text(encoding="utf-8"), '{"goal":"preserve me"}\n')
            self.assertTrue((state / "workspace.json").is_file())

    def test_duplicate_name_or_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "one", root / "two"
            first.mkdir()
            second.mkdir()
            registry = WorkspaceRegistry(root / "home")
            registry.register("one", first)
            with self.assertRaisesRegex(ValueError, "points elsewhere"):
                registry.register("one", second)
            with self.assertRaisesRegex(ValueError, "already registered"):
                registry.register("alias", first)

    def test_global_workspace_selector_parses_before_command(self):
        args = palamedes.build_parser().parse_args(["-w", "alpha", "show"])
        self.assertEqual(args.workspace_selector, "alpha")
        self.assertEqual(args.command, "show")


if __name__ == "__main__":
    unittest.main()
