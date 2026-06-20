# Lead Agent 构造调用链

入口文件：`backend/packages/harness/deerflow/agents/lead_agent/agent.py`

先抓本质：本章讲的是“agent 如何被装配出来”，不是“agent 如何执行”。执行发生在 `run_agent()` 的 `agent.astream()`；这里做的是把模型、工具、middleware、prompt、状态 schema 组装成一个可运行的 agent。

## 总调用链

```text
run_agent()
  -> agent_factory(config=runnable_config, app_config=ctx.app_config)
  -> make_lead_agent(config)
  -> _get_runtime_config(config)
  -> _make_lead_agent(config, app_config)
      -> _get_runtime_config(config)
      -> validate_agent_name(...)
      -> load_agent_config(agent_name)
      -> _available_skill_names(agent_config, is_bootstrap)
      -> _resolve_model_name(requested or agent_config.model)
      -> build_tracing_callbacks()
      -> _load_enabled_skills_for_tool_policy(...)
      -> get_available_tools(...)
      -> filter_tools_by_skill_allowed_tools(...)
      -> _assemble_deferred(...)
      -> _build_middlewares(...)
      -> apply_prompt_template(...)
      -> create_agent(...)
```

## 1. `_get_runtime_config()`

作用：把 `config["configurable"]` 和 `config["context"]` 扁平合并。

优先级：

```text
configurable -> context 覆盖 configurable
```

为什么这样做：

- 老代码很多地方从 `configurable` 读参数。
- LangGraph 新版本推荐用 `context`。
- DeerFlow 同时兼容两套通道。

本质解释：`_get_runtime_config()` 是配置世界的“翻译层”。外面传入的是 LangGraph 风格的嵌套配置，agent 工厂真正需要的是扁平的运行决策，比如模型、agent 名称、plan mode、子代理开关。

常见字段：

- `thread_id`
- `run_id`
- `model_name`
- `mode`
- `thinking_enabled`
- `reasoning_effort`
- `is_plan_mode`
- `subagent_enabled`
- `max_concurrent_subagents`
- `agent_name`
- `is_bootstrap`

这些运行字段大多来自前端 `frontend/src/core/threads/hooks.ts`。前端先根据 `context.mode` 推导布尔开关，后端再读取这些已经算好的结果：

| 前端 mode | `_get_runtime_config()` 读到的重点字段 |
| --- | --- |
| `flash` | `thinking_enabled=false`, `is_plan_mode=false`, `subagent_enabled=false` |
| `thinking` | `thinking_enabled=true`, `is_plan_mode=false`, `subagent_enabled=false`, `reasoning_effort="low"` |
| `pro` | `thinking_enabled=true`, `is_plan_mode=true`, `subagent_enabled=false`, `reasoning_effort="medium"` |
| `ultra` | `thinking_enabled=true`, `is_plan_mode=true`, `subagent_enabled=true`, `reasoning_effort="high"` |

注意：`mode` 字符串本身主要用于前端表达用户选择；后端关键行为看的是 `thinking_enabled`、`is_plan_mode`、`subagent_enabled`、`reasoning_effort` 这些派生字段。
- `app_config`

## 2. `_resolve_model_name()`

优先级：

```text
请求 model_name
  -> 自定义 agent 配置 model
  -> config.models[0].name
  -> 无模型时报 ValueError
```

行为：

- 请求模型存在：直接使用。
- 请求模型不存在：日志警告，回退默认。
- 没有任何模型配置：抛 `ValueError`。

注意：

- HTTP `start_run()` 已经对请求传入的 `model_name` 做 allowlist 校验，非法值会 400。
- `_resolve_model_name()` 仍然保留回退逻辑，是因为 agent 工厂也可能被非 HTTP 路径调用。

## 3. `_make_lead_agent()` 九步

### 步骤 1：解析运行时参数

读取：

- `thinking_enabled`
- `reasoning_effort`
- `requested_model_name`
- `is_plan_mode`
- `subagent_enabled`
- `max_concurrent_subagents`
- `is_bootstrap`
- `agent_name`

### 步骤 2：加载自定义 Agent 配置

```text
agent_name 非空且非 bootstrap
  -> load_agent_config(agent_name)
  -> 可得到 agent_config.model / tool_groups / skills
```

bootstrap 模式不加载自定义 agent，因为此时自定义 agent 可能还不存在。

### 步骤 3：模型选择

```text
model_name = _resolve_model_name(requested_model_name or agent_model_name)
model_config = app_config.get_model_config(model_name)
```

如果模型不支持 thinking，但请求开启了 thinking：

```text
thinking_enabled = False
logger.warning(...)
```

### 步骤 4：注入 metadata 和 tracing callbacks

写入 `config["metadata"]`：

- `agent_name`
- `model_name`
- `thinking_enabled`
- `reasoning_effort`
- `is_plan_mode`
- `subagent_enabled`
- `tool_groups`
- `available_skills`

然后调用：

```text
build_tracing_callbacks()
```

关键不变量：

- tracing callback 在图根注入。
- 后续所有 `create_chat_model()` 必须传 `attach_tracing=False`。
- 否则会产生重复 span，且 Langfuse root trace 属性无法正确传播。

### 步骤 5：加载技能用于工具策略

```text
_load_enabled_skills_for_tool_policy(available_skills, app_config)
```

技能可以声明 `allowed-tools`。后续 `filter_tools_by_skill_allowed_tools()` 会用它过滤工具。

### 分支 A：Bootstrap Agent

调用链：

```text
get_available_tools(...) + [setup_agent]
  -> filter_tools_by_skill_allowed_tools(...)
  -> _assemble_deferred(...)
  -> create_chat_model(..., attach_tracing=False)
  -> _build_middlewares(...)
  -> apply_prompt_template(available_skills={"bootstrap"})
  -> create_agent(...)
```

特点：

- 只暴露 bootstrap 技能。
- 增加 `setup_agent` 工具。
- 用于首次创建自定义 agent。

### 分支 B：默认/自定义 Agent

调用链：

```text
extra_tools = [update_agent] if agent_name else []
get_available_tools(groups=agent_config.tool_groups, ...)
  -> filter_tools_by_skill_allowed_tools(raw_tools + extra_tools, skills)
  -> _assemble_deferred(...)
  -> create_chat_model(..., reasoning_effort=..., attach_tracing=False)
  -> _build_middlewares(...)
  -> apply_prompt_template(agent_name=agent_name, available_skills=...)
  -> create_agent(...)
```

特点：

- 自定义 agent 可获得 `update_agent`，默认 agent 没有。
- 自定义 agent 会注入 `SOUL.md` 和 agent-specific 配置。
- `tool_groups` 可限制工具分组。

## 4. 中间件构建顺序

`_build_middlewares()` 分两段：

1. `build_lead_runtime_middlewares()` 添加底层运行时中间件。
2. `agent.py` 继续追加上下文、摘要、标题、记忆、视觉、延迟工具、子代理限制等。

本质解释：middleware 是横切逻辑。它不属于某一个工具，也不适合全塞进 prompt，但每次 agent 运行都可能需要。顺序重要，因为前面的 middleware 往往准备上下文，后面的 middleware 处理结果、错误或统计。

顺序：

| 顺序 | 中间件 | 主要职责 |
| --- | --- | --- |
| 1 | `ThreadDataMiddleware` | 创建线程目录和 `thread_data` |
| 2 | `UploadsMiddleware` | 跟踪并注入上传文件 |
| 3 | `SandboxMiddleware` | 管理沙箱状态 |
| 4 | `DanglingToolCallMiddleware` | 修复缺失 ToolMessage |
| 5 | `LLMErrorHandlingMiddleware` | 模型错误恢复 |
| 6 | `GuardrailMiddleware` | 工具调用前授权 |
| 7 | `SandboxAuditMiddleware` | 沙箱操作审计 |
| 8 | `ToolErrorHandlingMiddleware` | 工具异常转 ToolMessage |
| 9 | `DynamicContextMiddleware` | 注入日期、记忆等动态上下文 |
| 10 | `SummarizationMiddleware` | 压缩长上下文 |
| 11 | `TodoMiddleware` | plan mode 下暴露 todo 工具 |
| 12 | `TokenUsageMiddleware` | token 用量统计 |
| 13 | `TitleMiddleware` | 首轮后自动标题 |
| 14 | `MemoryMiddleware` | 对话入长期记忆队列 |
| 15 | `ViewImageMiddleware` | 视觉模型图片注入 |
| 16 | `DeferredToolFilterMiddleware` | 延迟 MCP 工具 schema |
| 17 | `SubagentLimitMiddleware` | 限制 task tool 并发 |
| 18 | `LoopDetectionMiddleware` | 检测工具调用循环 |
| 19 | `SafetyFinishReasonMiddleware` | 安全终止时清理 tool_calls |
| 20 | `ClarificationMiddleware` | 最终拦截 ask_clarification |

## 5. 延迟工具：`_assemble_deferred()`

目的：减少 MCP 工具 schema 对模型上下文的占用。

本质解释：deferred tool 是“按需暴露工具”。不是工具不可用，而是不把所有 MCP 工具一次性塞进模型上下文。模型先看到 `tool_search`，需要时再搜索并提升具体工具，减少 schema 噪音和上下文占用。

启用 `tool_search` 时：

```text
普通工具 -> 直接绑定模型
MCP 工具 -> 从绑定列表移入 deferred catalog
tool_search -> 作为普通工具绑定模型
```

模型先看到 `tool_search`，需要某类工具时再搜索并提升。

安全策略：

```text
tool_search enabled
  and MCP tools survived filtering
  and deferred_names empty
  -> RuntimeError
```

这是 fail-closed，防止 MCP schema 静默丢失。

## 6. `ThreadState`

文件：`backend/packages/harness/deerflow/agents/thread_state.py`

本质解释：`ThreadState` 是 agent 图执行时的业务状态白板。它回答“这个 thread 积累了什么状态”，不回答“这一次 run 是否成功”。run 是否成功由 `RunRecord`、run store 和 worker 终态负责。

核心字段：

- `sandbox`
- `thread_data`
- `title`
- `artifacts`
- `todos`
- `uploaded_files`
- `viewed_images`
- `promoted`

关键 reducer：

- `merge_artifacts()`：按 artifact id 去重。
- `merge_viewed_images()`：合并/清空已查看图片。
- `merge_todos()`：合并 todo 状态。
- `merge_promoted()`：记录已经由 `tool_search` 提升的工具。

读 `ThreadState` 的意义：

- 它定义了 agent 图状态能保存什么。
- 中间件和工具写入的状态必须在这里有 schema 支持。
- checkpoint 最终保存的 channel values 与这些字段直接相关。

## 7. 源码精读顺序

Lead Agent 这一章最容易读散，因为模型、技能、工具、middleware、prompt 都集中在同一个工厂里。建议按“配置 -> 资源 -> 装配 -> 创建”的顺序读：

| 顺序 | 函数/区域 | 先回答的问题 |
| --- | --- | --- |
| 1 | `make_lead_agent()` | 公共入口如何转到内部 `_make_lead_agent()`？ |
| 2 | `_get_runtime_config()` | `RunnableConfig` 中哪些字段会被扁平化？ |
| 3 | `_resolve_model_name()` | 请求模型、自定义 agent 模型、全局默认模型如何决策？ |
| 4 | `load_agent_config()` 相关调用 | `agent_name` 如何影响 prompt、tools、model？ |
| 5 | `_load_enabled_skills_for_tool_policy()` | skill 的 allowed-tools 如何参与过滤？ |
| 6 | `get_available_tools()` | 内置工具、MCP 工具、ACP 工具如何汇合？ |
| 7 | `_assemble_deferred()` | 哪些工具直接给模型，哪些工具藏到 `tool_search` 后面？ |
| 8 | `_build_middlewares()` | middleware 为什么按这个顺序排列？ |
| 9 | `create_agent()` | 最终传给 LangGraph/LangChain agent 的是什么？ |

## 8. Agent 构造中的关键变量

| 变量 | 来源 | 影响 |
| --- | --- | --- |
| `config` | `run_agent()` 中的 `RunnableConfig` | 带入 metadata、callbacks、context、configurable |
| `cfg` | `_get_runtime_config(config)` | 扁平化后的运行配置，供后续决策读取 |
| `model_name` | request context / agent config / app config | 决定 `create_chat_model()` 使用哪个模型 |
| `agent_name` | request context | 决定是否加载自定义 agent 配置 |
| `mode` | 前端聊天设置 | 前端用于推导 thinking/plan/subagent；后端通常不直接靠它决策 |
| `thinking_enabled` | 前端 `mode !== "flash"` | 决定 `create_chat_model()` 是否启用模型 thinking 能力 |
| `reasoning_effort` | 前端按 mode 推导，或用户显式设置 | 传给支持该参数的模型，影响推理强度 |
| `is_plan_mode` | 前端 `mode === "pro" || mode === "ultra"` | 决定 plan/todo 相关 middleware 是否启用 |
| `subagent_enabled` | 前端 `mode === "ultra"` | 决定是否加入 `task_tool` 并允许子代理委派 |
| `is_bootstrap` | request context | bootstrap 模式下跳过自定义 agent 配置 |
| `skills_for_tool_policy` | skill loader | 决定工具是否被 allowed-tools 过滤 |
| `raw_tools` | `get_available_tools()` | 候选工具全集 |
| `final_tools` | `_assemble_deferred()` | 直接绑定到模型的工具 |
| `setup` | `_assemble_deferred()` | deferred tool 的运行时目录和提升逻辑 |
| `middleware` | `_build_middlewares()` | 运行前后处理、工具错误、摘要、记忆、标题等 |
| `system_prompt` | prompt template + config | 进入模型的系统提示词 |

## 9. 方法级调用图

```text
run_agent()
  -> agent_factory(config=runnable_config, app_config=ctx.app_config)
      -> make_lead_agent(config, app_config=...)
          -> _make_lead_agent(config, app_config=...)
              -> _get_runtime_config(config)
              -> validate_agent_name(...)
              -> load_agent_config(agent_name)
              -> _resolve_model_name(...)
              -> build_tracing_callbacks()
              -> _load_enabled_skills_for_tool_policy(...)
              -> get_available_tools(...)
                  -> get_cached_mcp_tools()
                  -> build_invoke_acp_agent_tool(...)
              -> filter_tools_by_skill_allowed_tools(...)
              -> _assemble_deferred(...)
                  -> build_deferred_tool_setup(...)
              -> _build_middlewares(...)
                  -> ThreadDataMiddleware
                  -> UploadsMiddleware
                  -> SandboxMiddleware
                  -> DynamicContextMiddleware
                  -> SummarizationMiddleware
                  -> MemoryMiddleware
                  -> DeferredToolFilterMiddleware
                  -> SubagentLimitMiddleware
              -> apply_prompt_template(...)
              -> create_chat_model(...)
              -> create_agent(model=..., tools=final_tools, middleware=...)
```

读这张图时要注意：`_make_lead_agent()` 是“构造 agent”，不是“执行 agent”。真正执行在 `run_agent()` 的 `agent.astream()`。

## 10. 常见误区

| 误区 | 正确理解 |
| --- | --- |
| `model_name` 只来自全局配置 | 请求 context、自定义 agent 配置、全局默认都会参与 |
| 所有工具都直接暴露给模型 | MCP 工具可能被 deferred，只通过 `tool_search` 逐步提升 |
| middleware 顺序无所谓 | 前置上下文、工具错误、摘要、记忆、标题等都有依赖顺序 |
| `ThreadState` 是 run metadata | 它是 LangGraph 图状态，run metadata 在 run store/thread store |
| `make_lead_agent()` 会处理 SSE | SSE 在 worker 和 stream bridge，不在 agent 工厂 |

## 11. 自测题

读完本章后，尝试回答：

1. 如果请求中传了 `model_name`，它经过哪些函数才影响 `create_chat_model()`？
2. 自定义 agent 配置和全局 app config 冲突时，模型选择优先级是什么？
3. `tool_search` 开启后，为什么 MCP 工具不一定直接出现在模型 schema 中？
4. 哪些 middleware 会写入或读取 `ThreadState`？
5. 如果某个工具没有出现在模型可调用列表中，你会按什么顺序排查？
