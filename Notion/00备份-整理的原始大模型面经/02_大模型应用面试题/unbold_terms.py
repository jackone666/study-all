#!/usr/bin/env python3
"""
去掉之前添加的术语加粗，保留段落标签加粗。
"""
import re
from pathlib import Path

DIR = Path("/Users/zing/Desktop/Obsidian文件/面试准备/面试题")

# 需要去掉加粗的术语（与之前 bold_format.py 的 TECH_TERMS 一致）
TECH_TERMS = [
    'RAG', 'LLM', 'Agent', 'Workflow', 'ReAct', 'CoT',
    'Zero-shot', 'Few-shot', 'Chain-of-Thought', 'Self-Consistency',
    'Fine-tuning', 'SFT', 'RLHF', 'DPO',
    'Hallucination',
    'FlashAttention', 'KV Cache',
    'Embedding', 'BM25', 'Rerank', 'Recall@5', 'MRR',
    'LangChain', 'LangGraph', 'LlamaIndex',
    'Function Calling', 'Tool Calling',
    'Prompt Caching', 'Guardrails',
    'Plan-and-Execute', 'Reflexion',
    'MHA', 'MQA', 'GQA', 'MLA',
    'SSE', 'WebSocket',
    'OCR', 'Text-to-SQL',
    'LSTM', 'GRU', 'RNN', 'CNN',
]


def unbold_terms(text: str) -> str:
    """将 **术语** 恢复为 术语（不在代码块内）"""
    for term in TECH_TERMS:
        escaped = re.escape(term)
        # 匹配 **Term** 但不在更长的加粗片段内
        # 例如 **RAG** 但不匹配 **RAG 系统**
        pattern = rf'\*\*({escaped})\*\*(?!\*\*)'
        # 检查前面没有未闭合的 **
        text = re.sub(pattern, r'\1', text)
    return text


def process_file(filepath: Path) -> int:
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_code_block = False
    changes = 0
    new_lines = []

    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue
        if in_code_block:
            new_lines.append(line)
            continue
        # 跳过标题行、表格行
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('|'):
            new_lines.append(line)
            continue

        original = line
        line = unbold_terms(line)
        if line != original:
            changes += 1
        new_lines.append(line)

    result = "\n".join(new_lines)
    filepath.write_text(result, encoding="utf-8")
    return changes


def main():
    md_files = sorted(DIR.glob("*.md"))
    total = 0
    for fp in md_files:
        n = process_file(fp)
        total += n
        print(f"  {fp.name}: {n} 行修改")
    print(f"总计: {total} 行修改")


if __name__ == "__main__":
    main()
