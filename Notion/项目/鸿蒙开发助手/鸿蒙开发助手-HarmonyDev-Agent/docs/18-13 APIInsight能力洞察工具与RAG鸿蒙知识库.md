# 13 APIInsight Kit 能力洞察工具与RAG鸿蒙知识库

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 理解 APIInsight 在 HarmonyDev 链路里的"前置认知层"定位——不是检索API/代码片段，而是给后面所有工具提供"这个Kit 领域长什么样"的常识。

- 第一次接 RAG 鸿蒙知识库：从知识库构建 → 检索 → 结构化输出整条管线。

- 看懂为什么 APIInsight 是 fork 三件事里"调用链 ≥ 3"的合理候选——它内部要做"常用方案 → 约束 → 方案复杂度区间"三跳。

- 理解 RAG 不是简单"向量检索"，而是"召回 + 提炼 + 摘要"三步，给模型的是结论不是原文。

**阅读重点：** 这一章的工程难度是 9 个工具里相对低的，但**业务设计上很关键**——APIInsight 决定了 PatchPicker 二次筛选时是否懂行。看代码时关注 RAG 检索后**怎么把原文压成结构化 insight**，而不是把 5 篇文档原封不动塞回模型。

---

## 1、本章导读

### 1.1 没有 APIInsight 会发生什么

回想第 12 章结束的状态：主 loop 拿到 Top-N 个 CompatResult，准备喂给 PatchPicker 做二次筛选。

如果直接进 PatchPicker，模型只能基于 query 文本 + 候选约束表面字段做选择。会出现这种问题：

| 场景 | 没有Kit 能力常识时的失误 |
| --- | --- |
| 用户说"ArkUI 状态管理问题，不要使用废弃 API" | 不知道"ArkUI 状态管理问题"通常涉及哪些 API / 生命周期点，可能漏选 |
| 用户说"Ability 跳转后参数丢失" | 不知道这类场景常见于 want 参数、router 参数还是跨 Ability 数据共享 |
| 用户说"Stage 模型路由迁移" | 不知道这场景下Stage 模型路由 vs FA 模型迁移的使用差异 |

让模型"现场学Kit 领域知识"是不现实的——它的训练数据未必涉及这种垂类细节，而且每条 query 都现学一次代价巨大。

APIInsight 解决的就是：**把每个Kit 领域的"行家常识"提前沉淀成知识库，按需检索回来。**

### 1.2 本章先做什么，不做什么

要做的：

1. 设计 APIInsight 的工具签名：模型传Kit 领域，得到结构化 insight。

1. 构建一个最小可用的 RAG 鸿蒙知识库（API 文档卡片 / 能力图谱 / 方案复杂度区间）。

1. 实现"召回 → 提炼 → 摘要"三步链路，输出结构化的 `APIInsightOutput`。

1. 解释为什么 APIInsight 是"调用链 ≥ 3" 触发 fork 的典型场景。

不做的：

- 知识库的离线建设流水线（爬虫、清洗、定期更新）超出当前实现范围，本章给一个静态 JSONL + 向量索引的最小例子。

- PatchPicker 怎么消费这些 insight 留给第 14 章。

---

## 2、APIInsight 在工具链里的位置

### 2.1 它通常在 DocSearch 之前还是之后

**两种合理位置都存在**，看用户 query 形态：

| 用户 query 形态 | APIInsight 触发时机 |
| --- | --- |
| "想实现一套 ArkUI 状态管理方案，目标 HarmonyOS 5.0，不要使用废弃 API" | 在 DocSearch 之前——先弄清"组合方案"包含什么 |
| "我已经拿到这 12 条候选，哪几条最适合当前项目" | 在 PatchPicker 之前——补 Kit 能力常识用于筛选 |

第一种是 Planner 已经把Kit 领域拆出来了，主 loop 在 fork DocSearch 之前先调一次 APIInsight 拿到典型组件建议列表。第二种是 DocSearch 已经跑完，主 loop 在筛选之前补一次Kit 能力常识。

主 loop 通过 system prompt 自己学会判断什么时候调 APIInsight。

### 2.2 用三件事判断 fork 与否

| 条件 | APIInsight 内部 |
| --- | --- |
| 能并行 | ❌ 一次输入一次输出 |
| 上下文要隔离 | ⚠️ 中等——RAG 召回的 5-10 篇文档原文很大，不该污染主 loop |
| 调用链 ≥ 3 | ✅ 内部要"常用方案检索 → 约束提取 → 方案复杂度区间统计"三跳 |

满足后两个，**这是个值得 fork 的场景**——主 loop 调 task_tool，子 Agent 内部跑完 RAG + 提炼 + 摘要后，只回传压缩过的结构化 insight。

---

## 3、RAG 鸿蒙知识库的最小形态

### 3.1 知识库里放什么

不是把整个互联网的API 使用经验都灌进去。HarmonyDev 的知识库只放三类卡片：

| 卡片类型 | 内容样例 | 作用 |
| --- | --- | --- |
| API 文档卡片 | "ArkUI 状态管理问题：ArkUI 状态管理方案 / 路由返回处理 / LocalStorage 状态持久化" | 给 DocSearch 拆 sub-query |
| 能力图谱卡片 | "API 约束：AppStorage 60% / LocalStorage 25% / @Provide/@Consume 15%；跨页面共享占 70%" | 给 PatchPicker 判断典型约束 |
| 方案复杂度区间卡片 | "轻量方案 60-150 / 中等改造 150-400 / 架构改造 400+ 常见跨模块重构" | 给 PatchPicker 判断方案复杂度档位 |

每张卡片都是结构化的——不是把社区长帖整段灌进去。这一点和"通用 RAG"不一样。

### 3.2 知识库 schema

```python
# app/recall/category_kb.py
from pydantic import BaseModel
from typing import Literal

class InsightCard(BaseModel):
    card_id: str
    category: str                           # 标准化的 Kit 能力域名，如 "ArkUI 状态管理问题"
    card_type: Literal["common_pattern", "attribute", "complexity_range"]
    summary: str                            # 已经提炼好的一段结论
    raw_evidence: list[str]                 # 支撑这条结论的 1-3 段原始证据
    last_updated: str                       # ISO 时间戳
    confidence: float                       # 0-1 的置信度（来自数据 / 来自人工标注）
```

### 3.3 知识库灌库（极简版）

本节使用 `OpenSearch` 作为应用层向量库，主要原因是它能同时存 `knn_vector` + 元数据 + 全文检索字段，检索时可走 KNN + BM25 两路 Hybrid Query 打分融合。选型论证详见 [第 4-1 章 向量基础设施选型与 OpenSearch 演进方向](<08-04-1 向量基础设施选型与OpenSearch演进方向.md>)。

```python
# scripts/build_category_kb.py
import json
import os
from pathlib import Path

import httpx
from opensearchpy import OpenSearch, helpers

CARDS_PATH = Path("data/category_cards.jsonl")
INDEX_NAME = "globex_category_kb"
VECTOR_DIM = 1024   # 与 问题意图塔输出维度一致

client = OpenSearch(
    hosts=[{"host": os.environ["OPENSEARCH_HOST"], "port": 9200}],
    http_auth=(os.environ["OPENSEARCH_USER"], os.environ["OPENSEARCH_PASS"]),
    use_ssl=False,
)

# 同一份索引同时存：结构化字段 + 全文字段（ik 分词） + KNN 向量字段
INDEX_MAPPING = {
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "card_id":      {"type": "keyword"},
            "category":     {"type": "text", "analyzer": "ik_max_word"},
            "card_type":    {"type": "keyword"},
            "summary":      {"type": "text", "analyzer": "ik_max_word"},
            "raw_evidence": {"type": "text", "analyzer": "ik_max_word"},
            "last_updated": {"type": "date"},
            "confidence":   {"type": "float"},
            "content_vector": {
                "type": "knn_vector",
                "dimension": VECTOR_DIM,
                "method": {
                    "name":       "hnsw",
                    "engine":     "faiss",        # 底层 ANN 引擎
                    "space_type": "cosinesimil",  # 与 问题意图塔 cosine 一致
                },
            },
        }
    },
}

async def encode(text: str) -> list[float]:
    """复用 问题意图塔做 embedding（同模型避免分布偏移）。"""
    async with httpx.AsyncClient(timeout=5.0) as cli:
        r = await cli.post(
            os.environ["TOWER_QUERY_ENDPOINT"], json={"query": text},
        )
        r.raise_for_status()
        return r.json()["embedding"]

async def build():
    if not client.indices.exists(INDEX_NAME):
        client.indices.create(INDEX_NAME, body=INDEX_MAPPING)

    cards = [json.loads(l) for l in CARDS_PATH.open(encoding="utf-8")]

    actions = [ ]

    for c in cards:
        text = f"{c['category']} {c['card_type']} {c['summary']}"
        vec  = await encode(text)
        actions.append({
            "_index":  INDEX_NAME,
            "_id":     c["card_id"],
            "_source": {**c, "content_vector": vec},
        })

    helpers.bulk(client, actions)
    client.indices.refresh(INDEX_NAME)

if __name__ == "__main__":
    import asyncio
    asyncio.run(build())
```

这一步跳过了原来“独立 meta.json + Faiss 索引文件”的双文件维护：API 文档卡片的元数据、全文、向量都住在同一个 `OpenSearch` 文档里，检索时一句 `client.search(...)` 全拿回。知识库构建仍是离线流程，工具运行时只读该索引。

> 上面这段 ETL 是“能跑”版本。真实项目里“数据从哪来 / 怎么标准化 / 怎么过入库门禁”是另一条需要展开的链路，详见 [13-1 章 §2 数据生产管线](<19-13-1 RAG召回精排进阶：数据生产·Hybrid·Rerank·评测.md#_2、数据生产管线让卡片本身够好>)。

---

## 4、APIInsight 工具签名

```python
# app/tools/api_insight.py
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Literal

class CommonPattern(BaseModel):
    name: str
    complexity_score: float
    why_popular: str

class AttributeDist(BaseModel):
    name: str
    distribution: dict[str, float]    # {"AppStorage": 0.6, "LocalStorage": 0.25, ...}

class ComplexityTier(BaseModel):
    tier: Literal["simple", "medium", "complex"]
    complexity_range: tuple[float, float]
    notes: str

class APIInsightOutput(BaseModel):
    category: str
    components: list[str]              # 这个 Kit 能力域典型涉及哪些 API / 生命周期点
    common_patterns: list[CommonPattern]
    attributes: list[AttributeDist]
    complexity_tiers: list[ComplexityTier]
    confidence: float                  # 整体置信度

@tool
async def api_insight(category: str, depth: Literal["quick", "deep"] = "quick") -> APIInsightOutput:
    """获取一个Kit 领域的结构化常识：典型组件 / 常用方案 / 能力边界分布 / 方案复杂度档位。

    Args:
        category: 标准化Kit 领域名，例如 "ArkUI 状态管理问题" / "Ability 跳转" / "Stage 模型路由"。
        depth: quick 只查常用方案 + 实现成本档；deep 同时查能力图谱（更慢）。

    Returns:
        APIInsightOutput: 已经被压缩过的结构化常识，不含 RAG 原文。
    """
    ...
```

设计要点：

- `depth`** 控制深度**：让模型在不需要全部维度时省一次约束检索。

- **出参不带 **`raw_evidence`：所有原文证据在工具内部消化掉，给主 loop 的只有结论。这是"RAG 给结论不给原文"。

---

## 5、工具实现：召回 → 提炼 → 摘要

### 5.1 三步管线

```
1) 召回：用 category 在 OpenSearch 走 KNN + BM25 双路 Hybrid Query，得到 Top-K 张 InsightCard
2) 提炼：按 card_type 分组，对每组卡片做结构化提取
3) 摘要：把同一组的多张卡片合并成一个结构化字段
```

### 5.2 召回部分

```python
# app/tools/api_insight.py（续）
import os

from opensearchpy import OpenSearch
from app.api.monitor import monitor
from app.recall.towers import tower_client
from app.recall.category_kb import InsightCard

INDEX_NAME = "globex_category_kb"

_kb_client = OpenSearch(
    hosts=[{"host": os.environ["OPENSEARCH_HOST"], "port": 9200}],
    http_auth=(os.environ["OPENSEARCH_USER"], os.environ["OPENSEARCH_PASS"]),
    use_ssl=False,
)

async def _recall_cards(category: str, top_k: int) -> list[InsightCard]:
    """Hybrid 检索：KNN 向量召回 + BM25 全文匹配，引擎层加权融合。"""
    emb = await tower_client.encode_query(category)

    body = {
        "size": top_k,
        "query": {
            "hybrid": {
                "queries": [
                    # 子路 1：KNN 向量语义召回
                    {"knn": {"content_vector": {"vector": emb, "k": top_k * 3}}},
                    # 子路 2：BM25 中文全文匹配（category 字段权重 ×2）
                    {"multi_match": {
                        "query":   category,
                        "fields":  ["category^2", "summary"],
                        "analyzer": "ik_max_word",
                    }},
                ]
            }
        },
        # 不要把高维向量原样返回，减少带宽
        "_source": {"excludes": ["content_vector"]},
    }

    # search_pipeline 在 OpenSearch 端配：
    #   normalization=min_max, combination=arithmetic_mean, compat_weights=[0.7, 0.3]
    # 完整 DSL 参见第 4-1 章 §6 「OpenSearch Hybrid Query 最小配方」
    resp = _kb_client.search(
        index=INDEX_NAME,
        body=body,
        params={"search_pipeline": "globex_hybrid_pipeline"},
    )

    cards = [ ]

    for hit in resp["hits"]["hits"]:
        cards.append(InsightCard(**hit["_source"]))
    return cards
```

两个关键变化：

- **从单路 **`Faiss.search`** 变成双路 Hybrid Query**：在文本匹配能走清的 case（比如 `category="LocalStorage 页面状态保存"` 与卡片 `category` 字段几乎一致），补上 BM25 可以明显拉高 TopK 质量；语义偏离的 case 仍然靠 KNN 兜底。

- **不再需要 idx → meta.json 二级映射**：`hit["_source"]` 直接是完整的 `InsightCard` 数据，只需隔离掉 `content_vector` 有效载荷即可。

> 这里只给 search_pipeline 的名字，完整的 normalization / combination / compat_weights 配置与调参经验见 [13-1 章 §3 完整 Hybrid DSL 与权重调参](<19-13-1 RAG召回精排进阶：数据生产·Hybrid·Rerank·评测.md#_3、完整-hybrid-dsl-与权重调参>)。另外，粗排 Top-K 在进提炼之前还应走一次 cross-encoder rerank，主路实现与短路判定见 [13-1 章 §4 Rerank 精排](<19-13-1 RAG召回精排进阶：数据生产·Hybrid·Rerank·评测.md#_4、rerank-精排补上-rag-的最后一公里>)。

### 5.3 提炼部分

```python
def _split_by_type(cards: list[InsightCard]) -> dict[str, list[InsightCard]]:

    bag: dict[str, list[InsightCard]] = {"common_pattern": [ ], "attribute": [ ], "complexity_range": [ ]}

    for c in cards:

        bag.setdefault(c.card_type, [ ]).append(c)

    return bag

def _extract_components(pattern_cards: list[InsightCard]) -> list[str]:
    """从 API 文档卡片 summary 中提取典型 API / 生命周期点。"""
    found: set[str] = set()
    for c in pattern_cards:
        # InsightCard.summary 写法约定: "ArkUI 状态管理问题：ArkUI 状态管理方案 / 路由返回处理 / LocalStorage 状态持久化"
        if "：" in c.summary and "/" in c.summary:
            parts = c.summary.split("：", 1)[1]
            for token in parts.split("/"):
                token = token.strip()
                if token:
                    found.add(token)
    return sorted(found)

def _extract_common_patterns(cards: list[InsightCard]) -> list[CommonPattern]:

    out = [ ]

    for c in cards:
        # InsightCard 在灌库时已结构化（实际见 raw_evidence 里的抽取字段）
        evidences = c.raw_evidence
        if not evidences:
            continue
        # 极简：第一条证据按 "name | complexity_score | reason" 拆
        for line in evidences:
            try:
                name, complexity, reason = [s.strip() for s in line.split("|")]
                out.append(CommonPattern(
                    name=name, complexity_score=float(complexity), why_popular=reason,
                ))
            except ValueError:
                continue
    return out[:5]

def _extract_attributes(cards: list[InsightCard]) -> list[AttributeDist]:

    out: list[AttributeDist] = [ ]

    for c in cards:
        # InsightCard.summary: "API 约束：AppStorage 60% / LocalStorage 25% / @Provide/@Consume 15%"
        if "：" not in c.summary:
            continue
        attr_name, dist_str = c.summary.split("：", 1)
        dist: dict[str, float] = {}
        for token in dist_str.split("/"):
            token = token.strip()
            if not token:
                continue
            parts = token.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].endswith("%"):
                try:
                    dist[parts[0]] = float(parts[1].rstrip("%")) / 100
                except ValueError:
                    pass
        if dist:
            out.append(AttributeDist(name=attr_name.strip(), distribution=dist))
    return out

def _extract_complexity_tiers(cards: list[InsightCard]) -> list[ComplexityTier]:

    tiers = [ ]

    label_map = {"simple": "轻量方案", "medium": "中等改造", "complex": "架构改造"}
    for tier_key, label in label_map.items():
        for c in cards:
            if label in c.summary:
                # 简化：靠正则提一对数字区间
                import re
                m = re.search(r"(\d+)\s*[-—]\s*(\d+)", c.summary)
                if m:
                    tiers.append(ComplexityTier(
                        tier=tier_key,
                        complexity_range=(float(m.group(1)), float(m.group(2))),
                        notes=c.summary,
                    ))
                    break
    return tiers
```

实际项目里，提炼步通常会调一次小模型做"summary → JSON"的转换。本章用规则示意，方便看清结构化思路。

### 5.4 主体函数

```python
# app/tools/api_insight.py（续）
import time

@tool
async def api_insight(category: str, depth: Literal["quick", "deep"] = "quick") -> APIInsightOutput:
    """获取一个 Kit 能力域的结构化常识。"""
    await monitor.report_tool_start("api_insight", {
        "category": category, "depth": depth,
    })
    t0 = time.time()

    top_k = 8 if depth == "quick" else 15
    cards = await _recall_cards(category, top_k)
    grouped = _split_by_type(cards)

    components = _extract_components(grouped["common_pattern"])
    common_patterns = _extract_common_patterns(grouped["common_pattern"])
    complexity_tiers = _extract_complexity_tiers(grouped["complexity_range"])

    if depth == "deep":
        attributes = _extract_attributes(grouped["attribute"])
    else:

        attributes = [ ]

    confidence = (
        sum(c.confidence for c in cards) / len(cards) if cards else 0.0
    )

    await monitor.report_tool_end("api_insight", int((time.time() - t0) * 1000))
    return APIInsightOutput(
        category=category,
        components=components,
        common_patterns=common_patterns,
        attributes=attributes,
        complexity_tiers=complexity_tiers,
        confidence=round(confidence, 2),
    )
```

### 5.5 一个简单的调用示例

摸清输入输出最快的办法是脱离 Agent 上下文、手工调一下：

```python
# scripts/try_api_insight.py
import asyncio
from app.tools.api_insight import api_insight

async def main():
    # quick 模式：Top-K=8，不跑约束提炼
    result = await api_insight.ainvoke({
        "category": "ArkUI 状态管理问题",
        "depth": "quick",
    })
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

运行后会得到一个结构化的 `APIInsightOutput`（下面字段值为示意）：

```
APIInsightOutput(
    category="ArkUI 状态管理问题",
    components=["ArkUI 状态管理方案", "路由返回处理", "LocalStorage 状态持久化"],
    common_patterns=[
        CommonPattern(name="LocalStorage 页面级状态保存", complexity_score=2.1, why_popular="改动小，适合单页面返回恢复"),
        CommonPattern(name="AppStorage 全局状态方案",     complexity_score=2.8, why_popular="适合跨页面共享状态"),
        # ...共 3-5 条
    ],

    attributes=[ ],                       # quick 模式不返能力边界分布

    complexity_tiers=[
        ComplexityTier(tier="simple",  complexity_range=(0.0, 2.0), notes="轻量方案 0—2"),
        ComplexityTier(tier="medium",  complexity_range=(2.0, 4.0), notes="中等改造 2—4"),
        ComplexityTier(tier="complex", complexity_range=(4.0, 8.0), notes="架构改造 4+"),
    ],
    confidence=0.78,
)
```

把 `depth` 换成 `"deep"`，Top-K 会升到 15，额外跑一轮约束提炼，`attributes` 字段就会被填上：

```
attributes=[
    AttributeDist(name="API 约束", distribution={"AppStorage": 0.6, "LocalStorage": 0.25, "@Provide/@Consume": 0.15}),
    AttributeDist(name="容量", distribution={"小": 0.2, "中": 0.55, "大": 0.25}),
]
```

其它字段保持不变。`quick` / `deep` 的差异只在这一项上。

---

## 6、为什么是"调用链 ≥ 3"的 fork 候选

### 6.1 调用链拆解

APIInsight 内部三步：

```
Step 1: tower_client.encode_query(category)   → 1 次 RPC
Step 2: ann.search                            → 1 次本地检索
Step 3: 三组规则提炼（实际项目通常会上小模型）→ 1-3 次 LLM 调用
```

如果用小模型做提炼，**调用链长度直接 ≥ 3**。

### 6.2 fork 之后主 loop 看到什么

主 loop 调 `task_tool(demands="给我'ArkUI 状态管理问题'的Kit 能力常识")`，子 Agent 内部跑完三步管线，回传给主 loop 的字符串大概是这样的：

```
ArkUI 状态管理问题Kit 能力常识：
- 典型组件：ArkUI 状态管理方案 / 路由返回处理 / LocalStorage 状态持久化
- 常用方案 5 件：（建议列表）
- 方案复杂度档位：轻量方案 60-150 / 中等改造 150-400 / 架构改造 400+
- 数据置信度 0.78
```

主 loop 不需要看 5-15 张原始 InsightCard。它的上下文清爽得多——这就是"调用链 ≥ 3 + 上下文要隔离"两个条件叠加触发 fork 的最直接好处。

### 6.3 不 fork 行不行

也行。`api_insight` 作为普通工具直接被主 loop 调，把结构化结果（APIInsightOutput 已经压缩过原文）返回，对主 loop 上下文压力也不大。**fork 不是必须**——本章列出 fork 路径是为了让你看到这种判断在工程层是真的能落地的，不是只在第 3 章纸上谈兵。

实际部署时，`depth="deep"` 触发 fork，`depth="quick"` 主 loop 直接调，是个常见折衷。

---

## 7、和后续工具怎么协作

### 7.1 喂给 PatchPicker 的字段

第 14 章会讲 PatchPicker。这里先把"喂什么"约定好：

| PatchPicker 关心 | 来自 APIInsight 的哪个字段 |
| --- | --- |
| 方案是否覆盖必要 API 和状态边界 | `components` |
| 候选约束是否符合 Kit 能力域主流 | `attributes` 的 distribution 排前几位 |
| 候选实现成本是否落在合理档位 | `complexity_tiers` 的 complexity_range |
| 决策置信度 | `confidence`（低于 0.5 时主 loop 应再补 WebSearch） |

### 7.2 知识库刷新策略（说明性）

| 刷新类型 | 频率 | 数据源 |
| --- | --- | --- |
| API 文档卡片 | 每周 | 官方文档索引 + 社区 Issue 统计 |
| 能力图谱卡片 | 每月 | API 知识库约束聚合 |
| 方案复杂度区间卡片 | 每月 | 历史修复方案复杂度分位数 |

刷新流程不在工具运行时——是个独立的离线任务。刷新与上线间还需要一套兜底：召回评测（Recall@K / MRR / NDCG）、冷启动 WebSearch 兜底、多语言归一、索引别名切换等详见 [13-1 章 §5 评测脚手架](<19-13-1 RAG召回精排进阶：数据生产·Hybrid·Rerank·评测.md#_5、召回评测脚手架让升级有刹车>) 与 [§6 收尾工程建议列表](<19-13-1 RAG召回精排进阶：数据生产·Hybrid·Rerank·评测.md#_6、收尾工程建议列表>)。

---

**本章小结：**

到这里，APIInsight 已经把"行家常识"接到 Agent 链路里。现在你应该清楚：

- APIInsight 不是另一个搜索工具，它是**前置认知层**——给 DocSearch 拆 sub-query、给 PatchPicker 提供API 选型判断依据；

- RAG 鸿蒙知识库不放整篇社区长帖，只放结构化卡片：常用方案 / 能力图谱 / 方案复杂度区间；

- 工具内部走"召回 → 提炼 → 摘要"三步，给主 loop 的是结论而不是原文；

- 这个工具是 fork 三件事里"调用链 ≥ 3 + 上下文要隔离"两个条件叠加的典型场景，`depth="deep"` 时尤其适合 fork；

- APIInsight 输出的 api_set / constraints / version_notes / confidence 是 PatchPicker 二次筛选的判据。

下一章「[主 AgentLoop 组装与同质子 AgentLoop fork 协同机制](<20-14 主AgentLoop组装与同质子AgentLoop-fork协同机制.md>)」会真正把所有工具串起来：组装主 AgentLoop、收尾 PatchPicker / DevSummary、并交付一套防 fork 失控的工程兜底。
