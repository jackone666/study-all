# 工具、沙箱与 MCP

先抓本质：工具系统解决的是“模型如何安全地影响外部世界”。模型本身只会生成文本；工具让它能搜索、读写文件、执行命令、调用 MCP 服务。但一旦允许模型行动，就必须同时解决权限、隔离、审计、上下文传递和错误恢复。

## 工具装配入口

文件：`backend/packages/harness/deerflow/tools/tools.py`

调用链：

```text
_make_lead_agent()
  -> get_available_tools(groups, include_mcp, model_name, subagent_enabled, app_config)
      -> filter config.tools by group
      -> remove host bash if local sandbox forbids it
      -> resolve_variable(cfg.use, BaseTool)
      -> _ensure_sync_invocable_tool(tool)
      -> add built-in tools
      -> add skill_manage_tool if skill_evolution enabled
      -> add task_tool if subagent_enabled
      -> add view_image_tool if model supports vision
      -> load cached MCP tools
      -> tag_mcp_tool(...)
      -> add ACP invoke tool
      -> deduplicate by tool.name
      -> return unique tools
```

## 工具来源

| 来源 | 示例 | 进入条件 |
| --- | --- | --- |
| 配置工具 | `config.tools[*].use` | `group` 过滤后加载 |
| 内置工具 | `present_file_tool`, `ask_clarification_tool` | 总是加入 |
| 技能管理工具 | `skill_manage_tool` | `skill_evolution.enabled=true` |
| 子代理工具 | `task_tool` | `subagent_enabled=true` |
| 视觉工具 | `view_image_tool` | 当前模型 `supports_vision=true` |
| MCP 工具 | `get_cached_mcp_tools()` | extensions 中有启用 MCP server |
| ACP 工具 | `invoke_acp_agent` | 配置了 ACP agents |

## 去重规则

工具按名称去重，优先级：

```text
config-loaded tools -> built-ins -> MCP tools -> ACP tools
```

原因：

- LLM 绑定重复 tool schema 会造成歧义。
- runtime 路由工具名时可能出现 “not a valid tool”。

## 沙箱中间件

文件：`backend/packages/harness/deerflow/sandbox/middleware.py`

本质解释：sandbox 不是为了“方便执行命令”，而是为了“允许执行命令时仍然控制风险”。文件路径、用户目录、命令执行、审计事件都要被约束在当前 thread/user/run 的边界内。

生命周期：

```text
SandboxMiddleware(lazy_init=True)
  -> before_agent(): lazy 模式不获取沙箱
  -> 首次工具调用 ensure_sandbox_initialized_async()
  -> provider.acquire_async(thread_id)
  -> runtime.state["sandbox"] = {"sandbox_id": sandbox_id}
  -> runtime.context["sandbox_id"] = sandbox_id
  -> after_agent(): 当前实现会释放 state/context 中的 sandbox
```

注意：

- 模块 docstring 说同一线程复用沙箱，但当前 `after_agent/aafter_agent` 会释放 sandbox；阅读时要以代码行为为准。
- `lazy_init=True` 的价值是：纯对话不触发沙箱启动成本。
- 异步工具路径优先用 `provider.acquire_async()`，避免阻塞事件循环。

## 沙箱工具主链路

文件：`backend/packages/harness/deerflow/sandbox/tools.py`

### 异步工具共用路径

```text
_bash_tool_async(...)
  -> _run_sync_tool_after_async_sandbox_init(bash_tool.func, runtime, ...)
      -> ensure_sandbox_initialized_async(runtime)
      -> asyncio.to_thread(func, runtime, ...)
```

`ls/glob/grep/read_file/write_file/str_replace` 都采用同样模式。

### `ensure_sandbox_initialized_async()`

调用链：

```text
ensure_sandbox_initialized_async(runtime)
  -> validate runtime and runtime.state
  -> if runtime.state["sandbox"].sandbox_id exists:
       provider.get(sandbox_id)
       runtime.context["sandbox_id"] = sandbox_id
       return sandbox
  -> resolve thread_id from runtime.context or runtime.config.configurable
  -> provider.acquire_async(thread_id)
  -> runtime.state["sandbox"] = {"sandbox_id": sandbox_id}
  -> provider.get(sandbox_id)
  -> runtime.context["sandbox_id"] = sandbox_id
  -> return sandbox
```

关键点：

- `runtime.state` 让同一次 agent 运行中的多次工具调用共享 sandbox。
- `runtime.context` 让 after_agent 能知道该释放哪个 sandbox。
- 缺少 `thread_id` 会抛 `SandboxRuntimeError`。

## 本地沙箱路径模型

线程级目录来自 `ThreadDataMiddleware`：

```text
backend/.deer-flow/users/{user_id}/threads/{thread_id}/user-data/
  ├─ workspace/
  ├─ uploads/
  └─ outputs/
```

工具对 LLM 暴露的是虚拟路径，例如：

```text
/mnt/user-data/workspace
/mnt/user-data/uploads
/mnt/user-data/outputs
/mnt/skills
```

本地执行时会转换到主机真实路径。

### 路径安全函数

重点阅读：

- `_reject_path_traversal()`
- `validate_local_tool_path()`
- `_resolve_and_validate_user_data_path()`
- `validate_local_bash_command_paths()`
- `replace_virtual_paths_in_command()`
- `mask_local_paths_in_output()`

设计目的：

- 防止 `..` 越权访问。
- 防止 bash 命令操作线程目录之外的主机路径。
- 输出中隐藏主机真实路径，统一显示虚拟路径。
- 对 custom mount、skills path、ACP workspace 做例外处理。

## 典型工具调用链

### `bash`

```text
LLM tool_call bash(description, command)
  -> _bash_tool_async(runtime, description, command)
  -> ensure_sandbox_initialized_async(runtime)
  -> asyncio.to_thread(bash_tool.func, ...)
  -> bash_tool()
      -> ensure_sandbox_initialized(runtime)
      -> if local sandbox:
           is_host_bash_allowed()
           ensure_thread_directories_exist()
           validate_local_bash_command_paths()
           replace_virtual_paths_in_command()
           _apply_cwd_prefix()
           sandbox.execute_command(command)
           mask_local_paths_in_output()
           _truncate_bash_output()
      -> else:
           sandbox.execute_command(command)
           _truncate_bash_output()
```

### `read_file`

```text
LLM tool_call read_file(path)
  -> _read_file_tool_async(...)
  -> ensure_sandbox_initialized_async()
  -> asyncio.to_thread(read_file_tool.func, ...)
  -> read_file_tool()
      -> validate_local_tool_path(path, read_only=True)
      -> resolve skills/acp/custom/user-data path
      -> sandbox.read_file(path)
      -> optional line slicing
      -> _truncate_read_file_output()
```

### `write_file`

```text
LLM tool_call write_file(path, content)
  -> _write_file_tool_async(...)
  -> ensure_sandbox_initialized_async()
  -> asyncio.to_thread(write_file_tool.func, ...)
  -> write_file_tool()
      -> validate_local_tool_path(path)
      -> resolve user-data path
      -> get_file_operation_lock(sandbox, path)
      -> sandbox.write_file(path, content, append)
```

## MCP 工具

本质解释：MCP 把外部能力变成工具，但外部 server 的连接和 schema 拉取都有成本，也可能失败。缓存的意义是把“发现工具”和“运行 agent”解耦，让 agent 构造更稳定。

关键文件：

- `backend/packages/harness/deerflow/mcp/cache.py`
- `backend/packages/harness/deerflow/mcp/tools.py`
- `backend/packages/harness/deerflow/mcp/session_pool.py`
- `backend/packages/harness/deerflow/tools/builtins/tool_search.py`

高层链路：

```text
Gateway startup or config reload
  -> initialize_mcp_tools()
  -> cache tools

Agent construction
  -> get_available_tools(include_mcp=True)
  -> get_cached_mcp_tools()
  -> tag_mcp_tool(tool)
  -> filter_tools_by_skill_allowed_tools()
  -> _assemble_deferred()
      -> build_deferred_tool_setup()
      -> final_tools include tool_search
```

MCP 调用链：

```text
LLM calls promoted MCP tool
  -> _make_session_pool_tool()
  -> call_with_persistent_session()
  -> MCPSessionPool.get_session(...)
  -> session.call_tool(...)
  -> _convert_call_tool_result(...)
```

## 子代理工具

文件：`backend/packages/harness/deerflow/tools/builtins/task_tool.py`

主链路：

```text
主 Agent LLM
  -> tool_call task(description, prompt, subagent_type)
  -> task_tool()
      -> get_subagent_config()
      -> resolve_subagent_model_name()
      -> SubagentExecutor.execute_async(prompt)
      -> poll get_background_task_result(task_id)
      -> get_stream_writer() 推送进度
      -> cache subagent token usage
      -> return final text to主 Agent
```

token 用量：

- 子代理用量按 `tool_call_id` 缓存在 `_subagent_usage_cache`。
- `TokenUsageMiddleware` 后续调用 `pop_cached_subagent_usage()` 合并到父 AIMessage。

## 源码精读顺序

工具系统建议按“工具从哪里来 -> 如何被过滤 -> 如何执行 -> 如何写回状态”的顺序读。

| 顺序 | 文件/函数 | 先回答的问题 |
| --- | --- | --- |
| 1 | `tools/tools.py::get_available_tools()` | 候选工具全集从哪里收集？ |
| 2 | `mcp/cache.py` | MCP 工具为什么要缓存？缓存什么时候刷新？ |
| 3 | `agent.py::_assemble_deferred()` | 哪些工具直接暴露，哪些进入 deferred catalog？ |
| 4 | `tools/builtins/tool_search.py` | `tool_search` 如何搜索并提升 deferred tool？ |
| 5 | `sandbox/sandbox_provider.py` | 沙箱实例如何获取？ |
| 6 | `community/aio_sandbox/` | 本地/远端 sandbox backend 如何执行命令或文件操作？ |
| 7 | `tools/builtins/task_tool.py` | 子代理工具如何启动后台任务并返回结果？ |
| 8 | `agents/middlewares/*tool*` | 工具错误、工具输出、工具权限在哪里处理？ |

## 工具排查路线

当你发现“某个工具没有被模型调用/没有出现/调用失败”时，按这个顺序查：

```text
1. get_available_tools() 是否收到了这个工具？
2. skill allowed-tools 是否把它过滤掉？
3. _assemble_deferred() 是否把它移入 deferred catalog？
4. 如果是 MCP 工具，get_cached_mcp_tools() 是否有缓存？
5. 如果是 sandbox 工具，runtime.context 里是否有 thread_id/run_id/user_id？
6. 如果执行时报错，ToolErrorHandlingMiddleware 是否转成 ToolMessage？
7. 如果输出太长，ToolOutputBudgetMiddleware/截断逻辑是否介入？
```

## 必须盯住的上下文

| 上下文 | 谁安装 | 谁读取 | 为什么重要 |
| --- | --- | --- | --- |
| `runtime.context["thread_id"]` | `run_agent()` | 上传、沙箱、线程目录、工具 | 决定工具操作属于哪个线程 |
| `runtime.context["run_id"]` | `run_agent()` | RunJournal、审计、进度 | 决定工具事件归属哪个 run |
| `runtime.context["user_id"]` | `services.inject_authenticated_user_context()` + `run_agent()` | 用户隔离、repository、memory | 防止跨用户读写 |
| `runtime.store` | `run_agent()` | LangGraph 工具运行时 | 访问持久 store |
| `ThreadState.promoted` | `DeferredToolFilterMiddleware` / `tool_search` | deferred tool 逻辑 | 记录哪些工具已经提升 |

## 自测题

1. 为什么 MCP 工具不一定直接暴露给模型？
2. `tool_search` 和普通搜索工具有什么区别？
3. sandbox 工具为什么不能只依赖当前 HTTP request？
4. 子代理工具的 token 用量为什么要缓存再合并？
5. 如果一个工具需要访问上传文件，你会检查哪些 context 字段？
