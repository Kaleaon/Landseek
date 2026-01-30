
import time
import timeit
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag import RAGManager, AIRAGStore, RetrievalResult

class MockAIRAGStore:
    def __init__(self, ai_id, delay=0.1):
        self.ai_id = ai_id
        self.delay = delay

    def retrieve(self, query, top_k=5):
        time.sleep(self.delay)
        return []

class BenchmarkRAGQuery(unittest.TestCase):
    def test_query_all_performance(self):
        manager = RAGManager()
        # Clear existing stores for benchmark
        manager._stores = {}

        # Create 10 stores, each taking 0.1s to retrieve
        num_stores = 10
        delay_per_store = 0.1

        for i in range(num_stores):
            ai_id = f"ai_{i}"
            manager._stores[ai_id] = MockAIRAGStore(ai_id, delay=delay_per_store)

        start_time = time.time()
        manager.query_all("test query")
        end_time = time.time()

        duration = end_time - start_time
        print(f"\nBenchmark Results:")
        print(f"Number of stores: {num_stores}")
        print(f"Delay per store: {delay_per_store}s")
        print(f"Total execution time: {duration:.4f}s")

        # In serial execution, time should be roughly num_stores * delay_per_store
        # In parallel execution, it should be roughly delay_per_store (plus overhead)

        expected_serial_time = num_stores * delay_per_store
        print(f"Expected serial time: ~{expected_serial_time:.4f}s")

        return duration

if __name__ == '__main__':
    unittest.main()
