# PolicyPulse · 金源观潮

> 说明：本仓库开源内容仅供学习与研究用途，不构成任何投资建议、交易建议或法律意见；使用者应自行评估风险并遵守相关法律法规与各信息源网站条款。

[![Daily crawl and deploy](https://github.com/ChenyuHeee/PolicyPulse/actions/workflows/daily.yml/badge.svg)](https://github.com/ChenyuHeee/PolicyPulse/actions/workflows/daily.yml)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-online-success)](https://chenyuheee.github.io/PolicyPulse/)
[![Last commit](https://img.shields.io/github/last-commit/ChenyuHeee/PolicyPulse)](https://github.com/ChenyuHeee/PolicyPulse/commits/main)
[![Stars](https://img.shields.io/github/stars/ChenyuHeee/PolicyPulse?style=social)](https://github.com/ChenyuHeee/PolicyPulse)

PolicyPulse 是一个 **GitHub 原生** 的金融政策/宏观信息聚合站：每天由 GitHub Actions 自动抓取官方源，数据直接落在仓库里（JSONL），随后构建静态站并部署到 GitHub Pages。

在线预览： https://chenyuheee.github.io/PolicyPulse/

## 目录

- [核心特性](#核心特性)
- [站点页面](#站点页面)
- [仓库结构](#仓库结构)
- [快速开始](#快速开始)
- [数据格式](#数据格式)
- [配置新闻源](#配置新闻源)
- [自动化与部署](#自动化与部署)
- [可选 Secrets](#可选-secrets)
- [常见问题](#常见问题)
- [贡献](#贡献)

## 核心特性

- **低运维**：无需数据库/服务器，数据直接 commit 到仓库
- **全自动**：定时（可手动）抓取 → 校验 → 有变化才提交 → 构建 → Pages 部署
- **信息密度导向**：面向金融从业者的紧凑排版，移动端可用
- **可扩展**：每个来源一个 adapter，RSS/HTML/API 均可接入

## 站点页面

- Latest：按时间线浏览最新条目
- Sources：按来源浏览与追踪
- Topics：按议题（宏观、利率、外汇、财政、监管等）聚合

## 仓库结构

- `crawler/`：Python 爬虫与校验
- `data/`：数据落盘（`news.jsonl`）与索引（`index.json`）
- `site/`：Astro + Tailwind 的静态站
- `.github/workflows/daily.yml`：自动化流水线（抓取+构建+部署）
- `docs/`：规划与来源说明
  - `docs/网站规划.md`
  - `docs/新闻源与获取方式.md`

## 快速开始

### 1) Python 环境

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) 运行爬虫与校验

```bash
python -m crawler crawl
python -m crawler validate
```

自定义数据路径：

```bash
python -m crawler crawl --data data/news.jsonl --index data/index.json
python -m crawler validate --data data/news.jsonl
```

### 3) 本地启动站点

```bash
cd site
npm install
npm run dev
```

## 数据格式

`data/news.jsonl` 每一行是一条 JSON 记录，字段示例：

- `id`：`sha256(source_id + canonical_url)`
- `source_id` / `source_name`
- `title` / `url` / `canonical_url`
- `published_at` / `fetched_at`（ISO 8601）
- `summary` / `keywords` / `content_type` / `language` / `region`

示例：

```json
{
  "id": "...",
  "source_id": "federal_reserve",
  "source_name": "Federal Reserve (FOMC/Press)",
  "title": "Federal Reserve issues FOMC statement",
  "url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240201a.htm",
  "canonical_url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240201a.htm",
  "published_at": "2024-02-01T19:00:00+00:00",
  "fetched_at": "2024-02-02T01:10:00+00:00",
  "summary": "...",
  "keywords": ["FOMC", "rate decision"],
  "content_type": "news",
  "language": "en",
  "region": "US"
}
```

## 配置新闻源

- 各来源 adapter：`crawler/sources/`
- 运行时配置（启用/禁用、URL、选择器、API 端点等）：`crawler/sources_config.yaml`

### 默认启用的来源（以 `crawler/sources_config.yaml` 为准）

当前默认启用覆盖中美欧英的典型官方源（HTML/RSS）：

- PBoC（人民银行）
- SAFE（外汇局）
- CSRC（证监会）
- MOF（财政部/国务院）
- NBS（国家统计局）
- Federal Reserve（美联储 RSS）
- ECB（欧洲央行 RSS）
- BoE（英格兰银行 RSS）
- BIS（国际清算银行 RSS）

启用一个来源：编辑 `crawler/sources_config.yaml`，将对应 `enabled: true`，并按需要补全配置项。

## 自动化与部署

工作流：`.github/workflows/daily.yml`

默认流程：

1. crawl + validate
2. 仅在 `data/` 变化时提交
3. 构建 Astro 静态站
4. 部署到 GitHub Pages

### GitHub Pages 设置

1. 仓库 Settings → Pages
2. Source 选择 “GitHub Actions”

本仓库为 **项目页（project pages）**，构建时会用 `BASE_PATH` 适配 `/PolicyPulse/` 这样的 base path。

## 可选 Secrets

部分 API 来源（默认禁用）需要 key 或合规 UA，可在 GitHub Secrets 配置：

- `FRED_API_KEY`
- `BLS_API_KEY`
- `BEA_API_KEY`
- `EIA_API_KEY`
- `SEC_USER_AGENT`

如果缺少所需 secret，对应来源会被跳过但不会中断全局流程。

## 常见问题

### 为什么有些来源默认禁用？

- API 来源：需要 key、速率限制与稳定性评估（例如 FRED/BLS/BEA/EIA/SEC 等）
- JS 渲染页面：不引入 headless 浏览器的前提下难以稳定抓取（例如部分交易所披露页）
- 特殊情况：IEA 在 GitHub hosted runner 上常见 HTTP 403，因此默认禁用（可自行本地/自托管 runner 运行）

## 贡献

欢迎提 PR：新增官方来源、改进分类/页面信息架构、优化抓取稳定性与日志。
