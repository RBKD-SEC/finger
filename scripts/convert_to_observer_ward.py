#!/usr/bin/env python3
"""一次性迁移脚本：finger.json（wappalyzergo/httpx -cff 格式）→ FingerprintHub(observer_ward) yaml。

任务 C（portfolio-plan-2026-09-16）：123 条国内指纹迁入 observer_ward 生态。
转换语义（有损，报告见 docs/conversion-report.md）：
- html / scriptSrc 正则   → body regex matcher（OR）
- headers {名: 值正则}     → part:<header名> regex matcher（空正则=存在性；`\\;confidence:`/`\\;version:` 后缀剥除）
- cookies {名: 值正则}     → part:set-cookie regex matcher（cookie 名出现在 Set-Cookie 值中）
- meta / js / dom / url / implies → 丢弃（无对应语义或浏览器级；全部 123 条均有更强信号，覆盖无损）
- 中文名条目经 SLUG_MAP 固化 ascii id（人工核对，可在此表修订后重跑）
产物：web-fingerprint/00_unknown/<id>.yaml + docs/conversion-report.md
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "finger.json"
OUT_DIR = ROOT / "web-fingerprint" / "00_unknown"
REPORT = ROOT / "docs" / "conversion-report.md"
AUTHOR = "P0m32Kun"

# 中文名条目 → ascii slug（id 不支持中文）。产品英文官方名优先，无官方名用拼音。
SLUG_MAP = {
    "苹果CMS": "maccms",
    "通达OA": "tongda-oa",
    "致远OA": "seeyon-oa",
    "泛微e-cology": "weaver-e-cology",
    "泛微e-office": "weaver-e-office",
    "泛微e-mobile": "weaver-e-mobile",
    "蓝凌OA": "landray-oa",
    "华天动力OA": "huatian-oa",
    "金和OA": "jinhe-oa",
    "用友NC": "yonyou-nc",
    "用友U8": "yonyou-u8",
    "金蝶EAS": "kingdee-eas",
    "金蝶云·星空": "kingdee-cloud-galaxy",
    "亿邮邮件系统": "eyou-mail",
    "深信服SSL VPN": "sangfor-ssl-vpn",
    "深信服AC": "sangfor-ac",
    "深信服AF": "sangfor-af",
    "深信服EDR": "sangfor-edr",
    "深信服WAF": "sangfor-waf",
    "奇安信天眼": "qianxin-tianyan",
    "奇安信网神SecGate": "qianxin-secgate",
    "绿盟WAF": "nsfocus-waf",
    "绿盟IPS": "nsfocus-ips",
    "山石网科Hillstone": "hillstone",
    "天融信TopApp-LB": "topsec-topapp-lb",
    "天融信防火墙": "topsec-firewall",
    "启明星辰天清汉马": "venustech-tianqing-hanma",
    "安恒明御WAP": "anhen-mingyu-waf",
    "安恒明御WAF": "dbapp-mingyu-waf",
    "安恒玄武盾": "dbapp-xuanwudun",
    "网御星云SecFox": "leadsec-secfox",
    "网康NGFW": "netentsec-ngfw",
    "华为USG": "huawei-usg",
    "华为eSpace": "huawei-espace",
    "H3C设备": "h3c",
    "锐捷网络设备": "ruijie",
    "海康威视": "hikvision",
    "大华股份": "dahua",
    "宇视科技": "uniview",
    "齐治堡垒机": "qizhi-fortress",
    "行云堡垒": "xingyun-fortress",
    "宝塔面板": "bt-panel",
    "phpStudy小皮面板": "phpstudy-panel",
    "永洪BI": "yonghong-bi",
    "Nightingale夜莺监控": "nightingale",
    "钉钉开放平台": "dingtalk-open-platform",
    "企业微信": "wecom",
    "飞书Lark": "feishu-lark",
    "小鹅通": "xiaoe-tech",
    "石墨文档": "shimo-docs",
    "金山文档": "kingsoft-docs",
    "腾讯文档": "tencent-docs",
    "加速乐Jiasule": "jiasule",
    "白山云CDN": "baishan-cdn",
    "又拍云CDN": "upyun-cdn",
    "七牛云CDN": "qiniu-cdn",
    "京东云CDN": "jdcloud-cdn",
    "腾讯云EdgeOne": "tencent-edgeone",
    "阿里云WAF": "aliyun-waf",
    "腾讯云WAF": "tencent-cloud-waf",
    "百度云WAF": "baidu-cloud-waf",
    "Tower协作": "tower",
    "WordPress繁体中文": "wordpress-zh-tw",
    "Gitea中国镜像": "gitea-cn-mirror",
    "宝塔WAF": "bt-waf",
    "安全狗": "safedog",
    "云锁": "yunsuo",
}

# Rust regex 不兼容构造（lookaround / 反向引用），命中即整条 pattern 丢弃并记录
RUST_INCOMPATIBLE = re.compile(r"\(\?=<?!?|\\[1-9]")
# wappalyzergo 弱信号指令（\;confidence:N）——置信度模型在单规则 OR 语义下无法保真，
# 保留会把「需多信号佐证」降级成「任一弱信号即命中」，一律丢弃。
WEAK_SIGNAL = re.compile(r"\\;confidence:")


def strip_directives(pattern: str) -> str:
    """剥除 wappalyzergo 的 \\;version: / \\;confidence: 后缀指令。"""
    return re.split(r"\\;(?:version|confidence):", pattern)[0]


def slugify(name: str) -> str:
    if name in SLUG_MAP:
        return SLUG_MAP[name]
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    if not slug:
        raise ValueError(f"无法为 {name!r} 生成 ascii slug，请补充 SLUG_MAP")
    return slug


def convert(app_name: str, rule: dict) -> tuple[dict | None, list[str]]:
    """转换单条 wappalyzergo 规则；返回 (yaml 对象或 None, 备注)。"""
    notes = []
    matchers = []

    body_patterns = []
    for key in ("html", "scriptSrc"):
        for pattern in rule.get(key, []):
            if WEAK_SIGNAL.search(pattern):
                notes.append(f"丢弃 {key} 弱信号（confidence 降级语义无法保真）: {pattern[:60]}")
                continue
            core = strip_directives(pattern)
            if not core:
                continue
            if RUST_INCOMPATIBLE.search(core):
                notes.append(f"丢弃 {key} pattern（Rust regex 不兼容）: {core[:60]}")
                continue
            body_patterns.append(core)
    if body_patterns:
        matchers.append({"type": "regex", "regex": body_patterns, "case-insensitive": True})

    for header, value_regex in rule.get("headers", {}).items():
        # 弱信号（confidence<100）丢弃：见 WEAK_SIGNAL 注释
        if value_regex and WEAK_SIGNAL.search(value_regex):
            notes.append(f"丢弃 header {header} 弱信号（confidence 降级语义无法保真）")
            continue
        core = strip_directives(value_regex) if value_regex else ""
        if core and RUST_INCOMPATIBLE.search(core):
            notes.append(f"丢弃 header {header} pattern（Rust regex 不兼容）: {core[:60]}")
            continue
        matchers.append(
            {
                "type": "regex",
                "part": header.lower(),
                # 空正则=存在性语义：observer_ward 对缺失 header 按空串匹配，
                # 必须用 .+（非空）而非 .*（空串也命中=永真陷阱，实测）
                "regex": [core if core else ".+"],
                "case-insensitive": True,
            }
        )

    for cookie, value_regex in rule.get("cookies", {}).items():
        if value_regex and WEAK_SIGNAL.search(value_regex):
            notes.append(f"丢弃 cookie {cookie} 弱信号（confidence 降级语义无法保真）")
            continue
        core = strip_directives(value_regex) if value_regex else ""
        pattern = re.escape(cookie)
        if core and RUST_INCOMPATIBLE.search(core):
            notes.append(f"丢弃 cookie {cookie} 值正则（Rust regex 不兼容），退化为 cookie 名匹配")
        elif core:
            pattern += f"=[^;]*{core}"
        matchers.append(
            {
                "type": "regex",
                "part": "set-cookie",
                "regex": [pattern],
                "case-insensitive": True,
            }
        )

    for dropped in ("meta", "js", "dom", "url", "implies"):
        if rule.get(dropped):
            notes.append(f"丢弃 {dropped} 信号（无 observer_ward 对应语义）")

    if not matchers:
        return None, notes + ["无可转换信号，整条跳过"]

    slug = slugify(app_name)
    info = {
        "name": app_name,
        "author": AUTHOR,
        "tags": f"detect,tech,{slug}",
        "severity": "info",
        "metadata": {"product": slug, "vendor": "00_unknown", "verified": False},
    }
    if rule.get("description"):
        info["description"] = rule["description"]
    if rule.get("website"):
        info["reference"] = [rule["website"]]
    template = {
        "id": slug,
        "info": info,
        "http": [
            {
                "method": "GET",
                "path": ["{{BaseURL}}/"],
                "matchers": matchers,
            }
        ],
    }
    return template, notes


def main() -> int:
    apps = json.loads(SOURCE.read_text())["apps"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# wappalyzergo → FingerprintHub 转换报告",
        "",
        f"源：finger.json（{len(apps)} 条）｜生成：scripts/convert_to_observer_ward.py｜author：{AUTHOR}",
        "",
        "| 应用 | 输出 id | 转换备注 |",
        "| --- | --- | --- |",
    ]
    converted = skipped = 0
    for app_name, rule in sorted(apps.items()):
        template, notes = convert(app_name, rule)
        if template is None:
            skipped += 1
            report_lines.append(f"| {app_name} | （跳过） | {'；'.join(notes)} |")
            continue
        out = OUT_DIR / f"{template['id']}.yaml"
        out.write_text(
            yaml.safe_dump(template, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        converted += 1
        report_lines.append(
            f"| {app_name} | {template['id']} | {'；'.join(notes) if notes else '完整转换'} |"
        )
    REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"转换完成：{converted} 条落 yaml，{skipped} 条跳过；报告 {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
