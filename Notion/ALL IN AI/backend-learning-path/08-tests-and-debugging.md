# 测试与调试路线

## 推荐测试入口

在 `backend/` 目录下：

```bash
uv run pytest tests/test_runs_api_endpoints.py -q
uv run pytest tests/test_run_manager.py -q
uv run pytest tests/test_runtime_lifecycle_e2e.py -q
uv run pytest tests/test_threads_router.py -q
uv run pytest tests/test_uploads_router.py -q
uv run pytest tests/test_harness_boundary.py -q
uv run pytest tests/test_auth_middleware.py -q
uv run pytest tests/test_memory_router.py -q
uv run pytest tests/test_mcp_session_pool.py -q
uv run pytest tests/test_sandbox_tools_security.py -q
```

## 按主题找测试

| 主题 | 测试文件 |
| --- | --- |
| Run API | `test_runs_api_endpoints.py`, `test_thread_run_messages_pagination.py` |
| Run 状态机 | `test_run_manager.py`, `test_cancel_run_idempotent.py`, `test_gateway_run_recovery.py` |
| Stream/SSE | `test_sse_format.py`, `test_stream_bridge.py`, `test_wait_disconnect_handling.py` |
| Agent 创建 | `test_create_deerflow_agent.py`, `test_lead_agent_model_resolution.py`, `test_lead_agent_prompt.py` |
| 中间件 | `test_*_middleware.py` |
| 沙箱 | `test_sandbox_tools_security.py`, `test_local_sandbox_provider_mounts.py`, `test_aio_sandbox*.py` |
| MCP | `test_mcp_*.py`, `test_tool_search.py` |
| 技能 | `test_skills_*.py`, `test_skill_manage_tool.py` |
| 记忆 | `test_memory_*.py` |
| 上传 | `test_uploads_router.py`, `test_uploads_middleware_core_logic.py` |
| 鉴权 | `test_auth*.py`, `test_owner_isolation.py`, `test_internal_auth.py` |
| IM 频道 | `test_dingtalk_channel.py`, `test_discord_channel.py`, `test_wechat_channel.py` |

## 调试一次聊天请求

### 从前端触发

前端最常用的触发方式：

```text
打开工作区聊天页
  -> 进入一个 thread，或打开 /workspace/chats/new
  -> 在底部输入框输入一条消息
  -> 点击发送按钮，或按 Enter
  -> 前端开始 streaming
```

这会经过前端链路：

```text
frontend/src/components/workspace/chats/use-thread-chat.ts
  -> 生成或读取 threadId

frontend/src/core/threads/hooks.ts
  -> thread.submit(...)
  -> context 中写入 mode/model_name/thinking_enabled/is_plan_mode/subagent_enabled/thread_id

frontend/src/core/api/api-client.ts
  -> getAPIClient()
  -> client.runs.stream(...)
  -> sanitizeRunStreamOptions(...)
  -> LangGraph SDK 发起 stream 请求

Gateway
  -> POST /api/threads/{thread_id}/runs/stream
```

本质解释：前端不是手写 `fetch("/api/threads/.../runs/stream")`，而是通过 LangGraph SDK 的 `client.runs.stream()` 触发。`api-client.ts` 做了一层兼容包装，负责 CSRF、stream mode 清洗、断线重连错误处理。

建议断点顺序：

1. `backend/app/gateway/routers/thread_runs.py::stream_run`
2. `backend/app/gateway/services.py::start_run`
3. `backend/packages/harness/deerflow/runtime/runs/manager.py::RunManager.create_or_reject`
4. `backend/packages/harness/deerflow/runtime/runs/worker.py::run_agent`
5. `backend/packages/harness/deerflow/agents/lead_agent/agent.py::make_lead_agent`
6. `backend/packages/harness/deerflow/agents/lead_agent/agent.py::_make_lead_agent`
7. `backend/packages/harness/deerflow/tools/tools.py::get_available_tools`
8. `backend/packages/harness/deerflow/runtime/stream_bridge/memory.py::MemoryStreamBridge.publish`
9. `backend/app/gateway/services.py::sse_consumer`

前端同时可以观察：

- 浏览器 DevTools -> Network：找 `/api/threads/{thread_id}/runs/stream` 或 `/api/langgraph/threads/{thread_id}/runs/stream`。
- Request Payload：看 `input.messages`、`config`、`context`。
- Response/EventStream：看 `metadata`、`messages`、`values`、`updates`、`end` 等事件。
- Console：`api-client.ts` 会输出 `Creating API client with base URL: ...`。

重点对照字段：

| 前端字段 | 来源 | 后端观察点 |
| --- | --- | --- |
| `threadId` | `use-thread-chat.ts` | `stream_run(thread_id=...)` |
| `messages` | `hooks.ts::thread.submit()` | `services.normalize_input()` |
| `context.model_name` | 聊天上下文/模型选择 | `start_run()` 模型校验、`_resolve_model_name()` |
| `context.mode` | 前端聊天模式 | `merge_run_context_overrides()` |
| `thinking_enabled` | `mode !== "flash"` | `_get_runtime_config()` |
| `is_plan_mode` | `mode === "pro" || mode === "ultra"` | `_build_middlewares()` / `TodoMiddleware` |
| `subagent_enabled` | `mode === "ultra"` | `get_available_tools()` 是否加入 `task_tool` |
| `streamSubgraphs` | `thread.submit()` options | `RunCreateRequest.stream_subgraphs` |
| `streamResumable` | `thread.submit()` options | SSE 断点续传相关行为 |

### 前端操作和后端流程对应表

| 前端操作 | 会触发的后端流程 | 推荐断点 |
| --- | --- | --- |
| 新聊天页发送普通消息 | 创建 thread id、创建 run、启动 Lead Agent、SSE 返回 | `stream_run()`、`start_run()`、`run_agent()`、`_make_lead_agent()` |
| 在已有 thread 里继续发送 | 同一个 `thread_id` 下创建新的 run，读取旧 checkpoint | `start_run()`、`checkpointer.aget_tuple()`、`agent.astream()` |
| 选择 flash/pro/ultra 等模式后发送 | 写入 `context.mode`，影响 thinking、plan mode、subagent | `merge_run_context_overrides()`、`_get_runtime_config()`、`_build_middlewares()` |
| 选择具体模型后发送 | 写入 `context.model_name`，后端先校验再解析模型 | `start_run()` 的 `get_model_config()`、`_resolve_model_name()` |
| 上传文件后发送 | 先走 upload API，再把 files 放入 message `additional_kwargs` | uploads router、`normalize_input()`、`UploadsMiddleware` |
| 等待回复完成 | SSE 收到 end，前端状态从 streaming 结束 | `MemoryStreamBridge.publish_end()`、`sse_consumer()` |
| 回复完成后出现追问建议 | 前端额外请求 suggestions 接口 | `POST /api/threads/{thread_id}/suggestions` |
| 刷新页面后回到同一 thread | 前端加载历史消息/状态，必要时尝试 join stream | runs messages/history、`joinStream()`、`stream_existing_run()` |

### 推荐 Debug 流程

1. 前端打开 DevTools Network，清空请求列表。
2. 后端在 `stream_run()`、`start_run()`、`run_agent()`、`_make_lead_agent()` 打断点。
3. 前端发送一句简单消息，例如：

```text
你好，简单介绍一下你能做什么
```

4. 命中 `stream_run()` 时，先记录 `thread_id` 和 request body。
5. 命中 `start_run()` 时，观察 `body.context`、`model_name`、`stream_mode`。
6. 命中 `run_agent()` 时，观察 `run_id`、`runtime_ctx`、`config["context"]`。
7. 命中 `_make_lead_agent()` 时，观察 `model_name`、`is_plan_mode`、`subagent_enabled`、`final_tools`、`middleware`。
8. 回到浏览器 Network，看 EventStream 是否持续收到事件。

判断链路跑通的最小证据：

```text
前端 status=streaming
  -> Network 出现 runs/stream
  -> 后端 stream_run 命中
  -> RunManager 创建 RunRecord
  -> run_agent 发布 metadata
  -> EventStream 收到 metadata/message/end
```

### 调试时常见前端误判

- 看到 URL 是 `/api/langgraph/...` 不代表有单独 LangGraph 服务；前端 SDK 路径会被 Gateway 兼容处理。
- 新聊天页路径里的 `new` 不是真正 thread id，`use-thread-chat.ts` 会生成 UUID。
- 前端传了 `context.thread_id`，但后端真正的线程归属仍以 URL path 的 `thread_id` 为准。
- 前端显示 streaming 不等于模型已经开始输出；可能只是 run 已创建、SSE 已连接。
- 工具没有显示在 UI，不代表工具没加载；可能是 deferred tool，被 `tool_search` 按需提升。

## 调试工具不可用

检查顺序：

1. `config.yaml` 中是否配置了工具。
2. `get_available_tools()` 是否按 group 过滤掉了。
3. `is_host_bash_allowed()` 是否移除了 host bash。
4. 当前模型是否支持 vision，决定 `view_image_tool` 是否加入。
5. `subagent_enabled` 是否为 true，决定 `task_tool` 是否加入。
6. 技能 `allowed-tools` 是否过滤掉了工具。
7. `tool_search.enabled` 是否让 MCP 工具进入 deferred catalog。
8. `DeferredToolFilterMiddleware` 是否隐藏了未提升工具。

## 调试沙箱路径错误

重点断点：

- `ensure_sandbox_initialized_async()`
- `get_thread_data()`
- `validate_local_tool_path()`
- `_resolve_and_validate_user_data_path()`
- `validate_local_bash_command_paths()`
- `replace_virtual_paths_in_command()`

排查问题：

- `runtime.context["thread_id"]` 是否存在。
- `ThreadDataMiddleware` 是否写入 `thread_data`。
- 用户传入路径是否是 `/mnt/user-data/...` 虚拟路径。
- 是否触发 `..`、绝对路径越权或 custom mount 限制。
- host bash 是否被禁用。

## 调试 run 卡住

检查：

1. `RunRecord.status` 是否仍是 `running`。
2. `RunRecord.task.done()` 是否为 false。
3. `StreamBridge` 是否仍有 heartbeat。
4. `RunJournal.flush()` 是否卡在 event store。
5. 工具是否在同步阻塞路径中运行。
6. `tests/blocking_io/` 是否覆盖该路径。

相关命令：

```bash
cd backend
uv run pytest tests/blocking_io -q
uv run pytest tests/test_wait_disconnect_handling.py -q
```

## 调试用户隔离

重点对象：

- `request.state.user`
- `deerflow.runtime.user_context._current_user`
- `runtime.context["user_id"]`
- repository 方法的 `user_id` 参数

断点：

- `AuthMiddleware`
- `services.inject_authenticated_user_context()`
- `user_context.resolve_runtime_user_id()`
- `user_context.resolve_user_id()`
- `authz.require_permission()`

常见错误：

- 后台工具只依赖 ContextVar，脱离请求任务后拿不到用户。
- repository 意外传 `user_id=None`，导致绕过隔离。
- 内部系统角色不应写入普通用户上下文。

## 调试配置热加载

区分两类配置：

### 请求期配置

断点：

- `deps.get_config()`
- `get_app_config()`
- `_make_lead_agent(..., app_config=...)`

适合验证：

- 模型参数变更
- tool_search 开关
- token_usage 开关
- agent 配置

### 启动期配置

断点：

- `app.py::lifespan`
- `deps.langgraph_runtime`

适合验证：

- database backend
- checkpointer backend
- stream bridge backend
- run event store backend

这些变更通常需要重启 Gateway。
