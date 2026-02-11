import fs from "node:fs";
import path from "node:path";
import type { NewsItem } from "./types";

const DATA_PATH = path.resolve(process.cwd(), "..", "data", "news.jsonl");
const INDEX_PATH = path.resolve(process.cwd(), "..", "data", "index.json");

type SourceRunStatus = {
  fetched?: number;
  new?: number;
  skipped?: number;
  status?: string;
  failure_streak?: number;
  zero_new_streak?: number;
  last_run?: string;
  last_error?: string;
};

type IndexPayload = {
  last_run?: {
    sources?: Record<string, SourceRunStatus>;
  };
};

export function loadNews(): NewsItem[] {
  if (!fs.existsSync(DATA_PATH)) {
    return [];
  }
  const raw = fs.readFileSync(DATA_PATH, "utf-8");
  if (!raw.trim()) {
    return [];
  }
  return raw
    .split("\n")
    .map((line: string) => line.trim())
    .filter(Boolean)
    .map((line: string): NewsItem | null => {
      try {
        return JSON.parse(line) as NewsItem;
      } catch {
        return null;
      }
    })
    .filter((item): item is NewsItem => Boolean(item))
    .sort((a: NewsItem, b: NewsItem) => b.published_at.localeCompare(a.published_at));
}

export function getNewsPage(page: number, perPage = 30) {
  const items = loadNews();
  const totalPages = Math.max(1, Math.ceil(items.length / perPage));
  const safePage = Math.min(Math.max(page, 1), totalPages);
  const start = (safePage - 1) * perPage;
  return {
    items: items.slice(start, start + perPage),
    totalPages,
    currentPage: safePage,
    totalItems: items.length,
  };
}

export function getLatestBySource(limitPerSource = 6) {
  const items = loadNews();
  const perSource: Record<
    string,
    { id: string; name: string; items: NewsItem[]; latest: string }
  > = {};

  for (const item of items) {
    const bucket = perSource[item.source_id];
    if (!bucket) {
      perSource[item.source_id] = {
        id: item.source_id,
        name: item.source_name || item.source_id,
        items: [item],
        latest: item.published_at,
      };
      continue;
    }

    if (bucket.items.length >= limitPerSource) {
      continue;
    }
    bucket.items.push(item);
  }

  return Object.values(perSource).sort((a, b) => b.latest.localeCompare(a.latest));
}

export function getSourcesSummary() {
  const items = loadNews();
  const summary: Record<string, { name: string; count: number }> = {};
  for (const item of items) {
    if (!summary[item.source_id]) {
      summary[item.source_id] = { name: item.source_name, count: 0 };
    }
    summary[item.source_id].count += 1;
  }
  return Object.entries(summary)
    .map(([id, data]) => ({ id, ...data }))
    .sort((a, b) => b.count - a.count);
}

export type TopicId =
  | "rates_liquidity"
  | "fx_crossborder"
  | "macro_data"
  | "regulation"
  | "fiscal"
  | "stability_risk"
  | "real_estate_credit"
  | "trade_industry"
  | "capital_markets"
  | "banking_insurance";

export const TOPIC_LABELS: Record<TopicId, string> = {
  rates_liquidity: "利率/流动性",
  fx_crossborder: "外汇/跨境",
  macro_data: "宏观数据",
  regulation: "监管/规则",
  fiscal: "财政/预算",
  stability_risk: "金融稳定/风险",
  real_estate_credit: "地产/信用",
  trade_industry: "贸易/产业",
  capital_markets: "资本市场",
  banking_insurance: "银行/保险",
};

export type EventTypeId =
  | "policy"
  | "data"
  | "regulation"
  | "speech"
  | "operations"
  | "risk";

export const EVENT_LABELS: Record<EventTypeId, string> = {
  policy: "政策",
  data: "数据",
  regulation: "监管",
  speech: "讲话",
  operations: "操作",
  risk: "风险",
};

function includesAny(haystack: string, needles: string[]) {
  return needles.some((needle) => haystack.includes(needle));
}

export function classifyTopics(item: NewsItem): TopicId[] {
  const title = (item.title || "").toLowerCase();
  const summary = (item.summary || "").toLowerCase();
  const sourceId = (item.source_id || "").toLowerCase();
  const contentType = (item.content_type || "").toLowerCase();
  const text = `${title}\n${summary}\n${contentType}`;

  const topics = new Set<TopicId>();

  // Source priors.
  if (["pboc", "federal_reserve", "ecb", "boe"].includes(sourceId)) {
    topics.add("rates_liquidity");
  }
  if (sourceId === "safe") {
    topics.add("fx_crossborder");
  }
  if (sourceId === "nbs") {
    topics.add("macro_data");
  }
  if (sourceId === "mof_state_council" || sourceId === "mof") {
    topics.add("fiscal");
  }
  if (sourceId === "csrc") {
    topics.add("capital_markets");
    topics.add("regulation");
  }
  if (sourceId === "nfra") {
    topics.add("banking_insurance");
    topics.add("regulation");
  }

  if (
    includesAny(text, [
      "interest rate",
      "policy rate",
      "benchmark",
      "repo",
      "rrr",
      "reserve requirement",
      "mlf",
      "omo",
      "liquidity",
      "yield",
      "rate cut",
      "rate hike",
      "利率",
      "降息",
      "加息",
      "公开市场",
      "逆回购",
      "lpr",
      "准备金",
      "流动性",
    ])
  ) {
    topics.add("rates_liquidity");
  }

  if (
    includesAny(text, [
      "fx",
      "foreign exchange",
      "exchange rate",
      "capital flow",
      "cross-border",
      "remittance",
      "usd",
      "cny",
      "rmb",
      "外汇",
      "汇率",
      "跨境",
      "资本流动",
      "结售汇",
      "收支",
    ])
  ) {
    topics.add("fx_crossborder");
  }

  if (
    includesAny(text, [
      "cpi",
      "ppi",
      "gdp",
      "employment",
      "unemployment",
      "retail sales",
      "industrial production",
      "pmi",
      "inflation",
      "growth",
      "宏观",
      "国内生产总值",
      "就业",
      "失业",
      "社融",
      "信贷",
      "进出口",
      "工业",
      "零售",
    ])
  ) {
    topics.add("macro_data");
  }

  if (
    includesAny(text, [
      "bond",
      "bonds",
      "stock",
      "equity",
      "ipo",
      "listing",
      "delisting",
      "futures",
      "derivative",
      "fund",
      "etf",
      "asset management",
      "securities",
      "capital market",
      "债券",
      "国债",
      "地方债",
      "股票",
      "上市",
      "退市",
      "ipo",
      "再融资",
      "并购",
      "重组",
      "期货",
      "衍生品",
      "基金",
      "etf",
      "资管",
      "证券",
      "资本市场",
    ])
  ) {
    topics.add("capital_markets");
  }

  if (
    includesAny(text, [
      "bank",
      "banking",
      "insurance",
      "insurer",
      "capital adequacy",
      "basel",
      "npl",
      "provision",
      "deposit",
      "loan",
      "credit",
      "金融机构",
      "银行",
      "保险",
      "偿付能力",
      "资本充足",
      "不良",
      "拨备",
      "存款",
      "贷款",
      "信贷",
      "授信",
    ])
  ) {
    topics.add("banking_insurance");
  }

  if (
    includesAny(text, [
      "regulation",
      "supervision",
      "guideline",
      "compliance",
      "rule",
      "consultation",
      "监管",
      "监督",
      "条例",
      "办法",
      "征求意见",
      "合规",
      "行政处罚",
    ])
  ) {
    topics.add("regulation");
  }

  if (
    includesAny(text, [
      "budget",
      "treasury",
      "bond issuance",
      "deficit",
      "tax",
      "fiscal",
      "财政",
      "预算",
      "国债",
      "地方债",
      "赤字",
      "税",
    ])
  ) {
    topics.add("fiscal");
  }

  if (
    includesAny(text, [
      "financial stability",
      "stress",
      "risk",
      "crisis",
      "resolution",
      "default",
      "bank run",
      "金融稳定",
      "风险",
      "处置",
      "违约",
      "挤兑",
    ])
  ) {
    topics.add("stability_risk");
  }

  if (
    includesAny(text, [
      "property",
      "real estate",
      "mortgage",
      "credit",
      "housing",
      "developer",
      "地产",
      "房地产",
      "按揭",
      "房贷",
      "信用",
      "融资",
    ])
  ) {
    topics.add("real_estate_credit");
  }

  if (
    includesAny(text, [
      "trade",
      "tariff",
      "export",
      "import",
      "supply chain",
      "manufacturing",
      "semiconductor",
      "energy",
      "贸易",
      "关税",
      "出口",
      "进口",
      "供应链",
      "制造业",
      "产业",
      "芯片",
      "能源",
    ])
  ) {
    topics.add("trade_industry");
  }

  const ordered: TopicId[] = [
    "rates_liquidity",
    "fx_crossborder",
    "macro_data",
    "regulation",
    "fiscal",
    "stability_risk",
    "real_estate_credit",
    "trade_industry",
  ];
  return ordered.filter((t) => topics.has(t));
}

export function classifyEventType(item: NewsItem): EventTypeId {
  const title = (item.title || "").toLowerCase();
  const summary = (item.summary || "").toLowerCase();
  const sourceId = (item.source_id || "").toLowerCase();
  const contentType = (item.content_type || "").toLowerCase();
  const text = `${title}\n${summary}\n${contentType}`;

  // Source priors.
  if (sourceId === "nbs") {
    return "data";
  }

  // Regulation first (often very specific signals).
  if (
    includesAny(text, [
      "regulation",
      "supervision",
      "guideline",
      "compliance",
      "rule",
      "consultation",
      "enforcement",
      "监管",
      "监督",
      "条例",
      "办法",
      "征求意见",
      "合规",
      "行政处罚",
    ])
  ) {
    return "regulation";
  }

  // Macro / data releases.
  if (
    includesAny(text, [
      "cpi",
      "ppi",
      "gdp",
      "employment",
      "unemployment",
      "retail sales",
      "industrial production",
      "pmi",
      "inflation",
      "macro data",
      "发布",
      "公布",
      "统计",
      "国内生产总值",
      "就业",
      "失业",
      "社融",
      "信贷",
      "进出口",
      "工业",
      "零售",
    ])
  ) {
    return "data";
  }

  // Speeches / remarks.
  if (
    includesAny(text, [
      "speech",
      "remarks",
      "testimony",
      "press conference",
      "statement",
      "minutes",
      "讲话",
      "发言",
      "致辞",
      "记者会",
      "声明",
      "纪要",
    ])
  ) {
    return "speech";
  }

  // Market operations.
  if (
    includesAny(text, [
      "repo",
      "reverse repo",
      "rrr",
      "reserve requirement",
      "mlf",
      "omo",
      "auction",
      "liquidity",
      "公开市场",
      "逆回购",
      "准备金",
      "流动性",
      "操作",
    ])
  ) {
    return "operations";
  }

  // Risk.
  if (
    includesAny(text, [
      "financial stability",
      "stress",
      "risk",
      "crisis",
      "resolution",
      "default",
      "金融稳定",
      "风险",
      "处置",
      "违约",
    ])
  ) {
    return "risk";
  }

  // Default to policy for central-bank / official communications.
  if (["pboc", "federal_reserve", "ecb", "boe", "safe"].includes(sourceId)) {
    return "policy";
  }

  return "policy";
}

export function getLatestByTopic(limitPerTopic = 10) {
  const items = loadNews();
  const perTopic: Partial<
    Record<TopicId, { id: TopicId; label: string; items: NewsItem[]; latest: string }>
  > = {};

  for (const item of items) {
    const topics = classifyTopics(item);
    for (const topic of topics) {
      const bucket = perTopic[topic];
      if (!bucket) {
        perTopic[topic] = {
          id: topic,
          label: TOPIC_LABELS[topic],
          items: [item],
          latest: item.published_at,
        };
        continue;
      }
      if (bucket.items.length >= limitPerTopic) {
        continue;
      }
      bucket.items.push(item);
    }
  }

  return Object.values(perTopic)
    .filter(Boolean)
    .sort((a, b) => (b!.latest || "").localeCompare(a!.latest || "")) as Array<{
    id: TopicId;
    label: string;
    items: NewsItem[];
    latest: string;
  }>;
}

export function getTopicsSummary() {
  const items = loadNews();
  const summary: Partial<
    Record<
      TopicId,
      {
        id: TopicId;
        label: string;
        count: number;
        latest: string;
      }
    >
  > = {};

  for (const item of items) {
    const topics = classifyTopics(item);
    for (const topic of topics) {
      const bucket = summary[topic];
      if (!bucket) {
        summary[topic] = {
          id: topic,
          label: TOPIC_LABELS[topic],
          count: 1,
          latest: item.published_at,
        };
        continue;
      }
      bucket.count += 1;
      if (item.published_at > bucket.latest) {
        bucket.latest = item.published_at;
      }
    }
  }

  return Object.values(summary)
    .filter(Boolean)
    .sort((a, b) => (b!.latest || "").localeCompare(a!.latest || "")) as Array<{
    id: TopicId;
    label: string;
    count: number;
    latest: string;
  }>;
}

function loadIndex(): IndexPayload | null {
  if (!fs.existsSync(INDEX_PATH)) {
    return null;
  }
  try {
    const raw = fs.readFileSync(INDEX_PATH, "utf-8");
    return JSON.parse(raw) as IndexPayload;
  } catch {
    return null;
  }
}

export function getSourceStatusMap(): Record<string, SourceRunStatus> {
  const index = loadIndex();
  return index?.last_run?.sources ?? {};
}
