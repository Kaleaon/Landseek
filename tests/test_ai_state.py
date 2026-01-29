"""
Tests for AI State Management

Tests for persistent state, customizable names, private conversations,
and emotion tracking.
"""

import pytest
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta


# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_state import (
    AIState, AIStateManager, PrivateConversation, ChatHistoryEntry,
    EmotionalState, get_documents_folder, initialize_state_manager
)


class TestChatHistoryEntry:
    """Tests for ChatHistoryEntry dataclass."""
    
    def test_create_entry(self):
        """Test creating a chat history entry."""
        entry = ChatHistoryEntry(
            timestamp="2024-01-01T12:00:00",
            sender="Nova",
            content="Hello, world!"
        )
        assert entry.sender == "Nova"
        assert entry.content == "Hello, world!"
        assert entry.is_private is False
        assert entry.private_with is None
    
    def test_create_private_entry(self):
        """Test creating a private chat entry."""
        entry = ChatHistoryEntry(
            timestamp="2024-01-01T12:00:00",
            sender="User",
            content="Private message",
            is_private=True,
            private_with="Nova"
        )
        assert entry.is_private is True
        assert entry.private_with == "Nova"
    
    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = ChatHistoryEntry(
            timestamp="2024-01-01T12:00:00",
            sender="Nova",
            content="Hello"
        )
        data = entry.to_dict()
        assert data["sender"] == "Nova"
        assert data["content"] == "Hello"
        assert data["is_private"] is False
    
    def test_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "timestamp": "2024-01-01T12:00:00",
            "sender": "Echo",
            "content": "Hi there!",
            "is_private": True,
            "private_with": "User"
        }
        entry = ChatHistoryEntry.from_dict(data)
        assert entry.sender == "Echo"
        assert entry.is_private is True
        assert entry.private_with == "User"


class TestPrivateConversation:
    """Tests for PrivateConversation class."""
    
    def test_create_conversation(self):
        """Test creating a private conversation."""
        conv = PrivateConversation(
            participant_a="User",
            participant_b="Nova"
        )
        assert conv.participant_a == "User"
        assert conv.participant_b == "Nova"
        assert len(conv.messages) == 0
    
    def test_conversation_id(self):
        """Test that conversation ID is consistent regardless of order."""
        conv1 = PrivateConversation(participant_a="User", participant_b="Nova")
        conv2 = PrivateConversation(participant_a="Nova", participant_b="User")
        assert conv1.conversation_id == conv2.conversation_id
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        conv = PrivateConversation(
            participant_a="User",
            participant_b="Nova"
        )
        conv.add_message("User", "Hello Nova!")
        conv.add_message("Nova", "Hi there!")
        
        assert len(conv.messages) == 2
        assert conv.messages[0].sender == "User"
        assert conv.messages[1].sender == "Nova"
        assert conv.messages[0].is_private is True
    
    def test_get_recent_messages(self):
        """Test getting recent messages."""
        conv = PrivateConversation(
            participant_a="User",
            participant_b="Nova"
        )
        for i in range(15):
            conv.add_message("User", f"Message {i}")
        
        recent = conv.get_recent_messages(5)
        assert len(recent) == 5
        assert recent[0].content == "Message 10"
    
    def test_to_dict_and_from_dict(self):
        """Test serialization roundtrip."""
        conv = PrivateConversation(
            participant_a="User",
            participant_b="Nova"
        )
        conv.add_message("User", "Test message")
        
        data = conv.to_dict()
        restored = PrivateConversation.from_dict(data)
        
        assert restored.participant_a == conv.participant_a
        assert restored.participant_b == conv.participant_b
        assert len(restored.messages) == 1


class TestEmotionalState:
    """Tests for EmotionalState enum."""
    
    def test_emotional_states(self):
        """Test that all emotional states are defined."""
        assert EmotionalState.NEUTRAL.value == "neutral"
        assert EmotionalState.HAPPY.value == "happy"
        assert EmotionalState.CURIOUS.value == "curious"
        assert EmotionalState.THOUGHTFUL.value == "thoughtful"
        assert EmotionalState.EXCITED.value == "excited"
        assert EmotionalState.CALM.value == "calm"
        assert EmotionalState.FOCUSED.value == "focused"
        assert EmotionalState.PLAYFUL.value == "playful"
        assert EmotionalState.EMPATHETIC.value == "empathetic"
        assert EmotionalState.INSPIRED.value == "inspired"


class TestAIState:
    """Tests for AIState dataclass."""
    
    def test_create_state(self):
        """Test creating an AI state."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Curious and analytical"
        )
        assert state.ai_id == "nova"
        assert state.display_name == "Nova"
        assert state.personality == "Curious and analytical"
        assert state.is_active is True
    
    def test_add_chat_entry(self):
        """Test adding chat entries to state."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test"
        )
        state.add_chat_entry("User", "Hello!")
        state.add_chat_entry("Nova", "Hi there!")
        
        assert len(state.chat_history) == 2
    
    def test_set_emotion(self):
        """Test setting emotional state."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test"
        )
        state.set_emotion(EmotionalState.HAPPY, 0.8)
        
        assert state.current_emotion == "happy"
        assert state.emotion_intensity == 0.8
        assert len(state.mood_history) == 1
    
    def test_emotion_intensity_bounds(self):
        """Test that emotion intensity is bounded."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test"
        )
        state.set_emotion(EmotionalState.EXCITED, 1.5)
        assert state.emotion_intensity == 1.0
        
        state.set_emotion(EmotionalState.CALM, -0.5)
        assert state.emotion_intensity == 0.0
    
    def test_update_relationship(self):
        """Test updating relationships."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test"
        )
        state.update_relationship("User", "positive", "Had a nice chat")
        
        assert "User" in state.relationships
        assert state.relationships["User"]["sentiment"] == "positive"
        assert state.relationships["User"]["interaction_count"] == 1
    
    def test_add_memory(self):
        """Test adding memories."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test"
        )
        state.add_memory("User mentioned they like science")
        
        assert len(state.memories) == 1
        assert "science" in state.memories[0]
    
    def test_rename(self):
        """Test renaming an AI."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test"
        )
        state.rename("Supernova")
        assert state.display_name == "Supernova"
        assert state.original_name == "Nova"
    
    def test_get_recent_history(self):
        """Test getting recent chat history."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test"
        )
        for i in range(20):
            state.add_chat_entry("User", f"Message {i}")
        
        recent = state.get_recent_history(5)
        assert len(recent) == 5
    
    def test_to_dict_and_from_dict(self):
        """Test serialization roundtrip."""
        state = AIState(
            ai_id="nova",
            display_name="Nova",
            original_name="Nova",
            personality="Test personality",
            avatar="🌟",
            tags=["analytical", "curious"]
        )
        state.add_chat_entry("User", "Test")
        state.set_emotion(EmotionalState.HAPPY, 0.7)
        
        data = state.to_dict()
        restored = AIState.from_dict(data)
        
        assert restored.ai_id == state.ai_id
        assert restored.display_name == state.display_name
        assert restored.personality == state.personality
        assert restored.current_emotion == state.current_emotion
        assert len(restored.chat_history) == 1


class TestAIStateManager:
    """Tests for AIStateManager class."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_create_manager(self, temp_storage):
        """Test creating a state manager."""
        manager = AIStateManager(storage_dir=temp_storage)
        assert manager.storage_dir == temp_storage
        assert (temp_storage / "ai_states").exists()
        assert (temp_storage / "private_chats").exists()
    
    def test_create_state(self, temp_storage):
        """Test creating an AI state through manager."""
        manager = AIStateManager(storage_dir=temp_storage)
        state = manager.create_state(
            ai_id="nova",
            display_name="Nova",
            personality="Curious and analytical",
            avatar="🌟"
        )
        
        assert state.ai_id == "nova"
        assert state.display_name == "Nova"
        
        # Check data was created in DB
        db_path = temp_storage / "ai_data.db"
        assert db_path.exists()

        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT data FROM ai_states WHERE ai_id = ?", ("nova",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        data = json.loads(row[0])
        assert data["display_name"] == "Nova"
    
    def test_get_state(self, temp_storage):
        """Test retrieving an AI state."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(
            ai_id="nova",
            display_name="Nova",
            personality="Test"
        )
        
        state = manager.get_state("nova")
        assert state is not None
        assert state.ai_id == "nova"
    
    def test_save_and_load_state(self, temp_storage):
        """Test saving and loading state from disk."""
        manager1 = AIStateManager(storage_dir=temp_storage)
        state = manager1.create_state(
            ai_id="nova",
            display_name="Nova",
            personality="Test"
        )
        state.add_chat_entry("User", "Hello!")
        manager1.save_state(state)
        
        # Create new manager and load
        manager2 = AIStateManager(storage_dir=temp_storage)
        loaded = manager2.get_state("nova")
        
        assert loaded is not None
        assert len(loaded.chat_history) == 1
    
    def test_delete_state(self, temp_storage):
        """Test deleting an AI state."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(
            ai_id="nova",
            display_name="Nova",
            personality="Test"
        )
        
        assert manager.delete_state("nova") is True
        assert manager.get_state("nova") is None
        assert not (temp_storage / "ai_states" / "nova.json").exists()
    
    def test_list_states(self, temp_storage):
        """Test listing all states."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(ai_id="nova", display_name="Nova", personality="Test")
        manager.create_state(ai_id="echo", display_name="Echo", personality="Test")
        manager.create_state(ai_id="sage", display_name="Sage", personality="Test")
        
        states = manager.list_states()
        assert len(states) == 3
    
    def test_list_active_states(self, temp_storage):
        """Test listing only active states."""
        manager = AIStateManager(storage_dir=temp_storage)
        state1 = manager.create_state(ai_id="nova", display_name="Nova", personality="Test")
        state2 = manager.create_state(ai_id="echo", display_name="Echo", personality="Test")
        
        state1.is_active = True
        state2.is_active = False
        manager.save_state(state1)
        manager.save_state(state2)
        
        active = manager.list_states(active_only=True)
        assert len(active) == 1
        assert active[0].ai_id == "nova"
    
    def test_set_active(self, temp_storage):
        """Test setting AI active status."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(ai_id="nova", display_name="Nova", personality="Test")
        
        manager.set_active("nova", False)
        state = manager.get_state("nova")
        assert state.is_active is False
        
        manager.set_active("nova", True)
        state = manager.get_state("nova")
        assert state.is_active is True
    
    def test_rename_ai(self, temp_storage):
        """Test renaming an AI through manager."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(ai_id="nova", display_name="Nova", personality="Test")
        
        manager.rename_ai("nova", "Supernova")
        state = manager.get_state("nova")
        assert state.display_name == "Supernova"
    
    def test_get_or_create_conversation(self, temp_storage):
        """Test getting or creating private conversations."""
        manager = AIStateManager(storage_dir=temp_storage)
        
        conv1 = manager.get_or_create_conversation("User", "Nova")
        assert conv1 is not None
        
        conv2 = manager.get_or_create_conversation("User", "Nova")
        assert conv1.conversation_id == conv2.conversation_id
    
    def test_add_private_message(self, temp_storage):
        """Test adding private messages."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(ai_id="nova", display_name="Nova", personality="Test")
        
        conv = manager.add_private_message("User", "nova", "Hello privately!")
        
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello privately!"
    
    def test_get_conversations_for(self, temp_storage):
        """Test getting all conversations for a participant."""
        manager = AIStateManager(storage_dir=temp_storage)
        
        manager.add_private_message("User", "Nova", "Hi Nova")
        manager.add_private_message("User", "Echo", "Hi Echo")
        manager.add_private_message("Nova", "Echo", "Hi from Nova")
        
        user_convs = manager.get_conversations_for("User")
        assert len(user_convs) == 2
        
        nova_convs = manager.get_conversations_for("Nova")
        assert len(nova_convs) == 2
    
    def test_settings(self, temp_storage):
        """Test settings management."""
        manager = AIStateManager(storage_dir=temp_storage)
        
        manager.set_setting("user_name", "TestUser")
        manager.set_setting("model", "ollama/gemma3:4b")
        
        assert manager.get_setting("user_name") == "TestUser"
        assert manager.get_setting("model") == "ollama/gemma3:4b"
        assert manager.get_setting("nonexistent", "default") == "default"
    
    def test_export_import(self, temp_storage):
        """Test exporting and importing data."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(ai_id="nova", display_name="Nova", personality="Test")
        manager.add_private_message("User", "Nova", "Test message")
        manager.set_setting("user_name", "TestUser")
        
        # Export
        data = manager.export_all()
        assert "states" in data
        assert "conversations" in data
        assert "settings" in data
        
        # Create new manager and import
        with tempfile.TemporaryDirectory() as new_dir:
            new_manager = AIStateManager(storage_dir=Path(new_dir))
            new_manager.import_all(data)
            
            assert new_manager.get_state("nova") is not None
            assert new_manager.get_setting("user_name") == "TestUser"
    
    def test_save_all(self, temp_storage):
        """Test saving all data at once."""
        manager = AIStateManager(storage_dir=temp_storage)
        manager.create_state(ai_id="nova", display_name="Nova", personality="Test")
        manager.create_state(ai_id="echo", display_name="Echo", personality="Test")
        manager.add_private_message("User", "Nova", "Test")
        manager.set_setting("test", "value")
        
        manager.save_all()
        
        # All data should exist in DB
        db_path = temp_storage / "ai_data.db"
        assert db_path.exists()

        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT count(*) FROM ai_states")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

        assert (temp_storage / "settings.json").exists()


class TestGetDocumentsFolder:
    """Tests for get_documents_folder function."""
    
    def test_returns_path(self):
        """Test that function returns a Path object."""
        folder = get_documents_folder()
        assert isinstance(folder, Path)
    
    def test_path_ends_with_aichat(self):
        """Test that path ends with AIChat folder name."""
        folder = get_documents_folder()
        assert folder.name in ["AIChat", ".aichat"]


class TestInitializeStateManager:
    """Tests for initialize_state_manager function."""
    
    def test_initialize_creates_manager(self):
        """Test that initialization creates a manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = initialize_state_manager(Path(tmpdir))
            assert manager is not None
            assert isinstance(manager, AIStateManager)
