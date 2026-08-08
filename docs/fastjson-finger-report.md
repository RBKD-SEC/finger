# Fastjson 指纹条目 — 验收报告

## 条目内容

`finger.json` `apps.Fastjson`：

```json
{
  "cats": [18],
  "description": "Fastjson 是阿里巴巴开源的 Java JSON 库（com.alibaba.fastjson）。无 HTTP 头特征，仅在应用将 fastjson 异常/版本信息回显到响应时可识别（未捕获异常、JSON 接口报错回显场景）。主动探测见 nuclei http/technologies/fastjson-version.yaml。",
  "website": "https://github.com/alibaba/fastjson",
  "icon": "Fastjson.png",
  "html": [
    "com\\.alibaba\\.fastjson\\.JSONException",
    "fastjson-version",
    "autoType is not support",
    "fastjson-version.*?([0-9]+\\.[0-9]+\\.[0-9]+)\\;version:\\1"
  ]
}
```

## JSON 校验

```
$ python3 -c "import json; d=json.load(open('finger.json')); assert 'Fastjson' in d['apps']; print(len(d['apps']))"
123
```

- JSON 合法 ✓
- 条目数 123（原 122 + Fastjson）✓
- `Fastjson` 在 `apps` 中 ✓
- 仅 `finger.json` 修改（`git status` 确认）✓

## 四条 html 正则说明

| # | 正则 | 用途 |
|---|------|------|
| 1 | `com\.alibaba\.fastjson\.JSONException` | 匹配未捕获的 fastjson 异常类名回显 |
| 2 | `fastjson-version` | 匹配 `fastjson-version` 字符串（报错信息/调试输出） |
| 3 | `autoType is not support` | 匹配 fastjson autoType 安全限制触发的报错信息 |
| 4 | `fastjson-version.*?([0-9]+\.[0-9]+\.[0-9]+)\;version:\1` | 从报错中提取版本号（wappalyzer 版本提取语法） |

## 与 Wappalyzer 官方查重

- enthec/webappanalyzer（Wappalyzer 官方仓库）中**无 Fastjson 条目**——本条目为纯增量。
- 本条目为被动指纹（httpx `-cff` 场景，仅匹配响应体），与 nuclei `http/technologies/fastjson-version.yaml`（主动发包探测）互补，不重复。

## 分类

- `cats: [18]`（Web frameworks），与 finger.json 中已有 5 条分类一致。
- 插入位置：FineBI 之后、Smartbi 之前（F 字母序区域）。
- 未修改任何现有 122 条。
