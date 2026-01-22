"""
Sample Add-on for AI Chat Room

This is a sample add-on that demonstrates how to:
1. Create custom tools for AI participants
2. Add new AI personalities
3. Register custom commands
4. Hook into message events
"""

import random
from typing import Any, Callable, Dict, List, Optional

# Import from parent package using try/except for robustness
try:
    from addons import AddonBase, AddonMetadata
except ImportError:
    import sys
    import os
    # Fallback path resolution
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from addons import AddonBase, AddonMetadata


# Constants for validation limits
MAX_DICE_COUNT = 100
MAX_DICE_SIDES = 1000


class SampleAddon(AddonBase):
    """Sample add-on demonstrating extensibility."""
    
    def __init__(self, metadata: AddonMetadata):
        super().__init__(metadata)
        self.fortune_messages = [
            "The stars align in your favor today!",
            "A pleasant surprise awaits you.",
            "Your creativity will lead to success.",
            "Trust your instincts - they're spot on.",
            "An exciting opportunity is coming your way.",
        ]
    
    def on_load(self) -> bool:
        """Called when the add-on is loaded."""
        print(f"[{self.metadata.name}] Loading...")
        self._loaded = True
        return True
    
    def on_unload(self) -> bool:
        """Called when the add-on is unloaded."""
        print(f"[{self.metadata.name}] Unloading...")
        self._loaded = False
        return True
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return custom tools provided by this add-on."""
        return [
            {
                "name": "fortune",
                "description": "Get a random fortune/prediction",
                "parameters": {},
                "function": self._fortune_tool,
                "category": "fun"
            },
            {
                "name": "roll_dice",
                "description": "Roll dice (e.g., 2d6 for two six-sided dice)",
                "parameters": {
                    "dice": {
                        "type": "string",
                        "description": "Dice notation like '2d6' or '1d20'",
                        "required": True
                    }
                },
                "function": self._roll_dice_tool,
                "category": "fun"
            },
            {
                "name": "flip_coin",
                "description": "Flip a coin",
                "parameters": {},
                "function": self._flip_coin_tool,
                "category": "fun"
            }
        ]
    
    def get_personalities(self) -> List[Dict[str, Any]]:
        """Return custom AI personalities."""
        return [
            {
                "name": "Oracle",
                "personality": "Mystical and enigmatic. Speaks in riddles and metaphors. "
                             "Offers cryptic but insightful advice.",
                "model": None  # Uses default model
            }
        ]
    
    def get_commands(self) -> Dict[str, Callable]:
        """Return custom chat commands."""
        return {
            "/fortune": self._cmd_fortune,
            "/roll": self._cmd_roll,
            "/flip": self._cmd_flip,
        }
    
    def on_message(self, sender: str, content: str) -> Optional[str]:
        """Hook called for each message."""
        # Example: Auto-respond to greetings
        greetings = ["hello", "hi", "hey", "greetings"]
        if any(g in content.lower() for g in greetings):
            # Could modify message or trigger side effects
            pass
        return None  # Return None to not modify
    
    # Tool implementations
    def _fortune_tool(self) -> Dict[str, Any]:
        """Get a random fortune."""
        fortune = random.choice(self.fortune_messages)
        return {"success": True, "output": f"🔮 {fortune}"}
    
    def _roll_dice_tool(self, dice: str) -> Dict[str, Any]:
        """Roll dice based on notation."""
        try:
            parts = dice.lower().split('d')
            if len(parts) != 2:
                return {"success": False, "output": None, "error": "Invalid dice notation. Use format like '2d6'"}
            
            num_dice = int(parts[0]) if parts[0] else 1
            num_sides = int(parts[1])
            
            if num_dice < 1 or num_dice > MAX_DICE_COUNT:
                return {"success": False, "output": None, "error": f"Number of dice must be 1-{MAX_DICE_COUNT}"}
            if num_sides < 2 or num_sides > MAX_DICE_SIDES:
                return {"success": False, "output": None, "error": f"Dice sides must be 2-{MAX_DICE_SIDES}"}
            
            rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(rolls)
            
            return {
                "success": True, 
                "output": f"🎲 Rolled {dice}: {rolls} = {total}"
            }
        except ValueError:
            return {"success": False, "output": None, "error": "Invalid dice notation"}
    
    def _flip_coin_tool(self) -> Dict[str, Any]:
        """Flip a coin."""
        result = random.choice(["Heads", "Tails"])
        return {"success": True, "output": f"🪙 {result}!"}
    
    # Command implementations
    def _cmd_fortune(self, args: str = "") -> str:
        """Fortune command handler."""
        result = self._fortune_tool()
        return result["output"]
    
    def _cmd_roll(self, args: str = "1d6") -> str:
        """Roll command handler."""
        dice = args.strip() if args.strip() else "1d6"
        result = self._roll_dice_tool(dice)
        if result["success"]:
            return result["output"]
        return f"❌ {result['error']}"
    
    def _cmd_flip(self, args: str = "") -> str:
        """Flip command handler."""
        result = self._flip_coin_tool()
        return result["output"]
