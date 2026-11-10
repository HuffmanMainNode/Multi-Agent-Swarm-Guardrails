"""SPIFFE Workload API-backed JWT-SVID identity verification.

Identity is validated online for every protected request. No token or identity
result is cached. The local Workload API endpoint remains part of the trust
boundary and must be protected by the SPIRE/Workload API deployment.
"""
from __future__ import annotations

import os
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class WorkloadIdentityError(RuntimeError):
    """Workload identity configuration or validation failure."""


@dataclass(frozen=True)
class VerifiedWorkloadIdentity:
    """Identity and expiry returned only after Workload API validation."""

    principal: str
    expires_at: int


class SpiffeJwtSvidVerifier:
    """Validate presented JWT-SVIDs through the local SPIFFE Workload API."""

    def __init__(
        self,
        *,
        socket_path: str | Path,
        audience: str,
        timeout: float = 2.0,
        client_factory: Any | None = None,
    ) -> None:
        if (
            not isinstance(audience, str) or not audience or len(audience) > 512
            or audience != audience.strip() or any(char.isspace() for char in audience)
            or audience == "*"
        ):
            raise WorkloadIdentityError("SPIFFE audience must be a non-empty exact bounded value")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0.1 <= timeout <= 10:
            raise WorkloadIdentityError("SPIFFE validation timeout must be between 0.1 and 10 seconds")

        supplied = os.fspath(socket_path)
        if supplied.startswith("unix:"):
            filesystem_path = supplied[5:]
            endpoint = supplied
        else:
            filesystem_path = supplied
            endpoint = f"unix:{supplied}"
        if not filesystem_path or not Path(filesystem_path).is_absolute():
            raise WorkloadIdentityError("SPIFFE endpoint must be an absolute Unix socket path")

        path = Path(filesystem_path)
        try:
            parent_metadata = path.parent.lstat()
            metadata = path.lstat()
        except OSError as exc:
            raise WorkloadIdentityError("SPIFFE endpoint socket cannot be inspected") from exc
        if (
            not stat.S_ISDIR(parent_metadata.st_mode) or parent_metadata.st_mode & 0o022
        ):
            raise WorkloadIdentityError("SPIFFE socket parent must be a protected, non-writable directory")
        if not stat.S_ISSOCK(metadata.st_mode):
            raise WorkloadIdentityError("SPIFFE endpoint must be a Unix socket, not a symlink or regular file")

        if client_factory is None:
            try:
                from spiffe import WorkloadApiClient
            except ImportError as exc:
                raise WorkloadIdentityError(
                    "SPIFFE support is optional; install masg-guardrails[spiffe]"
                ) from exc
            client_factory = WorkloadApiClient

        try:
            self._client = client_factory(socket_path=endpoint, default_timeout=float(timeout))
        except Exception as exc:
            raise WorkloadIdentityError("SPIFFE Workload API client initialization failed") from exc
        self.audience = audience
        self.timeout = float(timeout)

    def authenticate(self, token: str) -> VerifiedWorkloadIdentity:
        """Return validated identity and token expiry or fail closed."""
        if (
            not isinstance(token, str) or not token or len(token) > 8_192
            or not token.isascii() or any(char.isspace() for char in token)
            or token.count(".") != 2
        ):
            raise WorkloadIdentityError("JWT-SVID presentation is malformed or exceeds bounds")
        try:
            svid = self._client.validate_jwt_svid(
                token=token, audience=self.audience, timeout=self.timeout,
            )
            identity = str(svid.spiffe_id)
            expiry = svid.expiry
            if (
                not identity.startswith("spiffe://") or len(identity) > 1_024
                or "?" in identity or "#" in identity
            ):
                raise WorkloadIdentityError("validated SPIFFE ID is not canonical")
            if self.audience not in svid.audience:
                raise WorkloadIdentityError("validated JWT-SVID audience mismatch")
            if isinstance(expiry, bool) or not isinstance(expiry, int) or expiry <= int(time.time()):
                raise WorkloadIdentityError("validated JWT-SVID expiry is invalid or elapsed")
            return VerifiedWorkloadIdentity(principal=identity, expires_at=expiry)
        except WorkloadIdentityError:
            raise
        except Exception as exc:
            raise WorkloadIdentityError("JWT-SVID validation failed") from exc

    def close(self) -> None:
        """Close the Workload API gRPC channel."""
        self._client.close()
