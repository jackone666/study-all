# Run 主调用链：HTTP/SSE 到 LangGraph

本文件按方法级别追踪一次用户聊天请求。最常见入口是：

```http
POST /api/threads/{thread_id}/runs/stream
```

先抓本质：这条链路不是“一个 HTTP 请求里直接跑完 agent”。它解决的是三个生命周期不一致的问题：

- HTTP handler 要尽快返回 SSE response。
- Agent run 是后台长任务，可能持续很久。
- 前端 SSE 连接可能断开、重连或取消。

所以 DeerFlow 把一次请求拆成三部分：router 负责接入 HTTP，service 负责创建 run，worker 负责真正执行 agent，`StreamBridge` 负责把后台事件送回 SSE。

## 1. 路由入口：`stream_run()`

文件：`backend/app/gateway/routers/thread_runs.py`

调用链：

```text
stream_run(thread_id, body, request)
  -> get_stream_bridge(request)
  -> get_run_manager(request)
  -> start_run(body, thread_id, request)
  -> StreamingResponse(sse_consumer(...))
```

核心行为：

- 校验权限：`@require_permission("runs", "create", owner_check=True, require_existing=True)`。
- 创建后台 run，但 HTTP handler 不等待 agent 完成。
- 返回 `StreamingResponse`，让 `sse_consumer()` 持续从 `StreamBridge` 拉事件。
- 设置 `Content-Location`，兼容 LangGraph SDK 的 run id 提取逻辑。

阅读重点：

- `stream_run()` 自己不构造 agent，不处理模型，也不碰 checkpoint。
- 它只是把 HTTP/SSE 连接和后端 run 生命周期接起来。

本质解释：router 是协议适配层。它只应该理解 HTTP、权限、响应格式，不应该理解 agent 的内部构造。这样以后换运行时或调整 agent 工厂，不需要改 HTTP 入口。

## 2. 服务层：`start_run()`

文件：`backend/app/gateway/services.py`

调用链：

```text
start_run(body, thread_id, request)
  -> get_stream_bridge(request)
  -> get_run_manager(request)
  -> get_run_context(request)
  -> validate model_name
  -> run_mgr.create_or_reject(...)
  -> thread_store.get(thread_id)
  -> thread_store.create(...) or update_status("running")
  -> resolve_agent_factory(body.assistant_id)
  -> normalize_input(body.input)
  -> build_run_config(thread_id, body.config, body.metadata, assistant_id)
  -> merge_run_context_overrides(config, body.context)
  -> inject_authenticated_user_context(config, request)
  -> normalize_stream_modes(body.stream_mode)
  -> asyncio.create_task(run_agent(...))
  -> record.task = task
  -> return record
```

### 输入转换：`normalize_input()`

作用：把 LangGraph Platform 风格的消息 dict 转为 LangChain `BaseMessage`。

关键点：

- 使用 `convert_to_messages()`，保留 `additional_kwargs`、`id`、`name`。
- 出错时抛 `HTTPException(400)`，而不是让无效消息冒泡成 500。
- 这是上传文件元数据等前端附加字段不丢失的关键。

### 配置构造：`build_run_config()`

作用：创建 LangGraph `RunnableConfig` 字典。

本质解释：`RunnableConfig` 是把外部请求带进 LangGraph 世界的“运行说明书”。它不只是参数字典，还决定后续 agent、middleware、tool 能读到哪些上下文。

重点字段：

- `recursion_limit: 100`
- `configurable.thread_id`
- `context` 或 `configurable`
- `metadata`
- `run_name`
- 自定义 agent 时注入 `agent_name`

### 上下文合并：`merge_run_context_overrides()`

只转发白名单字段：

- `model_name`
- `mode`
- `thinking_enabled`
- `reasoning_effort`
- `is_plan_mode`
- `subagent_enabled`
- `max_concurrent_subagents`
- `agent_name`
- `is_bootstrap`

这些字段同时写入 `config["configurable"]` 和 `config["context"]`，兼容旧读取方式和 LangGraph 新的 `ToolRuntime.context`。

本质解释：`configurable` 更像 LangGraph/LangChain 的传统配置通道，`context` 更像 DeerFlow 自己给工具和 middleware 的运行上下文。两边同时写，是为了让旧代码和新运行时都能读到同一份事实。

### 用户注入：`inject_authenticated_user_context()`

从 `request.state.user` 写入：

```python
config["context"]["user_id"] = str(user.id)
```

注意：

- 它使用服务端认证结果。
- 不信任客户端传来的 `body.context.user_id`。
- 内部系统角色 `INTERNAL_SYSTEM_ROLE` 不写入用户上下文。

本质解释：`user_id` 不是普通配置，而是安全边界。客户端可以请求某些运行选项，但不能声明“我是谁”。用户身份必须来自认证中间件，再由服务端注入后台运行上下文。

## 3. Run 状态机：`RunManager.create_or_reject()`

文件：`backend/packages/harness/deerflow/runtime/runs/manager.py`

调用链：

```text
create_or_reject(thread_id, assistant_id, ...)
  -> acquire self._lock
  -> validate multitask_strategy
  -> find inflight runs for same thread
  -> reject / interrupt / rollback
  -> create RunRecord(status=pending)
  -> self._runs[run_id] = record
  -> _persist_new_run_to_store(record)
  -> cancel inflight runs if needed
  -> release lock
  -> _persist_status(interrupted_record, interrupted)
  -> return record
```

### 支持的并发策略

| 策略 | 行为 |
| --- | --- |
| `reject` | 同线程已有 pending/running run 时返回 409 |
| `interrupt` | 取消旧 run，保留已产生的检查点 |
| `rollback` | 取消旧 run，并在 worker 中尝试回滚到本轮前检查点 |

### 为什么要在锁内创建并插入

`has_inflight()` 再 `create()` 会有 TOCTOU 竞态。这里用同一把 `asyncio.Lock` 覆盖“检查活跃 run + 插入新 run”的窗口。

本质解释：`RunManager` 管的是 run 的控制面状态，不管 agent 对话内容。它要保证同一个 thread 下不会出现两个互相踩踏的后台任务。锁保护的不是数据库本身，而是“判断是否已有运行中任务”和“登记新任务”这两个动作的原子性。

## 4. 后台 worker：`run_agent()`

文件：`backend/packages/harness/deerflow/runtime/runs/worker.py`

主调用链：

```text
run_agent(...)
  -> create RunJournal if event_store exists
  -> run_manager.set_status(running)
  -> capture pre-run checkpoint
  -> bridge.publish("metadata", {run_id, thread_id})
  -> _build_runtime_context(thread_id, run_id, config.context, app_config)
  -> _install_runtime_context(config, runtime_ctx)
  -> Runtime(context=runtime_ctx, store=store)
  -> config["configurable"]["__pregel_runtime"] = runtime
  -> config["callbacks"].append(journal)
  -> inject_langfuse_metadata(...)
  -> RunnableConfig(**config)
  -> agent_factory(config=runnable_config, app_config=...)
  -> agent.checkpointer = checkpointer
  -> agent.store = store
  -> agent.astream(graph_input, config=runnable_config, stream_mode=...)
  -> bridge.publish(run_id, sse_event, serialize(chunk, mode=mode))
  -> set final status
  -> journal.flush()
  -> run_manager.update_run_completion(...)
  -> sync title to thread_store
  -> thread_store.update_status(...)
  -> bridge.publish_end(run_id)
  -> bridge.cleanup(run_id, delay=60)
```

### 最重要的对象：`runtime_ctx`

`_build_runtime_context()` 最少包含：

```python
{
    "thread_id": thread_id,
    "run_id": run_id,
    "app_config": app_config,
    "__run_journal": journal,
}
```

意义：

- 工具和中间件通过 `runtime.context` 拿到 `thread_id/run_id`。
- `setup_agent`、上传、沙箱路径、用户隔离等逻辑依赖这些字段。
- `__run_journal` 是内部通道，供中间件写审计和 token 事件。

本质解释：`runtime_ctx` 是从 HTTP 世界进入 agent/tool 世界时随身携带的事实包。后台 task 不能再依赖 `request`，所以必须把 `thread_id`、`run_id`、`user_id`、`app_config` 这类事实安装进 LangGraph runtime。

### 为什么手动设置 `__pregel_runtime`

Gateway 直接调用 `agent.astream(config=...)`，不像 langgraph-cli 自动传 context。这里手动创建 `Runtime` 并塞进：

```python
config["configurable"]["__pregel_runtime"] = runtime
```

这样 LangGraph 1.1+ 的工具运行时才能看到 `runtime.context`。

## 5. SSE 桥：`MemoryStreamBridge`

文件：`backend/packages/harness/deerflow/runtime/stream_bridge/memory.py`

本质解释：`StreamBridge` 是后台 worker 和 HTTP SSE response 之间的缓冲桥。worker 只管生产事件，SSE consumer 只管消费事件，中间靠 `run_id` 对齐。这样才能支持断线重连、heartbeat、后台继续执行和按策略取消。

发布链：

```text
run_agent()
  -> bridge.publish(run_id, event, data)
  -> MemoryStreamBridge.publish()
  -> append StreamEvent to _RunStream.events
  -> condition.notify_all()
```

订阅链：

```text
sse_consumer()
  -> bridge.subscribe(run_id, last_event_id)
  -> MemoryStreamBridge.subscribe()
  -> yield retained events
  -> wait condition or heartbeat timeout
  -> yield HEARTBEAT_SENTINEL / END_SENTINEL / StreamEvent
```

### `Last-Event-ID`

`_resolve_start_offset()` 支持从 `Last-Event-ID` 后继续回放。若 ID 不在保留缓冲中，会从最早保留事件开始。

### 断开连接

`sse_consumer()` 的 `finally`：

```text
if record.status in pending/running:
  if record.on_disconnect == cancel:
    run_mgr.cancel(record.run_id)
```

`wait_for_run_completion()` 也复用同一套桥接器，避免非流式 `/wait` 在客户端断开后错误返回半成品 checkpoint。

## 6. 终态与清理

`run_agent()` 最终会：

- 成功：`RunStatus.success`
- 用户中断：`RunStatus.interrupted`
- rollback：`RunStatus.error` + 尝试恢复 checkpoint
- LLM fallback 错误：`RunStatus.error`
- 未捕获异常：`RunStatus.error` + 发布 SSE `error`

最后一定调用：

```text
bridge.publish_end(run_id)
asyncio.create_task(bridge.cleanup(run_id, delay=60))
```

这保证前端 SSE 不悬挂。

本质解释：`interrupt` 只关心“停下来”，`rollback` 还关心“恢复到本轮 run 开始前”。所以 rollback 不能只取消 task，还必须依赖 worker 开始时捕获的 pre-run checkpoint。

## 7. 源码精读顺序

不要从 `run_agent()` 第一行开始硬读。建议按下面顺序逐层深入：

| 顺序 | 函数 | 先回答的问题 |
| --- | --- | --- |
| 1 | `thread_runs.py::stream_run()` | HTTP handler 做了什么、没有做什么？ |
| 2 | `services.py::start_run()` | 请求体如何变成 `RunRecord`、`graph_input`、`RunnableConfig`？ |
| 3 | `manager.py::RunManager.create_or_reject()` | 同线程并发 run 如何处理？ |
| 4 | `worker.py::run_agent()` 前半段 | runtime context、journal、checkpointer 如何安装？ |
| 5 | `worker.py::run_agent()` 执行循环 | `agent.astream()` 的 chunk 如何变成 SSE？ |
| 6 | `memory.py::MemoryStreamBridge.subscribe()` | 断线重连和 heartbeat 如何工作？ |
| 7 | `worker.py::run_agent()` finally | 终态、journal flush、thread status、bridge cleanup 如何保证执行？ |

每读一个函数，都用下面模板写一行自己的笔记：

```text
函数：
调用方：
下一跳：
关键输入：
关键输出：
副作用：
失败路径：
```

## 8. 关键变量追踪表

| 变量 | 首次出现 | 后续用途 | 阅读时要确认 |
| --- | --- | --- | --- |
| `thread_id` | URL path | run 归属、checkpoint key、thread metadata、runtime context | 是否始终来自服务端路径 |
| `run_id` | `RunManager.create_or_reject()` | SSE channel、RunJournal、run store、runtime context | 创建后是否所有事件都使用同一个 id |
| `assistant_id` | request body | agent factory 解析、run metadata、run name 默认值 | 当前是否都落到 `make_lead_agent` |
| `graph_input` | `normalize_input()` | 传给 `agent.astream()` | 消息 dict 是否保留 `additional_kwargs` |
| `config` | `build_run_config()` | LangGraph `RunnableConfig`、runtime context 安装 | `context` 和 `configurable` 是否同步写入 |
| `record` | `RunManager.create_or_reject()` | 状态机、取消事件、后台 task 引用 | task 什么时候挂回 `record.task` |
| `bridge` | app state | worker 发布事件、SSE consumer 订阅事件 | publish 和 subscribe 是否通过同一个 `run_id` |
| `journal` | `run_agent()` | callback、event store、completion data | 什么时候 flush，失败时是否也 flush |

## 9. 方法级调用图

这一段适合读源码时放在旁边对照：

```text
stream_run()
  -> get_stream_bridge(request)
  -> get_run_manager(request)
  -> start_run(...)
      -> get_run_context(request)
      -> app_config.get_model_config(model_name)
      -> run_mgr.create_or_reject(...)
          -> _persist_new_run_to_store(record)
          -> _persist_status(interrupted_record, interrupted)
      -> thread_store.get(thread_id)
      -> thread_store.create(...) / update_status(...)
      -> resolve_agent_factory(assistant_id)
      -> normalize_input(body.input)
      -> build_run_config(...)
      -> merge_run_context_overrides(config, body.context)
      -> inject_authenticated_user_context(config, request)
      -> normalize_stream_modes(body.stream_mode)
      -> asyncio.create_task(run_agent(...))
  -> StreamingResponse(sse_consumer(...))

run_agent()
  -> run_manager.set_status(run_id, running)
  -> checkpointer.aget_tuple(...)
  -> bridge.publish(run_id, "metadata", ...)
  -> _build_runtime_context(...)
  -> _install_runtime_context(config, runtime_ctx)
  -> Runtime(context=runtime_ctx, store=store)
  -> agent_factory(config=runnable_config, app_config=...)
  -> agent.astream(graph_input, config=runnable_config, stream_mode=...)
  -> bridge.publish(run_id, sse_event, serialized_chunk)
  -> run_manager.set_status(... final ...)
  -> journal.flush()
  -> run_manager.update_run_completion(...)
  -> thread_store.update_status(...)
  -> bridge.publish_end(run_id)
  -> bridge.cleanup(run_id, delay=60)
```

注意：`start_run()` 的职责是“创建后台 run 并返回记录”，`run_agent()` 的职责是“执行 run 并维护运行时状态”。不要把这两个函数混成一个概念。

## 10. 自测题

读完本章后，尝试不看笔记回答：

1. 为什么 `stream_run()` 返回 SSE 时 agent 可能还没真正开始执行？
2. `RunRecord.status` 从 `pending` 到 `running` 是谁改的？
3. `rollback` 为什么不能只在 `RunManager` 中完成？
4. `Last-Event-ID` 解决了什么问题？
5. 如果前端断开连接，后端什么时候会取消后台 task？
6. 如果 `agent.astream()` 抛异常，SSE、run store、journal 分别会发生什么？
