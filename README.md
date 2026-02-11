# PolicyPulse (PolicyPulse)

PolicyPulse is a GitHub-native, fully automated financial news aggregation site. It crawls official sources daily, stores data inside the repo, builds a static site, and deploys to GitHub Pages.

## Features

- Daily scheduled crawl with GitHub Actions (manual trigger supported)
- Source-by-source adapters with clean logs and graceful failure handling
- JSONL storage inside the repo with stable IDs and deduplication
- Astro + TailwindCSS static site, mobile friendly
- Zero external servers or databases

## Repository layout

- `crawler/` Python crawler and validator
- `data/` JSONL data and index
- `site/` Astro static site
- `.github/workflows/daily.yml` automation pipeline

## Data schema (JSONL)

Each line in `data/news.jsonl` is a JSON object with the following fields:

- `id` (string, required): sha256 of `source_id + canonical_url`
- `source_id` (string, required)
- `source_name` (string, required)
- `title` (string, required)
- `url` (string, required)
- `canonical_url` (string, required)
- `published_at` (string, required, ISO 8601)
- `fetched_at` (string, required, ISO 8601)
- `summary` (string, optional)
- `keywords` (array of strings, optional)
- `content_type` (string, optional)
- `language` (string, optional)
- `region` (string, optional)

Example:

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

## Local usage

### 1) Set up Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Run crawler

```bash
python -m crawler crawl
python -m crawler validate
```

Custom paths:

```bash
python -m crawler crawl --data data/news.jsonl --index data/index.json
python -m crawler validate --data data/news.jsonl
```

Data files will update in `data/`.

### 3) Run the site

```bash
cd site
npm install
npm run dev
```

## Configure sources

Source definitions live in `crawler/sources/` (one module per source). Runtime settings and enabling live in `crawler/sources_config.yaml`.

### Enabled sources (default)

- China Securities Regulatory Commission (CSRC) news
  - List page: https://www.csrc.gov.cn/csrc/c100028/common_list.shtml
- National Financial Regulatory Administration (NFRA) regulatory updates (API)
  - API: https://www.nfra.gov.cn/cbircweb/DocInfo/SelectDocByItemIdAndChild
- Ministry of Finance (MOF) policy releases
  - List page: https://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/
- State Administration of Foreign Exchange (SAFE) news
  - List page: https://www.safe.gov.cn/safe/whxw/index.html
- People's Bank of China (PBoC) news
  - List page: https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html
- Bank of England (BoE) news (RSS)
  - Feed: https://www.bankofengland.co.uk/rss/news
  - Source index: https://www.bankofengland.co.uk/rss
- European Central Bank (ECB) press releases, speeches, and interviews (RSS)
  - Feed: https://www.ecb.europa.eu/rss/press.html
- Federal Reserve press releases (RSS)
  - Feed: https://www.federalreserve.gov/feeds/press_all.xml
  - Source index: https://www.federalreserve.gov/feeds/default.htm
- FRED release dates (API)
  - API: https://api.stlouisfed.org/fred/releases/dates
- U.S. Bureau of Labor Statistics (BLS) unemployment series (API)
  - API: https://api.bls.gov/publicAPI/v1/timeseries/data/LNS14000000
- National Bureau of Statistics of China (NBS) data releases (HTML list)
  - List page: https://www.stats.gov.cn/sj/zxfb/
  - Rationale: official “数据发布” list with stable list entries and dates

To enable a source:

1. Open `crawler/sources_config.yaml`
2. Set `enabled: true` for the source
3. Fill in adapter config (feed URLs, endpoints, selectors, etc.)
4. Add secrets if required (see below)

To add a new source:

1. Create a new source module in `crawler/sources/`
2. Add it to `crawler/sources/registry.py`
3. Add a config block in `crawler/sources_config.yaml`
4. Implement the adapter config (RSS, HTML, or API)

## GitHub Actions

The workflow `.github/workflows/daily.yml` runs daily at 01:00 UTC and supports manual trigger.

It performs:

1. Crawl and validate data
2. Commit `data/` changes (only if changed)
3. Build Astro site
4. Deploy to GitHub Pages

## Secrets

Some sources require API keys or a compliant User-Agent. Configure these in GitHub Secrets:

- `FRED_API_KEY`
- `BLS_API_KEY`
- `BEA_API_KEY`
- `EIA_API_KEY`
- `SEC_USER_AGENT`

If a required secret is missing, the crawler will skip that source and continue.

## Enable GitHub Pages

1. Go to Repository Settings -> Pages
2. Set Source to "GitHub Actions"
3. Save

## Notes

- No external database is used; all data is committed to the repo.
- Default retention is disabled (full history). You can enable retention in `crawler/sources_config.yaml` if desired.
