import json
import os
import socket
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from masg.audit import verify_ledger
from masg.broker import ExecutionBroker, _ThreadedUnixServer, _RequestHandler, submit

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "posix" and hasattr(socket, "SO_PEERCRED"), "Linux peer credentials required")
class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.policy = self.root / "policy.json"
        self.principals = self.root / "principals.json"
        self.replay = self.root / "replay.sqlite3"
        self.ledger = self.root / "ledger.jsonl"
        self.principal = "service:masg-test"
        self.policy.write_text(json.dumps({
            "version": "broker-test-v1", "default_effect": "DENY",
            "rules": [{
                "id": "allow-audit-append", "principals": [self.principal],
                "actions": ["audit.append"], "targets": ["audit-ledger"],
                "scopes": ["append"], "effect": "ALLOW",
            }],
        }), encoding="utf-8")
        self.principals.write_text(json.dumps({str(os.getuid()): self.principal}), encoding="utf-8")
        self.broker = self.make_broker()
        now = datetime.now(timezone.utc)
        self.request = {
            "request_id": "broker-request-001",
            "issued_at": (now - timedelta(seconds=2)).isoformat(),
            "expires_at": (now + timedelta(minutes=2)).isoformat(),
            "event": {"kind": "test", "details": "authorized append"},
        }

    def make_broker(self):
        return ExecutionBroker(
            policy_path=self.policy, principal_map_path=self.principals,
            replay_db=self.replay, ledger_path=self.ledger,
        )

    def tearDown(self):
        self.temp.cleanup()

    def call(self, request=None, uid=None):
        return self.broker.process(
            json.dumps(self.request if request is None else request).encode(),
            os.getuid() if uid is None else uid,
        )

    def test_authorized_peer_executes_fixed_operation(self):
        result = self.call()
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["operation"], "audit.append")
        self.assertTrue(verify_ledger(self.ledger)["valid"])

    def test_second_use_of_request_id_denied(self):
        self.assertEqual(self.call()["decision"], "ALLOW")
        self.assertEqual(self.call()["reason_code"], "REPLAY_DETECTED")
        self.assertEqual(verify_ledger(self.ledger)["events"], 1)

    def test_unmapped_os_uid_denied(self):
        self.assertEqual(self.call(uid=os.getuid() + 100_000)["reason_code"], "CALLER_IDENTITY_UNMAPPED")

    def test_caller_cannot_supply_principal_or_operation(self):
        request = {**self.request, "principal": "service:admin", "action": "shell.exec"}
        self.assertEqual(self.call(request)["reason_code"], "REQUEST_SHAPE_INVALID")

    def test_caller_cannot_change_event_schema(self):
        request = {**self.request, "event": {"kind": "test", "details": "x", "path": "/etc/passwd"}}
        self.assertEqual(self.call(request)["reason_code"], "REQUEST_FIELDS_INVALID")

    def test_oversized_event_rejected(self):
        request = {**self.request, "event": {"kind": "test", "details": "x" * 4097}}
        self.assertEqual(self.call(request)["reason_code"], "REQUEST_FIELDS_INVALID")

    def test_duplicate_json_key_rejected(self):
        raw = b'{"request_id":"one","request_id":"two","issued_at":"2026-01-01T00:00:00Z","expires_at":"2099-01-01T00:00:00Z","event":{"kind":"x","details":"y"}}'
        self.assertEqual(self.broker.process(raw, os.getuid())["reason_code"], "REQUEST_INVALID")

    def test_long_validity_window_rejected(self):
        request = dict(self.request)
        request["expires_at"] = (datetime.fromisoformat(request["issued_at"]) + timedelta(hours=1)).isoformat()
        self.assertEqual(self.call(request)["reason_code"], "REQUEST_TTL_TOO_LONG")

    def test_denied_policy_does_not_write_ledger(self):
        self.policy.write_text(json.dumps({"version":"deny","default_effect":"DENY","rules":[]}), encoding="utf-8")
        broker = self.make_broker()
        self.assertEqual(broker.process(json.dumps(self.request).encode(), os.getuid())["decision"], "DENY")
        self.assertFalse(self.ledger.exists())

    def test_replay_store_failure_fails_closed(self):
        replay_dir = self.root / "not-a-database"
        replay_dir.mkdir()
        broker = ExecutionBroker(
            policy_path=self.policy, principal_map_path=self.principals,
            replay_db=replay_dir, ledger_path=self.ledger,
        )
        self.assertEqual(broker.process(json.dumps(self.request).encode(), os.getuid())["reason_code"], "REPLAY_STORE_UNAVAILABLE")
        self.assertFalse(self.ledger.exists())

    def test_corrupt_ledger_prevents_execution(self):
        self.ledger.write_text("not-json\n", encoding="utf-8")
        self.assertEqual(self.call()["reason_code"], "EXECUTION_FAILED")
        self.assertFalse(verify_ledger(self.ledger)["valid"])

    def test_concurrent_replay_has_one_execution(self):
        barrier = threading.Barrier(8)
        def attempt(_):
            barrier.wait()
            return self.call()["decision"]
        with ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(attempt, range(8)))
        self.assertEqual(outcomes.count("ALLOW"), 1)
        self.assertEqual(verify_ledger(self.ledger)["events"], 1)

    def test_socket_peer_credentials_and_client_roundtrip(self):
        socket_path = self.root / "broker.sock"
        server = _ThreadedUnixServer(str(socket_path), _RequestHandler)
        server.broker = self.broker
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request_path = self.root / "request.json"
            request_path.write_text(json.dumps(self.request), encoding="utf-8")
            result = submit(socket_path, request_path)
            self.assertEqual(result["decision"], "ALLOW")
            self.assertEqual(result["operation"], "audit.append")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
