#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finger capability catalog generator (Ticket 03)

Reads finger.json + scripts/slugs.yaml + capabilities/rights/provenance.json
and writes a deterministic capabilities/catalog-v1.json containing only
accepted assets. A .sha256 sidecar is produced alongside.

Usage:
  uv run python scripts/generate_catalog.py --write
  uv run python scripts/generate_catalog.py --check   # verify existing catalog
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAP_DIR = ROOT / "capabilities"
SCHEMA_DIR = CAP_DIR / "schema"


def sha256_digest(text):
    if isinstance(text, str):
        text = text.encode("utf-8")
    return "sha256:" + hashlib.sha256(text).hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def write_canonical(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = canonical_json(obj)
    path.write_text(text, encoding="utf-8")
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(sha256_digest(text) + "\n", encoding="utf-8")
    return path


def load_finger_json():
    return json.loads((ROOT / "finger.json").read_text(encoding="utf-8"))


def load_slugs():
    return json.loads((ROOT / "scripts" / "slugs.json").read_text(encoding="utf-8"))["slugs"]


def load_provenance():
    path = CAP_DIR / "rights" / "provenance.json"
    if not path.is_file():
        return {"assets": []}
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc


def build_catalog(apps, slugs, provenance):
    accepted_by_dest = {a["destination"]: a for a in provenance.get("assets", [])
                        if a.get("decision") == "accepted"}
    # whole-file provenance record applies to all capabilities derived from that file
    file_prov = accepted_by_dest.get("finger.json")
    capabilities = []
    for key, app in sorted(apps.items()):
        slug = slugs.get(key)
        if not slug:
            continue
        prov = file_prov
        if not prov:
            continue
        caps = []
        for field in ("headers", "html", "meta", "scriptSrc", "cookies", "js", "url"):
            vals = app.get(field)
            if vals:
                caps.append(field)
        entry = {
            "id": slug,
            "kind": "fingerprint",
            "path": "finger.json",
            "contract": {
                "target_types": ["http-response"],
                "inputs": ["url", "headers", "body"],
                "positive_evidence": "matcher fields命中即识别为 " + key,
                "negative_or_failure": "无命中不证明不存在",
                "interface_version": "wappalyzer-v1",
            },
            "safety": "safe",
            "lifecycle": "active",
            "replacement": None,
            "provenance_id": prov["provenance_id"],
            "content_digest": prov["content_digest"],
            "components": [],
            "requires": [],
            "extensions": {
                "rbkd": {
                    "original_key": key,
                    "matcher_fields": caps,
                    "implies": app.get("implies", []),
                }
            },
        }
        capabilities.append(entry)
    return {
        "schema_version": 1,
        "repository": "finger",
        "capabilities": capabilities,
    }


def generate(write=False):
    apps = load_finger_json()["apps"]
    slugs = load_slugs()
    provenance = load_provenance()
    catalog = build_catalog(apps, slugs, provenance)
    catalog_path = CAP_DIR / "catalog-v1.json"
    if write:
        write_canonical(catalog_path, catalog)
        print(f"✓ wrote {catalog_path} ({len(catalog['capabilities'])} capabilities)")
    else:
        expected = canonical_json(catalog)
        actual = catalog_path.read_text(encoding="utf-8") if catalog_path.is_file() else ""
        if expected != actual:
            print("✗ catalog drift detected")
            return 1
        print("✓ catalog up to date")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write catalog and sidecar")
    args = parser.parse_args(argv)
    return generate(write=args.write)


if __name__ == "__main__":
    sys.exit(main())
