/**
 * 核心 TypeScript 类型定义
 *
 * 统一导出所有类型接口，供前端组件和 API 客户端使用。
 */

// ─── API 响应信封 ───────────────────────────────────────────

/** 后端统一 JSON 响应格式 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/** 分页响应数据 */
export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** 分页响应 */
export type PaginatedResponse<T> = ApiResponse<PaginatedData<T>>;

// ─── 用户 ───────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  display_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ─── 监控组 ─────────────────────────────────────────────────

export interface MonitorGroup {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// ─── 资讯源 ─────────────────────────────────────────────────

export type SourceType = 'rss' | 'web';
export type CollectStatus = 'success' | 'error';

export interface Source {
  id: string;
  name: string;
  url: string;
  source_type: SourceType;
  monitor_group_id: string;
  is_enabled: boolean;
  collect_interval_minutes: number;
  last_collected_at: string | null;
  last_collect_status: CollectStatus | null;
  last_error_message: string | null;
  created_at: string;
  updated_at: string;
}

// ─── 资讯 ───────────────────────────────────────────────────

export type ProcessingStatus = 'pending' | 'processing' | 'processed' | 'failed';

export type TagType = 'brand' | 'monitor_group' | 'content_type' | 'keyword';

export interface ArticleTag {
  id: string;
  article_id: string;
  tag_type: TagType;
  tag_value: string;
  is_auto: boolean;
  created_at: string;
}

export interface Article {
  id: string;
  source_id: string;
  original_title: string;
  original_url: string;
  original_language: string;
  original_excerpt: string | null;
  chinese_summary: string | null;
  published_at: string | null;
  collected_at: string;
  processing_status: ProcessingStatus;
  tags: ArticleTag[];
  is_bookmarked?: boolean;
  is_topic_candidate?: boolean;
  created_at: string;
  updated_at: string;
}

export interface ArticleFilters {
  brand?: string;
  monitor_group?: string;
  content_type?: string;
  start_date?: string;
  end_date?: string;
  keyword?: string;
  status?: ProcessingStatus;
  page?: number;
  page_size?: number;
}

// ─── 收藏与待选题 ───────────────────────────────────────────

export interface Bookmark {
  id: string;
  user_id: string;
  article_id: string;
  article?: Article;
  created_at: string;
}

export interface TopicCandidate {
  id: string;
  user_id: string;
  article_id: string;
  article?: Article;
  created_at: string;
}

// ─── 每日简报 ───────────────────────────────────────────────

export interface BriefingHighlight {
  article_id: string;
  title: string;
  summary: string;
}

export interface BriefingSection {
  monitor_group: string;
  highlights: BriefingHighlight[];
}

export interface BriefingContent {
  summary: string;
  sections: BriefingSection[];
  trends: string[];
  follow_up_suggestions: string[];
}

export interface DailyBriefing {
  id: string;
  briefing_date: string;
  content: BriefingContent;
  has_new_articles: boolean;
  created_at: string;
}

// ─── 知识库 ─────────────────────────────────────────────────

export type KnowledgeCategory =
  | 'brand_profile'
  | 'style_history'
  | 'classic_item'
  | 'person_profile';

export interface KnowledgeEntry {
  id: string;
  title: string;
  category: KnowledgeCategory;
  content: Record<string, unknown>;
  summary: string | null;
  brands: string[];
  keywords: string[];
  created_at: string;
  updated_at: string;
}

// ─── 深度分析 ─────────────────────────────────────────────────

export interface DeepAnalysis {
  id: string;
  article_id: string;
  importance: string;
  industry_background: string;
  follow_up_suggestions: string;
  created_at: string;
}

// ─── 品牌 ───────────────────────────────────────────────────

export interface Brand {
  id: string;
  name_zh: string;
  name_en: string;
  official_name: string | null;
  social_media_name: string | null;
  naming_notes: string | null;
  monitor_group_id: string;
  created_at: string;
  updated_at: string;
}

export type LogoType = 'main' | 'horizontal' | 'icon' | 'monochrome' | 'other';
export type LogoFormat = 'png' | 'svg' | 'jpg';

export interface BrandLogo {
  id: string;
  brand_id: string;
  file_name: string;
  file_path: string;
  file_format: LogoFormat;
  logo_type: LogoType;
  file_size_bytes: number | null;
  thumbnail_path: string | null;
  created_at: string;
}

// ─── 关键词 ─────────────────────────────────────────────────

export interface Keyword {
  id: string;
  word_zh: string;
  word_en: string;
  monitor_group_id: string;
  created_at: string;
  updated_at: string;
}

// ─── AI 提供者 ──────────────────────────────────────────────

export interface AIProvider {
  id: string;
  name: string;
  api_key_masked: string;
  api_base_url: string;
  model_name: string;
  is_preset: boolean;
  is_active: boolean;
  last_test_at: string | null;
  last_test_status: 'success' | 'failed' | null;
  last_test_error: string | null;
  created_at: string;
  updated_at: string;
}

export type AIErrorType =
  | 'auth_failed'
  | 'quota_exceeded'
  | 'network_timeout'
  | 'model_not_found'
  | 'server_error';

export interface ConnectionTestResult {
  status: 'success' | 'failed';
  response_time_ms?: number;
  model_info?: string;
  error_type?: AIErrorType;
  error_message?: string;
}

// ─── 仪表盘 ─────────────────────────────────────────────────

export interface DashboardOverview {
  today_new_articles: number;
  group_distribution: Record<string, number>;
  pending_count: number;
  bookmark_count: number;
  topic_candidate_count: number;
}

export interface TrendingTag {
  monitor_group: string;
  tags: Array<{ tag_value: string; count: number }>;
}
