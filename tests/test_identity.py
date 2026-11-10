import socket
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from masg.identity import SpiffeJwtSvidVerifier, VerifiedWorkloadIdentity, WorkloadIdentityError


class FakeWorkloadApiClient:
    def __init__(self, *, socket_path, default_timeout):
        self.socket_path = socket_path
        self.default_timeout = default_timeout
        self.calls = []
        self.closed = False
        self.expiry = int(time.time()) + 300
        self.audience_override = None

    def validate_jwt_svid(self, *, token, audience, timeout):
        self.calls.append((token, audience, timeout))
        if token == "invalid.token.value":
            raise RuntimeError("rejected")
        return SimpleNamespace(
            spiffe_id="spiffe://example.org/agent/test",
            audience={self.audience_override or audience},
            expiry=self.expiry,
        )

    def close(self):
        self.closed = True


class SpiffeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.socket_path = self.root / "workload-api.sock"
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.socket_path))
        server.close()
        self.client = None

    def tearDown(self):
        self.temp.cleanup()

    def factory(self, **kwargs):
        self.client = FakeWorkloadApiClient(**kwargs)
        return self.client

    def test_valid_token_returns_validated_identity_and_expiry(self):
        verifier = SpiffeJwtSvidVerifier(
            socket_path=self.socket_path, audience="masg-broker",
            client_factory=self.factory,
        )
        self.assertEqual(
            verifier.authenticate("header.payload.signature"),
            VerifiedWorkloadIdentity(
                principal="spiffe://example.org/agent/test",
                expires_at=self.client.expiry,
            ),
        )
        self.assertEqual(self.client.calls, [
            ("header.payload.signature", "masg-broker", 2.0),
        ])
        verifier.close()
        self.assertTrue(self.client.closed)

    def test_invalid_token_fails_closed(self):
        verifier = SpiffeJwtSvidVerifier(
            socket_path=self.socket_path, audience="masg-broker",
            client_factory=self.factory,
        )
        with self.assertRaises(WorkloadIdentityError):
            verifier.authenticate("invalid.token.value")

    def test_malformed_or_oversized_token_rejected_before_provider_call(self):
        verifier = SpiffeJwtSvidVerifier(
            socket_path=self.socket_path, audience="masg-broker",
            client_factory=self.factory,
        )
        for token in ("", "not-a-jwt", "a.b.c\n", "a" * 8193):
            with self.subTest(token=token[:20]), self.assertRaises(WorkloadIdentityError):
                verifier.authenticate(token)
        self.assertEqual(self.client.calls, [])

    def test_expired_svid_rejected(self):
        verifier = SpiffeJwtSvidVerifier(
            socket_path=self.socket_path, audience="masg-broker",
            client_factory=self.factory,
        )
        self.client.expiry = int(time.time()) - 1
        with self.assertRaises(WorkloadIdentityError):
            verifier.authenticate("header.payload.signature")

    def test_wrong_audience_rejected(self):
        verifier = SpiffeJwtSvidVerifier(
            socket_path=self.socket_path, audience="masg-broker",
            client_factory=self.factory,
        )
        self.client.audience_override = "another-service"
        with self.assertRaises(WorkloadIdentityError):
            verifier.authenticate("header.payload.signature")

    def test_empty_audience_rejected(self):
        with self.assertRaises(WorkloadIdentityError):
            SpiffeJwtSvidVerifier(
                socket_path=self.socket_path, audience="",
                client_factory=self.factory,
            )

    def test_non_socket_endpoint_rejected(self):
        regular = self.root / "not-a-socket"
        regular.write_text("x", encoding="utf-8")
        with self.assertRaises(WorkloadIdentityError):
            SpiffeJwtSvidVerifier(
                socket_path=regular, audience="masg-broker",
                client_factory=self.factory,
            )

    def test_relative_endpoint_rejected(self):
        with self.assertRaises(WorkloadIdentityError):
            SpiffeJwtSvidVerifier(
                socket_path="relative.sock", audience="masg-broker",
                client_factory=self.factory,
            )


if __name__ == "__main__":
    unittest.main()
