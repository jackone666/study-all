# 00. 后端学习计划

目标：用课程式路径读完整个 DeerFlow 后端，并在关键节点做方法级源码精读。读完后，你应该能独立追踪一次 run，解释 agent 构造过程，定位工具、状态、持久化和用户隔离相关问题。

## 读源码的方法

每个核心函数都按同一个模板读：

```text
函数位置：
谁调用它：
它调用谁：
输入对象：
输出对象：
主要副作用：
失败路径：
对应测试：
```

不要一上来逐行读。先建立调用链，再回头读实现细节。尤其是异步代码，要先标出边界：

- `asyncio.create_task()`
- `async for chunk in agent.astream(...)`
- `StreamingResponse(...)`
- `StreamBridge.subscribe(...)`
- `asyncio.to_thread(...)`

## 阶段 1：建立后端地图

阅读文件：

- `backend/app/gateway/app.py`
- `backend/app/gateway/deps.py`
- `backend/app/gateway/services.py`
- `backend/packages/harness/deerflow/runtime/`
- `backend/packages/harness/deerflow/agents/`

要回答的问题：

- FastAPI app 在哪里创建？
- `app.state` 中放了哪些运行时对象？
- Gateway 层和 harness/deerflow 层的边界是什么？
- 哪些代码属于 API 适配，哪些代码属于核心运行时？

精读入口：

```text
app.py::lifespan()
deps.py::langgraph_runtime()
deps.py::get_run_context()
services.py::start_run()
```

阶段产出：

- 画出 Gateway、RunManager、StreamBridge、checkpointer、store、agent factory 的关系。
- 能解释为什么 router 不直接创建 agent。

## 阶段 2：追踪一次 Run

阅读文件：

- `backend/app/gateway/routers/thread_runs.py`
- `backend/app/gateway/services.py`
- `backend/packages/harness/deerflow/runtime/runs/manager.py`
- `backend/packages/harness/deerflow/runtime/runs/worker.py`
- `backend/packages/harness/deerflow/runtime/stream_bridge/memory.py`

主调用链：

```text
stream_run()
  -> start_run()
  -> RunManager.create_or_reject()
  -> asyncio.create_task(run_agent(...))
  -> run_agent()
  -> agent.astream(...)
  -> bridge.publish(...)
  -> sse_consumer()
```

要回答的问题：

- `RunRecord` 是什么时候创建的？
- HTTP handler 为什么不等待 agent 完成？
- SSE 消费者和后台 worker 如何通过 `run_id` 连接？
- `on_disconnect=cancel` 时取消的是谁？
- `rollback` 的 checkpoint 恢复在哪里发生？

阶段产出：

- 能手写 `stream_run()` 到 `run_agent()` 的方法级调用链。
- 能解释 pending、running、success、interrupted、error 的转换。

## 阶段 3：理解 Lead Agent 构造

阅读文件：

- `backend/packages/harness/deerflow/agents/lead_agent/agent.py`
- `backend/packages/harness/deerflow/agents/middlewares/`
- `backend/packages/harness/deerflow/tools/tools.py`
- `backend/packages/harness/deerflow/tools/builtins/tool_search.py`
- `backend/packages/harness/deerflow/config/`

主调用链：

```text
make_lead_agent()
  -> _make_lead_agent()
  -> _get_runtime_config()
  -> _resolve_model_name()
  -> get_available_tools()
  -> _assemble_deferred()
  -> _build_middlewares()
  -> create_agent()
```

要回答的问题：

- 请求里的 `model_name` 如何覆盖默认模型？
- `agent_name` 如何影响自定义 agent 配置？
- skill policy 如何过滤工具？
- deferred tool search 为什么要把一部分工具隐藏到搜索工具后面？
- middleware 的顺序为什么重要？

阶段产出：

- 能解释一次 agent 创建过程中模型、工具、middleware、prompt 的装配顺序。
- 能指出新增一个工具或 middleware 应该看哪些文件。

## 阶段 4：工具、沙箱、MCP

阅读文件：

- `backend/packages/harness/deerflow/tools/`
- `backend/packages/harness/deerflow/mcp/`
- `backend/packages/harness/deerflow/sandbox/`
- `backend/packages/harness/deerflow/community/aio_sandbox/`

要回答的问题：

- 内置工具和 MCP 工具在哪里汇合？
- 哪些工具需要 sandbox？
- sandbox 生命周期是谁管理的？
- 工具执行时如何拿到 `thread_id/run_id/user_id`？
- MCP 工具为什么需要缓存？

阶段产出：

- 跟踪一个工具从加载到被 agent 调用的路径。
- 能解释 `Runtime(context=...)` 对工具系统的意义。

## 阶段 5：状态、持久化、认证

阅读文件：

- `backend/packages/harness/deerflow/state.py`
- `backend/packages/harness/deerflow/persistence/`
- `backend/packages/harness/deerflow/runtime/journal.py`
- `backend/app/gateway/auth_middleware.py`
- `backend/app/gateway/authz.py`
- `backend/app/gateway/services.py`

要回答的问题：

- `ThreadState` 保存的是 agent 状态，还是 run 元数据？
- checkpointer 和 store 的职责有什么区别？
- `RunJournal` 记录了哪些事件？
- `request.state.user` 什么时候进入 `RunnableConfig.context`？
- 为什么不能信任客户端传来的 `user_id`？

阶段产出：

- 能追踪 `user_id` 从认证中间件进入 runtime context 的路径。
- 能解释 thread、run、checkpoint、journal 之间的关系。

## 阶段 6：外围能力接入主链路

阅读文件：

- `backend/app/gateway/routers/uploads.py`
- `backend/packages/harness/deerflow/uploads/`
- `backend/packages/harness/deerflow/agents/memory/`
- `backend/app/channels/`

要回答的问题：

- 上传文件如何变成 agent 可见的上下文？
- 长期记忆更新是同步执行还是异步排队？
- IM channel 是直接调用 agent，还是复用 Gateway/runtime？
- 外围能力为什么不应该绕过 run 生命周期？

阶段产出：

- 能说明上传、记忆、频道分别插入主链路的哪个位置。

## 阶段 7：测试和调试

阅读文件：

- `backend/tests/test_gateway_services.py`
- `backend/tests/test_run_worker_rollback.py`
- `backend/tests/test_stream_bridge.py`
- `backend/tests/test_thread_state_reducers.py`
- `backend/tests/test_tool_search.py`
- `backend/tests/test_uploads_router.py`

要回答的问题：

- 哪些测试覆盖 run 创建？
- 哪些测试覆盖 worker 状态转换？
- 哪些测试覆盖 SSE 桥？
- 想验证工具过滤或 deferred tool，应该从哪个测试入手？

阶段产出：

- 能选一个测试作为调试入口。
- 能给 `start_run()`、`run_agent()`、`_make_lead_agent()` 设置断点并解释调用栈。

## 最终验收

当你能不看笔记完成下面四件事，说明后端主线已经读通：

1. 从 `POST /api/threads/{thread_id}/runs/stream` 追到 `agent.astream()`。
2. 解释 `RunnableConfig.context`、`Runtime.context`、`ThreadState` 的区别。
3. 说明一个工具如何被加载、过滤、执行，并拿到当前 run 上下文。
4. 找到一个 run 出错后状态、SSE、journal、thread metadata 分别在哪里更新。
