"""
RAG (Retrieval Augmented Generation) System for AI Chat Room

This module provides a scalable RAG system with:
- 10M+ token context database support
- Per-AI private vector storage
- Efficient chunking and embedding
- Multiple retrieval strategies
- Persistent storage in Documents folder

Each AI personality gets its own isolated knowledge base that persists
across sessions and grows over time.
"""

import json
import logging
import math
import os
import re
import hashlib
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
import bisect


# Set up logging
logger = logging.getLogger(__name__)


# Constants
MAX_CONTEXT_TOKENS = 10_000_000  # 10M token context database
DEFAULT_CHUNK_SIZE = 512  # tokens per chunk
DEFAULT_CHUNK_OVERLAP = 64  # overlap between chunks
DEFAULT_TOP_K = 10  # default number of results to retrieve
MAX_EMBEDDING_BATCH = 100  # max documents to embed at once


class RetrievalStrategy(Enum):
    """Strategies for retrieving relevant content."""
    SEMANTIC = "semantic"  # Embedding-based similarity
    KEYWORD = "keyword"  # TF-IDF keyword matching
    HYBRID = "hybrid"  # Combination of semantic and keyword
    RECENCY = "recency"  # Prioritize recent additions
    RELEVANCE_DECAY = "relevance_decay"  # Semantic with time decay
    MEMRL = "memrl"  # MemRL: Two-phase retrieval with Q-value ranking (arXiv:2601.03192)


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    chunk_id: str
    content: str
    source: str  # Source document or conversation
    source_type: str  # "document", "conversation", "memory", "knowledge"
    timestamp: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    # MemRL Q-value for utility-based ranking (arXiv:2601.03192)
    q_value: float = 0.5  # Initial Q-value (range 0-1)
    retrieval_count: int = 0  # Number of times this chunk was retrieved
    success_count: int = 0  # Number of successful retrievals (positive feedback)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type,
            "timestamp": self.timestamp,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "q_value": self.q_value,
            "retrieval_count": self.retrieval_count,
            "success_count": self.success_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextChunk":
        return cls(
            chunk_id=data.get("chunk_id", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            source_type=data.get("source_type", "document"),
            timestamp=data.get("timestamp", ""),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            q_value=data.get("q_value", 0.5),
            retrieval_count=data.get("retrieval_count", 0),
            success_count=data.get("success_count", 0)
        )


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""
    chunk: TextChunk
    score: float
    strategy: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "strategy": self.strategy
        }


@dataclass
class RAGStats:
    """Statistics about the RAG database."""
    total_chunks: int = 0
    total_tokens: int = 0
    documents_indexed: int = 0
    conversations_indexed: int = 0
    memories_indexed: int = 0
    last_updated: str = ""
    storage_size_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RAGStats":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in text (rough approximation)."""
    # Rough estimate: ~4 characters per token for English text
    return len(text) // 4


def generate_chunk_id(content: str, source: str) -> str:
    """Generate a unique chunk ID."""
    hash_input = f"{content[:100]}{source}{datetime.now().isoformat()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


class SimpleEmbedding:
    """
    Simple embedding implementation using TF-IDF-like approach.
    
    This provides a lightweight alternative when no external embedding
    model is available. For production, replace with sentence-transformers
    or similar.
    """
    
    def __init__(self, vocab_size: int = 10000):
        self.vocab_size = vocab_size
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_count = 0
        self._fitted = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def _get_term_frequencies(self, tokens: List[str]) -> Dict[str, float]:
        """Calculate term frequencies."""
        tf = defaultdict(int)
        for token in tokens:
            tf[token] += 1
        # Normalize by max frequency
        max_freq = max(tf.values()) if tf else 1
        return {k: v / max_freq for k, v in tf.items()}
    
    def fit(self, documents: List[str]) -> None:
        """Fit the embedding model on documents."""
        # Count document frequencies
        df = defaultdict(int)
        all_tokens = set()
        
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                df[token] += 1
                all_tokens.add(token)
        
        self.doc_count = len(documents)
        
        # Calculate IDF
        for token, freq in df.items():
            self.idf[token] = math.log(self.doc_count / (freq + 1)) + 1
        
        # Build vocabulary (top vocab_size by IDF)
        sorted_tokens = sorted(self.idf.items(), key=lambda x: x[1], reverse=True)
        self.vocab = {token: idx for idx, (token, _) in enumerate(sorted_tokens[:self.vocab_size])}
        
        self._fitted = True
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self._fitted:
            # Auto-fit with single document
            self.fit([text])
        
        tokens = self._tokenize(text)
        tf = self._get_term_frequencies(tokens)
        
        # Create sparse vector
        vector = [0.0] * min(self.vocab_size, len(self.vocab) + 1)
        
        for token, freq in tf.items():
            if token in self.vocab:
                idx = self.vocab[token]
                idf = self.idf.get(token, 1.0)
                vector[idx] = freq * idf
        
        # Normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        # Pad shorter vector
        max_len = max(len(vec1), len(vec2))
        v1 = vec1 + [0.0] * (max_len - len(vec1))
        v2 = vec2 + [0.0] * (max_len - len(vec2))
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class TextChunker:
    """Handles text chunking with various strategies."""
    
    def __init__(
        self, 
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(
        self, 
        text: str, 
        source: str,
        source_type: str = "document",
        metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        """
        Split text into chunks.
        
        Args:
            text: The text to chunk
            source: Source identifier
            source_type: Type of source (document, conversation, etc.)
            metadata: Additional metadata
            
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
        
        chunks = []
        metadata = metadata or {}
        
        # Split into sentences first
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = estimate_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(TextChunk(
                    chunk_id=generate_chunk_id(chunk_text, source),
                    content=chunk_text,
                    source=source,
                    source_type=source_type,
                    timestamp=datetime.now().isoformat(),
                    token_count=current_tokens,
                    metadata=metadata.copy()
                ))
                
                # Start new chunk with overlap
                overlap_tokens = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    s_tokens = estimate_tokens(s)
                    if overlap_tokens + s_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(TextChunk(
                chunk_id=generate_chunk_id(chunk_text, source),
                content=chunk_text,
                source=source,
                source_type=source_type,
                timestamp=datetime.now().isoformat(),
                token_count=current_tokens,
                metadata=metadata.copy()
            ))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class KeywordIndex:
    """Inverted index for keyword search."""
    
    def __init__(self):
        self.index: Dict[str, Set[str]] = defaultdict(set)  # term -> chunk_ids
        self.chunk_terms: Dict[str, Set[str]] = {}  # chunk_id -> terms
    
    def add(self, chunk_id: str, text: str) -> None:
        """Add a chunk to the index."""
        terms = self._extract_terms(text)
        self.chunk_terms[chunk_id] = terms
        for term in terms:
            self.index[term].add(chunk_id)
    
    def remove(self, chunk_id: str) -> None:
        """Remove a chunk from the index."""
        if chunk_id in self.chunk_terms:
            for term in self.chunk_terms[chunk_id]:
                self.index[term].discard(chunk_id)
            del self.chunk_terms[chunk_id]
    
    def search(self, query: str, limit: int = 100) -> List[Tuple[str, float]]:
        """
        Search for chunks matching query terms.
        
        Returns list of (chunk_id, score) tuples.
        """
        query_terms = self._extract_terms(query)
        if not query_terms:
            return []
        
        # If no chunks exist, return empty
        if not self.chunk_terms:
            return []
        
        # Score chunks by term overlap
        scores: Dict[str, float] = defaultdict(float)
        
        for term in query_terms:
            if term in self.index and self.index[term]:
                # IDF-like weighting (avoid log(0) by ensuring denominator > 0)
                doc_freq = len(self.index[term])
                total_docs = max(len(self.chunk_terms), 1)
                idf = math.log(total_docs / (doc_freq + 1) + 1)
                for chunk_id in self.index[term]:
                    if chunk_id in self.chunk_terms:  # Only score existing chunks
                        scores[chunk_id] += idf
        
        # Normalize by query length
        for chunk_id in scores:
            scores[chunk_id] /= len(query_terms)
        
        # Sort by score
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _extract_terms(self, text: str) -> Set[str]:
        """Extract terms from text."""
        text = text.lower()
        terms = set(re.findall(r'\b\w{2,}\b', text))
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'can', 'to', 'of',
                      'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                      'through', 'during', 'before', 'after', 'above', 'below',
                      'between', 'under', 'again', 'further', 'then', 'once', 'and',
                      'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither',
                      'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just'}
        return terms - stop_words
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": {k: list(v) for k, v in self.index.items()},
            "chunk_terms": {k: list(v) for k, v in self.chunk_terms.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeywordIndex":
        idx = cls()
        idx.index = defaultdict(set, {k: set(v) for k, v in data.get("index", {}).items()})
        idx.chunk_terms = {k: set(v) for k, v in data.get("chunk_terms", {}).items()}
        return idx


class AIRAGStore:
    """
    RAG (Retrieval Augmented Generation) store for a single AI personality.
    
    Each AI has its own private RAG store that contains:
    - Indexed documents
    - Conversation history
    - Learned memories and knowledge
    
    Supports 10M+ tokens of context.
    """
    
    def __init__(
        self, 
        ai_id: str, 
        storage_dir: Path,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        """
        Initialize RAG store for an AI.
        
        Args:
            ai_id: Unique AI identifier
            storage_dir: Directory for persistent storage
            max_tokens: Maximum tokens to store (default 10M)
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.ai_id = ai_id
        self.storage_dir = storage_dir / "rag" / ai_id
        self.max_tokens = max_tokens
        
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        self.embedding_model = SimpleEmbedding()
        self.keyword_index = KeywordIndex()
        
        self.chunks: Dict[str, TextChunk] = {}
        self.stats = RAGStats()
        
        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()

        # Load existing data
        self._load()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        db_path = self.storage_dir / "rag.db"
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Create chunks table
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT,
                    source_type TEXT,
                    timestamp TEXT,
                    token_count INTEGER,
                    metadata TEXT,
                    embedding TEXT,
                    q_value REAL DEFAULT 0.5,
                    retrieval_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0
                )
            """)

    def _get_chunks_file(self) -> Path:
        return self.storage_dir / "chunks.json"
    
    def _get_index_file(self) -> Path:
        return self.storage_dir / "keyword_index.json"
    
    def _get_stats_file(self) -> Path:
        return self.storage_dir / "stats.json"
    
    def _get_vocab_file(self) -> Path:
        return self.storage_dir / "vocab.json"
    
    def _load_chunks_from_db(self) -> None:
        """Load chunks from SQLite database."""
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM chunks")
                for row in cursor:
                    try:
                        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                        embedding = json.loads(row["embedding"]) if row["embedding"] else None

                        chunk = TextChunk(
                            chunk_id=row["chunk_id"],
                            content=row["content"],
                            source=row["source"],
                            source_type=row["source_type"],
                            timestamp=row["timestamp"],
                            token_count=row["token_count"],
                            metadata=metadata,
                            embedding=embedding,
                            q_value=row["q_value"],
                            retrieval_count=row["retrieval_count"],
                            success_count=row["success_count"]
                        )
                        self.chunks[chunk.chunk_id] = chunk
                    except Exception as e:
                        logger.error(f"Error loading chunk {row['chunk_id']}: {e}")
        except sqlite3.Error as e:
            logger.error(f"Database error loading chunks: {e}")

    def _load(self) -> None:
        """Load data from disk."""
        # Try loading from DB first
        self._load_chunks_from_db()

        # If DB is empty, check for legacy JSON file
        if not self.chunks:
            chunks_file = self._get_chunks_file()
            if chunks_file.exists():
                try:
                    with open(chunks_file, 'r') as f:
                        data = json.load(f)

                    # Load into memory
                    self.chunks = {
                        chunk_id: TextChunk.from_dict(chunk_data)
                        for chunk_id, chunk_data in data.items()
                    }

                    # Migrate to DB
                    logger.info(f"Migrating {len(self.chunks)} chunks from JSON to SQLite for {self.ai_id}")
                    with self.conn:
                        for chunk in self.chunks.values():
                            self.conn.execute("""
                                INSERT OR REPLACE INTO chunks (
                                    chunk_id, content, source, source_type, timestamp,
                                    token_count, metadata, embedding, q_value,
                                    retrieval_count, success_count
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                chunk.chunk_id,
                                chunk.content,
                                chunk.source,
                                chunk.source_type,
                                chunk.timestamp,
                                chunk.token_count,
                                json.dumps(chunk.metadata),
                                json.dumps(chunk.embedding) if chunk.embedding else None,
                                chunk.q_value,
                                chunk.retrieval_count,
                                chunk.success_count
                            ))

                    # Backup legacy file
                    chunks_file.rename(chunks_file.with_suffix(".json.bak"))

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not load chunks for {self.ai_id}: {e}")
        
        # Load keyword index
        index_file = self._get_index_file()
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                self.keyword_index = KeywordIndex.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load keyword index for {self.ai_id}: {e}")
        
        # Load stats
        stats_file = self._get_stats_file()
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                self.stats = RAGStats.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load stats for {self.ai_id}: {e}")
        
        # Load vocabulary
        vocab_file = self._get_vocab_file()
        if vocab_file.exists():
            try:
                with open(vocab_file, 'r') as f:
                    data = json.load(f)
                self.embedding_model.vocab = data.get("vocab", {})
                self.embedding_model.idf = data.get("idf", {})
                self.embedding_model.doc_count = data.get("doc_count", 0)
                self.embedding_model._fitted = data.get("fitted", False)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load vocab for {self.ai_id}: {e}")
        
        # Recalculate stats
        self._update_stats()
    
    def _save(self) -> None:
        """Save data to disk."""
        # Note: Chunks are now saved to SQLite incrementally.
        
        # Save keyword index
        with open(self._get_index_file(), 'w') as f:
            json.dump(self.keyword_index.to_dict(), f)
        
        # Save stats
        with open(self._get_stats_file(), 'w') as f:
            json.dump(self.stats.to_dict(), f)
        
        # Save vocabulary
        vocab_data = {
            "vocab": self.embedding_model.vocab,
            "idf": self.embedding_model.idf,
            "doc_count": self.embedding_model.doc_count,
            "fitted": self.embedding_model._fitted
        }
        with open(self._get_vocab_file(), 'w') as f:
            json.dump(vocab_data, f)
    
    def _update_stats(self) -> None:
        """Update statistics."""
        self.stats.total_chunks = len(self.chunks)
        self.stats.total_tokens = sum(c.token_count for c in self.chunks.values())
        self.stats.documents_indexed = len(set(
            c.source for c in self.chunks.values() if c.source_type == "document"
        ))
        self.stats.conversations_indexed = len(set(
            c.source for c in self.chunks.values() if c.source_type == "conversation"
        ))
        self.stats.memories_indexed = len([
            c for c in self.chunks.values() if c.source_type == "memory"
        ])
        self.stats.last_updated = datetime.now().isoformat()
        
        # Estimate storage size
        chunks_file = self._get_chunks_file()
        if chunks_file.exists():
            self.stats.storage_size_bytes = chunks_file.stat().st_size
    
    def _enforce_token_limit(self) -> None:
        """Remove oldest chunks if over token limit."""
        if self.stats.total_tokens <= self.max_tokens:
            return
        
        # Sort chunks by timestamp (oldest first)
        sorted_chunks = sorted(
            self.chunks.values(),
            key=lambda c: c.timestamp
        )
        
        # Remove oldest until under limit
        while self.stats.total_tokens > self.max_tokens and sorted_chunks:
            oldest = sorted_chunks.pop(0)
            self.remove_chunk(oldest.chunk_id)
    
    def add_document(
        self, 
        content: str, 
        source: str,
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """
        Add a document to the RAG store.
        
        Args:
            content: Document content
            source: Source identifier (e.g., filename)
            metadata: Additional metadata
            
        Returns:
            List of chunk IDs created
        """
        chunks = self.chunker.chunk_text(
            content, source, "document", metadata
        )
        
        chunk_ids = []
        for chunk in chunks:
            self._add_chunk(chunk)
            chunk_ids.append(chunk.chunk_id)
        
        self._update_embedding_model()
        self._save()
        
        logger.info(f"Added document '{source}' with {len(chunk_ids)} chunks to {self.ai_id}'s RAG")
        
        return chunk_ids
    
    def add_conversation(
        self, 
        messages: List[Dict[str, str]], 
        conversation_id: str,
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """
        Add a conversation to the RAG store.
        
        Args:
            messages: List of {"role": ..., "content": ...} messages
            conversation_id: Unique conversation identifier
            metadata: Additional metadata
            
        Returns:
            List of chunk IDs created
        """
        # Format conversation as text
        conv_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        chunks = self.chunker.chunk_text(
            conv_text, conversation_id, "conversation", metadata
        )
        
        chunk_ids = []
        for chunk in chunks:
            self._add_chunk(chunk)
            chunk_ids.append(chunk.chunk_id)
        
        self._update_embedding_model()
        self._save()
        
        return chunk_ids
    
    def add_memory(
        self, 
        memory: str, 
        source: str = "self",
        importance: float = 0.5,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Add a memory/learned fact to the RAG store.
        
        Args:
            memory: The memory content
            source: Source of the memory
            importance: Importance score (0-1)
            metadata: Additional metadata
            
        Returns:
            Chunk ID of the memory
        """
        metadata = metadata or {}
        metadata["importance"] = importance
        
        chunk = TextChunk(
            chunk_id=generate_chunk_id(memory, source),
            content=memory,
            source=source,
            source_type="memory",
            timestamp=datetime.now().isoformat(),
            token_count=estimate_tokens(memory),
            metadata=metadata
        )
        
        self._add_chunk(chunk)
        self._update_embedding_model()
        self._save()
        
        return chunk.chunk_id
    
    def add_knowledge(
        self, 
        fact: str, 
        category: str = "general",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Add a knowledge fact to the RAG store.
        
        Args:
            fact: The knowledge fact
            category: Category of knowledge
            metadata: Additional metadata
            
        Returns:
            Chunk ID of the knowledge
        """
        metadata = metadata or {}
        metadata["category"] = category
        
        chunk = TextChunk(
            chunk_id=generate_chunk_id(fact, category),
            content=fact,
            source=category,
            source_type="knowledge",
            timestamp=datetime.now().isoformat(),
            token_count=estimate_tokens(fact),
            metadata=metadata
        )
        
        self._add_chunk(chunk)
        self._update_embedding_model()
        self._save()
        
        return chunk.chunk_id
    
    def _add_chunk(self, chunk: TextChunk) -> None:
        """Add a chunk to the store."""
        # Generate embedding
        chunk.embedding = self.embedding_model.embed(chunk.content)
        
        # Add to storage
        self.chunks[chunk.chunk_id] = chunk
        
        # Add to SQLite
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO chunks (
                        chunk_id, content, source, source_type, timestamp,
                        token_count, metadata, embedding, q_value,
                        retrieval_count, success_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.chunk_id,
                    chunk.content,
                    chunk.source,
                    chunk.source_type,
                    chunk.timestamp,
                    chunk.token_count,
                    json.dumps(chunk.metadata),
                    json.dumps(chunk.embedding) if chunk.embedding else None,
                    chunk.q_value,
                    chunk.retrieval_count,
                    chunk.success_count
                ))
        except sqlite3.Error as e:
            logger.error(f"Error saving chunk {chunk.chunk_id} to DB: {e}")

        # Add to keyword index
        self.keyword_index.add(chunk.chunk_id, chunk.content)
        
        # Update stats
        self._update_stats()
        
        # Enforce token limit
        self._enforce_token_limit()
    
    def remove_chunk(self, chunk_id: str) -> bool:
        """Remove a chunk from the store."""
        if chunk_id not in self.chunks:
            return False
        
        del self.chunks[chunk_id]

        # Remove from SQLite
        try:
            with self.conn:
                self.conn.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        except sqlite3.Error as e:
            logger.error(f"Error removing chunk {chunk_id} from DB: {e}")

        self.keyword_index.remove(chunk_id)
        self._update_stats()
        
        return True
    
    def remove_document(self, source: str) -> int:
        """Remove all chunks from a document."""
        chunk_ids = [
            c.chunk_id for c in self.chunks.values()
            if c.source == source and c.source_type == "document"
        ]
        
        for chunk_id in chunk_ids:
            self.remove_chunk(chunk_id)
        
        self._save()
        return len(chunk_ids)
    
    def _update_embedding_model(self) -> None:
        """Update the embedding model with current chunks."""
        if len(self.chunks) > 10:  # Only refit if we have enough data
            texts = [c.content for c in self.chunks.values()]
            self.embedding_model.fit(texts)
            
            # Re-embed all chunks with updated model
            for chunk in self.chunks.values():
                chunk.embedding = self.embedding_model.embed(chunk.content)
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = DEFAULT_TOP_K,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        source_types: List[str] = None,
        time_decay: float = 0.0,
        memrl_q_weight: float = 0.4,
        memrl_candidate_multiplier: int = 3
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: The search query
            top_k: Number of results to return
            strategy: Retrieval strategy to use
            source_types: Filter by source types (document, conversation, memory, knowledge)
            time_decay: Time decay factor (0 = no decay, 1 = strong decay)
            memrl_q_weight: Weight for Q-value in MemRL scoring (0-1). Higher = more weight on Q-value.
            memrl_candidate_multiplier: Multiplier for candidate pool size in MemRL two-phase retrieval
            time_decay: Time decay factor (0 = no decay, 1 = strong decay)
            
        Returns:
            List of RetrievalResult objects
        """
        if not self.chunks:
            return []
        
        # Filter chunks by source type if specified
        candidate_chunks = list(self.chunks.values())
        if source_types:
            candidate_chunks = [c for c in candidate_chunks if c.source_type in source_types]
        
        if not candidate_chunks:
            return []
        
        results = []
        
        if strategy == RetrievalStrategy.SEMANTIC:
            results = self._semantic_search(query, candidate_chunks, top_k)
        
        elif strategy == RetrievalStrategy.KEYWORD:
            results = self._keyword_search(query, candidate_chunks, top_k)
        
        elif strategy == RetrievalStrategy.HYBRID:
            # Combine semantic and keyword search
            semantic_results = self._semantic_search(query, candidate_chunks, top_k * 2)
            keyword_results = self._keyword_search(query, candidate_chunks, top_k * 2)
            
            # Merge and deduplicate
            seen = set()
            combined = []
            
            for result in semantic_results + keyword_results:
                if result.chunk.chunk_id not in seen:
                    seen.add(result.chunk.chunk_id)
                    combined.append(result)
            
            # Re-sort by score
            combined.sort(key=lambda x: x.score, reverse=True)
            results = combined[:top_k]
        
        elif strategy == RetrievalStrategy.RECENCY:
            # Sort by timestamp, most recent first
            sorted_chunks = sorted(
                candidate_chunks,
                key=lambda c: c.timestamp,
                reverse=True
            )
            results = [
                RetrievalResult(chunk=c, score=1.0 - i/len(sorted_chunks), strategy="recency")
                for i, c in enumerate(sorted_chunks[:top_k])
            ]
        
        elif strategy == RetrievalStrategy.RELEVANCE_DECAY:
            # Semantic search with time decay
            semantic_results = self._semantic_search(query, candidate_chunks, top_k * 2)
            
            # Apply time decay
            now = datetime.now()
            for result in semantic_results:
                try:
                    chunk_time = datetime.fromisoformat(result.chunk.timestamp)
                    age_days = (now - chunk_time).days
                    decay = math.exp(-time_decay * age_days / 30)  # Decay over ~30 days
                    result.score *= decay
                except (ValueError, TypeError):
                    pass
            
            # Re-sort
            semantic_results.sort(key=lambda x: x.score, reverse=True)
            results = semantic_results[:top_k]
        
        elif strategy == RetrievalStrategy.MEMRL:
            # MemRL: Two-phase retrieval with Q-value ranking (arXiv:2601.03192)
            # Phase 1: Filter by semantic relevance (get more candidates than needed)
            semantic_results = self._semantic_search(
                query, candidate_chunks, top_k * memrl_candidate_multiplier
            )
            
            # Phase 2: Re-rank by Q-value (learned utility)
            # Combined score = semantic_score * (1 - q_weight) + q_value * q_weight
            semantic_weight = 1.0 - memrl_q_weight
            
            for result in semantic_results:
                q_value = result.chunk.q_value
                semantic_score = result.score
                # Combine semantic relevance with learned Q-value
                result.score = (semantic_score * semantic_weight) + (q_value * memrl_q_weight)
            
            # Re-sort by combined score
            semantic_results.sort(key=lambda x: x.score, reverse=True)
            results = [
                RetrievalResult(chunk=r.chunk, score=r.score, strategy="memrl")
                for r in semantic_results[:top_k]
            ]
        
        return results
    
    def _semantic_search(
        self, 
        query: str, 
        chunks: List[TextChunk], 
        top_k: int
    ) -> List[RetrievalResult]:
        """Perform semantic search using embeddings."""
        query_embedding = self.embedding_model.embed(query)
        
        results = []
        for chunk in chunks:
            if chunk.embedding:
                score = SimpleEmbedding.cosine_similarity(query_embedding, chunk.embedding)
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    strategy="semantic"
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _keyword_search(
        self, 
        query: str, 
        chunks: List[TextChunk], 
        top_k: int
    ) -> List[RetrievalResult]:
        """Perform keyword search using inverted index."""
        chunk_ids = {c.chunk_id for c in chunks}
        keyword_results = self.keyword_index.search(query, limit=top_k * 2)
        
        results = []
        for chunk_id, score in keyword_results:
            if chunk_id in chunk_ids and chunk_id in self.chunks:
                results.append(RetrievalResult(
                    chunk=self.chunks[chunk_id],
                    score=score,
                    strategy="keyword"
                ))
        
        return results[:top_k]
    
    def get_context(
        self, 
        query: str, 
        max_tokens: int = 2000,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    ) -> str:
        """
        Get context for a query, suitable for including in LLM prompts.
        
        Args:
            query: The query to get context for
            max_tokens: Maximum tokens in the context
            strategy: Retrieval strategy
            
        Returns:
            Formatted context string
        """
        results = self.retrieve(query, top_k=20, strategy=strategy)
        
        context_parts = []
        total_tokens = 0
        
        for result in results:
            chunk_tokens = result.chunk.token_count
            if total_tokens + chunk_tokens > max_tokens:
                break
            
            context_parts.append(f"[{result.chunk.source_type}:{result.chunk.source}]\n{result.chunk.content}")
            total_tokens += chunk_tokens
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_stats(self) -> RAGStats:
        """Get statistics about the RAG store."""
        self._update_stats()
        return self.stats
    
    def clear(self) -> None:
        """Clear all data from the RAG store."""
        self.chunks.clear()

        # Clear SQLite
        try:
            with self.conn:
                self.conn.execute("DELETE FROM chunks")
        except sqlite3.Error as e:
            logger.error(f"Error clearing chunks from DB: {e}")

        self.keyword_index = KeywordIndex()
        self.embedding_model = SimpleEmbedding()
        self.stats = RAGStats()
        self._save()
    
    def export_data(self) -> Dict[str, Any]:
        """Export all RAG data for backup."""
        return {
            "ai_id": self.ai_id,
            "chunks": {k: v.to_dict() for k, v in self.chunks.items()},
            "stats": self.stats.to_dict(),
            "exported_at": datetime.now().isoformat()
        }
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import RAG data from backup."""
        try:
            for chunk_id, chunk_data in data.get("chunks", {}).items():
                chunk = TextChunk.from_dict(chunk_data)
                self.chunks[chunk_id] = chunk
                self.keyword_index.add(chunk_id, chunk.content)
            
            self._update_embedding_model()
            self._save()
            return True
        except Exception as e:
            logger.error(f"Error importing RAG data: {e}")
            return False
    
    # MemRL: Q-value update methods (arXiv:2601.03192)
    
    def provide_feedback(
        self, 
        chunk_ids: List[str], 
        success: bool,
        learning_rate: float = 0.1
    ) -> None:
        """
        Provide feedback on retrieved chunks to update Q-values.
        
        This implements the runtime reinforcement learning aspect of MemRL,
        where Q-values are updated based on whether the retrieval was helpful.
        
        Args:
            chunk_ids: List of chunk IDs that were retrieved
            success: Whether the retrieval led to a successful outcome
            learning_rate: Learning rate for Q-value updates (0-1)
        """
        updated_chunks = []
        for chunk_id in chunk_ids:
            if chunk_id in self.chunks:
                chunk = self.chunks[chunk_id]
                chunk.retrieval_count += 1
                
                if success:
                    chunk.success_count += 1
                
                # Update Q-value using temporal difference-like update
                # Q(s,a) = Q(s,a) + α * (reward - Q(s,a))
                reward = 1.0 if success else 0.0
                chunk.q_value = chunk.q_value + learning_rate * (reward - chunk.q_value)
                
                # Clamp Q-value to [0, 1]
                chunk.q_value = max(0.0, min(1.0, chunk.q_value))

                updated_chunks.append(chunk)

        # Update SQLite
        if updated_chunks:
            try:
                with self.conn:
                    for chunk in updated_chunks:
                        self.conn.execute("""
                            UPDATE chunks
                            SET q_value = ?, retrieval_count = ?, success_count = ?
                            WHERE chunk_id = ?
                        """, (chunk.q_value, chunk.retrieval_count, chunk.success_count, chunk.chunk_id))
            except sqlite3.Error as e:
                logger.error(f"Error updating chunk stats in DB: {e}")
        
        self._save()
    
    def get_chunk_qvalues(self, chunk_ids: List[str] = None) -> Dict[str, float]:
        """
        Get Q-values for chunks.
        
        Args:
            chunk_ids: Optional list of specific chunk IDs. If None, returns all.
            
        Returns:
            Dict mapping chunk_id to Q-value
        """
        if chunk_ids is None:
            return {cid: chunk.q_value for cid, chunk in self.chunks.items()}
        return {
            cid: self.chunks[cid].q_value 
            for cid in chunk_ids 
            if cid in self.chunks
        }
    
    def reset_qvalues(self, initial_value: float = 0.5) -> None:
        """
        Reset all Q-values to initial value.
        
        Args:
            initial_value: The value to reset Q-values to (default 0.5)
        """
        for chunk in self.chunks.values():
            chunk.q_value = initial_value
            chunk.retrieval_count = 0
            chunk.success_count = 0

        # Update SQLite
        try:
            with self.conn:
                self.conn.execute("""
                    UPDATE chunks
                    SET q_value = ?, retrieval_count = 0, success_count = 0
                """, (initial_value,))
        except sqlite3.Error as e:
            logger.error(f"Error resetting q-values in DB: {e}")

        self._save()
    
    def get_memrl_stats(self) -> Dict[str, Any]:
        """
        Get MemRL-specific statistics.
        
        Returns:
            Dict with MemRL statistics including Q-value distribution
        """
        if not self.chunks:
            return {
                "total_chunks": 0,
                "avg_q_value": 0.5,
                "min_q_value": 0.5,
                "max_q_value": 0.5,
                "total_retrievals": 0,
                "total_successes": 0,
                "success_rate": 0.0
            }
        
        q_values = [c.q_value for c in self.chunks.values()]
        total_retrievals = sum(c.retrieval_count for c in self.chunks.values())
        total_successes = sum(c.success_count for c in self.chunks.values())
        
        return {
            "total_chunks": len(self.chunks),
            "avg_q_value": sum(q_values) / len(q_values),
            "min_q_value": min(q_values),
            "max_q_value": max(q_values),
            "total_retrievals": total_retrievals,
            "total_successes": total_successes,
            "success_rate": total_successes / total_retrievals if total_retrievals > 0 else 0.0
        }


class RAGManager:
    """
    Manages RAG stores for all AI personalities.
    
    Provides a central interface for creating, accessing, and managing
    per-AI RAG stores with 10M+ token context support.
    """
    
    def __init__(self, storage_dir: Path = None):
        """
        Initialize RAG manager.
        
        Args:
            storage_dir: Base storage directory (defaults to Documents/AIChat)
        """
        from ai_state import get_documents_folder
        self.storage_dir = storage_dir or get_documents_folder()
        self._stores: Dict[str, AIRAGStore] = {}
        
        # Ensure storage directory exists
        (self.storage_dir / "rag").mkdir(parents=True, exist_ok=True)
        
        # Load existing stores
        self._discover_stores()
    
    def _discover_stores(self) -> None:
        """Discover existing RAG stores."""
        rag_dir = self.storage_dir / "rag"
        if rag_dir.exists():
            for ai_dir in rag_dir.iterdir():
                if ai_dir.is_dir():
                    ai_id = ai_dir.name
                    self._stores[ai_id] = AIRAGStore(ai_id, self.storage_dir)
    
    def get_store(self, ai_id: str) -> AIRAGStore:
        """
        Get or create a RAG store for an AI.
        
        Args:
            ai_id: The AI identifier
            
        Returns:
            The AIRAGStore for this AI
        """
        if ai_id not in self._stores:
            self._stores[ai_id] = AIRAGStore(ai_id, self.storage_dir)
        return self._stores[ai_id]
    
    def delete_store(self, ai_id: str) -> bool:
        """
        Delete an AI's RAG store.
        
        Args:
            ai_id: The AI identifier
            
        Returns:
            True if deleted
        """
        if ai_id in self._stores:
            store = self._stores[ai_id]
            store.clear()
            
            # Remove directory
            import shutil
            store_dir = self.storage_dir / "rag" / ai_id
            if store_dir.exists():
                shutil.rmtree(store_dir)
            
            del self._stores[ai_id]
            return True
        return False
    
    def list_stores(self) -> List[str]:
        """List all AI IDs with RAG stores."""
        return list(self._stores.keys())
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics across all stores."""
        total_chunks = 0
        total_tokens = 0
        total_documents = 0
        total_conversations = 0
        total_memories = 0
        
        for store in self._stores.values():
            stats = store.get_stats()
            total_chunks += stats.total_chunks
            total_tokens += stats.total_tokens
            total_documents += stats.documents_indexed
            total_conversations += stats.conversations_indexed
            total_memories += stats.memories_indexed
        
        return {
            "total_stores": len(self._stores),
            "total_chunks": total_chunks,
            "total_tokens": total_tokens,
            "total_documents": total_documents,
            "total_conversations": total_conversations,
            "total_memories": total_memories,
            "max_tokens_supported": MAX_CONTEXT_TOKENS
        }
    
    def add_document_to_all(
        self, 
        content: str, 
        source: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, List[str]]:
        """
        Add a document to all AI RAG stores (shared knowledge).
        
        Args:
            content: Document content
            source: Source identifier
            metadata: Additional metadata
            
        Returns:
            Dict mapping ai_id to list of chunk_ids
        """
        results = {}
        for ai_id, store in self._stores.items():
            chunk_ids = store.add_document(content, source, metadata)
            results[ai_id] = chunk_ids
        return results
    
    def query_all(
        self, 
        query: str, 
        top_k: int = 5
    ) -> Dict[str, List[RetrievalResult]]:
        """
        Query all AI RAG stores.
        
        Args:
            query: Search query
            top_k: Results per store
            
        Returns:
            Dict mapping ai_id to retrieval results
        """
        results = {}
        for ai_id, store in self._stores.items():
            results[ai_id] = store.retrieve(query, top_k)
        return results


# Global RAG manager instance
_rag_manager: Optional[RAGManager] = None


def get_rag_manager() -> RAGManager:
    """Get the global RAG manager instance."""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager()
    return _rag_manager


def initialize_rag_manager(storage_dir: Path = None) -> RAGManager:
    """Initialize or reinitialize the RAG manager."""
    global _rag_manager
    _rag_manager = RAGManager(storage_dir)
    return _rag_manager
