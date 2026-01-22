"""
Add-on System for AI Chat Room

This module provides a plugin/add-on architecture that allows extending
the AI Chat Room with custom functionality. Add-ons can provide:
- Custom tools for AI participants
- Custom AI personalities
- UI extensions
- Integration with external services

Add-ons are loaded from the 'addons' directory and can be installed
via the add-on manager.
"""

import importlib
import importlib.util
import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


@dataclass
class AddonMetadata:
    """Metadata for an add-on."""
    id: str
    name: str
    version: str
    description: str
    author: str
    homepage: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    min_app_version: str = "0.1.0"
    permissions: List[str] = field(default_factory=list)
    enabled: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AddonMetadata":
        """Create metadata from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "0.0.1"),
            description=data.get("description", ""),
            author=data.get("author", "Unknown"),
            homepage=data.get("homepage"),
            dependencies=data.get("dependencies", []),
            min_app_version=data.get("min_app_version", "0.1.0"),
            permissions=data.get("permissions", []),
            enabled=data.get("enabled", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "dependencies": self.dependencies,
            "min_app_version": self.min_app_version,
            "permissions": self.permissions,
            "enabled": self.enabled
        }


class AddonBase(ABC):
    """Base class for all add-ons."""
    
    def __init__(self, metadata: AddonMetadata):
        self.metadata = metadata
        self._loaded = False
    
    @abstractmethod
    def on_load(self) -> bool:
        """Called when the add-on is loaded. Return True if successful."""
        pass
    
    @abstractmethod
    def on_unload(self) -> bool:
        """Called when the add-on is unloaded. Return True if successful."""
        pass
    
    def on_enable(self) -> bool:
        """Called when the add-on is enabled."""
        return True
    
    def on_disable(self) -> bool:
        """Called when the add-on is disabled."""
        return True
    
    def get_tools(self) -> List[Any]:
        """Return list of tools provided by this add-on."""
        return []
    
    def get_personalities(self) -> List[Dict[str, Any]]:
        """Return list of AI personalities provided by this add-on."""
        return []
    
    def get_commands(self) -> Dict[str, Callable]:
        """Return dict of chat commands provided by this add-on."""
        return {}
    
    def on_message(self, sender: str, content: str) -> Optional[str]:
        """Called for each message. Can return a modified message or None."""
        return None
    
    def on_ai_response(self, ai_name: str, response: str) -> Optional[str]:
        """Called for each AI response. Can return a modified response or None."""
        return None


class AddonManager:
    """Manages loading, unloading, and execution of add-ons."""
    
    def __init__(self, addons_dir: Optional[str] = None):
        """
        Initialize the add-on manager.
        
        Args:
            addons_dir: Directory containing add-ons. Defaults to './addons'
        """
        if addons_dir:
            self.addons_dir = Path(addons_dir)
        else:
            self.addons_dir = Path(__file__).parent / "addons"
        
        self.addons: Dict[str, AddonBase] = {}
        self.metadata: Dict[str, AddonMetadata] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "on_message": [],
            "on_ai_response": [],
            "on_tool_call": [],
            "on_document_upload": [],
        }
    
    def discover_addons(self) -> List[AddonMetadata]:
        """Discover all available add-ons in the addons directory."""
        discovered = []
        
        if not self.addons_dir.exists():
            self.addons_dir.mkdir(parents=True, exist_ok=True)
            return discovered
        
        for item in self.addons_dir.iterdir():
            if item.is_dir():
                manifest_path = item / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            data = json.load(f)
                        metadata = AddonMetadata.from_dict(data)
                        metadata.id = item.name  # Use directory name as ID
                        discovered.append(metadata)
                    except Exception as e:
                        print(f"Error loading manifest for {item.name}: {e}")
        
        return discovered
    
    def load_addon(self, addon_id: str) -> bool:
        """
        Load an add-on by its ID.
        
        Args:
            addon_id: The add-on identifier (directory name)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if addon_id in self.addons:
            return True  # Already loaded
        
        addon_path = self.addons_dir / addon_id
        if not addon_path.exists():
            print(f"Add-on not found: {addon_id}")
            return False
        
        manifest_path = addon_path / "manifest.json"
        if not manifest_path.exists():
            print(f"No manifest.json found for add-on: {addon_id}")
            return False
        
        try:
            # Load metadata
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            metadata = AddonMetadata.from_dict(data)
            metadata.id = addon_id
            
            # Load the add-on module
            main_file = addon_path / "__init__.py"
            if not main_file.exists():
                main_file = addon_path / "main.py"
            
            if not main_file.exists():
                print(f"No __init__.py or main.py found for add-on: {addon_id}")
                return False
            
            # Import the module
            spec = importlib.util.spec_from_file_location(
                f"addons.{addon_id}", 
                main_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"addons.{addon_id}"] = module
            spec.loader.exec_module(module)
            
            # Find the addon class
            addon_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, AddonBase) and 
                    obj is not AddonBase):
                    addon_class = obj
                    break
            
            if not addon_class:
                print(f"No AddonBase subclass found in add-on: {addon_id}")
                return False
            
            # Instantiate and load
            addon = addon_class(metadata)
            if addon.on_load():
                self.addons[addon_id] = addon
                self.metadata[addon_id] = metadata
                self._register_hooks(addon)
                print(f"✅ Loaded add-on: {metadata.name} v{metadata.version}")
                return True
            else:
                print(f"Add-on failed to load: {addon_id}")
                return False
                
        except Exception as e:
            print(f"Error loading add-on {addon_id}: {e}")
            return False
    
    def unload_addon(self, addon_id: str) -> bool:
        """
        Unload an add-on.
        
        Args:
            addon_id: The add-on identifier
            
        Returns:
            True if unloaded successfully
        """
        if addon_id not in self.addons:
            return True
        
        addon = self.addons[addon_id]
        try:
            if addon.on_unload():
                self._unregister_hooks(addon)
                del self.addons[addon_id]
                del self.metadata[addon_id]
                return True
        except Exception as e:
            print(f"Error unloading add-on {addon_id}: {e}")
        
        return False
    
    def enable_addon(self, addon_id: str) -> bool:
        """Enable an add-on."""
        if addon_id in self.addons:
            addon = self.addons[addon_id]
            if addon.on_enable():
                addon.metadata.enabled = True
                return True
        return False
    
    def disable_addon(self, addon_id: str) -> bool:
        """Disable an add-on."""
        if addon_id in self.addons:
            addon = self.addons[addon_id]
            if addon.on_disable():
                addon.metadata.enabled = False
                return True
        return False
    
    def load_all(self) -> int:
        """Load all discovered add-ons. Returns count of loaded add-ons."""
        count = 0
        for metadata in self.discover_addons():
            if metadata.enabled and self.load_addon(metadata.id):
                count += 1
        return count
    
    def get_all_tools(self) -> List[Any]:
        """Get all tools from all loaded add-ons."""
        tools = []
        for addon in self.addons.values():
            if addon.metadata.enabled:
                tools.extend(addon.get_tools())
        return tools
    
    def get_all_personalities(self) -> List[Dict[str, Any]]:
        """Get all AI personalities from all loaded add-ons."""
        personalities = []
        for addon in self.addons.values():
            if addon.metadata.enabled:
                personalities.extend(addon.get_personalities())
        return personalities
    
    def get_all_commands(self) -> Dict[str, Callable]:
        """Get all commands from all loaded add-ons."""
        commands = {}
        for addon in self.addons.values():
            if addon.metadata.enabled:
                commands.update(addon.get_commands())
        return commands
    
    def _register_hooks(self, addon: AddonBase) -> None:
        """Register hooks for an add-on."""
        if hasattr(addon, 'on_message'):
            self._hooks["on_message"].append(addon.on_message)
        if hasattr(addon, 'on_ai_response'):
            self._hooks["on_ai_response"].append(addon.on_ai_response)
    
    def _unregister_hooks(self, addon: AddonBase) -> None:
        """Unregister hooks for an add-on."""
        for hook_name, hooks in self._hooks.items():
            method = getattr(addon, hook_name, None)
            if method and method in hooks:
                hooks.remove(method)
    
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """Trigger a hook and return results."""
        results = []
        for hook in self._hooks.get(hook_name, []):
            try:
                result = hook(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                print(f"Error in hook {hook_name}: {e}")
        return results
    
    def list_addons(self) -> List[Dict[str, Any]]:
        """List all add-ons with their status."""
        result = []
        for metadata in self.discover_addons():
            addon_info = metadata.to_dict()
            addon_info["loaded"] = metadata.id in self.addons
            result.append(addon_info)
        return result


# Global addon manager instance
addon_manager = AddonManager()


def get_addon_manager() -> AddonManager:
    """Get the global addon manager instance."""
    return addon_manager
