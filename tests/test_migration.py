import pytest
import json
import sqlite3
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_state import AIStateManager, AIState, ChatHistoryEntry

class TestMigration:
    @pytest.fixture
    def temp_storage(self, tmp_path):
        return tmp_path

    def test_migrate_from_files(self, temp_storage):
        # 1. Setup legacy data
        states_dir = temp_storage / "ai_states"
        states_dir.mkdir(parents=True)

        legacy_data = {
            "ai_id": "legacy_bot",
            "display_name": "Legacy Bot",
            "chat_history": [
                {
                    "timestamp": "2024-01-01T10:00:00",
                    "sender": "User",
                    "content": "Old message"
                },
                {
                    "timestamp": "2024-01-01T10:01:00",
                    "sender": "Legacy Bot",
                    "content": "Old reply"
                }
            ],
            "current_emotion": "neutral",
            "relationships": {},
            "mood_history": [],
            "memories": []
        }

        with open(states_dir / "legacy_bot.json", 'w') as f:
            json.dump(legacy_data, f)

        # 2. Initialize manager
        # This should trigger migration once implemented
        manager = AIStateManager(storage_dir=temp_storage)

        # Manually call migrate for now if not yet in init (but plan implies I add it)
        # Assuming I will add it to __init__ or call it.
        # If the test runs before implementation, it fails.
        if hasattr(manager, '_migrate_from_files'):
            manager._migrate_from_files()

        # 3. Verify DB
        conn = sqlite3.connect(temp_storage / "ai_data.db")
        cursor = conn.cursor()

        # Check metadata
        cursor.execute("SELECT data FROM ai_states WHERE ai_id=?", ("legacy_bot",))
        row = cursor.fetchone()

        # If migration not implemented, this assertion fails
        if row is None:
            pytest.fail("Migration did not populate ai_states table")

        data = json.loads(row[0])
        assert data["display_name"] == "Legacy Bot"
        # chat_history might be present but empty if to_dict logic excludes it,
        # or it might be excluded. My implementation of to_dict excludes it if include_history=False.
        # But migration logic needs to call to_dict(include_history=False).
        assert "chat_history" not in data or len(data.get("chat_history", [])) == 0

        # Check history
        cursor.execute("SELECT count(*) FROM chat_history WHERE ai_id=?", ("legacy_bot",))
        count = cursor.fetchone()[0]
        assert count == 2

        cursor.execute("SELECT content FROM chat_history WHERE ai_id=? ORDER BY timestamp", ("legacy_bot",))
        rows = cursor.fetchall()
        assert rows[0][0] == "Old message"
        assert rows[1][0] == "Old reply"

        conn.close()

        # 4. Verify file renamed
        assert not (states_dir / "legacy_bot.json").exists()
        assert (states_dir / "legacy_bot.json.migrated").exists()
