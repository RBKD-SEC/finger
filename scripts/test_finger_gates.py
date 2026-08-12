#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finger gate tests (Ticket 03)

Covers:
  - catalog generation respects accepted/held provenance
  - accepted asset appears in catalog, held asset does not
  - catalog determinism
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PASS = 0
FAIL = 0


def case(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f"  ✓ {name}")
    except Exception as exc:
        FAIL += 1
        print(f"  ✗ {name}: {exc}")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_generate(tmp_root, provenance):
    tmp = Path(tmp_root)
    # copy minimal tree into temp dir
    (tmp / "scripts").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "finger.json", tmp / "finger.json")
    shutil.copy2(ROOT / "scripts" / "slugs.json", tmp / "scripts" / "slugs.json")
    (tmp / "capabilities" / "rights").mkdir(parents=True, exist_ok=True)
    (tmp / "capabilities" / "rights" / "provenance.json").write_text(
        json.dumps(provenance, sort_keys=True, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (tmp / "capabilities" / "schema").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "capabilities" / "schema" / "catalog-v1.schema.json",
                 tmp / "capabilities" / "schema" / "catalog-v1.schema.json")

    sys.path.insert(0, str(ROOT / "scripts"))
    import generate_catalog as gc  # noqa: E402
    gc.ROOT = tmp
    gc.CAP_DIR = tmp / "capabilities"
    gc.SCHEMA_DIR = gc.CAP_DIR / "schema"
    gc.generate(write=True)
    return tmp / "capabilities" / "catalog-v1.json"


def t_held_asset_not_in_catalog():
    provenance = {
        "schema_version": 1,
        "repository": "finger",
        "assets": [
            {"provenance_id": "prov-finger-finger-json-00000000",
             "destination": "finger.json",
             "content_digest": "sha256:" + "0" * 64,
             "origin_class": "unknown", "rights_basis": "unknown",
             "spdx": "LicenseRef-UNKNOWN", "modifications": "",
             "required_notices": [], "contributor_authority": "unknown",
             "decision": "held", "reviewer": None,
             "reason": "pending review"}
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = _run_generate(tmp, provenance)
        catalog = _load(path)
        assert catalog["capabilities"] == [], "held asset must not appear in catalog"


def t_accepted_asset_in_catalog():
    digest = "sha256:" + "a" * 64
    provenance = {
        "schema_version": 1,
        "repository": "finger",
        "assets": [
            {"provenance_id": "prov-finger-finger-json-aaaaaaaa",
             "destination": "finger.json",
             "content_digest": digest,
             "origin_class": "original", "rights_basis": "maintainer-owned",
             "spdx": "Apache-2.0", "modifications": "",
             "required_notices": [], "contributor_authority": "maintainer-owned",
             "decision": "accepted", "reviewer": "repository-maintainer",
             "reason": "accepted"}
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = _run_generate(tmp, provenance)
        catalog = _load(path)
        assert len(catalog["capabilities"]) == len(_load(ROOT / "finger.json")["apps"])
        assert catalog["capabilities"][0]["provenance_id"] == "prov-finger-finger-json-aaaaaaaa"


def t_catalog_deterministic():
    provenance = {
        "schema_version": 1,
        "repository": "finger",
        "assets": []
    }
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        p1 = _run_generate(tmp1, provenance)
        p2 = _run_generate(tmp2, provenance)
        assert p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8")


def main():
    cases = [
        ("held asset excluded from catalog", t_held_asset_not_in_catalog),
        ("accepted asset included in catalog", t_accepted_asset_in_catalog),
        ("catalog deterministic", t_catalog_deterministic),
    ]
    print("finger gate tests")
    for name, fn in cases:
        case(name, fn)
    print()
    print(f"结果：{PASS} 通过，{FAIL} 失败，共 {PASS + FAIL} 项")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
