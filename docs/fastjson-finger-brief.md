# finger 任务书：新增 Fastjson 指纹条目

## 必读

1. 本文件（任务书即唯一事实来源）
2. `~/DEV/finger/README.md`（wappalyzer 兼容格式说明、httpx `-cff` 加载方式）
3. `~/DEV/finger/finger.json`（现有 122 条，格式参照：MetInfo 等条目的 html/meta 写法）

## 背景（编排方已核实）

- fastjson 是阿里巴巴开源的 Java JSON 库，**无 HTTP 头/cookie/静态资源特征**（后端库，非服务）
- 唯一可识别信号：**应用将 fastjson 异常/版本信息回显到响应**时（未捕获异常、开发环境、JSON 接口报错回显），响应体出现 fastjson 特征
- wappalyzer 官方（enthec/webappanalyzer）**无 Fastjson 条目**——本条目是纯增量
- nuclei 官方已有主动探测指纹（`http/technologies/fastjson-version.yaml`，发 `{"@type":"java.lang.AutoCloseable"` 触发报错）——本条目是**被动版**（httpx 场景，不主动发包，仅匹配响应特征），与 nuclei 互补不重复
- 分类：cats=18（Web frameworks，finger.json 已有 5 条使用 18）

## 任务

在 `~/DEV/finger/finger.json` 的 `apps` 中新增 **Fastjson** 条目（保持 JSON 合法、不破坏现有 122 条）：

```json
"Fastjson": {
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

要点：
- `html` 数组 4 个正则**逐字使用**（JSON 转义后写入）
- `\;version:\1` 是 wappalyzer 的版本提取语法（分号在 JSON 字符串里无需转义，但正则里 `\\` 需正确转义为 JSON 的 `\\\\`——写入时保持与现有条目一致的转义风格，参照 MetInfo 的 `\"\\\\;version:\\\\1\"` 写法）
- 插入位置：`apps` 对象内按字母序（Fastjson 应位于 F 开头条目附近；若该区域无条目则追加到文件合适位置，不强制重排）
- 不修改任何现有条目

## 铁律

1. 只改 `finger.json` 一个文件、只加这一个条目
2. JSON 必须合法：完成后 `python3 -c "import json; d=json.load(open('finger.json')); assert 'Fastjson' in d['apps']; print(len(d['apps']))"` 通过（应输出 123）
3. **禁止任何 git 操作**
4. 不删除/不修改现有 122 条的任何字段

## 验收

1. JSON 合法，条目数 123，`Fastjson` 在 `apps` 中
2. 四个 html 正则与任务书一致（版本提取正则含 `\;version:\1`）
3. `git status` 确认仅 finger.json 修改
4. 报告写入 `docs/fastjson-finger-report.md`：条目内容、JSON 校验输出、与 wappalyzer 官方查重结论（官方无此条目）
