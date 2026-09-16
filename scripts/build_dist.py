#!/usr/bin/env python3
"""构建 dist：web-fingerprint/**/*.yaml → dist/observer-ward-fingerprints.json。

产物是 FingerprintHub web_fingerprint_v4.json 同 schema 的 Template 数组，
供 anchorscan 与官方库做 concat 合并后经 observer_ward `-p` 消费。
--check 只校验不落盘：yaml 可解析、字段齐全、id 唯一、无重复探针。
"""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web-fingerprint"
DIST = ROOT / "dist" / "observer-ward-fingerprints.json"

REQUIRED_INFO = {"name", "author", "tags", "severity"}


def load_templates() -> list[dict]:
    templates = []
    ids: set[str] = set()
    for path in sorted(SRC.rglob("*.yaml")):
        template = yaml.safe_load(path.read_text())
        if not isinstance(template, dict) or "id" not in template:
            raise SystemExit(f"{path}: 缺 id 或结构非法")
        if template["id"] in ids:
            raise SystemExit(f"{path}: 重复 id {template['id']}")
        ids.add(template["id"])
        info = template.get("info") or {}
        missing = REQUIRED_INFO - set(info)
        if missing:
            raise SystemExit(f"{path}: info 缺字段 {sorted(missing)}")
        if not template.get("http"):
            raise SystemExit(f"{path}: 缺 http 探针")
        templates.append(template)
    return templates


def main() -> int:
    templates = load_templates()
    if "--check" in sys.argv:
        print(f"check ok: {len(templates)} 条指纹，id 唯一、结构完整")
        return 0
    DIST.parent.mkdir(parents=True, exist_ok=True)
    DIST.write_text(json.dumps(templates, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"built {DIST}: {len(templates)} 条指纹")
    return 0


if __name__ == "__main__":
    sys.exit(main())
