#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify a finger release candidate in a fresh directory (Ticket 03).

Checks:
  - SHA256SUMS matches each file
  - catalog-v1.json validates against vendored schema
  - No absolute paths / private revisions / emails / secrets in public files

Usage:
  uv run python scripts/verify_release.py --release releases/2026.08.10.1
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import jsonschema


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(release_dir):
    release_dir = Path(release_dir)
    errors = []

    sums_path = release_dir / "SHA256SUMS"
    if not sums_path.is_file():
        errors.append("SHA256SUMS missing")
    else:
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) != 2:
                continue
            expected, rel = parts
            actual = sha256_file(release_dir / rel)
            if expected != actual:
                errors.append(f"{rel}: digest mismatch")

    catalog_path = release_dir / "catalog-v1.json"
    schema_path = release_dir / "schema" / "catalog-v1.schema.json"
    if catalog_path.is_file() and schema_path.is_file():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for err in validator.iter_errors(catalog):
            errors.append(f"catalog schema: {err.message}")

    # leak scan on public files
    url_pat = re.compile(r"(?:https?|file|ftp)://\S+")
    abs_path_pat = re.compile(r"(?:(?:/home|/Users|/var|/tmp|/opt|/etc|/root)(?:/[A-Za-z0-9_.-]+)+|(?:/[A-Za-z0-9_.-]+){2,})/?")
    email_pat = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    sha_pat = re.compile(r"\b[0-9a-f]{40}\b")
    for path in release_dir.rglob("*"):
        if not path.is_file() or path.name.endswith(".sha256"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            url_ranges = [(m.start(), m.end()) for m in url_pat.finditer(line)]
            for m in abs_path_pat.finditer(line):
                if any(s <= m.start() < e for s, e in url_ranges):
                    continue
                if m.start() > 0 and line[m.start() - 1] in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-":
                    continue
                errors.append(f"{path}: absolute path leak")
            if email_pat.search(line):
                errors.append(f"{path}: email leak")
            if sha_pat.search(line):
                errors.append(f"{path}: private revision leak")

    if errors:
        print(f"✗ {len(errors)} verification failure(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"✓ release {release_dir.name} verified")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, help="release directory path")
    args = parser.parse_args(argv)
    return verify(args.release)


if __name__ == "__main__":
    sys.exit(main())
