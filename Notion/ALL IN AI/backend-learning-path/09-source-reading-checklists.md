# 09. 源码阅读清单

这个文件用于确认“我真的读过并理解了源码”，而不是只看过学习笔记。建议每次学习只勾一个小节。

## 1. Gateway 和启动

- [ ] 读完 `backend/app/gateway/app.py::lifespan()`。
- [ ] 能说出 `app.state` 中有哪些运行时对象。
- [ ] 读完 `backend/app/gateway/deps.py` 中的 runtime 获取函数。
- [ ] 能解释 `get_run_context(request)` 返回的对象包含什么。
- [ ] 能区分 Gateway 层的职责和 `packages/harness/deerflow` 的职责。

自测：

```text
为什么运行时对象要挂在 app.state，而不是每个请求重新创建？
```

## 2. Run API 入口

- [ ] 读完 `backend/app/gateway/routers/thread_runs.py::stream_run()`。
- [ ] 找到 `@require_permission(...)` 并理解它保护的资源。
- [ ] 能解释 `StreamingResponse` 返回时后台 run 的状态。
- [ ] 能找到 `sse_consumer()` 如何订阅 `StreamBridge`。
- [ ] 能解释 `Content-Location` 的作用。

自测：

```text
router 为什么不直接调用 `agent.astream()`？
```

## 3. Service 层

- [ ] 读完 `backend/app/gateway/services.py::start_run()`。
- [ ] 读完 `normalize_input()`。
- [ ] 读完 `build_run_config()`。
- [ ] 读完 `merge_run_context_overrides()`。
- [ ] 读完 `inject_authenticated_user_context()`。
- [ ] 能说出 `graph_input`、`config`、`record` 分别是什么。

自测：

```text
`body.context` 中哪些字段会被转发？哪些字段不能信任？
```

## 4. RunManager

- [ ] 读完 `RunManager.create_or_reject()`。
- [ ] 能解释 `reject`、`interrupt`、`rollback` 的差异。
- [ ] 找到 `RunRecord` 的字段定义。
- [ ] 读完 `_persist_new_run_to_store()`。
- [ ] 读完 `set_status()` 和 `update_run_completion()`。
- [ ] 能解释为什么检查 inflight run 和插入新 run 要在同一把锁里。

自测：

```text
如果持久化新 run 失败，内存中的 run 为什么必须回滚？
```

## 5. Worker

- [ ] 读完 `backend/packages/harness/deerflow/runtime/runs/worker.py::run_agent()`。
- [ ] 读完 `_build_runtime_context()`。
- [ ] 读完 `_install_runtime_context()`。
- [ ] 读完 `_rollback_to_pre_run_checkpoint()`。
- [ ] 能解释 `Runtime(context=..., store=...)` 的用途。
- [ ] 能指出 `agent.checkpointer` 和 `agent.store` 在哪里挂载。
- [ ] 能解释 `journal.flush()` 为什么在 finally 路径也重要。

自测：

```text
工具为什么能在没有 HTTP request 的后台任务里拿到 `thread_id/run_id/user_id`？
```

## 6. StreamBridge 和 SSE

- [ ] 读完 `MemoryStreamBridge.publish()`。
- [ ] 读完 `MemoryStreamBridge.subscribe()`。
- [ ] 读完 `publish_end()`。
- [ ] 读完 `cleanup()`。
- [ ] 能解释 `Last-Event-ID` 如何影响回放起点。
- [ ] 能解释 heartbeat 的意义。

自测：

```text
如果 worker 已经结束但 SSE consumer 没收到 end，会出现什么用户体验问题？
```

## 7. Lead Agent

- [ ] 读完 `make_lead_agent()`。
- [ ] 读完 `_make_lead_agent()`。
- [ ] 读完 `_get_runtime_config()`。
- [ ] 读完 `_resolve_model_name()`。
- [ ] 读完 `_build_middlewares()`。
- [ ] 读完 `_assemble_deferred()`。
- [ ] 能解释 `create_agent()` 的主要参数来自哪里。

自测：

```text
`_make_lead_agent()` 是构造 agent，还是执行 agent？执行发生在哪里？
```

## 8. Middleware

- [ ] 找到 `ThreadDataMiddleware` 的职责。
- [ ] 找到 `UploadsMiddleware` 的职责。
- [ ] 找到 `SandboxMiddleware` 的职责。
- [ ] 找到 `DynamicContextMiddleware` 的职责。
- [ ] 找到 `SummarizationMiddleware` 的职责。
- [ ] 找到 `MemoryMiddleware` 的职责。
- [ ] 找到 `DeferredToolFilterMiddleware` 的职责。
- [ ] 找到 `SubagentLimitMiddleware` 的职责。

自测：

```text
为什么 middleware 顺序会影响最终 agent 行为？
```

## 9. 工具系统

- [ ] 读完 `tools/tools.py::get_available_tools()`。
- [ ] 找到内置工具列表。
- [ ] 找到 MCP 工具加入的位置。
- [ ] 找到 ACP agent tool 加入的位置。
- [ ] 读完 skill allowed-tools 过滤逻辑。
- [ ] 读完 `tool_search` deferred tool 逻辑。
- [ ] 能解释工具执行失败如何变成模型可见的消息。

自测：

```text
一个工具没有出现在模型 schema 中，可能有哪些原因？
```

## 10. Sandbox

- [ ] 读完 `sandbox_provider.py`。
- [ ] 读完 `community/aio_sandbox` 中 provider/backend 的核心类。
- [ ] 能区分 sandbox provider 和 sandbox backend。
- [ ] 能解释 thread 目录和 sandbox 文件操作的关系。
- [ ] 能指出沙箱审计事件在哪里记录。

自测：

```text
sandbox 生命周期为什么不能只由工具函数自己管理？
```

## 11. 状态和持久化

- [ ] 读完 `ThreadState` schema。
- [ ] 读完 artifacts/todos/uploads/viewed_images/promoted 的 reducer。
- [ ] 找到 checkpointer 挂载点。
- [ ] 找到 run store 写入点。
- [ ] 找到 thread store 写入点。
- [ ] 找到 event store 写入点。
- [ ] 能解释 checkpoint、store、journal、run store 的区别。

自测：

```text
如果只想恢复 LangGraph 图状态，应该看 run store 还是 checkpointer？
```

## 12. 用户隔离

- [ ] 找到认证中间件设置 `request.state.user` 的位置。
- [ ] 读完 `inject_authenticated_user_context()`。
- [ ] 找到 runtime user resolver。
- [ ] 找到 repository 的 `user_id=AUTO` 语义。
- [ ] 能解释 `None`、`AUTO`、显式字符串三种 user_id 的区别。

自测：

```text
为什么客户端传来的 `body.context.user_id` 不能直接使用？
```

## 13. 上传、记忆、频道

- [ ] 读完 uploads router 的入口。
- [ ] 找到上传元数据如何进入消息或线程上下文。
- [ ] 读完 memory queue 的 add/clear/flush 相关逻辑。
- [ ] 找到 IM channel manager 的入口。
- [ ] 能解释这些外围能力如何复用主 run 生命周期。

自测：

```text
上传、记忆、频道这些能力为什么不应该绕过 `RunManager`？
```
