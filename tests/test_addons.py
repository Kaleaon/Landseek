"""Tests for add-on system."""

import pytest
import os
import sys
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from addons import (
    AddonBase, AddonMetadata, AddonManager,
    get_addon_manager
)


class TestAddonMetadata:
    """Tests for AddonMetadata class."""
    
    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "id": "test_addon",
            "name": "Test Add-on",
            "version": "1.0.0",
            "description": "A test add-on",
            "author": "Test Author"
        }
        metadata = AddonMetadata.from_dict(data)
        
        assert metadata.id == "test_addon"
        assert metadata.name == "Test Add-on"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test add-on"
        assert metadata.author == "Test Author"
    
    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = AddonMetadata(
            id="test_addon",
            name="Test Add-on",
            version="1.0.0",
            description="A test add-on",
            author="Test Author"
        )
        data = metadata.to_dict()
        
        assert data["id"] == "test_addon"
        assert data["name"] == "Test Add-on"
        assert data["version"] == "1.0.0"
    
    def test_default_values(self):
        """Test default values."""
        data = {"id": "minimal"}
        metadata = AddonMetadata.from_dict(data)
        
        assert metadata.dependencies == []
        assert metadata.permissions == []
        assert metadata.enabled is True


class TestAddonBase:
    """Tests for AddonBase class."""
    
    def test_concrete_implementation(self):
        """Test that AddonBase requires implementation."""
        metadata = AddonMetadata(
            id="test",
            name="Test",
            version="1.0.0",
            description="Test",
            author="Test"
        )
        
        # Create a concrete implementation
        class TestAddon(AddonBase):
            def on_load(self):
                return True
            
            def on_unload(self):
                return True
        
        addon = TestAddon(metadata)
        assert addon.on_load() is True
        assert addon.on_unload() is True
    
    def test_get_tools_default(self):
        """Test that get_tools returns empty list by default."""
        metadata = AddonMetadata(
            id="test",
            name="Test",
            version="1.0.0",
            description="Test",
            author="Test"
        )
        
        class TestAddon(AddonBase):
            def on_load(self):
                return True
            
            def on_unload(self):
                return True
        
        addon = TestAddon(metadata)
        assert addon.get_tools() == []
    
    def test_get_personalities_default(self):
        """Test that get_personalities returns empty list by default."""
        metadata = AddonMetadata(
            id="test",
            name="Test",
            version="1.0.0",
            description="Test",
            author="Test"
        )
        
        class TestAddon(AddonBase):
            def on_load(self):
                return True
            
            def on_unload(self):
                return True
        
        addon = TestAddon(metadata)
        assert addon.get_personalities() == []


class TestAddonManager:
    """Tests for AddonManager class."""
    
    def test_init_with_custom_dir(self):
        """Test initializing with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            assert str(manager.addons_dir) == tmpdir
    
    def test_discover_addons_empty(self):
        """Test discovering addons in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            addons = manager.discover_addons()
            assert addons == []
    
    def test_discover_addons_with_manifest(self):
        """Test discovering addons with manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an addon directory with manifest
            addon_dir = Path(tmpdir) / "test_addon"
            addon_dir.mkdir()
            
            manifest = {
                "id": "test_addon",
                "name": "Test Add-on",
                "version": "1.0.0",
                "description": "A test add-on",
                "author": "Test Author"
            }
            
            with open(addon_dir / "manifest.json", 'w') as f:
                json.dump(manifest, f)
            
            manager = AddonManager(addons_dir=tmpdir)
            addons = manager.discover_addons()
            
            assert len(addons) == 1
            assert addons[0].name == "Test Add-on"
    
    def test_list_addons(self):
        """Test listing addons."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            
            # Create an addon
            addon_dir = Path(tmpdir) / "test_addon"
            addon_dir.mkdir()
            
            manifest = {
                "id": "test_addon",
                "name": "Test Add-on",
                "version": "1.0.0",
                "description": "Test",
                "author": "Test"
            }
            
            with open(addon_dir / "manifest.json", 'w') as f:
                json.dump(manifest, f)
            
            addons = manager.list_addons()
            assert len(addons) == 1
            assert addons[0]["name"] == "Test Add-on"
            assert addons[0]["loaded"] is False
    
    def test_load_nonexistent_addon(self):
        """Test loading non-existent addon."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            result = manager.load_addon("nonexistent")
            assert result is False
    
    def test_get_all_tools_empty(self):
        """Test getting tools when no addons loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            tools = manager.get_all_tools()
            assert tools == []
    
    def test_get_all_personalities_empty(self):
        """Test getting personalities when no addons loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            personalities = manager.get_all_personalities()
            assert personalities == []
    
    def test_get_all_commands_empty(self):
        """Test getting commands when no addons loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            commands = manager.get_all_commands()
            assert commands == {}


class TestGetAddonManager:
    """Tests for get_addon_manager function."""
    
    def test_returns_manager(self):
        """Test that get_addon_manager returns an AddonManager."""
        manager = get_addon_manager()
        assert isinstance(manager, AddonManager)
    
    def test_returns_same_instance(self):
        """Test that get_addon_manager returns the same instance."""
        manager1 = get_addon_manager()
        manager2 = get_addon_manager()
        assert manager1 is manager2


class TestAddonHooks:
    """Tests for addon hooks."""
    
    def test_trigger_hook_empty(self):
        """Test triggering hook with no handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AddonManager(addons_dir=tmpdir)
            results = manager.trigger_hook("on_message", "User", "Hello")
            assert results == []
