"""Structural checks only; not deployment certification."""
import json
from pathlib import Path
REQUIRED=[f"MSC-{i:03d}" for i in range(1,11)]
FILES=["README.md","SECURITY.md","LICENSE","contracts/manifest.json","docs/THREAT_MODEL.md","docs/CONFORMANCE.md","pyproject.toml"]
def verify_repository(root: str | Path) -> dict:
    base,errors,warnings,found=Path(root),[],[],[]
    for item in FILES:
        if not (base/item).is_file(): errors.append(f"missing required file: {item}")
    path=base/"contracts/manifest.json"
    if path.is_file():
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
            entries=data.get("contracts") if isinstance(data,dict) else None
            if not isinstance(entries,list): errors.append("contracts must be an array")
            else:
                found=[x.get("id") for x in entries if isinstance(x,dict)]
                if len(found)!=len(entries): errors.append("each contract must be an object")
                missing=sorted(set(REQUIRED)-set(found))
                duplicates=sorted({x for x in found if found.count(x)>1})
                if missing: errors.append("missing IDs: "+", ".join(missing))
                if duplicates: errors.append("duplicate IDs: "+", ".join(duplicates))
                if data.get("catalog_version")!="1.0.0": warnings.append("catalog version differs from baseline")
        except (OSError,json.JSONDecodeError) as exc: errors.append(f"cannot parse manifest: {exc}")
    return {"status":"PASS" if not errors else "FAIL","scope":"repository_structure_only",
            "contracts_found":len(found),"contracts_required":10,"errors":errors,"warnings":warnings,
            "limitations":["Does not test live deployment or enforcement mediation.",
            "Does not authenticate identities or verify policy signatures.",
            "Does not prove OS isolation, complete path coverage, or safety."]}
