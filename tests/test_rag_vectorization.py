
import numpy as np
import pytest
from pathlib import Path
from src.rag import AIRAGStore, TextChunk, RetrievalResult, SimpleEmbedding

class TestRAGVectorization:
    """Tests for vectorized operations in RAG store."""

    @pytest.fixture
    def store(self, tmp_path):
        return AIRAGStore("test_opt_ai", tmp_path)

    def test_semantic_search_vectorized_fallback(self, store):
        # Create chunks that are NOT in the index (by manually searching with external chunks)
        chunks = []
        for i in range(5):
            chunk = TextChunk(
                chunk_id=f"c{i}",
                content=f"content {i}",
                source="test",
                source_type="document",
                timestamp="",
                token_count=10,
                embedding=[0.1] * 10 # Uniform embedding
            )
            chunks.append(chunk)

        # Ensure store is empty so index is empty/invalid
        store.clear()

        # Mock query embedding
        store.embedding_model.embed = lambda text: [0.1] * 10

        # Search
        results = store._semantic_search("query", chunks, top_k=5)

        assert len(results) == 5
        # With identical vectors, cosine similarity should be 1.0 (approx)
        assert results[0].score > 0.99

    def test_semantic_search_dimension_mismatch_query_shorter(self, store):
        # Chunk embedding length 10
        chunks = [
            TextChunk(
                chunk_id="c1",
                content="content",
                source="test",
                source_type="document",
                timestamp="",
                token_count=10,
                embedding=[1.0] * 10
            )
        ]

        # Query embedding length 5
        store.embedding_model.embed = lambda text: [1.0] * 5

        results = store._semantic_search("query", chunks, top_k=1)

        assert len(results) == 1
        # Padding should happen.
        # Query [1...1] (5) -> [1...1, 0...0] (10)
        # Chunk [1...1] (10)
        # Cosine sim should be calculated correctly.
        # Dot product: 5 * 1*1 = 5
        # Norm query (padded): sqrt(5)
        # Norm chunk: sqrt(10)
        # Expected: 5 / (sqrt(5)*sqrt(10)) = 5 / sqrt(50) = 5 / 7.07 = 0.707

        expected = 5 / (np.sqrt(5) * np.sqrt(10))
        assert abs(results[0].score - expected) < 0.001

    def test_semantic_search_dimension_mismatch_chunk_shorter(self, store):
        # Chunk embedding length 5
        chunks = [
            TextChunk(
                chunk_id="c1",
                content="content",
                source="test",
                source_type="document",
                timestamp="",
                token_count=10,
                embedding=[1.0] * 5
            )
        ]

        # Query embedding length 10
        store.embedding_model.embed = lambda text: [1.0] * 10

        results = store._semantic_search("query", chunks, top_k=1)

        assert len(results) == 1
        # Chunk padded to 10
        # Expected same as above
        expected = 5 / (np.sqrt(5) * np.sqrt(10))
        assert abs(results[0].score - expected) < 0.001

    def test_semantic_search_mixed_indexed_and_fallback(self, store):
        # Add one chunk to store (indexed)
        store.add_memory("memory chunk", importance=1.0) # This triggers embedding and index update

        # Create an external chunk (fallback)
        fallback_chunk = TextChunk(
            chunk_id="external",
            content="external",
            source="test",
            source_type="document",
            timestamp="",
            token_count=10,
            embedding=[0.1] * 100 # Match default dim approx
        )

        # Search
        # Note: add_memory might use default embedding model which uses 10000 dim sparse vector.
        # To avoid massive mismatch issues in test, we should mock embedding model before add_memory if possible,
        # or just let it be.
        # Since our fallback logic handles mismatch, it should be fine.

        chunks = list(store.chunks.values()) + [fallback_chunk]

        # Search
        results = store._semantic_search("query", chunks, top_k=10)

        assert len(results) == 2
        ids = {r.chunk.chunk_id for r in results}
        assert "external" in ids
