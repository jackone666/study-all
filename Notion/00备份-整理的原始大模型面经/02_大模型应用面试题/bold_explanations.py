#!/usr/bin/env python3
"""
对关键解释加粗：
1. "一句话"和"背诵抓手"整行加粗（它们是每道题最核心的解释）
2. 正文中的关键结论句加粗（核心区别在于...、关键在于...等模式）
"""
import re
from pathlib import Path

DIR = Path("/Users/zing/Desktop/Obsidian文件/面试准备/面试题")

# 关键解释标志词 — 从这些词开始到句号为止，整句加粗
EXPLANATION_MARKERS = [
    '核心区别在于',
    '本质区别在于',
    '核心思想是',
    '核心观点是',
    '核心思路是',
    '关键在于',
    '重点是',
    '本质上',
    '总结',
    '总的来说',
    '一句话概括',
    '核心特征',
    '核心挑战',
    '核心问题',
    '最大的问题是',
    '根本限制',
    '根本性的局限',
    '关键点在于',
    '核心价值',
    '关键价值在于',
    '核心瓶颈',
    '最重要的是',
    '更重要的是',
    '需要注意的是',
    '关键是要',
    '决定性因素是',
]

# 短结论模式 — 跟着破折号后面的总结（就像——后面的内容）
DASH_CONCLUSION = re.compile(r'(——)([^。；\n]+)')


def bold_key_sentences(text: str) -> str:
    """对包含关键解释标志词的句子加粗，直到句号/分号/换行为止"""
    for marker in EXPLANATION_MARKERS:
        pattern = rf'({re.escape(marker)}[^。；\n]*)'
        text = re.sub(pattern, r'**\1**', text)
    return text


def bold_dash_conclusions(text: str) -> str:
    """对破折号后面的总结性短句加粗"""
    return DASH_CONCLUSION.sub(r'\1**\2**', text)


def format_question_content(content: str) -> str:
    """对单个题目的内容进行加粗处理"""
    lines = content.splitlines()
    new_lines = []

    for line in lines:
        stripped = line.strip()

        # 跳过标题行、表格行、代码块
        if stripped.startswith('#') or stripped.startswith('|'):
            new_lines.append(line)
            continue

        # 「一句话：」整行加粗
        if stripped.startswith('**一句话：**'):
            # 改为整行加粗
            inner = stripped[len('**一句话：**'):]
            if inner:
                new_lines.append(f'**一句话：{inner}**')
            else:
                new_lines.append(line)
            continue

        # 「背诵抓手：」整行加粗
        if stripped.startswith('**背诵抓手：**'):
            inner = stripped[len('**背诵抓手：**'):]
            if inner:
                new_lines.append(f'**背诵抓手：{inner}**')
            else:
                new_lines.append(line)
            continue

        # 正文：对关键解释句加粗
        line = bold_key_sentences(line)
        line = bold_dash_conclusions(line)

        new_lines.append(line)

    return '\n'.join(new_lines)


def process_file(filepath: Path) -> int:
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_code_block = False
    changes = 0
    new_lines = []

    for line in lines:
        stripped = line.strip()

        # 跟踪代码块
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue

        if in_code_block:
            new_lines.append(line)
            continue

        original = line

        # 跳过标题和表格
        if stripped.startswith('#') or stripped.startswith('|'):
            new_lines.append(line)
            continue

        # 「一句话：」整行加粗
        if stripped.startswith('**一句话：**'):
            inner = stripped[len('**一句话：**'):]
            if inner:
                # 检查是否已经整行加粗
                if not stripped.endswith('**'):
                    new_lines.append(f'**一句话：{inner}**')
                    changes += 1
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            continue

        # 「背诵抓手：」整行加粗
        if stripped.startswith('**背诵抓手：**'):
            inner = stripped[len('**背诵抓手：**'):]
            if inner:
                if not stripped.endswith('**'):
                    new_lines.append(f'**背诵抓手：{inner}**')
                    changes += 1
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            continue

        # 正文：对关键解释句加粗
        line = bold_key_sentences(line)
        line = bold_dash_conclusions(line)

        if line != original:
            changes += 1
        new_lines.append(line)

    result = '\n'.join(new_lines)
    filepath.write_text(result, encoding="utf-8")
    return changes


def main():
    md_files = sorted(DIR.glob("*.md"))
    total = 0
    for fp in md_files:
        n = process_file(fp)
        total += n
        print(f"  {fp.name}: {n} 处修改")
    print(f"总计: {total} 处修改")


if __name__ == "__main__":
    main()
