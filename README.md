# finger

为 [projectdiscovery/httpx](https://github.com/projectdiscovery/httpx) 补充的国内常见 Web 指纹库。

httpx 内置技术栈识别基于 [wappalyzergo](https://github.com/projectdiscovery/wappalyzergo)，对国外组件覆盖良好，但对国内常用的 CMS、OA、邮件系统、安全设备、运维面板、CDN/WAF 等覆盖很少。本仓库以 wappalyzer 兼容格式补齐这部分指纹，可直接通过 `-cff` / `-custom-fingerprint-file` 参数加载。

## 使用方法

httpx 0.0.7 以上版本（启用 `-tech-detect`）支持 `-custom-fingerprint-file`，将 `finger.json` 与默认指纹库合并使用：

```bash
httpx -l urls.txt -td -cff finger.json
```

只想使用本仓库指纹（不加载内置库），可使用 `wappalyzergo.NewFromFile(path, loadEmbedded=false, supersede=false)` 进行二次集成。

## 文件格式

`finger.json` 遵循 wappalyzergo 的官方 schema，结构为：

```json
{
  "apps": {
    "AppName": {
      "cats": [1],
      "description": "...",
      "website": "https://...",
      "icon": "AppName.png",
      "headers": { "header-name": "regex" },
      "cookies": { "cookie-name": "regex" },
      "html":     ["regex", "regex"],
      "scriptSrc":["regex"],
      "meta":     { "meta-name": ["regex"] },
      "dom":      { "css-selector": { "exists": "" } },
      "js":       { "window.var": "regex" },
      "url":      ["regex"],
      "implies":  ["OtherApp"]
    }
  }
}
```

关键约定：

- 所有匹配字段是 Go `regexp` 语法的正则，JSON 内需要双反斜杠转义（如 `\\d`、`\\.`）。
- 在正则末尾追加 `\\;version:\\1` 可用捕获组提取版本号。
- 在正则末尾追加 `\\;confidence:50` 可降低置信度（默认 100），多条 50 分会累加；置信度 0 等同于不构成证据，不要使用。
- `cats` 数字含义见 wappalyzergo 仓库的 [categories_data.json](https://github.com/projectdiscovery/wappalyzergo/blob/main/categories_data.json)（如 1=CMS，16=Security，22=Web servers，30=Webmail，31=CDN，37=Network devices，46=Remote access，50=DMS，65=Load balancers）。
- `implies` 用来联动出其他组件，例如检出 `ThinkPHP` 时自动补 `PHP`。
- `headers`/`cookies`/`meta` 的 key 一律小写。

## 已覆盖产品

当前 120 个指纹，分为以下几类：

### CMS / 建站
MetInfo、Empire CMS（帝国 CMS）、PbootCMS、74CMS（齐博）、苹果 CMS（maccms）、DouPHP、CmsEasy、SDCMS、JeecgBoot、JeeSite、RuoYi（若依）、JPress、JeeCMS、OneThink、HiShop、HDWiki、Z-BlogPHP、Typecho、Emlog、Discuz! Q、Halo。

### 论坛 / 社区
WeCenter、Tipask。

### OA / ERP
通达 OA、致远 OA、泛微 e-cology、泛微 e-office、泛微 e-mobile、蓝凌 OA、华天动力 OA、金和 OA、用友 NC/NCC、用友 U8、金蝶 EAS、金蝶云·星空、万户 OA。

### 邮件系统
Coremail、TurboMail、U-Mail、WinWebMail、Magic Winmail、亿邮邮件系统。

### 网络 / 安全设备
深信服 SSL VPN/AC/AF/EDR/WAF、奇安信天眼、奇安信网神 SecGate、绿盟 WAF/IPS、山石网科 Hillstone、天融信 NGFW/TopApp-LB、启明星辰天清汉马、安恒明御 WAF、安恒玄武盾、网御星云 SecFox、网康 NGFW、华为 USG、华为 eSpace、H3C、锐捷、海康威视、大华、宇视。

### 堡垒机 / 运维
JumpServer、齐治堡垒机、行云堡垒。

### 运维面板
宝塔面板、aaPanel、1Panel、小皮面板（phpStudy）。

### 编辑器 / 报表 / BI
KindEditor、UEditor、FineReport、FineBI、Smartbi、永洪 BI、DataEase。

### 协同 / SaaS
钉钉、企业微信、飞书 / Lark、小鹅通、石墨文档、金山文档、腾讯文档、Teambition、Tower。

### 监控 / 测试 / 知识库
Nightingale（夜莺）、MeterSphere、MaxKB、ShowDoc、YApi、Apifox、Eolinker。

### Web 服务器 / 容器
Tengine、OpenResty。

### CDN / WAF
加速乐（Jiasule）、ChinaCache、白山云 CDN、又拍云 CDN、七牛云 CDN、UCloud CDN、京东云 CDN、腾讯云 EdgeOne、阿里云 WAF、腾讯云 WAF、百度云 WAF、宝塔 WAF、安全狗、云锁、知道创宇创宇盾。

### 代码托管
Gitea（中文部署）、Gogs、Coding。

### 其他
PaddlePaddle、EasyImage、ChatGLM-Web、WordPress 国产主题。

## 校验

仓库的 `finger.json` 已用 `wappalyzergo.NewFromFile` 加载并通过样本回归测试。本地校验：

```bash
jq empty finger.json    # JSON 语法
```

最小的 Go 加载校验：

```go
client, err := wappalyzer.NewFromFile("finger.json", true, false)
if err != nil { log.Fatal(err) }
```

## 贡献

补充指纹时请保证：

1. 至少给出一个特异性较强的字段（独有 cookie/header、独有 script 路径、独有 favicon hash 替代字段、独有标题片段）；通用 cookie（如 `PHPSESSID`、`JSESSIONID`、`_csrf`）不要直接当作证据。
2. 多条 `html`/`scriptSrc` 越独立越好，能搭配组合证据更佳。
3. 正则尽量避免 `.*` 起手，必要的边界用 `^`/`$` 限制。
4. `cats` 一定要写，否则 wappalyzergo 会忽略整条指纹。
5. 若属于 wappalyzergo 已内置组件（参考其 [fingerprints_data.json](https://github.com/projectdiscovery/wappalyzergo/blob/main/fingerprints_data.json)），请勿重复添加。

提交前在本地至少跑一次 JSON 校验，最好附 1-2 个真实样本的命中验证。

## 参考资料

- httpx 仓库 https://github.com/projectdiscovery/httpx
- wappalyzergo 仓库 https://github.com/projectdiscovery/wappalyzergo
- httpx 增加 `-cff` 的提案 https://github.com/projectdiscovery/httpx/issues/1803
