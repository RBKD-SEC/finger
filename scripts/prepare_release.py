#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepare an immutable CalVer release candidate for finger (Ticket 03).

Outputs:
  releases/<calver>/
    catalog-v1.json
    catalog-v1.json.sha256
    schema/catalog-v1.schema.json + SHA256SUMS
    LICENSE
    NOTICE
    rights/provenance.json
    rights-report.md

Usage:
  uv run python scripts/prepare_release.py --calver 2026.08.10.1
"""
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def write_digest_list(release_dir, files):
    lines = []
    for rel in files:
        p = release_dir / rel
        lines.append(f"{sha256_file(p)[7:]}  {rel}")
    (release_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare(calver):
    release_dir = ROOT / "releases" / calver
    if release_dir.exists():
        print(f"release {calver} already exists", file=sys.stderr)
        return 1
    release_dir.mkdir(parents=True)

    # catalog + sidecar
    shutil.copy2(ROOT / "capabilities" / "catalog-v1.json",
                 release_dir / "catalog-v1.json")
    shutil.copy2(ROOT / "capabilities" / "catalog-v1.json.sha256",
                 release_dir / "catalog-v1.json.sha256")

    # schema
    schema_dir = release_dir / "schema"
    schema_dir.mkdir()
    shutil.copy2(ROOT / "capabilities" / "schema" / "catalog-v1.schema.json",
                 schema_dir / "catalog-v1.schema.json")
    shutil.copy2(ROOT / "capabilities" / "schema" / "SHA256SUMS",
                 schema_dir / "SHA256SUMS")

    # rights
    rights_dir = release_dir / "rights"
    rights_dir.mkdir()
    shutil.copy2(ROOT / "capabilities" / "rights" / "provenance.json",
                 rights_dir / "provenance.json")

    # license/notice
    shutil.copy2(ROOT / "LICENSE", release_dir / "LICENSE")
    shutil.copy2(ROOT / "NOTICE", release_dir / "NOTICE")

    # rights report
    report = [
        f"# finger {calver} Rights and Provenance Report",
        "",
        f"Release: `{calver}`",
        f"Prepared: {datetime.now(timezone.utc).isoformat()}",
        "",
        "All fingerprint assets in this release are currently held pending "
        "maintainer/rights-officer provenance review. The public catalog is therefore empty.",
        "",
        "See `rights/provenance.json` for per-asset status.",
        ""
    ]
    (release_dir / "rights-report.md").write_text("\n".join(report), encoding="utf-8")

    files = [
        "catalog-v1.json",
        "schema/catalog-v1.schema.json",
        "schema/SHA256SUMS",
        "LICENSE",
        "NOTICE",
        "rights/provenance.json",
        "rights-report.md",
    ]
    write_digest_list(release_dir, files)
    print(f"✓ prepared release candidate at {release_dir}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calver", required=True, help="CalVer release id, e.g. 2026.08.10.1")
    args = parser.parse_args(argv)
    return prepare(args.calver)


if __name__ == "__main__":
    sys.exit(main())
