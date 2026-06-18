## 3. 核心架构：LangGraph 工作流

### 3.1 为什么选择 LangGraph

LangGraph 是一个基于**有向图 (Directed Graph)** 的工作流编排框架，相比 LangChain 的线性 Chain，它天然支持：

- **条件分支**：根据中间结果动态选择下一步
- **循环/重试**：失败节点可以回到上游重新执行
- **状态持久化**：通过 State 对象在工作流中传递上下文
- **可观测**：每个节点的输入/输出/耗时都可通过装饰器追踪

本项目使用 LangGraph 的 `StateGraph` 构建了一个**13 节点 + 7 条件路由**的复杂工作流。每个节点都是纯 async 函数——意图分类和工具选择等核心决策以关键词/规则匹配为主，LLM 调用仅在同步上下文且配置了真实 API key 时作为可选增强生效。

### 3.2 统一状态对象：PipelineState

`PipelineState` 是整个工作流的**唯一真相来源 (Single Source of Truth)**，定义在 `graph/state.py`，使用 `TypedDict` 实现，包含约 70 个可选字段：

```python
class PipelineState(TypedDict, total=False):
    # === 输入层 ===
    query: str                          # 用户原始问题
    user_id: str                        # 调用者标识
    session_id: str                     # 会话标识

    # === 权限层 ===
    user_role: str                      # admin / developer / basic
    permissions: list[str]              # 权限列表

    # === 路由层 ===
    intent: str                         # 分类意图
    complexity: str                     # 问题复杂度
    route: str                          # 路由决策 ("rag" | "tools")

    # === RAG 层 ===
    retrieved_docs: list[dict]          # 检索到的文档
    reranked_docs: list[dict]           # 重排序后的文档

    # === 工具层 ===
    tool_calls: list[dict]              # 工具调用记录
    tool_results: list[dict]            # 工具执行结果
    tool_errors: list[str]              # 工具错误信息
    pending_tool_confirmations: list    # 等待用户确认的敏感操作

    # === 生成与校验层 ===
    draft_answer: str                   # 草稿答案
    verified: bool                      # 是否通过校验
    verification_reason: str            # 校验失败原因
    final_answer: str                   # 最终答案
    citations: list[dict]               # 引用来源
    need_human: bool                    # 是否需要人工介入

    # === 记忆层 ===
    chat_history: list[dict]            # 对话历史
    session_summary: str                # 会话摘要
    user_profile: dict                  # 用户档案
    memory_ckpt_id: str                 # 检查点 ID

    # === 上下文管理层 ===
    structured_context: dict            # 结构化上下文
    context_window: str                 # 上下文窗口
    prompt_context: dict                # 各 Agent 的 prompt
    token_budget: dict                  # Token 预算信息

    # === 恢复层 ===
    fallback_reason: str                # 兜底原因
    recovery_action: str                # 恢复动作
    retry_count: dict[str, int]         # 各节点重试计数
    retry_history: list[dict]           # 重试历史
    human_fallback_payload: dict        # 人工兜底载荷
    recoverable: bool                   # 是否可恢复

    # === 可观测层 ===
    trace_id: str                       # 追踪 ID
    node_events: list[dict]             # 节点事件
    metrics_snapshot: dict              # 指标快照

    # === LangGraph 消息流 ===
    messages: Annotated[list, add_messages]  # 对话消息（自动追加）
```

**设计要点：**

- `total=False` 使得所有字段都是可选的，新节点可以渐进式填充状态
- `messages` 字段使用 `Annotated[list, add_messages]`，LangGraph 的 reducer 机制会自动将新消息追加到已有列表
- 状态对象的每个字段都有明确的**生产者节点**和**消费者节点**，形成清晰的数据流

### 3.3 完整工作流拓扑

```
                        ┌──────────────┐
                        │    START     │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │ load_memory  │  ← 加载会话历史、用户档案、检查点
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │check_permission│ ← 权限校验
                        └──────┬───────┘
                               │
                    ┌──────────┼──────────┐
                    │ 权限不足  │          │ 权限通过
                    │           │          │
              ┌─────▼─────┐  ┌──▼──────────▼──┐
              │final_refusal│  │classify_intent │ ← 意图分类
              └─────┬─────┘  └──┬──────┬──────┘
                    │            │      │
                    │     ┌──────┘      └──────┐
                    │     │ 已知意图    未知意图 │
                    │     │                    │
                    │  ┌──▼──────┐    ┌───────▼──────┐
                    │  │ 路由判断 │    │human_fallback│ ← 人工兜底
                    │  └──┬───┬──┘    └───────┬──────┘
                    │     │   │               │
                    │     │   └─────────┐     │
                    │  ┌──▼──────┐ ┌───▼─────▼─┐
                    │  │retrieve │ │call_tools │ ← 工具执行(最多重试2次)
                    │  │knowledge│ └─────┬─────┘
                    │  └──┬───┬──┘       │
                    │     │   │          │
                    │     │   └──────────┘
                    │  ┌──▼──────────────▼──┐
                    │  │   build_context    │ ← 组装上下文+Token预算+引用
                    │  └────────┬───────────┘
                    │           │
                    │  ┌────────▼───────────┐
                    │  │  generate_answer   │ ← 生成草稿答案
                    │  └────────┬───────────┘
                    │           │
                    │  ┌────────▼───────────┐
                    │  │   verify_answer    │ ← 答案校验
                    │  └──┬──────┬──────┬───┘
                    │     │      │      │
                    │  ┌──┘  ┌──┘      └──┐
                    │  │通过 │未通过+重试 │未通过+耗尽
                    │  │     │           │
              ┌─────┐ │  ┌──▼──────┐ ┌──▼──────────┐
              │     │ │  │build_   │ │human_fallback│
              │     │ │  │context  │ │              │
              │     │ │  │(重新生成)│ └──────┬───────┘
              │     │ │  └─────────┘        │
              │  ┌──▼──▼──┐                 │
              │  │finalize │                 │
              │  │_answer  │                 │
              │  └──┬──────┘                 │
              │     │                        │
              └──┬──┴────────────────────────┘
                 │
          ┌──────▼───────┐
          │ save_memory  │  ← 保存对话、更新摘要、写检查点
          └──────┬───────┘
                 │
          ┌──────▼───────┐
          │     END      │
          └──────────────┘
```

### 3.4 路由决策逻辑

工作流中有 **7 个条件路由函数**，每个都基于当前 State 做出决策：

#### 权限门控 (`_after_permission`)

```python
def _after_permission(state) -> Literal["classify_intent", "final_refusal"]:
    # 用户必须有 knowledge_search 权限才能继续
    if "knowledge_search" not in state.get("permissions", []):
        return "final_refusal"    # → 礼貌拒绝
    return "classify_intent"      # → 意图分类
```

#### 意图路由 (`_after_classify`)

```python
def _after_classify(state) -> Literal["retrieve_knowledge", "call_tools", "human_fallback"]:
    intent = state.get("intent", "")
    if intent == "unknown":
        return "human_fallback"           # → 无法识别，人工兜底
    if state.get("route") == "tools":
        return "call_tools"               # → 排障/工单类，先调工具
    return "retrieve_knowledge"           # → 技术/政策类，检索知识库
```

#### 检索后路由 (`_after_retrieve`)

```python
def _after_retrieve(state) -> Literal["build_context", "call_tools", "rewrite_query", "human_fallback"]:
    docs = state.get("retrieved_docs", [])
    if docs and any(d.get("score", 0) > 0 for d in docs):
        return "build_context"            # → 有结果，构建上下文
    # 无结果：检查是否可以查询改写重试
    if _recovery.can_retry("retrieve", state.get("retry_count", {})):
        return "rewrite_query"            # → 改写查询重试
    return "human_fallback"               # → 重试耗尽，人工兜底
```

#### 校验后路由 (`_after_verify`)

```python
def _after_verify(state) -> Literal["finalize_answer", "build_context", "human_fallback"]:
    if state.get("verified", False):
        return "finalize_answer"          # → 校验通过，输出答案
    # 未通过：检查是否可以重新生成
    if _recovery.can_retry("verify", state.get("retry_count", {})):
        return "build_context"            # → 重新生成答案（回到上下文构建）
    return "human_fallback"               # → 重试耗尽，人工兜底
```

### 3.5 工作流编译

`build_workflow()` 函数将所有节点和边组装成可执行的图：

```python
def build_workflow() -> StateGraph:
    builder = StateGraph(PipelineState)

    # 每个节点都用 tracer.traced_node() 包装，自动记录执行追踪
    builder.add_node("load_memory",       _tracer.traced_node("load_memory", load_memory))
    builder.add_node("check_permission",  _tracer.traced_node("check_permission", check_permission))
    # ... 13 个节点

    # 定义边和条件边
    builder.add_edge(START, "load_memory")
    builder.add_conditional_edges("check_permission", _after_permission, {...})
    # ...

    graph = builder.compile()
    graph.name = "EnterpriseHybridRAG"
    return graph
```

每个节点函数都返回一个 `dict[str, Any]`，LangGraph 会自动将这些返回值**合并**到全局 State 中，实现状态在节点间的传递。

---

#### 📋 面试题追加（STAR 结构化）：Agent 工作流编排

> 以下面试题按 **STAR 法则**组织：**S** (情境) → **T** (任务) → **A** (行动) → **R** (结果)。项目相关答案基于 Enterprise Hybrid RAG 源码实现。

| 题目 | 重要性 |
|------|--------|
| Agent 和 Workflow 的区别与选择 | S |
| 为什么你的项目用了 Agent 而不是纯 Workflow？ | S |
| Multi-Agent 何时必要以及协作模式 | A |
| 多Agent系统如何编排？遇到过死锁吗？ | S |
| 多Agent系统如何防止死锁和无限循环？ | S |
| Orchestrator Agent 的任务分配出了错怎么办？ | S |
| Multi-Agent 系统的延迟怎么控制？ | A |
| LangGraph、CrewAI、AutoGen 等 Agent 框架对比 | A |
| 你的项目中利用LangGraph编排多工具调用链路的优势？ | A |

##### Q1: Workflow 编排 vs LLM Agent 的区别 [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 9/10）：** 本项目本质是 LangGraph StateGraph 构建的 13 节点条件流水线（§3.3），约 70% 请求走固定路径。动态行为体现在条件路由函数（§3.4）和基于关键词的意图分类后的路由决策（§4.2）。核心设计哲学：固定流程 + 条件分支覆盖主路径，工具选择以规则匹配为主，不依赖 LLM 做动态决策。

**项目区分：**
- **Workflow 部分**：load_memory → check_permission → classify_intent → retrieve → build_context → generate → verify → save_memory（固定 DAG）
- **动态路由部分**：工具根据意图+关键词选择、校验失败后 regenerate 决策、检索无结果时 query rewrite 重试——均基于硬编码条件判断，非 LLM 自主决策


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** Agent 和 Workflow 不是二元对立，而是光谱。选择标准：① 步骤确定性高的（如 FAQ 问答）→ Workflow；② 需要根据中间结果动态决策的（如多步工具调用）→ Agent；③ 实践中通常 80% Workflow + 20% Agent 混合架构。

##### Q2: 多节点系统如何防止死锁和无限循环？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 项目是 LangGraph 编排多个功能模块的架构，非多 Agent 自由协作。通过以下机制防止异常：① 检索重试上限 1 次、工具调用重试上限 2 次、校验重试上限 1 次（§9.4）；② 重试耗尽 → human_fallback（§9.7）；③ 工具的重复调用检测机制。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（多Agent系统）：** ① Orchestrator 全局超时（如 120s）→ 强制终止返回部分结果；② 环形依赖检测：维护 Agent 调用图，检测 A→B→C→A 环路；③ 最大跳数限制：任务经过的 Agent 跳数 ≤ N（通常 5-10）；④ 死信队列：超限任务转入人工介入队列。

##### Q3: 本项目的 RAG 与传统 RAG 的区别 [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 本项目的 RAG 相比传统线性 RAG（query→embed→search→generate）增加了：① 意图分类后的动态路由（retrieve vs call_tools vs human_fallback）；② 工具选择（基于关键词/正则匹配，非 LLM 驱动）；③ 答案校验后的 regenerate 或 finalize 决策；④ 检索失败时的 query rewrite 重试。注意：这些决策以规则匹配为主，LLM 仅作为可选增强。

**核心差异：** 传统 RAG = 固定管道（retrieve → generate）；本项目 = 多步骤条件流水线（classify → [retrieve ⇄ rewrite] → [generate ⇄ verify] → finalize），带有 fallback 机制。

##### Q4: Multi-Agent 何时必要以及协作模式 [A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 本项目是单图多模块架构（LangGraph 编排 4 个功能模块：Router/Knowledge/Tool/Verifier），各模块共享全局 PipelineState 通过 State 传递而非直接通信。选择此方案的理由：问题领域足够窄（企业知识问答），不需要多个独立 LLM Agent 自由协商。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（多Agent场景）：** Multi-Agent 必要性判断：① 任务天然可拆分（如一个 Agent 写代码、一个做 Code Review）；② 需要异质工具集（如一个 Agent 操作浏览器、一个操作数据库）；③ 需要辩论/反思机制（多个 Agent 交叉验证）。协作模式：顺序流水线（A→B→C）、层级调度（Orchestrator→Worker）、辩论/投票（多个 Agent 并行回答→取共识）。

##### Q5: 多模块系统如何编排？遇到过死锁吗？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 本项目通过 LangGraph StateGraph 做编排（§3.3），13 个节点、7 个条件路由函数，天然避免死锁——StateGraph 是 DAG（有向无环图），节点执行顺序由编译期确定，不存在循环等待。实际遇到的问题：工具调用链中的解析失败→通过规则兜底+正则提取参数解决。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** 死锁主要出现在多 Agent 自由通信场景（A 等待 B 的结果、B 等待 A 的确认）。解决方案：① 全局超时（120s）→ 强制返回部分结果；② 环形依赖检测：维护 Agent 调用图，检测 A→B→C→A；③ 最大跳数限制 ≤ 10。

##### Q6: 路由决策出错怎么办？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 项目没有 Orchestrator Agent，路由由 LangGraph 条件路由函数处理（§3.4）。路由错误防护：① 意图分类有规则 fallback（关键词匹配为主，LLM 可选）；② 工具选择的双层匹配兜底（意图不匹配时用关键词触发）；③ 最终 human_fallback 节点兜底。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** ① Orchestrator 自身也应有校验 Agent 检查分配结果；② 分配错误 → Worker 返回"N/A"信号 → Orchestrator 重新规划；③ 任务描述应包含"如果不能完成请明确回复"约束；④ 记录每次分配决策到 trace 中用于事后分析。

##### Q7: 多模块系统的延迟怎么控制？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 项目从三个层面控制延迟：① 检索层：并行检索，总延迟 = max(各路径)，不是 sum（§5.13.3 Rule 7）；② LLM 调用使用小 token 限制（Router 端 max_tokens=32、Knowledge 端用 2048）；③ 大部分请求走固定 Workflow 路径，LLM 调用为可选增强。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** ① 并行化独立调用（同时调多个工具而非串行）；② 小模型先行（Router→小模型、Generator→大模型）；③ 流式输出（首个 token 延迟 < 2s）；④ 缓存热门问题的完整答案或中间结果（语义缓存）。

##### Q8: LangGraph、CrewAI、AutoGen 等 Agent 框架对比 [A]

**本项目选 LangGraph 的原因（评分 8/10）：** StateGraph 的 TypedDict + Annotated reducer 机制天然适合多节点状态管理（§3.2）；条件路由函数提供确定性分支（§3.4）；Python 原生实现、社区活跃、LangChain 生态兼容。选 LangGraph 而非 CrewAI/AutoGen 的本质原因是：本项目不需要 LLM Agent 间的自由协商，需要的是确定性条件流水线。

**框架对比：**
| 维度 | LangGraph | CrewAI | AutoGen |
|------|-----------|--------|---------|
| 编排模型 | 状态图（DAG+条件分支） | 角色+任务+顺序/层级 | Agent 对话/聊天 |
| 状态管理 | TypedDict + Reducer（强） | 任务局部状态（弱） | 对话历史（中） |
| 多Agent模式 | 单图多节点 | 多角色协作 | Agent间自由对话 |
| 学习曲线 | 中（需理解图概念） | 低（角色+任务抽象） | 中 |
| 适用场景 | 生产级复杂 Workflow | 快速原型/简单协作 | 研究/开放式对话 |

**选择建议：** 确定性强的生产 Workflow → LangGraph；快速原型（3-5 个 Agent 的简单协作）→ CrewAI；需要 Agent 间自由辩论/协商 → AutoGen。

##### Q9: 项目中利用LangGraph编排多模块链路的优势？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** ① StateGraph 的条件路由让模块选择逻辑与执行逻辑解耦（§3.4），新增模块只需注册 + 添加路由条件；② PipelineState 贯穿所有节点（§3.2），各模块执行结果自动注入 State，后续节点无需重新查询；③ `add_messages` reducer 自动累积消息历史，支持多轮交互；④ 编译期生成的可视化图可直接用于文档和调试。

---

## 4. 模块体系深度解析

### 4.1 设计模式：规则驱动 + LLM 可选增强

本项目的四个功能模块采用统一的**规则驱动 + LLM 可选增强**双路径架构。注意：实际执行顺序是**规则优先**——LLM 路径仅在同步上下文、配置了真实 API key、且非 Mock Provider 时才会触发。在典型的 async 运行路径（如 LangGraph 的 `ainvoke`）上，LLM 调用会被直接跳过，全程走规则匹配。

```
                    ┌─────────────┐
                    │  输入请求    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ 规则/关键词  │  ← 默认路径（始终可用）
                    │ 匹配引擎    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ LLM 可用？  │  ← 仅 sync 上下文 + 真实 API key
                    └──┬──────┬──┘
                       │ 是   │ 否
                 ┌─────▼──┐   │
                 │ LLM 增强│   │
                 └────┬───┘   │
                      │       │
                 ┌────▼───┐   │
                 │ 成功？  │   │
                 └──┬──┬──┘   │
                    │是│否    │
              ┌─────▼┐┌▼─────▼┐
              │返回  ││返回规则│
              │结果  ││结果   │
              └──────┘└───────┘
```

这种设计的特点：
- **规则保底**：LLM 不可用时返回确定性规则结果，不会报错
- **开发友好**：使用 Mock Provider 时可以完整运行所有路径，无需配置 API key
- **本质限制**：决策智能程度受限于规则/关键词覆盖度，不能真正"理解"用户意图

### 4.2 意图分类器（Router）

**文件：** `modules/intent_router.py`

**职责：** 将用户自然语言问题分类为 5 种预定义意图之一。

**默认路径（关键词匹配）：** 使用 40+ 个中文关键词的词典进行命中计数，选取得分最高的意图。无命中则返回 `general_question`。此外，在 async 事件循环中运行时 **LLM 路径被完全跳过**，这意味着通过 LangGraph `ainvoke` 调用时始终只走关键词匹配。

**可选 LLM 路径：**
```python
def _classify_with_llm(provider, query: str) -> str:
    prompt = (
        "你是一个企业级意图分类器。请将用户问题分类为以下意图之一：\n"
        "policy_question, technical_question, troubleshooting, ticket_query, general_question\n\n"
        f"用户问题: {query}\n\n请只返回意图标签。"
    )
    resp = provider.generate(prompt, temperature=0.0, max_tokens=32)
    # 解析并验证返回的意图标签
```

**规则路径（关键词匹配，默认路径）：**
```python
INTENT_KEYWORDS: dict[str, list[str]] = {
    "policy_question":    ["政策", "规定", "权限", "流程", "审批", "合规", ...],
    "technical_question": ["API", "接口", "SDK", "接入", "文档", "参数", ...],
    "troubleshooting":    ["错误", "报错", "故障", "异常", "失败", "401", "403", "500", ...],
    "ticket_query":       ["工单", "ticket", "进度", "处理", "状态", "查询", ...],
}

def _classify_keyword(query: str) -> str:
    # 统计每个意图的关键词命中数
    for intent, keywords in INTENT_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in query.lower())
        scores[intent] = hits
    # 返回命中最多的意图，无命中返回 general_question
    return max(scores, key=lambda k: scores[k])
```

**设计细节：**
- 核心就是关键词命中计数——没有语义理解，不依赖 LLM
- 短于 5 字符的 `general_question` 会被标记为 `unknown`（防止无意义输入通过）
- 在 async 事件循环中自动跳过 LLM 路径（即 LangGraph `ainvoke` 全程走关键词）

### 4.3 答案生成器（Knowledge）

**文件：** `modules/answer_generator.py`

**职责：** 基于检索到的文档生成答案文本和引用列表。

**默认路径（模板拼接）：** 直接将文档片段拼接为答案，生成编号引用（去重同源文档）。格式为 "根据知识库检索结果，为您找到以下相关信息：\n\n{doc1}\n\n---\n参考来源: [1] source_A (相关度: 0.85)"。

**可选 LLM 路径：**
```python
def _generate_with_llm(provider, query, docs):
    # 将文档格式化为编号块
    parts = [f"[文档{i+1}] {d.get('source')}\n{d.get('content')}" for i, d in enumerate(docs)]

    prompt = (
        "你是一个企业知识库问答助手。请根据以下参考文档回答用户问题。"
        "在回答中使用 [1]、[2] 等标记引用来源。\n\n"
        f"参考文档:\n{chr(10).join(parts)}\n\n"
        f"用户问题: {query}\n\n请生成回答："
    )
    resp = provider.generate(prompt, temperature=0.3, max_tokens=2048)
```

**设计要点：**
- LLM prompt 中指令使用 `[1]`、`[2]` 标记引用，模板路径同样遵循此格式
- 模板路径本质就是拼接文档片段——没有推理、没有综合、没有改写
- 工具执行结果作为额外段落追加到答案末尾
- 同一来源的多个 chunk 在引用中去重

### 4.4 工具编排器（Tool）

**文件：** `modules/tool_orchestrator.py`

**职责：** 根据意图和查询内容选择并执行合适的工具。**纯规则驱动，零 LLM 参与。**

**工具选择策略（双层关键词/正则匹配，零 LLM 参与）：**

```
第一层：意图映射（硬编码 if-else）
  intent == "troubleshooting" → get_system_status + get_error_code_detail
  intent == "ticket_query"    → query_ticket

第二层：关键词/正则触发（可与第一层叠加）
  查询含"系统状态"     → get_system_status
  查询含"工单"/"TKT"   → query_ticket
  正则匹配 TKT-\d{3}    → 提取工单号传入工具
  正则匹配 AUTH_\d{3}   → 提取错误码传入工具
```

**正则提取：**
```python
ticket_match = re.search(r"TKT-\d{3}", query)          # 提取工单号
error_match  = re.search(r"(AUTH_\d{3}|RATE_\d{3}|SYS_\d{3})", query)  # 提取错误码
```

**安全设计：**
- `create_ticket` 不会自动执行（需要用户确认）
- `query_ticket` 和 `get_user_profile` 自动注入 `user_id`
- 工具执行失败不影响主流程，错误被记录到 `tool_errors`

### 4.5 答案校验器（Verifier）

**文件：** `modules/answer_verifier.py`

**职责：** 校验生成的答案是否基于检索文档、引用是否正确。

**默认路径（规则检查）：** 检查答案是否为空、是否过短（<10字符）、是否包含引用标记、所有文档评分是否均为噪声。这些检查是结构性的——不能真正检测幻觉内容。

**可选 LLM 路径：**
```python
def _verify_with_llm(provider, answer, citations, docs):
    prompt = (
        "你是一个企业级答案校验器。请从以下维度判断草稿答案是否可靠：\n"
        "1. 答案是否基于提供的参考文档？\n"
        "2. 是否包含幻觉信息？\n"
        "3. 引用标记是否正确？\n"
        "4. 答案是否完整？\n\n"
        f"草稿答案:\n{answer}\n\n参考文档数: {len(docs)}, 引用数: {len(citations)}\n\n"
        '返回JSON: {"verified": true/false, "reason": "..."}'
    )
```

**规则引擎（fallback）：**
```python
def _verify_rules(draft, citations, docs):
    reasons = []
    if not docs:
        reasons.append("未检索到任何相关文档，答案缺乏依据")
    if not draft or not draft.strip():
        reasons.append("生成的答案为空")
    # 检查引用标记
    has_cit = any(m in draft for m in ("参考来源", "引用", "[1]", "citation"))
    if not has_cit and not citations:
        reasons.append("答案缺少引用来源，不可信")
    if len(draft.strip()) < 10:
        reasons.append("答案过短，可能未完整回答问题")

    verified = len(reasons) <= 1  # 最多容忍 1 个警告
    return verified, "; ".join(reasons) if reasons else "所有检查通过"
```

**校验策略关键点：**
- 容忍度设为 "≤1 个警告"：允许比如 "引用标记缺失但有引用数据" 这种可自动修复的情况
- 无文档时直接判定不通过（答案必须有依据）
- 空答案直接判定不通过
- LLM 校验失败时自动 fallback 到规则引擎

---

#### 📋 面试题追加（STAR 结构化）：模块体系核心设计

> 以下面试题按 **STAR 法则**组织：**S** (情境) → **T** (任务) → **A** (行动) → **R** (结果)。项目相关答案基于 Enterprise Hybrid RAG 源码实现。

| 题目 | 重要性 | 关联子章节 |
|------|--------|-----------|
| Agent 和 LLM 的区别 | S | §4.1 |
| ReAct 的核心思想以及和 CoT 的关系 | S | §4.4 |
| Agent Planning 常见策略与任务分解 | A | §4.4 |
| Agent 为什么经常失败？常见失败模式 | S | §9.5 |
| Agent 评测体系：任务成功率、工具调用与幻觉率 | S | §11 |
| Agent 权限、安全控制与 Guardrails | S | §8 |
| MCP 是什么？和 Function Calling 的关系 | S | §8 |

##### Q1: Agent 和 LLM 的区别 [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：**
- **LLM**：纯语言模型，输入文本 → 输出文本，无外部交互能力，无状态
- **Agent**：LLM + 工具调用 + 记忆系统 + 规划能力的综合体。本项目通过 LangGraph 将各功能模块（Router/Knowledge/Tool/Verifier）编排为工作流节点。其中 Router、Knowledge、Verifier 可选调用 LLM，**Tool Module 完全不使用 LLM**（纯关键词/正则匹配驱动）。各节点共享全局 PipelineState
- 关键差异：Agent 能**感知环境**（读取 State）、**做出决策**（条件路由）、**执行动作**（Tool Calling）、**从反馈中学习**（verify→regenerate 循环）


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** Agent = LLM（推理核心）+ Tools（外部行动能力）+ Memory（状态保持）+ Planning（任务分解与排序）。LLM 完成"理解与生成"，Agent 完成"感知-决策-执行-反馈"的完整闭环。

##### Q2: ReAct 核心思想 [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 项目未显式实现 ReAct 文本模式（Thought→Action→Observation），但 LangGraph 的 retrieve ⇄ rewrite 循环和 generate ⇄ verify 循环本质上体现了 ReAct 的"推理→行动→观察→调整"思想。Tool Module 的双层匹配策略（意图驱动 + 关键词驱动）承担了"该调用哪个工具"的推理职责。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** ReAct = Reasoning（推理）+ Acting（行动）。每一轮：Thought（分析当前状态，决定下一步）→ Action（调用工具）→ Observation（观察工具返回结果）→ 循环直至能给出最终答案。与 CoT 的关系：CoT 是"纯思维链"（只在脑内推理），ReAct 是"思维链 + 外部行动"（推理与工具调用交织）。

##### Q3: MCP vs Function Calling [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 项目将企业知识搜索封装为 MCP 工具暴露给外部 Agent 调用（`tools/mcp_knowledge_search.py`），Agent 只看到受控的知识查询能力，真正的检索、重排、生成、权限隔离和降级都在服务端完成。MCP 解决的核心问题：将企业知识能力标准化暴露给 Agent，同时不绕过租户隔离和权限边界。

**二者关系：**
- **Function Calling**：LLM 原生工具调用机制（模型输出 JSON 指定函数名和参数）——是"怎么调用"的协议
- **MCP（Model Context Protocol）**：标准化的工具描述和发现协议（定义工具的 schema、认证、传输方式）——是"如何发现和描述工具"的协议
- 它们不在同一层：MCP 定义工具接口标准，Function Calling 是调用机制，两者可配合使用

##### Q4: Agent Planning 常见策略与任务分解 [A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 项目未显式实现 Planning 模块。隐式的"规划"体现在：Router Agent 的意图分类（§4.2）决定了后续走 retrieve 路径还是 call_tools 路径；Tool Module（§4.4）的双层匹配策略（意图驱动→工具类型 → 关键词驱动→具体参数）可视为轻量级 task decomposition。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 主流 Planning 策略：① **ReAct 式逐步推理**（Thought→Action→Observation 循环，每步决定下一步）；② **Plan-and-Execute**（先一次性生成完整计划，再逐步执行，适合任务步骤可预测的场景）；③ **分层规划**（高层目标分解→低层子任务分配→并行执行，适合复杂任务）。选型建议：步骤少的任务用 ReAct（灵活），步骤多且可预测用 Plan-and-Execute（高效），需要并行加速用分层规划。

##### Q5: Agent 为什么经常失败？常见失败模式 [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 项目实际遇到的失败模式（§9.5）：① **工具选择偏差**：意图分类不准 → 选错工具 → 意图规则兜底（注：`tool_orchestrator.py` 全程使用关键词/正则匹配，零 LLM 参与）；② **幻觉引用**：LLM 生成时可能引用不存在的来源 → Verifier 通过规则检查引用标记模式（`[1]`、`参考来源` 等）检测异常；③ **检索不足**：用户问太泛 → 查询改写重试（§9.6）；④ **LLM 调用失败**：超时/不可用 → Provider 自动降级到 Mock/Template。所有失败通过 RecoveryManager 三级兜底（重试→降级→人工，§9.1）。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** Agent 失败的 6 种模式：① Planning 失败（任务分解不完整/顺序错误）；② Tool 使用失败（选错工具/参数格式错误/工具超时）；③ 观察理解失败（误读工具返回结果）；④ 无限循环（ReAct loop 不收敛）；⑤ 幻觉引证（编造来源）；⑥ 上下文溢出（多轮后超出 token 限制）。治理策略：每层独立计数限次 + 全局超时 + 失败分类统计做持续改进。

##### Q6: Agent 评测体系 [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 项目的 Agent 评测分散在多个维度（§11）：RAG 评估器测检索（Recall/MRR），答案评估器测生成（Faithfulness/Relevance），在线反馈测用户满意度。但缺少专门的"Agent 端到端成功率"指标——即从 query 到最终回答的完整通过率（包括工具调用是否成功、校验是否通过）。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** Agent 评测需覆盖三个维度：① **任务成功率**（端到端完成任务的比例，按任务类型分组）；② **工具调用准确率**（选对工具+参数正确的比例）；③ **安全性指标**（幻觉率、危险操作拦截率、injection 攻击防御成功率）。评测方法：离线用 golden set 自动化 → 在线 A/B Test 看业务指标 → 人评抽样校准 LLM-as-Judge。

##### Q7: Agent 权限、安全控制与 Guardrails [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 9/10）：** 项目实现多层安全防护（§8.3-8.5）：① **工具安全分级**：Safe/Sensitive/Dangerous 三级（§8.3），不同等级不同审计强度+确认要求+频率限制；② **权限下推到存储层**：向量检索和关键词检索都带 tenant_id 过滤（§14.1）；③ **参数外部校验**：Tool Executor 在调用前校验参数（§8.4），不信任 LLM 输出的参数；④ **Guardrails**：Verifier Module（§4.5）作为最后一道防线，规则检查+LLM-Judge 双重校验。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** Guardrails 应覆盖三阶段：① **输入 Guard**：敏感内容过滤 + Prompt 注入检测 + 越权意图识别；② **过程 Guard**：工具调用前参数校验 + 权限检查 + 操作审计；③ **输出 Guard**：事实性校验 + 敏感信息脱敏 + 格式合规检查。核心原则：不信任 LLM 的任何输出，所有外部操作必须经过独立的规则引擎审批。

---

---

## 5. RAG 检索引擎

### 5.1 整体流水线

```
文档导入 → 预处理 → 分块 → 向量化 → 存储(Milvus) → 检索 → 重排序 → 返回
  │         │       │       │         │            │        │
  │    清洗控制字符 段落分割  BGE-M3   向量索引     混合检索  交叉编码器
  │    提取元数据   语义边界  (本地)                (向量+关键词) 重打分
  │    中文标点统一
```

### 5.2 文档加载器 (Document Loader)

**文件：** `rag/document_loader.py`

```python
def load_markdown_files(docs_dir=None) -> list[dict[str, str]]:
    """加载 data/docs/ 下的所有 .md 文件"""
    for md_path in sorted(docs_dir.glob("*.md")):
        content = md_path.read_text(encoding="utf-8")
        documents.append({
            "filename": md_path.name,
            "source": str(md_path),
            "content": content,
        })
```

- 路径解析基于模块位置（不依赖 CWD）
- 自动跳过空文件
- 返回结构化 dict 列表（filename + source + content）

### 5.3 文档预处理 (Preprocessing)

**文件：** `rag/preprocessing.py`

```python
def clean_text(text: str) -> str:
    """清洗控制字符、规范化空白、统一中文标点"""
    # 移除零宽字符、控制字符
    # 规范化换行（多个空行→2个）
    # 统一中文标点到全角
    # 非 ASCII 引号统一为中文引号
```

```python
def extract_metadata(content: str, source: str = "") -> dict:
    """提取文档元数据：标题、章节、字数、关键词"""
    # 提取首个 # 标题
    # 统计二级标题数量
    # 基于 TF（词频）提取 top-5 关键词
```

**元数据返回结构：**
```json
{
  "title": "API 认证说明",
  "sections": ["概述", "认证方式", "Token 管理"],
  "section_count": 11,
  "word_count": 3245,
  "keywords": ["认证", "Token", "API", "密钥", "OAuth"]
}
```

### 5.4 文档分块器 (Text Splitter)

**文件：** `rag/splitter.py`

采用**段落分割**策略（`rag/splitter.py` 的 `split_text` 函数，按双换行 `\n\n` 切分）：

```
┌──────────────────────────────────────────────┐
│ 1. 按 ## 二级标题分割（保留文档结构）         │
│    ↓ 块过大                                   │
│ 2. 按段落边界分割（保留语义完整性）           │
│    ↓ 块仍过大                                 │
│ 3. 按句子边界分割（尽量在标点处断开）         │
│    ↓ 仍无法分割                               │
│ 4. 字符级强制分割（保证不超过 chunk_size）    │
└──────────────────────────────────────────────┘
```

```python
@dataclass
class Chunk:
    chunk_id: str       # "sample_policy.md_2"
    content: str        # 块文本
    source: str         # 源文件路径
    section: str        # 所属章节标题
    chunk_index: int    # 块在文档中的序号
    metadata: dict      # 携带文档级元数据
```

**关键参数：**
- `chunk_size=500`：每个块约 500 字符
- `chunk_overlap=0`：当前实现不做重叠（`split_text` 函数中 `chunk_overlap` 参数标注为 "reserved for future use"，实际未启用）

---

#### 📋 面试题追加（STAR 结构化）：文档分块（Chunking）策略

> 以下面试题按 **STAR 法则**组织：**S** (情境) → **T** (任务) → **A** (行动) → **R** (结果)。项目相关答案基于 Enterprise Hybrid RAG 源码实现。

> 以下面试题按重要性排列，结合本项目给出答案、评分与满分答案。

**匹配到的面试题：**

| 题目 | 重要性 |
|------|--------|
| Chunk 切分策略与语义完整性 | S |
| 你实际项目中 Chunk 大小是怎么确定的？有没有做过对比实验？ | A |
| 语义切分具体怎么做？有什么开源工具？ | A |
| 如果文档是表格或图片混排的，Chunk 怎么切？ | A |
| Chunk 优化思路是什么？ | A |
| 文档切割策略有哪些？怎么保障语义完整性？ | B |
| RAG 的 chunk 划分策略是什么？ | S |
| 做Rag时候的分块策略 | S |
| 对于RAG中的文档，通常采用哪些策略进行分块（chunk）？ | S |
| GraphRAG的chunk划分与传统RAG有何不同？ | S |
| RAG 切片实现方法：如何设计和优化切片过程？ | S |

##### Q1: Chunk 切分策略与语义完整性 [S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 采用**段落分割**策略（`rag/splitter.py` 的 `split_text` 函数）。按双换行（`\n\n`）将文档切分为段落，每个段落作为独立 chunk。`chunk_size` 默认 500 字符，`chunk_overlap` 参数定义但标注为 "reserved for future use"（实际未启用）。每个 Chunk 携带 `chunk_id`、`source`、`section`、`chunk_index` 和 `metadata` 元数据。


**📊 R — 结果与评分：** **答案评分：8/10** — 实现了分层递归切割+overlap+元数据注入，但未实现基于 Embedding 相似度的语义边界检测（按相邻句子 cos_sim 判断切分点），也未做 Parent-Child 分层索引（小 Chunk 检索+大 Chunk 供给生成）。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及本项目）：** ① 结构化文档按标题层级切，FAQ 按 Q&A 对切；② 非结构化文档用相邻句子 Embedding 余弦相似度检测语义边界（`cos_sim < 0.5-0.7` 时切分）；③ Parent-Child 索引：小 Chunk（~200 tokens）检索保证精度 → 命中后返回父级大 Chunk（~1000 tokens）保证上下文完整；④ 文档类型感知：表格识别后转 Markdown 保留结构；⑤ 每个 Chunk 携带 metadata（source/doc_id/tenant_id/content_hash）支撑后续过滤和去重；⑥ 在金标集上验证 Recall@5。

##### Q2: Chunk 大小如何确定？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 选定 `chunk_size=500` 字符、`chunk_overlap=0`。500 字符约涵盖 1-2 个完整段落，既保证主题聚焦又不至于太碎片化。当前实现为简单段落分割（`split_text` 按 `

` 双换行切分），chunk_overlap 参数预留但未启用。


**📊 R — 结果与评分：** **答案评分：7/10** — 有明确的参数理由和设计意图，但未做系统性的对比实验（如 300/500/800/1000 字符的 Recall@5 对比）。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 在评测集上做 A/B 实验：`chunk_size ∈ {256, 512, 768, 1024, 1536}` 各跑 Recall@5 和 MRR；针对不同文档类型分别优化（FAQ 用 200-300、制度文档用 500-800、长教程用 1000-1500）；`chunk_overlap = max(chunk_size * 0.15, 50)` 自适应。

##### Q3: 语义切分具体怎么做？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 本项目按文档结构分层切分（标题→段落→句子→字符级），未使用基于 Embedding 的语义边界检测。


**📊 R — 结果与评分：** **答案评分：5/10** — 项目实现的是结构感知切分，非真正的语义切分。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 核心思想：计算相邻句子的 Embedding 余弦相似度，当 `cos_sim(s_i, s_{i+1}) < threshold`（经验值 0.5-0.7）时在此处切分。将句子按顺序排列，找相似度局部极小值点作为切分边界。开源工具推荐：LangChain 的 `SemanticChunker`、LlamaIndex 的 `SentenceSplitter`。

##### Q4: 文档是表格或图片混排的 Chunk 怎么切？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 当前以 Markdown 文档为主，未做专门的表格/图片剪切处理。


**📊 R — 结果与评分：** **答案评分：4/10** — 项目当前未覆盖此场景。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** ① 表格识别：先用规则或模型检测表格区域 → 小表格转 Markdown 格式保留行列结构 → 大表格按行切分保证每行数据完整；② 图片处理：OCR 提取文字 → 用 VLM（如 GPT-4V）生成图片描述 Caption → Caption + OCR 文字一起编码；③ 图文混排：按自然阅读顺序提取文本，图片位置插入 Caption 占位，保持上下文连贯。

##### Q5: GraphRAG 的 chunk 划分与传统 RAG 有何不同？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 项目当前为标准 RAG，未使用 GraphRAG。两者核心区别在于：标准 RAG 按文档线性切块，Chunk 之间无显式关系；GraphRAG 需要构建实体关系图，Chunk 划分围绕实体（Entity）和社区（Community）进行，每个 Chunk 携带实体关联信息。


**📊 R — 结果与评分：** **答案评分：6/10** — 能清晰解释差异但项目未实践。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** GraphRAG 的 Chunk 划分核心差异：① 不是简单按字符/段落切，而是先做实体识别和关系抽取，将文档转化为 (实体, 关系, 实体) 三元组；② Chunk 围绕"实体社区"组织——同一社区的实体及其关联文本构成一个 Chunk；③ 元数据层面携带实体 ID 和关系类型，检索时可做图遍历扩展（多跳检索）。

---

### 5.5 向量嵌入 (Embedding)

**文件：** `rag/embedding_provider.py`

```python
class EmbeddingProvider:
    """本地 BGE-M3 嵌入模型（通过 FlagEmbedding 加载）"""

    def __init__(self, model_name="BAAI/bge-m3"):
        self.model = SentenceTransformer(model_name)
        self.dimension = 1024  # BGE-M3 输出维度

    def encode(self, texts: list[str]) -> list[list[float]]:
        # 本地推理，无 API 调用
        # normalize_embeddings=True（余弦相似度）
```

**为什么选择 BGE-M3？**
- 支持中英双语，适合企业混合语言场景
- 1024 维向量，在精度和存储间取得平衡
- 支持 dense + sparse 混合检索（虽然本项目当前只用 dense）
- 本地运行，无外部 API 依赖

**降级策略：**
- BGE-M3 加载失败时自动回退到 `RandomEmbeddingProvider`（随机向量）
- 保证系统可用性（Mock 模式下仍可运行）

---

#### 📋 面试题追加（STAR 结构化）：Embedding 模型选型与优化

> 以下面试题按 **STAR 法则**组织：**S** (情境) → **T** (任务) → **A** (行动) → **R** (结果)。项目相关答案基于 Enterprise Hybrid RAG 源码实现。

| 题目 | 重要性 |
|------|--------|
| Embedding 模型选型、评估与召回优化 | A |
| 你在项目中具体用的哪个 Embedding 模型？为什么选它？ | A |
| Embedding 模型的维度越高效果一定越好吗？ | A |
| 微调 Embedding 模型时难负样本怎么构造？ | A |
| bge-m3模型的训练过程、loss设计等 | B |
| 现在的embedding模型有哪些问题？怎么改进？ | A |
| 嵌入模型为什么选 BGE？FAISS 索引如何构建？ | A |
| 向量模型怎么微调？ | A |

##### Q1: 为什么选 BGE-M3？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 通过 `SentenceTransformer` 本地加载 `BAAI/bge-m3`：① 中英双语支持，适合企业混合语言文档；② 1024 维向量，精度与存储间平衡；③ 支持 dense+sparse 混合表示；④ 本地零 API 成本，`normalize_embeddings=True` 配合余弦相似度；⑤ 降级：加载失败 → `RandomEmbeddingProvider`。


**📊 R — 结果与评分：** **答案评分：8/10** — 覆盖了关键选型维度（语言/维度/成本/降级），但未与其他候选模型做系统对比评测。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 在项目评测集上对比 ≥3 个候选模型（BGE-M3、GTE-Qwen2-7B、text-embedding-3-large），评测维度包括 Recall@5、MRR、推理延迟(p50/p99)、GPU 显存。选型矩阵需综合考虑：中英双语能力 > 本地零成本 > 社区活跃度 > 推理吞吐。

##### Q2: Embedding 模型维度越高效果一定越好吗？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（项目相关）：** 本项目用 1024 维（BGE-M3 默认输出维度）。更高维度理论上能编码更多信息但存在边际递减效应，且检索延迟和存储成本线性增加。实践上 768-1536 维是大多数场景的最优区间。


**📊 R — 结果与评分：** **答案评分：7/10** — 正确阐述了原理，但未在本项目中做维度对比实验。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** ① 维度与性能关系：1024 vs 768 通常有约 2-5% 的 Recall 提升，1024 vs 1536 提升 <1%；② 维度与成本：存储和检索延迟与维度正比；③ Matryoshka 表示学习允许从高维向量中截取前 N 维使用，无需重新训练；④ 建议在目标场景做维度 ablation study 找到最优平衡点。

##### Q3: 现在的 Embedding 模型有哪些问题？怎么改进？[A]

**答案评分：6/10（项目层面）** — 项目靠混合检索补偿 Embedding 的精确匹配不足，但未解决模型本身问题。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** ① 领域术语覆盖不足 → 在领域数据上用 contrastive loss 微调；② 长文本编码退化 → 用支持 32K+ 的长文本模型或分段编码+池化；③ 多语言混合质量不稳定 → 选多语言模型（BGE-M3、Multilingual-E5）；④ 微调时需要构造难负例（Hard Negative Mining）：用当前模型检索 top-20，人工或自动标注哪些是"看起来相关但实际不相关"的文档作为负例。

##### Q4: Embedding 模型选型评估与召回优化 [A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 项目选型考量（§5.5）：① 中英双语能力（企业文档中英混排）；② 本地部署零成本（SentenceTransformer 加载 BAAI/bge-m3）；③ 1024 维平衡精度与性能；④ `normalize_embeddings=True` 配合 COSINE 距离。降级策略：模型加载失败 → RandomEmbeddingProvider（SHA256 确定性伪向量）。召回优化靠混合检索互补（BM25 覆盖精确匹配、BGE-M3 覆盖语义匹配），而非单方面调 embedding。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 选型评估流程：① 用 MTEB 排行榜初筛候选（BGE-M3、GTE-Qwen2、E5-Mistral）；② 在自己的评测集上测 Recall@5、MRR、NDCG；③ 测推理吞吐（tokens/sec）、GPU 显存、批处理能力；④ 做维度 ablation（512/768/1024/1536）找最优性价比。召回优化：混合检索 + Query Rewrite + HyDE（生成假设答案辅助检索）三者组合通常比单改 embedding 提点更多。

##### Q5: 你在项目中具体用的哪个 Embedding 模型？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 9/10）：** 使用 **BAAI/bge-m3**，通过 `sentence-transformers` 库本地加载（`rag/embedding_provider.py`）。核心参数：`normalize_embeddings=True`、batch_size=32、device=cpu（M5 Mac 上可用 MPS 加速但当前用 CPU 保证兼容性）。选型理由见 Q1（中英双语、1024 维、本地零成本）。降级：模型文件缺失 → `RandomEmbeddingProvider`（SHA256 确定性伪向量）。项目未使用 FAISS——向量索引由 Milvus 管理（HNSW 索引），Embedding 模型只负责文本→向量转换。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 同 Q1 满分答案中关于 BGE-M3 与其他候选模型的对比评测部分。

##### Q6: 微调 Embedding 时难负样本怎么构造？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 6/10）：** 项目使用预训练 BGE-M3 未做微调，靠混合检索（BM25+向量）补偿 Embedding 的精确匹配不足。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 难负例挖掘（Hard Negative Mining）四步法：① 用当前最优模型检索每个 query 的 Top-20；② 人工标注：相关→正例，表面相似但无关→难负例，明显无关→普通负例；③ 构造 triplet：(query, positive, hard_negative)，用 contrastive loss（如 InfoNCE）微调；④ 迭代：每轮微调后用新模型重新检索 → 挖掘新的难负例 → 持续 2-3 轮。成本优化：可用 LLM 辅助标注（"这篇文档是否回答了 query？"），人工只审核边界 case。

##### Q7: BGE-M3 训练过程与 Loss 设计 [B]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 6/10）：** 项目使用 BGE-M3 预训练模型加载后直接推理，未涉及训练过程。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** BGE-M3 训练三阶段：① **RetroMAE 预训练**：用 [CLS] 向量重建被 mask 的输入文本（自编码），学到通用语义表示；② **对比学习微调**：在 10 亿+ 中英双语 pair 数据上用 InfoNCE loss，正例 pair 拉近、batch 内负例推开；③ **多向量蒸馏**：同时优化 dense（1024 维）、sparse（词权重向量）、colbert（token 级交互）三个表示空间，用 KL 散度互蒸馏。Loss = α·L_dense + β·L_sparse + γ·L_colbert + δ·L_distill。关键 trick：hard negative mining + in-batch negatives + cross-batch negatives（GradCache 增大有效 batch size）。

##### Q8: 向量模型怎么微调？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 6/10）：** 项目未对 Embedding 模型做微调。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** 微调流程：① 数据准备：从知识库抽取 (query, positive_doc) pair（可用用户点击日志、FAQ 的 Q&A 对、或用 LLM 为每个文档生成多个可能的问题）；② 负例构造：随机采样普通负例 + Hard Negative Mining 难负例（见 Q5），正负比通常 1:3~1:7；③ 训练：用 Sentence-Transformers 的 `InformationRetrievalEvaluator` + `CosineSimilarityLoss` 或 `MultipleNegativesRankingLoss`；④ 评估：在验证集上测 Recall@K 和 NDCG，确认有正向提升；⑤ 部署：替换原始模型权重，跑回归评测确保不引入退化。

---

### 5.6 混合检索器 (Retriever)

**文件：** `rag/retriever.py`

```python
class Retriever:
    def __init__(self, chunk_size=500, top_k=5):
        self._embedder = get_embedding_provider()        # BGE-M3
        self._milvus = MilvusStore()                     # 向量存储
        self._es_keyword = ESKeywordStore()               # ES IK分词关键词检索
        self._mem_keyword = KeywordRetriever(chunk_size, top_k)  # 内存 Jaccard 终极兜底
```

**四级降级检索链：**

```
① Fusion: Milvus 向量 + ES 关键词 → Weighted RRF
  ├─ ES 不可用 ──→ ② Milvus-only 向量检索
  │    └─ Milvus 不可用 ──→ ③ ES-only 关键词检索 (IK Analyzer + BM25)
  │         └─ ES 不可用 ──→ ④ 内存 Jaccard 检索 (终极兜底，永不失败)
```

**融合流程详解：**

```
                    query (改写后)
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
  ┌───────────────┐            ┌───────────────────┐
  │  向量检索      │            │  ES 关键词检索      │
  │  (Milvus)     │            │  (IK Analyzer)    │
  │               │            │                   │
  │ BGE-M3 编码   │            │ ik_max_word 索引   │
  │ COSINE 相似度 │            │ ik_smart 搜索      │
  │ top_k=5       │            │ BM25 评分          │
  └───────┬───────┘            └─────────┬─────────┘
          │                             │
          │  vector_results             │  keyword_results
          └──────────────┬──────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  Weighted RRF Fusion         │
          │  vector_weight  = 0.6        │
          │  keyword_weight = 0.4        │
          │  k = 60                      │
          └──────────────┬───────────────┘
                         │
                         ▼
                融合 + 去重(按source) → top_k=5
```

**ES 不可用时的降级路径：**
`fusion_retrieve()` 中 ES 不可用时自动回退到内存 `KeywordRetriever` 做 Jaccard 检索，确保融合链路始终可用。

**评分阈值：**
- 所有文档 score < 0.1：触发 `low_retrieval_score` fallback
- 无结果或全零分：触发 `no_relevant_docs` fallback

### 5.7 向量存储 (Milvus)

**文件：** `rag/milvus_store.py`

```python
class MilvusStore:
    collection: str = "enterprise_kb"
    dimension: int = 1024

    def search(self, query_vector, top_k=10, filter_expr=None):
        """向量相似度搜索，支持 metadata 过滤"""
        # Milvus 原生 HNSW 索引
        # 支持按 source/department/security_level 等元数据过滤

    def insert(self, chunks, embeddings):
        """批量插入向量，自动创建索引"""
```

**降级策略：**
- Milvus 不可用时自动回退到 `MemoryVectorStore`
- 内存存储基于余弦相似度的暴力搜索

---

#### 📋 面试题追加（STAR 结构化）：混合检索、Rerank 与向量数据库选型

> 以下面试题按 **STAR 法则**组织：**S** (情境) → **T** (任务) → **A** (行动) → **R** (结果)。项目相关答案基于 Enterprise Hybrid RAG 源码实现。

| 题目 | 重要性 |
|------|--------|
| Hybrid Search、BM25、RRF 与多路召回融合 | S |
| 混合检索一定比单路检索好吗？ | S |
| 多路召回怎么融合？RRF公式怎么写？ | S |
| Recall 与 Rerank：两阶段检索为什么必要 | S |
| Bi-Encoder 和 Cross-Encoder 模型结构的区别？ | S |
| 如果不加 Rerank 直接增大召回数量能不能替代？ | S |
| 召回后有没有做Rerank？为什么选Rerank？ | S |
| 向量数据库选型：Milvus vs Qdrant vs ES | S/A |
| HNSW 和 IVF 索引的原理与差异 | A/B |
| 向量检索的准召率如何保障？ | A |
| 向量数据库的元数据过滤怎么实现？ | B |
| 数据量从十万到十亿级怎么演进？ | A |

##### Q1: 本项目混合检索如何实现？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 采用 **Weighted RRF 融合** + 四级降级检索链（`rag/retriever.py`）：
```
① Fusion: Milvus 向量(BGE-M3编码, COSINE相似度) + ES 关键词(IK分词, BM25) 
   → Weighted RRF (vector_weight=0.6, keyword_weight=0.4)
  ├─ ES 不可用 → ② Milvus-only 向量检索
  │    └─ Milvus 不可用 → ③ ES-only 关键词检索
  │         └─ ES 不可用 → ④ 内存 Jaccard 检索 (终极兜底)
```

**RRF 公式（项目实际使用）：** `RRF(d) = Σ 1/(k + rank_i(d))`，其中 k=60 为平滑常数。融合分数 = 0.6×RRF_vector(d) + 0.4×RRF_keyword(d)。vector_weight=0.6 因为向量检索覆盖面广（语义匹配），keyword_weight=0.4 补全精确匹配缺口（产品型号、错误码等）。


**📊 R — 结果与评分：** **答案评分：9/10** — 实现了完整的混合检索+四级降级+加权RRF融合，参数有明确设计理由。扣1分因为未做 weight 对比调优实验。

##### Q2: 为什么需要 Recall+Rerank 两阶段检索？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** Recall 阶段用轻量 Bi-Encoder（BGE-M3）做语义召回+BM25 关键词召回，保证高覆盖率；Rerank 阶段需要 Cross-Encoder 做精细打分但本项目未集成专用 Reranker 模型，而是通过 RRF 融合分数排序后取 Top-5。


**📊 R — 结果与评分：** **答案评分：7/10** — 正确解释了两阶段原理，但项目实际未使用 Cross-Encoder Reranker（如 bge-reranker-v2-m3）。

**Bi-Encoder vs Cross-Encoder 区别：** Bi-Encoder（如 BGE-M3）将 query 和 doc 分别独立编码为向量，检索时只需向量相似度计算（快但精度有限）；Cross-Encoder（如 bge-reranker）将 query+doc 拼接后完整过 Transformer，做精细的相关性判断（精度高但计算量大，只能用于小候选集）。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** ① 召回 Top-50~100 → bge-reranker-v2-m3/Cohere Rerank 重打分 → Top-5 送 LLM；② Rerank 候选集大小需要在精度和延迟间权衡；③ 评测驱动优化：在固定评测集上对比加/不加 Rerank 的 Recall@5 和 Faithfulness 变化。

##### Q3: 向量数据库为什么选 Milvus？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案：** 选 Milvus v2.4 Standalone：① 企业级 HNSW 索引（ANN 搜索毫秒级）；② 支持元数据过滤（按 source/department/security_level）；③ 内置 COSINE/IP/L2 距离度量；④ 降级策略：Milvus 不可用 → MemoryVectorStore（余弦相似度暴力搜索）。


**📊 R — 结果与评分：** **答案评分：8/10** — 有明确选型理由+降级策略。

**Milvus vs Qdrant vs ES 对比：**

| 维度 | Milvus | Qdrant | Elasticsearch |
|------|--------|--------|---------------|
| 定位 | 专业向量数据库 | 向量数据库+Payload过滤 | 全文搜索引擎+向量扩展 |
| ANN 算法 | HNSW/IVF/DiskANN | HNSW（核心算法） | HNSW（8.x+ 引入） |
| 过滤能力 | Scalar 字段过滤 | Payload 过滤（灵活） | 最强的全文过滤+聚合 |
| 部署 | 较复杂（需 etcd/MinIO） | 轻量（单二进制） | 资源消耗大 |
| 生态 | 模型+评测工具链丰富 | API 设计优雅 | ELK 生态成熟 |
| 适用场景 | 纯向量+大规模 | 向量+灵活元数据 | 文本搜索为主+向量为辅 |

**本项目选择 Milvus 而非 ES 做向量的原因：** ES 的向量功能是 8.x 新增，HNSW 索引规模和查询延迟不及专业向量数据库。项目保留 ES 做关键词检索（BM25+IK），Milvus 专门做向量检索，各司其职。

##### Q4: 混合检索一定比单路检索好吗？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 不一定。项目的实际教训：在 ES 或 Milvus 不可用时，单路检索（纯向量或纯 BM25 或 Jaccard）作为降级路径仍有价值（§5.6 四级降级链）。混合检索的优势在**互补场景**最明显：用户问"9568321 错误怎么修"→ BM25 精确命中错误码 + 向量理解"怎么修"的语义 → 融合后效果最好。但在**纯精确匹配**场景（如搜"onCreate"）混合检索可能引入语义相关但无关的噪音。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** 关键不是"混合 vs 单路"，而是"召回源是否互补"。两路高度重叠的召回源融合效果提升有限。衡量互补性：计算两路 Top-20 结果的 Jaccard 相似度，< 0.3 说明互补性好，混合才有意义。实践中推荐 2-3 路（关键词+向量+可选的图谱），超过 3 路边际收益小。

##### Q5: 多路召回怎么融合？RRF 公式怎么写？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 9/10）：** 项目使用 Weighted RRF（§5.13.3，§5.6）：
```
RRF(d) = Σ w_s / (k + rank_s(d))
```
其中 s ∈ {keyword, vector, graph}，k=60（平滑常数），w_s 为各源权重。融合分 = 0.6×RRF_vector(d) + 0.4×RRF_keyword(d)（两路时）或 0.5×RRF_graph + 0.3×RRF_vector + 0.2×RRF_keyword（graph_first 三路时）。

**为什么是 k=60？** k 控制排名的影响程度：k 越小排名越重要（top-1 和 top-10 差异更大），k 越大越平滑。60 是业界经验值（来自论文），平衡了"top 结果应有优势"和"不能完全忽略中后段结果"。

**其他融合方式对比：**
| 方式 | 优点 | 缺点 |
|------|------|------|
| RRF | 无需归一化，跨源可比 | 丢失绝对分数信息 |
| 分数归一化 | 保留分数量级 | 需各源有可比分数，归一化方法敏感 |
| Learnt Fusion | 最优理论效果 | 需要训练数据，过拟合风险 |

##### Q6: Bi-Encoder 和 Cross-Encoder 模型结构的区别？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 项目 Recall 阶段用 Bi-Encoder（BGE-M3：query 和 doc 独立编码→余弦相似度），Rerank 阶段实际上未集成 Cross-Encoder，仅用 RRF 融合分数排序后取 Top-5。这是项目当前的一个能力缺口。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：**
| 维度 | Bi-Encoder | Cross-Encoder |
|------|-----------|---------------|
| 编码方式 | query 和 doc **独立**编码为向量 | query 和 doc **拼接**后一起过 Transformer |
| 交互 | 无 token 级交互（只在相似度计算时交互） | 全 token 级交叉注意力 |
| 速度 | 快（doc 向量可预计算，检索时只算 query） | 慢（每对 query-doc 都要完整前向） |
| 精度 | 中 | 高（通常 MRR 提升 5-15%） |
| 典型模型 | BGE-M3, text-embedding-3 | bge-reranker-v2-m3, Cohere Rerank |
| 适用位置 | Recall 阶段（Top-50~100 候选） | Rerank 阶段（Top-5~10 精选） |

##### Q7: 不加重排直接增大召回数量能替代 Rerank 吗？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 不能。项目的实际经验：增大 Top-K 虽然让"正确文档在候选集中"的概率变高，但也会引入更多噪声文档稀释 LLM 的注意力（Lost in the Middle 现象，§7.5）。Top-5 中包含 1 个正确文档 vs Top-20 中包含 1 个正确文档但混入 19 个噪声——前者的 LLM 回答质量通常更高。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** 实验数据表明：Top-5 经 Cross-Encoder Rerank > Top-20 经 RRF 融合 > Top-5 不经 Rerank > Top-20 不经 Rerank。原因是 LLM 的注意力机制对输入位置敏感（中间位置的文档容易被忽略），且过多文档消耗 token 预算。Rerank 的核心价值：在送 LLM 之前做高质量筛选，而非简单扩大候选集。

##### Q8: 召回后有没有做 Rerank？为什么选 Rerank？[S]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 项目当前未集成专用 Reranker 模型（如 bge-reranker-v2-m3），而是通过 Weighted RRF 融合分数做排序后取 Top-5（§5.6）。这属于"轻量排序"而非真正的 Cross-Encoder Rerank。原因：开发阶段优先保证链路的完整性和稳定性，Rerank 作为精度优化在第二阶段引入。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：** Rerank 的必要性判断：① 如果 RRF 融合后 Top-5 中正确文档的 MRR > 0.8（即正确答案大部分在 Top-2），则 Rerank 收益有限；② 如果正确答案散布在 Top-5~20 中，则 Cross-Encoder Rerank 可显著提升 Top-5 精度（通常 MRR 提升 10-20%）。选型建议：bge-reranker-v2-m3（中文效果好、本地部署）、Cohere Rerank（多语言 SOTA、API 调用）、ColBERT（token 级交互精度最高但延迟大）。

##### Q9: HNSW 和 IVF 索引的原理与差异 [A/B]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 6/10）：** 项目使用 Milvus 默认的 HNSW 索引，主要关注点是建索引和查询参数调优（§5.7），未做 IVF 对比实验。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案（不涉及项目）：**
| 维度 | HNSW（分层可导航小世界图） | IVF（倒排文件索引） |
|------|--------------------------|-------------------|
| 原理 | 构建多层图结构，搜索时从顶层粗粒度向下层细粒度导航 | 先 K-Means 聚类→搜索时只查最近 N 个聚类中心 |
| 建索引速度 | 慢（需构建多层图） | 快（只需做一次 K-Means） |
| 查询速度 | 快（图导航 O(log N)） | 中（取决于 nprobe 参数） |
| 召回率 | 高（参数 ef 调大可接近暴力搜索） | 中高（nprobe 越大越准越慢） |
| 内存占用 | 高（图结构 + 原始向量） | 中（聚类中心 + 原始向量） |
| 增量插入 | 支持 | 需定期重建索引 |
| 适用场景 | 查询性能优先、数据相对静态 | 插入频繁、内存受限 |

**本项目选择 HNSW 的理由：** 企业知识库数据量中等（万级~十万级），查询延迟要求高（P99 < 100ms），数据更新频率低（小时级 cron 触发），HNSW 的查快建慢正合适。

##### Q10: 向量检索的准召率如何保障？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 项目从三个层面保障：① **混合检索互补**：向量覆盖语义、BM25 覆盖精确匹配（如错误码），两者融合减少漏召回（§5.6）；② **Chunk 策略**：500 字符段落分割（`chunk_overlap=0`，当前未启用重叠）（§5.4），保证语义单元不被切碎，提升检索精度；③ **评测驱动**：离线 RAG 评估器持续监测 Recall@5、MRR（§11.3），发现退化立即回归定位。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** 保障准召率的系统性方法：① Embedding 质量保证（选型评测 + 领域数据微调）；② 多路召回互补（关键词+向量+图谱，≥2 路）；③ Chunk 策略调优（大小/重叠/语义边界）；④ Rerank 精排（Cross-Encoder 去噪）；⑤ Query 理解（Rewrite/Expansion/HyDE 提升表达质量）；⑥ 评测闭环（离线 golden set + 线上 A/B）。

##### Q11: 向量数据库的元数据过滤怎么实现？[B]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 8/10）：** 项目通过 Milvus REST API 的 `filter` 参数实现元数据过滤（§5.11.4）：`filter = 'source == "api_auth.md"'` 或 `filter = 'tenant_id == "tenant_001"'`。Milvus 支持在 ANN 搜索前先用标量字段做预过滤，缩小搜索空间。关键保障：所有 chunk 在写入 Milvus 时都携带 `tenant_id`、`source`、`department` 等元数据字段（§5.11.4 upsert_chunks）。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** 两种过滤模式：① **Pre-filtering**（先过滤再搜索）—— 保证过滤条件 100% 满足，但如果过滤后候选太少可能漏召回；② **Post-filtering**（先搜索再过滤）—— 保证候选数量，但可能过滤后结果不足 Top-K。Milvus 默认 pre-filtering。多租户场景必须在向量检索和关键词检索都下推 tenant_id 过滤（§14.1），不能只在应用层做。

##### Q12: 数据量从十万到十亿级怎么演进？[A]


**🎯 S/T/A — 项目实战（情境/任务/行动）：**
**本项目答案（评分 7/10）：** 项目当前面向十万级数据，已有演进预留：Milvus 支持分布式部署（Proxy + Query Node + Data Node + Index Node），从 Standalone 可平滑迁移到 Cluster 模式；ES 支持分片扩展。但未做实际的规模化压测。


**📖 通用满分答案（独立于项目，可迁移到其他面试）：**
**满分答案：** 规模演进路径：① 十万级 → 单机 Milvus Standalone + HNSW（当前）；② 百万级 → 内存优化（PQ 量化压缩 4-8x）+ 索引参数调优；③ 千万级 → Milvus Cluster（计算存储分离）+ ES 分片到 5-10 节点；④ 亿级以上 → 分层索引（热数据 HNSW + 冷数据 DiskANN）+ 分区路由（按时间/租户）+ GPU 加速检索（RAFT）。每个阶段的瓶颈不同：十万级瓶颈在 Chunk 质量，百万级瓶颈在索引内存，亿级瓶颈在分布式一致性。

---

| 维度 | Milvus | Qdrant | ES |
|------|--------|--------|-----|
| 向量检索性能 | ★★★★★ HNSW | ★★★★ | ★★★ (需 dense_vector) |
| 混合检索 | 需配合 ES | 原生支持 | ★★★★★ |
| 元数据过滤 | ★★★★ | ★★★★ | ★★★★★ |
| 运维复杂度 | 中 | 低 | 高 |
| 本项目适用性 | 向量为主 | 混合优先 | 关键词为主 |

**HNSW vs IVF 索引原理：**
- **HNSW**（分层导航小世界图）：Layer0 稀疏长跳跃快速定位区域 → 下层密集精确搜索。精度高但内存占用大。
- **IVF**（倒排索引）：先粗量化找最近聚类中心 → 在聚类内暴力搜索。速度快但精度取决于聚类质量。

---

### 5.8 ES IK Analyzer 中文分词方案详解

#### 5.8.1 为什么选择 IK Analyzer

Elasticsearch 默认的 `standard` 分词器对中文支持极差——它按**单个汉字**切分，导致：
- "认证方式" → `["认", "证", "方", "式"]`（丢失语义）
- 搜索 "认证" 无法匹配含 "身份验证" 的文档（缺少语义关联）

IK Analyzer 是 Elasticsearch 社区最广泛使用的中文分词插件，核心优势：
- **词典驱动**：内置 27 万+ 中文词条，支持自定义词典热更新
- **双模式策略**：`ik_max_word`（细粒度索引）+ `ik_smart`（粗粒度搜索）互补
- **8.x 兼容**：支持 ES 8.17 版本

#### 5.8.2 双分析器策略（经 ES 8.17 + IK 8.17 实测验证）

```
索引阶段 (ik_max_word)                    搜索阶段 (ik_smart)
─────────────────────                    ────────────────────
"中华人民共和国"                            "中华人民共和国"
     │                                         │
     ▼                                         ▼
9 个 token:                                 1 个 token:
  中华人民共和国                                 中华人民共和国
  中华人民                                    最粗粒度，一个完整词
  中华
  华人
  人民共和国
  人民
  共和国
  共和
  国
细粒度 → 任意子串都能命中                   粗粒度 → 保留完整短语语义
```

**实测 IK 分词效果（ES 8.17 + IK Analyzer 8.17，2026-06-02 实测）：**

| 原文 | ik_max_word (索引) | ik_smart (搜索) | 差异 |
|------|-------------------|-----------------|------|
| 中华人民共和国 | `["中华人民共和国","中华人民","中华","华人","人民共和国","人民","共和国","共和","国"]` (9) | `["中华人民共和国"]` (1) | **显著** — 细粒度产生 9 倍冗余 |
| API认证支持三种方式 | `["api","认证","支持","三种","三","种","方式"]` (7) | `["api","认证","支持","三种","方式"]` (5) | 中等 — ik_max_word 多了"三""种" |
| 认证方式 | `["认证","方式"]` (2) | `["认证","方式"]` (2) | 无 — 短词无冗余切分 |
| Bearer Token | `["bearer","token"]` (2) | `["bearer","token"]` (2) | 无 — 英文原样保留 |

> **实测关键发现**：
> - 对于简短中文词（如"认证方式"），两种模式结果**完全相同**，IK 词典已将"认证""方式"视为独立词条
> - 差异体现在**长复合词**（如"中华人民共和国"），ik_max_word 产生 9 个 token vs ik_smart 仅 1 个
> - 索引粒度优势：用户搜"华人"时，ik_max_word 索引的文档能被命中（因为索引时"中华人民共和国"→含"华人"token），而如果仅用 ik_smart 索引则搜不到
> - 这是**召回率 vs 精确率**的经典权衡：ik_max_word 索引增大 ~20-50% 索引大小，但保证长词子串可召回

#### 5.8.3 代码实现详解

**自定义分析器定义**（`es_keyword_store.py` 第 22-57 行）：

```python
_INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,      # 开发/单节点：1 个主分片足够
        "number_of_replicas": 0,     # 单节点无需副本（生产须 >=1）
        "analysis": {
            "analyzer": {
                "ik_index_analyzer": {           # 索引分析器
                    "type": "custom",
                    "tokenizer": "ik_max_word",  # 细粒度切分
                },
                "ik_search_analyzer": {          # 搜索分析器
                    "type": "custom",
                    "tokenizer": "ik_smart",     # 粗粒度切分
                },
            }
        },
    },
    "mappings": {
        "properties": {
            "content": {
                "type": "text",
                "analyzer": "ik_index_analyzer",       # 写入时用 ik_max_word
                "search_analyzer": "ik_search_analyzer", # 查询时用 ik_smart
            },
            "title": {
                "type": "text",
                "analyzer": "ik_index_analyzer",
                "search_analyzer": "ik_search_analyzer",
            },
            "source": {"type": "keyword"},        # 精确匹配，不分词
            "chunk_id": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "tenant_id": {"type": "keyword"},
        }
    },
}
```

**BM25 搜索实现**（第 226-297 行）：

```python
def search(self, query, top_k=5, filters=None):
    must_clauses = [{
        "multi_match": {
            "query": query,
            "fields": ["content^2", "title"],  # content 权重是 title 的 2 倍
            "type": "best_fields",             # 取最佳匹配字段的分数
        }
    }]
    # ... Bool Query: must(全文检索) + filter(租户/标签过滤, 不参与评分)
```

**搜索结果去重策略**：按 `source`（源文档）去重，避免同一文档的多个 chunk 占据全部 top_k 结果。

#### 5.8.4 检索链路中的定位

```
用户查询 "API认证方式"
     │
     ▼
query_rewriter → 改写为更精确的查询
     │
     ├──→ ES IK 关键词检索 (BM25)
     │      ik_smart: "API认证方式" → 搜索 token ["api","认证方式"]
     │      BM25 评分 → top_k=5 keyword_results
     │
     ├──→ Milvus 向量检索 (BGE-M3 + COSINE)
     │      语义相似度 → top_k=5 vector_results
     │
     └──→ Weighted RRF Fusion (vector 0.6 : keyword 0.4)
           去重(按 source) → 最终 top_k=5
```

#### 5.8.5 检查结果（2026-06-02 实测）

| 检查项 | 状态 | 实测数据 |
|--------|------|----------|
| IK Analyzer 插件安装 | ✅ 通过 | `analysis-ik 8.17.0` 通过 `elasticsearch-plugin install` 安装 |
| 双分析器策略 | ✅ 通过 | `ik_max_word` (索引) + `ik_smart` (搜索) 经 `_analyze` API 验证 |
| ik_max_word 细粒度效果 | ✅ 通过 | "中华人民共和国" → 9 tokens（含"华人""中华"等子词） |
| ik_smart 粗粒度效果 | ✅ 通过 | "中华人民共和国" → 1 token（最优切分路径） |
| 字段映射 | ✅ 通过 | `content` 和 `title` 使用 `ik_index_analyzer` / `ik_search_analyzer` |
| 单元测试 | ✅ 4/4 通过 | 优雅降级验证：ES 不可用时 search 返回 []、stats 返回 `available: False` |
| 集成测试 | ✅ 8/8 通过 | 索引创建、中文分词、增删查、租户过滤、结构验证 — `0.79s` 全部通过 |
| BM25 搜索 | ✅ 通过 | `multi_match` on `content^2 + title`，`best_fields` 策略 |
| 降级机制 | ✅ 通过 | ES 不可用时自动回退到内存 Jaccard 检索 |
| 端到端测试 | ✅ 通过 | FastAPI `/chat` 4 类查询（技术/故障/政策/权限）均返回真实数据 |
| `.env.example` | ✅ 已修复 | 已添加 `ES_HOST`/`ES_PORT`/`ES_INDEX`，Qdrant 变量替换为 Milvus |

### 5.9 关键词检索器（内存 Jaccard — 终极兜底）

**文件：** `rag/keyword_retriever.py` / `rag/retriever.py::KeywordRetriever`

```python
class KeywordRetriever:
    """终极兜底 — 内存 Jaccard 相似度检索，零外部依赖，永不失败"""
    def _score(self, query_tokens, chunk_text):
        # Jaccard: |query ∩ chunk| / |query|
        # 简单、快速、确定性，适合降级场景
```

**为什么需要两套关键词检索？**
- ES IK 分词：生产环境首选，中文语义感知，BM25 专业评分
- 内存 Jaccard：终极兜底（四级降级链的最底层），保证系统在 ES/Milvus 全挂时仍可运行
- 精确术语匹配（如错误码 "AUTH_401"、工单号 "TKT-001"）两种方案都能捕获
- 向量检索对此类结构化标识符不敏感，关键词检索是必要补充

### 5.10 对象存储 (MinIO)

**文件：** `rag/minio_store.py`

```python
class MinIOStore:
    """S3 兼容的对象存储，存放原始文档"""
    bucket: str

    def upload_document(self, file_path, object_name=None):
        """上传文档到 MinIO"""

    def download_document(self, object_name):
        """下载原始文档"""

    def list_documents(self, prefix=""):
        """列出存储桶中的文档"""
```

- 原始文档独立存储，与向量索引解耦
- 支持文档更新后重新分块/重新向量化
- 降级到本地文件系统

### 5.11 离线文档导入流水线 (Offline Ingestion Pipeline)

RAG 系统分为**在线（Online）**和**离线（Offline）**两套流程：

| 维度 | 在线流程 (Online) | 离线流程 (Offline) |
|------|-------------------|---------------------|
| **触发时机** | 每次用户请求 | 手动/定时脚本触发 |
| **核心动作** | query→embed→search→rerank→返回 | load→preprocess→split→dedup→embed→store |
| **参与者** | Retriever → Milvus | IngestionPipeline → Milvus + MinIO |
| **目标** | 毫秒级返回 top-k 相关文档 | 批量构建/更新向量索引 |
| **频率** | 高频（每次请求） | 低频（知识库更新时） |
| **入口** | `retrieve_knowledge` 节点 | `scripts/ingest_docs.py` |

#### 5.11.1 离线流水线 7 阶段全景

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    离线文档导入流水线 (Offline Ingestion Pipeline)              │
│                                                                             │
│  data/docs/*.md                                                             │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 1: 文档加载 (Document Loader)                                    │  │
│  │                                                                       │  │
│  │  load_markdown_files() → [{"filename", "source", "content"}, ...]    │  │
│  │  • 扫描 data/docs/ 下所有 .md 文件                                     │  │
│  │  • 按文件名排序（保证确定性）                                           │  │
│  │  • 跳过空文件                                                          │  │
│  │  • 无文件时提前返回 → IngestionReport(errors=["No markdown files"])    │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 2: 文档预处理 (Preprocessing)                                    │  │
│  │                                                                       │  │
│  │  clean_text() → 清洗控制字符、规范化空白、统一中文标点                    │  │
│  │  preprocess_document() → 返回结构化预处理结果:                          │  │
│  │    • cleaned: 清洗后文本                                               │  │
│  │    • sections: 章节结构 (Markdown # / 中文编号 / 数字编号)              │  │
│  │    • tables: 表格检测 (pipe table)                                     │  │
│  │    • images: 图片引用 ![]()                                            │  │
│  │    • citations: 引用标记 [1] /（年份）                                 │  │
│  │    • char_count: 字符统计                                              │  │
│  │    • title: 文档标题                                                   │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 3: 两层去重 (Two-Layer Deduplication)                           │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │ Layer 1: SHA256 精确哈希去重 (Fast Path)                         │ │  │
│  │  │                                                                  │ │  │
│  │  │  content_hash = sha256(content).hexdigest()[:16]                 │ │  │
│  │  │  if content_hash in seen_hashes: skip  ← O(1) 内存查找           │ │  │
│  │  │                                                                  │ │  │
│  │  │  适用场景: 完全相同的文档副本                                      │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                    │                                  │  │
│  │          SHA256 不重复              │                                  │  │
│  │                                    ▼                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │ Layer 2: 向量余弦相似度近重复检测 (Semantic Path)                  │ │  │
│  │  │                                                                  │ │  │
│  │  │  1. sample_doc_embedding(content):                               │ │  │
│  │  │     取文档 head(500字符) + tail(300字符) → embed → doc_vec        │ │  │
│  │  │                                                                  │ │  │
│  │  │  2. NearDedupIndex.detect(doc_vec):                              │ │  │
│  │  │     遍历已注册文档指纹, 计算 cosine_sim(vec, existing_vec)        │ │  │
│  │  │     if max_sim >= 0.95: → 判定为近重复, 跳过                      │ │  │
│  │  │                                                                  │ │  │
│  │  │  3. NearDedupIndex.register(doc_id, content, embedding):         │ │  │
│  │  │     通过后注册新指纹 → 内存 + Redis (TTL 30天)                    │ │  │
│  │  │                                                                  │ │  │
│  │  │  适用场景: 内容高度相似但非完全相同的文档 (如版本微调)              │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                       │  │
│  │  NearDedupIndex 存储策略:                                              │  │
│  │    Redis (主): dedup:doc:{id} Hash, dedup:hash:{hash} Set             │  │
│  │    内存 (降级): _fingerprints dict                                     │  │
│  │    JSON (冷启动): data/near_dedup_index.json                          │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 4: 文档分块 (Text Splitting)                                    │  │
│  │                                                                       │  │
│  │  split_documents(deduped_docs, chunk_size=500):                       │  │
│  │  • 段落分割: 按双换行(\n\n)切分为段落级 chunk                       │  │
│  │  • chunk_overlap = 0 (当前预留参数，未启用重叠)                          │  │
│  │  • 每个 chunk 注入:                                                    │  │
│  │      - tenant_id = "default"    (多租户预留)                           │  │
│  │      - doc_id = source 路径                                           │  │
│  │      - content_hash = sha256(chunk_content)[:16]                      │  │
│  │      - chunk_id = "{source}_{chunk_index}"                            │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 5: 向量嵌入 (Embedding)                                         │  │
│  │                                                                       │  │
│  │  embedder.embed([chunk.content for chunk in chunks]):                 │  │
│  │                                                                       │  │
│  │  EmbeddingProvider 选择 (EMBEDDING_PROVIDER 环境变量):                 │  │
│  │    "local"  → LocalEmbeddingProvider (sentence-transformers)          │  │
│  │               从 EMBEDDING_MODEL_PATH 加载本地模型                     │  │
│  │               batch_size=32, 返回 List[List[float]]                   │  │
│  │    "openai" → OpenAIEmbeddingProvider (text-embedding-3-small)        │  │
│  │    "mock"   → MockEmbeddingProvider (SHA256 确定性哈希向量)            │  │
│  │                                                                       │  │
│  │  失败处理: 嵌入失败 → 报告 error, 提前返回 (不损坏现有索引)            │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 6: MinIO 原始文档上传                                           │  │
│  │                                                                       │  │
│  │  for doc in raw_docs:                                                 │  │
│  │      minio.upload_document(source_path, object_name=filename)         │  │
│  │                                                                       │  │
│  │  • 上传到 MinIO bucket (默认: enterprise-rag-docs)                     │  │
│  │  • MinIO 不可用时静默跳过 (非致命错误)                                  │  │
│  │  • 记录 minio_uploaded 计数                                           │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Phase 7: Milvus 向量写入                                              │  │
│  │                                                                       │  │
│  │  if milvus.available:                                                 │  │
│  │      1. ensure_collection(collection_name):                           │  │
│  │          检查/创建集合 (dimension=VECTOR_SIZE, metric=COSINE)          │  │
│  │      2. upsert_chunks(chunks, vectors):                               │  │
│  │          逐条构建 payload: {id, vector, source, content, title, tags} │  │
│  │          POST /v2/vectordb/entities/insert                            │  │
│  │          返回 insertCount                                             │  │
│  │  else:                                                                │  │
│  │      报告 "Milvus unavailable — vectors not stored"                   │  │
│  │                                                                       │  │
│  │  • 主键: abs(hash(chunk_id)) % (2^63-1) → Int64                       │  │
│  │  • 通过 REST API 交互 (无 SDK 依赖)                                    │  │
│  │  • 支持按 source 过滤删除 → delete_by_source()                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│                          ┌─────────────────────┐                           │
│                          │   IngestionReport   │                           │
│                          │                     │                           │
│                          │  total_docs: N      │                           │
│                          │  total_chunks: M    │                           │
│                          │  minio_uploaded: X  │                           │
│                          │  milvus_upserted: Y │                           │
│                          │  errors: [...]      │                           │
│                          │  duration_ms: T     │                           │
│                          └─────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.11.2 两层去重策略详解

```python
class NearDedupIndex:
    """文档级语义指纹索引，用于近重复检测。

    双层检测：
      Layer 1 — SHA256 精确哈希: O(1) Redis Set 查找
      Layer 2 — 向量余弦相似度: NumPy 内存计算

    阈值: 0.95 (cosine_sim ≥ 0.95 判定为重复)
    TTL:  30 天 (适配月度重导入节奏)
    """

    def register(self, doc_id, content, embedding, metadata) -> bool:
        # 1. SHA256 精确哈希 → Redis O(1) 查找
        content_hash = sha256(content).hexdigest()[:16]
        if self.redis.exists(f"dedup:hash:{content_hash}"):
            return False  # 精确重复，跳过

        # 2. 向量余弦相似度 → NumPy 内存计算
        if embedding:
            vec = np.array(embedding, dtype=np.float32)
            for existing_id, fp in self._fingerprints.items():
                existing_vec = np.array(fp["embedding"], dtype=np.float32)
                sim = cosine_similarity(vec, existing_vec)
                if sim >= 0.95:  # 近重复阈值
                    return False

        # 3. 注册新指纹 → 内存 + Redis
        self._fingerprints[doc_id] = {...}
        self._save_redis(doc_id, content_hash, embedding, metadata)
        return True
```

**文档采样嵌入（`sample_doc_embedding`）:**
- 不嵌入整个文档（避免长文本稀释语义）
- 取 **head(500字符) + tail(300字符)** 拼接后编码
- 头部包含文档概要/标题/引言，尾部包含总结/版本信息
- 比全文档嵌入快 5-10 倍，同时保持去重准确度

#### 5.11.3 嵌入提供者策略

```python
# 工厂模式：通过环境变量切换
def get_embedding_provider() -> BaseEmbeddingProvider:
    provider_name = os.getenv("EMBEDDING_PROVIDER", "local").lower()

    if provider_name == "local":
        return LocalEmbeddingProvider(
            model_path=os.getenv("EMBEDDING_MODEL_PATH")
        )   # 本地 sentence-transformers 模型 (推荐)
            # batch_size=32, show_progress_bar=False

    if provider_name == "openai":
        return OpenAIEmbeddingProvider(
            model="text-embedding-3-small"
        )   # 1536 维, 需 API Key

    return MockEmbeddingProvider()
        # SHA256 确定性哈希 → 768 维伪向量
        # 用于开发/测试, 无需模型文件
```

**降级链:**

```
LocalEmbeddingProvider
  ├─ 模型路径存在 → SentenceTransformer 加载 → batch 推理
  ├─ 模型路径不存在 → logger.warning → 自动降级
  └─ 降级 ↓
MockEmbeddingProvider
  SHA256 哈希驱动, 确定性输出 (相同文本始终产生相同向量)
```

#### 5.11.4 Milvus 集合管理

```python
class MilvusStore:
    """通过 REST API 与 Milvus 交互 (无 SDK 依赖)"""

    def ensure_collection(self, collection_name) -> bool:
        # 1. GET /v2/vectordb/collections → 检查是否存在
        # 2. 不存在 → POST /v2/vectordb/collections/create
        #    payload: {collectionName, dimension, metricType: "COSINE",
        #              primaryField: "id", vectorField: "vector"}

    def upsert_chunks(self, chunks, vectors) -> int:
        # 主键: abs(hash(chunk_id)) % (2^63-1) → Int64
        # 字段: id, vector(768d), source, content, title, tags(JSON)
        # POST /v2/vectordb/entities/insert → insertCount

    def search(self, query_vector, top_k=5, filters=None):
        # POST /v2/vectordb/entities/search
        # 支持 metadata 过滤: filter = 'source == "api_auth.md"'
        # 返回: [{content, source, score(distance), chunk_id, metadata}]

    def delete_by_source(self, source) -> int:
        # POST /v2/vectordb/entities/delete
        # filter: 'source == "{source}"'
        # 用于文档更新时的"先删后插"策略
```

#### 5.11.5 运行导入

```bash
# 确保基础设施就绪
docker compose up -d milvus minio

# 执行导入
python scripts/ingest_docs.py

# 输出示例:
# ============================================================
#  Enterprise Hybrid RAG — Document Ingestion
# ============================================================
# 总文档数: 8
# 总切片数: 47
# MinIO 上传: 8
# Milvus 写入: 47
# 耗时: 2341.56ms
# ✓ Ingestion complete!
```

### 5.12 RAG 知识库更新策略（定时 + 实时）

> "知识库不是静态的——它应该像代码一样持续集成和部署。"

#### 5.12.1 双轨更新架构

```
                    ┌──────────────────────────────────────┐
                    │        RAG 知识库更新策略               │
                    └──────────────────┬───────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
    │  实时更新 (Watch) │    │  定时更新 (Cron)     │    │  手动更新 (CLI)   │
    │                  │    │                     │    │                  │
    │ 文件系统监听      │    │ crontab 定时触发      │    │ 运维人员主动触发   │
    │ SHA256 变更检测   │    │ smart/full 双模式     │    │ single 文档刷新    │
    │ 秒级增量更新      │    │ 锁文件防并发          │    │ 紧急修复场景       │
    └────────┬────────┘    └──────────┬──────────┘    └────────┬─────────┘
             │                        │                        │
             └────────────────────────┼────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │         IngestionPipeline            │
                    │                                     │
                    │  incremental_update(source)         │
                    │    ├─ delete_by_source (ES + Milvus) │
                    │    ├─ re-upload MinIO                │
                    │    ├─ re-split + re-embed             │
                    │    └─ re-index (ES + Milvus)         │
                    │                                     │
                    │  smart_update()                      │
                    │    ├─ detect_changes() (SHA256 diff) │
                    │    ├─ 变更<50% → incremental per file│
                    │    └─ 变更≥50% → full re-ingestion   │
                    │                                     │
                    │  run()  ← 全量重新导入                │
                    └─────────────────────────────────────┘
```

#### 5.12.2 实时更新（文件监听模式）

**触发条件：**`data/docs/` 下任意 `.md` 文件内容变更（SHA256 哈希变化）

**代码入口：**`scripts/schedule_ingest.py --mode watch`

```python
# watch_mode 核心逻辑
file_hashes: dict[str, str] = {}  # {filename: sha256_hex[:16]}

while True:
    sleep(interval)  # 默认 30s 轮询
    for doc in load_markdown_files():
        new_hash = sha256(file_content)[:16]
        old_hash = file_hashes.get(fname, "")
        
        if old_hash and new_hash != old_hash:
            # 检测到变更 → 增量更新
            pipeline.incremental_update(fname)
        
        file_hashes[fname] = new_hash
```

**增量更新流程（`incremental_update`）：**

```
┌─────────────────────────────────────────────────────────────────┐
│  incremental_update("sample_api_doc.md")                        │
│                                                                 │
│  1. 定位文档: load_markdown_files() → 匹配 source == filename   │
│  2. 删除旧数据:                                                  │
│     ES:  delete_by_source("sample_api_doc.md")                  │
│     Milvus: delete_by_source("sample_api_doc.md")               │
│  3. 重新上传: MinIO.upload_document()                            │
│  4. 重新分块: split_documents([target], chunk_size=500)         │
│  5. 重新嵌入: embedder.embed(texts)                              │
│  6. 重新索引:                                                    │
│     ES:  index_chunks(chunks)                                    │
│     Milvus: upsert_chunks(chunks, vectors)                       │
│                                                                 │
│  策略: 先删后插 (delete-then-reindex)                            │
│  原子性: 非事务性（删除和写入之间 ES/Milvus 可能短暂不一致）      │
│  适用: 单个或少量文档变更                                        │
└─────────────────────────────────────────────────────────────────┘
```

#### 5.12.3 定时更新（Cron 调度模式）

**触发方式：**系统 crontab 定时执行

```bash
# 每 2 小时智能增量更新
0 */2 * * * cd /path/to/project && python scripts/schedule_ingest.py --mode smart

# 每天凌晨 3 点全量重建（兜底）
0 3 * * * cd /path/to/project && python scripts/schedule_ingest.py --mode full
```

**smart_update 决策逻辑：**

```python
def smart_update():
    changed = detect_changes()  # SHA256 对比检测变更文件

    if not changed:
        return "No changes — up to date"        # 跳过，零开销

    if len(changed) > total_docs * 0.5:
        return full_ingestion()                  # 超过 50% 变更 → 全量重导

    for src in changed:
        incremental_update(src)                  # 逐个增量更新
```

**变更检测机制（`detect_changes`）：**

| 检测方式 | 适用场景 | 准确度 |
|----------|----------|--------|
| 文件 SHA256 对比（本地 hash map） | watch 模式（内存态） | 100%（精确） |
| ES 索引查询（对比 content_hash） | 定时模式（无状态） | 依赖 ES 可用性 |
| 回退：标记全部变更 | ES 不可用时 | 安全保守（宁可多更新不少更新） |

#### 5.12.4 三种模式对比

| 维度 | 实时更新 (watch) | 定时更新 (cron) | 手动更新 (CLI) |
|------|-----------------|-----------------|----------------|
| **触发时机** | 文件变更即触发 | crontab 定时 | 运维主动执行 |
| **延迟** | ≤30s（轮询间隔） | 取决于 cron 频率（2h/24h） | 即时 |
| **范围** | 单个变更文件 | 增量或全量 | 可指定单文件 |
| **并发控制** | 无锁（轮询单线程） | 文件锁（`fcntl.flock`） | 文件锁 |
| **适用场景** | 开发环境/频繁变更 | 生产环境/稳定变更 | 紧急修复/调试 |
| **命令** | `--mode watch` | `--mode smart/full` | `--mode single --source X` |
| **资源开销** | 低（常驻进程，仅变更时工作） | 中（定时触发，完成后退出） | 低（单次执行） |
| **状态持久化** | 内存（重启丢失 hash map） | `data/ingestion_state.json` | `data/ingestion_state.json` |

#### 5.12.5 最佳实践

**知识库更新操作手册：**

```
场景 A: 新增文档
  cp new_doc.md data/docs/
  → watch 模式自动检测 → incremental_update("new_doc.md")

场景 B: 修改现有文档
  vim data/docs/sample_api_doc.md
  → watch 模式检测 hash 变化 → incremental_update("sample_api_doc.md")

场景 C: 批量导入（>50% 文档变更）
  → watch 模式会检测到大量变更 → 建议手动执行 --mode full

场景 D: 删除文档
  rm data/docs/old_doc.md
  → watch 模式检测文件消失 event → 从 hash map 移除
  → 但 ES/Milvus 中的旧数据不会自动删除（需手动 incremental_update + 源文件不存在时报错）
  → 建议: 先执行 incremental_update 再删除，或执行 full re-ingestion

场景 E: 紧急回滚到上一版本
  git checkout HEAD~1 -- data/docs/
  → python scripts/schedule_ingest.py --mode full
```

**注意事项：**

1. **非事务性更新**：`delete_by_source` 和 `re-index` 之间存在短暂窗口（毫秒级），期间该文档的搜索结果可能为空。对于高并发生产环境，可考虑**先写后删**（create new index → alias switch → delete old）
2. **锁文件机制**：`data/.ingest.lock` 防止多个 ingestion 进程同时运行导致索引冲突
3. **状态审计**：每次运行记录写入 `data/ingestion_state.json`（保留最近 100 条），可回溯历史
4. **ES/Milvus 一致性**：当前先删 ES 再删 Milvus，再写 ES 再写 Milvus。如果任一环节失败，两个存储可能不一致（ES 有但 Milvus 无，或反过来）。生产建议引入补偿机制

---

### 5.13 Graph-Augmented Hybrid RAG 🆕

#### 5.13.1 设计动机

传统 Hybrid RAG（关键词 + 向量）在处理以下问题时存在局限：

| 问题类型 | 传统 Hybrid RAG 局限 | Graph RAG 优势 |
|----------|---------------------|----------------|
| 关系类问题（"A 和 B 有什么关系？"） | 依赖文档中恰好包含关系描述 | 从图谱直接查询实体关系和路径 |
| 调用链问题（"EntryAbility 的调用链是什么？"） | 无法建模多跳依赖 | 支持 1-2 跳邻居扩展 |
| 影响分析（"这个变更影响哪些模块？"） | 只能检索到提及相关词的文档 | 图谱中沿着 DEPENDS_ON/AFFECTS 边遍历 |
| 生命周期问答 | 文档可能分散在不同章节 | 图谱将实体与生命周期方法关联 |

#### 5.13.2 架构总览

```
                    ┌──────────────────────────┐
                    │      用户 Query           │
                    └────────────┬─────────────┘
                                 ↓
                    ┌──────────────────────────┐
                    │     Query Analyzer        │
                    │  (intent + entities +     │
                    │   keywords extraction)    │
                    └────────────┬─────────────┘
                                 ↓
                    ┌──────────────────────────┐
                    │   Retrieval Router 🆕      │
                    │  ┌────────────────────┐   │
                    │  │ Rule 1-2: 全局开关/  │   │
                    │  │ DB不可用→hybrid_only│   │
                    │  │ Rule 3: 关系推理    │   │
                    │  │ → graph_first       │   │
                    │  │ Rule 4: 精确匹配    │   │
                    │  │ → parallel(kw重点)   │   │
                    │  │ Rule 5: 语义理解    │   │
                    │  │ → parallel(vec重点)  │   │
                    │  │ Rule 6: 默认→parallel│   │
                    │  │ (9条规则,纯规则引擎) │   │
                    │  └────────────────────┘   │
                    └────────────┬─────────────┘
                                 ↓
              ┌──────────────────┼──────────────────┐
              ↓                  ↓                  ↓
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │Keyword        │  │Vector        │  │Graph 🆕      │
    │Retriever      │  │Retriever     │  │Retriever     │
    │(ES BM25/IK)  │  │(Milvus)      │  │(Neo4j)       │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           ↓                 ↓                 ↓
    ┌──────────────────────────────────────────────┐
    │         Hybrid + Graph Fusion 🆕              │
    │     (三路 Weighted RRF: kw|vec|graph)         │
    └──────────────────┬───────────────────────────┘
                       ↓
    ┌──────────────────────────────────────────────┐
    │              Reranker                         │
    │     (BGE-reranker-v2-m3 / rule-based)         │
    └──────────────────┬───────────────────────────┘
                       ↓
    ┌──────────────────────────────────────────────┐
    │        Context Builder (支持 graph_paths)      │
    │  ┌──────────────────────────────────────┐    │
    │  │ chunk metadata + graph_paths          │    │
    │  │ + [知识图谱关系路径] section           │    │
    │  └──────────────────────────────────────┘    │
    └──────────────────┬───────────────────────────┘
                       ↓
    ┌──────────────────────────────────────────────┐
    │                LLM 生成                       │
    └──────────────────────────────────────────────┘
```

#### 5.13.3 核心组件

**1. Entity Extractor** (`rag/graph/entity_extractor.py`)

纯规则引擎，零外部 API 调用。识别 9 种实体类型：

| 类型 | 示例 | 检测策略 |
|------|------|----------|
| ERROR_CODE | `9568321`, `AUTH_401` | 5-10 位数字 + 大写字母_数字模式 |
| API | `@ohos.router`, `import { ... } from '...'` | @ohos 前缀 + import 语句 |
| FUNCTION | `onCreate`, `onWindowStageCreate` | 生命周期函数名 + 函数定义 |
| CLASS | `EntryAbility`, `UIAbility`, `class X` | class/extends 关键字 + Ability 后缀 |
| CONFIG | `module.json5`, `A=value` 模式 | 配置文件 + 大写下划线赋值 |
| MODULE | `@ohos.xxx` 导入 | import from @ohos 模式 |
| LIFECYCLE | `生命周期`, `lifecycle` | 关键词 + 生命周期方法 |
| COMPONENT | `@Component`, `struct`, `Button` | ArkUI 装饰器 + 组件名 |
| CONCEPT | `ArkTS`, `HAP`, `白屏`, `签名` | 领域概念关键词 |

实体去重：按 `(normalized_name, type)` 在 chunk 内去重。

**2. Relation Extractor** (`rag/graph/relation_extractor.py`)

双层策略：

- **显式模式匹配**：语义规则匹配 9 种关系类型
  - `RELATED_TO`: "A 和 B 相关", "A 和 B 有什么关系"
  - `DEPENDS_ON`: "A 依赖 B", "import ... from ..."
  - `CALLS`: "A 调用 B", "A.B()"
  - `CAUSES`: "A 导致 B", "A 触发 B"
  - `FIXES`: "A 修复 B", "通过 A 解决 B"
  - `BELONGS_TO`: "A 属于 B"
  - `PART_OF`: "A 包含 B"
  - `HAS_LIFECYCLE`: "A 的 onCreate"
  - `AFFECTS`: "A 影响 B"

- **共现降级**：如果显式模式匹配不到足够关系，使用同 chunk 内实体共现（距离 < 300 字符）生成 `RELATED_TO` 关系

**3. Graph Indexer** (`rag/graph/graph_indexer.py`)

Neo4j 连接管理：
```
Neo4jConnection (lazy singleton)
├── 健康检查：TCP socket connect (2s timeout)
├── 驱动初始化：neo4j GraphDatabase.driver (连接池 10, 超时 30s)
└── 优雅关闭：driver.close()
```

图谱写入流程：
```
1. MERGE Document 节点 (doc_id UNIQUE)
2. MERGE Chunk 节点 (chunk_id UNIQUE) + HAS_CHUNK 关系
3. MERGE Entity 节点 (entity_id UNIQUE) + MENTIONS 关系
4. MERGE Entity-[RELATION]->Entity 边 (去重)
```

约束和索引：
```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE
CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.normalized_name)
CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)
```

**4. Graph Retriever** (`rag/graph/graph_retriever.py`)

检索流程：
```
1. 收集实体搜索词
   ├── query_analysis.entities（精确匹配）
   ├── query_analysis.keywords（降级）
   └── 从 raw query 提取 CamelCase/ALL_CAPS/错误码模式

2. 实体查找（多策略）
   ├── normalized_name 精确匹配 (score=1.0)
   ├── normalized_name 前缀匹配 (score=0.8)
   └── normalized_name 包含匹配 (score=0.6)

3. 邻居扩展
   ├── 1-hop: MATCH (e)-[r]-(neighbor) LIMIT 20
   └── 2-hop: MATCH (e)-[r1]-(mid)-[r2]-(far) LIMIT 15

4. 证据 chunks 检索
   └── MATCH (c:Chunk) WHERE c.chunk_id IN $evidence_ids

5. 候选构建与评分
```

评分公式：
```
graph_score = entity_match_score × 0.4   # 实体匹配覆盖度
            + relation_weight_score × 0.3  # 平均关系权重
            + evidence_score × 0.2         # 是否有文本证据
            + path_length_score × 0.1      # 路径长度惩罚 (1/avg_len)
```

**5. Retrieval Router** (`rag/retrieval_router.py`)

纯规则引擎路由，零 LLM 调用。每条路由决策写入 `RetrievalPlan.reason`（中文可读原因），完整可追溯。

**9 条路由规则（优先级从高到低）：**

| 规则 | 触发条件 | mode | 权重 (kw/vec/graph) | reason 示例 |
|------|---------|------|---------------------|------------|
| **Rule 1** | `ENABLE_GRAPH_RAG=false` | `hybrid_only` | 0.4/0.6/0.0 | "ENABLE_GRAPH_RAG=false，Graph RAG 全局关闭 → hybrid_only" |
| **Rule 2** | Neo4j 不可达 / GraphRetriever 初始化失败 | `hybrid_only` | 0.4/0.6/0.0 | "Graph 数据库不可用或 GraphRetriever 初始化失败 → hybrid_only" |
| **Rule 3** | 命中关系类关键词（关系/依赖/调用链/影响/导致/上下游/链路/生命周期/路径/关联）或 intent=relational 或多实体+连接词 | `graph_first` | 0.2/0.3/0.5 | "关系推理类问题 → graph_first（命中关系类关键词，检测到3个实体且询问实体间联系）" |
| **Rule 4** | 命中精确匹配模式（错误码/API名/类名/函数名/配置项）或 intent=exact | `parallel` | 0.7/0.3/0.0 | "精确匹配类问题 → parallel（关键词权重最高）（检测到错误码），keyword_top_k 增大，vector 作为兜底" |
| **Rule 5** | 命中语义关键词（为什么/怎么解决/如何优化/区别/排查/怎么办）或 intent=semantic | `parallel` | 0.2/0.6/0.2 | "语义理解类问题 → parallel（向量权重最高）（命中语义关键词），keyword 和 graph 辅助" |
| **Rule 6** | 默认（以上均不命中） | `parallel` | 0.3/0.5/0.2 | "默认并行检索：keyword + vector + graph 三路 asyncio.gather 并发" |
| **Rule 7** | parallel 模式执行 | 三路 `asyncio.ensure_future` 并发启动 | — | graph 失败非致命 → graph_candidates=[]，权重归零后归一化，`trace.graph_failed=true` |
| **Rule 8** | graph_first 模式执行 | graph→查询扩展→keyword+vector | — | graph 成功→expanded_query→并行检索；graph 失败→`degraded_to=hybrid_only` |
| **Rule 9** | hybrid_only 模式执行 | keyword+vector 混合检索 | — | 复用原有 hybrid search，不调用 graph，不生成 graph_paths |

**查询分类器核心实现：**

```python
class RetrievalRouter:
    """纯规则引擎路由 — 无 LLM 调用，每条决策写 reason 到 RetrievalPlan"""

    # 关系类正则（Rule 3）
    _RELATIONAL_KEYWORDS = re.compile(
        r"关系|依赖|调用链|影响.*哪些|导致|上下游|链路|生命周期|路径|关联|"
        r"有关|涉及|联系|相连|连接|触发|回调|监听|订阅|通知"
    )

    # 精确匹配正则（Rule 4）
    _EXACT_ERROR_CODE = re.compile(r"\b\d{4,10}\b|\bERR[A-Z_]+\b|\b[A-Z]{2,6}_\d{3,8}\b")
    _EXACT_API_NAME = re.compile(r"@ohos\.\w+|@\w+\.\w+|\bimport\s+\{")
    _EXACT_CLASS_NAME = re.compile(r"\b[A-Z][a-z]+Ability\b|\bclass\s+\w+")
    _EXACT_FUNCTION_NAME = re.compile(r"\bon\w+Create\b|\bon\w+Destroy\b")
    _EXACT_CONFIG_NAME = re.compile(r"\b[A-Z_]{3,30}\b|module\.json|app\.json")

    # 语义类正则（Rule 5）
    _SEMANTIC_KEYWORDS = re.compile(
        r"为什么|怎么解决|可能原因|如何优化|区别|排查|怎么办|"
        r"如何|怎么|怎样|什么是|含义|原因|可能|建议|推荐|最佳实践"
    )

    def route(self, query, query_analysis=None) -> RetrievalPlan:
        # Rule 1: 全局开关 → hybrid_only
        if not self._graph_enabled:
            return self._make_hybrid_only("ENABLE_GRAPH_RAG=false...")
        # Rule 2: DB不可用 → hybrid_only
        if not self.graph_available:
            return self._make_hybrid_only("Graph 数据库不可用...")
        # 特征提取 → Rule 3/4/5/6 依次判断
        features = self._analyze_query(query, qa)
        if self._is_relational(query, features, qa):    # Rule 3
            return self._make_graph_first(features, qa, reason)
        if self._is_exact(query, features, qa):          # Rule 4
            return self._make_exact_parallel(features, qa)
        if self._is_semantic(query, features, qa):       # Rule 5
            return self._make_semantic_parallel(features, qa)
        return self._make_default_parallel(features, qa) # Rule 6
```

**可测试性设计：**
- `router._graph_available_override = True` 绕过真实 Neo4j 连接检查
- 14 个路由单元测试覆盖所有规则和边界情况

**6. Query Expander** (`rag/graph/query_expander.py`)

在 `graph_first` 模式中：

原始查询: `Ability 和页面生命周期有什么关系？`

图谱检索 → 找到实体和路径 → 提取扩展词：

```
expanded_query = 原始查询 + " " + "UIAbility onCreate onWindowStageCreate Page Router 生命周期 页面跳转"
```

扩展词来源：
- 图谱路径中的实体名称
- 关系类型转中文关键词（`HAS_LIFECYCLE` → "生命周期"）
- Candidate 内容中的关键技术术语（CamelCase, ALL_CAPS, @ohos API）

**7. Three-Way Fusion** (`rag/fusion.py`)

在原有两路 RRF 基础上扩展为三路：

```
score(chunk) = kw_weight / (k + rank_kw)
             + vec_weight / (k + rank_vec)
             + graph_weight / (k + rank_graph)
```

按 `(doc_id, chunk_id)` 去重，合并 `matched_sources` 和 `graph_paths`。

权重归一化降级：
```python
def normalize_weights_for_fallback(weights, available):
    # graph 不可用 → 权重归零，剩余归一化
    normalized = {k: 0 if k not in available else v for k, v in weights.items()}
    total = sum(normalized.values())
    return {k: v/total for k, v in normalized.items()}
```

#### 5.13.4 graph_first 执行流程

```
Stage 1: Graph Retrieval
  ├── 查找匹配实体（多策略查找）
  ├── 1-hop / 2-hop 邻居扩展
  ├── 收集 evidence chunk IDs
  └── 构建 GraphPath → Candidate

    ↓ (graph 失败 → 降级到 hybrid_only)

Stage 2: Query Expansion
  ├── 从 graph_paths 提取实体和关系
  ├── 生成 expanded_query
  └── 保留 original_query（用于 trace）

Stage 3: Keyword + Vector Retrieval (并行)
  ├── 使用 expanded_query 调用 ES keyword search
  └── 使用 expanded_query 调用 Milvus vector search

Stage 4: Three-Way Fusion
  └── graph(kw=0.2, vec=0.3, graph=0.5) RRF

Stage 5: Rerank → Context Builder → LLM
```

#### 5.13.5 降级链

```
                            用户 Query
                                │
                    ┌───────────┴───────────┐
                    │   RetrievalRouter      │
                    │   根据 9 条规则决策     │
                    └───────────┬───────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
    graph_first            parallel              hybrid_only
          │                     │                     │
          │  graph 检索          │  三路并发             │  keyword+vector
          │    ↓                │  kw|vec|graph        │
          │  graph 失败          │    ↓                │
          │    ↓                │  graph 失败           │
          ▼                     ▼                     │
   degraded_from=       degraded_from=                │
   "graph_first"        "parallel"                    │
   degraded_to=         degraded_to=                  │
   "hybrid_only"        "parallel_keyword_            │
        │               vector_only"                   │
        │                     │                        │
        ▼                     ▼                        │
  继续 keyword+          keyword+vector              keyword+vector
  vector (expanded      (graph权重归零,                 │
  query 兜底)           重新归一化)                     │
        │                     │                        │
        └─────────────────────┼────────────────────────┘
                              │
                              ▼
                        (ES 失败) → Milvus only
                              │
                              ▼
                        (Milvus 失败) → 内存 Jaccard
```

**详细降级路径：**

| 原始 mode | 失败场景 | degraded_from | degraded_to | trace 行为 |
|-----------|---------|---------------|-------------|-----------|
| `parallel` | graph 检索异常/超时 | `parallel` | `parallel_keyword_vector_only` | `graph_failed=true`，graph 权重归零，kw+vec 权重归一化 |
| `graph_first` | graph 检索异常/超时 | `graph_first` | `hybrid_only` | `graph_failed=true`，降级到 keyword+vector（不含 expanded_query） |
| `graph_first` | graph 返回空结果 | `graph_first` | `hybrid_only` | `graph_failed=true`，`graph_hit_count=0` |
| `hybrid_only` | ES 不可用 | — | — | 降级到 Milvus only（由 Retriever 层处理） |
| 任一 mode | ES + Milvus 均不可用 | — | — | 降级到内存 Jaccard（终极兜底） |

**实现要点：**
```python
# _execute_parallel: graph 失败非致命
try:
    graph_candidates = await graph_retriever.search(...)
except Exception:
    trace.graph_failed = True
    plan.degraded_from = "parallel"
    plan.degraded_to = "parallel_keyword_vector_only"
    graph_candidates = []
    # graph 权重归零，kw+vec 重新归一化

# _execute_graph_first: graph 失败 → 完全降级
try:
    graph_result = await graph_retriever.search(...)
except Exception:
    trace.graph_failed = True
    plan.degraded_from = "graph_first"
    plan.degraded_to = "hybrid_only"
    plan.graph_failed = True
    return await self._execute_hybrid_fallback(query, ...)
```

每一级降级都记录在 `RetrievalTrace` 中：
- `degraded_from`: 原始模式
- `degraded_to`: 降级目标
- `graph_failed`: 是否因 graph 失败触发降级
- `errors`: 降级原因
- `route_reason`: 原始路由决策原因（保留用于事后分析）

#### 5.13.6 Ingestion 扩展

在原有 ingestion pipeline 末尾增加图谱构建步骤：

```
文档加载 → 分块 → embedding → 写 Milvus → 写 ES → [图谱构建] 🆕
                                                        ↓
                                              实体抽取 → 关系抽取 → 写 Neo4j
```

关键保证：图谱构建失败**不影响**原有 ingestion。错误被记录在 `IngestionReport.errors` 中，但 keyword + vector 索引正常完成。

#### 5.13.7 观测增强

每次检索记录结构化 RetrievalTrace：

**正常执行示例（graph_first 模式，无降级）：**
```json
{
  "trace_id": "a1b2c3d4e5f6",
  "query": "Ability 和页面生命周期有什么关系？",
  "mode": "graph_first",
  "enabled_retrievers": ["graph", "keyword", "vector"],
  "keyword_hit_count": 5,
  "vector_hit_count": 8,
  "graph_hit_count": 12,
  "merged_count": 15,
  "reranked_count": 5,
  "graph_paths_count": 8,
  "keyword_latency_ms": 12.5,
  "vector_latency_ms": 45.2,
  "graph_latency_ms": 89.1,
  "fusion_latency_ms": 3.2,
  "total_latency_ms": 150.0,
  "degraded_from": "",
  "degraded_to": "",
  "graph_failed": false,
  "route_reason": "关系推理类问题 → graph_first（命中关系类关键词，检测到2个实体且询问实体间联系）",
  "errors": [],
  "fusion_method": "rrf",
  "fusion_weights": {"keyword": 0.2, "vector": 0.3, "graph": 0.5},
  "original_query": "Ability 和页面生命周期有什么关系？",
  "expanded_query": "Ability 和页面生命周期有什么关系？ UIAbility onCreate onWindowStageCreate Page Router 生命周期 页面跳转",
  "expansion_terms": ["UIAbility", "onCreate", "onWindowStageCreate", "Page", "Router", "生命周期", "页面跳转"]
}
```

**降级示例（parallel 模式，graph 失败）：**
```json
{
  "trace_id": "b2c3d4e5f6a1",
  "query": "ArkTS 页面跳转失败怎么办？",
  "mode": "parallel",
  "enabled_retrievers": ["keyword", "vector", "graph"],
  "keyword_hit_count": 6,
  "vector_hit_count": 9,
  "graph_hit_count": 0,
  "merged_count": 12,
  "reranked_count": 5,
  "graph_paths_count": 0,
  "keyword_latency_ms": 11.2,
  "vector_latency_ms": 38.7,
  "graph_latency_ms": 0.0,
  "fusion_latency_ms": 2.8,
  "total_latency_ms": 52.7,
  "degraded_from": "parallel",
  "degraded_to": "parallel_keyword_vector_only",
  "graph_failed": true,
  "route_reason": "默认并行检索：keyword + vector + graph 三路 asyncio.gather 并发",
  "errors": ["GraphRetriever.search() failed: Neo4j connection timeout after 30s"],
  "fusion_method": "rrf",
  "fusion_weights": {"keyword": 0.375, "vector": 0.625, "graph": 0.0}
}
```

**RetrievalTrace 完整字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `trace_id` | str | 本次检索的唯一追踪 ID |
| `query` | str | 原始用户查询 |
| `mode` | str | 路由决策的模式：parallel / graph_first / hybrid_only |
| `enabled_retrievers` | list[str] | 启用的检索器列表 |
| `route_reason` | str | 路由决策的可读原因（来自 `RetrievalPlan.reason`） |
| `graph_failed` | bool | graph 检索是否失败（非致命） |
| `degraded_from` | str | 降级前的原始 mode |
| `degraded_to` | str | 降级后的目标 mode |
| `fusion_weights` | dict | 实际使用的融合权重（降级后会归一化） |
| `original_query` | str | graph_first 模式下的原始查询 |
| `expanded_query` | str | graph_first 模式下扩展后的查询 |
| `expansion_terms` | list[str] | 扩展出的关键术语 |

#### 5.13.8 兼容性矩阵

| 场景 | 行为 |
|------|------|
| `ENABLE_GRAPH_RAG=false` | 完全回到原有 Hybrid RAG，行为与改造前一致 |
| Neo4j 不可达 | 自动降级到 hybrid_only，graph 权重归零 |
| 图谱为空 | `graph_hit_count=0`，继续 keyword + vector |
| 图谱构建失败 | ingestion 继续完成（keyword+vector 索引正常） |
| 原有接口 | 无变化，`/chat` 响应结构兼容 |
| 原有测试 | 全部通过，无破坏性变更 |

#### 5.13.9 文件清单

```
src/enterprise_hybrid_rag/
├── rag/
│   ├── graph/                          # 知识图谱模块 🆕
│   │   ├── __init__.py
│   │   ├── graph_schema.py             # RetrievalPlan, GraphPath, Candidate, RetrievalResult
│   │   ├── entity_extractor.py         # 9 种实体检测（纯规则）
│   │   ├── relation_extractor.py       # 9 种关系检测（双策略）
│   │   ├── graph_indexer.py            # Neo4j 连接 + 图谱写入
│   │   ├── graph_retriever.py          # 图谱检索（实体查找 + 邻居扩展）
│   │   └── query_expander.py           # 查询扩展（graph_first 模式）
│   ├── observability/
│   │   └── retrieval_trace.py          # 检索链路追踪 🆕
│   ├── retrieval_router.py             # 动态路由 🆕
│   └── graph_rag_orchestrator.py       # 图谱编排器 🆕
├── config/settings.py                   # 新增 Neo4j/GraphRAG/Router/Fusion 配置
scripts/
├── build_graph_indexes.py               # 初始化 Neo4j 约束和索引 🆕
├── ingest_graph.py                      # 从文档构建图谱 🆕
└── run_graph_rag.py                     # 运行 Graph RAG 并输出完整 trace 🆕
tests/
├── test_graph_router.py                 # 路由测试 🆕
├── test_graph_retriever.py             # 图谱检索测试 🆕
├── test_graph_fusion.py                # 三路融合测试 🆕
├── test_graph_context.py               # 上下文测试（graph_paths）🆕
└── test_graph_orchestrator.py          # 编排器 + 降级测试 🆕
```

---

### 5.14 Graph-Augmented Hybrid RAG — 问题回答

> 以下回答基于当前实现（2026-06-02），所有引用可追溯到源码文件。

#### Q1: RAG 检索是三路并行的吗？

**是的，但取决于路由决策。** 并不是所有请求都走三路并行：

| mode | 检索策略 | 并行方式 |
|------|---------|---------|
| `parallel`（默认） | keyword + vector + graph | 三路 `asyncio.ensure_future` 同时启动，哪个先返回先用哪个 |
| `graph_first` | graph → expanded_query → (keyword + vector) | graph 先执行，成功后 keyword+vector 并行 |
| `hybrid_only` | keyword + vector | 两路并行（回到传统 Hybrid RAG） |

**关键实现细节：**
- `parallel` 模式下，三路任务通过 `asyncio.ensure_future` 同时提交到事件循环，不是串行
- graph 是其中最慢的路径（Neo4j 网络 IO + Cypher 查询），但它**不阻塞** keyword 和 vector
- graph 失败（超时/异常/空结果）不影响其他两路，`trace.graph_failed=true`，权重归零后归一化
- 融合阶段使用 **Weighted RRF**，三路结果按 rank 加权求和后排序

**代码路径：** `rag/graph_rag_orchestrator.py::_execute_parallel()` 和 `rag/fusion.py`

---

#### Q2: 为什么用纯规则引擎而不是 LLM 做检索路由？

**四个核心原因：**

1. **延迟零开销**：规则引擎是 O(1) 正则匹配 + O(1) 条件判断，单次路由 < 1ms。LLM 调用至少 200ms+（网络 RTT + token 生成），对检索链路的 latency 目标（P99 < 500ms 总耗时）不可接受
2. **确定性输出**：同一 query 永远产生同一 RetrievalPlan，方便测试和调试。LLM 路由存在随机性（temperature > 0），会导致同一问题不同次的检索策略不同，难以复现和排查
3. **可测试性**：规则引擎可写出 14 个单元测试覆盖所有分支（`tests/test_graph_router.py`），LLM 路由需要 Eval 数据集 + LLM-as-Judge，测试成本高且不稳定
4. **意图分类已经有 LLM Agent**：Router Module（`modules/intent_router.py`）先用 LLM 做意图分类（intent + entities + keywords），其结果作为 `query_analysis` 输入给检索路由器。检索路由器只需要根据这些结构化特征做"策略选择"，规则引擎完全够用

**为什么不混用？** 已经在混用了——`query_analysis["intent"]` 来自 LLM Router Module，被 `_is_relational()` / `_is_exact()` / `_is_semantic()` 三大分类器消费。这是一个 **LLM 分类 + 规则路由** 的混合架构。

---

#### Q3: 9 条路由规则的优先级为什么这样排？

**优先级顺序反映了系统的"安全→效率→质量"金字塔：**

```
Rule 1 (global disable)     ← 安全层：全局开关最高优先，一票否决
Rule 2 (DB unavailable)     ← 安全层：DB 挂了不要尝试连接
Rule 3 (relational)         ← 质量层：关系推理是 graph 的核心优势场景
Rule 4 (exact match)        ← 效率层：精确匹配 keyword 最快最准
Rule 5 (semantic)           ← 质量层：语义理解 vector 最擅长
Rule 6 (default)            ← 兜底层：什么都没命中走平衡并行
Rule 7/8/9 (mode execution) ← 执行层：mode 确定后的具体执行策略
```

**具体设计理由：**

- **Rule 1 > Rule 2**：`ENABLE_GRAPH_RAG=false` 是人为主动关闭，应该比 DB 自然不可用优先级更高（但功能等价，都回到 hybrid_only）
- **Rule 2 检查了哪些？** `graph_available` 属性封装了：`ENABLE_GRAPH_RAG` 检查 + Neo4j TCP socket 连接测试 + `GraphRetriever.__init__` 是否抛异常。任一失败→不可用
- **Rule 3 中的多实体检测**：不仅仅靠关键词，还检查 `_MULTI_ENTITY_PATTERN`（CamelCase 实体间有"和/与/、/and"等连接词），这是从实际业务数据中总结的启发式规则
- **Rule 4 为什么 graph 权重是 0？** 精确匹配（错误码、API 名）在图谱中通常找不到——图谱存的是实体间关系，不是 API 引用文档。graph_weight=0 避免噪音

---

#### Q4: 降级链的 `parallel_keyword_vector_only` 和 `hybrid_only` 有什么区别？

**这是两种不同的降级目标，对应不同的原始 mode：**

| 维度 | `parallel_keyword_vector_only` | `hybrid_only` |
|------|-------------------------------|---------------|
| **降级来源** | `parallel` mode 的 graph 失败了 | `graph_first` mode 的 graph 失败了 |
| **查询扩展** | 无（parallel 不产生 expanded_query） | 无（graph 失败拿不到扩展词） |
| **与 hybrid_only 区别** | 行为上等价，但 trace 中保留了原始 `parallel` 意图 | trace 记录完整降级路径 `graph_first → hybrid_only` |
| **后续降级** | 同样的 ES→Milvus→Jaccard 链 | 同样的 ES→Milvus→Jaccard 链 |

**为什么分开命名？** 为了在可观测性上区分"并行模式下的 graph 坏了"和"专门降级到 hybrid 模式"。这在事后分析中很重要——如果大量 `parallel→parallel_keyword_vector_only`，说明 Neo4j 稳定性有问题但系统整体可用；如果大量 `graph_first→hybrid_only`，说明关系类问题靠 keyword+vector 兜底可能效果不好。

---

#### Q5: RetrievalTrace 和 Tracer 是什么关系？

**两个独立的追踪层，互补但不重叠：**

| 维度 | Tracer（`observability/tracer.py`） | RetrievalTrace（`rag/observability/retrieval_trace.py`） |
|------|-------------------------------------|----------------------------------------------------------|
| **粒度** | 请求级（整个 `/chat` 调用） | 检索级（单次 RAG 检索） |
| **覆盖范围** | 所有 14 个 graph 节点 + 工具调用 + 校验 | 检索路由 → 三路执行 → 融合 → 排序 |
| **数据结构** | Event 模型（`BaseEvent`, `NodeEvent`, `ToolEvent`, `RetrievalEvent`） | 扁平 dataclass（~30 个字段） |
| **持久化** | JSONL 文件 + Prometheus 指标 | 跟随 `RetrievalResult` 在内存中流转 |
| **用途** | 端到端请求追踪、Agent 级监控 | 检索质量诊断、路由决策审计、权重调整参考 |

**数据流：** `RetrievalTracer.populate_from_plan()` 将 `RetrievalPlan` 的字段复制到 `RetrievalTrace`，执行过程中填充 hits/latency/degradation，最终 `to_dict()` 作为 `RetrievalResult.trace` 返回给上层。

---

#### Q6: 图谱构建失败会影响 RAG 系统正常运行吗？

**不会。** 这是一个核心设计决策：

1. **Ingestion 隔离**：图谱构建在原有 ingestion pipeline 末尾作为独立步骤运行。`graph_indexer.index_document()` 异常被 catch，记录到 `IngestionReport.errors`，但 keyword+vector 索引已经完成
2. **路由级降级**：即使图谱已有数据但 Neo4j 后续不可用，`RetrievalRouter.graph_available` 返回 false，Router 自动路由到 `hybrid_only`
3. **编排器级降级**：即使 Router 决策了 `parallel`/`graph_first`，编排器中 graph 失败也会自动降级并设置 `trace.graph_failed=true`
4. **零代码路径**：`ENABLE_GRAPH_RAG=false` 整个 graph 模块完全旁路，代码路径与改造前 100% 一致

**结果：** 最坏情况是"图检索没贡献"（graph_hit_count=0），系统退化为传统 Hybrid RAG，不影响答案生成。

---

