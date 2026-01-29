import time
import tempfile
import json
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_state import AIStateManager, AIState, ChatHistoryEntry

def run_benchmark():
    print("Running save_state benchmark...")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        manager = AIStateManager(storage_dir=storage_dir)

        # Create an AI state
        state = manager.create_state(
            ai_id="benchmark_ai",
            display_name="Benchmark Bot",
            personality="Performance Tester"
        )

        sizes = [10, 100, 1000, 5000, 10000]
        results = {}

        print("\n--- Bulk Save (Initial) ---")
        for size in sizes:
            # Populate chat history (resetting each time to control exact size)
            state.chat_history = []
            state.max_history_size = size + 100

            for i in range(size):
                state.add_chat_entry(
                    sender="User" if i % 2 == 0 else "Bot",
                    content=f"This is message number {i} with some content to simulate real messages."
                )

            # Measure save time
            start_time = time.time()
            manager.save_state(state)
            end_time = time.time()

            duration = (end_time - start_time) * 1000 # ms
            results[size] = duration
            print(f"Size: {size} messages -> {duration:.2f} ms")

            # Verify file size (if using file backend)
            file_path = storage_dir / "ai_states" / "benchmark_ai.json"
            if file_path.exists():
                file_size = file_path.stat().st_size / 1024 # KB
                print(f"File size: {file_size:.2f} KB")
            else:
                # Check for DB file if we switch to DB
                db_path = storage_dir / "ai_data.db"
                if db_path.exists():
                    file_size = db_path.stat().st_size / 1024
                    print(f"DB size: {file_size:.2f} KB")

        print("\n--- Incremental Save (Add 1 msg) ---")
        # Reuse state with 10000 messages
        # Current state has 10000 messages and is saved in DB.

        # Add 1 message
        state.add_chat_entry("User", "New message")

        start_time = time.time()
        manager.save_state(state)
        end_time = time.time()

        duration = (end_time - start_time) * 1000
        print(f"Append 1 msg to {len(state.chat_history)} -> {duration:.2f} ms")

if __name__ == "__main__":
    run_benchmark()
