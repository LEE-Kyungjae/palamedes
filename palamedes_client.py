#!/usr/bin/env python3
import json
from dataclasses import dataclass
from http.client import HTTPConnection
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote
from uuid import uuid4


class PalamedesClientError(RuntimeError):
    def __init__(self, status: int, payload: Dict[str, Any], headers: Dict[str, str]) -> None:
        message = str(payload.get("error", f"http_{status}"))
        super().__init__(message)
        self.status = status
        self.payload = payload
        self.headers = headers
        self.error_code = str(payload.get("error_code", "")).strip()
        self.retryable = bool(payload.get("retryable", False))
        self.operation = str(payload.get("operation", "")).strip()
        self.step = str(payload.get("step", "")).strip()


class PalamedesConflictError(PalamedesClientError):
    def __init__(
        self,
        status: int,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        *,
        expected_fingerprint: str = "",
        current_fingerprint: str = "",
        operation: str = "",
        step: str = "",
        can_refresh: bool = True,
    ) -> None:
        super().__init__(status, payload, headers)
        self.expected_fingerprint = expected_fingerprint
        self.current_fingerprint = current_fingerprint
        self.operation = operation or self.operation
        self.step = step or self.step
        self.can_refresh = can_refresh

    def with_context(self, operation: str, step: str) -> "PalamedesConflictError":
        return PalamedesConflictError(
            self.status,
            self.payload,
            self.headers,
            expected_fingerprint=self.expected_fingerprint,
            current_fingerprint=self.current_fingerprint,
            operation=operation,
            step=step,
            can_refresh=self.can_refresh,
        )


class PalamedesClientOperationError(RuntimeError):
    def __init__(self, operation: str, step: str, cause: PalamedesClientError) -> None:
        super().__init__(f"{operation} failed during {step}: {cause}")
        self.operation = operation
        self.step = step
        self.cause = cause
        self.status = cause.status
        self.payload = cause.payload
        self.headers = cause.headers


class PalamedesHealthGateError(RuntimeError):
    def __init__(self, operation: str, step: str, health: Dict[str, Any]) -> None:
        status = str(health.get("status", "")).strip() or "unknown"
        super().__init__(f"{operation} blocked by storage health during {step}: {status}")
        self.operation = operation
        self.step = step
        self.health = health
        self.status = status


RequestTransport = Callable[[str, str, Optional[Dict[str, Any]], Optional[Dict[str, str]]], Tuple[int, Dict[str, Any], Dict[str, str]]]


def diff_top_level_fields(before: Dict[str, Any], after: Dict[str, Any]) -> List[str]:
    changed: List[str] = []
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            changed.append(key)
    return changed


def with_optional_key(payload: Dict[str, Any], key: str, value: str) -> Dict[str, Any]:
    enriched = dict(payload)
    if value:
        enriched[key] = value
    return enriched


def default_transport_factory(host: str, port: int, timeout: float = 10.0) -> RequestTransport:
    def transport(method: str, path: str, body: Optional[Dict[str, Any]], headers: Optional[Dict[str, str]]) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
        connection = HTTPConnection(host, port, timeout=timeout)
        raw_body = None
        merged_headers = dict(headers or {})
        if body is not None:
            raw_body = json.dumps(body).encode("utf-8")
            merged_headers.setdefault("Content-Type", "application/json")
        connection.request(method, path, body=raw_body, headers=merged_headers)
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        response_headers = dict(response.getheaders())
        connection.close()
        return response.status, payload, response_headers

    return transport


@dataclass
class PalamedesClient:
    transport: RequestTransport
    tracked_fingerprint: str = ""

    @classmethod
    def from_http(cls, host: str = "127.0.0.1", port: int = 8787, timeout: float = 10.0) -> "PalamedesClient":
        return cls(transport=default_transport_factory(host, port, timeout=timeout))

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        expected_fingerprint: str = "",
        use_tracked_fingerprint: bool = False,
    ) -> Dict[str, Any]:
        headers: Dict[str, str] = {}
        fingerprint = expected_fingerprint or (self.tracked_fingerprint if use_tracked_fingerprint else "")
        if fingerprint:
            headers["If-Match"] = f'"{fingerprint}"'
        status, payload, response_headers = self.transport(method, path, body, headers or None)
        etag = str(response_headers.get("ETag", "")).strip()
        if etag.startswith('"') and etag.endswith('"') and len(etag) >= 2:
            self.tracked_fingerprint = etag[1:-1]
        elif isinstance(payload, dict) and isinstance(payload.get("fingerprint"), str):
            self.tracked_fingerprint = payload["fingerprint"]
        if status >= 400:
            current_fingerprint = ""
            if isinstance(payload, dict):
                current_fingerprint = str(payload.get("current_fingerprint", "")).strip()
            if not current_fingerprint and etag.startswith('"') and etag.endswith('"') and len(etag) >= 2:
                current_fingerprint = etag[1:-1]
            if status == 412 and isinstance(payload, dict) and str(payload.get("error", "")).strip() == "plan fingerprint mismatch":
                raise PalamedesConflictError(
                    status,
                    payload,
                    response_headers,
                    expected_fingerprint=fingerprint,
                    current_fingerprint=current_fingerprint,
                    operation=str(payload.get("operation", "")).strip(),
                    step=str(payload.get("step", "")).strip(),
                    can_refresh=bool(payload.get("retryable", True)),
                )
            raise PalamedesClientError(status, payload, response_headers)
        return payload

    def _build_cycle_operation_result(
        self,
        *,
        operation: str,
        before: Dict[str, Any],
        mutation_result: Dict[str, Any],
        after: Dict[str, Any],
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        before_score = int(before.get("qa", {}).get("score", 0))
        after_score = int(after.get("qa", {}).get("score", 0))
        return {
            "ok": True,
            "operation": operation,
            "result_type": "planning_cycle",
            "pre_fingerprint": before.get("fingerprint", ""),
            "post_fingerprint": after.get("fingerprint", ""),
            "changed_fields": diff_top_level_fields(before.get("plan", {}), after.get("plan", {})),
            "qa_delta": after_score - before_score,
            "mutation_result": mutation_result,
            "step_results": step_results,
            "pre_cycle": before,
            "post_cycle": after,
        }

    def _enforce_write_health(self, operation: str, cycle: Dict[str, Any], step: str) -> None:
        health = cycle.get("health", {})
        status = str(health.get("status", "")).strip()
        if status and status != "ok":
            raise PalamedesHealthGateError(operation, step, health)

    def get_plan(self) -> Dict[str, Any]:
        return self.request("GET", "/plan")

    def get_qa(self) -> Dict[str, Any]:
        return self.request("GET", "/qa")

    def get_health(self) -> Dict[str, Any]:
        return self.request("GET", "/health")

    def get_doctor(self) -> Dict[str, Any]:
        return self.request("GET", "/doctor")

    def get_cycle(self, *, history_limit: int = 10) -> Dict[str, Any]:
        return self.request("GET", f"/cycle?limit={int(history_limit)}")

    def get_history(self) -> Dict[str, Any]:
        return self.request("GET", "/history")

    def get_reviews(
        self,
        *,
        status: str = "",
        scope: str = "",
        assigned_to: str = "",
        sort_by: str = "requested_at",
        order: str = "desc",
        limit: int = 20,
    ) -> Dict[str, Any]:
        query_parts = [f"limit={int(limit)}"]
        if status:
            query_parts.append(f"status={status}")
        if scope:
            query_parts.append(f"scope={scope}")
        if assigned_to:
            query_parts.append(f"assigned_to={assigned_to}")
        if sort_by:
            query_parts.append(f"sort_by={sort_by}")
        if order:
            query_parts.append(f"order={order}")
        return self.request("GET", f"/reviews?{'&'.join(query_parts)}")

    def get_review(self, request_id: str) -> Dict[str, Any]:
        return self.request("GET", f"/reviews/{quote(request_id, safe='')}")

    def get_reviewer_inbox(self, assignee: str, *, limit: int = 20) -> Dict[str, Any]:
        query_parts = [f"assignee={quote(assignee, safe='')}", f"limit={int(limit)}"]
        return self.request("GET", f"/reviews/inbox?{'&'.join(query_parts)}")

    def get_review_inbox(self, assignee: str, *, limit: int = 20) -> Dict[str, Any]:
        return self.get_reviewer_inbox(assignee, limit=limit)

    def list_reviews(
        self,
        *,
        status: str = "",
        scope: str = "",
        assigned_to: str = "",
        sort_by: str = "requested_at",
        order: str = "desc",
        limit: int = 20,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"limit": limit}
        if status:
            payload["status"] = status
        if scope:
            payload["scope"] = scope
        if assigned_to:
            payload["assigned_to"] = assigned_to
        if sort_by:
            payload["sort_by"] = sort_by
        if order:
            payload["order"] = order
        return self.execute_tool("list_reviews", payload)["result"]

    def get_tools(self) -> Dict[str, Any]:
        return self.request("GET", "/tools")

    def get_tool(self, tool_name: str) -> Dict[str, Any]:
        return self.request("GET", f"/tools/{tool_name}")

    def get_contracts(self) -> Dict[str, Any]:
        return self.request("GET", "/contracts")

    def get_host_action_contract(self, *, role: str = "planner") -> Dict[str, Any]:
        return self.request("GET", f"/host/action-contract?role={role}")

    def validate_plan(self) -> Dict[str, Any]:
        return self.request("GET", "/validate")

    def update_plan(self, payload: Dict[str, Any], *, expected_fingerprint: str = "") -> Dict[str, Any]:
        return self.request("POST", "/plan", body=payload, expected_fingerprint=expected_fingerprint, use_tracked_fingerprint=True)

    def replan(self, payload: Dict[str, Any], *, expected_fingerprint: str = "", idempotency_key: str = "") -> Dict[str, Any]:
        return self.request(
            "POST",
            "/replan",
            body=with_optional_key(payload, "idempotency_key", idempotency_key),
            expected_fingerprint=expected_fingerprint,
            use_tracked_fingerprint=True,
        )

    def add_evidence(self, payload: Dict[str, Any], *, expected_fingerprint: str = "", idempotency_key: str = "") -> Dict[str, Any]:
        return self.request(
            "POST",
            "/evidence",
            body=with_optional_key(payload, "idempotency_key", idempotency_key),
            expected_fingerprint=expected_fingerprint,
            use_tracked_fingerprint=True,
        )

    def execute_tool(self, tool_name: str, payload: Dict[str, Any], *, expected_fingerprint: str = "") -> Dict[str, Any]:
        return self.request(
            "POST",
            "/tools/execute",
            body={"tool": tool_name, "input": payload},
            expected_fingerprint=expected_fingerprint,
        )

    def run_tool(self, tool_name: str, payload: Dict[str, Any], *, expected_fingerprint: str = "") -> Dict[str, Any]:
        return self.execute_tool(tool_name, payload, expected_fingerprint=expected_fingerprint)

    def request_review(self, payload: Dict[str, Any], *, expected_fingerprint: str = "", idempotency_key: str = "") -> Dict[str, Any]:
        return self.execute_tool(
            "request_review",
            with_optional_key(payload, "idempotency_key", idempotency_key),
            expected_fingerprint=expected_fingerprint or self.tracked_fingerprint,
        )["result"]

    def resolve_review(self, payload: Dict[str, Any], *, expected_fingerprint: str = "", idempotency_key: str = "") -> Dict[str, Any]:
        return self.execute_tool(
            "resolve_review",
            with_optional_key(payload, "idempotency_key", idempotency_key),
            expected_fingerprint=expected_fingerprint or self.tracked_fingerprint,
        )["result"]

    def update_review(self, request_id: str, payload: Dict[str, Any], *, expected_fingerprint: str = "", idempotency_key: str = "") -> Dict[str, Any]:
        body = with_optional_key(dict(payload), "idempotency_key", idempotency_key)
        return self.request(
            "POST",
            f"/reviews/{quote(request_id, safe='')}",
            body=body,
            expected_fingerprint=expected_fingerprint or self.tracked_fingerprint,
            use_tracked_fingerprint=True,
        )

    def preview_restore(self, *, revision_id: str = "", previous: bool = False) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if revision_id:
            payload["revision_id"] = revision_id
        if previous:
            payload["previous"] = True
        return self.request("POST", "/restore/preview", body=payload)

    def restore_revision(self, *, revision_id: str = "", previous: bool = False, expected_fingerprint: str = "") -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if revision_id:
            payload["revision_id"] = revision_id
        if previous:
            payload["previous"] = True
        if not expected_fingerprint and self.tracked_fingerprint:
            expected_fingerprint = self.tracked_fingerprint
        return self.request("POST", "/restore", body=payload, expected_fingerprint=expected_fingerprint)

    def apply_and_get_cycle(
        self,
        operation: str,
        payload: Dict[str, Any],
        *,
        history_limit: int = 10,
        expected_fingerprint: str = "",
        require_healthy: bool = False,
    ) -> Dict[str, Any]:
        def restore_mutation(input_payload: Dict[str, Any], *, expected_fingerprint: str = "") -> Dict[str, Any]:
            return self.restore_revision(
                revision_id=str(input_payload.get("revision_id", "")).strip(),
                previous=bool(input_payload.get("previous", False)),
                expected_fingerprint=expected_fingerprint,
            )

        mutation_map = {
            "update_plan": self.update_plan,
            "replan": self.replan,
            "add_evidence": self.add_evidence,
            "request_review": self.request_review,
            "resolve_review": self.resolve_review,
            "update_review": lambda input_payload, *, expected_fingerprint="": self.update_review(
                str(input_payload.get("request_id", "")).strip(),
                input_payload,
                expected_fingerprint=expected_fingerprint,
            ),
            "restore_revision": restore_mutation,
        }
        if operation not in mutation_map:
            raise ValueError(f"unsupported operation: {operation}")
        before = self.get_cycle(history_limit=history_limit)
        if require_healthy:
            self._enforce_write_health(operation, before, "preflight")
        try:
            mutation_result = mutation_map[operation](payload, expected_fingerprint=expected_fingerprint)
        except PalamedesConflictError as exc:
            raise exc.with_context(operation, "mutation") from exc
        except PalamedesClientError as exc:
            raise PalamedesClientOperationError(operation, "mutation", exc) from exc
        try:
            after = self.get_cycle(history_limit=history_limit)
        except PalamedesClientError as exc:
            raise PalamedesClientOperationError(operation, "post_cycle", exc) from exc
        return self._build_cycle_operation_result(
            operation=operation,
            before=before,
            mutation_result=mutation_result,
            after=after,
            step_results={operation: mutation_result},
        )

    def apply_and_get_cycle_with_retry(
        self,
        operation: str,
        payload: Dict[str, Any],
        *,
        history_limit: int = 10,
        expected_fingerprint: str = "",
        allow_non_idempotent_retry: bool = False,
        require_healthy: bool = False,
    ) -> Dict[str, Any]:
        operation_payload = dict(payload)
        if operation in {"add_evidence", "replan", "request_review", "resolve_review", "update_review"} and allow_non_idempotent_retry and not str(operation_payload.get("idempotency_key", "")).strip():
            operation_payload["idempotency_key"] = f"{operation}_{uuid4().hex}"
        attempt = 1
        try:
            result = self.apply_and_get_cycle(
                operation,
                operation_payload,
                history_limit=history_limit,
                expected_fingerprint=expected_fingerprint,
                require_healthy=require_healthy,
            )
            result["retried"] = False
            result["attempts"] = attempt
            return result
        except PalamedesConflictError as exc:
            if not exc.can_refresh:
                raise
            if operation not in {"update_plan", "restore_revision"} and not allow_non_idempotent_retry:
                raise
            refreshed = self.get_cycle(history_limit=history_limit)
            if require_healthy:
                self._enforce_write_health(operation, refreshed, "retry_preflight")
            attempt += 1
            retry_fingerprint = str(refreshed.get("fingerprint", "")).strip() or exc.current_fingerprint
            result = self.apply_and_get_cycle(
                operation,
                operation_payload,
                history_limit=history_limit,
                expected_fingerprint=retry_fingerprint,
                require_healthy=False,
            )
            result["retried"] = True
            result["attempts"] = attempt
            result["retry_from_fingerprint"] = exc.expected_fingerprint
            result["retry_to_fingerprint"] = retry_fingerprint
            return result

    def capture_evidence_cycle(
        self,
        evidence_payload: Dict[str, Any],
        *,
        replan_payload: Optional[Dict[str, Any]] = None,
        history_limit: int = 10,
        idempotency_key: str = "",
        expected_fingerprint: str = "",
        allow_retry: bool = False,
        require_healthy: bool = False,
    ) -> Dict[str, Any]:
        cycle_key = str(idempotency_key).strip()
        if allow_retry and not cycle_key:
            cycle_key = f"capture_evidence_cycle_{uuid4().hex}"

        def run_cycle(write_fingerprint: str = "") -> Dict[str, Any]:
            before = self.get_cycle(history_limit=history_limit)
            if require_healthy:
                self._enforce_write_health("capture_evidence_cycle", before, "preflight")
            evidence_key = f"{cycle_key}:evidence" if cycle_key else ""
            replan_key = f"{cycle_key}:replan" if cycle_key else ""
            try:
                evidence_result = self.add_evidence(
                    evidence_payload,
                    expected_fingerprint=write_fingerprint,
                    idempotency_key=evidence_key,
                )
            except PalamedesConflictError as exc:
                raise exc.with_context("capture_evidence_cycle", "add_evidence") from exc
            except PalamedesClientError as exc:
                raise PalamedesClientOperationError("capture_evidence_cycle", "add_evidence", exc) from exc
            replan_input = dict(replan_payload or {})
            try:
                replan_result = self.replan(
                    replan_input,
                    expected_fingerprint=str(evidence_result.get("fingerprint", "")).strip(),
                    idempotency_key=replan_key,
                )
            except PalamedesConflictError as exc:
                raise exc.with_context("capture_evidence_cycle", "replan") from exc
            except PalamedesClientError as exc:
                raise PalamedesClientOperationError("capture_evidence_cycle", "replan", exc) from exc
            try:
                after = self.get_cycle(history_limit=history_limit)
            except PalamedesClientError as exc:
                raise PalamedesClientOperationError("capture_evidence_cycle", "post_cycle", exc) from exc
            result = self._build_cycle_operation_result(
                operation="capture_evidence_cycle",
                before=before,
                mutation_result=replan_result,
                after=after,
                step_results={
                    "add_evidence": evidence_result,
                    "replan": replan_result,
                },
            )
            result["evidence_result"] = evidence_result
            result["replan_result"] = replan_result
            if cycle_key:
                result["idempotency_key"] = cycle_key
            return result

        try:
            result = run_cycle(expected_fingerprint)
            result["retried"] = False
            result["attempts"] = 1
            return result
        except PalamedesConflictError as exc:
            if not allow_retry or not exc.can_refresh:
                raise
            refreshed = self.get_cycle(history_limit=history_limit)
            if require_healthy:
                self._enforce_write_health("capture_evidence_cycle", refreshed, "retry_preflight")
            retry_fingerprint = str(refreshed.get("fingerprint", "")).strip() or exc.current_fingerprint
            result = run_cycle(retry_fingerprint)
            result["retried"] = True
            result["attempts"] = 2
            result["retry_from_fingerprint"] = exc.expected_fingerprint
            result["retry_to_fingerprint"] = retry_fingerprint
            if cycle_key:
                result["idempotency_key"] = cycle_key
            return result
