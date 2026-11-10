import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from masg.models import Decision
from masg.policy import evaluate_files, load_request
from masg.replay import ReplayStore

ROOT = Path(__file__).resolve().parents[1]


class ReplayTests(unittest.TestCase):
    def test_first_request_allowed_second_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "replay.sqlite3"
            first = evaluate_files(ROOT / "examples/policy.json", ROOT / "examples/request.json", replay_db=database)
            second = evaluate_files(ROOT / "examples/policy.json", ROOT / "examples/request.json", replay_db=database)
            self.assertEqual(first.decision, Decision.ALLOW)
            self.assertEqual(second.reason_code, "REPLAY_DETECTED")

    def test_replay_database_persists_across_store_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "replay.sqlite3"
            request = load_request(ROOT / "examples/request.json")
            self.assertTrue(ReplayStore(database).consume(request))
            self.assertFalse(ReplayStore(database).consume(request))

    def test_concurrent_consumption_has_exactly_one_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "replay.sqlite3"
            request = load_request(ROOT / "examples/request.json")
            barrier = threading.Barrier(8)
            def consume(_):
                barrier.wait()
                return ReplayStore(database).consume(request)
            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(consume, range(8)))
            self.assertEqual(sum(outcomes), 1)

    def test_different_request_ids_are_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ReplayStore(Path(directory) / "replay.sqlite3")
            request = load_request(ROOT / "examples/request.json")
            self.assertTrue(store.consume(request))
            self.assertTrue(store.consume({**request, "request_id": "another-id"}))


if __name__ == "__main__":
    unittest.main()
