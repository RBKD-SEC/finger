# finger

[RBKD-SEC] 自有 Web 指纹库，**FingerprintHub（observer_ward）yaml 格式**，作为 anchorscan 生态的自定义指纹源。

## 角色与沿革

- 2026-09 前身：为 httpx `-cff` 维护的 wappalyzergo 格式指纹库（`finger.json`，123 条国内常见 CMS/OA/安全设备指纹）；httpx 随 anchorscan ADR-0023 退役后冻结。
- 2026-09-16 转型（portfolio 任务 C 改向）：迁移为 FingerprintHub yaml 格式并持续维护，不归档。
- `finger.json` 保留为迁移源数据（legacy，只读）；日常增改指纹直接编辑 `web-fingerprint/`。

## 布局

```
web-fingerprint/00_unknown/<id>.yaml   # 指纹规则（上游 FingerprintHub 同 schema）
dist/observer-ward-fingerprints.json   # 构建产物：Template 数组，供 -p / 合并消费
docs/conversion-report.md              # wappalyzergo→FingerprintHub 转换报告（有损项逐条留痕）
scripts/convert_to_observer_ward.py    # 一次性迁移脚本（重跑可再生成，SLUG_MAP 可修订）
scripts/build_dist.py                  # yaml → dist 构建（--check 仅校验）
```

## 使用

observer_ward 直接加载（**注意：`-p` 整体替换官方库，单测验证用；生产消费走 anchorscan 的合并机制**）：

```bash
observer_ward -t http://target -p dist/observer-ward-fingerprints.json --debug
```

构建与校验（`uv run` / 仓内 `.venv`）：

```bash
.venv/bin/python scripts/build_dist.py --check
.venv/bin/python scripts/build_dist.py
```

## 编写约定

- schema 与上游 [0x727/FingerprintHub](https://github.com/0x727/FingerprintHub) 一致（其 README「规则说明」节为权威）；`id` 不支持中文，中文名条目进 `info.name`。
- `author` 写贡献者 GitHub handle（如 P0m32Kun）；`verified: true` 需实测证据。
- 通用可上游的指纹优先向上游提 PR（swagger 子路径、knife4j 已备料），本仓承载尚未合入或不愿上游的自有增量。
- **引擎陷阱**：`part: <header>` 在 header 缺失时按空串匹配——存在性语义用 `.+`，`.*` 是永真匹配；`condition: or` 需显式声明。
- 转换语义与已知有损项（弱信号丢弃、meta/js/implies 不迁移）见 `docs/conversion-report.md`。

## 许可

同仓 LICENSE / NOTICE。
