# LAE - 个人日程与主支线管理系统

## 📋 项目概述

LAE (个人日程与主支线管理系统) 是一个个人任务和时间管理系统，旨在通过可视化的方式帮助管理多个并行任务，减少时间安排的不确定性和焦虑感。

**核心特性**：

  - 层级化活动管理（Domain x ActivityType 双轴矩阵）
  - 自由画布时间安排（V3 动态时长支持）
  - 三视图架构（汇总/周视图/月视图）
  - 精确vs模糊时间模式
  - 拖拽式/点击式交互

## 🏗️ 系统架构

**技术栈**：

  - **后端**: Python, FastAPI, SQLAlchemy, SQLite
  - **前端**: HTML5, CSS3, JavaScript, Bootstrap, Alpine.js
  - **开发**: 本地运行，浏览器访问

## 💾 数据模型

### V3 核心表结构

**`domains` (主支线)**：层级化项目/责任领域

  - `id`, `name`, `parent_id`, `description`

**`activity_types` (活动类型)**：工作性质标签

  - `id`, `name`, `parent_id`

**`schedules` (日程)**：附属于Domain的时间限制目标

  - `id`, `domain_id`, `name`, `start_date`, `deadline`, `status`

**`scheduled_events` (已安排活动)**：核心时间块单元

  - 基础字段：`id`, `event_date`, `time_slot`, `name`, `notes`, `status`
  - 关联字段：`domain_id`, `type_id`, `schedule_id`
  - V3字段：`duration`, `start_time`, `is_precise`, `canvas_position_y`, `x`, `y`

## 🔧 开发命令

```bash
# 启动开发服务器
python run.py
# 访问: http://127.0.0.1:8009

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m app.create_db
```

## 📈 开发历程记录

### V1.0 开发记录

**V1.0 开发日志 (2025-09-12 \~ 2025-09-13)**

**✅ 完成内容**：

  - 基础架构：FastAPI + SQLAlchemy + SQLite 后端
  - 三视图UI：Bootstrap + Alpine.js + SortableJS 前端
  - 核心功能：层级化活动管理、拖拽式日程安排
  - 智能拖拽：目标验证、自动重定向、错误恢复
  - **关键文件**：`app/templates/index.html`, `app/models.py`, `app/main.py`

-----

#### v1.0 系统文档 (已完成)

**版本: 1.0 (已完成)**

##### 1\. 项目背景 (Project Background)

为了解决在多任务并行时，对未来时间安排的高度不确定性和焦虑感，本项目旨在开发一个供个人使用的日程/主支线任务管理系统。通过**量化与可视化**的手段，清晰、直观地掌控个人时间和精力。

`zeroPPD` 将作为本系统设计和实践的第一个核心应用场景。

##### 2\. 核心功能 (Core Features)

  * **主支线任务管理:** 支持无限层级的父子任务结构。
  * **时间块估算与生成:** 以固定的“时段”为单位来规划任务。
  * **可视化排程白板:** 在周视图中通过拖拽方式安排日程。
  * **多视图切换:** 支持月视图、周视图和汇总视图。
  * **目标与进度管理:** 为每一次具体的日程安排附加一个可追踪的 `goal`。
  * **数据汇总与统计:** 在汇总视图中查看各主支线的精力投入和目标列表。

##### 3\. 系统架构与技术栈 (System Architecture & Technical Stack)

本项目将采用**方案A：轻量级Web框架**模式进行开发，在本地运行，通过浏览器访问。

  * **后端 (Backend):**
      * **语言:** Python
      * **Web 框架:** Flask (或 FastAPI)
      * **职责:** 负责所有业务逻辑、数据处理，并通过 API 接口与前端交互。
  * **数据库 (Database):**
      * **类型:** SQLite (单个 `.db` 文件，易于管理)
      * **交互:** 采用 **SQLAlchemy** (ORM) 进行数据库操作，以获得更好的代码可读性和维护性。
  * **前端 (Frontend):**
      * **技术:** HTML, CSS, JavaScript
      * **职责:** 负责渲染用户界面 (UI)，处理用户交互（如点击、拖拽），并通过异步请求(Ajax/Fetch)调用后端 API。

##### 4\. 数据模型 (Data Model)

系统的核心由两张 SQL 数据表构成，通过 SQLAlchemy 的 Models 进行定义。

**4.1. `activities` (活动库)**

定义所有可供选择的活动卡片及其层级关系。

| 字段名 (Field) | 类型 (Type) | 描述 |
| :--- | :--- | :--- |
| `id` | INTEGER | 唯一主键 |
| `name` | TEXT | 活动名称 (如 "zeroPPD-读文献") |
| `parent_id` | INTEGER | 指向父级活动的 `id`，顶级活动为 `NULL` |
| `description` | TEXT | (可选) 对活动的详细描述 |
| `created_at` | DATETIME | 创建时间 |

**4.2. `scheduled_events` (已安排日程)**

记录每一次具体的日程安排。

| 字段名 (Field) | 类型 (Type) | 描述 |
| :--- | :--- | :--- |
| `id` | INTEGER | 唯一主键 |
| `activity_id` | INTEGER | 外键，关联到 `activities.id` |
| `event_date` | DATE | 日程发生的日期 |
| `time_slot` | INTEGER | 时间槽编号 (详见时间槽规则) |
| `goal` | TEXT | 本次活动要达成的具体目标 (如 "读完第三篇文献") |
| `notes` | TEXT | 备注信息，不参与统计分析 |
| `status` | TEXT | 活动状态 (如: 'planned', 'completed') |

**4.3. 时间槽编码规则**

采用两位数编码：**第一位代表时段，第二位代表该时段内的序号**

**当前实现的时间槽：**

  - `21`: 上午第1时段
  - `22`: 上午第2时段
  - `51`: 下午第1时段
  - `52`: 下午第2时段
  - `71`: 晚上时段

##### 5\. 核心机制与视图逻辑 (Core Mechanisms & View Logic)

**5.1. 月视图 (Month View)**

  * **功能:** 宏观展示整月日程负荷，并作为导航入口。
  * **逻辑:** 后端查询指定月份的 `scheduled_events`，按天聚合活动数量。前端渲染日历网格，在每日单元格内显示活动数量的缩略信息。点击某一周可跳转至对应的周视图。

**5.2. 周视图 (Week View)**

  * **功能:** 项目的核心交互界面，用于日程的拖拽式编排。
  * **交互逻辑:**
    1.  用户从“活动卡片池”中拖拽一个活动卡片。
    2.  将其放置 (drop) 到主区域的某个具体时间槽中。
    3.  此时，前端可弹出一个输入框，让用户填写本次的 `goal`。
    4.  前端 JavaScript 向后端 API 发送一个 `POST` 请求。
    5.  后端在 `scheduled_events` 表中创建一条新记录。

**5.3. 汇总视图 (Summary View) - 层级化活动管理中心**

  * **功能:** 所有活动（主支线）的管理中心和层级化统计仪表盘。
  * **核心特性:**
    1.  **层级化活动管理:** 支持多级活动结构
    2.  **完整 CRUD 功能:** 创建、修改、删除任意层级的活动
    3.  **聚合统计显示:** 父级活动统计包含所有子活动的数据
    4.  **Goal 追踪管理:** 显示每个活动的所有目标及完成状态

##### 6\. 层级化活动架构 (Hierarchical Activity Architecture)

  * **设计理念:** LAE 系统采用递归的层级化活动管理，支持无限深度的活动嵌套。
  * **核心功能特性:**
    1.  **灵活拖拽:** 可将任意层级的活动拖拽到时间槽
    2.  **聚合统计:** 父级活动自动聚合所有子活动的统计数据
    3.  **Goal 管理:** 每个具体安排都有独立的目标和完成状态
    4.  **月度追踪:** 按月统计每个活动的安排频次和目标完成情况

##### 7\. Obsidian & Markdown 集成 (Obsidian & Markdown Integration)

  * **功能:** 提供"导出为 Markdown"功能，将日程安排无缝集成到现有的知识管理工作流中。

##### 7\. 开发路线图 (Development Roadmap)

**已完成阶段**

1.  **✅ Phase 1: 后端与数据基础** *(已完成)*
2.  **✅ Phase 2: 核心 UI 开发** *(已完成)*
3.  **✅ Phase 3: 功能增强** *(已完成)*
4.  **✅ Phase 4: 调试与最后优化** *(已完成)*

✅ 已修复bug (2025-09-15)

  - \~\~目前月视图存在问题，无法显示\~\~ **已修复**

##### 🎉 V1.0 开发完成 (2025-09-13)

**系统特性**：

  - ✅ 层级化活动管理（无限嵌套支持）
  - ✅ 直观的拖拽式日程安排
  - ✅ 智能的拖拽位置判断和错误修复
  - ✅ 三视图切换（汇总/周视图/月视图）
  - ✅ 完整的CRUD操作和统计功能

**技术架构**：

  - ✅ FastAPI + SQLAlchemy + SQLite 后端架构
  - ✅ Bootstrap + Alpine.js + SortableJS 前端架构

**🟢 系统已可投入使用**，所有核心功能验证通过。

##### 🚀 后续发展方向 (V2.0+)

  - Markdown导出功能
  - 移动端适配
  - 数据备份和恢复
  - 更多时间槽类型支持

##### 8\. 技术栈详情

**后端技术栈:**

  - **框架:** FastAPI 0.104.1
  - **数据库:** SQLite + SQLAlchemy 2.0.23 ORM
  - **服务器:** Uvicorn (开发环境)

**前端技术栈:**

  - **基础:** HTML5 + CSS3 + JavaScript (ES6+)
  - **UI框架:** Bootstrap 5.3.0
  - **状态管理:** Alpine.js 3.13.0
  - **拖拽功能:** SortableJS 1.15.0

-----

### V2.0 开发记录

**V2.0 开发日志 (2025-09-15 \~ 2025-09-16)**

**✅ 完成内容**：

  - 数据模型重构：引入 Domain x ActivityType 双轴矩阵
  - 新增表：`domains`, `activity_types`, `schedules`
  - 汇总视图v2.1：完整CRUD管理界面
  - Schedule时间条：周视图和月视图的时间线显示
  - **关键文件**：数据库架构升级，API端点重构

-----

#### LAE 个人日程与主支线管理系统 v2.0 - 系统架构与开发方案--草稿

##### 1\. V2 核心理念：从线性安排到矩阵管理

LAE v2.0 的核心变革是从 v1 的单线“活动 (Activity)”模型，演进为“**领域 (Domain) x 类型 (Type)**”的双轴矩阵模型。

系统承认一个个体在执行具体任务（“行动”）时，其意图是多维度的：既有**目的性**（“我做这件事是**为了**什么领域/项目？”——由 **Domain** 定义），也包含**方法性**（“我正在做的这件事**是**何种性质的工作？”——由 **Type** 定义）。

##### 2\. V2 系统架构

**2.1 概念模型**

  * **主支线 (Domains):** 定义用户长期关注的、层级化的**责任领域或项目分支**。
  * **活动类型 (Activity Types):** 定义工作**性质**的、扁平化的**标签**。
  * **日程 (Schedules):** **附属于**某个 Domain 节点下的、有时间限制的**具体目标**。
  * **已安排活动 (Actions):** 用户在周视图中安排的**最小时间块单元**。

**2.2 数据模型 (Data Model) - 初步方案**

1.  **`domains` 表 (由原 `activities` 表演进)**

      * `id` (INTEGER, PK): 主键
      * `name` (TEXT): 节点名称 (如 "zeroPPD")
      * `parent_id` (INTEGER, FK): 指向 `domains.id`，构建层级关系
      * `description` (TEXT, NULLABLE): 描述

2.  **`activity_types` 表 (新增)**

      * `id` (INTEGER, PK): 主键
      * `name` (TEXT): 类型名称 (如 "读文献")
      * `parent_id` (INTEGER, FK): 指向 `activity_types.id`，支持类型层级化

3.  **`schedules` 表 (新增)**

      * `id` (INTEGER, PK): 主键
      * `domain_id` (INTEGER, FK): **强制关联**到 `domains.id`
      * `name` (TEXT): 日程/目标名称
      * `deadline` (DATETIME, NULLABLE): 截止日期
      * `status` (TEXT): 状态 (e.g., 'ongoing', 'completed')

4.  **`scheduled_events` 表 (核心重构)**

      * `id` (INTEGER, PK): 主键
      * `event_date` (DATE): 日期
      * `time_slot` (INTEGER): 时间槽
      * `name` (TEXT): **用户自定义的行动名称**
      * `domain_id` (INTEGER, FK, **NULLABLE**): 关联到 `domains.id`
      * `type_id` (INTEGER, FK, **NULLABLE**): 关联到 `activity_types.id`
      * `schedule_id` (INTEGER, FK, **NULLABLE**): 关联到 `schedules.id`

**2.3 技术栈 (Technical Stack)**
技术栈保持与 v1 一致：

  * **后端:** Python, FastAPI, SQLAlchemy (ORM)
  * **数据库:** SQLite
  * **前端:** HTML, CSS, JavaScript, Bootstrap, Alpine.js, SortableJS

##### 3\. 初步开发方案 (Phased Approach)

**Phase 1: 数据库与后端重构 (The Foundation)**

  * **目标:** 搭建支持 V2 模型的底层基础。
  * **任务:**
    1.  **Schema 迁移:** 创建新的数据库 Schema。
    2.  **ORM 更新:** 创建 `Domain`, `ActivityType`, `Schedule` 的新 Model。
    3.  **基础 API 开发:**
          * 为 `domains` 和 `activity_types` 提供完整的层级化 CRUD API。
          * 为 `schedules` 提供基础的 CRUD API。
          * 重构 `scheduled_events` 的 CRUD API。

**Phase 2: 核心交互实现 (Core Interaction Implementation)**

  * **目标:** 让用户能够在新架构下，完成最核心的日程安排操作。
  * **任务:**
    1.  **汇总视图 v2.1 (管理中心): ✅ 已完成**
          * ✅ 实现 `domains` 和 `activity_types` 的树状结构展示。
          * ✅ 提供基础的节点管理功能：创建、重命名、删除。
          * ✅ 编辑删除功能完全实现，包括模态框和API调用。
    2.  **周视图 v2.1 (交互革命):**
          * **构建侧边栏:** 实现可切换的 `Domains` 和 `Types` 树状列表。
          * **实现点击创建:** 允许用户从侧边栏选中节点，再点击空白网格创建。
          * **开发新版编辑框:** 支持 `Name` (必填) 以及 `Domain`, `Type`, `Schedule` (可选)。

**Phase 3: 功能完善与关联 (Feature Integration)**

  * **目标:** 打通各模块间的关联，完善辅助功能。
  * **任务:**
    1.  **Schedule 功能闭环:**
          * ✅ 在汇总视图中，为 `Domain` 节点添加管理其 `Schedules` 的界面。
          * ✅ 在周视图中，查询并渲染 `Schedules` 的跨天时间条。(已完成)
    2.  **宏观视图集成:**
          * ✅ 在月视图中，查询并渲染 `Schedules` 的跨天时间条。(已完成)

-----

#### V2.0 开发注意事项与总结

**🎉 v2.2 会话成果总结 (2025-09-16)**

**✅ 本次会话完成的关键功能**

1.  **📅 Schedule起始日期功能**:
      - 为Schedule模型添加了start\_date字段
      - 更新了所有相关API支持起始日期
      - 完善了前端Schedule管理界面，支持起始和截止日期
2.  **📊 Schedule时间条基础功能**:
      - ✅ 在周视图网格上方添加了Schedule时间条展示区域
      - ✅ 实现了API支持按日期范围查询Schedule数据
      - ✅ 完成了基础的时间条渲染和颜色系统
      - ✅ 实现了跨天Schedule的检测和显示逻辑

**🔄 当前待完成的时间条优化任务**

1.  **时间条布局优化**:
      - 🔄 修改时间条为垂直堆叠布局，避免重叠遮盖
2.  **跨周连续时间条显示**:
      - 🔄 实现真正的连续时间条逻辑
3.  **交互体验优化**:
      - 🔄 优化悬停tooltip显示

-----

**🎉 v2.1 会话成果总结 (2025-09-15)**

**✅ 已完成的关键功能**

1.  **🔧 API错误修复**:
      - 修复了statistics API的500错误
      - 解决SQLAlchemy模型关系导入问题
2.  **🏗️ Domain完整CRUD实现**:
      - ✅ 编辑模态框 (showEditDomainModal)
      - ✅ updateDomain() API调用函数
      - ✅ deleteDomain() 删除功能
3.  **⚡ ActivityType完整CRUD实现**:
      - ✅ 编辑模态框 (showEditActivityTypeModal)
      - ✅ updateActivityType() API调用函数
      - ✅ deleteActivityType() 删除功能
4.  **🌐 服务器运行优化**:
      - 修复端口冲突问题
      - 服务器稳定运行在8002端口

**🎯 汇总视图v2.1 管理中心功能完成状态**

  - ✅ **Domain管理**: 创建、查看、编辑、删除全功能
  - ✅ **ActivityType管理**: 创建、查看、编辑、删除全功能
  - ✅ **树状结构展示**: 完整的层级显示

-----

### V3.0 开发记录

#### LAE v3.0 愿景：从时间网格到流动画布

**🎯 V3 核心理念：在模糊与精确之间取得平衡**

V3 的本质性变革，是放弃 V2 僵化的固定时间槽网格，转向一个更自由、更灵活、更符合直觉的“时间画布”界面。其核心是在一个统一的视图中，**实现计划的模糊性与精确性的共存与无缝转换**。

**V3 周视图 新网池的关键设计**

1.  **底层结构：10分钟微网格与视觉层级**
      - 整个系统将构建在一个以**10分钟**为单位的底层精细网格之上。
      - UI 将采用**视觉层级**设计：10分钟线细而浅，小时整点线粗而深。
2.  **核心交互：动态卡片与吸附对齐**
      - **动态高度**：任务卡片的高度与其预估**时长**成正比。
      - **吸附对齐**：所有卡片的拖拽、移动和调整大小，都会自动吸附到最近的10分钟网格线上。
      - **并行任务**：在同一时间段内，允许多张卡片**并排摆放**。
3.  **关键机制：模糊呈现 vs. 精确数据**
      - **模糊任务 (默认)**：视觉上暗示时间，不显示明确时间戳。
      - **精确任务 (按需)**：用户可以指定精确时间，如 `13:15 - 14:02`。
          - **数据层**：精确存储 `13:15` 和 `14:02`。
          - **显示层**：卡片上明确标注 "13:15 - 14:02"。
          - **布局层**：卡片在画布上的位置和大小会被**就近圆整**。
4.  **额外空间**：
    周视图的最上方 额外开辟空间，可以用来放置还没有确定时间的卡片。

-----

#### V3 完整开发方案

**核心原则**: 保持V2的交互方式兼容性 - 侧边栏选中节点后点击网格，或直接点击网格创建事件

**📋 Phase 1: 数据架构重构 (Foundation Redesign)**
**目标**: 建立支持V3动态时长和精确时间的数据基础
**🔧 任务 1.1: 数据库Schema升级**

  - **修改 `scheduled_events` 表**:
    ```sql
    -- 新增字段
    ALTER TABLE scheduled_events ADD COLUMN duration INTEGER; -- 时长(分钟)
    ALTER TABLE scheduled_events ADD COLUMN start_time TIME; -- 精确开始时间(可选)
    ALTER TABLE scheduled_events ADD COLUMN is_precise BOOLEAN DEFAULT FALSE; -- 是否精确任务
    ALTER TABLE scheduled_events ADD COLUMN canvas_position_y INTEGER DEFAULT 0; -- 画布Y坐标(并排摆放)
    ```

**🔧 任务 1.2: SQLAlchemy模型更新**

  - 更新 `ScheduledEvent` 模型，添加新字段
    **🔧 任务 1.3: API端点升级**
  - 修改 `/api/events/` 相关端点，支持新的数据字段

**📋 Phase 2: 核心画布UI重构 (Canvas Interface)**
**目标**: 实现10分钟网格系统和动态卡片交互
**🎨 任务 2.1: 10分钟微网格系统**

  - **网格架构重设计**:
    ```css
    .week-grid-v3 {
      display: grid;
      grid-template-columns: repeat(7, 1fr); /* 7天 */
      grid-template-rows: repeat(144, 10px); /* 24小时 * 6格/小时 = 144个10分钟格 */
    }
    ```

**🎨 任务 2.2: 动态卡片系统**

  - **卡片高度计算**:
    ```javascript
    // 卡片高度 = duration(分钟) / 10 * gridCellHeight(10px)
    function calculateCardHeight(durationMinutes) {
      return Math.max(durationMinutes / 10 * 10, 20); // 最小20px
    }
    ```

**🎨 任务 2.3: 智能吸附系统**

  - 实现拖拽过程中的10分钟网格吸附

**📋 Phase 3: 高级交互功能 (Advanced Interactions)**
**目标**: 实现精确vs模糊任务切换和并行摆放
**⚡ 任务 3.1: 模糊vs精确任务机制**

  - **双击切换功能**: 模糊任务双击→精确任务编辑模式
  - **精确任务编辑器**:
    **⚡ 任务 3.2: 并行摆放系统**
  - **水平位置管理**: 添加 `canvas_position_y` 字段
  - **碰撞检测**: 自动计算合适的并排位置
    **⚡ 任务 3.3: 待定区域功能**
  - 在周视图顶部实现"未确定时间"卡片池

**📋 Phase 4: 用户体验优化 (UX Enhancement)**
**目标**: 完善交互体验和视觉反馈
**✨ 任务 4.1: 交互优化**

  - 键盘快捷键
  - 右键菜单
    **✨ 任务 4.2: 视觉系统升级**
  - 时间密度可视化
  - 工作负荷指示器
    **✨ 任务 4.3: 响应式适配**
  - 缩放功能: 支持 25%\~200% 画布缩放

**📋 Phase 5: 数据迁移与向后兼容 (Migration & Compatibility)**
**目标**: 确保V2数据平滑迁移到V3
**🔄 任务 5.1: 数据迁移脚本**
**🔄 任务 5.2: 兼容模式**

**📋 Phase 6: 测试与优化 (Testing & Performance)**
**目标**: 确保V3系统稳定性和性能

**🔗 交互兼容性保证**
V3将完全保持V2的交互方式：

1.  **侧边栏选中节点后点击网格**
2.  **直接点击网格**
3.  **所有V2的编辑和管理功能**

-----

#### V3.0 开发日志

**V3.0 开发记录 (2025-09-17 \~ 2025-09-21)**

**Phase 1: 数据架构重构 (2025-09-17)**
**✅ 完成**：

  - V3字段：`duration`, `start_time`, `is_precise`, `canvas_position_y`, `x`, `y`
  - SQLAlchemy模型升级支持动态画布
  - API全面支持V3特性和向后兼容

**Phase 2A: 核心画布UI (2025-09-18)**
**✅ 完成**：

  - 10分钟微网格系统 (7:00-23:00, 96个时间格)
  - 缩放功能 (50%-200%)
  - V2/V3模式切换
  - 网格点击创建和编辑窗口

**Phase 2B: 交互模式重构 (2025-09-19)**
**✅ 完成**：

  - 移除拖拽系统，改为点击选择模式
  - 双击创建、单击选中、右键复制
  - 智能时间吸附和视觉反馈

**Canvas Phase: 自由画布系统 (2025-09-19 \~ 2025-09-21)**
**✅ 完成**：

  - 自由画布基础架构和标准网格
  - 点击选中交互系统替代拖拽
  - 卡片移动、编辑、复制功能
  - 位置时间联动计算

-----

**🔧 已修复的关键问题 (V3 开发期间)**

1.  ✅ **V3模糊卡片位置错误**:
      - 修复了`renderTaskCardV3()`方法中的位置计算逻辑
      - 确保所有卡片基于`start_time`字段正确定位
2.  ✅ **V3卡片点击编辑失效**:
      - 解决了事件绑定问题，添加了`stopPropagation()`
3.  ✅ **时间格式验证错误**:
      - 添加了`formatTimeForAPI()`方法处理时间格式转换 ("8:40" → "08:40:00")
4.  ✅ **网格对齐问题**:
      - 修复了时间轴与日期列之间的80px对齐偏移
5.  ✅ **编辑事件验证错误**:
      - 添加了`time_slot`验证和重新计算逻辑
6.  ✅ **侧边栏选择自动填入**:
      - 实现了V2兼容的`selectedNode`系统

-----

**✅ V3 Phase 2B 交互模式重构完成 (2025-09-19)**

**🎉 新交互模式实现**:
由于拖拽系统存在稳定性问题，已完全重构为基于点击选择的交互模式：

1.  **✅ 移除拖拽系统**:
      - 彻底移除SortableJS依赖和所有拖拽相关代码
2.  **✅ 新的点击选择机制**:
      - **单击空白区域**: 选择位置，显示蓝色时间线和列高亮
      - **双击空白区域**: 在选中位置创建新卡片
      - **双击已有卡片**: 编辑该卡片
      - **点击其他区域**: 清除选择状态
3.  **✅ 智能时间吸附**:
      - 自动吸附到最近的10分钟时间线
4.  **✅ 保持兼容功能**:
      - 侧边栏节点选中后的快捷输入功能完全保留
      - V3所有字段支持（duration、start\_time、is\_precise等）

**🎯 用户体验提升**:

  - 更稳定可靠的交互方式，无拖拽失效问题
  - 精确的时间定位和视觉反馈

**🛠️ 已修复问题 (2025-09-19)**:

  - ✅ **10分钟时间偏差**: 在标准缩放状态下添加偏差补偿逻辑
  - 📝 **已知限制**: 缩放和滚动状态下的时间计算仍需完善

-----

**✅ V3 自由画布系统开发完成 (2025-09-19)**

**🎉 Canvas Phase 1-2 已完成**：成功实现稳定、简洁的自由画布基础交互系统

**✅ Phase Canvas-1: 自由画布基础架构 (已完成)**

  - ✅ **标准网格背景**: 恢复时间轴、标题行、10分钟细网格线和60分钟粗网格线
  - ✅ **简单定位模式**: position: relative容器 + position: absolute卡片

**✅ Phase Canvas-2: 点击选中交互系统 (已完成)**

  - ✅ **双击创建**: 双击空白区域创建新卡片
  - ✅ **单击选中**: 单击卡片进入选中状态
  - ✅ **单击移动**: 选中卡片后，单击空白区域移动卡片到光标位置
  - ✅ **重叠支持**: 卡片可以自由重叠摆放

-----

**🚀 当前系统状态 (2025-09-20)**

**✅ V3 卡片交互功能开发完成**:

  - **数据架构**: 恢复V3数据字段(duration, start\_time, is\_precise, x, y)
  - **双击编辑**: 卡片双击弹出编辑窗口
  - **位置时间联动**: 卡片位置和时间属性实现双向计算和同步
  - **动态画布**: 支持自由位置摆放和数据库持久化

**🎯 当前交互流程**:

1.  **创建卡片**: 双击画布空白区域 → 弹出创建模态框
2.  **移动卡片**: 单击选中卡片 → 单击目标位置移动卡片
3.  **编辑卡片**: 双击已有卡片 → 弹出编辑窗口
4.  **侧边栏集成**: 选中domain/type节点后创建卡片自动填入
5.  **数据持久化**: 所有卡片变更同步保存到数据库

**🔧 2025-09-20 修复的关键问题**:

1.  ✅ **新建卡片x坐标小数验证错误** → 添加Math.round()
2.  ✅ **移动卡片后时间不更新** → 修复moveSelectedCardTo方法
3.  ✅ **编辑窗口时间编辑功能移除** → 简化为只读显示
4.  ✅ **calculateTimeFromPosition位置计算错误** → 使用动态列宽
5.  ✅ **editCard方法显示旧时间问题** → 优先使用位置计算的时间

-----

**🐛 开发日志 (2025-09-21 状态)**

**✅ 成功实现的新功能** (前期):

1.  **右键复制功能**: 单击选中卡片后，右键空白区域可复制卡片
2.  **时间偏差修复**: 修复了卡片位置和编辑窗口时间10分钟偏差

**✅ 修复的关键Bug** (前期):

1.  **移动卡片数据库更新失败** → 修复API模型缺少goal字段
2.  **编辑窗口日期显示为空** → 修复日期格式问题
3.  **程序启动时画布没有显示已有卡片** → 修复initializeFreeCanvas方法
4.  **复制卡片后原卡片消失** → 修复API冲突检测问题
5.  **创建和复制后卡片丢失** → 优化为本地数组直接更新
6.  **编辑卡片后卡片消失** → 实现V3模式下的本地更新机制

**✅ 2025-09-21 (下午) 修复的关键Bug**:
7\. **新建卡片编辑后属性无法保存** → 修复了V3模式下本地更新逻辑
8\. **旧卡片编辑时422错误** → 全面修复后端API验证逻辑 (Duration 0值, 外键兼容等)

**✅ 2025-09-21 (晚上) 修复的Bug**:
9\. **汇总页面卡片计数功能** → ✅ **已修复并正常工作**
10\. **API层面卡片移动功能** → ✅ **已修复** (修复后端Unicode编码错误)

**⚠️ 2025-09-21 遗留问题 (待修复)**:

1.  **卡片移动功能在前端界面中仍然失效** (API层面已修复，但UI层面问题持续)
2.  **🆕 卡片删除时复制卡片连带消失问题** (新发现)

-----

## 🚀 当前开发状态 (V3.2 - 2025-10-24)

### 📊 最新进展总结

**V3.2 自由画布系统 - 增强功能完成**：

  - ✅ **数据架构**：V3字段完整支持，API层面功能正常
  - ✅ **交互系统**：点击选择模式替代拖拽，操作稳定可靠
  - ✅ **核心功能**：创建、编辑、复制卡片功能完整实现
  - ✅ **待定任务区融合**：23:00网格线以下区域作为待定任务区（只有日期，无时间）
  - ✅ **日程条集成**：V3画布顶部显示Schedule时间条（复用V2组件）
  - ✅ **动态卡片高度**：根据duration字段（10-600分钟）动态调整卡片高度
  - ✅ **服务器运行**：[http://127.0.0.1:8009](http://127.0.0.1:8009) 正常运行

**当前交互流程**：

1.  双击空白区域 → 创建新卡片
2.  单击选中卡片 → 单击目标位置移动
3.  双击已有卡片 → 编辑属性
4.  右键空白区域 → 复制选中卡片
5.  在23:00以下区域创建/移动卡片 → 自动成为待定任务（无时间）

-----

### 🔧 V3.1 开发记录 (2025-10-24)

**✅ 任务1完成：待定任务区与画布融合**

**实现方案**：
- 利用23:00网格线以下的空白区域作为待定任务区
- 待定任务区的卡片特征：只有日期（`event_date`），时间为 `null`（`start_time: null`）
- 保持数据库结构不变，通过 `start_time` 是否为 `null` 来区分待定任务

**关键修改**：

1. **修改 `calculateTimeFromPosition()` 函数** ([index.html:4813-4894](app/templates/index.html#L4813-L4894))：
   - 添加23:00网格线边界检测：`gridEndY = headerOffset + (timeEndHour - timeStartHour) * 60 * v3ZoomLevel`
   - 当卡片Y坐标 > `gridEndY` 时，返回 `startTime: null`
   - 控制台输出标识：`📌 位置时间计算结果 (待定任务区):`

2. **修改 `handleCanvasDoubleClick()` 函数** ([index.html:4358-4440](app/templates/index.html#L4358-L4440))：
   - 统一使用 `calculateTimeFromPosition()` 计算时间
   - 支持在待定任务区双击创建待定任务
   - 待定任务的 `time_slot` 为空字符串

3. **扩展画布高度 `getCanvasHeight()`** ([index.html:5954-5960](app/templates/index.html#L5954-L5960))：
   - 在时间网格高度基础上增加200px待定任务区空间
   - 计算公式：`gridHeight + headerPadding + pendingAreaHeight`

**关键变量和数据结构**：
- **时间网格范围**：7:00-23:00（`v3TimeStart: 7`, `v3TimeEnd: 23`）
- **网格单位**：`gridUnit = 10 * v3ZoomLevel`（默认10px = 10分钟）
- **23:00边界Y坐标**：60 (header) + 16小时 × 60px = 1020px（缩放级别为1.0时）
- **待定任务判断**：`y > gridEndY` 且 `startTime === null`

**测试验证**：
- ✅ 时间网格区域（7:00-23:00）双击创建卡片有具体时间
- ✅ 23:00以下区域双击创建卡片时间为 null
- ✅ 卡片可在两区域间自由移动并自动更新时间状态
- ✅ 控制台输出正确的边界检测日志

**调试信息位置**：
- 控制台搜索关键词：`🔍 时间网格边界检测`、`📌 位置时间计算结果 (待定任务区)`、`🕰️ 位置时间计算结果`
- 相关函数：`calculateTimeFromPosition()`, `handleCanvasDoubleClick()`, `moveSelectedCardTo()`, `copySelectedCardTo()`

-----

### 🎯 V3.2 开发记录 (2025-10-24)

**✅ 任务2完成：引入日程条功能**

**实现方案**：
- 在V3画布顶部添加Schedule时间条区域（复用V2的日程条组件）
- 替换原有的"待定任务区"位置（位于画布上方）
- 删除"返回V2"按钮，简化界面

**关键修改**：

1. **HTML结构替换** ([index.html:982-984](app/templates/index.html#L982-L984))：
   - 删除了 `pending-area-v3` 和 `grid-toggle-v3` 控制面板
   - 添加 `schedule-timeline-container` 日程条区域
   - 使用 `x-html="renderScheduleTimeline()"` 动态渲染

2. **复用V2组件**：
   - CSS样式已存在：`.schedule-timeline-container`, `.schedule-timeline-label`, `.schedule-timeline-day`, `.schedule-bar`
   - JavaScript方法已存在：`renderScheduleTimeline()` ([index.html:3964+](app/templates/index.html#L3964))
   - 配色系统：`.schedule-color-*` 预定义8种颜色

**日程条结构说明**：
- 布局：网格布局（1个标签列 + 7天列）
- 数据来源：读取 `schedules` 表，按 `start_date` 和 `deadline` 计算跨度
- 交互功能：点击日程条可编辑（`editScheduleFromTimeline()`）

**查找相关代码的方法**：
- 搜索关键词：`schedule-timeline-container`, `renderScheduleTimeline`, `schedule-bar`
- CSS样式位置：[index.html:184-288](app/templates/index.html#L184-L288)
- 渲染方法位置：[index.html:3964+](app/templates/index.html#L3964)

**测试验证**：
- ✅ V3界面顶部显示日程条区域
- ✅ "返回V2"按钮已删除
- ✅ 日程条网格正确对齐7天列
- ✅ 如有Schedule数据，显示彩色日程条
- ✅ 点击日程条可触发编辑功能

-----

**✅ 任务3完成：动态卡片高度功能**

**需求说明**：
- 允许修改卡片时长（duration），默认60分钟
- 时长范围：10-600分钟，以10分钟为单位调整
- 卡片高度根据时长动态变化

**实现方案**：

1. **添加时长选择器** ([index.html:1298-1324](app/templates/index.html#L1298-L1324))：
   - 在编辑模态框中将只读的duration显示改为select下拉框
   - 提供22个选项：10, 20, 30...600分钟
   - 常用时长添加标注（如"60 分钟 (1小时)"）

2. **动态高度计算** ([index.html:4353-4359](app/templates/index.html#L4353-L4359))：
   - 位置：`renderFreeCard()` 方法中
   - 计算规则：
     ```javascript
     // 60分钟及以下：固定60px（保证文本可读性）
     // 60分钟以上：60px基础 + 每多1分钟增加1px
     const duration = card.duration || 60;
     const baseHeight = 60;
     const cardHeight = duration <= 60 ? baseHeight : baseHeight + (duration - 60);
     ```

3. **CSS调整** ([index.html:497](app/templates/index.html#L497))：
   - 将固定高度 `height: 60px` 改为 `min-height: 60px`
   - 允许内联style的动态高度覆盖

**高度对照表**：
| 时长 | 实际高度 |
|------|---------|
| 10分钟 | 60px |
| 30分钟 | 60px |
| 60分钟 | 60px（基准）|
| 90分钟 | 90px |
| 120分钟 | 120px |
| 180分钟 | 180px |
| 240分钟 | 240px |
| 600分钟 | 600px |

**数据保存**：
- `saveEditedEvent()` 方法已包含duration字段保存逻辑 ([index.html:3130](app/templates/index.html#L3130))
- 字段类型：整数，单位为分钟
- 默认值：60分钟

**查找相关代码的方法**：
- 时长选择器：搜索 `⏱️ 预计时长` 或 `x-model="editingEvent.duration"`
- 高度计算：搜索 `renderFreeCard` 或 `动态高度计算`
- 保存逻辑：搜索 `saveEditedEvent` 或 `duration: this.editingEvent.duration`

**测试验证**：
- ✅ 编辑模态框中可修改时长（10-600分钟可选）
- ✅ 60分钟及以下卡片高度统一为60px
- ✅ 超过60分钟的卡片高度线性增长
- ✅ 修改时长后刷新页面，高度正确更新
- ✅ 数据库正确保存duration值

-----

### 🎯 V3.3 开发记录 (2025-10-24)

**✅ 任务4完成：Obsidian集成**

**实现方案**：
- 创建Python脚本读取今日任务卡片，生成Markdown格式，写入指定Obsidian文件
- 使用双标记模式（`## 自动插入` 和 `## 自动插入尾部`）实现自动覆盖内容

**创建的文件**：
1. **`export_to_obsidian.py`** ([根目录](export_to_obsidian.py))
   - 核心导出脚本，包含数据库查询、格式化、文件写入逻辑
   - 配置区域（12-21行）：可修改目标文件路径、数据库路径、标记文本

2. **`export_to_obsidian.bat`** ([根目录](export_to_obsidian.bat))
   - Windows批处理启动脚本，双击即可运行

3. **`clear_export.py`** ([根目录](clear_export.py))
   - 清空脚本，用于手动清除自动插入区域的内容（可选使用）

**关键数据结构和配置**：

查看 `export_to_obsidian.py` 文件中的以下关键部分：
- **配置区域**（12-21行）：
  - `OBSIDIAN_FILE`: 目标Markdown文件路径
  - `DB_PATH`: 数据库路径（`./data/lae_schedule.db`）
  - `INSERT_MARKER`: 开始标记（`## 自动插入`）
  - `INSERT_MARKER_END`: 结束标记（`## 自动插入尾部`）

- **时段划分规则**（PERIODS字典，35-43行）：
注：我手动增加了午睡后这一时段 因此实际数据和此处记录的有出入
- **数据库查询**（`get_today_cards()` 函数，105-154行）：
  - 从 `scheduled_events` 表读取今日任务
  - 左连接 `domains` 和 `activity_types` 表获取领域和类型名称
  - 字段名注意：`activity_type_id`（不是 `type_id`）

- **卡片格式化**（`format_card()` 函数，161-176行）：
  ```
  时间: HH:MM-HH:MM
  活动: 卡片名称
  领域: 领域名称
  类型: 类型名称
  备注: 备注内容（如有）
  ```

- **写入逻辑**（`insert_to_obsidian_file()` 函数，237-287行）：
  - 双标记模式：自动清空两个标记之间的旧内容
  - 验证标记存在性和顺序
  - 保留标记外的内容不变

**使用方法**：
1. 确保目标MD文件中包含两行标记：
   - `## 自动插入`
   - `## 自动插入尾部`（必须在开始标记下方）
2. 双击运行 `export_to_obsidian.bat`
3. 脚本会自动清空标记之间的内容，插入今日任务

**重要特性**：
- ✅ 自动覆盖模式（不是追加）
- ✅ 待定任务（无时间）放在清晨时段之前
- ✅ UTF-8编码处理，支持中文
- ✅ 完整的错误检查和提示信息

**测试验证**：
- ✅ 脚本正常运行，找到5张测试卡片
- ✅ 成功写入目标文件
- ✅ 多次运行正确覆盖（不追加）
- ✅ 格式符合需求（时间/活动/领域/类型/备注）

**调试和排错**：
- 数据库表结构查看方法：
  ```python
  python -c "import sqlite3; conn = sqlite3.connect('./data/lae_schedule.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(scheduled_events)'); print([row for row in cursor.fetchall()])"
  ```
- 查看生成内容但不写入文件：修改 `main()` 函数，在写入前打印 `markdown_content`

-----

### 📋 下次会话计划

**任务5：潜在优化任务（按需）**
- 卡片内容自适应显示（长时长卡片显示更多信息）
- 日程条的创建和编辑功能增强
- 性能优化：大量卡片渲染优化
- 导出功能：周视图导出为图片或PDF

**Obsidian集成增强（如需）**：
- 支持导出指定日期（不只是今天）
- 添加统计信息（总时长、任务数量等）
- 支持更多导出格式
- GUI图形界面