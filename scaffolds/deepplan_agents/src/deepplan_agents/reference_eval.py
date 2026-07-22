#!/usr/bin/env python3
"""Offline evaluation for DeepPlan reference retrieval."""

from typing import Any, Dict, Iterable, List

from deepplan_agents.reference_rag import retrieve_reference_context


def evaluate_reference_retrieval(dataset: Dict[str, Any], corpus: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(dataset, dict):
        raise ValueError("reference evaluation dataset must be an object")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("reference evaluation dataset requires non-empty cases")
    corpus_items = list(corpus)
    reports: List[Dict[str, Any]] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"evaluation case {index} must be an object")
        case_id = str(case.get("id", f"case_{index + 1}")).strip()
        query = str(case.get("query", "")).strip()
        if not query:
            raise ValueError(f"evaluation case {case_id} requires query")
        relevant_ids = {str(item) for item in case.get("relevant_reference_ids", []) if str(item).strip()}
        expected_types = {str(item) for item in case.get("expected_source_types", []) if str(item).strip()}
        expected_sufficient = bool(case.get("expect_sufficient", True))
        result = retrieve_reference_context(query, corpus_items, limit=int(case.get("limit", 6)))
        selected_ids = [item["reference_id"] for item in result["patterns"]]
        selected_types = set(result["source_types"])
        hits = relevant_ids & set(selected_ids)
        recall = len(hits) / len(relevant_ids) if relevant_ids else 1.0
        reciprocal_rank = 0.0
        for rank, reference_id in enumerate(selected_ids, start=1):
            if reference_id in relevant_ids:
                reciprocal_rank = 1.0 / rank
                break
        actual_sufficient = result["quality_gate"]["status"] == "sufficient"
        reports.append(
            {
                "id": case_id,
                "query": query,
                "selected_reference_ids": selected_ids,
                "relevant_hits": sorted(hits),
                "recall_at_k": round(recall, 6),
                "reciprocal_rank": round(reciprocal_rank, 6),
                "source_type_coverage": sorted(expected_types & selected_types),
                "source_type_recall": round(len(expected_types & selected_types) / len(expected_types), 6) if expected_types else 1.0,
                "gate_correct": actual_sufficient == expected_sufficient,
                "quality_gate": result["quality_gate"],
            }
        )
    count = len(reports)
    metrics = {
        "case_count": count,
        "mean_recall_at_k": round(sum(item["recall_at_k"] for item in reports) / count, 6),
        "mean_reciprocal_rank": round(sum(item["reciprocal_rank"] for item in reports) / count, 6),
        "mean_source_type_recall": round(sum(item["source_type_recall"] for item in reports) / count, 6),
        "gate_accuracy": round(sum(item["gate_correct"] for item in reports) / count, 6),
    }
    thresholds = dataset.get("thresholds", {}) if isinstance(dataset.get("thresholds", {}), dict) else {}
    checks = {
        metric: metrics[metric] >= float(target)
        for metric, target in thresholds.items()
        if metric in metrics and isinstance(target, (int, float)) and not isinstance(target, bool)
    }
    return {
        "ok": all(checks.values()),
        "name": str(dataset.get("name", "reference-retrieval-evaluation")).strip(),
        "metrics": metrics,
        "thresholds": thresholds,
        "checks": checks,
        "cases": reports,
    }
