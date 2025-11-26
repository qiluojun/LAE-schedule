# 快速修复指南 - 500 错误问题

## 问题描述
部署到 Vercel 后，访问网页一直弹窗：**"操作失败: API错误: 500 - Internal Server Error"**

## 根本原因
Supabase 数据库是空的（只有表结构，没有数据），前端在加载统计数据时调用的 API 没有正确处理空数据库的情况。

## ✅ 已修复内容

### 1. 修改了 `app/api/statistics.py` 文件
为以下 API 添加了异常处理，确保空数据库时返回默认值而不是 500 错误：

- ✅ `/api/statistics/summary` - 系统总体统计
- ✅ `/api/statistics/domains/statistics` - Domain 统计
- ✅ `/api/statistics/activity-types/statistics` - ActivityType 统计

### 2. 错误处理机制
所有统计 API 现在都使用 try-catch 包裹，当数据库为空或出错时：
- 打印错误日志到控制台
- 返回空字典 `{}` 或默认值（如 `{total_events: 0, ...}`）
- 前端能够正常处理这些空数据

## 🚀 部署修复

### 方法 1：Git 推送自动部署（推荐）
```bash
git add app/api/statistics.py
git commit -m "Fix: Handle empty database in statistics APIs"
git push origin main
```

Vercel 会自动检测到 GitHub 的更新并重新部署（1-2分钟）。

### 方法 2：Vercel CLI 手动部署
```bash
vercel --prod
```

## 📝 验证修复

部署完成后，访问你的 Vercel 网站：

### 1. 不再出现 500 错误弹窗
- ✅ 页面应该能正常加载
- ✅ 汇总视图显示空的统计数据（全为 0）

### 2. 测试数据库写入功能

#### 步骤 1：创建 Domain（领域）
1. 切换到"汇总视图"
2. 在左侧"主支线管理"区域点击"➕ 新建Domain"
3. 输入名称（例如："工作"、"学习"、"个人项目"）
4. 点击"创建"

#### 步骤 2：创建 ActivityType（活动类型）
1. 在右侧"活动类型管理"区域点击"➕ 新建活动类型"
2. 输入名称（例如："编程"、"阅读"、"会议"）
3. 点击"创建"

#### 步骤 3：在周视图创建任务卡片
1. 切换到"周视图"
2. 双击画布上的空白区域
3. 填写任务信息：
   - 名称：例如 "完成项目报告"
   - 选择 Domain
   - 选择 ActivityType
   - 设置时长
4. 点击"保存"

#### 步骤 4：验证数据库更新
**方法 A：在 Supabase 查看**
1. 登录 Supabase
2. 进入你的项目
3. 点击左侧 "Table Editor"
4. 查看以下表：
   - `domains` - 应该能看到你创建的 Domain
   - `activity_types` - 应该能看到你创建的 ActivityType
   - `scheduled_events` - 应该能看到你创建的任务卡片

**方法 B：刷新页面验证**
1. 刷新浏览器（F5）
2. 如果之前创建的数据都还在，说明已成功保存到 Supabase

## 🎯 数据库自动更新机制

### ✅ 是的，数据会实时同步到 Supabase！

当你在网页上执行以下操作时，数据会**立即**写入 Supabase PostgreSQL 数据库：

| 操作 | API 端点 | Supabase 表 |
|------|---------|-------------|
| 创建 Domain | `POST /api/domains/` | `domains` |
| 编辑 Domain | `PUT /api/domains/{id}` | `domains` |
| 删除 Domain | `DELETE /api/domains/{id}` | `domains` |
| 创建 ActivityType | `POST /api/activity-types/` | `activity_types` |
| 创建任务卡片 | `POST /api/events/` | `scheduled_events` |
| 移动卡片 | `PUT /api/events/{id}` | `scheduled_events` |
| 编辑卡片 | `PUT /api/events/{id}` | `scheduled_events` |
| 删除卡片 | `DELETE /api/events/{id}` | `scheduled_events` |
| 创建 Schedule | `POST /api/schedules/` | `schedules` |

### 数据同步流程

```
前端操作 → FastAPI API → SQLAlchemy ORM → PostgreSQL (Supabase)
           ↓
      检测 DATABASE_URL 环境变量
           ↓
      自动连接到 Supabase 数据库
```

### 实时性
- **延迟**：通常 < 100ms（取决于网络）
- **持久化**：立即保存，刷新页面数据仍在
- **多设备**：不同设备访问同一个 URL，看到的是同一份数据

## ❓ 常见问题

### Q1: 修复后仍然看到 500 错误？
**A:** 检查以下几点：
1. 确认已推送代码到 GitHub
2. 检查 Vercel 部署日志是否成功
3. 清除浏览器缓存（Ctrl+Shift+R 强制刷新）
4. 检查 Supabase 项目是否处于激活状态

### Q2: 创建的数据在 Supabase 看不到？
**A:** 检查：
1. Vercel 环境变量 `DATABASE_URL` 是否正确设置
2. 在 Supabase SQL Editor 运行：`SELECT * FROM domains;` 查看数据
3. 检查是否连接到正确的 Supabase 项目

### Q3: 数据库表不存在？
**A:** 需要在 Supabase 创建表结构，参考 `DEPLOYMENT.md` 中的建表 SQL

### Q4: 如何查看详细的错误信息？
**A:**
1. 在 Vercel 项目页面点击 "Functions"
2. 选择最近的函数调用
3. 查看 Logs 标签页
4. 或者在浏览器按 F12 打开开发者工具 → Console 标签页

## 📞 需要帮助？

如果问题仍未解决，请提供以下信息：
1. Vercel 部署日志截图
2. 浏览器控制台错误信息（F12 → Console）
3. Supabase 数据库表列表截图
4. 具体的操作步骤和错误信息
