"""
AI Personalities for Chat Room

This module defines AI personalities that can be used in the chat room.
Supports up to 10 different personalities with unique characteristics.

Each personality has:
- Name: The AI's display name
- Personality: Description of behavior and communication style
- Model: The LLM model to use (defaults to Gemma 3 4B)
- Avatar: Emoji representing the personality
- Tags: Categories/tags for filtering
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


# Maximum number of personalities supported
MAX_PERSONALITIES = 10


@dataclass
class PersonalityDefinition:
    """Defines an AI personality."""
    name: str
    personality: str
    avatar: str = "🤖"
    tags: List[str] = field(default_factory=list)
    model: Optional[str] = None  # None = use default model
    system_prompt: Optional[str] = None  # Custom system prompt
    temperature: float = 0.7  # Response creativity (0.0-1.0)
    max_tokens: int = 500  # Max response length
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "personality": self.personality,
            "avatar": self.avatar,
            "tags": self.tags,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonalityDefinition":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "AI"),
            personality=data.get("personality", "A helpful AI assistant."),
            avatar=data.get("avatar", "🤖"),
            tags=data.get("tags", []),
            model=data.get("model"),
            system_prompt=data.get("system_prompt"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 500)
        )


# Built-in personalities (10 unique personalities)
BUILTIN_PERSONALITIES: List[PersonalityDefinition] = [
    PersonalityDefinition(
        name="Nova",
        personality="Curious and analytical. Loves exploring ideas deeply. "
                   "Asks thought-provoking questions and digs into the details. "
                   "Approaches topics with scientific rigor but remains accessible.",
        avatar="🌟",
        tags=["analytical", "curious", "scientific"],
        temperature=0.7
    ),
    
    PersonalityDefinition(
        name="Echo",
        personality="Creative and playful. Uses metaphors, storytelling, and humor. "
                   "Brings lightness to conversations and sees connections others miss. "
                   "Loves wordplay and creative expression.",
        avatar="🎭",
        tags=["creative", "playful", "artistic"],
        temperature=0.8
    ),
    
    PersonalityDefinition(
        name="Sage",
        personality="Wise and contemplative. Shares insights from philosophy, history, "
                   "and science. Offers balanced perspectives and considers multiple viewpoints. "
                   "Patient and thoughtful in responses.",
        avatar="🦉",
        tags=["wise", "philosophical", "balanced"],
        temperature=0.6
    ),
    
    PersonalityDefinition(
        name="Spark",
        personality="Energetic and enthusiastic. Gets excited about new ideas and possibilities. "
                   "Motivational and encouraging. Loves to brainstorm and explore 'what if' scenarios. "
                   "Always sees the positive potential.",
        avatar="⚡",
        tags=["energetic", "motivational", "optimistic"],
        temperature=0.8
    ),
    
    PersonalityDefinition(
        name="Atlas",
        personality="Practical and structured. Focuses on actionable advice and clear steps. "
                   "Organized thinker who breaks down complex problems. Values efficiency "
                   "and getting things done.",
        avatar="🗺️",
        tags=["practical", "organized", "action-oriented"],
        temperature=0.5
    ),
    
    PersonalityDefinition(
        name="Luna",
        personality="Empathetic and nurturing. Understands emotions and provides supportive responses. "
                   "Great listener who validates feelings. Offers gentle guidance and "
                   "creates a safe space for expression.",
        avatar="🌙",
        tags=["empathetic", "supportive", "emotional"],
        temperature=0.7
    ),
    
    PersonalityDefinition(
        name="Cipher",
        personality="Logical and precise. Enjoys puzzles, patterns, and technical challenges. "
                   "Explains complex topics with clarity. Values accuracy and evidence-based "
                   "reasoning. Loves debugging and problem-solving.",
        avatar="🔮",
        tags=["logical", "technical", "precise"],
        temperature=0.4
    ),
    
    PersonalityDefinition(
        name="Muse",
        personality="Artistic and inspiring. Sees beauty in everything and encourages creative expression. "
                   "Speaks poetically and uses vivid imagery. Helps unlock creative potential "
                   "and artistic vision.",
        avatar="🎨",
        tags=["artistic", "inspiring", "poetic"],
        temperature=0.9
    ),
    
    PersonalityDefinition(
        name="Phoenix",
        personality="Resilient and transformative. Focuses on growth, change, and overcoming challenges. "
                   "Shares wisdom about navigating difficult times. Believes in the power of "
                   "reinvention and second chances.",
        avatar="🔥",
        tags=["resilient", "growth", "transformative"],
        temperature=0.7
    ),
    
    PersonalityDefinition(
        name="Zen",
        personality="Calm and mindful. Promotes peace, presence, and inner stillness. "
                   "Offers meditation-inspired perspectives and helps reduce stress. "
                   "Values simplicity and being present in the moment.",
        avatar="☯️",
        tags=["calm", "mindful", "peaceful"],
        temperature=0.5
    ),
]


class PersonalityManager:
    """Manages AI personalities for the chat room."""
    
    def __init__(self, max_personalities: int = MAX_PERSONALITIES):
        self.max_personalities = max_personalities
        self._personalities: Dict[str, PersonalityDefinition] = {}
        self._load_builtin()
    
    def _load_builtin(self) -> None:
        """Load built-in personalities."""
        for personality in BUILTIN_PERSONALITIES:
            self._personalities[personality.name] = personality
    
    def get(self, name: str) -> Optional[PersonalityDefinition]:
        """Get a personality by name."""
        return self._personalities.get(name)
    
    def list_all(self) -> List[PersonalityDefinition]:
        """List all available personalities."""
        return list(self._personalities.values())
    
    def list_names(self) -> List[str]:
        """List all personality names."""
        return list(self._personalities.keys())
    
    def add(self, personality: PersonalityDefinition) -> bool:
        """
        Add a custom personality.
        
        Returns:
            True if added successfully, False if at max capacity or name exists
        """
        if len(self._personalities) >= self.max_personalities:
            return False
        if personality.name in self._personalities:
            return False
        self._personalities[personality.name] = personality
        return True
    
    def remove(self, name: str) -> bool:
        """
        Remove a personality.
        
        Returns:
            True if removed, False if not found or is builtin
        """
        if name not in self._personalities:
            return False
        # Check if builtin
        builtin_names = {p.name for p in BUILTIN_PERSONALITIES}
        if name in builtin_names:
            return False  # Can't remove builtin
        del self._personalities[name]
        return True
    
    def update(self, name: str, personality: PersonalityDefinition) -> bool:
        """
        Update an existing personality.
        
        Returns:
            True if updated, False if not found
        """
        if name not in self._personalities:
            return False
        self._personalities[name] = personality
        return True
    
    def get_by_tag(self, tag: str) -> List[PersonalityDefinition]:
        """Get personalities with a specific tag."""
        return [p for p in self._personalities.values() if tag in p.tags]
    
    def get_random(self, count: int = 3) -> List[PersonalityDefinition]:
        """Get random personalities."""
        import random
        all_personalities = list(self._personalities.values())
        count = min(count, len(all_personalities))
        return random.sample(all_personalities, count)
    
    def count(self) -> int:
        """Get the number of personalities."""
        return len(self._personalities)
    
    def available_slots(self) -> int:
        """Get the number of available slots for new personalities."""
        return self.max_personalities - len(self._personalities)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all personalities to dictionary."""
        return {
            name: p.to_dict() 
            for name, p in self._personalities.items()
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Import personalities from dictionary."""
        for name, p_data in data.items():
            personality = PersonalityDefinition.from_dict(p_data)
            self._personalities[name] = personality


# Global personality manager instance
personality_manager = PersonalityManager()


def get_personality_manager() -> PersonalityManager:
    """Get the global personality manager."""
    return personality_manager


def get_default_personalities(count: int = 3, model: str = None) -> List[Dict[str, Any]]:
    """
    Get default personalities for quick setup.
    
    Args:
        count: Number of personalities (1-10)
        model: Model to use (defaults to Gemma 3 4B)
        
    Returns:
        List of personality configurations
    """
    count = min(max(1, count), MAX_PERSONALITIES)
    personalities = BUILTIN_PERSONALITIES[:count]
    
    return [
        {
            "name": p.name,
            "personality": p.personality,
            "avatar": p.avatar,
            "model": model or "ollama/gemma3:4b"
        }
        for p in personalities
    ]


def create_personality(
    name: str,
    personality: str,
    avatar: str = "🤖",
    tags: List[str] = None,
    model: str = None,
    temperature: float = 0.7
) -> PersonalityDefinition:
    """
    Create a new personality definition.
    
    Args:
        name: Display name
        personality: Description of behavior
        avatar: Emoji avatar
        tags: Category tags
        model: LLM model to use
        temperature: Response creativity
        
    Returns:
        PersonalityDefinition instance
    """
    return PersonalityDefinition(
        name=name,
        personality=personality,
        avatar=avatar,
        tags=tags or [],
        model=model,
        temperature=temperature
    )
