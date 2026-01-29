"""
Local Storage Manager - Comprehensive Local Data Persistence

This module ensures ALL data is stored locally on the device, including:
- Chat histories (group and private)
- AI memories and emotions
- Relationships and interactions
- Remote session data (when connected to P2P host)
- RAG knowledge bases
- Document uploads
- Settings and preferences

Data is stored in the public Documents folder for accessibility and backup.
When in a remote P2P session, data is stored BOTH on the host AND locally.
"""

import json
import logging
import os
import shutil
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
import hashlib
import uuid
import threading


# Set up logging
logger = logging.getLogger(__name__)


def safe_json_loads(data: Optional[str], default: Any = None) -> Any:
    """Safely load JSON data, returning default on error."""
    if not data:
        return default
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default


# Storage locations
def get_base_storage_dir() -> Path:
    """Get the base storage directory (Documents/AIChat)."""
    # Check for Android
    if os.environ.get("ANDROID_STORAGE"):
        return Path("/storage/emulated/0/Documents/AIChat")
    
    # Check for common locations
    home = Path.home()
    
    # Windows/Mac/Linux Documents folder
    if (home / "Documents").exists():
        return home / "Documents" / "AIChat"
    
    # Fallback to home directory
    return home / ".aichat"


class StorageType(Enum):
    """Types of stored data."""
    CHAT_HISTORY = "chat_history"
    PRIVATE_CHAT = "private_chat"
    AI_STATE = "ai_state"
    AI_MEMORY = "ai_memory"
    RELATIONSHIP = "relationship"
    RAG_DATA = "rag_data"
    DOCUMENT = "document"
    REMOTE_SESSION = "remote_session"
    SETTINGS = "settings"


class SessionType(Enum):
    """Types of chat sessions."""
    LOCAL = "local"  # Running locally
    REMOTE_HOST = "remote_host"  # Hosting for others
    REMOTE_CLIENT = "remote_client"  # Connected to remote host


@dataclass
class InteractionRecord:
    """Records a single interaction for storage."""
    interaction_id: str
    timestamp: str
    session_id: str
    session_type: str  # "local", "remote_host", "remote_client"
    
    # Participants
    sender_id: str
    sender_name: str
    sender_type: str  # "user", "ai", "remote_user"
    
    # Content
    content: str
    content_type: str  # "message", "ai_response", "tool_result", "system"
    
    # Context
    ai_id: Optional[str] = None
    is_private: bool = False
    private_with: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    # Remote session info
    remote_host_id: Optional[str] = None
    remote_room_code: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "session_type": self.session_type,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "sender_type": self.sender_type,
            "content": self.content,
            "content_type": self.content_type,
            "ai_id": self.ai_id,
            "is_private": self.is_private,
            "private_with": self.private_with,
            "tool_calls": self.tool_calls,
            "remote_host_id": self.remote_host_id,
            "remote_room_code": self.remote_room_code,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractionRecord":
        return cls(
            interaction_id=data.get("interaction_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            session_id=data.get("session_id", ""),
            session_type=data.get("session_type", "local"),
            sender_id=data.get("sender_id", ""),
            sender_name=data.get("sender_name", ""),
            sender_type=data.get("sender_type", "user"),
            content=data.get("content", ""),
            content_type=data.get("content_type", "message"),
            ai_id=data.get("ai_id"),
            is_private=data.get("is_private", False),
            private_with=data.get("private_with"),
            tool_calls=data.get("tool_calls"),
            remote_host_id=data.get("remote_host_id"),
            remote_room_code=data.get("remote_room_code"),
            metadata=data.get("metadata", {})
        )


@dataclass
class RemoteSessionRecord:
    """Records details about a remote P2P session."""
    session_id: str
    session_type: str  # "host" or "client"
    
    # Connection info
    room_code: str
    host_id: str
    host_address: Optional[str] = None
    
    # Timing
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    
    # Participants
    participants: List[Dict[str, Any]] = field(default_factory=list)
    ai_personalities: List[str] = field(default_factory=list)
    
    # Statistics
    messages_sent: int = 0
    messages_received: int = 0
    ai_requests: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteSessionRecord":
        return cls(
            session_id=data.get("session_id", ""),
            session_type=data.get("session_type", "client"),
            room_code=data.get("room_code", ""),
            host_id=data.get("host_id", ""),
            host_address=data.get("host_address"),
            started_at=data.get("started_at", datetime.now().isoformat()),
            ended_at=data.get("ended_at"),
            participants=data.get("participants", []),
            ai_personalities=data.get("ai_personalities", []),
            messages_sent=data.get("messages_sent", 0),
            messages_received=data.get("messages_received", 0),
            ai_requests=data.get("ai_requests", 0),
            metadata=data.get("metadata", {})
        )


class LocalStorageManager:
    """
    Comprehensive local storage manager.
    
    Stores ALL data locally regardless of whether the session is local
    or remote. When connected to a remote host, data is stored on BOTH
    devices.
    """
    
    def __init__(self, storage_dir: Path = None):
        """
        Initialize the local storage manager.
        
        Args:
            storage_dir: Base directory for storage (defaults to Documents/AIChat)
        """
        self.storage_dir = storage_dir or get_base_storage_dir()
        self._ensure_directories()
        self._lock = threading.RLock()
        
        # Current session
        self._session_id = str(uuid.uuid4())
        self._session_type = SessionType.LOCAL
        self._remote_session: Optional[RemoteSessionRecord] = None
        
        # Database connection
        self._conn: Optional[sqlite3.Connection] = None

        # Initialize database
        self._init_database()
    
    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get the persistent database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._get_db_path()), check_same_thread=False)
        return self._conn

    def _ensure_directories(self) -> None:
        """Ensure all storage directories exist."""
        directories = [
            self.storage_dir,
            self.storage_dir / "interactions",
            self.storage_dir / "ai_states",
            self.storage_dir / "private_chats",
            self.storage_dir / "remote_sessions",
            self.storage_dir / "documents",
            self.storage_dir / "rag",
            self.storage_dir / "backups",
            self.storage_dir / "exports",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_db_path(self) -> Path:
        """Get the SQLite database path."""
        return self.storage_dir / "local_storage.db"
    
    def _init_database(self) -> None:
        """Initialize the SQLite database for efficient queries."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()

                # Interactions table - stores all chat interactions
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    interaction_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    session_type TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    sender_name TEXT NOT NULL,
                    sender_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    ai_id TEXT,
                    is_private INTEGER DEFAULT 0,
                    private_with TEXT,
                    tool_calls TEXT,
                    remote_host_id TEXT,
                    remote_room_code TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_session 
                ON interactions(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_timestamp 
                ON interactions(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_ai_id 
                ON interactions(ai_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_private 
                ON interactions(is_private, private_with)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_remote 
                ON interactions(remote_host_id, remote_room_code)
            """)
            
            # Remote sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS remote_sessions (
                    session_id TEXT PRIMARY KEY,
                    session_type TEXT NOT NULL,
                    room_code TEXT NOT NULL,
                    host_id TEXT NOT NULL,
                    host_address TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    participants TEXT,
                    ai_personalities TEXT,
                    messages_sent INTEGER DEFAULT 0,
                    messages_received INTEGER DEFAULT 0,
                    ai_requests INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            # AI memories table - for searchable AI memories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_memories (
                    memory_id TEXT PRIMARY KEY,
                    ai_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    timestamp TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_memories_ai_id 
                ON ai_memories(ai_id)
            """)
            
            # Relationships table - tracks AI-participant relationships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    relationship_id TEXT PRIMARY KEY,
                    ai_id TEXT NOT NULL,
                    participant_id TEXT NOT NULL,
                    participant_name TEXT NOT NULL,
                    sentiment TEXT DEFAULT 'neutral',
                    interaction_count INTEGER DEFAULT 0,
                    first_met TEXT NOT NULL,
                    last_interaction TEXT,
                    notes TEXT,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_relationships_pair 
                ON relationships(ai_id, participant_id)
            """)
            
    
    # Session Management
    def start_session(
        self, 
        session_type: SessionType = SessionType.LOCAL,
        remote_session: RemoteSessionRecord = None
    ) -> str:
        """
        Start a new storage session.
        
        Args:
            session_type: Type of session (local, remote_host, remote_client)
            remote_session: Remote session info if applicable
            
        Returns:
            The session ID
        """
        with self._lock:
            self._session_id = str(uuid.uuid4())
            self._session_type = session_type
            self._remote_session = remote_session
            
            if remote_session:
                self._save_remote_session(remote_session)
            
            return self._session_id
    
    def end_session(self) -> None:
        """End the current session."""
        with self._lock:
            if self._remote_session:
                self._remote_session.ended_at = datetime.now().isoformat()
                self._save_remote_session(self._remote_session)
            
            self._session_type = SessionType.LOCAL
            self._remote_session = None
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        return {
            "session_id": self._session_id,
            "session_type": self._session_type.value,
            "remote_session": self._remote_session.to_dict() if self._remote_session else None
        }
    
    # Interaction Storage
    def store_interaction(
        self,
        sender_id: str,
        sender_name: str,
        content: str,
        sender_type: str = "user",
        content_type: str = "message",
        ai_id: str = None,
        is_private: bool = False,
        private_with: str = None,
        tool_calls: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ) -> InteractionRecord:
        """
        Store an interaction locally.
        
        Args:
            sender_id: ID of the sender
            sender_name: Display name of sender
            content: Message content
            sender_type: Type of sender (user, ai, remote_user)
            content_type: Type of content (message, ai_response, tool_result, system)
            ai_id: ID of AI if applicable
            is_private: Whether this is a private message
            private_with: Who the private message is with
            tool_calls: Any tool calls made
            metadata: Additional metadata
            
        Returns:
            The stored InteractionRecord
        """
        record = InteractionRecord(
            interaction_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            session_id=self._session_id,
            session_type=self._session_type.value,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_type=sender_type,
            content=content,
            content_type=content_type,
            ai_id=ai_id,
            is_private=is_private,
            private_with=private_with,
            tool_calls=tool_calls,
            remote_host_id=self._remote_session.host_id if self._remote_session else None,
            remote_room_code=self._remote_session.room_code if self._remote_session else None,
            metadata=metadata or {}
        )
        
        self._store_interaction_record(record)
        return record
    
    def _store_interaction_record(self, record: InteractionRecord) -> None:
        """Store an interaction record in the database."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO interactions (
                    interaction_id, timestamp, session_id, session_type,
                    sender_id, sender_name, sender_type, content, content_type,
                    ai_id, is_private, private_with, tool_calls,
                    remote_host_id, remote_room_code, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.interaction_id,
                record.timestamp,
                record.session_id,
                record.session_type,
                record.sender_id,
                record.sender_name,
                record.sender_type,
                record.content,
                record.content_type,
                record.ai_id,
                1 if record.is_private else 0,
                record.private_with,
                json.dumps(record.tool_calls) if record.tool_calls else None,
                record.remote_host_id,
                record.remote_room_code,
                json.dumps(record.metadata)
            ))
            
            # Also update remote session statistics if applicable
            if self._remote_session:
                self._remote_session.messages_sent += 1
                self._save_remote_session(self._remote_session)
    
    def get_interactions(
        self,
        session_id: str = None,
        ai_id: str = None,
        is_private: bool = None,
        private_with: str = None,
        remote_room_code: str = None,
        limit: int = 100,
        offset: int = 0,
        order_desc: bool = True
    ) -> List[InteractionRecord]:
        """
        Query interactions with filters.
        
        Args:
            session_id: Filter by session ID
            ai_id: Filter by AI ID
            is_private: Filter by private status
            private_with: Filter by private chat partner
            remote_room_code: Filter by remote room code
            limit: Maximum results
            offset: Offset for pagination
            order_desc: Order by timestamp descending
            
        Returns:
            List of InteractionRecords
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM interactions WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            if ai_id:
                query += " AND ai_id = ?"
                params.append(ai_id)
            if is_private is not None:
                query += " AND is_private = ?"
                params.append(1 if is_private else 0)
            if private_with:
                query += " AND private_with = ?"
                params.append(private_with)
            if remote_room_code:
                query += " AND remote_room_code = ?"
                params.append(remote_room_code)
            
            order = "DESC" if order_desc else "ASC"
            query += f" ORDER BY timestamp {order} LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to records
            columns = [
                "interaction_id", "timestamp", "session_id", "session_type",
                "sender_id", "sender_name", "sender_type", "content", "content_type",
                "ai_id", "is_private", "private_with", "tool_calls",
                "remote_host_id", "remote_room_code", "metadata", "created_at"
            ]
            
            records = []
            for row in rows:
                data = dict(zip(columns, row))
                data["is_private"] = bool(data["is_private"])
                if data["tool_calls"]:
                    data["tool_calls"] = safe_json_loads(data["tool_calls"])
                if data["metadata"]:
                    data["metadata"] = safe_json_loads(data["metadata"], {})
                records.append(InteractionRecord.from_dict(data))
            
            return records
    
    def get_ai_chat_history(
        self, 
        ai_id: str, 
        limit: int = 50,
        include_private: bool = False
    ) -> List[InteractionRecord]:
        """Get chat history for a specific AI."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if include_private:
                query = """
                    SELECT * FROM interactions 
                    WHERE ai_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params = [ai_id, limit]
            else:
                query = """
                    SELECT * FROM interactions 
                    WHERE ai_id = ? AND is_private = 0
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params = [ai_id, limit]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            columns = [
                "interaction_id", "timestamp", "session_id", "session_type",
                "sender_id", "sender_name", "sender_type", "content", "content_type",
                "ai_id", "is_private", "private_with", "tool_calls",
                "remote_host_id", "remote_room_code", "metadata", "created_at"
            ]
            
            records = []
            for row in rows:
                data = dict(zip(columns, row))
                data["is_private"] = bool(data["is_private"])
                if data["tool_calls"]:
                    data["tool_calls"] = safe_json_loads(data["tool_calls"])
                if data["metadata"]:
                    data["metadata"] = safe_json_loads(data["metadata"], {})
                records.append(InteractionRecord.from_dict(data))
            
            return list(reversed(records))  # Return in chronological order
    
    def get_private_chat_history(
        self, 
        participant_a: str, 
        participant_b: str,
        limit: int = 50
    ) -> List[InteractionRecord]:
        """Get private chat history between two participants."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM interactions 
                WHERE is_private = 1 
                AND (
                    (sender_id = ? AND private_with = ?)
                    OR (sender_id = ? AND private_with = ?)
                )
                ORDER BY timestamp DESC 
                LIMIT ?
            """, [participant_a, participant_b, participant_b, participant_a, limit])
            
            rows = cursor.fetchall()
            
            columns = [
                "interaction_id", "timestamp", "session_id", "session_type",
                "sender_id", "sender_name", "sender_type", "content", "content_type",
                "ai_id", "is_private", "private_with", "tool_calls",
                "remote_host_id", "remote_room_code", "metadata", "created_at"
            ]
            
            records = []
            for row in rows:
                data = dict(zip(columns, row))
                data["is_private"] = bool(data["is_private"])
                if data["tool_calls"]:
                    data["tool_calls"] = safe_json_loads(data["tool_calls"])
                if data["metadata"]:
                    data["metadata"] = safe_json_loads(data["metadata"], {})
                records.append(InteractionRecord.from_dict(data))
            
            return list(reversed(records))
    
    # Remote Session Storage
    def _save_remote_session(self, session: RemoteSessionRecord) -> None:
        """Save a remote session record."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO remote_sessions (
                        session_id, session_type, room_code, host_id, host_address,
                        started_at, ended_at, participants, ai_personalities,
                        messages_sent, messages_received, ai_requests, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.session_type,
                    session.room_code,
                    session.host_id,
                    session.host_address,
                    session.started_at,
                    session.ended_at,
                    json.dumps(session.participants),
                    json.dumps(session.ai_personalities),
                    session.messages_sent,
                    session.messages_received,
                    session.ai_requests,
                    json.dumps(session.metadata)
                ))
            
            # Also save to JSON for easy access
            session_file = self.storage_dir / "remote_sessions" / f"{session.session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
    
    def get_remote_sessions(
        self, 
        session_type: str = None,
        limit: int = 50
    ) -> List[RemoteSessionRecord]:
        """Get remote session history."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if session_type:
                cursor.execute("""
                    SELECT * FROM remote_sessions 
                    WHERE session_type = ?
                    ORDER BY started_at DESC 
                    LIMIT ?
                """, [session_type, limit])
            else:
                cursor.execute("""
                    SELECT * FROM remote_sessions 
                    ORDER BY started_at DESC 
                    LIMIT ?
                """, [limit])
            
            rows = cursor.fetchall()
            
            columns = [
                "session_id", "session_type", "room_code", "host_id", "host_address",
                "started_at", "ended_at", "participants", "ai_personalities",
                "messages_sent", "messages_received", "ai_requests", "metadata"
            ]
            
            records = []
            for row in rows:
                data = dict(zip(columns, row))
                if data["participants"]:
                    data["participants"] = safe_json_loads(data["participants"], [])
                if data["ai_personalities"]:
                    data["ai_personalities"] = safe_json_loads(data["ai_personalities"], [])
                if data["metadata"]:
                    data["metadata"] = safe_json_loads(data["metadata"], {})
                records.append(RemoteSessionRecord.from_dict(data))
            
            return records
    
    def get_remote_session_interactions(
        self, 
        room_code: str,
        limit: int = 100
    ) -> List[InteractionRecord]:
        """Get all interactions from a specific remote session."""
        return self.get_interactions(remote_room_code=room_code, limit=limit)
    
    # AI Memory Storage
    def store_ai_memory(
        self,
        ai_id: str,
        content: str,
        memory_type: str = "general",
        source: str = None,
        importance: float = 0.5,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store a memory for an AI.
        
        Args:
            ai_id: The AI's ID
            content: Memory content
            memory_type: Type of memory (general, conversation, fact, preference)
            source: Source of the memory
            importance: Importance score (0-1)
            metadata: Additional metadata
            
        Returns:
            The memory ID
        """
        memory_id = str(uuid.uuid4())
        
        with self._lock:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO ai_memories (
                        memory_id, ai_id, memory_type, content, source,
                        timestamp, importance, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory_id,
                    ai_id,
                    memory_type,
                    content,
                    source,
                    datetime.now().isoformat(),
                    importance,
                    json.dumps(metadata or {})
                ))
        
        return memory_id
    
    def get_ai_memories(
        self,
        ai_id: str,
        memory_type: str = None,
        min_importance: float = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get memories for an AI."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM ai_memories WHERE ai_id = ?"
            params = [ai_id]
            
            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type)
            if min_importance is not None:
                query += " AND importance >= ?"
                params.append(min_importance)
            
            query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            columns = [
                "memory_id", "ai_id", "memory_type", "content", "source",
                "timestamp", "importance", "metadata", "created_at"
            ]
            
            memories = []
            for row in rows:
                memory = dict(zip(columns, row))
                if memory["metadata"]:
                    memory["metadata"] = safe_json_loads(memory["metadata"], {})
                memories.append(memory)
            
            return memories
    
    def search_ai_memories(
        self,
        ai_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search AI memories by content."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Simple LIKE search - could be enhanced with FTS5
            cursor.execute("""
                SELECT * FROM ai_memories 
                WHERE ai_id = ? AND content LIKE ?
                ORDER BY importance DESC, timestamp DESC 
                LIMIT ?
            """, [ai_id, f"%{query}%", limit])
            
            rows = cursor.fetchall()
            
            columns = [
                "memory_id", "ai_id", "memory_type", "content", "source",
                "timestamp", "importance", "metadata", "created_at"
            ]
            
            memories = []
            for row in rows:
                memory = dict(zip(columns, row))
                if memory["metadata"]:
                    memory["metadata"] = safe_json_loads(memory["metadata"], {})
                memories.append(memory)
            
            return memories
    
    # Relationship Storage
    def update_relationship(
        self,
        ai_id: str,
        participant_id: str,
        participant_name: str,
        sentiment: str = "neutral",
        notes: str = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Update or create a relationship record."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                
                # Check if relationship exists
                cursor.execute("""
                    SELECT relationship_id, interaction_count, notes
                    FROM relationships
                    WHERE ai_id = ? AND participant_id = ?
                """, [ai_id, participant_id])
                
                existing = cursor.fetchone()
                now = datetime.now().isoformat()

                if existing:
                    relationship_id, count, existing_notes = existing
                    new_notes = existing_notes or "[]"
                    notes_list = safe_json_loads(new_notes, [])
                    if notes:
                        notes_list.append({"note": notes, "timestamp": now})
                        if len(notes_list) > 20:
                            notes_list = notes_list[-20:]

                    cursor.execute("""
                        UPDATE relationships SET
                            participant_name = ?,
                            sentiment = ?,
                            interaction_count = ?,
                            last_interaction = ?,
                            notes = ?,
                            metadata = ?
                        WHERE relationship_id = ?
                    """, (
                        participant_name,
                        sentiment,
                        count + 1,
                        now,
                        json.dumps(notes_list),
                        json.dumps(metadata or {}),
                        relationship_id
                    ))
                else:
                    relationship_id = str(uuid.uuid4())
                    notes_list = [{"note": notes, "timestamp": now}] if notes else []

                    cursor.execute("""
                        INSERT INTO relationships (
                            relationship_id, ai_id, participant_id, participant_name,
                            sentiment, interaction_count, first_met, last_interaction,
                            notes, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        relationship_id,
                        ai_id,
                        participant_id,
                        participant_name,
                        sentiment,
                        1,
                        now,
                        now,
                        json.dumps(notes_list),
                        json.dumps(metadata or {})
                    ))
    
    def get_ai_relationships(self, ai_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for an AI."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM relationships 
                WHERE ai_id = ?
                ORDER BY interaction_count DESC
            """, [ai_id])
            
            rows = cursor.fetchall()
            
            columns = [
                "relationship_id", "ai_id", "participant_id", "participant_name",
                "sentiment", "interaction_count", "first_met", "last_interaction",
                "notes", "metadata"
            ]
            
            relationships = []
            for row in rows:
                rel = dict(zip(columns, row))
                if rel["notes"]:
                    rel["notes"] = safe_json_loads(rel["notes"], [])
                if rel["metadata"]:
                    rel["metadata"] = safe_json_loads(rel["metadata"], {})
                relationships.append(rel)
            
            return relationships
    
    # Export and Backup
    def export_all_data(self, export_path: Path = None) -> Path:
        """Export all data to a JSON file."""
        export_path = export_path or (self.storage_dir / "exports" / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with self._lock:
            data = {
                "export_date": datetime.now().isoformat(),
                "interactions": [r.to_dict() for r in self.get_interactions(limit=10000)],
                "remote_sessions": [s.to_dict() for s in self.get_remote_sessions(limit=1000)],
                "ai_data": {}
            }
            
            # Get all unique AI IDs
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT ai_id FROM ai_memories WHERE ai_id IS NOT NULL")
            ai_ids = [row[0] for row in cursor.fetchall()]
            
            for ai_id in ai_ids:
                data["ai_data"][ai_id] = {
                    "memories": self.get_ai_memories(ai_id, limit=1000),
                    "relationships": self.get_ai_relationships(ai_id)
                }
            
            with open(export_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        return export_path
    
    def backup_database(self) -> Path:
        """Create a backup of the database."""
        backup_path = self.storage_dir / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        with self._lock:
            shutil.copy2(self._get_db_path(), backup_path)
        
        return backup_path
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Count interactions
            cursor.execute("SELECT COUNT(*) FROM interactions")
            total_interactions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM interactions WHERE is_private = 1")
            private_interactions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM interactions WHERE remote_host_id IS NOT NULL")
            remote_interactions = cursor.fetchone()[0]
            
            # Count remote sessions
            cursor.execute("SELECT COUNT(*) FROM remote_sessions")
            total_remote_sessions = cursor.fetchone()[0]
            
            # Count memories
            cursor.execute("SELECT COUNT(*) FROM ai_memories")
            total_memories = cursor.fetchone()[0]
            
            # Count relationships
            cursor.execute("SELECT COUNT(*) FROM relationships")
            total_relationships = cursor.fetchone()[0]
            
            # Get database size
            db_path = self._get_db_path()
            db_size = db_path.stat().st_size if db_path.exists() else 0
            
            return {
                "total_interactions": total_interactions,
                "private_interactions": private_interactions,
                "remote_interactions": remote_interactions,
                "total_remote_sessions": total_remote_sessions,
                "total_ai_memories": total_memories,
                "total_relationships": total_relationships,
                "database_size_bytes": db_size,
                "storage_directory": str(self.storage_dir)
            }


# Global instance
_local_storage: Optional[LocalStorageManager] = None


def get_local_storage() -> LocalStorageManager:
    """Get the global local storage manager instance."""
    global _local_storage
    if _local_storage is None:
        _local_storage = LocalStorageManager()
    return _local_storage


def initialize_local_storage(storage_dir: Path = None) -> LocalStorageManager:
    """Initialize or reinitialize the local storage manager."""
    global _local_storage
    _local_storage = LocalStorageManager(storage_dir)
    return _local_storage
