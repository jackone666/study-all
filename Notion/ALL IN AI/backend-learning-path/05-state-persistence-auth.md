# 状态、持久化与用户隔离

先抓本质：这一章不是在讲“一种状态”，而是在区分多种状态分别服务什么问题。`ThreadState` 服务图执行恢复，`RunRecord` 服务 run 生命周期，`RunJournal` 服务过程追踪，`user_id` 服务数据隔离。混淆这些对象，是读后端最容易卡住的地方。

## 状态分层

| 层 | 对象 | 生命周期 | 用途 |
| --- | --- | --- | --- |
| HTTP 请求 | `Request` / `request.state.user` | 单请求 | 鉴权、权限判断 |
| Run 记录 | `RunRecord` | 单次 run | run 状态、task、token、错误 |
| LangGraph 状态 | `ThreadState` | 线程级 | messages、sandbox、title、artifacts 等 |
| Checkpoint | `checkpointer` | 持久化/内存 | 保存 LangGraph channel values |
| Store | `store` | 持久化/内存 | LangGraph thread metadata 等 |
| RunEvent | `RunJournal` + `RunEventStore` | run 事件日志 | 消息、LLM 请求响应、工具事件、审计 |
| SQL Repository | `persistence/*` | 数据库 | run、feedback、user、thread meta |

一个快速判断法：

- 想知道 agent 图里现在有什么，查 `ThreadState`/checkpoint。
- 想知道这次执行是否完成，查 `RunRecord`/run store。
- 想知道执行过程中发生了什么，查 `RunJournal`/event store。
- 想知道数据属于谁，沿着 `user_id` 查认证、runtime、repository。

## `ThreadState`

文件：`backend/packages/harness/deerflow/agents/thread_state.py`

本质解释：`ThreadState` 是 LangGraph 的线程级业务状态 schema。它不是 run 记录，也不是数据库模型，而是规定 agent 图的每一步可以读写哪些共享状态，以及这些状态如何通过 reducer 合并。

字段：

```text
messages       LangChain AgentState 继承字段
sandbox        当前 run/线程沙箱状态
thread_data    workspace/uploads/outputs 路径
title          线程标题
artifacts      生成文件和展示产物
todos          plan mode 待办事项
uploaded_files 上传文件元数据
viewed_images  已查看图片缓存
promoted       tool_search 提升过的延迟工具
```

重点 reducer：

- `merge_artifacts()`：新 artifact 覆盖旧 id，防止重复展示。
- `merge_viewed_images()`：支持合并和清空。
- `merge_todos()`：让 todo 状态可跨节点累积。
- `merge_promoted()`：按 catalog hash 记录 MCP 工具提升结果。

## Checkpointer

文件：`backend/packages/harness/deerflow/runtime/checkpointer/async_provider.py`

本质解释：checkpointer 回答的是“这个 thread 的图执行状态能不能恢复”。它保存的是 LangGraph checkpoint/channel values，不负责告诉 UI 某个 run 是否成功。

调用链：

```text
langgraph_runtime(app, startup_config)
  -> make_checkpointer(config)
      -> if app_config.checkpointer: _async_checkpointer(...)
      -> elif database backend != memory: _async_checkpointer_from_database(...)
      -> else InMemorySaver()
```

支持：

- memory
- sqlite
- postgres

SQLite 处理：

```text
resolve_sqlite_conn_str()
ensure_sqlite_parent_dir()
AsyncSqliteSaver.from_conn_string()
saver.setup()
```

Postgres 处理：

```text
_build_postgres_pool()
AsyncPostgresSaver(conn=pool)
saver.setup()
```

## Store

文件：`backend/packages/harness/deerflow/runtime/store/async_provider.py`

调用链：

```text
langgraph_runtime()
  -> make_store(config)
      -> if checkpointer config absent: InMemoryStore()
      -> else _async_store(app_config.checkpointer)
```

Store 和 checkpointer 使用同一后端配置，保证状态和元数据后端一致。

本质解释：store 是给 LangGraph runtime/tool 使用的长期数据空间。它和 checkpointer 经常使用同一后端配置，但语义不同：checkpointer 偏执行恢复，store 偏运行时数据访问。

## RunManager 与 RunStore

文件：`backend/packages/harness/deerflow/runtime/runs/manager.py`

本质解释：`RunManager` 管的是 run 的生命周期控制面。它关心 pending、running、success、error，关心 task、取消、并发策略和持久化状态；它不保存完整对话内容。

### 创建

```text
RunManager.create_or_reject()
  -> create RunRecord(status=pending)
  -> _persist_new_run_to_store(record)
  -> return record
```

### 状态更新

```text
set_status(run_id, status, error)
  -> update in-memory RunRecord
  -> _persist_status(record, status, error)
```

### 完成更新

```text
run_agent finally
  -> journal.get_completion_data()
  -> run_manager.update_run_completion(run_id, status=record.status.value, **completion)
```

保存字段包括：

- token 用量
- LLM 调用次数
- message_count
- first_human_message
- last_ai_message
- status/error

### SQLite 锁重试

`_call_store_with_retry()` 对 SQLite 瞬时锁错误做指数退避：

- `database is locked`
- `database table is locked`
- `database is busy`
- `SQLITE_BUSY`
- `SQLITE_LOCKED`

## RunJournal

文件：`backend/packages/harness/deerflow/runtime/journal.py`

本质解释：`RunJournal` 是运行过程的黑匣子。`RunRecord` 告诉你最终状态，`RunJournal` 告诉你过程中模型、工具、middleware、token、错误分别发生了什么。

职责：

- 捕获 LangChain callback。
- 标准化写入 `RunEventStore`。
- 累加 token。
- 识别调用方：`lead_agent`、`subagent:{name}`、`middleware:{name}`。
- 提供 run completion 数据给 `RunManager`。

方法级事件：

```text
on_chain_start()
  -> event_type="run.start"

on_chat_model_start()
  -> event_type="llm_request"
  -> extract first human message

on_llm_end()
  -> event_type="llm_response"
  -> token accumulators
  -> ai_message event

on_tool_start()
  -> tool event

on_tool_end()
  -> tool event

flush()
  -> event_store writes

get_completion_data()
  -> dict for RunManager.update_run_completion()
```

## 用户上下文

文件：`backend/packages/harness/deerflow/runtime/user_context.py`

本质解释：用户隔离不是一个 if 判断，而是一条贯穿链路的约束。HTTP 层确认“你是谁”，runtime 层把“你是谁”带进后台 task，repository/tool/upload/memory/sandbox 再用这个身份隔离数据。

有两条通道：

### 1. `ContextVar`

```text
AuthMiddleware
  -> set_current_user(user)
  -> request handling
  -> reset_current_user(token)
```

用于 repository 默认 `user_id=AUTO` 时解析当前用户。

### 2. `runtime.context["user_id"]`

```text
services.inject_authenticated_user_context()
  -> config["context"]["user_id"] = str(user.id)
  -> run_agent()
  -> Runtime(context=runtime_ctx)
  -> tools/middlewares read runtime.context
```

用于工具、沙箱、上传、custom agent、memory 等可能脱离 HTTP 请求任务的路径。

### `resolve_runtime_user_id()`

解析优先级：

```text
runtime.context["user_id"]
  -> ContextVar current user
  -> "default"
```

这比直接 `get_effective_user_id()` 更适合工具和中间件。

## Repository 的 user_id 三态

`resolve_user_id(value)` 支持：

| 值 | 含义 |
| --- | --- |
| `AUTO` | 从 ContextVar 读取，缺失时报错 |
| `str` | 使用显式用户 id |
| `None` | 不加用户过滤，仅迁移/管理路径使用 |

这个设计让正常请求默认隔离，同时允许迁移脚本有意识地绕过隔离。

## 重启恢复

启动时：

```text
langgraph_runtime()
  -> app.state.run_manager = RunManager(store=run_store)
  -> if database.backend == "sqlite":
       reconcile_orphaned_inflight_runs(...)
       _mark_latest_recovered_threads_error(...)
```

目的：

- Gateway 的 `asyncio.Task` 是进程内对象，重启后不可恢复。
- SQL 中旧的 `pending/running` run 已经没有 worker 接管。
- 启动时将它们标记为 `error`，避免 UI 永远显示运行中。

## 状态系统的阅读顺序

状态相关代码容易混在一起。建议先区分四类状态：

| 类型 | 代表对象 | 作用 |
| --- | --- | --- |
| 图状态 | `ThreadState` | LangGraph 执行时的 channel values |
| 运行状态 | `RunRecord` / run store | pending、running、success、error 等 run 生命周期 |
| 线程元数据 | thread store | 标题、状态、展示名等 UI/列表信息 |
| 事件日志 | `RunJournal` / event store | token、工具、模型、chunk、completion data |

按这个顺序读源码：

```text
1. ThreadState schema
2. reducers：状态如何合并
3. checkpointer：图状态如何保存
4. RunManager：run 状态如何保存
5. RunJournal：运行事件如何保存
6. auth middleware：用户身份如何进入 request.state
7. services.inject_authenticated_user_context()
8. runtime user resolver / repository user_id 三态
```

## `user_id` 追踪图

```text
HTTP request
  -> auth middleware
  -> request.state.user
  -> start_run()
  -> inject_authenticated_user_context(config, request)
  -> config["context"]["user_id"]
  -> run_agent()
  -> _build_runtime_context(...)
  -> Runtime(context=runtime_ctx, store=store)
  -> tools / middlewares / repositories
```

关键原则：

- 客户端可以传 `body.context`，但不能决定最终 `user_id`。
- HTTP 请求结束后，后台 task 仍然要知道用户是谁，所以必须把 `user_id` 放进 runtime context。
- repository 使用 `AUTO` 时依赖 ContextVar；工具和中间件更适合用 runtime context。

## Checkpoint、Store、Journal 的区别

| 名称 | 保存什么 | 读源码时看哪里 |
| --- | --- | --- |
| checkpointer | LangGraph 线程检查点、channel values | `run_agent()` 挂载 `agent.checkpointer` |
| store | LangGraph store，供 runtime/tool 使用 | `Runtime(context=..., store=store)` |
| run store | run 记录、状态、开始结束时间 | `RunManager` |
| thread store | thread metadata、标题、运行状态 | `services.start_run()` 和 `run_agent()` |
| event store | run 过程事件 | `RunJournal.flush()` |

## 自测题

1. `ThreadState` 和 `RunRecord` 分别回答什么问题？
2. 为什么 `RunManager` 的内存状态和持久化状态都要维护？
3. 后台 task 中为什么不能只依赖 `request.state.user`？
4. 重启后为什么不能恢复原来的 `asyncio.Task`？
5. 如果 UI 一直显示 running，你会检查 run store 还是 checkpointer？为什么？
