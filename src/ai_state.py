"""
AI State Management - Persistent State for AI Personalities

This module manages persistent state for AI personalities including:
- Chat history (per AI)
- Emotions and mood
- Customizable names
- Personality traits
- Private conversations between participants

All data is stored in the public Documents folder for accessibility.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


# Set up logging
logger = logging.getLogger(__name__)


# Default storage location (public Documents folder)
def get_documents_folder() -> Path:
    """Get the public Documents folder path."""
    # Check for Android
    if os.environ.get("ANDROID_STORAGE"):
        return Path("/storage/emulated/0/Documents/AIChat")
    
    # Check for common locations
    home = Path.home()
    
    # Windows
    if (home / "Documents").exists():
        return home / "Documents" / "AIChat"
    
    # macOS/Linux
    if (home / "Documents").exists():
        return home / "Documents" / "AIChat"
    
    # Fallback to home directory
    return home / ".aichat"


# Create storage directory
STORAGE_DIR = get_documents_folder()


class EmotionalState(Enum):
    """Emotional states for AI personalities."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    CURIOUS = "curious"
    THOUGHTFUL = "thoughtful"
    EXCITED = "excited"
    CALM = "calm"
    FOCUSED = "focused"
    PLAYFUL = "playful"
    EMPATHETIC = "empathetic"
    INSPIRED = "inspired"


@dataclass
class ChatHistoryEntry:
    """A single entry in chat history."""
    timestamp: str
    sender: str
    content: str
    is_private: bool = False
    private_with: Optional[str] = None  # Who the private chat was with
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "sender": self.sender,
            "content": self.content,
            "is_private": self.is_private,
            "private_with": self.private_with
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatHistoryEntry":
        return cls(
            timestamp=data.get("timestamp", ""),
            sender=data.get("sender", ""),
            content=data.get("content", ""),
            is_private=data.get("is_private", False),
            private_with=data.get("private_with")
        )


@dataclass
class PrivateConversation:
    """A private conversation between two participants."""
    participant_a: str  # First participant (can be AI or user)
    participant_b: str  # Second participant (can be AI or user)
    messages: List[ChatHistoryEntry] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def conversation_id(self) -> str:
        """Generate a unique conversation ID."""
        # Sort names to ensure consistent ID regardless of order
        names = sorted([self.participant_a, self.participant_b])
        return f"{names[0]}__{names[1]}"
    
    def add_message(self, sender: str, content: str) -> None:
        """Add a message to the conversation."""
        entry = ChatHistoryEntry(
            timestamp=datetime.now().isoformat(),
            sender=sender,
            content=content,
            is_private=True,
            private_with=self.participant_b if sender == self.participant_a else self.participant_a
        )
        self.messages.append(entry)
        self.last_activity = datetime.now().isoformat()
    
    def get_recent_messages(self, count: int = 10) -> List[ChatHistoryEntry]:
        """Get recent messages."""
        return self.messages[-count:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "participant_a": self.participant_a,
            "participant_b": self.participant_b,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrivateConversation":
        conv = cls(
            participant_a=data.get("participant_a", ""),
            participant_b=data.get("participant_b", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_activity=data.get("last_activity", datetime.now().isoformat())
        )
        conv.messages = [
            ChatHistoryEntry.from_dict(m) 
            for m in data.get("messages", [])
        ]
        return conv


@dataclass
class AIState:
    """Persistent state for an AI personality."""
    # Identity
    ai_id: str  # Unique identifier (e.g., "nova", "echo")
    display_name: str  # Customizable display name
    original_name: str  # Original built-in name
    
    # Personality
    personality: str  # Description of behavior
    avatar: str = "🤖"
    tags: List[str] = field(default_factory=list)
    
    # Emotional state
    current_emotion: str = EmotionalState.NEUTRAL.value
    emotion_intensity: float = 0.5  # 0.0-1.0
    mood_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Chat history
    chat_history: List[ChatHistoryEntry] = field(default_factory=list)
    max_history_size: int = 1000  # Max messages to keep
    
    # Relationships (how this AI feels about other participants)
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Custom traits and memories
    memories: List[str] = field(default_factory=list)
    custom_traits: Dict[str, Any] = field(default_factory=dict)
    
    # Settings
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500
    is_active: bool = True  # Whether this AI is in the chat room
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_chat_entry(self, sender: str, content: str, is_private: bool = False, private_with: str = None) -> None:
        """Add a chat entry to history."""
        entry = ChatHistoryEntry(
            timestamp=datetime.now().isoformat(),
            sender=sender,
            content=content,
            is_private=is_private,
            private_with=private_with
        )
        self.chat_history.append(entry)
        self.last_active = datetime.now().isoformat()
        
        # Trim history if too large
        if len(self.chat_history) > self.max_history_size:
            self.chat_history = self.chat_history[-self.max_history_size:]
    
    def set_emotion(self, emotion: EmotionalState, intensity: float = 0.5) -> None:
        """Set the current emotional state."""
        self.current_emotion = emotion.value
        self.emotion_intensity = max(0.0, min(1.0, intensity))
        self.mood_history.append({
            "emotion": emotion.value,
            "intensity": self.emotion_intensity,
            "timestamp": datetime.now().isoformat()
        })
        # Keep mood history reasonable
        if len(self.mood_history) > 100:
            self.mood_history = self.mood_history[-100:]
    
    def update_relationship(self, participant: str, sentiment: str = "neutral", notes: str = None) -> None:
        """Update relationship with another participant."""
        if participant not in self.relationships:
            self.relationships[participant] = {
                "sentiment": "neutral",
                "interaction_count": 0,
                "notes": [],
                "first_met": datetime.now().isoformat()
            }
        
        self.relationships[participant]["sentiment"] = sentiment
        self.relationships[participant]["interaction_count"] += 1
        self.relationships[participant]["last_interaction"] = datetime.now().isoformat()
        
        if notes:
            self.relationships[participant]["notes"].append({
                "note": notes,
                "timestamp": datetime.now().isoformat()
            })
            # Keep notes reasonable
            if len(self.relationships[participant]["notes"]) > 20:
                self.relationships[participant]["notes"] = self.relationships[participant]["notes"][-20:]
    
    def add_memory(self, memory: str) -> None:
        """Add a memory."""
        self.memories.append(f"[{datetime.now().isoformat()}] {memory}")
        # Keep memories reasonable
        if len(self.memories) > 50:
            self.memories = self.memories[-50:]
    
    def get_recent_history(self, count: int = 10, include_private: bool = False) -> List[ChatHistoryEntry]:
        """Get recent chat history."""
        if include_private:
            return self.chat_history[-count:]
        return [h for h in self.chat_history if not h.is_private][-count:]
    
    def rename(self, new_name: str) -> None:
        """Change the display name."""
        self.display_name = new_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ai_id": self.ai_id,
            "display_name": self.display_name,
            "original_name": self.original_name,
            "personality": self.personality,
            "avatar": self.avatar,
            "tags": self.tags,
            "current_emotion": self.current_emotion,
            "emotion_intensity": self.emotion_intensity,
            "mood_history": self.mood_history,
            "chat_history": [h.to_dict() for h in self.chat_history],
            "max_history_size": self.max_history_size,
            "relationships": self.relationships,
            "memories": self.memories,
            "custom_traits": self.custom_traits,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_active": self.last_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIState":
        """Create from dictionary."""
        state = cls(
            ai_id=data.get("ai_id", ""),
            display_name=data.get("display_name", ""),
            original_name=data.get("original_name", ""),
            personality=data.get("personality", ""),
            avatar=data.get("avatar", "🤖"),
            tags=data.get("tags", []),
            current_emotion=data.get("current_emotion", EmotionalState.NEUTRAL.value),
            emotion_intensity=data.get("emotion_intensity", 0.5),
            mood_history=data.get("mood_history", []),
            max_history_size=data.get("max_history_size", 1000),
            relationships=data.get("relationships", {}),
            memories=data.get("memories", []),
            custom_traits=data.get("custom_traits", {}),
            model=data.get("model"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 500),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_active=data.get("last_active", datetime.now().isoformat())
        )
        state.chat_history = [
            ChatHistoryEntry.from_dict(h) 
            for h in data.get("chat_history", [])
        ]
        return state


class AIStateManager:
    """Manages persistent state for all AI personalities."""
    
    def __init__(self, storage_dir: Path = None):
        """
        Initialize the state manager.
        
        Args:
            storage_dir: Directory to store state files (defaults to Documents/AIChat)
        """
        self.storage_dir = storage_dir or STORAGE_DIR
        self._ensure_storage_dir()
        self._states: Dict[str, AIState] = {}
        self._private_conversations: Dict[str, PrivateConversation] = {}
        self._settings: Dict[str, Any] = {}
        self._load_all()
    
    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "ai_states").mkdir(exist_ok=True)
        (self.storage_dir / "private_chats").mkdir(exist_ok=True)
    
    def _get_state_file(self, ai_id: str) -> Path:
        """Get the state file path for an AI."""
        return self.storage_dir / "ai_states" / f"{ai_id}.json"
    
    def _get_conversation_file(self, conv_id: str) -> Path:
        """Get the conversation file path."""
        return self.storage_dir / "private_chats" / f"{conv_id}.json"
    
    def _get_settings_file(self) -> Path:
        """Get the settings file path."""
        return self.storage_dir / "settings.json"
    
    def _load_all(self) -> None:
        """Load all saved states and conversations."""
        # Load AI states
        states_dir = self.storage_dir / "ai_states"
        if states_dir.exists():
            for state_file in states_dir.glob("*.json"):
                try:
                    with open(state_file, 'r') as f:
                        data = json.load(f)
                    state = AIState.from_dict(data)
                    self._states[state.ai_id] = state
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not load state from {state_file}: {e}")
        
        # Load private conversations
        chats_dir = self.storage_dir / "private_chats"
        if chats_dir.exists():
            for chat_file in chats_dir.glob("*.json"):
                try:
                    with open(chat_file, 'r') as f:
                        data = json.load(f)
                    conv = PrivateConversation.from_dict(data)
                    self._private_conversations[conv.conversation_id] = conv
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not load conversation from {chat_file}: {e}")
        
        # Load settings
        settings_file = self._get_settings_file()
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, KeyError):
                self._settings = {}
    
    def save_state(self, state: AIState) -> bool:
        """
        Save an AI state to disk.
        
        Args:
            state: The AI state to save
            
        Returns:
            True if saved successfully
        """
        try:
            file_path = self._get_state_file(state.ai_id)
            with open(file_path, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            self._states[state.ai_id] = state
            return True
        except Exception as e:
            logger.error(f"Error saving state for {state.ai_id}: {e}")
            return False
    
    def save_all(self) -> None:
        """Save all states and conversations."""
        for state in self._states.values():
            self.save_state(state)
        
        for conv in self._private_conversations.values():
            self.save_conversation(conv)
        
        self.save_settings()
    
    def get_state(self, ai_id: str) -> Optional[AIState]:
        """Get an AI state by ID."""
        return self._states.get(ai_id)
    
    def create_state(
        self, 
        ai_id: str, 
        display_name: str, 
        personality: str,
        avatar: str = "🤖",
        tags: List[str] = None,
        model: str = None
    ) -> AIState:
        """
        Create a new AI state.
        
        Args:
            ai_id: Unique identifier
            display_name: Display name
            personality: Personality description
            avatar: Emoji avatar
            tags: Category tags
            model: LLM model
            
        Returns:
            The created AIState
        """
        state = AIState(
            ai_id=ai_id,
            display_name=display_name,
            original_name=display_name,
            personality=personality,
            avatar=avatar,
            tags=tags or [],
            model=model
        )
        self._states[ai_id] = state
        self.save_state(state)
        return state
    
    def delete_state(self, ai_id: str) -> bool:
        """
        Delete an AI state.
        
        Args:
            ai_id: The AI ID to delete
            
        Returns:
            True if deleted
        """
        if ai_id not in self._states:
            return False
        
        del self._states[ai_id]
        
        file_path = self._get_state_file(ai_id)
        if file_path.exists():
            file_path.unlink()
        
        return True
    
    def list_states(self, active_only: bool = False) -> List[AIState]:
        """List all AI states."""
        states = list(self._states.values())
        if active_only:
            return [s for s in states if s.is_active]
        return states
    
    def list_active_ai_ids(self) -> List[str]:
        """List IDs of active AIs."""
        return [s.ai_id for s in self._states.values() if s.is_active]
    
    def set_active(self, ai_id: str, active: bool) -> bool:
        """
        Set whether an AI is active in the chat room.
        
        Args:
            ai_id: The AI ID
            active: Whether to activate or deactivate
            
        Returns:
            True if changed
        """
        state = self._states.get(ai_id)
        if not state:
            return False
        
        state.is_active = active
        self.save_state(state)
        return True
    
    def rename_ai(self, ai_id: str, new_name: str) -> bool:
        """
        Rename an AI.
        
        Args:
            ai_id: The AI ID
            new_name: New display name
            
        Returns:
            True if renamed
        """
        state = self._states.get(ai_id)
        if not state:
            return False
        
        state.rename(new_name)
        self.save_state(state)
        return True
    
    # Private conversation management
    def get_or_create_conversation(self, participant_a: str, participant_b: str) -> PrivateConversation:
        """
        Get or create a private conversation between two participants.
        
        Args:
            participant_a: First participant
            participant_b: Second participant
            
        Returns:
            The PrivateConversation
        """
        # Create temporary conversation to get ID
        temp = PrivateConversation(participant_a=participant_a, participant_b=participant_b)
        conv_id = temp.conversation_id
        
        if conv_id in self._private_conversations:
            return self._private_conversations[conv_id]
        
        self._private_conversations[conv_id] = temp
        self.save_conversation(temp)
        return temp
    
    def save_conversation(self, conversation: PrivateConversation) -> bool:
        """Save a private conversation."""
        try:
            file_path = self._get_conversation_file(conversation.conversation_id)
            with open(file_path, 'w') as f:
                json.dump(conversation.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False
    
    def get_conversations_for(self, participant: str) -> List[PrivateConversation]:
        """Get all private conversations involving a participant."""
        return [
            conv for conv in self._private_conversations.values()
            if conv.participant_a == participant or conv.participant_b == participant
        ]
    
    def add_private_message(
        self, 
        from_participant: str, 
        to_participant: str, 
        content: str
    ) -> PrivateConversation:
        """
        Add a message to a private conversation.
        
        Args:
            from_participant: Sender
            to_participant: Recipient
            content: Message content
            
        Returns:
            The conversation
        """
        conv = self.get_or_create_conversation(from_participant, to_participant)
        conv.add_message(from_participant, content)
        self.save_conversation(conv)
        
        # Also add to AI state history if applicable
        from_state = self._states.get(from_participant.lower())
        to_state = self._states.get(to_participant.lower())
        
        if from_state:
            from_state.add_chat_entry(
                from_participant, content, 
                is_private=True, private_with=to_participant
            )
            self.save_state(from_state)
        
        if to_state:
            to_state.add_chat_entry(
                from_participant, content, 
                is_private=True, private_with=from_participant
            )
            self.save_state(to_state)
        
        return conv
    
    # Settings management
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._settings[key] = value
        self.save_settings()
    
    def save_settings(self) -> bool:
        """Save settings to disk."""
        try:
            with open(self._get_settings_file(), 'w') as f:
                json.dump(self._settings, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get_active_personality_names(self) -> Dict[str, str]:
        """Get mapping of ai_id to display_name for active AIs."""
        return {
            state.ai_id: state.display_name 
            for state in self._states.values() 
            if state.is_active
        }
    
    def export_all(self) -> Dict[str, Any]:
        """Export all data for backup."""
        return {
            "states": {ai_id: state.to_dict() for ai_id, state in self._states.items()},
            "conversations": {
                conv_id: conv.to_dict() 
                for conv_id, conv in self._private_conversations.items()
            },
            "settings": self._settings,
            "exported_at": datetime.now().isoformat()
        }
    
    def import_all(self, data: Dict[str, Any]) -> bool:
        """Import data from backup."""
        try:
            # Import states
            for ai_id, state_data in data.get("states", {}).items():
                state = AIState.from_dict(state_data)
                self._states[ai_id] = state
                self.save_state(state)
            
            # Import conversations
            for conv_id, conv_data in data.get("conversations", {}).items():
                conv = PrivateConversation.from_dict(conv_data)
                self._private_conversations[conv.conversation_id] = conv
                self.save_conversation(conv)
            
            # Import settings
            self._settings.update(data.get("settings", {}))
            self.save_settings()
            
            return True
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False


# Global state manager instance
_state_manager: Optional[AIStateManager] = None


def get_state_manager() -> AIStateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = AIStateManager()
    return _state_manager


def initialize_state_manager(storage_dir: Path = None) -> AIStateManager:
    """Initialize or reinitialize the state manager."""
    global _state_manager
    _state_manager = AIStateManager(storage_dir)
    return _state_manager
