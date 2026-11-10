"""Separate-process Linux broker for one narrowly allowlisted protected operation.

Uses Linux SO_PEERCRED to derive caller UID; never accepts a principal from the request.
Authorizes only audit.append to the broker-owned ledger. Not a general command runner.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import socketserver
import stat
import struct
import sys
import threading
import uuid
from typing import Any

from .audit import append_event
from .policy import evaluate, load_policy
from .replay import ReplayStore, ReplayStoreError

MAX_MESSAGE_BYTES = 16_384
MAX_EVENT_DETAILS = 4_096
MAX_REQUEST_TTL_SECONDS = 300
OPERATION = "audit.append"
TARGET = "audit-ledger"
SCOPE = "append"


class BrokerError(RuntimeError):
    """Broker configuration or transport error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _decode(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ValueError("request exceeds broker message limit")
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant,
        )
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds parser safety limit") from exc
    if not isinstance(value, dict):
        raise ValueError("request must be a JSON object")
    return value


def _regular_operator_file(path: str | Path, label: str) -> Path:
    target = Path(path)
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise BrokerError(f"{label} cannot be inspected") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise BrokerError(f"{label} must be a regular file, not a symlink or special file")
    if metadata.st_mode & 0o022:
        raise BrokerError(f"{label} must not be group-writable or world-writable")
    return target


def _load_principals(path: str | Path) -> dict[int, str]:
    target = _regular_operator_file(path, "principal map")
    raw = target.read_bytes()
    if len(raw) > 65_536:
        raise BrokerError("principal map exceeds size limit")
    data = _decode(raw)
    result: dict[int, str] = {}
    for key, principal in data.items():
        if not isinstance(key, str) or not key.isascii() or not key.isdecimal():
            raise BrokerError("principal map keys must be decimal operating-system UIDs")
        uid = int(key)
        if uid in result or uid < 0:
            raise BrokerError("principal map contains an invalid or duplicate UID")
        if not isinstance(principal, str) or not principal.strip() or len(principal) > 1_024:
            raise BrokerError("principal map values must be non-empty principal strings")
        result[uid] = principal
    if not result:
        raise BrokerError("principal map must contain at least one UID mapping")
    return result


def _peer_uid(connection: socket.socket) -> int:
    if not sys.platform.startswith("linux") or not hasattr(socket, "SO_PEERCRED"):
        raise BrokerError("broker currently requires Linux SO_PEERCRED support")
    credentials = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", credentials)
    if uid < 0:
        raise BrokerError("operating-system peer UID is invalid")
    return uid


class ExecutionBroker:
    """Authorize and execute the fixed audit.append operation."""

    def __init__(
        self, *, policy_path: str | Path, principal_map_path: str | Path,
        replay_db: str | Path, ledger_path: str | Path,
    ) -> None:
        if not sys.platform.startswith("linux") or not hasattr(socket, "SO_PEERCRED"):
            raise BrokerError("execution broker currently supports Linux only")
        policy_file = _regular_operator_file(policy_path, "policy file")
        self.policy = load_policy(policy_file)
        self.principals = _load_principals(principal_map_path)
        replay_path = Path(replay_db)
        ledger = Path(ledger_path)
        for path, label in ((replay_path, "replay database"), (ledger, "evidence ledger")):
            if path.is_symlink():
                raise BrokerError(f"{label} must not be a symlink")
        if replay_path.resolve() == ledger.resolve():
            raise BrokerError("replay database and evidence ledger must be different files")
        self.replay = ReplayStore(replay_path)
        self.ledger_path = ledger
        self._ledger_lock = threading.Lock()

    def process(self, raw: bytes, peer_uid: int) -> dict[str, Any]:
        try:
            request = _decode(raw)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return {"decision": "DENY", "reason_code": "REQUEST_INVALID"}
        if set(request) != {"request_id", "issued_at", "expires_at", "event"}:
            return {"decision": "DENY", "reason_code": "REQUEST_SHAPE_INVALID"}

        principal = self.principals.get(peer_uid)
        if principal is None:
            return {"decision": "DENY", "reason_code": "CALLER_IDENTITY_UNMAPPED"}

        request_id, issued_at, expires_at, event = (
            request.get("request_id"), request.get("issued_at"),
            request.get("expires_at"), request.get("event"),
        )
        if (
            not isinstance(request_id, str) or len(request_id) != 36
            or not isinstance(issued_at, str) or len(issued_at) > 64
            or not isinstance(expires_at, str) or len(expires_at) > 64
            or not isinstance(event, dict) or set(event) != {"kind", "details"}
            or not isinstance(event.get("kind"), str) or not event["kind"].strip()
            or len(event["kind"]) > 64
            or not isinstance(event.get("details"), str)
            or len(event["details"]) > MAX_EVENT_DETAILS
        ):
            return {"decision": "DENY", "reason_code": "REQUEST_FIELDS_INVALID"}

        try:
            parsed_id = uuid.UUID(request_id)
            if parsed_id.version != 4 or str(parsed_id) != request_id:
                return {"decision": "DENY", "reason_code": "REQUEST_ID_INVALID"}
        except (ValueError, AttributeError):
            return {"decision": "DENY", "reason_code": "REQUEST_ID_INVALID"}

        policy_request = {
            "principal": principal, "action": OPERATION, "target": TARGET, "scope": SCOPE,
            "request_id": request_id, "issued_at": issued_at, "expires_at": expires_at,
            "delegation_chain": [],
        }
        result = evaluate(self.policy, policy_request)
        if result.decision.value != "ALLOW":
            return {
                "decision": "DENY", "reason_code": result.reason_code,
                "policy_version": result.policy_version,
            }
        try:
            issued = datetime.fromisoformat(issued_at.replace("Z", "+00:00"))
            expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if (expires - issued).total_seconds() > MAX_REQUEST_TTL_SECONDS:
                return {"decision": "DENY", "reason_code": "REQUEST_TTL_TOO_LONG"}
            if issued.tzinfo is None or expires.tzinfo is None:
                return {"decision": "DENY", "reason_code": "REQUEST_TIME_INVALID"}
        except (TypeError, ValueError, OverflowError):
            return {"decision": "DENY", "reason_code": "REQUEST_TIME_INVALID"}

        try:
            consumed = self.replay.consume(policy_request)
        except ReplayStoreError:
            return {"decision": "DENY", "reason_code": "REPLAY_STORE_UNAVAILABLE"}
        if not consumed:
            return {"decision": "DENY", "reason_code": "REPLAY_DETECTED"}

        record_event = {
            "operation": OPERATION, "principal": principal, "peer_uid": peer_uid,
            "request_id": request_id, "submitted_event": event,
        }
        try:
            with self._ledger_lock:
                record = append_event(self.ledger_path, record_event)
        except (OSError, ValueError, TypeError):
            # ID remains consumed; inspect evidence before any operator-directed recovery.
            return {"decision": "DENY", "reason_code": "EXECUTION_FAILED"}
        return {
            "decision": "ALLOW", "reason_code": "EXECUTED",
            "policy_version": result.policy_version, "operation": OPERATION,
            "evidence_sequence": record["sequence"], "evidence_hash": record["hash"],
        }


class _RequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.connection.settimeout(3.0)
        try:
            uid = _peer_uid(self.connection)
            raw = self.rfile.readline(MAX_MESSAGE_BYTES + 1)
            if len(raw) > MAX_MESSAGE_BYTES or not raw.endswith(b"\n"):
                response = {"decision": "DENY", "reason_code": "MESSAGE_LIMIT_OR_FRAMING"}
            else:
                response = self.server.broker.process(raw[:-1], uid)  # type: ignore[attr-defined]
        except (BrokerError, OSError):
            response = {"decision": "DENY", "reason_code": "PEER_OR_TRANSPORT_UNAVAILABLE"}
        encoded = json.dumps(response, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        self.wfile.write(encoded)
        self.wfile.flush()


class _ThreadedUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    request_queue_size = 32
    _capacity = threading.BoundedSemaphore(32)

    def process_request(self, request: socket.socket, client_address: str) -> None:
        if not self._capacity.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._capacity.release()
            raise

    def process_request_thread(self, request: socket.socket, client_address: str) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._capacity.release()


def serve(
    *, socket_path: str | Path, policy_path: str | Path, principal_map_path: str | Path,
    replay_db: str | Path, ledger_path: str | Path,
) -> None:
    """Serve until interrupted. Existing socket paths are never unlinked automatically."""
    if not sys.platform.startswith("linux"):
        raise BrokerError("broker server currently supports Linux only")
    path = Path(socket_path)
    if not path.parent.is_dir():
        raise BrokerError("socket parent directory must already exist and be operator-controlled")
    if path.exists() or path.is_symlink():
        raise BrokerError("socket path already exists; inspect it and remove stale sockets manually")
    broker = ExecutionBroker(
        policy_path=policy_path, principal_map_path=principal_map_path,
        replay_db=replay_db, ledger_path=ledger_path,
    )
    server = _ThreadedUnixServer(str(path), _RequestHandler)
    server.broker = broker  # type: ignore[attr-defined]
    socket_stat = None
    try:
        os.chmod(path, 0o660)
        socket_stat = path.lstat()
        if not stat.S_ISSOCK(socket_stat.st_mode):
            raise BrokerError("bound path is not a socket")
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        try:
            current = path.lstat()
            if socket_stat and stat.S_ISSOCK(current.st_mode) and current.st_ino == socket_stat.st_ino:
                path.unlink()
        except FileNotFoundError:
            pass


def submit(socket_path: str | Path, request_path: str | Path) -> dict[str, Any]:
    """Send one bounded JSON request to a local broker and return its response."""
    raw = Path(request_path).read_bytes()
    if len(raw) > MAX_MESSAGE_BYTES:
        raise BrokerError("request exceeds broker message limit")
    _decode(raw)
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(5.0)
    try:
        client.connect(str(socket_path))
        client.sendall(raw.rstrip(b"\n") + b"\n")
        client.shutdown(socket.SHUT_WR)
        response = bytearray()
        while len(response) <= MAX_MESSAGE_BYTES:
            chunk = client.recv(4_096)
            if not chunk:
                break
            response.extend(chunk)
            if b"\n" in response:
                break
        if len(response) > MAX_MESSAGE_BYTES or not response.endswith(b"\n"):
            raise BrokerError("broker response framing invalid")
        return _decode(bytes(response[:-1]))
    except OSError as exc:
        raise BrokerError("cannot communicate with local broker") from exc
    finally:
        client.close()
