# 潮流情报编辑工作台 (Fashion Intel Workbench)

全球时尚/潮流/服装资讯 AI 情报平台，面向潮流编辑的工作台。

## 功能

- **资讯聚合** — 自动从全球 RSS 源采集最新潮流资讯
- **AI 分析** — 中文摘要、自动标签、深度分析、每日简报
- **知识库** — 品牌档案、风格历史、经典单品、人物档案
- **品牌池** — 品牌官方写法查询、Logo 管理
- **编辑工具** — 收藏、待选题、多维度筛选搜索
- **AI 模型可配置** — 支持 OpenAI 及兼容 API 的第三方模型

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL (生产) / SQLite (本地开发) |
| 缓存/队列 | Redis + Celery |
| AI | OpenAI 兼容 API (可配置) |
| 部署 | Docker Compose + Nginx |

## 本地开发

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

### 后端

```bash
cd backend
pip install -e ".[dev]"
cp ../.env.example .env  # 编辑配置
python -m uvicorn app.main:app --reload --port 8000
# API 文档 http://localhost:8000/docs
```

默认账号：`admin` / `admin123`

### Docker (完整环境)

```bash
cp .env.example .env  # 编辑配置
docker compose up
```

## 生产部署

参见 [DEPLOY.md](DEPLOY.md)

## 项目结构

```
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── models/       # SQLAlchemy 数据模型
│   │   ├── routers/      # API 路由
│   │   ├── services/     # 业务逻辑
│   │   ├── aggregation/  # 资讯采集引擎
│   │   └── tasks/        # Celery 异步任务
│   └── tests/
├── frontend/         # Next.js 前端
│   └── src/
│       ├── app/          # 页面
│       ├── components/   # 组件
│       ├── lib/          # 工具库
│       └── types/        # TypeScript 类型
├── nginx/            # Nginx 配置
├── scripts/          # 初始化脚本
├── docker-compose.yml
└── DEPLOY.md
```

## License

Private
