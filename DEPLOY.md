# 潮流情报编辑工作台 — 生产部署指南

## 目录

- [前置条件](#前置条件)
- [环境变量配置](#环境变量配置)
- [SSL 证书配置](#ssl-证书配置)
- [构建与部署](#构建与部署)
- [数据库初始化](#数据库初始化)
- [种子数据](#种子数据)
- [监控与日志](#监控与日志)
- [常见问题排查](#常见问题排查)
- [更新与回滚](#更新与回滚)

---

## 前置条件

- **Docker** >= 24.0
- **Docker Compose** >= 2.20（推荐使用 `docker compose` V2 命令）
- 一台海外云服务器（推荐 2 核 4GB 内存以上）
- 域名（已解析到服务器 IP）
- SSL 证书（可使用 Let's Encrypt 免费获取）

---

## 环境变量配置

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，**必须修改**以下配置项：

```dotenv
# --- PostgreSQL（使用强密码） ---
POSTGRES_USER=fashion_intel
POSTGRES_PASSWORD=<你的数据库强密码>
POSTGRES_DB=fashion_intel

# --- JWT（生成随机密钥） ---
# 生成方式: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=<随机生成的JWT密钥>

# --- Fernet 加密密钥（用于 API Key 加密存储） ---
# 生成方式: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=<生成的Fernet密钥>

# --- CORS（生产环境设置为你的域名） ---
CORS_ORIGINS=https://your-domain.com
```

> **安全提示**：切勿将 `.env` 文件提交到版本控制系统。

---

## SSL 证书配置

### 方式一：Let's Encrypt（推荐）

使用 certbot 获取免费 SSL 证书：

```bash
# 安装 certbot
sudo apt install certbot

# 获取证书（先确保 80 端口可用）
sudo certbot certonly --standalone -d your-domain.com

# 复制证书到项目目录
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chmod 644 nginx/ssl/*.pem
```

### 方式二：自签名证书（仅测试用）

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

---

## 构建与部署

### 首次部署

```bash
# 1. 构建所有镜像
docker compose -f docker-compose.prod.yml build

# 2. 启动所有服务
docker compose -f docker-compose.prod.yml up -d

# 3. 查看服务状态
docker compose -f docker-compose.prod.yml ps
```

### 验证部署

```bash
# 检查后端健康状态
curl -k https://localhost/health

# 检查 Nginx 健康状态
curl http://localhost/nginx-health

# 查看所有容器日志
docker compose -f docker-compose.prod.yml logs
```

---

## 数据库初始化

首次部署后需要初始化数据库结构和默认管理员账号：

```bash
# 运行数据库迁移
docker compose -f docker-compose.prod.yml exec backend \
  python -m alembic upgrade head

# 初始化数据库（创建默认管理员用户）
docker compose -f docker-compose.prod.yml exec backend \
  python -m scripts.init_db
```

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`（请登录后立即修改）

---

## 种子数据

插入预置的监控组、示例品牌和关键词数据：

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python -m scripts.seed_data
```

种子数据包含：
- 四个预置监控组：Luxury、Sports、Outdoor、Rap/Culture
- 预置 OpenAI AI 提供者配置
- 示例品牌和关键词数据

---

## 监控与日志

### 查看服务日志

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery-worker
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f frontend
```

### 健康检查端点

| 服务 | 端点 | 说明 |
|------|------|------|
| Nginx | `http://localhost/nginx-health` | Nginx 自身健康状态 |
| Backend | `https://your-domain.com/health` | 后端 API 健康状态 |
| PostgreSQL | 内部 `pg_isready` | 数据库就绪检查 |
| Redis | 内部 `redis-cli ping` | Redis 连通性检查 |

### 资源监控

```bash
# 查看容器资源使用情况
docker stats

# 查看磁盘使用
docker system df
```

---

## 常见问题排查

### 1. 容器启动失败

```bash
# 查看失败容器的日志
docker compose -f docker-compose.prod.yml logs <service-name>

# 检查容器状态
docker compose -f docker-compose.prod.yml ps -a
```

### 2. 数据库连接失败

- 确认 `.env` 中的 `POSTGRES_USER` 和 `POSTGRES_PASSWORD` 配置正确
- 确认 PostgreSQL 容器已启动并通过健康检查：
  ```bash
  docker compose -f docker-compose.prod.yml exec postgres pg_isready
  ```

### 3. SSL 证书问题

- 确认 `nginx/ssl/` 目录下存在 `fullchain.pem` 和 `privkey.pem`
- 确认证书文件权限正确（至少可读）
- 检查 Nginx 日志：
  ```bash
  docker compose -f docker-compose.prod.yml logs nginx
  ```

### 4. AI 功能不可用

- 登录后在「设置 → AI 提供者」页面配置有效的 API Key
- 使用「连接测试」按钮验证 API Key 和 Base URL 是否有效
- 检查 Celery Worker 日志确认异步任务是否正常执行

### 5. 前端页面空白或 API 请求失败

- 确认 Nginx 配置中的 upstream 地址正确
- 确认前端构建时 `NEXT_PUBLIC_API_URL` 设置为 `/api/v1`
- 检查浏览器开发者工具中的网络请求和控制台错误

### 6. 上传文件（Logo）失败

- 确认 `uploads_data` 卷已正确挂载
- 确认 Nginx 的 `client_max_body_size` 设置足够大（默认 20MB）
- 检查后端日志中的文件存储错误

### 7. 定时采集任务未执行

- 确认 Celery Worker 容器正在运行
- 检查 Celery Worker 健康检查状态：
  ```bash
  docker compose -f docker-compose.prod.yml exec celery-worker \
    celery -A app.tasks.celery_app inspect ping
  ```
- 确认 Redis 连接正常

---

## 更新与回滚

### 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并部署（零停机）
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 运行数据库迁移（如有新迁移）
docker compose -f docker-compose.prod.yml exec backend \
  python -m alembic upgrade head
```

### 回滚

```bash
# 回滚到上一个版本
git checkout <previous-commit>
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 回滚数据库迁移（如需要）
docker compose -f docker-compose.prod.yml exec backend \
  python -m alembic downgrade -1
```

### 数据备份

```bash
# 备份 PostgreSQL 数据
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$(date +%Y%m%d).sql

# 备份上传文件
docker cp fashion-intel-backend:/app/uploads ./uploads_backup_$(date +%Y%m%d)
```

---

## 架构概览

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Nginx    │  :80 (→ HTTPS) / :443
                    │  SSL + 代理  │
                    └──┬──────┬───┘
                       │      │
              ┌────────▼┐  ┌──▼────────┐
              │ Frontend │  │  Backend  │
              │ Next.js  │  │  Gunicorn │
              │ :3000    │  │  :8000    │
              └──────────┘  └──┬────┬───┘
                               │    │
                    ┌──────────▼┐ ┌─▼──────────┐
                    │ PostgreSQL│ │   Redis     │
                    │  :5432    │ │   :6379     │
                    └───────────┘ └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │   Celery    │
                                  │   Worker    │
                                  └─────────────┘
```
