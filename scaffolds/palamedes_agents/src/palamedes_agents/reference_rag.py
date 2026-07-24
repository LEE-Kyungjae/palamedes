#!/usr/bin/env python3
"""Deterministic reference retrieval for Palamedes strategy prompts.

The module deliberately owns retrieval and provenance, not strategic judgment.
Hosts may replace the lexical scorer with BM25/vector/reranking later while
preserving the returned context contract.
"""

import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


REFERENCE_TYPES = {"success_case", "failure_case", "counter_view", "paper", "review", "behavior_evidence", "other"}
SEARCHABLE_FIELDS = ("context", "problem", "mechanism", "outcome", "failure_boundary", "content")


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _tokens(value: str) -> List[str]:
    return re.findall(r"[0-9a-zA-Z가-힣_+-]+", value.lower())


def normalize_reference_pattern(item: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("reference corpus entries must be objects")
    reference_id = _text(item.get("reference_id")) or f"reference_{index + 1}"
    source = _text(item.get("source")) or _text(item.get("source_url")) or reference_id
    source_type = _text(item.get("source_type")) or "other"
    if source_type not in REFERENCE_TYPES:
        source_type = "other"
    confidence = item.get("confidence", 50)
    if not isinstance(confidence, int) or isinstance(confidence, bool):
        confidence = 50
    return {
        "reference_id": reference_id,
        "source": source,
        "source_url": _text(item.get("source_url")),
        "source_type": source_type,
        "context": _text(item.get("context")),
        "problem": _text(item.get("problem")),
        "mechanism": _text(item.get("mechanism")),
        "outcome": _text(item.get("outcome")),
        "failure_boundary": _text(item.get("failure_boundary")),
        "content": _text(item.get("content")),
        "evidence_quotes": _strings(item.get("evidence_quotes")),
        "applicable_axes": _strings(item.get("applicable_axes")),
        "confidence": max(0, min(100, confidence)),
    }


def _document_frequency(patterns: Sequence[Dict[str, Any]]) -> Counter:
    counts: Counter = Counter()
    for pattern in patterns:
        text = " ".join(_text(pattern.get(field)) for field in SEARCHABLE_FIELDS)
        text += " " + " ".join(pattern.get("applicable_axes", []))
        counts.update(set(_tokens(text)))
    return counts


def _pattern_tokens(pattern: Dict[str, Any]) -> List[str]:
    text = " ".join(_text(pattern.get(field)) for field in SEARCHABLE_FIELDS)
    text += " " + " ".join(pattern.get("applicable_axes", []))
    return _tokens(text)


def _score(
    query_tokens: Sequence[str],
    pattern: Dict[str, Any],
    document_frequency: Counter,
    corpus_size: int,
    average_document_length: float,
) -> float:
    if not query_tokens:
        return 0.0
    field_weights = {
        "mechanism": 1.5,
        "problem": 1.35,
        "failure_boundary": 1.3,
        "outcome": 1.15,
        "context": 1.0,
        "content": 0.8,
    }
    field_score = 0.0
    unique_query = set(query_tokens)
    for field, weight in field_weights.items():
        field_counts = Counter(_tokens(_text(pattern.get(field))))
        for token in unique_query:
            if token not in field_counts:
                continue
            inverse_frequency = math.log((corpus_size + 1) / (document_frequency[token] + 1)) + 1.0
            field_score += weight * inverse_frequency * (1.0 + math.log(field_counts[token]))
    axis_tokens = set(_tokens(" ".join(pattern.get("applicable_axes", []))))
    field_score += len(unique_query & axis_tokens) * 1.4
    document_tokens = _pattern_tokens(pattern)
    document_counts = Counter(document_tokens)
    document_length = len(document_tokens)
    bm25_score = 0.0
    k1 = 1.5
    b = 0.75
    for token in unique_query:
        frequency = document_counts[token]
        if not frequency:
            continue
        inverse_frequency = math.log(1 + ((corpus_size - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5)))
        denominator = frequency + k1 * (1 - b + b * document_length / max(1.0, average_document_length))
        bm25_score += inverse_frequency * (frequency * (k1 + 1) / denominator)
    confidence_weight = 0.75 + (pattern.get("confidence", 50) / 200)
    combined = (field_score / max(1, len(unique_query))) + bm25_score
    return round(combined * confidence_weight, 6)


def _select_diverse(scored: Sequence[Tuple[float, Dict[str, Any]]], limit: int) -> List[Tuple[float, Dict[str, Any]]]:
    by_type: Dict[str, List[Tuple[float, Dict[str, Any]]]] = defaultdict(list)
    for entry in scored:
        by_type[entry[1]["source_type"]].append(entry)
    preferred = ["success_case", "failure_case", "counter_view", "behavior_evidence", "review", "paper", "other"]
    selected: List[Tuple[float, Dict[str, Any]]] = []
    seen = set()
    for source_type in preferred:
        if by_type[source_type] and len(selected) < limit:
            entry = by_type[source_type][0]
            selected.append(entry)
            seen.add(entry[1]["reference_id"])
    for entry in scored:
        if len(selected) >= limit:
            break
        if entry[1]["reference_id"] not in seen:
            selected.append(entry)
            seen.add(entry[1]["reference_id"])
    return sorted(selected, key=lambda entry: entry[0], reverse=True)


def retrieve_reference_context(
    query: str,
    corpus: Iterable[Dict[str, Any]],
    *,
    limit: int = 6,
    minimum_score: float = 0.08,
    semantic_scores: Optional[Mapping[str, float]] = None,
    semantic_weight: float = 0.35,
) -> Dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("reference retrieval query must be non-empty")
    patterns = [normalize_reference_pattern(item, index) for index, item in enumerate(corpus)]
    query_tokens = _tokens(query)
    frequencies = _document_frequency(patterns)
    document_lengths = [len(_pattern_tokens(item)) for item in patterns]
    average_document_length = sum(document_lengths) / len(document_lengths) if document_lengths else 0.0
    scored = []
    for item in patterns:
        lexical_score = _score(query_tokens, item, frequencies, len(patterns), average_document_length)
        semantic_score = float(semantic_scores.get(item["reference_id"], 0.0)) if semantic_scores else 0.0
        score = lexical_score + max(0.0, semantic_score) * max(0.0, semantic_weight)
        scored.append((round(score, 6), item))
    relevant = [entry for entry in sorted(scored, key=lambda entry: entry[0], reverse=True) if entry[0] >= minimum_score]
    selected = _select_diverse(relevant, max(1, limit))
    source_types = sorted({item["source_type"] for _, item in selected})
    cited_count = sum(bool(item["source_url"] or item["evidence_quotes"]) for _, item in selected)
    sufficient = len(selected) >= 2 and len(source_types) >= 2 and cited_count >= 1
    reasons: List[str] = []
    if len(selected) < 2:
        reasons.append("fewer_than_two_relevant_references")
    if len(source_types) < 2:
        reasons.append("insufficient_viewpoint_diversity")
    if cited_count < 1:
        reasons.append("missing_citable_evidence")
    return {
        "query": query.strip(),
        "retrieval_method": "hybrid_bm25_semantic_with_type_diversity" if semantic_scores else "bm25_field_weighted_with_type_diversity",
        "corpus_size": len(patterns),
        "selected_count": len(selected),
        "source_types": source_types,
        "quality_gate": {
            "status": "sufficient" if sufficient else "insufficient",
            "reasons": reasons,
            "recommended_decision": "generate_with_citations" if sufficient else "stop_and_research",
        },
        "patterns": [dict(item, retrieval_score=score) for score, item in selected],
    }


def resolve_reference_corpus(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    corpus = payload.get("reference_corpus", [])
    if not isinstance(corpus, list):
        raise ValueError("reference_corpus must be an array")
    store_path = _text(payload.get("reference_store_path"))
    if not corpus and store_path:
        from pathlib import Path

        from palamedes_agents.reference_store import ReferenceStore

        corpus = ReferenceStore(Path(store_path)).list()
    return corpus


def reference_query(payload: Dict[str, Any]) -> str:
    query_parts = [
        _text(payload.get("topic")),
        _text(payload.get("idea")),
        _text(payload.get("target_user")),
        _text(payload.get("problem")),
        _text(payload.get("differentiation")),
    ]
    return " ".join(part for part in query_parts if part) or "product strategy reference insight"


def build_reference_rag_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    corpus = resolve_reference_corpus(payload)
    if not corpus:
        return {}
    semantic_scores = payload.get("reference_semantic_scores")
    if semantic_scores is not None and not isinstance(semantic_scores, dict):
        raise ValueError("reference_semantic_scores must be an object")
    return retrieve_reference_context(reference_query(payload), corpus, semantic_scores=semantic_scores)


def validate_reference_grounding(report: Dict[str, Any], retrieval: Dict[str, Any]) -> List[str]:
    """Check that provider judgment respects retrieval sufficiency and provenance."""
    if not retrieval:
        return []
    errors: List[str] = []
    gate = retrieval.get("quality_gate", {})
    if isinstance(gate, dict) and gate.get("status") == "insufficient" and report.get("decision") != "stop_and_research":
        errors.append("insufficient reference retrieval requires decision=stop_and_research")
    patterns = retrieval.get("patterns", [])
    pattern_by_id = {
        item.get("reference_id"): item
        for item in patterns
        if isinstance(item, dict) and isinstance(item.get("reference_id"), str)
    } if isinstance(patterns, list) else {}
    allowed_ids = set(pattern_by_id)
    insights = report.get("reference_insights", [])
    if not isinstance(insights, list):
        return errors
    if isinstance(gate, dict) and gate.get("status") == "sufficient" and not insights:
        errors.append("sufficient reference retrieval requires at least one reference insight")
    for index, insight in enumerate(insights):
        if not isinstance(insight, dict):
            continue
        reference_ids = insight.get("reference_ids", [])
        if not isinstance(reference_ids, list) or not reference_ids:
            errors.append(f"reference_insights[{index}] must cite at least one retrieved reference_id")
            continue
        unknown = sorted(reference_id for reference_id in reference_ids if reference_id not in allowed_ids)
        if unknown:
            errors.append(f"reference_insights[{index}] cites references outside retrieval context: {', '.join(unknown)}")
            continue
        expected_urls = {
            pattern_by_id[reference_id]["source_url"]
            for reference_id in reference_ids
            if pattern_by_id[reference_id].get("source_url")
        }
        actual_urls = set(insight.get("source_urls", [])) if isinstance(insight.get("source_urls"), list) else set()
        if not expected_urls.issubset(actual_urls):
            errors.append(f"reference_insights[{index}] does not preserve cited source URLs")
        expected_quotes = {
            quote
            for reference_id in reference_ids
            for quote in pattern_by_id[reference_id].get("evidence_quotes", [])
        }
        actual_quotes = set(insight.get("evidence_quotes", [])) if isinstance(insight.get("evidence_quotes"), list) else set()
        if not expected_quotes.issubset(actual_quotes):
            errors.append(f"reference_insights[{index}] does not preserve cited evidence quotes")
    return errors
