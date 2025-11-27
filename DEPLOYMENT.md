# LAE 部署指南 - Vercel + Supabase--V3ING

## 📋 部署前准备

### 1. 创建 Supabase 项目

1. 访问 [Supabase](https://supabase.com/) 并创建账号
2. 创建新项目（选择离你最近的区域）
3. 等待数据库初始化完成
4. 进入 Project Settings → Database
5. 复制 Connection String (URI 格式)
   - 应该类似：`postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`

### 2. 初始化数据库表结构

在 Supabase SQL Editor 中执行以下 SQL（或使用 Alembic 迁移）：

```sql
-- 创建 domains 表
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES domains(id),
    description TEXT
);

-- 创建 activity_types 表
CREATE TABLE activity_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES activity_types(id)
);

-- 创建 schedules 表
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER REFERENCES domains(id),
    name VARCHAR(255) NOT NULL,
    start_date DATE,
    deadline DATE,
    status VARCHAR(50)
);

-- 创建 scheduled_events 表
CREATE TABLE scheduled_events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    time_slot VARCHAR(10),
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    status VARCHAR(50),
    domain_id INTEGER REFERENCES domains(id),
    activity_type_id INTEGER REFERENCES activity_types(id),
    schedule_id INTEGER REFERENCES schedules(id),
    duration INTEGER DEFAULT 60,
    start_time TIME,
    is_precise BOOLEAN DEFAULT FALSE,
    canvas_position_y INTEGER DEFAULT 0,
    x INTEGER,
    y INTEGER
);
```

## 🚀 Vercel 部署步骤

### 1. 安装 Vercel CLI（可选）

```bash
npm i -g vercel
```

### 2. 部署到 Vercel

#### 方法 A：使用 Vercel 网站（推荐）

1. 访问 [Vercel](https://vercel.com/) 并登录
2. 点击 "Add New Project"
3. 导入你的 GitHub 仓库
4. 配置环境变量：
   - 变量名：`DATABASE_URL`
   - 值：从 Supabase 复制的 Connection String
5. 点击 Deploy

#### 方法 B：使用 CLI

```bash
# 在项目根目录执行
vercel

# 设置环境变量
vercel env add DATABASE_URL
# 粘贴 Supabase 的 Connection String

# 重新部署
vercel --prod
```

## 🔧 环境变量配置

在 Vercel 项目设置中添加以下环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DATABASE_URL` | `postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres` | Supabase 数据库连接字符串 |

## 🧪 本地测试云端数据库

如果你想在本地测试连接云端数据库：

```bash
# Windows (PowerShell)
$env:DATABASE_URL="postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres"
python run.py

# Windows (CMD)
set DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres
python run.py

# Linux/Mac
export DATABASE_URL="postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres"
python run.py
```

## 📝 注意事项

### 数据库差异

SQLite 和 PostgreSQL 存在一些差异，可能需要调整：

1. **自增主键**：
   - SQLite: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - PostgreSQL: `SERIAL PRIMARY KEY`

2. **布尔类型**：
   - SQLite: 用 `0/1` 存储
   - PostgreSQL: 原生 `BOOLEAN` 类型

3. **日期时间**：
   - 两者在 SQLAlchemy 中通常兼容，但注意时区处理

### Vercel 限制

- **无状态**：Vercel 函数是无状态的，不要依赖本地文件存储
- **超时**：免费版函数执行超时 10 秒，Pro 版 60 秒
- **冷启动**：首次请求可能较慢（3-5 秒）

### 静态文件

当前 `vercel.json` 配置将所有请求路由到 FastAPI。如果需要优化静态文件服务：

```json
{
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/app/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

## 🔍 故障排查

### 1. 部署失败

检查 Vercel 部署日志，常见问题：
- `requirements.txt` 中的包版本冲突
- Python 版本不兼容
- 缺少必要的依赖

### 2. 数据库连接失败

- 确认 `DATABASE_URL` 环境变量正确设置
- 检查 Supabase 项目是否激活
- 验证 IP 白名单设置（Supabase 默认允许所有 IP）

### 3. 性能问题

- 启用数据库连接池（已在 `database.py` 中配置）
- 考虑添加 Redis 缓存
- 优化数据库查询，添加索引

## 📦 数据迁移

如果需要将本地 SQLite 数据迁移到 Supabase：

1. 使用数据库迁移工具（如 `pgloader`）
2. 或编写 Python 脚本手动迁移：

```python
# migration_script.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 本地 SQLite
local_engine = create_engine("sqlite:///data/lae_schedule.db")
LocalSession = sessionmaker(bind=local_engine)

# 云端 PostgreSQL
cloud_url = os.getenv("DATABASE_URL")
cloud_engine = create_engine(cloud_url)
CloudSession = sessionmaker(bind=cloud_engine)

# TODO: 实现数据迁移逻辑
```

## ✅ 部署检查清单

- [ ] Supabase 项目已创建
- [ ] 数据库表结构已初始化
- [ ] `DATABASE_URL` 已添加到 Vercel 环境变量
- [ ] 代码已推送到 GitHub
- [ ] Vercel 项目已连接到 GitHub 仓库
- [ ] 部署成功并能访问
- [ ] 数据库连接正常
- [ ] 所有功能测试通过

## 🎯 后续优化建议

1. **CDN 加速**：Vercel 自动提供 CDN，但可优化静态资源
2. **缓存策略**：添加 Redis 或使用 Vercel KV
3. **监控告警**：配置 Sentry 或 LogTail
4. **备份策略**：定期备份 Supabase 数据
5. **CI/CD**：配置 GitHub Actions 自动测试和部署
