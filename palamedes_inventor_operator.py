#!/usr/bin/env python3
"""Advance the external Inventor proof as far as explicit consent permits."""

from __future__ import annotations

import argparse
import json
import re
import secrets
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from palamedes_inventor_proof import prepare_inventor_run, validate_inventor_portfolio
from palamedes_observe import utc_now
from palamedes_proof import generate_condition, load_object, prepare_blind_packet, write_object


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTREACH = ROOT / "experiments" / "inventor-proof-outreach.json"
DEFAULT_STATE = ROOT / "experiments" / "inventor-proof-operator-state.json"
DEFAULT_RUN_ROOT = ROOT / "experiments" / "inventor-proof-runs"
OWN_LOGIN = "LEE-Kyungjae"
POSITIVE = re.compile(r"\b(yes|interested|open to|happy to|sounds useful|would like to|count me in)\b", re.I)
NEGATIVE = re.compile(r"\b(no|not interested|decline|do not|please close|cannot participate)\b", re.I)
JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.I | re.S)


INTAKE_REQUEST = """Thanks for considering the pilot. To prevent the experiment from seeding its own answer, please reply with one fenced `json` object using this shape. Replace every placeholder; do not include secrets or private customer data.

```json
{
  "inventor_intake_version": "palamedes-inventor-intake/1",
  "case_id": "short-project-id",
  "owner_id": "non-secret-owner-id",
  "owner_relationship": "independent_external",
  "palamedes_tuning_exposure": false,
  "participation_consent": true,
  "project_repository": "https://github.com/owner/repository",
  "unresolved_product_question": "One real question not yet decided",
  "required_decision": "The continue, stop, pivot, position, or sequence choice",
  "owner_prior_hypotheses": ["Ideas recorded before seeing either output"],
  "approved_public_artifacts": ["README.md"],
  "excluded_private_information": ["credentials and private user data"],
  "probe_preregistration": {
    "decision_to_be_changed": "Exact decision",
    "intervention_window": "1-7 days",
    "primary_metric": "One observable metric",
    "success_threshold": "Fixed threshold",
    "failure_threshold": "Fixed stop threshold",
    "measurement_source": "Immutable log, survey, analytics export, or external dataset"
  },
  "publication": {
    "project_name_may_be_published": false,
    "owner_id_may_be_published": false,
    "raw_artifacts_may_be_published": false,
    "blind_packet_may_be_published": false,
    "aggregate_result_may_be_published": true,
    "additional_restrictions": []
  },
  "owner_attestation": "I supplied this unresolved question before seeing generated candidates."
}
```

Submitting this object records consent to prepare the blinded comparison only. It grants no code, deployment, credential, or publication authority beyond the explicit publication fields."""


def _gh(args: List[str], *, input_text: str = "") -> Any:
    result = subprocess.run(
        ["gh", *args], input=input_text, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    text = result.stdout.strip()
    return json.loads(text) if text.startswith(("{", "[")) else text


def _thread_comments(contact: Dict[str, Any]) -> List[Dict[str, Any]]:
    if contact["channel"] == "github_issue":
        match = re.fullmatch(r"https://github.com/([^/]+)/([^/]+)/issues/(\d+)", contact["contact_url"])
        if not match:
            raise ValueError("invalid GitHub issue URL")
        owner, repo, number = match.groups()
        rows = _gh(["api", f"repos/{owner}/{repo}/issues/{number}/comments", "--paginate"])
        return [{"id": str(row["id"]), "author": row["user"]["login"], "body": row["body"], "url": row["html_url"]} for row in rows]
    match = re.fullmatch(r"https://github.com/([^/]+)/([^/]+)/discussions/(\d+)#discussioncomment-\d+", contact["contact_url"])
    if not match:
        raise ValueError("invalid GitHub discussion URL")
    owner, repo, number = match.groups()
    query = "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){discussion(number:$number){comments(first:100){nodes{id url body author{login} replies(first:100){nodes{id url body author{login}}}}}}}}"
    data = _gh(["api", "graphql", "-f", f"query={query}", "-F", f"owner={owner}", "-F", f"name={repo}", "-F", f"number={number}"])
    rows = []
    for node in data["data"]["repository"]["discussion"]["comments"]["nodes"]:
        rows.append({"id": node["id"], "author": node["author"]["login"], "body": node["body"], "url": node["url"]})
        for reply in node["replies"]["nodes"]:
            rows.append({"id": reply["id"], "author": reply["author"]["login"], "body": reply["body"], "url": reply["url"]})
    return rows


def _post_comment(contact: Dict[str, Any], body: str) -> str:
    if contact["channel"] == "github_issue":
        match = re.fullmatch(r"https://github.com/([^/]+)/([^/]+)/issues/(\d+)", contact["contact_url"])
        owner, repo, number = match.groups()
        row = _gh(["api", f"repos/{owner}/{repo}/issues/{number}/comments", "-f", f"body={body}"])
        return row["html_url"]
    match = re.fullmatch(r"https://github.com/([^/]+)/([^/]+)/discussions/(\d+)#discussioncomment-\d+", contact["contact_url"])
    owner, repo, number = match.groups()
    query = "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){discussion(number:$number){id}}}"
    data = _gh(["api", "graphql", "-f", f"query={query}", "-F", f"owner={owner}", "-F", f"name={repo}", "-F", f"number={number}"])
    discussion_id = data["data"]["repository"]["discussion"]["id"]
    mutation = "mutation($discussionId:ID!,$body:String!){addDiscussionComment(input:{discussionId:$discussionId,body:$body}){comment{url}}}"
    data = _gh(["api", "graphql", "-f", f"query={mutation}", "-F", f"discussionId={discussion_id}", "-f", f"body={body}"])
    return data["data"]["addDiscussionComment"]["comment"]["url"]


def validate_intake(payload: Dict[str, Any]) -> List[str]:
    errors = []
    required = ("case_id", "owner_id", "project_repository", "unresolved_product_question", "required_decision", "owner_attestation")
    if payload.get("inventor_intake_version") != "palamedes-inventor-intake/1":
        errors.append("invalid inventor_intake_version")
    for field in required:
        if not str(payload.get(field, "")).strip():
            errors.append(f"{field} is required")
    if payload.get("owner_relationship") != "independent_external":
        errors.append("owner_relationship must be independent_external")
    if payload.get("palamedes_tuning_exposure") is not False:
        errors.append("palamedes_tuning_exposure must be false")
    if payload.get("participation_consent") is not True:
        errors.append("participation_consent must be true")
    if not isinstance(payload.get("approved_public_artifacts"), list) or not payload["approved_public_artifacts"]:
        errors.append("approved_public_artifacts must be non-empty")
    probe = payload.get("probe_preregistration")
    for field in ("decision_to_be_changed", "intervention_window", "primary_metric", "success_threshold", "failure_threshold", "measurement_source"):
        if not isinstance(probe, dict) or not str(probe.get(field, "")).strip():
            errors.append(f"probe_preregistration.{field} is required")
    if not isinstance(payload.get("publication"), dict):
        errors.append("publication must be an object")
    elif not isinstance(payload["publication"].get("blind_packet_may_be_published"), bool):
        errors.append("publication.blind_packet_may_be_published must be boolean")
    return errors


def _classify_external(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    external = [row for row in comments if row["author"] != OWN_LOGIN]
    for row in reversed(external):
        blocks = JSON_BLOCK.findall(row["body"])
        if blocks:
            try:
                intake = json.loads(blocks[-1])
            except json.JSONDecodeError as exc:
                return {"status": "invalid_intake_json", "comment": row, "error": str(exc)}
            errors = validate_intake(intake)
            return {"status": "intake_complete" if not errors else "intake_invalid", "comment": row, "intake": intake, "errors": errors}
        if NEGATIVE.search(row["body"]):
            return {"status": "declined", "comment": row}
        if POSITIVE.search(row["body"]):
            return {"status": "consent_interest", "comment": row}
        return {"status": "human_review_required", "comment": row}
    return {"status": "awaiting_response"}


def _initial_state() -> Dict[str, Any]:
    return {"inventor_operator_state_version": "palamedes-inventor-operator/1", "updated_at": utc_now(), "contacts": {}, "admitted_cases": {}, "run_id": "", "stage": "outreach"}


def advance(*, outreach_path: Path = DEFAULT_OUTREACH, state_path: Path = DEFAULT_STATE, allow_external_writes: bool = True) -> Dict[str, Any]:
    outreach = load_object(outreach_path)
    state = load_object(state_path) if state_path.exists() else _initial_state()
    actions = []
    for contact in outreach["contacts"]:
        candidate_id = contact["candidate_id"]
        classification = _classify_external(_thread_comments(contact))
        row = state["contacts"].setdefault(candidate_id, {})
        row["status"] = classification["status"]
        if classification.get("comment"):
            row["latest_external_comment_url"] = classification["comment"]["url"]
        if classification["status"] == "consent_interest" and not row.get("intake_requested"):
            if allow_external_writes:
                row["intake_request_url"] = _post_comment(contact, INTAKE_REQUEST)
                row["intake_requested"] = True
                actions.append({"candidate_id": candidate_id, "action": "intake_requested", "url": row["intake_request_url"]})
        if classification["status"] == "intake_complete":
            intake = classification["intake"]
            intake_path = outreach_path.parent / "inventor-intakes" / f"{intake['case_id']}.json"
            if not intake_path.exists():
                write_object(intake_path, intake)
            state["admitted_cases"][intake["case_id"]] = {"candidate_id": candidate_id, "intake_path": str(intake_path), "source_comment_url": classification["comment"]["url"]}
    if len(state["admitted_cases"]) == 3 and not state.get("run_id"):
        template = load_object(outreach_path.parent / "inventor-proof-portfolio.example.json")
        cases = []
        for admitted in state["admitted_cases"].values():
            intake = load_object(Path(admitted["intake_path"]))
            repo_slug = intake["project_repository"].removeprefix("https://github.com/").removesuffix(".git")
            local_repo = outreach_path.parent / "inventor-candidates" / intake["case_id"]
            if not local_repo.exists():
                _gh(["repo", "clone", repo_slug, str(local_repo), "--", "--depth=1"])
            cases.append({"case_id": intake["case_id"], "owner_id": intake["owner_id"], "owner_relationship": "independent_external", "palamedes_tuning_exposure": False, "repository": str(local_repo), "question": intake["unresolved_product_question"], "required_decision": intake["required_decision"], "artifacts": intake["approved_public_artifacts"], "probe_preregistration": intake["probe_preregistration"]})
        template["portfolio_id"] = "external-inventor-proof-001"
        template["cases"] = cases
        errors = validate_inventor_portfolio(template)
        if errors:
            raise ValueError("assembled portfolio invalid: " + "; ".join(errors))
        portfolio_path = outreach_path.parent / "inventor-proof-portfolio-001.json"
        write_object(portfolio_path, template)
        result = prepare_inventor_run(template, run_root=DEFAULT_RUN_ROOT, run_id="inventor-proof-001")
        state["run_id"] = result["run_id"]
        state["run_path"] = result["run_path"]
        state["stage"] = "prepared"
        actions.append({"action": "run_prepared", "run_id": result["run_id"]})
    if state.get("stage") == "prepared":
        run_path = Path(state["run_path"])
        generate_condition(run_path, condition="tournament")
        generate_condition(run_path, condition="palamedes")
        seed = secrets.token_hex(32)
        prepare_blind_packet(run_path, seed=seed, comparison_condition="tournament", treatment_condition="palamedes")
        write_object(run_path / "private" / "blind-seed-custody.json", {"blind_seed_custody_version": "palamedes-inventor-blind-seed/1", "created_at": utc_now(), "seed": seed, "must_remain_private_until_reviews_complete": True})
        state["stage"] = "blind_packet_ready"
        actions.append({"action": "conditions_generated_and_blinded", "run_path": str(run_path)})
    if state.get("stage") == "blind_packet_ready" and allow_external_writes:
        run_path = Path(state["run_path"])
        packet_path = run_path / "blind" / "packet.json"
        intakes = [load_object(Path(row["intake_path"])) for row in state["admitted_cases"].values()]
        public_packet_allowed = all(
            row.get("publication", {}).get("blind_packet_may_be_published") is True
            for row in intakes
        )
        gist_url = ""
        if public_packet_allowed:
            gist_url = _gh([
                "gist", "create", "--public", str(packet_path),
                "--desc", f"Origin-blinded Palamedes Inventor review packet for {state['run_id']}",
            ])
        packet_access = (
            f"Blind packet: {gist_url}"
            if gist_url
            else "The blind packet is not public under owner custody. Eligible volunteers will receive access only through an owner-approved channel."
        )
        body = f"""We are seeking independent human reviewers for an origin-blinded external-project comparison.

{packet_access}

Please review A and B without guessing authorship. Score each from 1 to 5 on every rubric axis, choose A, B, or tie, explain whether the difference would change a real product decision, and report confidence from 0 to 100.

Eligibility:
- human reviewer;
- not an owner or contributor of any included case;
- no access to the answer key or other reviews before submission;
- no involvement in Palamedes tuning.

Reply here only to volunteer. The operator will provide the machine-readable response form separately so answers can be collected without exposing prior reviews. The answer key remains private until the review gate closes. This is an evaluation request, not a request for stars, endorsement, code, or a favorable result."""
        issue_url = _gh([
            "issue", "create", "-R", "LEE-Kyungjae/Palamedes",
            "--title", f"Independent reviewers wanted: {state['run_id']} Inventor pilot",
            "--body", body,
        ])
        state["review_packet_gist_url"] = gist_url
        state["public_blind_packet_allowed"] = public_packet_allowed
        state["reviewer_recruitment_url"] = issue_url
        state["stage"] = "reviewer_recruitment_open"
        actions.append({"action": "independent_reviewer_recruitment_opened", "gist_url": gist_url, "issue_url": issue_url})
    state["updated_at"] = utc_now()
    write_object(state_path, state)
    return {"stage": state["stage"], "actions": actions, "contacts": state["contacts"], "admitted_case_count": len(state["admitted_cases"]), "run_id": state.get("run_id", "")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outreach", default=str(DEFAULT_OUTREACH))
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--read-only", action="store_true")
    args = parser.parse_args()
    result = advance(outreach_path=Path(args.outreach), state_path=Path(args.state), allow_external_writes=not args.read_only)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
