"""Optional TUF-backed policy retrieval from an operator-controlled local mirror.

All signature, metadata version, expiry, delegation, and target hash verification is delegated
to python-tuf. MASG does not implement its own signature scheme or TUF metadata parser.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import stat
from urllib.parse import unquote, urlsplit


class PolicyTrustError(RuntimeError):
    """A policy target could not be authenticated and retrieved."""


MAX_BOOTSTRAP_BYTES = 512_000
MAX_POLICY_BYTES = 1_048_576
MAX_MIRROR_OBJECT_BYTES = 6_000_000


def _protected_directory(path: str | Path, label: str) -> Path:
    target = Path(path)
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise PolicyTrustError(f"{label} cannot be inspected") from exc
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_mode & 0o022:
        raise PolicyTrustError(f"{label} must be an operator-controlled, non-writable directory")
    return target


def _protected_file(path: str | Path, label: str) -> Path:
    target = Path(path)
    _protected_directory(target.parent, f"{label} parent directory")
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise PolicyTrustError(f"{label} cannot be inspected") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o022:
        raise PolicyTrustError(f"{label} must be a regular, non-group/world-writable file")
    return target


def _validate_target_name(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PolicyTrustError("TUF target path is invalid")
    target = PurePosixPath(value)
    if target.is_absolute() or any(part in {"", ".", ".."} for part in target.parts):
        raise PolicyTrustError("TUF target path must be a normalized relative POSIX path")
    if str(target) != value:
        raise PolicyTrustError("TUF target path must be canonical")
    return value


def fetch_verified_policy(
    *,
    repository_root: str | Path,
    bootstrap_root: str | Path,
    cache_dir: str | Path,
    target_name: str = "policies/active.json",
    max_target_bytes: int = MAX_POLICY_BYTES,
) -> Path:
    """Refresh TUF metadata and download one verified policy target from a local mirror.

    The bootstrap root is an out-of-band trust anchor. The TUF metadata cache must be
    persistent and protected from rollback by the adopter's operating system/storage.
    """
    try:
        from tuf.api.exceptions import DownloadHTTPError
        from tuf.ngclient import Updater
        from tuf.ngclient.fetcher import FetcherInterface
    except ImportError as exc:
        raise PolicyTrustError("TUF support is optional; install masg-guardrails[tuf]") from exc

    repository = _protected_directory(repository_root, "TUF repository mirror").resolve(strict=True)
    bootstrap_file = _protected_file(bootstrap_root, "TUF bootstrap root")
    cache = _protected_directory(cache_dir, "TUF cache directory").resolve(strict=True)
    target_name = _validate_target_name(target_name)
    if max_target_bytes < 1 or max_target_bytes > MAX_POLICY_BYTES:
        raise PolicyTrustError("TUF policy size limit is outside the permitted range")

    metadata_dir = cache / "metadata"
    targets_dir = cache / "targets"
    for directory in (metadata_dir, targets_dir):
        if directory.is_symlink():
            raise PolicyTrustError("TUF cache subdirectories must not be symlinks")
        directory.mkdir(mode=0o700, exist_ok=True)
        _protected_directory(directory, "TUF cache subdirectory")

    class LocalMirrorFetcher(FetcherInterface):
        """Read-only fetcher that maps TUF URLs to a local repository mirror."""

        def _fetch(self, url: str):
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.netloc != "masg.invalid" or parsed.query or parsed.fragment:
                raise DownloadHTTPError("TUF fetch URL is outside the configured local mirror", 403)
            decoded = unquote(parsed.path)
            if decoded.startswith("/metadata/"):
                relative = Path("metadata") / decoded.removeprefix("/metadata/")
            elif decoded.startswith("/targets/"):
                relative = Path("targets") / decoded.removeprefix("/targets/")
            else:
                raise DownloadHTTPError("TUF fetch path is not permitted", 404)
            candidate = repository / relative
            try:
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(repository)
                if candidate.is_symlink() or not resolved.is_file():
                    raise DownloadHTTPError("TUF mirror object is not a regular file", 404)
                if resolved.stat().st_size > MAX_MIRROR_OBJECT_BYTES:
                    raise DownloadHTTPError("TUF mirror object exceeds configured bound", 413)
                yield resolved.read_bytes()
            except FileNotFoundError as exc:
                raise DownloadHTTPError("TUF mirror object not found", 404) from exc
            except (OSError, ValueError) as exc:
                raise DownloadHTTPError("TUF mirror object cannot be read safely", 404) from exc

    try:
        if bootstrap_file.stat().st_size > MAX_BOOTSTRAP_BYTES:
            raise PolicyTrustError("TUF bootstrap root exceeds size limit")
        bootstrap = bootstrap_file.read_bytes()
        updater = Updater(
            metadata_dir=str(metadata_dir),
            metadata_base_url="https://masg.invalid/metadata/",
            target_dir=str(targets_dir),
            target_base_url="https://masg.invalid/targets/",
            fetcher=LocalMirrorFetcher(),
            bootstrap=bootstrap,
        )
        updater.refresh()
        target_info = updater.get_targetinfo(target_name)
        if target_info is None:
            raise PolicyTrustError("TUF metadata does not authorize the requested policy target")
        if target_info.length > max_target_bytes:
            raise PolicyTrustError("TUF policy target exceeds configured size limit")
        downloaded = Path(updater.download_target(target_info))
        resolved_target = downloaded.resolve(strict=True)
        resolved_target.relative_to(targets_dir.resolve(strict=True))
        if downloaded.is_symlink() or not resolved_target.is_file():
            raise PolicyTrustError("TUF returned a non-regular policy target")
        if resolved_target.stat().st_size > max_target_bytes:
            raise PolicyTrustError("verified policy target exceeds configured size limit")
        return resolved_target
    except PolicyTrustError:
        raise
    except Exception as exc:
        raise PolicyTrustError("TUF policy verification or retrieval failed") from exc
