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

