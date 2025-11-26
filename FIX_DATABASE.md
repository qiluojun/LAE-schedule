# 数据库表结构重建指南

## 🚨 问题说明

你遇到的 500 错误和 "创建领域失败" 是因为：
1. Supabase 数据库表结构与 Python 模型定义不匹配
2. 缺少必要的索引和默认值

## ✅ 已修复内容

### 1. 修复了所有模型定义
- ✅ 所有 `String` 类型改为 `String(255)` 指定长度
- ✅ 所有主键添加 `autoincrement=True`
- ✅ `scheduled_events.time_slot` 改为可选（支持V3待定任务）

修改的文件：
- `app/models/domain.py`
- `app/models/activity_type.py`
- `app/models/schedule.py`
- `app/models/scheduled_event.py`
- `app/models/activity.py`

## 🔧 立即修复步骤

### 方法 1：删除并重建表（推荐，如果没有重要数据）

#### 步骤 1：登录 Supabase
1. 访问 https://supabase.com/
2. 进入你的项目
3. 点击左侧 "SQL Editor"

#### 步骤 2：删除旧表
复制以下 SQL 并执行：

```sql
-- 删除所有旧表（按依赖顺序）
DROP TABLE IF EXISTS scheduled_events CASCADE;
DROP TABLE IF EXISTS schedules CASCADE;
DROP TABLE IF EXISTS activities CASCADE;
DROP TABLE IF EXISTS activity_types CASCADE;
DROP TABLE IF EXISTS domains CASCADE;
```

#### 步骤 3：创建新表
复制以下 SQL 并执行：

```sql
-- 创建 domains 表
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES domains(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_domains_id ON domains(id);
CREATE INDEX ix_domains_name ON domains(name);

-- 创建 activity_types 表
CREATE TABLE activity_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES activity_types(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_activity_types_id ON activity_types(id);
CREATE INDEX ix_activity_types_name ON activity_types(name);

-- 创建 schedules 表
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'ongoing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_schedules_id ON schedules(id);
CREATE INDEX ix_schedules_name ON schedules(name);
CREATE INDEX ix_schedules_status ON schedules(status);

-- 创建 activities 表 (V1兼容)
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES activities(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_activities_id ON activities(id);
CREATE INDEX ix_activities_name ON activities(name);

-- 创建 scheduled_events 表
CREATE TABLE scheduled_events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    time_slot VARCHAR(10),
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'planned',
    activity_id INTEGER REFERENCES activities(id),
    goal TEXT,
    domain_id INTEGER REFERENCES domains(id),
    activity_type_id INTEGER REFERENCES activity_types(id),
    schedule_id INTEGER REFERENCES schedules(id),
    duration INTEGER,
    start_time TIME,
    is_precise BOOLEAN DEFAULT FALSE,
    canvas_position_y INTEGER DEFAULT 0,
    x INTEGER,
    y INTEGER
);

CREATE INDEX ix_scheduled_events_id ON scheduled_events(id);
CREATE INDEX ix_scheduled_events_event_date ON scheduled_events(event_date);
```

### 方法 2：修改现有表（如果有重要数据需要保留）

如果你已经有数据需要保留，在 Supabase SQL Editor 执行：

```sql
-- 修改 domains 表
ALTER TABLE domains
ALTER COLUMN name TYPE VARCHAR(255);

-- 修改 activity_types 表
ALTER TABLE activity_types
ALTER COLUMN name TYPE VARCHAR(255);

-- 修改 schedules 表
ALTER TABLE schedules
ALTER COLUMN name TYPE VARCHAR(255),
ALTER COLUMN status TYPE VARCHAR(50);

-- 修改 scheduled_events 表
ALTER TABLE scheduled_events
ALTER COLUMN name TYPE VARCHAR(255),
ALTER COLUMN status TYPE VARCHAR(50),
ALTER COLUMN time_slot TYPE VARCHAR(10),
ALTER COLUMN time_slot DROP NOT NULL;  -- 改为可选

-- 添加缺失的索引
CREATE INDEX IF NOT EXISTS ix_domains_name ON domains(name);
CREATE INDEX IF NOT EXISTS ix_activity_types_name ON activity_types(name);
CREATE INDEX IF NOT EXISTS ix_schedules_name ON schedules(name);
CREATE INDEX IF NOT EXISTS ix_scheduled_events_event_date ON scheduled_events(event_date);
```

## 🚀 部署修复代码

完成数据库修复后，推送代码更新：

```bash
# 1. 提交所有模型修改
git add app/models/*.py DEPLOYMENT.md FIX_DATABASE.md
git commit -m "Fix: PostgreSQL model definitions with proper types and autoincrement"

# 2. 推送到 GitHub
git push origin main
```

Vercel 会自动重新部署（1-2分钟）。

## 🧪 验证修复

### 1. 等待部署完成
- 访问 Vercel Dashboard
- 确认部署状态为 "Ready"

### 2. 测试创建 Domain
1. 刷新网页（Ctrl+F5 强制刷新）
2. 切换到"汇总视图"
3. 点击"➕ 新建Domain"
4. 输入名称（例如："工作"）
5. 点击"创建"

**预期结果**：
- ✅ 创建成功，不再出现 500 错误
- ✅ Domain 出现在列表中

### 3. 测试创建任务卡片
1. 切换到"周视图"
2. 双击画布空白区域
3. 填写任务信息
4. 点击"保存"

**预期结果**：
- ✅ 创建成功，不再出现 "not valid JSON" 错误
- ✅ 卡片显示在画布上

### 4. 验证数据持久化
1. 刷新浏览器（F5）
2. 检查数据是否仍然存在

**预期结果**：
- ✅ 所有数据都保留，说明成功保存到 Supabase

## ❓ 常见问题

### Q1: 执行 SQL 时出现"table already exists"错误
**A:** 使用方法 1 中的 DROP TABLE 命令先删除旧表，然后再创建新表。

### Q2: 仍然出现 500 错误
**A:** 检查：
1. Vercel 是否部署成功（查看部署日志）
2. 浏览器是否清除了缓存（Ctrl+Shift+R）
3. Supabase 数据库是否在线

### Q3: 如何查看详细错误信息
**A:** 在 Vercel 项目页面：
1. 点击 "Functions" 标签
2. 选择最近的调用
3. 查看 "Logs" 获取详细错误

### Q4: 数据类型不匹配错误
**A:** 确保执行了方法 1 的完整 SQL，特别是 `time_slot VARCHAR(10)` 的修改。

## 📊 检查数据库表结构

执行以下 SQL 验证表结构是否正确：

```sql
-- 查看 domains 表结构
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'domains'
ORDER BY ordinal_position;

-- 查看 scheduled_events 表结构
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'scheduled_events'
ORDER BY ordinal_position;
```

**预期结果**：
- `name` 列应该是 `character varying(255)`
- `time_slot` 列应该是 `character varying(10)` 且 `is_nullable = YES`
- `status` 列应该是 `character varying(50)`

## ✅ 成功标志

修复成功后，你应该能够：
- ✅ 创建 Domain 不出错
- ✅ 创建 ActivityType 不出错
- ✅ 在周视图创建任务卡片不出错
- ✅ 刷新页面数据仍然存在
- ✅ 在 Supabase Table Editor 看到新建的数据

## 📞 还有问题？

如果仍然无法解决，请提供：
1. Supabase SQL Editor 执行结果截图
2. Vercel Functions 日志截图
3. 浏览器控制台错误信息（F12 → Console）
