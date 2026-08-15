#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import palamedes_inventor_operator as operator
from palamedes_proof import write_object


def intake():
    return {"inventor_intake_version": "palamedes-inventor-intake/1", "case_id": "project-one", "owner_id": "owner-one", "owner_relationship": "independent_external", "palamedes_tuning_exposure": False, "participation_consent": True, "project_repository": "https://github.com/example/project", "unresolved_product_question": "What next?", "required_decision": "Choose a loop.", "owner_prior_hypotheses": ["One"], "approved_public_artifacts": ["README.md"], "excluded_private_information": [], "probe_preregistration": {"decision_to_be_changed": "Choose.", "intervention_window": "1-7 days", "primary_metric": "return", "success_threshold": "one", "failure_threshold": "zero", "measurement_source": "fixed-log"}, "publication": {"project_name_may_be_published": False, "blind_packet_may_be_published": False}, "owner_attestation": "Supplied before candidates."}


class InventorOperatorTests(unittest.TestCase):
    def test_only_explicit_positive_response_advances_to_intake(self):
        ambiguous = operator._classify_external([{"author": "owner", "body": "Can you explain the cost?", "url": "u", "id": "1"}])
        positive = operator._classify_external([{"author": "owner", "body": "Yes, I am interested.", "url": "u", "id": "2"}])
        self.assertEqual(ambiguous["status"], "human_review_required")
        self.assertEqual(positive["status"], "consent_interest")

    def test_valid_fenced_intake_is_admitted(self):
        row = {"author": "owner", "body": "```json\n" + json.dumps(intake()) + "\n```", "url": "u", "id": "1"}
        result = operator._classify_external([row])
        self.assertEqual(result["status"], "intake_complete")

    def test_advance_is_append_only_and_posts_intake_once(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            outreach = root / "outreach.json"
            state = root / "state.json"
            write_object(outreach, {"contacts": [{"candidate_id": "one", "channel": "github_issue", "contact_url": "https://github.com/a/b/issues/1"}]})
            comments = [{"author": "owner", "body": "Yes, interested.", "url": "u", "id": "1"}]
            with patch.object(operator, "_thread_comments", return_value=comments), patch.object(operator, "_post_comment", return_value="followup") as post:
                first = operator.advance(outreach_path=outreach, state_path=state)
                second = operator.advance(outreach_path=outreach, state_path=state)
            self.assertEqual(first["actions"][0]["action"], "intake_requested")
            self.assertEqual(second["actions"], [])
            post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
