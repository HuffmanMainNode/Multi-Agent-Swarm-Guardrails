"""Command-line entry point for local MASG reference checks."""
import argparse
import json
import sys
from pathlib import Path

from .audit import verify_ledger
from .broker import BrokerError, serve as serve_broker, submit as submit_broker
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
    ev.add_argument("--replay-db", help="enable local SQLite one-time request-ID consumption")
    audit = sub.add_parser("audit", help="verify a local hash-chain ledger")
    subaudit = audit.add_subparsers(dest="audit_command", required=True)
    av = subaudit.add_parser("verify")
    av.add_argument("path")
    broker = sub.add_parser("broker", help="operate the separate-process Linux execution broker")
    broker_sub = broker.add_subparsers(dest="broker_command", required=True)
    serve = broker_sub.add_parser("serve", help="serve the fixed audit.append operation")
    serve.add_argument("--socket", required=True)
    serve.add_argument("--policy", required=True)
    serve.add_argument("--principal-map", required=True)
    serve.add_argument("--replay-db", required=True)
    serve.add_argument("--ledger", required=True)
    append = broker_sub.add_parser("append", help="submit one request to the local broker")
    append.add_argument("--socket", required=True)
    append.add_argument("--request", required=True)

    args = parser.parse_args(argv)
    if args.command == "verify":
        result = verify_repository(Path(args.root))
        code = 0 if result["status"] == "PASS" else 2
    elif args.command == "evaluate":
        result = evaluate_files(args.policy, args.request, replay_db=args.replay_db).to_dict()
        result["replay_protection"] = "LOCAL_SQLITE_ENABLED" if args.replay_db else "DISABLED"
        code = 0 if result["decision"] == "ALLOW" else 3
    elif args.command == "audit":
        result = verify_ledger(args.path)
        code = 0 if result["valid"] else 4
    elif args.broker_command == "serve":
        try:
            serve_broker(
                socket_path=args.socket, policy_path=args.policy,
                principal_map_path=args.principal_map, replay_db=args.replay_db,
                ledger_path=args.ledger,
            )
        except (BrokerError, OSError, ValueError) as exc:
            print(json.dumps({"decision": "DENY", "reason_code": "BROKER_START_FAILED", "detail": str(exc)}), file=sys.stderr)
            return 5
        return 0
    else:
        try:
            result = submit_broker(args.socket, args.request)
        except (BrokerError, OSError, ValueError) as exc:
            print(json.dumps({"decision": "DENY", "reason_code": "BROKER_REQUEST_FAILED", "detail": str(exc)}), file=sys.stderr)
            return 6
        code = 0 if result.get("decision") == "ALLOW" else 7
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
