"""Tests for personalities module."""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from personalities import (
    PersonalityDefinition, PersonalityManager,
    BUILTIN_PERSONALITIES, MAX_PERSONALITIES,
    get_personality_manager, get_default_personalities,
    create_personality
)


class TestPersonalityDefinition:
    """Tests for PersonalityDefinition class."""
    
    def test_create_personality(self):
        """Test creating a personality."""
        p = PersonalityDefinition(
            name="Test",
            personality="A test personality"
        )
        assert p.name == "Test"
        assert p.personality == "A test personality"
        assert p.avatar == "🤖"  # default
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        p = PersonalityDefinition(
            name="Test",
            personality="A test personality",
            avatar="🔥",
            tags=["test", "example"]
        )
        d = p.to_dict()
        assert d["name"] == "Test"
        assert d["personality"] == "A test personality"
        assert d["avatar"] == "🔥"
        assert "test" in d["tags"]
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        d = {
            "name": "Test",
            "personality": "A test personality",
            "avatar": "⭐",
            "temperature": 0.8
        }
        p = PersonalityDefinition.from_dict(d)
        assert p.name == "Test"
        assert p.avatar == "⭐"
        assert p.temperature == 0.8


class TestBuiltinPersonalities:
    """Tests for built-in personalities."""
    
    def test_builtin_count(self):
        """Test that there are 10 built-in personalities."""
        assert len(BUILTIN_PERSONALITIES) == 10
    
    def test_max_personalities(self):
        """Test max personalities constant."""
        assert MAX_PERSONALITIES == 10
    
    def test_builtin_names_unique(self):
        """Test that all built-in names are unique."""
        names = [p.name for p in BUILTIN_PERSONALITIES]
        assert len(names) == len(set(names))
    
    def test_builtin_have_avatars(self):
        """Test that all built-ins have avatars."""
        for p in BUILTIN_PERSONALITIES:
            assert p.avatar is not None
            assert len(p.avatar) > 0
    
    def test_builtin_have_tags(self):
        """Test that all built-ins have tags."""
        for p in BUILTIN_PERSONALITIES:
            assert len(p.tags) > 0
    
    def test_specific_personalities_exist(self):
        """Test that expected personalities exist."""
        names = [p.name for p in BUILTIN_PERSONALITIES]
        assert "Nova" in names
        assert "Echo" in names
        assert "Sage" in names
        assert "Spark" in names
        assert "Atlas" in names
        assert "Luna" in names
        assert "Cipher" in names
        assert "Muse" in names
        assert "Phoenix" in names
        assert "Zen" in names


class TestPersonalityManager:
    """Tests for PersonalityManager class."""
    
    def test_manager_loads_builtins(self):
        """Test that manager loads built-in personalities."""
        pm = PersonalityManager()
        assert pm.count() == 10
    
    def test_get_personality(self):
        """Test getting a personality by name."""
        pm = PersonalityManager()
        nova = pm.get("Nova")
        assert nova is not None
        assert nova.name == "Nova"
    
    def test_get_nonexistent(self):
        """Test getting non-existent personality."""
        pm = PersonalityManager()
        result = pm.get("NonExistent")
        assert result is None
    
    def test_list_all(self):
        """Test listing all personalities."""
        pm = PersonalityManager()
        all_p = pm.list_all()
        assert len(all_p) == 10
    
    def test_list_names(self):
        """Test listing personality names."""
        pm = PersonalityManager()
        names = pm.list_names()
        assert "Nova" in names
        assert "Sage" in names
    
    def test_add_personality(self):
        """Test adding a custom personality."""
        pm = PersonalityManager()
        # Remove a builtin to make room
        # Actually, we can't remove builtins, but we're at max
        # So this should fail
        custom = PersonalityDefinition(
            name="Custom",
            personality="A custom personality"
        )
        # At max capacity, should fail
        result = pm.add(custom)
        assert result is False
    
    def test_get_by_tag(self):
        """Test getting personalities by tag."""
        pm = PersonalityManager()
        analytical = pm.get_by_tag("analytical")
        assert len(analytical) > 0
        assert all("analytical" in p.tags for p in analytical)
    
    def test_get_random(self):
        """Test getting random personalities."""
        pm = PersonalityManager()
        random_p = pm.get_random(3)
        assert len(random_p) == 3
        # All should be unique
        names = [p.name for p in random_p]
        assert len(names) == len(set(names))
    
    def test_available_slots(self):
        """Test available slots calculation."""
        pm = PersonalityManager()
        # Already at max with builtins
        assert pm.available_slots() == 0
    
    def test_to_dict(self):
        """Test exporting to dictionary."""
        pm = PersonalityManager()
        d = pm.to_dict()
        assert "Nova" in d
        assert d["Nova"]["name"] == "Nova"


class TestGetPersonalityManager:
    """Tests for get_personality_manager function."""
    
    def test_returns_manager(self):
        """Test that function returns a manager."""
        pm = get_personality_manager()
        assert isinstance(pm, PersonalityManager)
    
    def test_returns_same_instance(self):
        """Test that function returns same instance."""
        pm1 = get_personality_manager()
        pm2 = get_personality_manager()
        assert pm1 is pm2


class TestGetDefaultPersonalities:
    """Tests for get_default_personalities function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        p = get_default_personalities()
        assert isinstance(p, list)
    
    def test_default_count(self):
        """Test default count is 3."""
        p = get_default_personalities()
        assert len(p) == 3
    
    def test_custom_count(self):
        """Test custom count."""
        p = get_default_personalities(count=5)
        assert len(p) == 5
    
    def test_max_count(self):
        """Test count is capped at max."""
        p = get_default_personalities(count=100)
        assert len(p) == MAX_PERSONALITIES
    
    def test_min_count(self):
        """Test count is at least 1."""
        p = get_default_personalities(count=0)
        assert len(p) == 1
    
    def test_custom_model(self):
        """Test custom model is applied."""
        p = get_default_personalities(model="custom/model")
        assert all(x["model"] == "custom/model" for x in p)


class TestCreatePersonality:
    """Tests for create_personality function."""
    
    def test_create_basic(self):
        """Test creating basic personality."""
        p = create_personality(
            name="Test",
            personality="Test personality"
        )
        assert p.name == "Test"
        assert p.personality == "Test personality"
    
    def test_create_with_options(self):
        """Test creating with all options."""
        p = create_personality(
            name="Test",
            personality="Test personality",
            avatar="🎯",
            tags=["test"],
            model="custom/model",
            temperature=0.9
        )
        assert p.avatar == "🎯"
        assert "test" in p.tags
        assert p.model == "custom/model"
        assert p.temperature == 0.9
