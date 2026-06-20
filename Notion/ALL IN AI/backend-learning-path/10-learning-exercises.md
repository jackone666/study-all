# 10. 学习练习和调试任务

这个文件把阅读变成实战。每个练习都应该打开源码完成，必要时配合测试、断点或日志。

## 练习 1：手写一次 Run 调用链

目标：不看笔记，从 HTTP 入口写到 `agent.astream()`。

步骤：

1. 打开 `backend/app/gateway/routers/thread_runs.py`。
2. 找到 `stream_run()`。
3. 顺着函数调用进入 `services.start_run()`。
4. 找到 `asyncio.create_task(run_agent(...))`。
5. 进入 `worker.run_agent()`。
6. 找到 `agent.astream(...)`。

交付：

```text
stream_run()
  -> 写出你在源码中找到的中间函数
  -> agent.astream(...)
```

检查问题：

- 哪个函数创建 `RunRecord`？
- 哪个函数把 run 状态改为 running？
- 哪个函数把 chunk 发布给 SSE？

## 练习 2：追踪 `user_id`

目标：理解用户隔离不是只发生在 HTTP 层。

步骤：

1. 找到认证中间件设置 `request.state.user` 的位置。
2. 打开 `services.inject_authenticated_user_context()`。
3. 确认 `config["context"]["user_id"]` 如何写入。
4. 打开 `worker.run_agent()`。
5. 找到 `_build_runtime_context()` 和 `Runtime(context=...)`。
6. 找一个工具或 repository，看它如何解析当前用户。

交付：

```text
request.state.user
  -> config["context"]["user_id"]
  -> runtime.context["user_id"]
  -> tool/repository
```

检查问题：

- 为什么不能信任客户端传来的 `user_id`？
- 后台 task 中为什么不能只依赖 request？

## 练习 3：解释 `RunnableConfig.context` 和 `configurable`

目标：分清 DeerFlow 扩展上下文和 LangGraph 配置。

步骤：

1. 读 `build_run_config()`。
2. 读 `merge_run_context_overrides()`。
3. 记录哪些字段同时写入 `context` 和 `configurable`。
4. 找到 `_get_runtime_config()` 如何读取这些字段。

交付：

| 字段 | 写入位置 | 读取位置 | 作用 |
| --- | --- | --- | --- |
| `model_name` |  |  |  |
| `agent_name` |  |  |  |
| `is_plan_mode` |  |  |  |
| `subagent_enabled` |  |  |  |

检查问题：

- 为什么要同时兼容 `context` 和 `configurable`？

## 练习 4：追踪模型选择

目标：知道一次请求最终使用哪个模型。

步骤：

1. 在 `services.start_run()` 找到 `model_name` 校验。
2. 在 `agent.py` 找到 `_get_runtime_config()`。
3. 找到 `_resolve_model_name()`。
4. 找到 `create_chat_model(...)`。
5. 找到对应测试：`test_lead_agent_model_resolution.py`。

交付：

```text
request context model_name
  -> start_run validation
  -> RunnableConfig
  -> _get_runtime_config()
  -> _resolve_model_name()
  -> create_chat_model()
```

检查问题：

- 请求模型、自定义 agent 模型、默认模型的优先级是什么？

## 练习 5：追踪一个工具为什么没有出现

目标：掌握工具排查路线。

步骤：

1. 找到 `get_available_tools()`。
2. 选择一个工具名，确认它是否在候选工具里。
3. 检查 skill allowed-tools 过滤。
4. 检查 `_assemble_deferred()` 是否把它移入 deferred catalog。
5. 如果是 MCP 工具，检查 MCP cache。
6. 如果是 sandbox 工具，检查 runtime context。

交付：

```text
tool candidate
  -> skill filter
  -> deferred decision
  -> final_tools or tool_search catalog
```

检查问题：

- “没有直接暴露给模型”和“不可用”是不是一回事？

## 练习 6：追踪 SSE 事件

目标：理解 worker 和 HTTP response 如何通过 `StreamBridge` 解耦。

步骤：

1. 找到 `worker.run_agent()` 中的 `bridge.publish(...)`。
2. 打开 `MemoryStreamBridge.publish()`。
3. 打开 `MemoryStreamBridge.subscribe()`。
4. 找到 router 中的 `sse_consumer()`。
5. 找到 `publish_end()` 和 cleanup。

交付：

```text
agent chunk
  -> serialize
  -> bridge.publish
  -> StreamEvent
  -> bridge.subscribe
  -> SSE frame
```

检查问题：

- heartbeat 有什么用？
- `Last-Event-ID` 什么时候生效？

## 练习 7：理解 rollback

目标：知道 rollback 不是简单取消 task。

步骤：

1. 读 `RunManager.create_or_reject()` 中 rollback 分支。
2. 找到旧 run 如何设置 `abort_action`。
3. 打开 `worker.run_agent()` 的取消/异常处理。
4. 找到 `_rollback_to_pre_run_checkpoint()`。
5. 阅读 `test_run_worker_rollback.py`。

交付：

```text
new run with rollback
  -> old record abort_action=rollback
  -> old task cancel
  -> worker catches cancellation
  -> restore pre-run checkpoint
```

检查问题：

- 为什么 checkpoint 快照必须在 worker 开始时捕获？

## 练习 8：区分四类状态

目标：把 `ThreadState`、run store、thread store、journal 分清楚。

步骤：

1. 打开 `ThreadState`。
2. 找到 `RunRecord`。
3. 找到 run repository。
4. 找到 thread metadata repository。
5. 找到 `RunJournal`。
6. 分别写出它们保存什么。

交付：

| 状态 | 保存什么 | 什么时候写 | 谁读取 |
| --- | --- | --- | --- |
| `ThreadState` |  |  |  |
| `RunRecord` |  |  |  |
| thread metadata |  |  |  |
| `RunJournal` |  |  |  |

检查问题：

- UI 线程列表需要的数据主要来自哪里？
- LangGraph 恢复执行需要的数据主要来自哪里？

## 练习 9：用测试验证理解

目标：用已有测试做阅读入口。

建议测试：

```bash
cd /Users/zing/Desktop/核心/核心开源学习/deer-flow/backend
uv run pytest tests/test_gateway_services.py -q
uv run pytest tests/test_run_worker_rollback.py -q
uv run pytest tests/test_stream_bridge.py -q
uv run pytest tests/test_tool_search.py -q
```

检查问题：

- 哪个测试最接近 `start_run()` 的行为？
- 哪个测试最接近 worker 的终态处理？
- 哪个测试最接近 deferred tool 行为？

## 练习 10：讲给别人听

目标：检验你是否真的理解。

用 5 分钟讲清楚：

```text
用户发送一条消息后，DeerFlow 后端如何：
1. 创建 run
2. 启动后台 agent
3. 构造模型和工具
4. 流式返回事件
5. 保存状态
6. 隔离用户数据
```

如果讲到某一步只能说“然后它就处理了”，说明那里还没有读透。回到对应章节补源码。
