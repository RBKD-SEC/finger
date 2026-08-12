#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finger release gate validator (Ticket 03)

Checks:
  - catalog-v1.json validates against vendored schema
  - catalog sidecar matches
  - Every app in finger.json has a stable slug
  - Slug collisions / duplicate IDs
  - Regexes compile (headers/html/meta/scriptSrc/cookies/js/url)
  - Non-ASCII/space key count does not exceed baseline (touched-file ratchet)
  - Basic secret scan (no obvious private keys/tokens in finger.json)

Usage:
  uv run python scripts/validate_finger_gates.py
  exit 0 = passed, 1 = failed
"""
import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
BASELINE_NON_ASCII = 71


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_catalog_schema(errors):
    catalog_path = ROOT / "capabilities" / "catalog-v1.json"
    schema_path = ROOT / "capabilities" / "schema" / "catalog-v1.schema.json"
    if not catalog_path.is_file():
        errors.append("capabilities/catalog-v1.json missing")
        return
    if not schema_path.is_file():
        errors.append("capabilities/schema/catalog-v1.schema.json missing")
        return
    schema = load_json(schema_path)
    catalog = load_json(catalog_path)
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(catalog), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"catalog schema: {path}: {err.message}")


def check_sidecar(errors):
    catalog_path = ROOT / "capabilities" / "catalog-v1.json"
    sidecar_path = catalog_path.with_suffix(".json.sha256")
    if not sidecar_path.is_file():
        errors.append("capabilities/catalog-v1.json.sha256 missing")
        return
    text = catalog_path.read_text(encoding="utf-8")
    expected = "sha256:" + __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()
    actual = sidecar_path.read_text(encoding="utf-8").strip()
    if actual != expected:
        errors.append(f"catalog sidecar mismatch: expected {expected}, got {actual}")


def check_slugs(errors):
    apps = load_json(ROOT / "finger.json")["apps"]
    slugs = load_json(ROOT / "scripts" / "slugs.json")["slugs"]
    seen = {}
    for key in apps:
        if key not in slugs:
            errors.append(f"app '{key}' missing slug mapping")
            continue
        slug = slugs[key]
        if slug in seen:
            errors.append(f"slug collision: '{slug}' used by '{key}' and '{seen[slug]}'")
        else:
            seen[slug] = key


def check_regexes(errors):
    apps = load_json(ROOT / "finger.json")["apps"]
    for key, app in apps.items():
        for field in ("headers", "html", "meta", "scriptSrc", "cookies", "js", "url"):
            values = app.get(field)
            if not values:
                continue
            if isinstance(values, dict):
                values = [v for sub in values.values() for v in (sub if isinstance(sub, list) else [sub])]
            for pat in values:
                if not isinstance(pat, str):
                    continue
                try:
                    re.compile(pat)
                except re.error as exc:
                    errors.append(f"{key}.{field}: invalid regex '{pat[:40]}': {exc}")


def check_ratchet(errors):
    apps = load_json(ROOT / "finger.json")["apps"]
    non_ascii = sum(1 for key in apps if not re.fullmatch(r"[A-Za-z0-9._-]+", key))
    if non_ascii > BASELINE_NON_ASCII:
        errors.append(
            f"touched-file ratchet: non-ASCII/space keys increased from "
            f"{BASELINE_NON_ASCII} to {non_ascii}")
    print(f"  non-ASCII/space keys: {non_ascii} (baseline {BASELINE_NON_ASCII})")


def check_secrets(errors):
    text = (ROOT / "finger.json").read_text(encoding="utf-8")
    patterns = [
        ("private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
        ("aws key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("github pat", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ]
    for name, pat in patterns:
        if pat.search(text):
            errors.append(f"potential secret detected: {name}")


def main():
    errors = []
    print("Validating finger gates...")
    check_catalog_schema(errors)
    check_sidecar(errors)
    check_slugs(errors)
    check_regexes(errors)
    check_ratchet(errors)
    check_secrets(errors)
    if errors:
        print(f"\n✗ {len(errors)} gate failure(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\n✓ All finger gates passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
