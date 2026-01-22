"""
Tests for Local Storage Manager
"""

import json
import os
import sys
import pytest
import tempfile
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from local_storage import (
    LocalStorageManager, InteractionRecord, RemoteSessionRecord,
    SessionType, StorageType, get_base_storage_dir,
    get_local_storage, initialize_local_storage
)


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a LocalStorageManager with temporary directory."""
    return LocalStorageManager(temp_storage_dir)


class TestInteractionRecord:
    """Tests for InteractionRecord."""
    
    def test_create_record(self):
        """Test creating an interaction record."""
        record = InteractionRecord(
            interaction_id="test-123",
            timestamp=datetime.now().isoformat(),
            session_id="session-456",
            session_type="local",
            sender_id="user-1",
            sender_name="Test User",
            sender_type="user",
            content="Hello, AI!",
            content_type="message"
        )
        
        assert record.interaction_id == "test-123"
        assert record.sender_name == "Test User"
        assert record.content == "Hello, AI!"
        assert record.is_private is False
    
    def test_record_to_dict(self):
        """Test converting record to dict."""
        record = InteractionRecord(
            interaction_id="test-123",
            timestamp="2024-01-01T00:00:00",
            session_id="session-456",
            session_type="local",
            sender_id="user-1",
            sender_name="Test User",
            sender_type="user",
            content="Hello",
            content_type="message",
            ai_id="nova",
            is_private=True,
            private_with="echo"
        )
        
        data = record.to_dict()
        assert data["interaction_id"] == "test-123"
        assert data["is_private"] is True
        assert data["private_with"] == "echo"
        assert data["ai_id"] == "nova"
    
    def test_record_from_dict(self):
        """Test creating record from dict."""
        data = {
            "interaction_id": "test-789",
            "timestamp": "2024-01-01T00:00:00",
            "session_id": "session-abc",
            "session_type": "remote_client",
            "sender_id": "ai-nova",
            "sender_name": "Nova",
            "sender_type": "ai",
            "content": "Hello, human!",
            "content_type": "ai_response",
            "ai_id": "nova",
            "remote_host_id": "host-123",
            "remote_room_code": "ABC123"
        }
        
        record = InteractionRecord.from_dict(data)
        assert record.interaction_id == "test-789"
        assert record.session_type == "remote_client"
        assert record.remote_host_id == "host-123"


class TestRemoteSessionRecord:
    """Tests for RemoteSessionRecord."""
    
    def test_create_session_record(self):
        """Test creating a remote session record."""
        record = RemoteSessionRecord(
            session_id="session-123",
            session_type="client",
            room_code="ABC123",
            host_id="host-456",
            host_address="192.168.1.100:8765"
        )
        
        assert record.session_id == "session-123"
        assert record.session_type == "client"
        assert record.room_code == "ABC123"
        assert record.messages_sent == 0
    
    def test_session_to_dict(self):
        """Test converting session to dict."""
        record = RemoteSessionRecord(
            session_id="session-123",
            session_type="host",
            room_code="XYZ789",
            host_id="self-123",
            participants=[{"id": "peer-1", "name": "User 1"}],
            ai_personalities=["nova", "echo", "sage"]
        )
        
        data = record.to_dict()
        assert data["room_code"] == "XYZ789"
        assert len(data["participants"]) == 1
        assert len(data["ai_personalities"]) == 3


class TestLocalStorageManager:
    """Tests for LocalStorageManager."""
    
    def test_initialization(self, storage_manager, temp_storage_dir):
        """Test storage manager initializes correctly."""
        assert storage_manager.storage_dir == temp_storage_dir
        assert (temp_storage_dir / "interactions").exists()
        assert (temp_storage_dir / "ai_states").exists()
        assert (temp_storage_dir / "remote_sessions").exists()
    
    def test_start_local_session(self, storage_manager):
        """Test starting a local session."""
        session_id = storage_manager.start_session(SessionType.LOCAL)
        
        assert session_id is not None
        info = storage_manager.get_session_info()
        assert info["session_type"] == "local"
        assert info["remote_session"] is None
    
    def test_start_remote_session(self, storage_manager):
        """Test starting a remote session."""
        remote_session = RemoteSessionRecord(
            session_id="remote-123",
            session_type="client",
            room_code="ABC123",
            host_id="host-456"
        )
        
        session_id = storage_manager.start_session(
            SessionType.REMOTE_CLIENT,
            remote_session
        )
        
        info = storage_manager.get_session_info()
        assert info["session_type"] == "remote_client"
        assert info["remote_session"] is not None
        assert info["remote_session"]["room_code"] == "ABC123"
    
    def test_store_interaction(self, storage_manager):
        """Test storing an interaction."""
        record = storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="Test User",
            content="Hello, Nova!",
            ai_id="nova"
        )
        
        assert record.interaction_id is not None
        assert record.content == "Hello, Nova!"
        assert record.ai_id == "nova"
    
    def test_store_private_interaction(self, storage_manager):
        """Test storing a private interaction."""
        record = storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="Test User",
            content="Private message",
            is_private=True,
            private_with="nova"
        )
        
        assert record.is_private is True
        assert record.private_with == "nova"
    
    def test_store_remote_interaction(self, storage_manager):
        """Test storing an interaction in a remote session."""
        remote_session = RemoteSessionRecord(
            session_id="remote-123",
            session_type="client",
            room_code="XYZ789",
            host_id="host-456"
        )
        storage_manager.start_session(SessionType.REMOTE_CLIENT, remote_session)
        
        record = storage_manager.store_interaction(
            sender_id="ai-nova",
            sender_name="Nova",
            sender_type="ai",
            content="Hello from remote!",
            ai_id="nova"
        )
        
        assert record.remote_host_id == "host-456"
        assert record.remote_room_code == "XYZ789"
    
    def test_get_interactions(self, storage_manager):
        """Test retrieving interactions."""
        # Store some interactions
        for i in range(5):
            storage_manager.store_interaction(
                sender_id=f"user-{i}",
                sender_name=f"User {i}",
                content=f"Message {i}"
            )
        
        interactions = storage_manager.get_interactions(limit=10)
        assert len(interactions) == 5
    
    def test_get_ai_chat_history(self, storage_manager):
        """Test getting chat history for a specific AI."""
        # Store interactions with different AIs
        storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="User",
            content="Hello Nova",
            ai_id="nova"
        )
        storage_manager.store_interaction(
            sender_id="ai-nova",
            sender_name="Nova",
            sender_type="ai",
            content="Hello!",
            ai_id="nova"
        )
        storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="User",
            content="Hello Echo",
            ai_id="echo"
        )
        
        nova_history = storage_manager.get_ai_chat_history("nova")
        assert len(nova_history) == 2
        
        echo_history = storage_manager.get_ai_chat_history("echo")
        assert len(echo_history) == 1
    
    def test_get_private_chat_history(self, storage_manager):
        """Test getting private chat history."""
        # Store private messages
        storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="User",
            content="Private to Nova",
            is_private=True,
            private_with="nova"
        )
        storage_manager.store_interaction(
            sender_id="nova",
            sender_name="Nova",
            sender_type="ai",
            content="Private reply",
            is_private=True,
            private_with="user-1"
        )
        storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="User",
            content="Private to Echo",
            is_private=True,
            private_with="echo"
        )
        
        history = storage_manager.get_private_chat_history("user-1", "nova")
        assert len(history) == 2
    
    def test_store_ai_memory(self, storage_manager):
        """Test storing AI memories."""
        memory_id = storage_manager.store_ai_memory(
            ai_id="nova",
            content="User likes cats",
            memory_type="preference",
            importance=0.8
        )
        
        assert memory_id is not None
        
        memories = storage_manager.get_ai_memories("nova")
        assert len(memories) == 1
        assert memories[0]["content"] == "User likes cats"
        assert memories[0]["importance"] == 0.8
    
    def test_search_ai_memories(self, storage_manager):
        """Test searching AI memories."""
        storage_manager.store_ai_memory(
            ai_id="nova",
            content="User's favorite color is blue",
            memory_type="fact"
        )
        storage_manager.store_ai_memory(
            ai_id="nova",
            content="User prefers Python programming",
            memory_type="preference"
        )
        
        results = storage_manager.search_ai_memories("nova", "color")
        assert len(results) == 1
        assert "blue" in results[0]["content"]
    
    def test_update_relationship(self, storage_manager):
        """Test updating relationships."""
        storage_manager.update_relationship(
            ai_id="nova",
            participant_id="user-1",
            participant_name="Test User",
            sentiment="positive",
            notes="Friendly conversation"
        )
        
        relationships = storage_manager.get_ai_relationships("nova")
        assert len(relationships) == 1
        assert relationships[0]["sentiment"] == "positive"
        assert relationships[0]["interaction_count"] == 1
        
        # Update again
        storage_manager.update_relationship(
            ai_id="nova",
            participant_id="user-1",
            participant_name="Test User",
            sentiment="very_positive"
        )
        
        relationships = storage_manager.get_ai_relationships("nova")
        assert relationships[0]["interaction_count"] == 2
        assert relationships[0]["sentiment"] == "very_positive"
    
    def test_get_remote_sessions(self, storage_manager):
        """Test getting remote session history."""
        # Create and save a remote session
        session = RemoteSessionRecord(
            session_id="session-1",
            session_type="client",
            room_code="ABC123",
            host_id="host-1"
        )
        storage_manager.start_session(SessionType.REMOTE_CLIENT, session)
        storage_manager.end_session()
        
        sessions = storage_manager.get_remote_sessions()
        assert len(sessions) == 1
        assert sessions[0].room_code == "ABC123"
    
    def test_get_remote_session_interactions(self, storage_manager):
        """Test getting interactions for a specific remote session."""
        # Start a remote session
        session = RemoteSessionRecord(
            session_id="session-1",
            session_type="client",
            room_code="TEST123",
            host_id="host-1"
        )
        storage_manager.start_session(SessionType.REMOTE_CLIENT, session)
        
        # Store some interactions
        for i in range(3):
            storage_manager.store_interaction(
                sender_id=f"user-{i}",
                sender_name=f"User {i}",
                content=f"Remote message {i}"
            )
        
        # Get interactions for this room
        interactions = storage_manager.get_remote_session_interactions("TEST123")
        assert len(interactions) == 3
        for interaction in interactions:
            assert interaction.remote_room_code == "TEST123"
    
    def test_export_all_data(self, storage_manager, temp_storage_dir):
        """Test exporting all data."""
        # Store some data
        storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="User",
            content="Test message"
        )
        storage_manager.store_ai_memory(
            ai_id="nova",
            content="Test memory"
        )
        
        export_path = storage_manager.export_all_data()
        assert export_path.exists()
        
        with open(export_path) as f:
            data = json.load(f)
        
        assert "interactions" in data
        assert "export_date" in data
    
    def test_backup_database(self, storage_manager, temp_storage_dir):
        """Test database backup."""
        # Store some data first
        storage_manager.store_interaction(
            sender_id="user-1",
            sender_name="User",
            content="Test message"
        )
        
        backup_path = storage_manager.backup_database()
        assert backup_path.exists()
        assert "backup" in str(backup_path)
    
    def test_get_storage_stats(self, storage_manager):
        """Test getting storage statistics."""
        # Store some data
        for i in range(5):
            storage_manager.store_interaction(
                sender_id=f"user-{i}",
                sender_name=f"User {i}",
                content=f"Message {i}"
            )
        
        storage_manager.store_ai_memory(
            ai_id="nova",
            content="Memory 1"
        )
        
        stats = storage_manager.get_storage_stats()
        assert stats["total_interactions"] == 5
        assert stats["total_ai_memories"] == 1
        assert stats["database_size_bytes"] > 0


class TestGlobalStorageInstance:
    """Tests for global storage instance functions."""
    
    def test_get_local_storage(self, temp_storage_dir):
        """Test getting global storage instance."""
        storage = initialize_local_storage(temp_storage_dir)
        assert storage is not None
        assert storage.storage_dir == temp_storage_dir
        
        # Get should return same instance
        storage2 = get_local_storage()
        assert storage2 is storage


class TestBidirectionalStorage:
    """Tests for bidirectional storage scenarios."""
    
    def test_client_stores_host_data(self, temp_storage_dir):
        """Test that client can store data received from host."""
        # Simulate client storage
        client_storage = LocalStorageManager(temp_storage_dir / "client")
        
        # Start remote session as client
        remote_session = RemoteSessionRecord(
            session_id="session-1",
            session_type="client",
            room_code="HOST123",
            host_id="host-device-1",
            host_address="192.168.1.100:8765"
        )
        client_storage.start_session(SessionType.REMOTE_CLIENT, remote_session)
        
        # Store AI response (received from host)
        client_storage.store_interaction(
            sender_id="ai-nova",
            sender_name="Nova",
            sender_type="ai",
            content="Hello! I'm Nova, running on the host device.",
            content_type="ai_response",
            ai_id="nova"
        )
        
        # Verify storage
        interactions = client_storage.get_interactions()
        assert len(interactions) == 1
        assert interactions[0].remote_host_id == "host-device-1"
        assert interactions[0].content_type == "ai_response"
    
    def test_host_stores_client_messages(self, temp_storage_dir):
        """Test that host stores messages from clients."""
        # Simulate host storage
        host_storage = LocalStorageManager(temp_storage_dir / "host")
        
        # Start remote session as host
        remote_session = RemoteSessionRecord(
            session_id="session-1",
            session_type="host",
            room_code="ABC123",
            host_id="self-host-id"
        )
        host_storage.start_session(SessionType.REMOTE_HOST, remote_session)
        
        # Store message from remote client
        host_storage.store_interaction(
            sender_id="remote-client-1",
            sender_name="Remote User",
            sender_type="remote_user",
            content="Hello from my phone!",
            content_type="message"
        )
        
        # Verify storage
        interactions = host_storage.get_interactions()
        assert len(interactions) == 1
        assert interactions[0].sender_type == "remote_user"
    
    def test_both_devices_store_conversation(self, temp_storage_dir):
        """Test complete conversation stored on both devices."""
        # Set up both storages
        host_storage = LocalStorageManager(temp_storage_dir / "host")
        client_storage = LocalStorageManager(temp_storage_dir / "client")
        
        # Start sessions
        host_session = RemoteSessionRecord(
            session_id="session-host",
            session_type="host",
            room_code="SHARED123",
            host_id="host-id"
        )
        client_session = RemoteSessionRecord(
            session_id="session-client",
            session_type="client",
            room_code="SHARED123",
            host_id="host-id"
        )
        
        host_storage.start_session(SessionType.REMOTE_HOST, host_session)
        client_storage.start_session(SessionType.REMOTE_CLIENT, client_session)
        
        # Simulate conversation - each device stores all messages
        messages = [
            ("client-1", "Client User", "remote_user", "Hi Nova!", "message"),
            ("ai-nova", "Nova", "ai", "Hello! How can I help?", "ai_response"),
            ("client-1", "Client User", "remote_user", "Tell me about AI", "message"),
            ("ai-nova", "Nova", "ai", "AI is fascinating!", "ai_response"),
        ]
        
        for sender_id, sender_name, sender_type, content, content_type in messages:
            # Store on host
            host_storage.store_interaction(
                sender_id=sender_id,
                sender_name=sender_name,
                sender_type=sender_type,
                content=content,
                content_type=content_type
            )
            # Store on client  
            client_storage.store_interaction(
                sender_id=sender_id,
                sender_name=sender_name,
                sender_type=sender_type,
                content=content,
                content_type=content_type
            )
        
        # Both should have same conversation
        host_interactions = host_storage.get_interactions(limit=10)
        client_interactions = client_storage.get_interactions(limit=10)
        
        assert len(host_interactions) == 4
        assert len(client_interactions) == 4
        
        # Content should match
        for h, c in zip(sorted(host_interactions, key=lambda x: x.timestamp),
                        sorted(client_interactions, key=lambda x: x.timestamp)):
            assert h.content == c.content
            assert h.sender_name == c.sender_name


class TestStorageTypes:
    """Tests for different storage types."""
    
    def test_storage_type_enum(self):
        """Test StorageType enum values."""
        assert StorageType.CHAT_HISTORY.value == "chat_history"
        assert StorageType.PRIVATE_CHAT.value == "private_chat"
        assert StorageType.AI_STATE.value == "ai_state"
        assert StorageType.REMOTE_SESSION.value == "remote_session"
    
    def test_session_type_enum(self):
        """Test SessionType enum values."""
        assert SessionType.LOCAL.value == "local"
        assert SessionType.REMOTE_HOST.value == "remote_host"
        assert SessionType.REMOTE_CLIENT.value == "remote_client"
