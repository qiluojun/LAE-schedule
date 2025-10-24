# -*- coding: utf-8 -*-
"""
清理 Obsidian 导出内容
功能：删除"自动插入"标记后的所有内容
"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 文件路径
FILE_PATH = r"C:\OneDrive_Downloads\qiluo\00-BASE\我也不知道为啥才搞.md"
MARKER_START = "## 自动插入"
MARKER_END = "## 自动插入尾部"


def clear_content():
    """清除自动插入区域的内容（双标记模式）"""
    try:
        # 读取文件
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找开始标记
        if MARKER_START not in content:
            print(f"⚠️  未找到开始标记 '{MARKER_START}'")
            return False

        # 查找结束标记
        if MARKER_END not in content:
            print(f"⚠️  未找到结束标记 '{MARKER_END}'")
            return False

        # 查找标记位置
        start_pos = content.find(MARKER_START)
        end_pos = content.find(MARKER_END)

        # 验证标记顺序
        if start_pos >= end_pos:
            print(f"❌ 错误：结束标记必须在开始标记之后")
            return False

        # 构建新内容：保留开始标记之前和结束标记之后的内容，清空中间部分
        before_marker = content[:start_pos + len(MARKER_START)]
        after_end_marker = content[end_pos:]

        new_content = before_marker + '\n\n' + after_end_marker

        # 写回文件
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)

        deleted_chars = end_pos - (start_pos + len(MARKER_START))
        print("✅ 已清除自动插入区域的内容")
        print(f"   删除了 {deleted_chars} 个字符")
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("清理 Obsidian 自动导出内容")
    print("=" * 50)
    print()

    clear_content()

    print()
    print("=" * 50)
