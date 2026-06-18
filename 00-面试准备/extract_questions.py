#!/usr/bin/env python3
"""提取面试题目，去重，只保留面试回答要点。"""
import re
import os
from pathlib import Path
from collections import OrderedDict

SRC_DIRS = [
    "/Users/zing/Desktop/Obsidian文件/面试准备/00备份/01_面试真题",
    "/Users/zing/Desktop/Obsidian文件/面试准备/00备份/02_大模型应用面试题",
]
OUT_DIR = Path("/Users/zing/Desktop/Obsidian文件/面试准备/简化")


def extract_questions_from_file(filepath: str) -> list[dict]:
    """从单个文件提取所有带 [重要性:X] 标签的题目。"""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    questions = []
    # 匹配 ## 或 ### 级别 + [重要性:S/A] 标签的标题行
    # 用括号捕获标题级别
    pattern = re.compile(
        r'^(#{2,3})\s+(.+?)\s*\[重要性:([SA])\]\s*$',
        re.MULTILINE
    )

    matches = list(pattern.finditer(text))
    for idx, m in enumerate(matches):
        level = len(m.group(1))  # 2 or 3
        title = m.group(2).strip()
        importance = m.group(3)

        # 去除编号前缀
        title_clean = re.sub(r'^[\d一二三四五六七八九十]+[\.\、\s]+', '', title).strip()

        # 提取 body：从当前标题结束到下一个同级或更高级标题
        body_start = m.end()
        body_end = len(text)

        # 找下一个同级或更高级标题
        next_pattern = re.compile(
            rf'^{"#" * level}\s+.+$|^{"#" * (level-1)}\s+.+$',
            re.MULTILINE
        )
        next_m = next_pattern.search(text, body_start)
        if next_m:
            body_end = next_m.start()

        body = text[body_start:body_end].strip()

        # 检查 📎 重复题目（在 body 中或在前 300 字符内）
        is_dup = bool(re.search(r'📎\s*重复题目', body))

        # 也检查标题行之前的 300 字符（如果 📎 在外层分组标题下）
        if not is_dup:
            before_start = max(0, m.start() - 400)
            before = text[before_start:m.start()]
            if re.search(r'📎\s*重复题目', before):
                # 确认这个 📎 和当前标题之间没有其他问题标题
                between = text[before_start:m.start()]
                if not re.search(r'\[重要性:[SA]\]', between):
                    is_dup = True

        # 提取回答内容
        answers = extract_answers(body)

        questions.append({
            "title": title_clean,
            "importance": importance,
            "answers": answers,
            "is_dup": is_dup,
            "source_file": os.path.basename(filepath),
            "source_dir": os.path.basename(os.path.dirname(filepath)),
        })

    return questions


def extract_answers(body: str) -> dict:
    """从题目 body 中提取回答要点。"""
    result = {
        "one_liner": "",
        "grasp": "",
        "simple_answer": "",
        "interview_answer": "",
        "project_answer": "",
    }

    # 一句话 / 面试速记（取第一个匹配）
    for pattern in [r'\*\*一句话[：:]\*\*', r'\*\*面试速记[：:]\*\*']:
        m = re.search(pattern + r'\s*(.+?)(?=\n\n\*\*|\n###|\n####|\Z)', body, re.DOTALL)
        if m:
            raw = m.group(1).strip()
            # 分离嵌入的记忆抓手（可能带 ** 或不带）
            grasp_match = re.search(r'\*\*(?:记忆|背诵)抓手[：:]\*\*\s*(.+)', raw)
            if not grasp_match:
                grasp_match = re.search(r'(?:记忆|背诵)抓手[：:]\s*(.+)', raw)
            if grasp_match:
                result["one_liner"] = clean_text(raw[:grasp_match.start()].strip())
            else:
                result["one_liner"] = clean_text(raw)
            break

    # 简单回答（匹配 **简单回答** 或 ### 简单回答）
    m = re.search(r'(?:\*\*|###\s+)?简单回答(?:\*\*)?\s*\n+(.+?)(?=\n(?:###|\*\*详细解释|\*\*详细解答|\*\*面试|####)|\Z)', body, re.DOTALL)
    if m:
        result["simple_answer"] = clean_text(m.group(1))

    # 面试时可以这样答
    m = re.search(
        r'(?:\*\*|###\s+)?面试时可以这样答(?:\*\*)?\s*\n+(.+?)(?=\n(?:###\s|####\s|##\s|\*\*详细解释|\*\*延展|\*\*结合项目|---\n)|\Z)',
        body, re.DOTALL
    )
    if m:
        result["interview_answer"] = clean_text(m.group(1))

    # 兜底：解释 / 答案 或 解释/答案
    if not result["simple_answer"] and not result["interview_answer"]:
        m = re.search(
            r'\*\*解释\s*/\s*答案[：:]\*\*\s*\n+(.+?)(?=\n(?:####\s+结合|###\s+\*\*|##\s|\*\*面试速记|---\n)|\Z)',
            body, re.DOTALL
        )
        if m:
            result["simple_answer"] = clean_text(m.group(1))

    # 结合项目回答
    m = re.search(
        r'(?:####\s+)?结合项目回答[（(]面试版[）)]\s*\n+(.+?)(?=\n(?:##\s|###\s\w)|\Z)',
        body, re.DOTALL
    )
    if m:
        result["project_answer"] = clean_text(m.group(1))

    return result


def clean_text(text: str) -> str:
    """清理提取文本中的格式残留。"""
    if not text:
        return text
    # 移除 **：** 或 **:** 或 **： 等格式残留
    text = re.sub(r'\*\*[：:]\*?\*?\s*', '', text)
    # 移除开头多余的 ：
    text = re.sub(r'^[：:]\s*', '', text)
    # 移除开头多余的 "
    text = re.sub(r'^"', '', text)
    # 移除 "详见xxx" 引用
    text = re.sub(r'详见[^\s。，]*。?', '', text)
    text = re.sub(r'详见[^。\n]+', '', text)
    # 移除 "（来源：...）"
    text = re.sub(r'[（(]来源[：:][^)）]+[)）]', '', text)
    return text.strip()


def clean_answer(text: str) -> str:
    """对回答文本做额外清理。"""
    if not text:
        return text
    # 移除 "**真实面经补充**" 及其后续内容
    text = re.sub(r'\n?\*\*真实面经补充[：:]*\*\*.*', '', text, flags=re.DOTALL)
    # 移除末尾残留的"详见§xxx"格式引用
    text = re.sub(r'详见[§\d].*$', '', text)
    # 移除末尾残留的子章节标题（提取时边界未能正确截断的部分）
    text = re.sub(r'\n+\*\*[一二三四五六七八九十\d]+[、.][^*]*\*\*\s*$', '', text)
    text = re.sub(r'\n+\*\*[一二三四五六七八九十\d]+[)）][^*]*\*\*\s*$', '', text)
    # 移除末尾残留的"详细解答"/"延展问答"等
    text = re.sub(r'\n+详细解答\s*$', '', text)
    text = re.sub(r'\n+延展问答\s*$', '', text)
    # 确保回答不以冒号结尾（截断标识）
    text = re.sub(r'[：:]\s*$', '。', text)
    return text.strip()


def trim_text(text: str, max_len: int = 2000) -> str:
    """裁剪文本到合适长度，在段落边界截断。"""
    if len(text) <= max_len:
        return text
    cutoff = text[:max_len].rfind('\n\n')
    if cutoff > max_len // 2:
        return text[:cutoff]
    return text[:max_len] + "…"


def build_answer(q: dict) -> str:
    """构建简化版面试回答：只要核心要点 + 回答。"""
    parts = []
    ans = q["answers"]

    if ans["one_liner"]:
        parts.append(f"**核心要点：** {trim_text(ans['one_liner'], 500)}")

    if ans["simple_answer"]:
        parts.append(f"**回答：** {clean_answer(trim_text(ans['simple_answer'], 1500))}")
    elif ans["interview_answer"]:
        parts.append(f"**回答：** {clean_answer(trim_text(ans['interview_answer'], 1500))}")

    return "\n\n".join(parts)


def normalize_title(title: str) -> str:
    t = title.strip()
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[?？!！。，,、]', '', t)
    return t.lower()


def main():
    all_questions = []
    for src_dir in SRC_DIRS:
        src_name = os.path.basename(src_dir)
        for f in sorted(Path(src_dir).glob("*.md")):
            if f.name.startswith("."):
                continue
            qs = extract_questions_from_file(str(f))
            dup_n = sum(1 for q in qs if q["is_dup"])
            print(f"📄 {f.name}: {len(qs)} 题 (📎重复:{dup_n})")
            all_questions.extend(qs)

    print(f"\n📊 总共提取: {len(all_questions)} 题")

    # 去重：跳过有 📎 标记的
    unique = [q for q in all_questions if not q["is_dup"]]
    skipped = len(all_questions) - len(unique)
    print(f"✅ 跳过 📎 重复: {skipped} 题")

    # 标题二次去重
    seen = {}
    final = []
    title_dup = 0
    for q in unique:
        key = normalize_title(q["title"])
        if key in seen:
            title_dup += 1
            existing = seen[key]
            if q["importance"] == "S" and existing["importance"] != "S":
                final.remove(existing)
                final.append(q)
                seen[key] = q
            continue
        seen[key] = q
        final.append(q)
    if title_dup > 0:
        print(f"✅ 标题去重: {title_dup} 题")

    print(f"📊 最终: {len(final)} 题")

    # 分类
    cat_map = {
        "01_RAG核心链路": "RAG核心链路", "02_RAG": "RAG核心链路",
        "02_Agent核心原理": "Agent核心原理", "01_Agent": "Agent核心原理",
        "03_大模型应用工程化": "大模型应用工程化", "03_工程化与系统设计": "大模型应用工程化",
        "04_项目面试与场景题": "项目面试与场景题", "05_项目面试与场景题": "项目面试与场景题",
        "05_必要的大模型基础": "大模型基础", "06_大模型基础": "大模型基础",
        "04_提示工程": "提示工程",
    }

    groups = OrderedDict()
    for q in final:
        cat = q["source_file"].replace(".md", "")
        name = cat_map.get(cat, cat)
        groups.setdefault(name, []).append(q)

    # 清空输出目录
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.md"):
        if old.name != "extract_questions.py":
            old.unlink()

    total = 0
    for i, (gname, qs) in enumerate(groups.items(), 1):
        fname = f"{i:02d}_{gname}.md"
        lines = [f"# {gname}\n"]
        for j, q in enumerate(qs, 1):
            lines.append(f"## {j}. {q['title']} [重要性:{q['importance']}]")
            lines.append("")
            lines.append(build_answer(q))
            lines.append("")
            lines.append("---")
            lines.append("")
        (OUT_DIR / fname).write_text("\n".join(lines), encoding="utf-8")
        print(f"✍️  {fname}: {len(qs)} 题")
        total += len(qs)

    # 统计报告
    report = [
        "# 面试题提取报告\n",
        f"## 统计",
        f"- 原始题目数: {len(all_questions)}",
        f"- 📎 标记重复跳过: {skipped}",
        f"- 标题去重: {title_dup}",
        f"- 最终题目数: **{total}**",
        f"- 输出文件数: {len(groups)}",
        "",
        "## 分类",
    ]
    for gname, qs in groups.items():
        s_n = sum(1 for q in qs if q["importance"] == "S")
        a_n = sum(1 for q in qs if q["importance"] == "A")
        report.append(f"- **{gname}**: {len(qs)} 题 (S:{s_n}, A:{a_n})")
    report.append(f"\n## 输出\n{OUT_DIR}")
    (OUT_DIR / "00_提取报告.md").write_text("\n".join(report), encoding="utf-8")

    print(f"\n🎉 完成！共 {total} 题 → {OUT_DIR}")


if __name__ == "__main__":
    main()
