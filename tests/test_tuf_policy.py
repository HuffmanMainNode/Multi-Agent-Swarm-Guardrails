import hashlib
import json
import os
import socket
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from securesystemslib.signer import CryptoSigner
    from tuf.api.metadata import (
        TOP_LEVEL_ROLE_NAMES, MetaFile, Metadata, Root, Snapshot, TargetFile, Targets, Timestamp,
    )
    from tuf.api.serialization.json import JSONSerializer
    TUF_TESTS_AVAILABLE = True
except ImportError:
    TUF_TESTS_AVAILABLE = False

from masg.broker import ExecutionBroker
from masg.trust import PolicyTrustError, fetch_verified_policy


@unittest.skipUnless(TUF_TESTS_AVAILABLE, "install the optional MASG TUF dependencies")
class TUFPolicyTests(unittest.TestCase):
    target_name = "policies/active.json"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repository = self.root / "mirror"
        (self.repository / "metadata").mkdir(parents=True)
        (self.repository / "targets").mkdir()
        self.cache = self.root / "cache"
        self.cache.mkdir(mode=0o700)
        self.expiry = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=2)
        self.signers = {}
        self.root_metadata = Metadata(Root(expires=self.expiry))
        for role in TOP_LEVEL_ROLE_NAMES:
            signer = CryptoSigner.generate_ed25519()
            self.root_metadata.signed.add_key(signer.public_key, role)
            self.signers[role] = signer
        self.root_metadata.signed.consistent_snapshot = True
        self.root_metadata.sign(self.signers["root"])
        self.bootstrap = self.root_metadata.to_bytes(JSONSerializer())
        self.bootstrap_path = self.root / "trusted-root.json"
        self.bootstrap_path.write_bytes(self.bootstrap)
        self.publish(b'{"version":"signed-policy-v1","default_effect":"DENY","rules":[]}', 1)

    def tearDown(self):
        self.temp.cleanup()

    def publish(self, policy: bytes, version: int, *, expiry=None):
        expires = expiry or self.expiry
        targets = Metadata(Targets(expires=expires))
        targets.signed.version = version
        target_info = TargetFile.from_data(self.target_name, policy, ["sha256"])
        targets.signed.targets[self.target_name] = target_info
        targets.sign(self.signers["targets"])
        targets_bytes = targets.to_bytes(JSONSerializer())

        snapshot = Metadata(Snapshot(expires=expires))
        snapshot.signed.version = version
        snapshot.signed.meta["targets.json"] = MetaFile(
            targets.signed.version, len(targets_bytes),
            {"sha256": hashlib.sha256(targets_bytes).hexdigest()},
        )
        snapshot.sign(self.signers["snapshot"])
        snapshot_bytes = snapshot.to_bytes(JSONSerializer())

        timestamp = Metadata(Timestamp(expires=expires))
        timestamp.signed.version = version
        timestamp.signed.snapshot_meta = MetaFile(
            snapshot.signed.version, len(snapshot_bytes),
            {"sha256": hashlib.sha256(snapshot_bytes).hexdigest()},
        )
        timestamp.sign(self.signers["timestamp"])

        metadata = self.repository / "metadata"
        (metadata / f"{version}.targets.json").write_bytes(targets_bytes)
        (metadata / f"{version}.snapshot.json").write_bytes(snapshot_bytes)
        (metadata / "timestamp.json").write_bytes(timestamp.to_bytes(JSONSerializer()))

        digest = hashlib.sha256(policy).hexdigest()
        target_file = self.repository / "targets" / "policies" / f"{digest}.active.json"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_bytes(policy)

    def fetch(self, *, cache=None, target_name=None):
        return fetch_verified_policy(
            repository_root=self.repository,
            bootstrap_root=self.bootstrap_path,
            cache_dir=cache or self.cache,
            target_name=target_name or self.target_name,
        )

    def test_verified_policy_is_downloaded(self):
        path = self.fetch()
        self.assertEqual(path.read_bytes(), b'{"version":"signed-policy-v1","default_effect":"DENY","rules":[]}')
        self.assertTrue(path.is_file())

    def test_tampered_target_is_rejected(self):
        path = next((self.repository / "targets" / "policies").glob("*.active.json"))
        path.write_bytes(b'{"version":"attacker-policy"}')
        with self.assertRaises(PolicyTrustError):
            self.fetch()

    def test_tampered_targets_metadata_is_rejected(self):
        path = self.repository / "metadata" / "1.targets.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaises(PolicyTrustError):
            self.fetch()

    def test_rollback_to_older_timestamp_is_rejected(self):
        timestamp_path = self.repository / "metadata" / "timestamp.json"
        old_timestamp = timestamp_path.read_bytes()
        self.fetch()
        self.publish(b'{"version":"signed-policy-v2","default_effect":"DENY","rules":[]}', 2)
        self.fetch()
        timestamp_path.write_bytes(old_timestamp)
        with self.assertRaises(PolicyTrustError):
            self.fetch()

    def test_expired_metadata_is_rejected(self):
        expired = datetime.now(timezone.utc) - timedelta(days=2)
        self.publish(b'{"version":"expired","default_effect":"DENY","rules":[]}', 3, expiry=expired)
        with self.assertRaises(PolicyTrustError):
            self.fetch()

    def test_wrong_but_valid_bootstrap_root_is_rejected(self):
        other = Metadata(Root(expires=self.expiry))
        other_signers = {}
        for role in TOP_LEVEL_ROLE_NAMES:
            signer = CryptoSigner.generate_ed25519()
            other.signed.add_key(signer.public_key, role)
            other_signers[role] = signer
        other.signed.consistent_snapshot = True
        other.sign(other_signers["root"])
        wrong_root = self.root / "wrong-root.json"
        wrong_root.write_bytes(other.to_bytes(JSONSerializer()))
        with self.assertRaises(PolicyTrustError):
            fetch_verified_policy(
                repository_root=self.repository,
                bootstrap_root=wrong_root,
                cache_dir=self.root / "wrong-cache",
                target_name=self.target_name,
            )

    def test_target_path_traversal_is_rejected(self):
        with self.assertRaises(PolicyTrustError):
            self.fetch(target_name="../outside.json")

    def test_cache_must_not_be_group_or_world_writable(self):
        unsafe_cache = self.root / "unsafe-cache"
        unsafe_cache.mkdir()
        unsafe_cache.chmod(0o777)
        try:
            with self.assertRaises(PolicyTrustError):
                self.fetch(cache=unsafe_cache)
        finally:
            unsafe_cache.chmod(0o700)

    @unittest.skipUnless(sys.platform.startswith("linux") and hasattr(socket, "SO_PEERCRED"), "Linux broker required")
    def test_broker_loads_policy_only_after_tuf_verification(self):
        policy = {
            "version": "tuf-broker-policy-v1",
            "default_effect": "DENY",
            "rules": [{
                "id": "allow-audit-append",
                "principals": ["service:tuf-test"],
                "actions": ["audit.append"],
                "targets": ["audit-ledger"],
                "scopes": ["append"],
                "effect": "ALLOW",
            }],
        }
        self.publish(json.dumps(policy).encode(), 2)
        principals = self.root / "principals.json"
        principals.write_text(json.dumps({str(os.getuid()): "service:tuf-test"}), encoding="utf-8")
        broker = ExecutionBroker(
            policy_path=None,
            principal_map_path=principals,
            replay_db=self.root / "replay.sqlite3",
            ledger_path=self.root / "evidence.jsonl",
            tuf_repository=self.repository,
            tuf_bootstrap_root=self.bootstrap_path,
            tuf_cache=self.cache,
        )
        self.assertEqual(broker.policy["version"], "tuf-broker-policy-v1")


if __name__ == "__main__":
    unittest.main()
