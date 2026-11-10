"""Local JSONL SHA-256 chain; not a signature or immutable remote log."""
import hashlib
import json
from pathlib import Path
from typing import Any
GENESIS="0"*64
def _canonical(value: dict[str,Any]) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def append_event(path: str | Path,event: dict[str,Any]) -> dict[str,Any]:
    if not isinstance(event,dict): raise ValueError("event must be an object")
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    previous,sequence=GENESIS,1
    if target.exists() and target.stat().st_size:
        report=verify_ledger(target)
        if not report["valid"]: raise ValueError("refusing to append to invalid ledger")
        previous,sequence=report["last_hash"],report["events"]+1
    body={"sequence":sequence,"previous_hash":previous,"event":event}
    digest=hashlib.sha256(_canonical(body)).hexdigest()
    record={**body,"hash":digest}
    with target.open("a",encoding="utf-8") as stream:
        stream.write(json.dumps(record,sort_keys=True,ensure_ascii=False)+"\n"); stream.flush()
    return record
def verify_ledger(path: str | Path) -> dict[str,Any]:
    target,previous,count=Path(path),GENESIS,0
    try:
        with target.open(encoding="utf-8") as stream:
            for line_no,line in enumerate(stream,1):
                if not line.strip(): return {"valid":False,"events":count,"last_hash":previous,"error":f"blank line {line_no}"}
                try: record=json.loads(line)
                except json.JSONDecodeError: return {"valid":False,"events":count,"last_hash":previous,"error":f"invalid JSON line {line_no}"}
                if not isinstance(record,dict) or record.get("sequence")!=count+1 or record.get("previous_hash")!=previous:
                    return {"valid":False,"events":count,"last_hash":previous,"error":f"sequence/link mismatch line {line_no}"}
                if not isinstance(record.get("event"),dict): return {"valid":False,"events":count,"last_hash":previous,"error":f"invalid event line {line_no}"}
                body={"sequence":record["sequence"],"previous_hash":record["previous_hash"],"event":record["event"]}
                digest=hashlib.sha256(_canonical(body)).hexdigest()
                if record.get("hash")!=digest: return {"valid":False,"events":count,"last_hash":previous,"error":f"hash mismatch line {line_no}"}
                previous,count=digest,count+1
    except OSError as exc: return {"valid":False,"events":count,"last_hash":previous,"error":str(exc)}
    return {"valid":True,"events":count,"last_hash":previous,"error":None}
