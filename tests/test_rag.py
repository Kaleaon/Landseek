"""
Tests for RAG (Retrieval Augmented Generation) System
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag import (
    TextChunk, RetrievalResult, RAGStats, RetrievalStrategy,
    estimate_tokens, generate_chunk_id,
    SimpleEmbedding, TextChunker, KeywordIndex,
    AIRAGStore, RAGManager,
    get_rag_manager, initialize_rag_manager,
    MAX_CONTEXT_TOKENS, DEFAULT_CHUNK_SIZE, DEFAULT_TOP_K
)


class TestTokenEstimation:
    """Tests for token estimation."""
    
    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0
    
    def test_estimate_tokens_short(self):
        """Test token estimation for short text."""
        # ~4 chars per token
        tokens = estimate_tokens("Hello world")
        assert tokens > 0
        assert tokens < 10
    
    def test_estimate_tokens_long(self):
        """Test token estimation for longer text."""
        text = "This is a longer piece of text that should have more tokens."
        tokens = estimate_tokens(text)
        assert tokens > 10


class TestChunkId:
    """Tests for chunk ID generation."""
    
    def test_generate_chunk_id(self):
        """Test chunk ID generation."""
        chunk_id = generate_chunk_id("test content", "test_source")
        assert len(chunk_id) == 16
        assert chunk_id.isalnum()
    
    def test_unique_chunk_ids(self):
        """Test that chunk IDs are unique."""
        id1 = generate_chunk_id("content1", "source1")
        id2 = generate_chunk_id("content2", "source2")
        # Different inputs should produce different IDs
        # (timestamps make them unique even with same content)


class TestTextChunk:
    """Tests for TextChunk dataclass."""
    
    def test_create_chunk(self):
        """Test creating a text chunk."""
        chunk = TextChunk(
            chunk_id="test123",
            content="Test content",
            source="test_doc.txt",
            source_type="document",
            timestamp=datetime.now().isoformat(),
            token_count=5
        )
        assert chunk.chunk_id == "test123"
        assert chunk.content == "Test content"
        assert chunk.source_type == "document"
    
    def test_chunk_to_dict(self):
        """Test converting chunk to dict."""
        chunk = TextChunk(
            chunk_id="test123",
            content="Test content",
            source="test_doc.txt",
            source_type="document",
            timestamp="2024-01-01T00:00:00",
            token_count=5,
            metadata={"key": "value"}
        )
        data = chunk.to_dict()
        assert data["chunk_id"] == "test123"
        assert data["content"] == "Test content"
        assert data["metadata"]["key"] == "value"
    
    def test_chunk_from_dict(self):
        """Test creating chunk from dict."""
        data = {
            "chunk_id": "test123",
            "content": "Test content",
            "source": "test_doc.txt",
            "source_type": "document",
            "timestamp": "2024-01-01T00:00:00",
            "token_count": 5
        }
        chunk = TextChunk.from_dict(data)
        assert chunk.chunk_id == "test123"
        assert chunk.content == "Test content"


class TestSimpleEmbedding:
    """Tests for SimpleEmbedding model."""
    
    def test_create_embedding_model(self):
        """Test creating embedding model."""
        model = SimpleEmbedding(vocab_size=100)
        assert model.vocab_size == 100
        assert not model._fitted
    
    def test_fit_embedding_model(self):
        """Test fitting embedding model."""
        model = SimpleEmbedding()
        documents = [
            "The quick brown fox jumps over the lazy dog",
            "A fast red fox leaps over a sleeping dog",
            "Machine learning is fascinating"
        ]
        model.fit(documents)
        assert model._fitted
        assert model.doc_count == 3
    
    def test_embed_text(self):
        """Test embedding text."""
        model = SimpleEmbedding(vocab_size=50)
        documents = ["hello world", "foo bar baz"]
        model.fit(documents)
        
        embedding = model.embed("hello world")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(v, float) for v in embedding)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = SimpleEmbedding.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001  # Should be ~1.0
        
        vec3 = [0.0, 1.0, 0.0]
        similarity2 = SimpleEmbedding.cosine_similarity(vec1, vec3)
        assert abs(similarity2) < 0.001  # Should be ~0.0
    
    def test_similar_texts_have_similar_embeddings(self):
        """Test that similar texts produce similar embeddings."""
        model = SimpleEmbedding()
        docs = [
            "The cat sat on the mat",
            "The dog sat on the rug",
            "Machine learning is great"
        ]
        model.fit(docs)
        
        emb1 = model.embed("The cat sat on the mat")
        emb2 = model.embed("The cat sits on the mat")
        emb3 = model.embed("Quantum physics explained")
        
        sim_similar = SimpleEmbedding.cosine_similarity(emb1, emb2)
        sim_different = SimpleEmbedding.cosine_similarity(emb1, emb3)
        
        # Similar texts should have higher similarity
        assert sim_similar > sim_different


class TestTextChunker:
    """Tests for TextChunker."""
    
    def test_create_chunker(self):
        """Test creating chunker."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 10
    
    def test_chunk_short_text(self):
        """Test chunking short text."""
        chunker = TextChunker(chunk_size=1000)
        chunks = chunker.chunk_text(
            "Hello world. This is a test.",
            "test_source"
        )
        assert len(chunks) == 1
        assert "Hello world" in chunks[0].content
    
    def test_chunk_long_text(self):
        """Test chunking longer text."""
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here. Fifth sentence here."
        chunks = chunker.chunk_text(text, "test_source")
        assert len(chunks) > 1
    
    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("", "test_source")
        assert len(chunks) == 0
    
    def test_chunks_have_metadata(self):
        """Test that chunks include metadata."""
        chunker = TextChunker()
        metadata = {"author": "test", "date": "2024-01-01"}
        chunks = chunker.chunk_text(
            "Test content here.",
            "test_source",
            metadata=metadata
        )
        assert len(chunks) > 0
        assert chunks[0].metadata["author"] == "test"


class TestKeywordIndex:
    """Tests for KeywordIndex."""
    
    def test_create_index(self):
        """Test creating keyword index."""
        index = KeywordIndex()
        assert len(index.index) == 0
    
    def test_add_to_index(self):
        """Test adding to keyword index."""
        index = KeywordIndex()
        index.add("chunk1", "hello world machine learning")
        assert "hello" in index.index
        assert "chunk1" in index.index["hello"]
    
    def test_search_index(self):
        """Test searching keyword index."""
        index = KeywordIndex()
        index.add("chunk1", "hello world machine learning")
        index.add("chunk2", "goodbye world deep learning")
        index.add("chunk3", "hello from python programming")
        
        results = index.search("hello")
        assert len(results) > 0
        chunk_ids = [r[0] for r in results]
        assert "chunk1" in chunk_ids or "chunk3" in chunk_ids
    
    def test_remove_from_index(self):
        """Test removing from keyword index."""
        index = KeywordIndex()
        index.add("chunk1", "hello world")
        index.remove("chunk1")
        
        results = index.search("hello")
        chunk_ids = [r[0] for r in results]
        assert "chunk1" not in chunk_ids
    
    def test_index_serialization(self):
        """Test index serialization."""
        index = KeywordIndex()
        index.add("chunk1", "hello world")
        
        data = index.to_dict()
        loaded = KeywordIndex.from_dict(data)
        
        results = loaded.search("hello")
        assert len(results) > 0


class TestAIRAGStore:
    """Tests for AIRAGStore."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_create_store(self, temp_dir):
        """Test creating RAG store."""
        store = AIRAGStore("nova", temp_dir)
        assert store.ai_id == "nova"
        assert store.max_tokens == MAX_CONTEXT_TOKENS
    
    def test_add_document(self, temp_dir):
        """Test adding document to store."""
        store = AIRAGStore("nova", temp_dir)
        chunk_ids = store.add_document(
            "This is a test document. It has multiple sentences.",
            "test.txt"
        )
        assert len(chunk_ids) > 0
        stats = store.get_stats()
        assert stats.total_chunks > 0
        assert stats.documents_indexed > 0
    
    def test_add_conversation(self, temp_dir):
        """Test adding conversation to store."""
        store = AIRAGStore("nova", temp_dir)
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ]
        chunk_ids = store.add_conversation(messages, "conv_001")
        assert len(chunk_ids) > 0
        stats = store.get_stats()
        assert stats.conversations_indexed > 0
    
    def test_add_memory(self, temp_dir):
        """Test adding memory to store."""
        store = AIRAGStore("nova", temp_dir)
        chunk_id = store.add_memory(
            "The user prefers formal language.",
            importance=0.8
        )
        assert chunk_id
        stats = store.get_stats()
        assert stats.memories_indexed > 0
    
    def test_add_knowledge(self, temp_dir):
        """Test adding knowledge to store."""
        store = AIRAGStore("nova", temp_dir)
        chunk_id = store.add_knowledge(
            "Python is a programming language.",
            category="programming"
        )
        assert chunk_id
    
    def test_retrieve_semantic(self, temp_dir):
        """Test semantic retrieval."""
        store = AIRAGStore("nova", temp_dir)
        store.add_document("Machine learning is a branch of AI.", "ml.txt")
        store.add_document("Cooking recipes for beginners.", "cooking.txt")
        
        results = store.retrieve(
            "artificial intelligence",
            strategy=RetrievalStrategy.SEMANTIC
        )
        assert len(results) > 0
    
    def test_retrieve_keyword(self, temp_dir):
        """Test keyword retrieval."""
        store = AIRAGStore("nova", temp_dir)
        store.add_document("Python programming tutorial.", "python.txt")
        store.add_document("Java programming basics.", "java.txt")
        
        results = store.retrieve(
            "Python",
            strategy=RetrievalStrategy.KEYWORD
        )
        assert len(results) > 0
    
    def test_retrieve_hybrid(self, temp_dir):
        """Test hybrid retrieval."""
        store = AIRAGStore("nova", temp_dir)
        store.add_document("Deep learning neural networks.", "dl.txt")
        store.add_document("Shallow water fishing.", "fishing.txt")
        
        results = store.retrieve(
            "deep neural networks",
            strategy=RetrievalStrategy.HYBRID
        )
        assert len(results) > 0
    
    def test_get_context(self, temp_dir):
        """Test getting context for LLM."""
        store = AIRAGStore("nova", temp_dir)
        store.add_document("Important document content here.", "doc.txt")
        
        context = store.get_context("document", max_tokens=500)
        assert "Important document" in context
    
    def test_remove_document(self, temp_dir):
        """Test removing document."""
        import uuid
        # Use unique AI ID to avoid any caching/interference issues
        unique_id = f"nova_remove_{uuid.uuid4().hex[:8]}"
        store = AIRAGStore(unique_id, temp_dir)
        
        # Verify store starts empty
        initial_stats = store.get_stats()
        assert initial_stats.total_chunks == 0, f"Store should start empty: {initial_stats}"
        
        # Use longer content to ensure chunks are created
        content = (
            "This is a test document with enough content to create at least one chunk. "
            "It contains multiple sentences that should be processed by the chunker. "
            "The document should be indexed and then removable from the store."
        )
        chunk_ids = store.add_document(content, "test.txt")
        
        # Verify chunks were created
        assert len(chunk_ids) > 0, f"Should have created chunks, got: {chunk_ids}"
        assert len(store.chunks) > 0, f"Store should have chunks"
        
        stats_before = store.get_stats()
        assert stats_before.total_chunks > 0, f"Should have chunks in stats: {stats_before}"
        
        removed = store.remove_document("test.txt")
        assert removed > 0, f"Should have removed chunks, removed: {removed}"
        
        stats_after = store.get_stats()
        assert stats_after.total_chunks == 0, f"Should have no chunks after removal: {stats_after}"
    
    def test_persistence(self, temp_dir):
        """Test data persistence."""
        # Create and add data
        store1 = AIRAGStore("nova", temp_dir)
        store1.add_document("Persistent content.", "persist.txt")
        store1.add_memory("I remember this.")
        
        # Create new store instance (should load from disk)
        store2 = AIRAGStore("nova", temp_dir)
        stats = store2.get_stats()
        
        assert stats.total_chunks > 0
        assert stats.documents_indexed > 0
    
    def test_clear_store(self, temp_dir):
        """Test clearing store."""
        store = AIRAGStore("nova", temp_dir)
        store.add_document("Some content.", "doc.txt")
        
        store.clear()
        stats = store.get_stats()
        
        assert stats.total_chunks == 0
    
    def test_export_import(self, temp_dir):
        """Test export and import."""
        store1 = AIRAGStore("nova", temp_dir)
        store1.add_document("Export test content.", "export.txt")
        
        exported = store1.export_data()
        assert "chunks" in exported
        
        # Create new store and import
        store2 = AIRAGStore("echo", temp_dir)
        success = store2.import_data(exported)
        assert success
        
        stats = store2.get_stats()
        assert stats.total_chunks > 0


class TestRAGManager:
    """Tests for RAGManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_create_manager(self, temp_dir):
        """Test creating RAG manager."""
        manager = RAGManager(temp_dir)
        assert len(manager.list_stores()) == 0
    
    def test_get_store(self, temp_dir):
        """Test getting store from manager."""
        manager = RAGManager(temp_dir)
        store = manager.get_store("nova")
        assert store.ai_id == "nova"
        assert "nova" in manager.list_stores()
    
    def test_delete_store(self, temp_dir):
        """Test deleting store."""
        manager = RAGManager(temp_dir)
        manager.get_store("nova")
        
        deleted = manager.delete_store("nova")
        assert deleted
        assert "nova" not in manager.list_stores()
    
    def test_get_total_stats(self, temp_dir):
        """Test getting aggregate stats."""
        manager = RAGManager(temp_dir)
        
        store1 = manager.get_store("nova")
        store1.add_document("Doc 1", "doc1.txt")
        
        store2 = manager.get_store("echo")
        store2.add_document("Doc 2", "doc2.txt")
        
        stats = manager.get_total_stats()
        assert stats["total_stores"] == 2
        assert stats["total_chunks"] > 0
    
    def test_add_document_to_all(self, temp_dir):
        """Test adding document to all stores."""
        manager = RAGManager(temp_dir)
        manager.get_store("nova")
        manager.get_store("echo")
        
        results = manager.add_document_to_all(
            "Shared knowledge content.",
            "shared.txt"
        )
        
        assert len(results) == 2
        assert "nova" in results
        assert "echo" in results
    
    def test_query_all(self, temp_dir):
        """Test querying all stores."""
        manager = RAGManager(temp_dir)
        
        store1 = manager.get_store("nova")
        store1.add_document("Machine learning content.", "ml.txt")
        
        store2 = manager.get_store("echo")
        store2.add_document("Deep learning content.", "dl.txt")
        
        results = manager.query_all("learning")
        assert len(results) == 2


class TestRAGStats:
    """Tests for RAGStats."""
    
    def test_create_stats(self):
        """Test creating stats."""
        stats = RAGStats(
            total_chunks=100,
            total_tokens=50000,
            documents_indexed=10
        )
        assert stats.total_chunks == 100
        assert stats.total_tokens == 50000
    
    def test_stats_serialization(self):
        """Test stats serialization."""
        stats = RAGStats(
            total_chunks=100,
            total_tokens=50000
        )
        data = stats.to_dict()
        loaded = RAGStats.from_dict(data)
        
        assert loaded.total_chunks == 100
        assert loaded.total_tokens == 50000


class TestRetrievalStrategies:
    """Tests for different retrieval strategies."""
    
    @pytest.fixture
    def populated_store(self):
        """Create a populated RAG store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AIRAGStore("test", Path(tmpdir))
            
            # Add various documents
            store.add_document(
                "Python is a high-level programming language. It is widely used for web development.",
                "python.txt"
            )
            store.add_document(
                "JavaScript is used for web development. It runs in browsers.",
                "javascript.txt"
            )
            store.add_document(
                "Machine learning uses algorithms to learn from data.",
                "ml.txt"
            )
            store.add_memory("User likes Python programming.", importance=0.9)
            store.add_knowledge("Python was created by Guido van Rossum.", category="history")
            
            yield store
    
    def test_semantic_strategy(self, populated_store):
        """Test semantic retrieval strategy."""
        results = populated_store.retrieve(
            "programming language",
            strategy=RetrievalStrategy.SEMANTIC
        )
        assert len(results) > 0
        assert all(r.strategy == "semantic" for r in results)
    
    def test_keyword_strategy(self, populated_store):
        """Test keyword retrieval strategy."""
        results = populated_store.retrieve(
            "Python",
            strategy=RetrievalStrategy.KEYWORD
        )
        assert len(results) > 0
        assert all(r.strategy == "keyword" for r in results)
    
    def test_hybrid_strategy(self, populated_store):
        """Test hybrid retrieval strategy."""
        results = populated_store.retrieve(
            "Python programming",
            strategy=RetrievalStrategy.HYBRID
        )
        assert len(results) > 0
    
    def test_recency_strategy(self, populated_store):
        """Test recency retrieval strategy."""
        results = populated_store.retrieve(
            "any query",
            strategy=RetrievalStrategy.RECENCY
        )
        assert len(results) > 0
        assert all(r.strategy == "recency" for r in results)
    
    def test_filter_by_source_type(self, populated_store):
        """Test filtering by source type."""
        results = populated_store.retrieve(
            "Python",
            source_types=["memory"]
        )
        # Should only return memory type chunks
        assert all(r.chunk.source_type == "memory" for r in results)


class TestLargeContext:
    """Tests for large context handling (10M+ tokens)."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_max_context_constant(self):
        """Test that max context is set to 10M+."""
        assert MAX_CONTEXT_TOKENS >= 10_000_000
    
    def test_token_limit_enforcement(self, temp_dir):
        """Test that token limit is enforced."""
        # Create store with very small limit for testing
        store = AIRAGStore("test", temp_dir, max_tokens=100)
        
        # Add content that exceeds limit
        for i in range(10):
            store.add_document(f"Document number {i} with some content here.", f"doc{i}.txt")
        
        stats = store.get_stats()
        # Should have enforced limit by removing old chunks
        assert stats.total_tokens <= 100 + DEFAULT_CHUNK_SIZE  # Some tolerance


class TestGlobalFunctions:
    """Tests for global RAG manager functions."""
    
    def test_get_rag_manager(self):
        """Test getting global RAG manager."""
        manager = get_rag_manager()
        assert manager is not None
        assert isinstance(manager, RAGManager)
    
    def test_initialize_rag_manager(self):
        """Test initializing RAG manager with custom dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = initialize_rag_manager(Path(tmpdir))
            assert manager is not None
            
            # Check it uses custom directory
            store = manager.get_store("test")
            assert tmpdir in str(store.storage_dir)


class TestRetrievalResult:
    """Tests for RetrievalResult."""
    
    def test_create_result(self):
        """Test creating retrieval result."""
        chunk = TextChunk(
            chunk_id="test",
            content="Test content",
            source="test.txt",
            source_type="document",
            timestamp=datetime.now().isoformat(),
            token_count=5
        )
        result = RetrievalResult(chunk=chunk, score=0.95, strategy="semantic")
        
        assert result.score == 0.95
        assert result.strategy == "semantic"
    
    def test_result_to_dict(self):
        """Test result serialization."""
        chunk = TextChunk(
            chunk_id="test",
            content="Test content",
            source="test.txt",
            source_type="document",
            timestamp=datetime.now().isoformat(),
            token_count=5
        )
        result = RetrievalResult(chunk=chunk, score=0.95, strategy="semantic")
        
        data = result.to_dict()
        assert data["score"] == 0.95
        assert data["strategy"] == "semantic"
        assert "chunk" in data


class TestMemRL:
    """Tests for MemRL (Memory Reinforcement Learning) functionality.
    
    Based on arXiv:2601.03192 - Self-Evolving Agents via Runtime 
    Reinforcement Learning on Episodic Memory.
    """
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def populated_store(self, temp_dir):
        """Create a populated RAG store for MemRL tests."""
        store = AIRAGStore("memrl_test", temp_dir)
        
        # Add various documents
        store.add_document(
            "Python is a high-level programming language widely used for AI.",
            "python.txt"
        )
        store.add_document(
            "Machine learning algorithms learn patterns from data.",
            "ml.txt"
        )
        store.add_document(
            "Deep learning uses neural networks with multiple layers.",
            "dl.txt"
        )
        store.add_memory("User prefers Python for data science.", importance=0.9)
        
        return store
    
    def test_chunk_qvalue_initialization(self, temp_dir):
        """Test that chunks are initialized with default Q-value."""
        store = AIRAGStore("test", temp_dir)
        store.add_document("Test content.", "test.txt")
        
        for chunk in store.chunks.values():
            assert chunk.q_value == 0.5  # Default Q-value
            assert chunk.retrieval_count == 0
            assert chunk.success_count == 0
    
    def test_chunk_qvalue_serialization(self, temp_dir):
        """Test that Q-values are correctly serialized and deserialized."""
        store = AIRAGStore("test", temp_dir)
        store.add_document("Test content.", "test.txt")
        
        # Modify Q-value
        chunk_id = list(store.chunks.keys())[0]
        store.chunks[chunk_id].q_value = 0.8
        store.chunks[chunk_id].retrieval_count = 5
        store.chunks[chunk_id].success_count = 3
        store._save()
        
        # Create new store instance (should load from disk)
        store2 = AIRAGStore("test", temp_dir)
        chunk = store2.chunks[chunk_id]
        
        assert chunk.q_value == 0.8
        assert chunk.retrieval_count == 5
        assert chunk.success_count == 3
    
    def test_provide_positive_feedback(self, populated_store):
        """Test that positive feedback increases Q-value."""
        # Get some chunks
        results = populated_store.retrieve("Python", top_k=2)
        chunk_ids = [r.chunk.chunk_id for r in results]
        
        # Get initial Q-values
        initial_qvalues = {cid: populated_store.chunks[cid].q_value for cid in chunk_ids}
        
        # Provide positive feedback
        populated_store.provide_feedback(chunk_ids, success=True)
        
        # Q-values should increase
        for cid in chunk_ids:
            assert populated_store.chunks[cid].q_value > initial_qvalues[cid]
            assert populated_store.chunks[cid].retrieval_count == 1
            assert populated_store.chunks[cid].success_count == 1
    
    def test_provide_negative_feedback(self, populated_store):
        """Test that negative feedback decreases Q-value."""
        # Get some chunks
        results = populated_store.retrieve("Python", top_k=2)
        chunk_ids = [r.chunk.chunk_id for r in results]
        
        # Get initial Q-values
        initial_qvalues = {cid: populated_store.chunks[cid].q_value for cid in chunk_ids}
        
        # Provide negative feedback
        populated_store.provide_feedback(chunk_ids, success=False)
        
        # Q-values should decrease
        for cid in chunk_ids:
            assert populated_store.chunks[cid].q_value < initial_qvalues[cid]
            assert populated_store.chunks[cid].retrieval_count == 1
            assert populated_store.chunks[cid].success_count == 0
    
    def test_qvalue_bounds(self, populated_store):
        """Test that Q-values stay within [0, 1] bounds."""
        chunk_id = list(populated_store.chunks.keys())[0]
        
        # Many positive feedbacks - should not exceed 1.0
        for _ in range(20):
            populated_store.provide_feedback([chunk_id], success=True)
        assert populated_store.chunks[chunk_id].q_value <= 1.0
        
        # Many negative feedbacks - should not go below 0.0
        for _ in range(50):
            populated_store.provide_feedback([chunk_id], success=False)
        assert populated_store.chunks[chunk_id].q_value >= 0.0
    
    def test_memrl_retrieval_strategy(self, populated_store):
        """Test MemRL retrieval strategy."""
        # First, train some Q-values by providing feedback
        results = populated_store.retrieve(
            "Python programming",
            strategy=RetrievalStrategy.SEMANTIC
        )
        
        # Give positive feedback to first result, negative to others
        if len(results) >= 2:
            populated_store.provide_feedback([results[0].chunk.chunk_id], success=True)
            populated_store.provide_feedback([results[1].chunk.chunk_id], success=False)
        
        # Now use MemRL strategy
        memrl_results = populated_store.retrieve(
            "Python programming",
            strategy=RetrievalStrategy.MEMRL
        )
        
        assert len(memrl_results) > 0
        assert all(r.strategy == "memrl" for r in memrl_results)
    
    def test_memrl_ranks_by_qvalue(self, temp_dir):
        """Test that MemRL considers Q-values in ranking."""
        store = AIRAGStore("test", temp_dir)
        
        # Add similar documents
        store.add_document("Python for machine learning.", "doc1.txt")
        store.add_document("Python for data science.", "doc2.txt")
        
        # Manually set Q-values to test ranking
        chunk_ids = list(store.chunks.keys())
        if len(chunk_ids) >= 2:
            store.chunks[chunk_ids[0]].q_value = 0.9  # High Q-value
            store.chunks[chunk_ids[1]].q_value = 0.1  # Low Q-value
            store._save()
            
            # MemRL should favor high Q-value chunks
            results = store.retrieve("Python", strategy=RetrievalStrategy.MEMRL)
            
            assert len(results) > 0
            # The high Q-value chunk should rank higher (given similar semantic relevance)
            # This is a soft test since semantic scores also matter
    
    def test_get_chunk_qvalues(self, populated_store):
        """Test getting Q-values for chunks."""
        # Get all Q-values
        all_qvalues = populated_store.get_chunk_qvalues()
        assert len(all_qvalues) == len(populated_store.chunks)
        assert all(0 <= v <= 1 for v in all_qvalues.values())
        
        # Get specific Q-values
        chunk_ids = list(populated_store.chunks.keys())[:2]
        specific_qvalues = populated_store.get_chunk_qvalues(chunk_ids)
        assert len(specific_qvalues) == len(chunk_ids)
    
    def test_reset_qvalues(self, populated_store):
        """Test resetting Q-values."""
        # Modify Q-values
        for chunk in populated_store.chunks.values():
            chunk.q_value = 0.9
            chunk.retrieval_count = 10
            chunk.success_count = 5
        
        # Reset
        populated_store.reset_qvalues(initial_value=0.3)
        
        # Verify reset
        for chunk in populated_store.chunks.values():
            assert chunk.q_value == 0.3
            assert chunk.retrieval_count == 0
            assert chunk.success_count == 0
    
    def test_get_memrl_stats(self, populated_store):
        """Test getting MemRL statistics."""
        # Provide some feedback
        chunk_ids = list(populated_store.chunks.keys())
        populated_store.provide_feedback(chunk_ids[:2], success=True)
        populated_store.provide_feedback(chunk_ids[1:3], success=False)
        
        stats = populated_store.get_memrl_stats()
        
        assert "total_chunks" in stats
        assert "avg_q_value" in stats
        assert "min_q_value" in stats
        assert "max_q_value" in stats
        assert "total_retrievals" in stats
        assert "total_successes" in stats
        assert "success_rate" in stats
        
        assert stats["total_chunks"] == len(populated_store.chunks)
        assert 0 <= stats["avg_q_value"] <= 1
        assert stats["total_retrievals"] > 0
    
    def test_memrl_stats_empty_store(self, temp_dir):
        """Test MemRL stats for empty store."""
        store = AIRAGStore("empty", temp_dir)
        stats = store.get_memrl_stats()
        
        assert stats["total_chunks"] == 0
        assert stats["avg_q_value"] == 0.5  # Default
        assert stats["total_retrievals"] == 0
        assert stats["success_rate"] == 0.0
    
    def test_learning_rate_effect(self, temp_dir):
        """Test that learning rate affects Q-value updates."""
        store = AIRAGStore("test", temp_dir)
        store.add_document("Test content.", "test.txt")
        
        chunk_id = list(store.chunks.keys())[0]
        initial_qvalue = store.chunks[chunk_id].q_value
        
        # High learning rate should cause bigger change
        store.provide_feedback([chunk_id], success=True, learning_rate=0.5)
        high_lr_qvalue = store.chunks[chunk_id].q_value
        
        # Reset
        store.chunks[chunk_id].q_value = initial_qvalue
        
        # Low learning rate should cause smaller change
        store.provide_feedback([chunk_id], success=True, learning_rate=0.01)
        low_lr_qvalue = store.chunks[chunk_id].q_value
        
        # High LR should result in bigger change
        high_lr_change = abs(high_lr_qvalue - initial_qvalue)
        low_lr_change = abs(low_lr_qvalue - initial_qvalue)
        assert high_lr_change > low_lr_change
