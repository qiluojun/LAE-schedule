# -*- coding: utf-8 -*-
"""
LAE Obsidian 导出脚本
功能：读取今日任务卡片，生成Markdown格式，写入指定文件
"""

import sqlite3
from datetime import datetime
from pathlib import Path


# ==================== 配置区域 ====================
# Obsidian Markdown 文件路径
OBSIDIAN_FILE = r"C:\OneDrive_Downloads\qiluo\00-BASE\我也不知道为啥才搞.md"

# 数据库路径（相对于脚本所在目录）
DB_PATH = "./data/lae_schedule.db"

# 自动插入标记
INSERT_MARKER = "## 自动插入"
INSERT_MARKER_END = "## 自动插入尾部"

# 时段定义（开始时间 -> 时段名称）
TIME_PERIODS = [
    ("05:00", "### 1清晨"),
    ("09:30", "### 2上午"),
    ("11:30", "### 3午饭后"),
    ("13:00", "### 4午睡后"),  # 注意：实际归入下午
    ("13:30", "### 5下午"),
    ("17:30", "### 6晚饭后"),
    ("19:00", "### 7晚上"),
    ("21:30", "### 8睡前"),
]

# 简化的时段定义（实际使用）
PERIODS = {
    "清晨": ("05:00", "09:30"),
    "上午": ("09:30", "11:30"),
    "午饭后": ("11:30", "12:30"),
    "午睡后": ("13:30", "13:30"),  
    "下午": ("13:30", "17:30"),
    "晚饭后": ("17:30", "19:00"),
    "晚上": ("19:00", "21:30"),
    "睡前": ("21:30", "23:59"),
}


# ==================== 工具函数 ====================

def time_to_minutes(time_str):
    """将时间字符串转换为分钟数（从00:00开始）"""
    if not time_str:
        return None
    try:
        h, m = map(int, time_str.split(':')[:2])
        return h * 60 + m
    except:
        return None


def get_period_name(start_time):
    """根据开始时间判断所属时段"""
    if not start_time:
        return None

    minutes = time_to_minutes(start_time)
    if minutes is None:
        return None

    # 按顺序检查时段
    if minutes < time_to_minutes("09:30"):
        return "清晨"
    elif minutes < time_to_minutes("11:30"):
        return "上午"
    elif minutes < time_to_minutes("12:30"):
        return "午饭后"
    elif minutes < time_to_minutes("13:30"):
        return "午睡后"
    elif minutes < time_to_minutes("17:30"):
        return "下午"
    elif minutes < time_to_minutes("19:00"):
        return "晚饭后"
    elif minutes < time_to_minutes("21:30"):
        return "晚上"
    else:
        return "睡前"


def format_time_range(start_time, duration):
    """格式化时间范围（开始时间-结束时间）"""
    if not start_time:
        return "时间待定"

    try:
        start_minutes = time_to_minutes(start_time)
        if start_minutes is None:
            return "时间待定"

        end_minutes = start_minutes + (duration or 60)
        end_h = end_minutes // 60
        end_m = end_minutes % 60

        return f"{start_time[:5]}-{end_h:02d}:{end_m:02d}"
    except:
        return start_time[:5] if start_time else "时间待定"


# ==================== 数据库查询 ====================

def get_today_cards():
    """从数据库读取今日的任务卡片"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 连接数据库
    db_path = Path(__file__).parent / DB_PATH
    if not db_path.exists():
        print(f"❌ 错误：数据库文件不存在 - {db_path}")
        return []

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 查询今日的任务卡片，并关联领域和类型信息
    query = """
    SELECT
        e.id,
        e.name,
        e.start_time,
        e.duration,
        e.notes,
        d.name as domain_name,
        t.name as type_name
    FROM scheduled_events e
    LEFT JOIN domains d ON e.domain_id = d.id
    LEFT JOIN activity_types t ON e.activity_type_id = t.id
    WHERE e.event_date = ?
    ORDER BY
        CASE WHEN e.start_time IS NULL THEN 0 ELSE 1 END,
        e.start_time
    """

    cursor.execute(query, (today,))
    rows = cursor.fetchall()

    # 转换为字典列表
    cards = []
    for row in rows:
        cards.append({
            'id': row[0],
            'name': row[1],
            'start_time': row[2],
            'duration': row[3] or 60,
            'notes': row[4] or '',
            'domain': row[5] or '未分类',
            'type': row[6] or '未分类'
        })

    conn.close()
    return cards


# ==================== Markdown 生成 ====================

def format_card(card):
    """格式化单张卡片为Markdown格式"""
    time_range = format_time_range(card['start_time'], card['duration'])

    lines = [
        f"时间: {time_range}",
        f"活动: {card['name']}",
        f"领域: {card['domain']}",
        f"类型: {card['type']}",
    ]

    # 只有当备注不为空时才添加
    if card['notes'].strip():
        lines.append(f"备注: {card['notes']}")

    return '\n'.join(lines)


def generate_markdown_content(cards):
    """生成完整的Markdown内容"""
    lines = []

    # 1. 待定任务（无时间的卡片）
    pending_cards = [c for c in cards if not c['start_time']]
    if pending_cards:
        for card in pending_cards:
            lines.append(format_card(card))
            lines.append('')  # 卡片之间空一行

    # 2. 按时段分组
    period_cards = {
        "清晨": [],
        "上午": [],
        "午饭后": [],
        "下午": [],
        "晚饭后": [],
        "晚上": [],
        "睡前": [],
    }

    for card in cards:
        if card['start_time']:
            period = get_period_name(card['start_time'])
            if period and period in period_cards:
                period_cards[period].append(card)

    # 3. 生成各时段内容
    period_order = ["清晨", "上午", "午饭后", "下午", "晚饭后", "晚上", "睡前"]

    for period_name in period_order:
        # 输出时段标题
        if period_name == "午睡后":
            continue  # 跳过午睡后（已合并到下午）

        # 时段编号映射
        period_nums = {
            "清晨": "1", "上午": "2", "午饭后": "3",
            "下午": "5", "晚饭后": "6", "晚上": "7", "睡前": "8"
        }
        num = period_nums.get(period_name, "")
        lines.append(f"### {num}{period_name}")
        lines.append('')

        # 输出该时段的卡片
        for card in period_cards[period_name]:
            lines.append(format_card(card))
            lines.append('')  # 卡片之间空一行

    return '\n'.join(lines)


# ==================== 文件写入 ====================

def insert_to_obsidian_file(content):
    """将生成的内容插入到Obsidian文件中（双标记模式：自动清空区域内容）"""
    file_path = Path(OBSIDIAN_FILE)

    # 检查文件是否存在
    if not file_path.exists():
        print(f"❌ 错误：目标文件不存在 - {file_path}")
        return False

    # 读取原文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"❌ 错误：无法读取文件 - {e}")
        return False

    # 查找开始标记
    if INSERT_MARKER not in original_content:
        print(f"❌ 错误：未找到开始标记 '{INSERT_MARKER}'")
        return False

    # 查找结束标记
    if INSERT_MARKER_END not in original_content:
        print(f"❌ 错误：未找到结束标记 '{INSERT_MARKER_END}'")
        return False

    # 查找标记位置
    start_pos = original_content.find(INSERT_MARKER)
    end_pos = original_content.find(INSERT_MARKER_END)

    # 验证标记顺序
    if start_pos >= end_pos:
        print(f"❌ 错误：结束标记必须在开始标记之后")
        return False

    # 构建新内容：开始标记之前 + 开始标记 + 新内容 + 结束标记 + 结束标记之后
    before_marker = original_content[:start_pos + len(INSERT_MARKER)]
    after_end_marker = original_content[end_pos:]

    new_content = before_marker + '\n\n' + content + '\n\n' + after_end_marker

    # 写入文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 成功：已清空旧内容并写入新内容")
        return True
    except Exception as e:
        print(f"❌ 错误：无法写入文件 - {e}")
        return False


# ==================== 主函数 ====================

def main():
    # 设置Windows控制台为UTF-8编码
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 50)
    print("LAE Obsidian 导出工具")
    print("=" * 50)
    print()

    # 1. 读取今日卡片
    print("📖 正在读取今日任务卡片...")
    cards = get_today_cards()
    print(f"   找到 {len(cards)} 张卡片")
    print()

    if not cards:
        print("⚠️  提示：今日无任务卡片，跳过导出")
        return

    # 2. 生成Markdown内容
    print("📝 正在生成Markdown内容...")
    markdown_content = generate_markdown_content(cards)
    print("   内容生成完成")
    print()

    # 3. 写入Obsidian文件
    print("💾 正在写入Obsidian文件...")
    success = insert_to_obsidian_file(markdown_content)
    print()

    if success:
        print("🎉 导出完成！")
    else:
        print("❌ 导出失败，请检查错误信息")

    print("=" * 50)


if __name__ == "__main__":
    main()
