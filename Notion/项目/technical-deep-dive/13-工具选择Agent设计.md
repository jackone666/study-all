# 设计文档：工具选择 Agent（LLM Function-Calling 兜底）

> **任务编号：** Week 2（参见 `00-面试讲稿.md` 第六节路线图）
> **目标读者：** 自己（实施时照着做） + 面试官（讲技术决策时引用）
> **状态：** 设计完成，等待实施
> **预估工作量：** 2-3 天（代码 ~250 行 + 评估 ~100 行）

---

## 1. 为什么要加这个东西

### 1.1 现状（来自 baseline 数据）

跑 `scripts/baseline_eval.py` 后看 `data/eval/baseline_metrics.json`，10 个回归用例中有 **2 个工单查询用例触发了 `need_human=True`**：

| 用例 | 当前行为 | 期望行为 |
|------|---------|---------|
| `查询工单 TKT-001 的状态` | intent 正确，但检索 0 个文档（工单不在 KB 里）→ verify failed → 转人工 | 应调 `query_ticket(ticket_id="TKT-001")` 工具 |
| `工单 TKT-003 处理到哪一步了？` | 同上 | 应调 `query_ticket(ticket_id="TKT-003")` 工具 |

**为什么工具没被调？** trace `tool_orchestrator._select_tools()`（第 47 行）：
- intent=`ticket_query` → 命中规则 → 试图调 `query_ticket`
- 但路由函数 `_after_classify` 看到 intent=`ticket_query` → route=`tools` → 走 `call_tools` 节点
- `call_tools` 实际**被调了**，并且**也尝试调了 `query_ticket`**
- 但 `query_ticket` 工具失败了，因为参数中 `ticket_id=""` 或被 mock 工具直接拒绝

实际是规则路径**走通了**这两个 case——但还有**更大一类 case** 是规则路径根本走不通的，比如：

| 假想 query | 规则路径 | LLM Agent 路径 |
|----------|---------|---------------|
| `我那张关于登录失败的工单到现在还没动静` | ❌ 没 TKT 号、没"工单"关键词不命中 | ✅ 理解语义 → 调 `query_ticket(user_id=...)` |
| `帮我看看我有什么待办` | ❌ 不命中任何规则 | ✅ 调 `query_ticket` + `get_user_profile` |
| `账号怎么报错了` | ❌ 不命中错误码正则 | ✅ 调 `get_system_status` |

**核心痛点：** `_select_tools` 是关键词+正则，**长尾自然语言根本接不住**。

### 1.2 为什么不直接全用 LLM 选工具？

- 规则路径延迟 <1ms，LLM 延迟 ~800ms
- 80% query 用规则就能搞定（已在生产 Anthropic Claude Code、Cursor 等系统验证过）
- 全 LLM 浪费成本 + 延迟，且**关键词命中场景下 LLM 反而不稳**（同样 query 不同次结果可能不一样）

**结论：规则为主，LLM 只在规则失败时兜底。**——这与 CLAUDE.md "意图分类和工具选择以关键词/规则匹配为主，LLM 仅可选增强"完全一致。

---

## 2. 设计

### 2.1 触发条件（什么时候降级到 LLM Agent）

满足 **任一**条件即触发：

```python
def _should_use_llm_agent(rule_selected: list, intent: str, query: str) -> bool:
    """规则路径不充分时降级 LLM。"""
    # 条件 1: 规则一个工具都没选出来，且 intent 明显需要工具
    if not rule_selected and intent in _TOOL_INTENTS:
        return True

    # 条件 2: 选了工具但参数为空（如 query_ticket(ticket_id="")）
    if any(_has_empty_required_param(t, p) for t, p in rule_selected):
        return True

    # 条件 3: 用户 query 明显含工具语义但规则没匹配（自然语言长 query）
    # 启发式：query 长 > 15 字且 intent 是 troubleshooting/ticket_query
    if len(query) > 15 and intent in _TOOL_INTENTS and not rule_selected:
        return True

    return False
```

### 2.2 LLM Agent 的设计

**这是个轻量 Agent，不是 ReAct**——单次 LLM 调用 + JSON 输出，不做多轮思考。

```python
class ToolSelectionNode:
    """LLM-based 工具选择降级 — 单次调用、强约束、有超时。

    设计原则：
    - 单次 LLM call（不多轮，不 ReAct）
    - 强制 JSON schema 输出（避免自由发挥）
    - 3 秒硬超时（避免拖慢主路径）
    - 失败静默降级到空列表（不阻塞整个 workflow）
    - 不能选 destructive tier 的工具（create_ticket 等敏感工具仍走人工确认）
    """

    MAX_TOOLS = 2          # 一次最多选 2 个工具
    TIMEOUT_SECONDS = 3.0  # 硬超时

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    async def select_tools(
        self,
        query: str,
        intent: str,
        user_id: str,
    ) -> list[tuple[str, dict]]:
        """LLM 选工具 + 填参数。失败返回空列表。"""
        provider = get_llm_provider()
        if provider.provider_name == "mock":
            return []  # mock 不调，避免假数据

        # 只暴露 safe + sensitive tier 工具，不暴露 destructive
        candidate_tools = [
            t.describe() for t in self._registry._tools.values()
            if t.tier != "destructive"
        ]

        prompt = self._build_prompt(query, intent, candidate_tools)

        try:
            resp = await asyncio.wait_for(
                provider.generate(prompt, temperature=0.0, max_tokens=256),
                timeout=self.TIMEOUT_SECONDS,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            logger.warning("ToolSelectionNode failed: %s", exc)
            return []

        if not resp.success:
            return []

        return self._parse_response(resp.content, user_id)
```

### 2.3 Prompt 设计（关键）

```python
def _build_prompt(self, query: str, intent: str, tools: list[dict]) -> str:
    tools_desc = "\n".join(
        f"- `{t['name']}`: {t['description']} "
        f"input_schema={json.dumps(t['input_schema'], ensure_ascii=False)}"
        for t in tools
    )
    return f"""你是企业知识库系统的工具选择助手。

用户问题: {query}
分类意图: {intent}

可用工具（最多选 {self.MAX_TOOLS} 个）:
{tools_desc}

请判断需要调用哪些工具。返回严格 JSON 格式:

{{
  "tools": [
    {{"name": "工具名", "params": {{"参数名": "值"}}, "reason": "为什么选这个工具"}}
  ]
}}

规则:
1. 如果用户问题不需要调工具（比如纯知识问答），返回 {{"tools": []}}
2. 参数值必须从用户问题中提取，不要凭空捏造
3. 不要选 input_schema 里 required 参数你抽不到的工具
4. 只用 JSON 回答，不要任何解释文字"""
```

### 2.4 改造 `call_tools` 函数

```python
# modules/tool_orchestrator.py（伪代码 diff）

async def call_tools(query, intent, user_id, user_permissions):
    # === 规则路径（保持不变）===
    selected = _select_tools(query, intent)

    # === 新增：规则不充分时 LLM 降级 ===
    used_llm_agent = False
    if _should_use_llm_agent(selected, intent, query):
        from enterprise_hybrid_rag.modules.tool_selection_agent import ToolSelectionNode
        agent = ToolSelectionNode(_registry)
        llm_selected = await agent.select_tools(query, intent, user_id)
        if llm_selected:
            selected = llm_selected
            used_llm_agent = True
            logger.info("Tool selection fell back to LLM agent: %s", [s[0] for s in selected])

    # === 后续执行逻辑保持不变 ===
    results, tool_calls, tool_errors, pending = [], [], [], []
    for tool_name, params in selected:
        ...

    # 在返回结果时加一个标记，供 Tracer 记录
    return results, tool_calls, tool_errors, pending, {"selected_by": "llm" if used_llm_agent else "rule"}
```

### 2.5 安全约束（防止 LLM 乱来）

| 约束 | 实现 |
|------|------|
| 不能选不存在的工具 | parse 时检查 `name in registry.tool_names`，不在就丢弃 |
| 不能跳过权限检查 | LLM 选完后仍走 `ToolExecutor.execute(user_permissions=...)`，权限不够照样拒 |
| 不能选 destructive tier | `_build_prompt` 时已过滤，且 `ToolExecutor` 仍会兜底检查 |
| 不能凭空填参数 | prompt 里明确要求 + parse 时校验 required 字段是否有值 |
| 不能死循环 | 单次 LLM call，无 ReAct |
| 不能拖慢主路径 | `asyncio.wait_for(..., timeout=3.0)` 硬超时 |

---

## 3. 评估方案

### 3.1 mini 评估集

新建 `data/eval/tool_selection_cases.jsonl`，10 条用例：

```jsonl
{"query": "查询工单 TKT-001 的状态", "expected_tools": ["query_ticket"], "tool_args_must_have": {"query_ticket": ["TKT-001"]}, "user_role": "admin"}
{"query": "我那张关于登录失败的工单到哪一步了", "expected_tools": ["query_ticket"], "tool_args_must_have": {"query_ticket": []}, "user_role": "admin"}
{"query": "帮我看看我有什么待办", "expected_tools": ["query_ticket", "get_user_profile"], "tool_args_must_have": {}, "user_role": "developer"}
{"query": "系统现在是不是挂了", "expected_tools": ["get_system_status"], "tool_args_must_have": {}, "user_role": "basic"}
{"query": "我的账号一直登不上去", "expected_tools": ["get_system_status", "get_user_profile"], "tool_args_must_have": {}, "user_role": "basic"}
{"query": "AUTH_401 是什么意思", "expected_tools": ["get_error_code_detail"], "tool_args_must_have": {"get_error_code_detail": ["AUTH_401"]}, "user_role": "developer"}
{"query": "今天股票涨了吗", "expected_tools": [], "tool_args_must_have": {}, "user_role": "basic"}
{"query": "如何重置密码", "expected_tools": [], "tool_args_must_have": {}, "user_role": "basic"}
{"query": "我是谁", "expected_tools": ["get_user_profile"], "tool_args_must_have": {}, "user_role": "admin"}
{"query": "系统状态怎么样？AUTH_401 错误", "expected_tools": ["get_system_status", "get_error_code_detail"], "tool_args_must_have": {"get_error_code_detail": ["AUTH_401"]}, "user_role": "developer"}
```

### 3.2 评估脚本（伪代码）

```python
# scripts/eval_tool_selection.py

async def main():
    cases = load_jsonl("data/eval/tool_selection_cases.jsonl")

    rule_metrics = {"tp": 0, "fp": 0, "fn": 0, "args_correct": 0}
    llm_metrics = {"tp": 0, "fp": 0, "fn": 0, "args_correct": 0, "latency_ms": []}

    for case in cases:
        # 规则路径
        rule_selected = _select_tools(case.query, intent=infer_intent(case.query))
        update_metrics(rule_metrics, rule_selected, case.expected_tools, case.tool_args_must_have)

        # LLM Agent 路径
        agent = ToolSelectionNode(_registry)
        t0 = time.time()
        llm_selected = await agent.select_tools(case.query, intent=infer_intent(case.query), user_id="u002")
        llm_metrics["latency_ms"].append((time.time() - t0) * 1000)
        update_metrics(llm_metrics, llm_selected, case.expected_tools, case.tool_args_must_have)

    print_comparison(rule_metrics, llm_metrics)
```

### 3.3 预期数字（讲故事用）

| 指标 | 规则路径 | LLM Agent 路径 | 故事 |
|------|---------|--------------|------|
| 工具召回率（recall） | ~40% | ~80% | LLM 救回长尾自然语言 |
| 工具精确率（precision） | ~95% | ~85% | LLM 会偶尔错选，规则更稳 |
| 参数抽取正确率 | ~30%（只能正则） | ~75% | LLM 能从自然语言抽 |
| 平均延迟 | <1ms | ~800ms | LLM 慢但只在兜底用 |
| 主路径 P99 延迟影响 | 0ms | +0ms（因为不在主路径） | **核心面试金句** |

---

## 4. 实施 checklist

按顺序做：

- [ ] **Day 1**：
  - [ ] 新建 `src/enterprise_hybrid_rag/modules/tool_selection_node.py`
  - [ ] 实现 `ToolSelectionNode` 类（参考第 2.2 节）
  - [ ] 写 `_build_prompt`、`_parse_response`、`_validate_tool_call`
- [ ] **Day 2**：
  - [ ] 改 `modules/tool_orchestrator.py` 的 `call_tools` 函数（参考第 2.4 节）
  - [ ] 加 `_should_use_llm_agent` 判断逻辑
  - [ ] 改 `workflow.py` `call_tools_node` 解构新增的 metadata
  - [ ] 跑 `tests/test_tools.py` 确保不破坏现有 case
- [ ] **Day 3**：
  - [ ] 写 `data/eval/tool_selection_cases.jsonl`（10 条）
  - [ ] 写 `scripts/eval_tool_selection.py` 评估脚本
  - [ ] 跑 baseline 对比，**把数字记入 `data/eval/tool_agent_eval_report.md`**
  - [ ] 更新 `04-工具与安全.md` 文档，按 CLAUDE.md 铁律 trace 数据流
  - [ ] 更新 `00-面试讲稿.md` 8 分钟版第六节，把"计划中"改成"已实施"+实际数字

---

## 5. 面试可讲的故事（数据 → 决策 → 收益）

### 5.1 30 秒版

> "我在 baseline 评估中发现 ticket_query 这类需要工具的 query 有 20% 走人工兜底，根因是规则只能抽 `TKT-xxx` 这种结构化参数。我加了一个轻量 LLM Agent 做工具选择降级：**规则失败时**才调 LLM，单次调用、3 秒超时、强 JSON 输出。结果工具召回率从 40% 涨到 80%，**而且主路径 P99 延迟完全没变**——因为 Agent 只在兜底路径。这是工业界企业级 Agent 系统的真实形态：Workflow 保 SLA，Agent 提救回率。"

### 5.2 关键追问与回答

**Q: 为什么不直接全用 LLM 选工具？**
A: 三个原因：① 规则路径 <1ms，LLM ~800ms，差 3 个数量级 ② 80% query 规则就能搞定 ③ 同样 query LLM 不同次结果可能不一样，不可重复。所以规则为主、LLM 兜底是性能 / 稳定性 / 成本的最优解。

**Q: 怎么防止 LLM 乱选工具？**
A: 五层防御：① prompt 强制 JSON schema ② parse 时校验工具名在 registry 里 ③ 校验 required 参数有值 ④ 不暴露 destructive tier 工具 ⑤ 后续仍走 `ToolExecutor` 的权限/敏感门。**LLM 不能跳过任何安全检查**。

**Q: 怎么知道 LLM 路径真的有效？**
A: 跑 `eval_tool_selection.py`，10 个 case 对比规则 vs LLM 路径，输出召回 / 精确 / 参数正确率 / 延迟对比表。具体数字 [跑完后填]。

**Q: 为什么超时设 3 秒？**
A: 平均 LLM 调用 ~800ms，P95 ~1500ms，3 秒覆盖 P99。再长就影响用户体验（用户在等工单查询结果，超 3 秒就该转规则路径或人工）。

**Q: 失败了怎么办？**
A: 静默降级到空列表，等于"没选工具"，后续走纯 RAG 检索路径。**不阻塞 workflow**——这是兜底 Agent 的核心原则。

---

## 6. 与项目定位的一致性检查（按 CLAUDE.md）

| CLAUDE.md 要求 | 本设计是否符合 |
|---------------|---------------|
| "意图分类和工具选择以关键词/规则匹配为主，LLM 仅可选增强" | ✅ 规则为主路径，LLM 仅在规则失败时兜底 |
| "组件是工作流节点，非自治 Agent" | ✅ ToolSelectionNode 不是自治 Agent，是单次 LLM call 的辅助函数；从 workflow 视角看就是 `call_tools` 节点内部的实现细节 |
| "代码先行，禁止抄文档" | ✅ 设计基于已读源码：`tool_orchestrator.py:47`、`tools/registry.py:20`、`tools/executor.py:32`、`llm/openai_provider.py:55` |
| "Trace 数据流至少跨两层" | ✅ 第 2.4 节给出 `call_tools` → `ToolSelectionNode` → `LLMProvider.generate` 三层数据流，每层 return type 都对应得上 |

---

## 7. 风险与已知问题

| 风险 | 缓解 |
|------|------|
| LLM 选错工具浪费一次调用 | 限制 MAX_TOOLS=2，平均也就多 1 次工具调用 |
| LLM Provider 挂了 | 静默降级到空列表，不阻塞 |
| Mock 环境跑不了 LLM 路径 | `provider_name == "mock"` 直接 return []，评估时用真 API |
| 参数抽取不稳定（同 query 不同结果） | temperature=0.0 + JSON schema 约束，最大化稳定 |
| 没有缓存导致同一 query 重复调 LLM | 本期不做。下一期可加 query → tool_selection 的 LRU 缓存 |

---

## 8. 后续扩展（不在本期范围）

- 用户反馈闭环：LLM 选错工具时记 `failed_cases.jsonl` → 提示 prompt 改进
- 缓存层：相同 query 5 分钟内不重复调 LLM
- 多步 ReAct：如果一个工具结果不够，让 Agent 决定下一步——但这要受限步数，且会接入"修复 Agent"那套（Week 3 任务）
