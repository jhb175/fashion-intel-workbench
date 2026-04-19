# 实现计划：潮流情报编辑工作台（Fashion Intel Workbench）

## 概述

本实现计划将潮流情报编辑工作台的设计方案转化为可执行的编码任务序列。任务按照从基础设施搭建 → 后端核心模型与服务 → API 接口 → 前端页面与组件 → 集成联调 → 部署配置的顺序排列，确保每一步都在前一步的基础上递增构建，不产生孤立代码。

后端使用 Python (FastAPI + SQLAlchemy + Celery)，前端使用 TypeScript (Next.js 14 + Tailwind CSS + Radix UI + Framer Motion)。

## 任务

- [x] 1. 项目基础设施搭建
  - [x] 1.1 初始化后端项目结构
    - 创建 `backend/` 目录，初始化 `pyproject.toml`（包含 fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic, pyjwt, celery, redis, feedparser, httpx, beautifulsoup4, openai, cryptography, apscheduler, hypothesis, pytest, pytest-asyncio 等依赖）
    - 创建 `backend/app/main.py` FastAPI 应用入口，配置 CORS 中间件
    - 创建 `backend/app/config.py` 配置管理（从环境变量读取数据库连接、Redis 地址、JWT 密钥、加密密钥等）
    - 创建 `backend/app/database.py` 异步数据库连接（AsyncSession + async engine）
    - _需求：15.2, 15.3_

  - [x] 1.2 初始化前端项目结构
    - 使用 Next.js 14 (App Router) + TypeScript 初始化 `frontend/` 项目
    - 安装并配置 Tailwind CSS、Radix UI、Framer Motion
    - 创建 `frontend/src/app/layout.tsx` 根布局（中文字体、全局样式）
    - 创建 `frontend/src/lib/api.ts` API 客户端（统一请求封装、错误拦截、401 自动跳转登录）
    - 创建 `frontend/src/types/` 目录，定义核心 TypeScript 类型接口
    - _需求：12.1, 12.7, 15.2_

  - [x] 1.3 配置 Docker Compose 开发环境
    - 创建 `docker-compose.yml`（PostgreSQL 16 + Redis 7 + 后端 + 前端 + Celery Worker）
    - 创建 `backend/Dockerfile` 和 `frontend/Dockerfile`
    - 创建 `.env.example` 环境变量模板
    - 确保 `docker-compose up` 可启动完整开发环境
    - _需求：15.1, 15.2, 15.3_

- [x] 2. 数据库模型与迁移
  - [x] 2.1 创建 SQLAlchemy 数据模型
    - 创建 `backend/app/models/` 目录下所有模型文件：`user.py`、`monitor_group.py`、`source.py`、`article.py`、`tag.py`（article_tags）、`brand.py`、`brand_logo.py`、`keyword.py`、`bookmark.py`、`briefing.py`（daily_briefings + briefing_articles）、`knowledge.py`（knowledge_entries + knowledge_entry_brands + knowledge_entry_keywords）、`ai_provider.py`
    - 定义所有字段、约束、索引和关联关系，严格按照设计文档数据表定义
    - 创建 `backend/app/models/__init__.py` 统一导出所有模型
    - _需求：1.3, 3.2, 5.1, 5.2, 7.2, 8.5, 13.3, 14.1, 16.1, 17.1, 17.2_

  - [x] 2.2 配置 Alembic 数据库迁移
    - 初始化 Alembic 配置（`backend/alembic.ini` + `backend/alembic/`）
    - 生成初始迁移脚本，包含所有数据表创建
    - 在迁移中启用 `pg_trgm` 扩展和全文搜索索引
    - _需求：15.2_

  - [x] 2.3 创建数据库初始化与种子数据脚本
    - 创建 `scripts/init_db.py`：运行迁移、创建默认管理员用户
    - 创建 `scripts/seed_data.py`：插入四个预置监控组（Luxury、Sports、Outdoor、Rap/Culture）、预置 OpenAI AI 提供者、示例品牌和关键词数据
    - _需求：10.5, 14.2_

- [x] 3. 检查点 - 确保数据库模型和迁移正常工作
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 4. 用户认证模块
  - [x] 4.1 实现后端认证服务
    - 创建 `backend/app/utils/auth.py`：JWT token 生成与验证、密码哈希（bcrypt）、`get_current_user` 依赖注入
    - 创建 `backend/app/schemas/auth.py`：LoginRequest、TokenResponse、UserResponse Pydantic 模型
    - 创建 `backend/app/routers/auth.py`：实现 `POST /api/v1/auth/login`、`POST /api/v1/auth/refresh`、`GET /api/v1/auth/me` 接口
    - 创建 `backend/app/utils/errors.py`：统一异常处理中间件，定义 ValidationError、AuthenticationError、NotFoundError 等业务异常类
    - _需求：13.1, 13.2, 13.4, 15.4_

  - [ ]* 4.2 编写认证模块属性测试
    - **属性 16：未认证请求拒绝**
    - **验证需求：13.2**

  - [ ]* 4.3 编写认证模块单元测试
    - 测试 JWT 生成/验证、token 过期、无效 token、密码哈希验证
    - _需求：13.1, 13.2_

  - [x] 4.4 实现前端登录页面
    - 创建 `frontend/src/app/login/page.tsx` 登录页面
    - 创建 `frontend/src/lib/auth.ts` 认证工具（token 存储、登录状态检查、自动跳转）
    - 在根布局中添加认证守卫，未登录用户重定向到登录页
    - _需求：13.1, 13.2_

- [x] 5. AI 提供者适配层与加密服务
  - [x] 5.1 实现加密服务
    - 创建 `backend/app/services/encryption_service.py`：使用 Fernet 对称加密实现 API Key 的加密、解密和掩码展示
    - _需求：14.6_

  - [ ]* 5.2 编写加密服务属性测试
    - **属性 19：API Key 加密存储与掩码展示**
    - **验证需求：14.6**

  - [x] 5.3 实现 AI 提供者适配层
    - 创建 `backend/app/services/ai_provider_adapter.py`：实现 `AIProviderAdapter` 类，包含 `get_active_provider`、`create_client`、`chat_completion`、`test_connection` 方法
    - 利用 openai Python SDK 的 `base_url` 参数实现多提供者切换
    - 实现 AI 错误分类逻辑（auth_failed / quota_exceeded / network_timeout / model_not_found / server_error）
    - _需求：14.3, 14.4, 14.7_

  - [ ]* 5.4 编写 AI 适配层属性测试
    - **属性 17：AI 适配层使用当前激活配置**
    - **验证需求：14.3, 14.4**
    - **属性 20：AI 错误分类正确性**
    - **验证需求：14.7**

  - [x] 5.5 实现 AI 提供者配置管理服务与 API
    - 创建 `backend/app/services/ai_provider_service.py`：AI 提供者 CRUD、激活切换、连接测试
    - 创建 `backend/app/schemas/ai_provider.py`：请求/响应 Pydantic 模型（API Key 掩码处理）
    - 创建 `backend/app/routers/ai_providers.py`：实现所有 AI 提供者配置接口（GET/POST/PUT/DELETE/PATCH activate/POST test）
    - _需求：14.1, 14.2, 14.5_

  - [ ]* 5.6 编写 AI 提供者 CRUD 属性测试
    - **属性 18：AI 提供者 CRUD round-trip**
    - **验证需求：14.2**

- [x] 6. AI 业务服务层
  - [x] 6.1 实现 AI 业务服务
    - 创建 `backend/app/services/ai_service.py`：实现 `AIServiceBase` 的具体子类，包含 `generate_summary`、`extract_tags`、`generate_deep_analysis`、`generate_daily_briefing`、`generate_history_analysis`、`match_knowledge_entries` 方法
    - 每个方法构建合适的 prompt 并通过 `AIProviderAdapter.chat_completion` 调用 AI
    - 实现中文资讯跳过翻译逻辑（original_language == "zh" 时直接使用原文）
    - _需求：2.4, 3.1, 3.2, 3.3, 6.1, 6.2, 7.1, 7.2, 9.1, 9.5_

  - [ ]* 6.2 编写 AI 服务属性测试
    - **属性 3：中文资讯跳过翻译**
    - **验证需求：2.4**
    - **属性 4：中文摘要长度约束**
    - **验证需求：3.1**
    - **属性 5：标签提取合法性**
    - **验证需求：3.2, 3.3**
    - **属性 9：深度分析报告结构完整性**
    - **验证需求：6.2**
    - **属性 10：每日简报结构完整性**
    - **验证需求：7.2**

- [x] 7. 检查点 - 确保认证和 AI 服务层测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 8. 资讯聚合引擎
  - [x] 8.1 实现采集器与去重服务
    - 创建 `backend/app/aggregation/base.py`：`BaseCollector` 抽象基类
    - 创建 `backend/app/aggregation/rss_collector.py`：RSS/Atom 采集器（使用 feedparser）
    - 创建 `backend/app/aggregation/web_collector.py`：网页采集器（使用 httpx + BeautifulSoup4）
    - 创建 `backend/app/aggregation/dedup.py`：去重服务（基于 original_url 唯一性 + 标题相似度计算）
    - _需求：1.1, 1.2, 1.6_

  - [ ]* 8.2 编写去重服务属性测试
    - **属性 1：去重判断对称性**
    - **验证需求：1.2**

  - [x] 8.3 实现资讯聚合服务与 Celery 异步任务
    - 创建 `backend/app/services/aggregation_service.py`：聚合调度逻辑（遍历启用的资讯源、调用采集器、去重、存储、触发 AI 处理）
    - 创建 `backend/app/tasks/celery_app.py`：Celery 应用配置（Redis 作为 broker）
    - 创建 `backend/app/tasks/aggregation_tasks.py`：定时采集任务
    - 创建 `backend/app/tasks/ai_tasks.py`：异步 AI 分析任务（摘要生成 + 标签提取）
    - 配置 APScheduler 定时触发采集任务
    - 实现采集错误处理：单个源失败不影响其他源，记录错误日志，更新源状态
    - _需求：1.1, 1.4, 1.5, 3.4_

  - [ ]* 8.4 编写资讯元数据完整性属性测试
    - **属性 2：资讯元数据完整性**
    - **验证需求：1.3**

- [x] 9. 资讯核心 API
  - [x] 9.1 实现资讯服务与搜索服务
    - 创建 `backend/app/services/article_service.py`：资讯 CRUD、标签编辑、状态管理
    - 创建 `backend/app/services/search_service.py`：多维度筛选（品牌、监控组、内容类型、时间范围）+ 关键词全文搜索（PostgreSQL pg_trgm + zhparser）
    - 创建 `backend/app/schemas/article.py`：资讯相关 Pydantic 模型
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 9.2 编写筛选与搜索属性测试
    - **属性 6：资讯筛选正确性**
    - **验证需求：4.1, 4.2, 4.3, 4.4, 4.6**
    - **属性 7：关键词搜索命中**
    - **验证需求：4.5**

  - [x] 9.3 实现资讯 API 路由
    - 创建 `backend/app/routers/articles.py`：实现所有资讯接口（列表/详情/标签编辑/重新分析/深度分析/关联知识/历史背景分析）
    - _需求：2.1, 2.2, 2.3, 2.5, 3.5, 6.1, 6.4, 9.1, 9.5_

- [x] 10. 收藏与待选题 API
  - [x] 10.1 实现收藏与待选题服务和 API
    - 创建 `backend/app/services/bookmark_service.py`：收藏和待选题的添加、取消、列表查询（支持筛选）
    - 创建 `backend/app/schemas/bookmark.py`：请求/响应 Pydantic 模型
    - 创建 `backend/app/routers/bookmarks.py`：实现收藏和待选题接口（GET/POST/DELETE）
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 10.2 编写收藏 round-trip 属性测试
    - **属性 8：用户标记 round-trip**
    - **验证需求：5.1, 5.2, 5.5**

- [x] 11. 每日简报 API
  - [x] 11.1 实现简报服务和 API
    - 创建 `backend/app/services/briefing_service.py`：简报生成（调用 AI 服务）、简报列表查询（按日期倒序）、手动触发生成
    - 创建 `backend/app/schemas/briefing.py`：请求/响应 Pydantic 模型
    - 创建 `backend/app/routers/briefings.py`：实现简报接口（GET 列表/GET 详情/POST 生成）
    - 在 Celery 定时任务中添加每日简报自动生成任务
    - _需求：7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 11.2 编写简报列表排序属性测试
    - **属性 11：简报列表日期倒序**
    - **验证需求：7.3**

- [x] 12. 知识库 API
  - [x] 12.1 实现知识库服务和 API
    - 创建 `backend/app/services/knowledge_service.py`：知识条目 CRUD、按类别和关键词搜索、与资讯的关联匹配
    - 创建 `backend/app/schemas/knowledge.py`：请求/响应 Pydantic 模型
    - 创建 `backend/app/routers/knowledge.py`：实现知识库接口（GET 列表/GET 详情/POST/PUT/DELETE）
    - _需求：8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.4_

  - [ ]* 12.2 编写知识库属性测试
    - **属性 12：知识条目类别合法性**
    - **验证需求：8.1**
    - **属性 13：知识条目元数据完整性**
    - **验证需求：8.5**
    - **属性 14：知识库匹配相关性**
    - **验证需求：9.1**

- [x] 13. 后台管理 API
  - [x] 13.1 实现后台管理服务和 API
    - 创建 `backend/app/services/brand_service.py`：品牌 CRUD、品牌写法搜索（模糊匹配）、Logo 管理
    - 创建 `backend/app/services/file_storage_service.py`：文件存储服务（Logo 上传到 `uploads/logos/`、缩略图生成、文件下载）
    - 创建 `backend/app/schemas/admin.py`：资讯源、品牌、关键词、监控组相关 Pydantic 模型
    - 创建 `backend/app/routers/admin.py`：实现所有后台管理接口（资讯源 CRUD + 启用禁用、品牌 CRUD + 写法搜索 + Logo 管理、关键词 CRUD、监控组查看编辑）
    - _需求：10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 16.1, 16.2, 16.3, 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ]* 13.2 编写品牌写法与 Logo 属性测试
    - **属性 21：品牌写法模糊搜索命中**
    - **验证需求：16.3**
    - **属性 22：品牌 Logo 文件格式合法性**
    - **验证需求：17.1, 17.2**
    - **属性 23：品牌 Logo CRUD round-trip**
    - **验证需求：17.3, 17.4**

- [x] 14. 仪表盘 API
  - [x] 14.1 实现仪表盘服务和 API
    - 创建 `backend/app/routers/dashboard.py`：实现仪表盘接口（GET overview / GET recent-articles / GET trending-tags）
    - 数据概览：今日新增资讯数、各监控组分布、待处理数、收藏和待选题总数
    - 最近资讯：最多 20 条，按发布时间倒序
    - 热门标签：各监控组的热门标签统计
    - _需求：11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 14.2 编写仪表盘属性测试
    - **属性 15：仪表盘最近资讯约束**
    - **验证需求：11.3**

- [x] 15. 检查点 - 确保所有后端 API 和测试通过
  - 确保所有测试通过，如有问题请向用户确认。


- [x] 16. 前端通用 UI 组件与布局
  - [x] 16.1 实现全局布局与通用 UI 组件
    - 创建 `frontend/src/components/layout/AppLayout.tsx`：全局布局（侧边导航 + 主内容区）
    - 创建 `frontend/src/components/layout/Sidebar.tsx`：侧边导航栏（页面导航链接、用户信息、中文菜单文案）
    - 创建 `frontend/src/components/layout/PageHeader.tsx`：页面标题栏（面包屑导航 + 操作按钮）
    - 创建通用 UI 组件：`LoadingSpinner`、`ErrorMessage`（含重试按钮）、`EmptyState`、`Pagination`、`TagBadge`、`SearchInput`、`DateRangePicker`、`ConfirmDialog`
    - 配置 Tailwind CSS 主题（简洁有质感的时尚设计风格、中文字体）
    - 实现响应式布局：桌面端多栏布局（≥1024px）、移动端单栏布局（<768px）
    - _需求：12.1, 12.4, 12.6, 12.7_

- [x] 17. 前端仪表盘首页
  - [x] 17.1 实现仪表盘页面与组件
    - 创建 `frontend/src/app/page.tsx` 仪表盘首页
    - 创建 `frontend/src/components/dashboard/StatsOverview.tsx`：数据概览卡片组
    - 创建 `frontend/src/components/dashboard/BriefingSummary.tsx`：今日简报摘要卡片（点击跳转完整简报）
    - 创建 `frontend/src/components/dashboard/RecentArticles.tsx`：最近资讯列表（最多 20 条）
    - 创建 `frontend/src/components/dashboard/TrendingTags.tsx`：热门标签词云/列表
    - 实现首屏视觉冲击力设计，突出展示当日重点内容
    - 添加 Framer Motion 页面切换和卡片悬停动效
    - _需求：11.1, 11.2, 11.3, 11.4, 11.5, 12.3, 12.5_

- [x] 18. 前端资讯列表与详情页
  - [x] 18.1 实现资讯列表页
    - 创建 `frontend/src/app/articles/page.tsx` 资讯列表页
    - 创建 `frontend/src/components/articles/ArticleCard.tsx`：精致卡片式布局（中文摘要、英文原标题、来源、时间、标签、收藏/待选题按钮、已收藏/已标记视觉标记）
    - 创建 `frontend/src/components/articles/ArticleList.tsx`：资讯列表容器（支持无限滚动加载）
    - 创建 `frontend/src/components/articles/ArticleFilters.tsx`：筛选面板（品牌、监控组、内容类型、时间范围、关键词搜索）
    - 实现多筛选条件组合使用（"与"关系）
    - 添加卡片悬停、滚动、筛选操作的流畅过渡动效
    - _需求：2.1, 2.2, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.6, 12.2, 12.3, 12.6_

  - [x] 18.2 实现资讯详情页
    - 创建 `frontend/src/app/articles/[id]/page.tsx` 资讯详情页
    - 创建 `frontend/src/components/articles/ArticleDetail.tsx`：完整中文摘要 + 英文原标题 + 原文链接（新标签页打开）+ 原文摘录段落
    - 创建 `frontend/src/components/articles/TagEditor.tsx`：标签编辑器（添加、删除标签）
    - 创建 `frontend/src/components/articles/AIAnalysisPanel.tsx`：AI 深度分析面板（加载状态、重试按钮、分析报告展示）
    - 创建 `frontend/src/components/articles/RelatedKnowledge.tsx`：相关历史背景模块（匹配到的知识条目摘要，点击跳转知识详情；无匹配时隐藏模块）
    - 创建 `frontend/src/components/brands/BrandNamingBadge.tsx`：品牌官方写法提示徽章
    - 实现收藏/待选题按钮交互（点击切换状态）
    - _需求：2.1, 2.2, 2.3, 2.5, 3.5, 5.1, 5.2, 5.5, 6.1, 6.3, 6.4, 6.5, 9.1, 9.2, 9.3, 9.4, 16.4_

- [x] 19. 前端收藏与待选题页
  - [x] 19.1 实现收藏/待选题管理页面
    - 创建 `frontend/src/app/bookmarks/page.tsx` 收藏/待选题管理页面
    - 实现收藏列表和待选题列表的 Tab 切换展示
    - 支持按品牌、类型、时间筛选
    - 复用 `ArticleCard` 组件展示资讯
    - _需求：5.3, 5.4_

- [x] 20. 前端每日简报页
  - [x] 20.1 实现简报列表与详情页
    - 创建 `frontend/src/app/briefings/page.tsx` 简报列表页（按日期倒序）
    - 创建 `frontend/src/app/briefings/[id]/page.tsx` 简报详情页
    - 创建 `frontend/src/components/briefings/BriefingList.tsx`：简报列表组件
    - 创建 `frontend/src/components/briefings/BriefingDetail.tsx`：简报详情展示（按监控组分类的重点资讯、趋势热点、跟进建议，资讯可点击跳转详情页）
    - 实现手动触发生成当日简报按钮
    - _需求：7.3, 7.4, 7.5_

- [x] 21. 前端知识库页面
  - [x] 21.1 实现知识库浏览与详情页
    - 创建 `frontend/src/app/knowledge/page.tsx` 知识库浏览页
    - 创建 `frontend/src/app/knowledge/[id]/page.tsx` 知识条目详情页
    - 创建 `frontend/src/components/knowledge/KnowledgeGrid.tsx`：知识条目网格展示（按类别筛选、关键词搜索）
    - 创建 `frontend/src/components/knowledge/KnowledgeDetail.tsx`：知识条目详情（时间线、关键事件、关联品牌/人物、品牌官方写法信息、品牌 Logo 文件列表）
    - _需求：8.1, 8.2, 8.3, 16.5, 17.6_

- [x] 22. 检查点 - 确保前端核心页面正常工作
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 23. 前端后台管理页面
  - [x] 23.1 实现资讯源管理页面
    - 创建 `frontend/src/app/admin/sources/page.tsx` 资讯源管理页面
    - 实现资讯源列表展示（名称、URL、类型、监控组、启用状态、最近采集时间、采集状态）
    - 实现添加、编辑、启用/禁用、删除资讯源的交互
    - _需求：10.1, 10.2_

  - [x] 23.2 实现品牌池管理页面
    - 创建 `frontend/src/app/admin/brands/page.tsx` 品牌池管理页面
    - 实现品牌列表展示和 CRUD 操作（中文名、英文名、监控组、官方写法、社交媒体写法、写法备注）
    - 创建 `frontend/src/components/brands/BrandNamingSearch.tsx`：品牌写法搜索组件（模糊匹配）
    - 创建 `frontend/src/components/brands/BrandNamingCard.tsx`：品牌写法展示卡片
    - 创建 `frontend/src/components/brands/BrandLogoGallery.tsx`：品牌 Logo 画廊（缩略图展示、按类型筛选）
    - 创建 `frontend/src/components/brands/BrandLogoUploader.tsx`：Logo 上传组件（拖拽上传、选择 Logo 类型）
    - 创建 `frontend/src/components/brands/BrandLogoCard.tsx`：Logo 卡片（缩略图、文件名、格式、类型、下载/删除按钮）
    - _需求：10.3, 16.1, 16.2, 16.3, 17.1, 17.2, 17.3, 17.4, 17.5_

  - [x] 23.3 实现关键词池与监控组管理页面
    - 创建 `frontend/src/app/admin/keywords/page.tsx` 关键词池管理页面（CRUD：中文词、英文词、监控组）
    - 创建 `frontend/src/app/admin/monitor-groups/page.tsx` 监控组管理页面（查看和编辑配置）
    - _需求：10.4, 10.5_

  - [x] 23.4 实现 AI 提供者配置页面
    - 创建 `frontend/src/app/admin/ai-providers/page.tsx` AI 提供者配置页面
    - 创建 `frontend/src/components/ai-providers/AIProviderList.tsx`：提供者列表（标识激活和预置提供者）
    - 创建 `frontend/src/components/ai-providers/AIProviderForm.tsx`：配置表单（名称、API Key 掩码输入、Base URL、模型名称）
    - 创建 `frontend/src/components/ai-providers/AIProviderCard.tsx`：提供者卡片（配置摘要、激活状态、测试结果、操作按钮）
    - 创建 `frontend/src/components/ai-providers/ConnectionTestButton.tsx`：连接测试按钮
    - 创建 `frontend/src/components/ai-providers/APIKeyInput.tsx`：API Key 掩码输入组件
    - 创建 `frontend/src/components/ai-providers/AIErrorAlert.tsx`：AI 错误提示组件（按错误类型展示信息和建议）
    - _需求：14.1, 14.2, 14.5, 14.6, 14.7_

- [x] 24. 前端知识库管理功能
  - [x] 24.1 实现知识条目编辑功能
    - 创建 `frontend/src/components/knowledge/KnowledgeEditor.tsx`：知识条目编辑表单（标题、类别、结构化内容、关联品牌、关联关键词）
    - 在后台管理中集成知识条目的创建、编辑和删除功能
    - _需求：8.4_

- [x] 25. 检查点 - 确保所有后台管理页面正常工作
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 26. 前后端集成与联调
  - [x] 26.1 前后端完整联调
    - 验证所有前端页面与后端 API 的数据交互正确性
    - 确保认证流程完整（登录 → token 存储 → API 请求携带 token → 过期刷新）
    - 确保资讯采集 → AI 处理 → 前端展示的完整流程正常
    - 确保收藏/待选题、简报、知识库、后台管理的完整 CRUD 流程正常
    - 确保 AI 提供者配置 → 连接测试 → AI 功能调用的完整流程正常
    - 确保品牌写法搜索和 Logo 上传/下载流程正常
    - _需求：1.1-17.6 全部需求_

  - [ ]* 26.2 编写前端组件测试
    - 使用 Vitest + React Testing Library 测试关键组件的渲染和交互
    - 测试 ArticleCard、ArticleFilters、AIProviderForm、BrandLogoUploader 等核心组件
    - _需求：12.2, 12.6_

- [x] 27. 生产部署配置
  - [x] 27.1 配置生产环境部署
    - 创建 `docker-compose.prod.yml`（生产环境配置，优化资源分配）
    - 创建 `nginx/nginx.conf`（HTTPS 终端、静态资源服务、反向代理配置）
    - 配置前端生产构建优化（Next.js standalone 输出）
    - 配置后端生产运行参数（Gunicorn + Uvicorn workers）
    - 编写部署文档（README 或 DEPLOY.md）
    - _需求：15.1, 15.2, 15.3, 15.5_

- [x] 28. 最终检查点 - 确保所有测试通过，系统完整可用
  - 确保所有测试通过，如有问题请向用户确认。

## 说明

- 标记 `*` 的子任务为可选任务，可跳过以加速 MVP 交付
- 每个任务引用了具体的需求编号，确保需求可追溯
- 检查点任务用于阶段性验证，确保增量构建的正确性
- 属性测试验证设计文档中定义的 23 条正确性属性
- 单元测试验证具体示例和边界条件
- 后端使用 Python (FastAPI)，前端使用 TypeScript (Next.js 14)