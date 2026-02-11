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
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line) as NewsItem;
      } catch {
        return null;
      }
    })
    .filter((item): item is NewsItem => Boolean(item))
    .sort((a, b) => b.published_at.localeCompare(a.published_at));
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
