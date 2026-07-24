#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.reference_embeddings import OpenAIReferenceEmbeddingProvider, cosine_similarity, pattern_embedding_text


class ReferenceEmbeddingTests(unittest.TestCase):
    def test_cosine_similarity_and_pattern_text(self):
        self.assertEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        text = pattern_embedding_text({"source": "Case", "problem": "Generic idea", "mechanism": "Decision gate", "applicable_axes": ["direction"]})
        self.assertIn("Decision gate", text)
        self.assertIn("direction", text)

    def test_openai_embedding_provider_batches_query_and_patterns(self):
        class Embedding:
            def __init__(self, index, embedding):
                self.index = index
                self.embedding = embedding

        class Embeddings:
            def __init__(self):
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                return type("Response", (), {"data": [Embedding(0, [1.0, 0.0]), Embedding(1, [0.8, 0.2]), Embedding(2, [0.0, 1.0])]})()

        class Client:
            def __init__(self):
                self.embeddings = Embeddings()

        client = Client()
        provider = OpenAIReferenceEmbeddingProvider(model="text-embedding-3-small", client=client)
        scores = provider.semantic_scores(
            "generic idea",
            [
                {"reference_id": "close", "source": "Close", "problem": "generic idea"},
                {"reference_id": "far", "source": "Far", "problem": "unrelated"},
            ],
        )
        self.assertGreater(scores["close"], scores["far"])
        call = client.embeddings.calls[0]
        self.assertEqual(call["model"], "text-embedding-3-small")
        self.assertEqual(call["encoding_format"], "float")
        self.assertEqual(len(call["input"]), 3)


if __name__ == "__main__":
    unittest.main()
