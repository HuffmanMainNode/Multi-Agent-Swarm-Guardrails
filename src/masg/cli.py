"""Command-line entry point for local MASG reference checks."""
import argparse
import json
import sys
from pathlib import Path

from .audit import verify_ledger
from .conformance import verify_repository
from .policy import evaluate_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="masg", description="Local MASG reference verifier")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("verify", help="check repository structure only")
    check.add_argument("--root", default=".")

    ev = sub.add_parser("evaluate", help="evaluate a request against a local policy")
    ev.add_argument("--policy", required=True)
    ev.add_argument("--request", required=True)
    ev.add_argument(
        "--replay-db",
        help="enable local SQLite one-time request-ID consumption; protect this database from rollback",
    )

    audit = sub.add_parser("audit", help="verify a local hash-chain ledger")
    subaudit = audit.add_subparsers(dest="audit_command", required=True)
    av = subaudit.add_parser("verify")
    av.add_argument("path")

    args = parser.parse_args(argv)
    if args.command == "verify":
        result = verify_repository(Path(args.root))
        code = 0 if result["status"] == "PASS" else 2
    elif args.command == "evaluate":
        result = evaluate_files(args.policy, args.request, replay_db=args.replay_db).to_dict()
        result["replay_protection"] = "LOCAL_SQLITE_ENABLED" if args.replay_db else "DISABLED"
        code = 0 if result["decision"] == "ALLOW" else 3
    else:
        result = verify_ledger(args.path)
        code = 0 if result["valid"] else 4
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
