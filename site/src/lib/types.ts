export type NewsItem = {
  id: string;
  source_id: string;
  source_name: string;
  title: string;
  url: string;
  canonical_url: string;
  published_at: string;
  fetched_at: string;
  summary?: string | null;
  keywords?: string[];
  content_type?: string | null;
  language?: string | null;
  region?: string | null;
};
