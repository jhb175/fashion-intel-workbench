# 潮流情报编辑工作台 / Fashion Intel Workbench

[中文](#中文) | [English](#english) | [日本語](#日本語)

---

## 中文

全球时尚/潮流/服装资讯 AI 情报平台，面向潮流编辑的专业工作台。

### 功能

- **资讯聚合** — 自动从全球 RSS 源采集最新潮流资讯
- **AI 分析** — 中文摘要、自动标签、深度分析、每日简报
- **知识库** — 品牌档案、风格历史、经典单品、人物档案
- **品牌池** — 55+ 品牌官方写法查询、Logo 管理
- **编辑工具** — 收藏、待选题、多维度筛选搜索
- **AI 模型可配置** — 支持 OpenAI 及兼容 API 的第三方模型

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL (生产) / SQLite (本地开发) |
| 缓存/队列 | Redis + Celery |
| 部署 | Docker Compose + Nginx |

### 快速开始

**一键部署（生产环境）：**

```bash
git clone https://github.com/jhb175/fashion-intel-workbench.git
cd fashion-intel-workbench
bash scripts/deploy.sh
```

**本地开发：**

```bash
# 后端
cd backend
pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --port 8000

# 前端（另一个终端）
cd frontend
npm install && npm run dev
```

默认账号：`admin` / `admin123`

### 项目结构

```
├── backend/          # FastAPI 后端 (47+ API 端点)
├── frontend/         # Next.js 前端 (40+ 组件)
├── nginx/            # Nginx 反向代理配置
├── scripts/          # 部署和初始化脚本
├── docker-compose.yml
└── DEPLOY.md         # 详细部署文档
```

---

## English

AI-powered global fashion intelligence platform for trend editors.

### Features

- **News Aggregation** — Auto-collect latest fashion news from global RSS feeds
- **AI Analysis** — Chinese summaries, auto-tagging, deep analysis, daily briefings
- **Knowledge Base** — Brand profiles, style history, classic items, designer archives
- **Brand Pool** — 55+ brands with official naming conventions & logo management
- **Editor Tools** — Bookmarks, topic candidates, multi-dimensional search
- **Configurable AI** — Supports OpenAI and compatible third-party models

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend | Python FastAPI + SQLAlchemy |
| Database | PostgreSQL (prod) / SQLite (local dev) |
| Cache/Queue | Redis + Celery |
| Deploy | Docker Compose + Nginx |

### Quick Start

**One-click deploy (production):**

```bash
git clone https://github.com/jhb175/fashion-intel-workbench.git
cd fashion-intel-workbench
bash scripts/deploy.sh
```

**Local development:**

```bash
# Backend
cd backend
pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install && npm run dev
```

Default login: `admin` / `admin123`

### Project Structure

```
├── backend/          # FastAPI backend (47+ API endpoints)
├── frontend/         # Next.js frontend (40+ components)
├── nginx/            # Nginx reverse proxy config
├── scripts/          # Deploy & init scripts
├── docker-compose.yml
└── DEPLOY.md         # Detailed deployment guide
```

---

## 日本語

ファッションエディター向けのAI搭載グローバルファッションインテリジェンスプラットフォーム。

### 機能

- **ニュース集約** — グローバルRSSフィードから最新ファッションニュースを自動収集
- **AI分析** — 中国語要約、自動タグ付け、深層分析、デイリーブリーフィング
- **ナレッジベース** — ブランドプロフィール、スタイル史、クラシックアイテム
- **ブランドプール** — 55以上のブランドの公式表記・ロゴ管理
- **エディターツール** — ブックマーク、トピック候補、多次元検索
- **AI設定可能** — OpenAIおよび互換APIをサポート

### クイックスタート

```bash
git clone https://github.com/jhb175/fashion-intel-workbench.git
cd fashion-intel-workbench
bash scripts/deploy.sh
```

デフォルトログイン: `admin` / `admin123`

---

## License

Private
