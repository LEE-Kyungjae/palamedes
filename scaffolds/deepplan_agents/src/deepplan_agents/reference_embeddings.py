#!/usr/bin/env python3
"""Optional semantic-scoring adapters for hybrid reference retrieval."""

import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from deepplan_agents.reference_rag import SEARCHABLE_FIELDS


def pattern_embedding_text(pattern: Dict[str, Any]) -> str:
    parts = [str(pattern.get("source", "")).strip(), str(pattern.get("source_type", "")).strip()]
    parts.extend(str(pattern.get(field, "")).strip() for field in SEARCHABLE_FIELDS)
    axes = pattern.get("applicable_axes", [])
    if isinstance(axes, list):
        parts.extend(str(item).strip() for item in axes)
    return "\n".join(part for part in parts if part)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("embedding vectors must be non-empty and have equal dimensions")
    dot = sum(float(a) * float(b) for a, b in zip(left, right))
    left_norm = math.sqrt(sum(float(value) ** 2 for value in left))
    right_norm = math.sqrt(sum(float(value) ** 2 for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


@dataclass
class OpenAIReferenceEmbeddingProvider:
    model: str = "text-embedding-3-small"
    client: Optional[Any] = None

    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("OpenAI embeddings require the openai Python package") from exc
        return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def semantic_scores(self, query: str, patterns: List[Dict[str, Any]]) -> Dict[str, float]:
        if not query.strip():
            raise ValueError("embedding query must be non-empty")
        if not patterns:
            return {}
        inputs = [query] + [pattern_embedding_text(pattern) for pattern in patterns]
        response = self._client().embeddings.create(model=self.model, input=inputs, encoding_format="float")
        data = getattr(response, "data", None)
        if not isinstance(data, list):
            raise ValueError("OpenAI embeddings response must contain data")
        ordered = sorted(data, key=lambda item: int(getattr(item, "index", item.get("index", 0) if isinstance(item, dict) else 0)))
        vectors = [getattr(item, "embedding", item.get("embedding") if isinstance(item, dict) else None) for item in ordered]
        if len(vectors) != len(inputs) or not all(isinstance(vector, list) for vector in vectors):
            raise ValueError("OpenAI embeddings response did not match requested inputs")
        query_vector = vectors[0]
        return {
            pattern["reference_id"]: round(max(0.0, cosine_similarity(query_vector, vector)), 6)
            for pattern, vector in zip(patterns, vectors[1:])
        }
