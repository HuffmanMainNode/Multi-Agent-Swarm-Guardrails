import socket
import tempfile
import time
import unittest
from unittest.mock import patch
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



    def test_wildcard_or_whitespace_audience_rejected(self):
        for audience in ("*", " masg-broker", "masg-broker "):
            with self.subTest(audience=audience), self.assertRaises(WorkloadIdentityError):
                SpiffeJwtSvidVerifier(
                    socket_path=self.socket_path, audience=audience,
                    client_factory=self.factory,
                )

    def test_group_writable_socket_parent_rejected(self):
        unsafe = self.root / "unsafe-sockets"
        unsafe.mkdir()
        unsafe.chmod(0o777)
        socket_path = unsafe / "workload-api.sock"
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(socket_path))
        server.close()
        try:
            with self.assertRaises(WorkloadIdentityError):
                SpiffeJwtSvidVerifier(
                    socket_path=socket_path, audience="masg-broker",
                    client_factory=self.factory,
                )
        finally:
            unsafe.chmod(0o700)

    def test_symlink_socket_parent_rejected(self):
        alias = self.root / "socket-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(WorkloadIdentityError):
            SpiffeJwtSvidVerifier(
                socket_path=alias / "workload-api.sock", audience="masg-broker",
                client_factory=self.factory,
            )



    def test_sdk_default_factory_uses_expected_workload_api_client(self):
        try:
            import spiffe
        except ImportError:
            self.skipTest("optional SPIFFE SDK is not installed")
        fake = self.factory(
            socket_path=f"unix:{self.socket_path}", default_timeout=2.0,
        )
        with patch.object(spiffe, "WorkloadApiClient", return_value=fake) as factory:
            verifier = SpiffeJwtSvidVerifier(
                socket_path=self.socket_path, audience="masg-broker",
            )
        factory.assert_called_once_with(
            socket_path=f"unix:{self.socket_path}", default_timeout=2.0,
        )
        self.assertEqual(
            verifier.authenticate("header.payload.signature").principal,
            "spiffe://example.org/agent/test",
        )
        verifier.close()

    def test_dotdot_socket_path_rejected(self):
        path = self.root / "nested" / ".." / "workload-api.sock"
        with self.assertRaises(WorkloadIdentityError):
            SpiffeJwtSvidVerifier(
                socket_path=path, audience="masg-broker",
                client_factory=self.factory,
            )

    def test_symlinked_ancestor_directory_rejected(self):
        nested = self.root / "nested"
        nested.mkdir()
        actual_socket = nested / "workload-api.sock"
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(actual_socket))
        server.close()
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(WorkloadIdentityError):
            SpiffeJwtSvidVerifier(
                socket_path=alias / "nested" / "workload-api.sock",
                audience="masg-broker", client_factory=self.factory,
            )


if __name__ == "__main__":
    unittest.main()
