# 04-1 向量基础设施选型与OpenSearch演进方向

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 看清 HarmonyDev 项目里 **三处向量需求** 的本质差异：API/代码片段召回、RAG 知识库、长期记忆 Store。

- 掌握"标量过滤"与"向量检索"结合的 **三种模式**：Pre-filtering / Post-filtering / Hybrid Fusion。

- 理解为什么 HarmonyDev 最终走 **召回层 Faiss + 应用层 OpenSearch** 的双栈分层方案。

- 看懂 `OpenSearch` 的 `Search Pipeline + Hybrid Query` 最小可运行配方，知道权重在引擎层是怎么调的。

**阅读重点：** 这一章是 [第 4 章](<07-04-0 鸿蒙开发助手三塔召回与工程语义.md>) 的"姊妹章"——第 4 章讲三塔模型本身，本章讲三塔训出来的向量、以及第 6 / 13 章用到的应用层向量"该放到哪个数据库"。读时先记两条主线：**召回层 vs 应用层** 职责分离；**模式 A / B / C** 对应业内三种标量+向量组合方式。看到 `OpenSearch DSL` 时不必背 API，重点理解"为什么权重在引擎层可调"是关键差异点。

---

## 1、本章导读

### 1.1 为什么单独开这一节

[第 4 章](<07-04-0 鸿蒙开发助手三塔召回与工程语义.md>) 把三塔模型和 ANN 检索讲清楚了，但有几件事故意没展开：

- 三塔训出来的向量到底进哪个数据库？

- [第 6 章](<11-06 长期记忆与开发者画像Store.md>) 的长期记忆 Store 后端选什么？

- [第 13 章](<18-13 APIInsight能力洞察工具与RAG鸿蒙知识库.md>) `APIInsight` 的 RAG 鸿蒙知识库索引用什么？

这三件事如果分散在各章里讲，会让读者一头雾水：为什么 `DocSearch` 用 `Faiss`、知识库也是 `Faiss`、长期记忆又是另一回事？这背后到底是经过选型论证的，还是随手拍的？

这一节把三处的选型放到一起，给出统一答案：**召回层用 **`Faiss`**（生产演进 **`Milvus`**），应用层用 **`OpenSearch`。

### 1.2 本章先做什么，不做什么

完成的：

1. 把项目里向量需求按"召回层 vs 应用层"分类，看清两类需求的本质差异。

1. 横向对比 8 家主流向量库 / 检索引擎在 HarmonyDev 场景下的得分。

1. 给出 `OpenSearch Hybrid Query` 的最小可运行配方。

1. 给出双栈定型图 + 后续章节的写法基线。

暂时不碰的：

- 三塔模型本身的训练细节（在 [第 4 章](<07-04-0 鸿蒙开发助手三塔召回与工程语义.md>)）。

- `OpenSearch` 集群运维（分片 / 副本 / 备份恢复，留给生产部署章节）。

- `Lucene` 索引底层（本章只到 `HNSW` 为止）。

---

## 2、HarmonyDev 项目里向量检索散在哪

先把 HarmonyDev 里所有"用到向量"的地方列清楚。这一步直接决定了我们要不要分栈。

| 章节 | 用途 | 数据规模 | 向量来源 | 必备能力 | 对延迟敏感度 |
| --- | --- | --- | --- | --- | --- |
| [第 4 / 11 章](<16-11 DocSearch文档检索工具实现与多源fork触发场景.md>) | API/代码片段三塔召回（`doc_search`） | 百万 ~ 千万级 API 条目 | **自有训练三塔**，已是 numpy 数组 | 高 QPS、`IP` 度量、批量重建索引 | 极高（P99 < 50ms） |
| [第 13 章](<18-13 APIInsight能力洞察工具与RAG鸿蒙知识库.md>) | RAG 鸿蒙知识库（`api_insight`） | 千 ~ 万级卡片 | `Query` 塔 HTTP 在线编码 | metadata filter（`card_type` / `category`）、增量写入 | 一般（P99 < 200ms） |
| [第 6 章](<11-06 长期记忆与开发者画像Store.md>) | 长期记忆 Store | 每用户几十条偏好 | `Query` 塔 HTTP 在线编码 | metadata filter（`category=blacklist`）+ 跨会话持久化 + 时间衰减 | 较低（P99 < 500ms） |

把这三行盯一会儿，会发现一件事：**它们在数据规模、向量生成方式、延迟要求、过滤需求上几乎完全不同**。

具体来说：

- **第 4 / 11 章**：吃的是"训练好的稠密向量直怼 ANN 索引"这种纯算力场景。引入数据库层只会增加序列化开销。

- **第 6 / 13 章**：吃的是"语义召回 + metadata filter + 业务规则"的组合场景。这种场景如果用纯向量库（比如 `Faiss`），过滤逻辑只能塞回业务代码，越写越复杂。

所以可以先下一个判断：**第 4/11 章是"召回层"，对算力和延迟敏感；第 6/13 章是"应用层"，对工程整合和过滤能力敏感**。两类需求性质不同，不应该用同一种数据库一刀切。

> **一个常见误解：** 既然都是"向量检索"，统一用一个数据库不是更省事吗？  
> 答案是：**省事的代价是其中一类场景被严重劣化**。这就是接下来要展开的事情。

---

## 3、标量过滤与向量检索：三种结合方式

要讲清楚为什么要分栈，先把"标量过滤怎么和向量检索结合"这件事拆开。业内现有方案大致分三种模式。

为了让三种模式的差异一眼看到，下面三小节用**同一个例子**串起来：

> API 知识库里有 1 万条 API/代码片段，每条 API/代码片段有名称、实现成本、API 约束三个字段。
> 用户需求：**找“和 ‘页面返回后状态丢失’ 最像、且实现成本 < 3”的 API/代码片段**。

请重点关注每一步「剩多少条」。

### 3.1 模式 A：Pre-filtering（先过滤，再 ANN）

```
标量过滤  ->  候选子集  ->  向量检索  ->  TopK
```

**代表实现**：`Milvus`、`Qdrant`（filterable HNSW）、`pgvector`。

**例子**：先过滤实现成本，再在候选集里找最像的。

```
1 万条 API/代码片段
   ↓  WHERE 实现成本 < 3
8 条候选
   ↓  HNSW ANN 找最像“页面返回后状态丢失”的
8 条中的 TopK
```

**问题在哪**：`HNSW` 的近邻图是为「稠密的 1 万个点」建的，现在只剩 8 个点，索引几乎完全失效——结果接近于「在这 8 条里随机抽」。如果过滤后只剩 1 条，「最近邻」这个问题本身就没意义。

**一句话总结**：**过滤越严，向量检索越不准**。

### 3.2 模式 B：Post-filtering（先 ANN，再过滤）

```
向量检索  ->  TopK  ->  标量过滤  ->  交集结果
```

**代表实现**：纯 `Faiss` + 业务层过滤、`Chroma`。

**例子**：同样 1 万条 API/代码片段、同样需求。这次反过来：先找最像的，再过滤实现成本。

```
1 万条 API/代码片段
   ↓  ANN 找最像“页面返回后状态丢失”的 Top-100
100 条候选
   ↓  filter 实现成本 < 3
2 条
```

但第 101 名、第 200 名、第 500 名里还有很多低改动的 LocalStorage 方案——它们在语义上也很像，但在 ANN 阶段就被截断了，**根本没机会进入候选**。

调大 TopK（比如拿 Top-1000）能缓解，但内存和延迟会随之翻倍。

**一句话总结**：**被 ANN 起手丢掉的，过滤阶段捞不回来**。

### 3.3 模式 C：Hybrid Fusion（多路并行融合）

```
向量检索（KNN）       ->  结果集 A（含相似度分） \
                                                   -> 归一化 -> 加权融合 -> TopK
全文 / 标量检索（BM25）-> 结果集 B（含相关性分） /
```

**核心公式：**

```
最终分 = α × 归一化向量分 + β × 归一化文本分
```

**例子**：还是同样的 1 万条 API/代码片段、同样的需求。这次不串行，让两路并行走：

```
              ┌── 子路 1：ANN 找“像页面返回后状态丢失”的 ─→ 50 条，每条带相似度分（0~1）
1 万条 ─┤
              └── 子路 2：filter 实现成本 < 3             ─→ 800 条，每条带实现成本匹配分

两路合并去重（并集≈838 条，不是取交集）
   ↓  缺席的那一路分数补 0
   ↓  两路分数各自归一化到 [0, 1]
最终分 = 0.7 × 相似度分 + 0.3 × 实现成本匹配分
   ↓
按最终分排序，取 Top-10
```

> 为什么是并集不是交集？交集只会留下 50 ∩ 800 那 ~12 条，“语义很像但改动成本略高”、“低改动但语义稍偏”的中间 API/代码片段全都会被过滤掉——又退化成 Pre/Post filter 的同样问题。并集 + 加权打分才能让**两路互相代偿对方的缺席**。

拿到的 10 条是“语义上够像 + 实现成本足够低”的最佳组合。两路互不干扰：ANN 不需要提前考虑实现成本，实现成本过滤也不需要关心语义。

**这种模式最大的好处：权重运行时可调**。

| 今天想让用户看到什么 | 怎么调 | 要不要重启服务 |
| --- | --- | --- |
| 更看重“像” | α=0.9, β=0.1 | 不需要 |
| 更看重“低改动” | α=0.4, β=0.6 | 不需要 |
| 两者平衡 | α=0.5, β=0.5 | 不需要 |

权重在引擎层就是个参数，这是前两种模式**都做不到的事**。

### 3.4 三种模式本质对比

| 模式 | 两路是否独立 | 权重是否可调 | 改权重要不要重启服务 |
| --- | --- | --- | --- |
| Pre-filtering | 否（过滤决定向量候选） | — | — |
| Post-filtering | 否（先 ANN 决定过滤池） | — | — |
| **Hybrid Fusion** | **是（两路并行）** | **是** | **不需要** |

把这张表对到 HarmonyDev 应用层（第 6 / 13 章）的现实需求上：

- 第 6 章 [`Store.read_relevant`](<11-06 长期记忆与开发者画像Store.md>) 要做"硬约束（黑名单）全量返回 + 软偏好（preference）向量 Top-K"——明显是模式 C 的目标场景。

- 第 13 章 [`api_insight`](<18-13 APIInsight能力洞察工具与RAG鸿蒙知识库.md>) 要做"按 `card_type` 分桶 + 按语义相关度排序"——也是模式 C。

而召回层（第 4 / 11 章）的诉求不一样——它的"过滤"主要是按平台（harmony_docs / openharmony_docs / sample_code / migration_notes）分库，用 fork 子 AgentLoop 的方式天然解决了，不需要在向量库里做 Hybrid。

---

## 4、主流向量库横向对比

把视野放到整个生态，做一次横向对比：

| 数据库 | 向量索引 | 全文检索 | 标量过滤 | Hybrid 加权融合 | 协议 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `Faiss` | HNSW / IVF / PQ | 不支持 | 业务层 | 否 | MIT | **算法库**，召回层标杆 |
| `Milvus` | HNSW / IVF / DiskANN | 不支持 | Pre-filter | 弱（RRF 排名融合） | Apache 2.0 | 千万 - 亿级演进路径 |
| `Qdrant` | HNSW | 不支持 | filterable HNSW | 否 | Apache 2.0 | 纯向量库 |
| `Weaviate` | HNSW | 内置 | 内置 | 是（`alpha` 参数） | BSD-3 | 一站式 |
| `pgvector` | HNSW / IVFFlat | 靠 PG 全文 | 靠 PG `WHERE` | 否（要写联合 SQL） | PostgreSQL | 复用 PG 体系 |
| `Redis Stack` | HNSW | RediSearch | RediSearch | 弱（RRF） | RSALv2 / SSPL | 中小规模友好 |
| `Chroma` | HNSW | 不支持 | Post-filter | 否 | Apache 2.0 | 入门、原型 |
| `Elasticsearch 8+` | HNSW（Lucene） | BM25 + 分词 | 完整 | 是（RRF / linear） | SSPL / Elastic | 7.11 起协议变更 |
| `OpenSearch` | **HNSW（FAISS / nmslib / Lucene）** | **BM25 + 分词** | **完整** | **是（线性加权 + 多种归一化）** | **Apache 2.0** | **HarmonyDev 应用层选型** |

把 HarmonyDev 应用层的诉求逐项过一遍：

- **Hybrid 加权融合**：只有 `OpenSearch` / `ES 8+` / `Weaviate` 三家原生支持。

- **中文全文检索**（含 `ik` 分词）：上述三家都能装中文分词器插件。

- **标量过滤**（`category` 精确 + 时间 `range`）：上述三家全部完整支持。

- **中文分词器复用**：`OpenSearch` 直接装同名 `analysis-ik` 插件即可。

综合下来，**应用层的最优解是 **`OpenSearch`——不是单项最强，而是它把"语义召回 + 全文匹配 + 标量过滤"装在了同一个引擎里，权重还能在引擎层调。

---

## 5、为什么应用层最终选 OpenSearch

把上一节的横向对比再翻译成 HarmonyDev 视角的"否决理由"，会更清楚。

| 候选 | 否决理由 |
| --- | --- |
| `Faiss` | 没有 metadata filter、没有全文检索，应用层逻辑会全部塞回业务代码 |
| `Milvus` | 千万级以上的"召回层"利器，但应用层只有几千条数据，杀鸡用牛刀；混合检索只支持 RRF 排名融合，没有线性加权 |
| `Qdrant` | 纯向量库，第 6 章长期记忆里"黑名单全量 + 偏好 Top-K"的双通道融合做不了 |
| `Weaviate` | 能做 Hybrid，但生态较新、运维心智和团队不通用 |
| `pgvector` | 项目没用 `Postgres`，引入一套 PG 体系成本过高 |
| `Redis Stack` | 中小规模友好，但 Hybrid 只能走 RRF，权重不可调；和教学侧重"分数融合权重在引擎层可调"的目标不匹配 |
| `Chroma` | 入门好用，但只有 Post-filter，不适合生产 |
| `Elasticsearch 8+` | 能力最接近 `OpenSearch`，但 7.11 起协议变更，企业商用要小心 |

剩下的就是 `OpenSearch`：

- **它是 **`ES 7.10`** 的 fork**，所以读者已经掌握的 `mapping / bool query / ik 分词` 知识全部复用。

- **协议干净**（Apache 2.0），企业可以放心用。

- **唯一开源 + 原生支持线性加权融合**——`Search Pipeline` + `Hybrid Query` 这套组合是 ES 体系里最早成熟的（2.10+），且 `Neural Search` 插件可托管 embedding。

> 一句话总结：`OpenSearch`** 在 HarmonyDev 应用层之所以是最优解，不是因为它单项能力最强，而是因为它把"语义 + 文本 + 标量"三件事用同一套 DSL 表达成了一次请求，并且把分数融合的权重做成了运行时可调参数。**

---

## 6、OpenSearch Hybrid Query 最小配方

`OpenSearch` 解决"双路融合"用的是两个组合拳：**Search Pipeline** + **Hybrid Query**。

### 6.1 第一步：定义搜索管道

告诉引擎：怎么归一化每路分数、按什么权重组合。

```python
# 创建一个 search pipeline
search_pipeline = {
    "phase_results_processors": [
        {
            "normalization-processor": {
                # 归一化方式：min_max（推荐）、l2
                "normalization": {"technique": "min_max"},
                # 融合方式：arithmetic_mean / geometric_mean / harmonic_mean
                "combination": {
                    "technique": "arithmetic_mean",
                    # 这里就是公式里的 [α, β]
                    # 向量分权重 0.7、全文分权重 0.3
                    "parameters": {"compat_weights": [0.7, 0.3]},
                },
            }
        }
    ]
}

await client.transport.perform_request(
    "PUT", "/_search/pipeline/hybrid_pipeline", body=search_pipeline,
)
```

`normalization-processor` 是 `OpenSearch 2.10+` 才有的搜索管道处理器；`min_max` 把每路分数线性映射到 `[0, 1]`，避免 `cosine` 的 `0~1` 和 `BM25` 的无界正数直接相加导致量纲打架。

### 6.2 第二步：写 Hybrid 查询

把多路检索装进同一次请求。下面这段以 [第 6 章长期记忆](<11-06 长期记忆与开发者画像Store.md>) 的 `read_relevant` 为例：

```python
query = {
    "query": {
        "hybrid": {
            "queries": [
                # 子路 1：语义召回（软偏好）
                {
                    "knn": {
                        "content_vector": {
                            "vector": query_embedding,  # 问题意图塔编码用户当前问题
                            "k": 100,
                        }
                    }
                },
                # 子路 2：全文 + 标量过滤（硬约束 + 业务条件）
                {
                    "bool": {
                        "must":   [{"match": {"content": "不接受废弃 API"}}],
                        "filter": [
                            {"term":  {"category": "blacklist"}},
                            {"term":  {"user_id":   "user-abc123"}},
                            {"range": {"created_at": {"gte": "now-90d"}}},
                        ],
                    }
                },
            ]
        }
    }
}

resp = await client.search(
    index="globex_memory",
    body=query,
    params={"search_pipeline": "hybrid_pipeline"},
)
```

### 6.3 引擎内部的处理流程

```
向量子路  ->  [score_v1, score_v2, ...]  ->  min_max 归一化  ->  [0~1]
全文子路  ->  [score_t1, score_t2, ...]  ->  min_max 归一化  ->  [0~1]

最终分 = (norm_score_v × 0.7 + norm_score_t × 0.3) / (0.7 + 0.3)
       ->  按最终分排序  ->  返回 TopK
```

应用层拿到的就是已经融合好的 TopK，**不需要自己写归一化和加权**。

### 6.4 这件事在其他方案里做不到

把同样的事情放到 `Faiss + Redis` 或 `Qdrant + ES` 这种"双库手工拼"的方案上：

| 卡点 | 原因 |
| --- | --- |
| 跨库归一化做不了 | 两个引擎各自只能看见自己那一路的分数 |
| 改权重要重启服务 | `α / β` 是写在应用层代码里的常量 |
| 跨库过滤要写两遍 | `category` / `user_id` / `created_at` 在两边各写一次，容易漏改 |
| 两套客户端 + 两套监控 | 任何一套掉链子都让整个查询降级 |

而 `OpenSearch Hybrid Query` 把这四件事都收口到一个引擎里。

---

## 7、HarmonyDev 的最终双栈定型

### 7.1 双栈定位图

```
┌─────────────────────────────────────────────────────────────────┐
│  HarmonyDev 向量基础设施（双栈分层）                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  召回层  │  Faiss（HNSW + IP）  ─→  演进路径：Milvus           │
│          │  - 第 4 章三塔召回                               │
│          │  - 第 11 章 DocSearch 工具                          │
│  ─────── │  ─────────────────────────────────────────────       │
│                                                                 │
│  应用层  │  OpenSearch（Hybrid Query + COSINE + HNSW）          │
│          │  - 第 6 章长期记忆 Store（黑名单全量 + 偏好向量 TopK）│
│          │  - 第 13 章 APIInsight 知识库 RAG                │
│  ─────── │  ─────────────────────────────────────────────       │
│                                                                 │
│  Embed   │  统一复用三塔 问题意图塔（HTTP）                       │
│          │  - 召回层离线灌库用                                  │
│          │  - 应用层在线增量写入用                              │
│          │  - 保证两栈向量空间一致                              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 关键决策矩阵

| 决策 | 选什么 | 否决了谁 | 主因 |
| --- | --- | --- | --- |
| 召回层向量库 | `Faiss`（生产演进 `Milvus`） | `Milvus` / `Qdrant` / `Redis Stack` | 千万级训练向量、纯算力场景；引入数据库层只增加序列化开销 |
| 应用层向量库 | `OpenSearch` | `Faiss` / `Redis Stack` / `Chroma` / `pgvector` | 唯一同时支持"语义 + 全文 + 标量 + 加权融合"的开源方案 |
| 长期记忆接口壳 | `LangGraph BaseStore` | 自研抽象基类 | 与 LangGraph 生态对齐，下层后端可换 |
| Embedding 模型 | **三塔 **`Query`** 塔** | `DashScope` / `OpenAI` | 项目自身就在训练 Encoder，引入第三方反而打架 |
| 距离度量 | 召回层 `IP` / 应用层 `COSINE` | `L2` | `IP` 配三塔训练（向量已归一化）；`COSINE` 配文本通用 embedding |

### 7.3 后续章节的写法基线

把这张选型矩阵翻译成"后续章节代码长什么样"：

| 章节 | 关键技术栈 | 代码骨架 |
| --- | --- | --- |
| [第 4 章](<07-04-0 鸿蒙开发助手三塔召回与工程语义.md>) | `Faiss` + `IndexHNSWFlat`（IP） | 三塔训练 + 离线灌索引 + ANN 检索 |
| [第 11 章](<16-11 DocSearch文档检索工具实现与多源fork触发场景.md>) | `Faiss.read_index` + `AnnClient` | `doc_search` 工具内部包装 ANN 客户端 |
| [第 6 章](<11-06 长期记忆与开发者画像Store.md>) | `LangGraph BaseStore` + `OpenSearch` 后端 | `Store.read_relevant` 用 Hybrid Query 实现"黑名单全量 + 偏好向量 TopK" |
| [第 13 章](<18-13 APIInsight能力洞察工具与RAG鸿蒙知识库.md>) | `OpenSearch` + `OpenSearchVectorSearch` 替换 `Faiss` | `api_insight` 用 Hybrid Query 一次返回结构化卡片 |

> 注：当前各章代码示例如还残留 `Faiss` 写法实现应用层向量检索（第 6 / 13 章），将在后续重构中切到 `OpenSearch` 客户端；召回层（第 4 / 11 章）保持 `Faiss` 不变。

### 7.4 不适用场景

不是所有场景都该照搬这套双栈：

- 当**召回层向量规模到上亿**，且追求极致 P99 延迟时，建议向 `Milvus` 演进（`OpenSearch` 在这个量级会被检索吞吐量拖累）。

- 当**应用层数据规模 < 1k**、且无须做加权融合时，纯 `Redis Stack` 或 `Chroma` 反而更轻量。

- 当**团队已深度依赖 **`Postgres`** 体系**，且没有独立检索集群时，`pgvector` 是合理的折中。

HarmonyDev 的双栈选型对应的是"中等规模 + 教学场景 + 应用层有融合需求"的典型路径，覆盖大多数真实鸿蒙开发助手 Agent 项目。

---

**本章小结：**

- HarmonyDev 项目里向量检索分布在三处：第 4 / 11 章API/代码片段召回（千万级 API 条目 + 自有训练向量）、第 13 章 RAG 知识库（千~万级 + 问题意图塔编码）、第 6 章长期记忆（每用户几十条 + 问题意图塔编码）。

- "标量过滤"和"向量检索"的结合方式有三种：Pre-filtering（候选过少时召回塌方）、Post-filtering（TopK 之外的相关结果先被丢）、**Hybrid Fusion（两路独立 + 引擎层加权融合，唯一让权重运行时可调）**。

- 横向对比 8 家主流方案后，HarmonyDev 应用层的最优解是 `OpenSearch`——它是唯一同时满足"语义 + 全文 + 标量过滤 + 线性加权融合 + 干净开源协议"的方案。

- 召回层不上 `OpenSearch`：千万级训练向量场景下 `Faiss` 直接吃 numpy 数组、单机就能跑出 P99 < 50ms，引入数据库层只增加序列化开销。

- 双栈定型：**召回层 **`Faiss`**（生产演进 **`Milvus`**） + 应用层 **`OpenSearch`，两栈共享同一份 `Query` 塔做 embedding，避免向量空间漂移。

下一章 [Cache Breakpoint 上下文压缩与缓存治理](<10-05 Cache-Breakpoint上下文压缩与缓存治理.md>) 回到工程层，讲 50 轮对话之后 token 怎么不爆掉的问题。
