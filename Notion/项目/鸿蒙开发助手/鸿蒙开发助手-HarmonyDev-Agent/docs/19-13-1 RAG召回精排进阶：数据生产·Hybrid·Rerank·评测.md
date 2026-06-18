# 13-1 RAG召回精排进阶：数据生产·Hybrid·Rerank·评测

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 把第 13 章「最小可用」的 RAG 链路推到「上线敢推」的工程档位：补齐数据生产、Hybrid 调参、Rerank 精排、召回评测四个真正决定上限的环节。

- 学会用一份完整的 OpenSearch `search_pipeline` 配置做权重调参，并清楚什么时候把 BM25 权重降到接近 0。

- 在召回链路上增加 cross-encoder Rerank，把 Recall@8 从 0.6 档拉到 0.8 档。

- 搭一套最小召回评测脚手架（30-50 条标注集 + Recall@K / MRR / NDCG），让 APIInsight 每次升级都有客观刹车。

**阅读重点：** 这一章是第 13 章的"工程化补丁"。如果只看最小可运行链路，第 13 章已经够了。但如果你要把 APIInsight 真的接到线上、还要持续优化，下面四节才是关键约束。看代码时把第 13 章 §3 和 §5 打开对照——本章基本上是在那两节的位置上贴补丁。

---

## 1、本章导读

### 1.1 第 13 章为什么"轻"

第 13 章把链路跑通的代价是把 RAG 的几个深水区"打了占位符"：

| 第 13 章的处理 | 真实工程里的隐患 |
| --- | --- |
| 卡片"假定已有" | 卡片质量决定召回上限，没有数据生产管线就等于在空气上建房子 |
| `search_pipeline` 只给名字 | normalization / compat_weights 没给，跑起来不知道权重是否合理 |
| 粗排出来直接进提炼 | Top-K 里夹了 1-2 张完全不相关的卡片，提炼出的 insight 就跑偏 |
| 提炼后就交给主 loop | 升级一版召回不知道有没有变好——可能 case-by-case 是好的，整体倒退 |

这四件事，对应本章四节主线。

### 1.2 本章节奏

```
节 1 数据生产管线        → 让卡片"够用"
节 2 完整 Hybrid DSL 调参 → 让粗排"够准"
节 3 Rerank 精排（浅档）  → 让 Top-K"够干净"
节 4 召回评测脚手架       → 让每次升级"有刹车"
节 5 工程建议列表（收尾）     → 多语言 / 冷启动 / 兜底 / 成本，一句话各表
```

---

## 2、数据生产管线：让卡片本身够好

### 2.1 数据从哪来

HarmonyDev 知识库的三类卡片（常用方案 / 能力图谱 / 方案复杂度区间）背后是四路原始数据：

| 数据源 | 喂给哪类卡片 | 频率 |
| --- | --- | --- |
| 官方示例工程与历史采纳日志 | API 文档卡片 | 周 |
| 官方文档变更列表 | API 文档卡片 | 周 |
| API 知识库约束聚合 | 能力图谱卡片 | 月 |
| 历史采纳复杂度分位 | 方案复杂度区间卡片 | 月 |

四路数据在原始形态上完全不同（CSV / API / 数仓查询 / 文档抓取 / 仓库扫描），不能直接灌进 OpenSearch。中间需要一段离线 ETL 把它们都收敛成 `InsightCard` 这一种结构。

### 2.2 ETL 的三步

```
原始数据
  -> Step 1: 标准化（字段统一、Kit 领域名归一）
  -> Step 2: 小模型抽取（生成 summary + raw_evidence）
  -> Step 3: 入库门禁（confidence 可信度 + 抽审）
  -> InsightCard 写入 OpenSearch
```

### 2.3 Step 1：字段标准化

四路数据的第一个公分母——**Kit 领域名归一**。"页面状态保存" / "ArkUI 状态管理问题" / "页面返回状态恢复" 在不同源里写法不一，但它们对应的卡片应该指向同一个Kit 领域。

```python
# app/recall/category_norm.py
CATEGORY_ALIASES: dict[str, str] = {
    "页面状态保存":      "ArkUI 状态管理问题",
    "页面返回状态恢复":    "ArkUI 状态管理问题",
    "页面状态恢复方案":    "ArkUI 状态管理问题",
    "Ability 跳转":        "Ability 跳转",
    "页面路由跳转":    "Ability 跳转",
    # ...离线靠人工 + API/代码片段图谱维护，规模一般在几百条
}

def normalize_category(raw: str) -> str:
    raw = raw.strip().lower()
    return CATEGORY_ALIASES.get(raw, raw)
```

归一表自己不是"自动产生"的——是API/代码片段运营 + 数据团队共维护的一张表。**HarmonyDev 的工程边界把它当 ground truth，不让 LLM 现场猜**。

### 2.4 Step 2：小模型抽取生成 summary

`InsightCard.summary` 的写法是有约定的（第 13 章 §5.3 的规则提炼就靠这种约定才能解析）。让小模型按约定生成：

```python
# scripts/etl/extract_card.py
from app.agent.llm import get_judge_llm   # 同 judge 共用强模型

EXTRACT_PROMPT = """
你是 HarmonyDev Kit 领域知识库的卡片抽取器。

输入：一段关于 Kit 能力域 {category} 的原始资料（官方文档 / 示例工程 / API 知识库聚合）。
输出：一张严格按格式写的 InsightCard.summary。

约定格式（任选一种，根据 card_type）：
  common_pattern: "{{category}}：{{方案1}} / {{方案2}} / {{方案3}}"
  attribute:   "API 约束：AppStorage 60% / LocalStorage 25% / @Provide/@Consume 15%"
  complexity_range: "轻量方案 0-2 / 中等改造 2-4 / 架构改造 4+ 常见跨模块重构"

raw_evidence 字段额外输出 1-3 条原始文本，每条不超过 80 字。
confidence: 0-1 之间，基于"原始数据量"和"措辞确定性"自评。

只输出 JSON，不要解释。
"""

async def extract_card(category: str, raw_text: str, card_type: str) -> dict:
    llm = get_judge_llm()
    resp = await llm.ainvoke([
        ("system", EXTRACT_PROMPT.format(category=category)),
        ("user", f"card_type={card_type}\n\n资料：\n{raw_text}"),
    ])
    import json
    return json.loads(resp.content)
```

抽取后立刻按约定格式做一次校验——格式错的直接 reject、不进入下一步。**让小模型为后续规则提炼负责，而不是让规则提炼为小模型的"自由发挥"擦屁股**。

### 2.5 Step 3：入库门禁

不是抽出来就能进库。三道门禁串行：

```python
# scripts/etl/admit.py
from pydantic import ValidationError
from app.recall.category_kb import InsightCard

MIN_CONFIDENCE = 0.5
MAX_SUMMARY_LEN = 200
SAMPLE_AUDIT_RATIO = 0.1   # 10% 的卡片走人工抽审

def admit(raw: dict) -> tuple[bool, str]:
    # 门 1：schema 严格校验
    try:
        card = InsightCard(**raw)
    except ValidationError as e:
        return False, f"schema 校验失败: {e}"

    # 门 2：confidence + 长度
    if card.confidence < MIN_CONFIDENCE:
        return False, f"confidence {card.confidence} < {MIN_CONFIDENCE}"
    if len(card.summary) > MAX_SUMMARY_LEN:
        return False, f"summary 超长 {len(card.summary)}"

    # 门 3：summary 格式约定校验
    if card.card_type == "common_pattern" and "：" not in card.summary:
        return False, "common_pattern summary 缺少 Kit 能力域前缀"
    if card.card_type == "attribute" and "%" not in card.summary:
        return False, "attribute summary 缺少百分比"

    return True, "ok"
```

10% 的卡片同时进人工抽审队列——抽审是离线异步的，主流程不阻塞。

### 2.6 数据生产的产出

跑一轮全量 ETL 大致是这样：

| 阶段 | 数量级 |
| --- | --- |
| 原始资料 | ~50000 段 |
| 标准化通过 | ~32000 段 |
| 抽取产出 | ~28000 张草卡 |
| 门禁通过 | ~21000 张 |
| 实际入库 | ~21000 张 |
| 人工抽审 | ~2100 张 |

后面第 4 节的召回评测，用的就是从抽审里挑出来的高质量样本。

---

## 3、完整 Hybrid DSL 与权重调参

### 3.1 search_pipeline 完整配置

第 13 章 §5.2 的代码里有这么一行：

```python
params={"search_pipeline": "globex_hybrid_pipeline"},
```

`globex_hybrid_pipeline` 长什么样？这一节给完整 JSON。

```bash
# 一次性注册到 OpenSearch（开发期可以放 scripts/setup_pipeline.sh）
PUT _search/pipeline/globex_hybrid_pipeline
{
  "description": "KNN + BM25 双路召回的归一与加权融合",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": { "technique": "min_max" },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": { "compat_weights": [0.7, 0.3] }
        }
      }
    }
  ]
}
```

三个关键配置：

| 字段 | 含义 |
| --- | --- |
| `normalization=min_max` | KNN 余弦分（-1~1）和 BM25 分（0~30+）量纲完全不同，先各自归一到 [0, 1] |
| `combination=arithmetic_mean` | 算数平均（简单稳定，比 RRF 在小知识库上更可控） |
| `compat_weights=[0.7, 0.3]` | KNN 权重 0.7、BM25 权重 0.3 |

`compat_weights` 数组的顺序对应第 13 章 §5.2 `body["query"]["hybrid"]["queries"]` 数组的顺序——**子路顺序和权重顺序必须一一对应，否则会调反**。

### 3.2 权重调参的经验取值

`compat_weights=[0.7, 0.3]` 不是拍出来的，是按 Kit 能力域 query 的形态分档调出来的：

| Kit 能力域 query 形态 | 推荐 compat_weights[KNN, BM25] | 原因 |
| --- | --- | --- |
| 名词为主（"Ability 跳转"/"LocalStorage"） | [0.5, 0.5] | 字面匹配本来就够准，BM25 不弱 |
| 偏约束约束（"跨页面共享ArkUI 状态管理问题"） | [0.7, 0.3] | KNN 撑语义，BM25 兜字面长尾 |
| 偏现象描述（"页面切回来数据没了"） | [0.9, 0.1] | 现象描述 BM25 几乎命不中，主要靠语义 |
| 完全口语（"返回上一页怎么数据都没了"） | [1.0, 0.0] | 关掉 BM25 子路，纯 KNN |

HarmonyDev 在 v1 默认 [0.7, 0.3]——覆盖最常见的"Kit 领域 + 约束"形态。要做按 query 形态自适应权重，可以在主 loop Think 阶段判断 query 类型，调用时通过 `search_pipeline?compat_weights=...` 临时覆盖。

### 3.3 什么时候关掉 BM25 子路

不是改权重为 0 那么粗暴。**完全语义化的 query**（如 "页面切回来数据没了"）下，BM25 子路返回的可能只是 "页面 / 数据" 这类字面命中的杂项卡片，反而把 KNN 准命中的"LocalStorage 页面状态保存"卡片挤出 Top-K。

更稳的做法是**判定型分支**：

```python
# app/tools/api_insight.py 召回前的预判
SEMANTIC_TOKENS = {"状态丢失", "生命周期", "废弃 api", "兼容", "api level", "targetsdkversion", "stage 模型", "低改动"}

def should_disable_bm25(category: str) -> bool:
    """Kit 领域 query 含弱字面匹配特征，关掉 BM25 子路。"""
    normalized = category.lower()
    return any(t in normalized for t in SEMANTIC_TOKENS)
```

在第 13 章 §5.2 的 `body` 构造里，根据这个判定决定是否塞入 BM25 子路即可。

---

## 4、Rerank 精排：补上 RAG 的"最后一公里"

### 4.1 为什么粗排到此还不够

第 13 章直接把 Hybrid 召回的 Top-8 喂给提炼。但实践里 Top-8 经常夹着 1-2 张"相关但跑题"的卡片——比如查"ArkUI 状态管理问题"，召回里混进一张"页面状态ArkUI 状态管理方案"的约束卡（它命中"页面状态"但不是套装）。提炼步是规则解析，混进来的杂卡会让 `components` 字段出现错位。

解决办法是**用 cross-encoder 在 Top-30 上做精排，再取 Top-8**。

双塔模型（问题意图塔 + API 文档塔）是 "你算你的、我算我的、最后比相似度"，没有交叉特征；cross-encoder 是 query 和候选**拼接进同一个模型**，对相关性判断更细。代价是慢得多——所以前者做粗排（百级候选），后者做精排（个位数候选）。

### 4.2 模型选型

| 候选 | 优点 | 缺点 | 推荐场景 |
| --- | --- | --- | --- |
| `BGE-Reranker-v2-m3` | 开源 / 多语言 / 性能稳 | 需要本地或自建服务 | HarmonyDev 默认 ✅ |
| `Cohere Rerank v3` | API 即用 / 多语言强 | 付费 / 数据出境 | 个人项目 / 早期 demo |
| LLM-as-Reranker（小模型） | 灵活、可解释 | 慢 + 贵 | 扩展方向，本章不展开 |

本章按 **BGE-Reranker-v2-m3 + 本地服务** 实现。它支持中英多语言，对鸿蒙开发 query 友好。

### 4.3 Reranker 客户端

```python
# app/recall/reranker.py
import os
import httpx
from typing import Sequence

class RerankerClient:
    """BGE-Reranker-v2-m3 的极简客户端。

    要求服务端暴露 /rerank：
      入参 {query: str, candidates: list[str]}
      出参 {scores: list[float]}  与 candidates 同序
    """

    def __init__(self) -> None:
        self.endpoint = os.environ["RERANKER_ENDPOINT"]
        self._client = httpx.AsyncClient(timeout=3.0)

    async def score(self, query: str, candidates: Sequence[str]) -> list[float]:
        r = await self._client.post(
            self.endpoint,
            json={"query": query, "candidates": list(candidates)},
        )
        r.raise_for_status()
        return r.json()["scores"]

reranker = RerankerClient()
```

### 4.4 接进 _recall_cards

第 13 章 §5.2 的 `_recall_cards` 内部，Top-K=8。这里改成"粗排 30、精排 8"：

```python
# app/tools/api_insight.py（替换原 _recall_cards）
COARSE_K = 30          # Hybrid 召回粗排
FINE_K_QUICK = 8       # depth=quick 时精排后保留
FINE_K_DEEP = 15       # depth=deep 时精排后保留
RERANK_BYPASS_TOP_SCORE = 0.92   # 粗排首位置分高于此值则跳过 rerank

async def _recall_cards(category: str, top_k: int) -> list[InsightCard]:
    emb = await tower_client.encode_query(category)

    body = _build_hybrid_body(category, emb, coarse_k=COARSE_K)
    resp = _kb_client.search(
        index=INDEX_NAME,
        body=body,
        params={"search_pipeline": "globex_hybrid_pipeline"},
    )
    hits = resp["hits"]["hits"]
    if not hits:

        return [ ]

    # 短路 1：粗排首位置置信度足够高，跳过 rerank 省 50ms
    if hits[0]["_score"] >= RERANK_BYPASS_TOP_SCORE:
        return [InsightCard(**h["_source"]) for h in hits[:top_k]]

    # 短路 2：粗排只有少量结果，直接返
    if len(hits) <= top_k:
        return [InsightCard(**h["_source"]) for h in hits]

    # 精排：query × candidates summary 做 cross-encoder 打分
    candidates_text = [h["_source"]["summary"] for h in hits]
    scores = await reranker.score(category, candidates_text)
    paired = sorted(zip(scores, hits), key=lambda x: x[0], reverse=True)
    return [InsightCard(**h["_source"]) for _, h in paired[:top_k]]
```

注意两个"短路"——**rerank 不是无脑加，是按需要才走**：

| 短路条件 | 意义 |
| --- | --- |
| 粗排首位置分高于阈值 | 粗排已经非常确定，rerank 没增量 |
| 粗排候选 ≤ Top-K | 没排序压力，rerank 没增量 |

### 4.5 加入 rerank 后的实测变化

| 指标 | 仅 Hybrid 粗排 | 粗排 + Rerank | 备注 |
| --- | --- | --- | --- |
| Recall@8 | ~0.62 | ~0.81 | 主要收益来源 |
| MRR | ~0.55 | ~0.74 | 第一条卡片更"对" |
| 单次延迟 P50 | ~25 ms | ~75 ms | rerank 一次 ~50 ms |
| 单次延迟 P99 | ~80 ms | ~140 ms | 短路命中率约 30% |

P50 +50ms 在 RAG 子链路里完全可接受，主 loop 那一轮 Think 本来就要花几百毫秒。

---

## 5、召回评测脚手架：让升级有刹车

### 5.1 评测放在哪一层

HarmonyDev 已经有第 8 章的 Rubric 端到端评测。**召回评测不是替代它，是补它的盲区**：

| 评测类型 | 关心什么 | 跑得起 / 用什么标注 |
| --- | --- | --- |
| Rubric（第 8 章） | 端到端修复方案建议列表质量 | 慢、贵、需要 judge LLM |
| 召回评测（本节） | APIInsight 单点 | 快、低成本、纯结构化指标 |

APIInsight 改了一行代码、调了一次 compat_weights、换了一版 reranker——这些变更不该每次都走 Rubric。**召回评测是模块级的"日常体检"**。

### 5.2 标注集长什么样

不需要几千条。HarmonyDev 在 v1 准备的标注集：

```
- 50 条典型Kit 领域 query（覆盖名词类 / 约束类 / 症状描述类 / 口语类四种形态）
- 每条 query 由API/代码片段运营人工挑选"应该被召回"的 5 张 InsightCard（按重要性排序）
- 这 250 个 (query, card_id) 对就是 ground truth
```

存储格式：

```json
// data/eval/category_recall.jsonl
{"query": "ArkUI 状态管理问题", "relevant": ["c_001", "c_017", "c_042", "c_088", "c_101"]}
{"query": "页面切回来数据没了", "relevant": ["c_220", "c_233", "c_251", "c_268", "c_271"]}
```

每行一条，方便增量补标。

### 5.3 三个核心指标

```python
# app/eval/recall_metrics.py
from typing import Sequence

def recall_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int) -> float:
    """Top-K 召回里覆盖了多少标注。"""
    top_k = set(retrieved[:k])
    rel = set(relevant)
    if not rel:
        return 0.0
    return len(top_k & rel) / len(rel)

def mrr(retrieved: Sequence[str], relevant: Sequence[str]) -> float:
    """首条相关卡片的倒数排名。"""
    rel = set(relevant)
    for i, rid in enumerate(retrieved, start=1):
        if rid in rel:
            return 1.0 / i
    return 0.0

def ndcg_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int) -> float:
    """NDCG@K：考虑位置 + 标注序的 gain。"""
    import math
    rel_rank = {rid: len(relevant) - i for i, rid in enumerate(relevant)}
    dcg = sum(
        rel_rank.get(rid, 0) / math.log2(i + 2)
        for i, rid in enumerate(retrieved[:k])
    )
    ideal = sum(
        rel_rank[rid] / math.log2(i + 2)
        for i, rid in enumerate(relevant[:k])
    )
    return dcg / ideal if ideal else 0.0
```

三者各自关心一件事：

| 指标 | 关心 | 什么时候它最重要 |
| --- | --- | --- |
| Recall@K | 标注的卡片是否被找回来 | 任何召回环节的"底线" |
| MRR | 首条命中的位置 | Top-1 直接影响 PatchPicker 时 |
| NDCG@K | 排序质量 | 不只看是否命中，还看高质量卡片是否靠前 |

### 5.4 跑测脚本

```python
# scripts/eval/run_category_recall.py
import asyncio
import json
from pathlib import Path
from app.tools.api_insight import _recall_cards
from app.eval.recall_metrics import recall_at_k, mrr, ndcg_at_k

EVAL_PATH = Path("data/eval/category_recall.jsonl")
TOP_K = 10

async def main():
    samples = [json.loads(l) for l in EVAL_PATH.open(encoding="utf-8")]
    recall_sum = mrr_sum = ndcg_sum = 0.0

    for s in samples:
        cards = await _recall_cards(s["query"], top_k=TOP_K)
        retrieved = [c.card_id for c in cards]
        recall_sum += recall_at_k(retrieved, s["relevant"], TOP_K)
        mrr_sum += mrr(retrieved, s["relevant"])
        ndcg_sum += ndcg_at_k(retrieved, s["relevant"], TOP_K)

    n = len(samples)
    print(f"Recall@{TOP_K} = {recall_sum / n:.3f}")
    print(f"MRR          = {mrr_sum / n:.3f}")
    print(f"NDCG@{TOP_K}   = {ndcg_sum / n:.3f}")

if __name__ == "__main__":
    asyncio.run(main())
```

跑一次 50 条标注的全量 ~5 秒（含 rerank），完全适合 CI 上常驻。

### 5.5 回归门禁

把这套指标接进发版流程：

| 门禁档位 | 阈值（HarmonyDev v1） | 触发后处理 |
| --- | --- | --- |
| Recall@10 | ≥ 0.75 | 低于阻断发版 |
| MRR | ≥ 0.65 | 低于阻断发版 |
| NDCG@10 | ≥ 0.70 | 低于告警 + 评审是否发版 |

任何对 compat_weights / coarse_k / rerank 阈值的修改，都要先跑一次本地评测、过门禁，再合代码。

---

## 6、收尾工程建议列表

最后这些不展开成大节，但都要心里有数。

### 6.1 多语言对齐

鸿蒙开发天然涉及多语种 query。两种工程路径：

| 路径 | 优点 | 缺点 | 推荐 |
| --- | --- | --- | --- |
| query 翻译归一到中文索引 | 索引成本低 / 维护轻 | 翻译失真 / 长尾词丢 | HarmonyDev 默认 ✅ |
| 多语言并行建索引（中 + 英 + ...） | 召回更准 / 不丢长尾 | 索引膨胀 N 倍 / 维护重 | 业务到一定规模再上 |

翻译归一可以放在 `_recall_cards` 入口前——非中文 query 先调一次 问题意图塔的多语言版本归一到中文向量空间，再走 Hybrid。

### 6.2 冷启动：新Kit 领域无卡片

新 Kit 能力域（如刚发布的新 Kit 或新 API）知识库还没卡片。`_recall_cards` 拿不到任何 hit。退化策略：

```
1. Recall 命中 0 -> 主 loop 收到空 insight
2. 主 loop 在 Think 阶段判断 components/common_patterns 全空 -> 调一次 WebSearch 兜底
3. WebSearch 结果用同样的小模型抽成草卡（不入库，仅本轮使用）
```

入库由离线 ETL 负责，**不让在线工具污染知识库**——这是入库门禁的初衷。

### 6.3 query 级缓存

同一个 category 几小时内被反复查（如同一用户在同一会话里多次提到"ArkUI 状态管理问题"），不需要每次都走 Hybrid + Rerank。Redis 加一层薄薄的 cache：

```python
# 伪代码
cache_key = f"cinsight:{category}:{depth}"
cached = await redis.get(cache_key)
if cached:
    return APIInsightOutput.model_validate_json(cached)
# ... 正常召回 ...
await redis.setex(cache_key, 3600, result.model_dump_json())
```

3600s TTL 适配"卡片每周/每月刷新"的业务节奏。

### 6.4 异常 / 空召回兜底

| 异常类型 | 兜底 |
| --- | --- |
| OpenSearch 不可用 | 返回 confidence=0 的空 insight + 上报 |
| Reranker 超时 | 跳过精排，直接用粗排 Top-K（已有兜底） |
| Tower 不可用 | 退化到纯 BM25 查询（仅 BM25 子路） |
| 召回空 | 同 §6.2 走 WebSearch |

所有兜底**不抛异常**——给主 loop 一个"低置信度"的结构化结果，让它自己决定下一步（比如调 WebSearch 或直接 ChatFallback 与用户对齐）。

### 6.5 工程指标看板

最终上线时应在监控里跑这些指标：

| 指标 | 期望值（HarmonyDev v1） |
| --- | --- |
| Recall@10 | ≥ 0.75 |
| 单次 P50 延迟 | ≤ 80 ms |
| 单次 P99 延迟 | ≤ 200 ms |
| Rerank 短路命中率 | ≥ 25% |
| 空召回率 | ≤ 2% |
| Cache 命中率 | ≥ 30% |

任意一项跌出 1.5σ，触发告警。

---

**本章小结：**

到这里，HarmonyDev 的 RAG 链路从"跑得通"升级到"上线敢推"：

- **数据生产管线**：标准化 → 小模型抽取 → 入库门禁三步，让卡片本身就是高质量结构化数据；

- **完整 Hybrid DSL**：`search_pipeline` 完整配置 + `[0.7, 0.3]` 权重 + 按 query 形态分档调参，必要时关掉 BM25 子路；

- **Rerank 精排**：BGE-Reranker-v2-m3 + 两条短路（首位置高分跳过 / 候选不足跳过），把 Recall@8 从 ~0.62 推到 ~0.81，代价仅 +50ms P50；

- **召回评测脚手架**：50 条人工标注 + Recall@K / MRR / NDCG 三指标 + 回归门禁，每次改动都有客观刹车；

- **收尾工程建议列表**：多语言归一 / 冷启动 WebSearch 兜底 / Redis cache / 全链路异常兜底 / 上线指标看板。

对照第 13 章的 `_recall_cards`，可以看出生产化版本需要补齐哪些环节——而第 13 章给的那一版只是它的脚手架。

下一章「[主 AgentLoop 组装与同质子 AgentLoop fork 协同机制](<20-14 主AgentLoop组装与同质子AgentLoop-fork协同机制.md>)」继续往下走，把 APIInsight 和前 13 章铺垫的所有工具组装成可运行的主 AgentLoop。
