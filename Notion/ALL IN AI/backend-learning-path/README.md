# DeerFlow 后端学习路径

这套笔记用于完整阅读 DeerFlow 后端。它不是 API 文档，也不是源码的复述，而是一条可以边读源码边验证理解的学习路线。

推荐使用方式：

1. 先读 `00-learning-plan.md`，确定每一阶段要解决的问题。
2. 每章按“目标 -> 源码入口 -> 方法调用链 -> 关键变量 -> 自测题”的顺序阅读。
3. 打开源码对照阅读，不要只看笔记。每个核心函数都要回答：谁调用它、它调用谁、它改了什么状态。
4. 每读完一章，到 `09-source-reading-checklists.md` 勾掉对应清单。
5. 每读完一个阶段，到 `10-learning-exercises.md` 做一次调试或追踪练习。

## 学习地图

| 阶段 | 文档 | 你要获得的能力 |
| --- | --- | --- |
| 0 | `00-learning-plan.md` | 知道后端学习顺序、每天读什么、读完如何自测 |
| 1 | `01-backend-architecture-map.md` | 看懂 Gateway、runtime、agent、tool、persistence 的分层 |
| 2 | `02-run-call-chain.md` | 能从一次 HTTP/SSE 请求追到 `run_agent()` |
| 3 | `03-lead-agent-call-chain.md` | 能解释 Lead Agent 如何选择模型、工具、middleware、prompt |
| 4 | `04-tools-sandbox-mcp.md` | 能说清工具、沙箱、MCP、deferred tool 的关系 |
| 5 | `05-state-persistence-auth.md` | 能追踪 `ThreadState`、checkpoint、store、RunJournal、用户隔离 |
| 6 | `06-channels-uploads-memory.md` | 能理解上传、长期记忆、IM channel 如何接入主运行时 |
| 7 | `07-annotated-code-reading.md` | 对关键函数做逐段源码精读 |
| 8 | `08-tests-and-debugging.md` | 知道用哪些测试、断点、日志验证自己的理解 |
| 9 | `09-source-reading-checklists.md` | 按模块检查自己是否真的读完源码 |
| 10 | `10-learning-exercises.md` | 用练习把“看懂”变成“能追、能改、能解释” |

## 最短主线

如果你只想先抓住后端主干，按这个顺序读：

```text
backend/app/gateway/app.py::lifespan()
  -> backend/app/gateway/deps.py::langgraph_runtime()
  -> backend/app/gateway/routers/thread_runs.py::stream_run()
  -> backend/app/gateway/services.py::start_run()
  -> backend/packages/harness/deerflow/runtime/runs/manager.py::RunManager.create_or_reject()
  -> backend/packages/harness/deerflow/runtime/runs/worker.py::run_agent()
  -> backend/packages/harness/deerflow/agents/lead_agent/agent.py::make_lead_agent()
  -> backend/packages/harness/deerflow/agents/lead_agent/agent.py::_make_lead_agent()
```

这条链路回答的是：“用户发起一次聊天请求后，后端到底如何创建 run、启动 agent、流式返回事件、保存状态？”

## 四条必须掌握的线

### 1. 请求运行线

```text
HTTP request
  -> router
  -> service
  -> RunManager
  -> background worker
  -> LangGraph agent
  -> StreamBridge
  -> SSE response
```

重点看 `thread_id`、`run_id`、`assistant_id`、`stream_mode` 如何传递。

### 2. Agent 构造线

```text
RunnableConfig
  -> runtime config
  -> model resolution
  -> skill policy
  -> tool loading
  -> middleware
  -> system prompt
  -> create_agent()
```

重点看 `model_name`、`agent_name`、`is_plan_mode`、`subagent_enabled` 如何影响 agent。

### 3. 状态持久化线

```text
ThreadState
  -> checkpointer
  -> store
  -> RunJournal
  -> run repository
  -> thread metadata
```

重点看哪些状态属于 LangGraph 线程状态，哪些属于 DeerFlow 自己的 run/thread 元数据。

### 4. 工具执行线

```text
tool registry
  -> built-in tools
  -> MCP tools
  -> sandbox-backed tools
  -> deferred tool search
  -> middleware filtering
  -> tool runtime context
```

重点看工具如何拿到 `runtime.context`，以及为什么 `thread_id/run_id/user_id` 必须在 worker 中安装。

## 推荐节奏

| 天数 | 内容 | 产出 |
| --- | --- | --- |
| Day 1 | 总览、目录、启动、依赖注入 | 画出 Gateway 到 runtime 的结构图 |
| Day 2 | Run 主链路 | 写出 `stream_run()` 到 `run_agent()` 的调用链 |
| Day 3 | Lead Agent 构造 | 解释模型、工具、middleware 的装配顺序 |
| Day 4 | 工具、沙箱、MCP | 跟踪一个工具从注册到执行的路径 |
| Day 5 | 状态、持久化、认证 | 解释 `user_id` 和 `thread_id` 如何隔离数据 |
| Day 6 | 上传、记忆、频道 | 找到这些能力插入主链路的位置 |
| Day 7 | 测试与调试 | 用断点或测试复现一次完整 run |

## 学习时的判断标准

读完一章后，不要用“我看过了”判断，而用下面的问题判断：

- 我能不能从入口函数不看笔记说出下一跳？
- 我能不能指出这个函数最重要的输入、输出、副作用？
- 我能不能说明它为什么放在这一层，而不是 router、agent 或 tool 里？
- 我能不能找到对应测试？
- 我能不能设计一个最小请求或断点验证它？

如果回答不上来，回到对应章节的“源码精读顺序”和 `09-source-reading-checklists.md`。
