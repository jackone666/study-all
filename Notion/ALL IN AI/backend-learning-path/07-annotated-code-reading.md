# 关键源码注释式阅读

本文件不替代源码，而是把最关键的函数按“逐段注释”的方式展开。阅读源码时可以把这里当旁注。

## 1. `services.start_run()`

文件：`backend/app/gateway/services.py`

```python
async def start_run(body, thread_id, request) -> RunRecord:
    # 从 FastAPI app.state 取出本次运行要用的长期对象。
    # bridge 负责 SSE 事件发布/订阅。
    # run_mgr 负责 run 状态机。
    # run_ctx 汇总 checkpointer/store/event_store/thread_store/app_config。
    bridge = get_stream_bridge(request)
    run_mgr = get_run_manager(request)
    run_ctx = get_run_context(request)

    # 将 API 字符串转换成内部枚举。
    # cancel 表示 SSE 断开时取消后台任务；continue_ 表示继续跑但没人订阅。
    disconnect = DisconnectMode.cancel if body.on_disconnect == "cancel" else DisconnectMode.continue_

    # model_name 从 body.context 来，而不是 body.config。
    # 它是 DeerFlow 扩展上下文，不是纯 LangGraph RunnableConfig。
    body_context = getattr(body, "context", None) or {}
    model_name = body_context.get("model_name")

    # 请求传来的模型必须在 config.yaml allowlist 中。
    # 这里提前 400，比进入 agent 工厂后回退默认模型更符合 API 语义。
    if model_name:
        app_config = get_app_config()
        resolved = app_config.get_model_config(model_name)
        if resolved is None:
            raise HTTPException(...)

    # 原子创建 run。
    # create_or_reject 会处理同线程并发策略：reject / interrupt / rollback。
    record = await run_mgr.create_or_reject(...)

    # 即使线程不是显式 POST /threads 创建的，也要 upsert thread metadata。
    # 否则侧边栏或 /threads/search 看不到这个线程。
    existing = await run_ctx.thread_store.get(thread_id)
    if existing is None:
        await run_ctx.thread_store.create(...)
    else:
        await run_ctx.thread_store.update_status(thread_id, "running")

    # 当前所有 assistant_id 最终都映射到 make_lead_agent。
    # 自定义 agent 名称通过 config/context 中的 agent_name 注入。
    agent_factory = resolve_agent_factory(body.assistant_id)

    # 把前端消息 dict 转为 LangChain BaseMessage。
    # 这里保留 additional_kwargs，上传文件等信息不会丢。
    graph_input = normalize_input(body.input)

    # 创建 RunnableConfig，再合并 DeerFlow 扩展上下文和认证用户。
    config = build_run_config(...)
    merge_run_context_overrides(config, getattr(body, "context", None))
    inject_authenticated_user_context(config, request)

    # 后台启动真正的 LangGraph 执行。
    # HTTP handler 不 await 这个 task，因此可以马上返回 SSE。
    task = asyncio.create_task(run_agent(...))
    record.task = task

    return record
```

阅读提示：

- `start_run()` 是 Gateway service 层的核心，不是 router。
- 它创建 run，但不消费 run 事件。
- 它把“请求数据”转换成“LangGraph 可运行配置”。

## 2. `RunManager.create_or_reject()`

文件：`backend/packages/harness/deerflow/runtime/runs/manager.py`

```python
async def create_or_reject(...):
    # 预先生成 run_id 和时间戳，避免锁内做不必要的复杂逻辑。
    run_id = str(uuid.uuid4())
    now = _now_iso()

    async with self._lock:
        # 只支持三种策略；enqueue 在 API 模型中存在，但当前 manager 不实现。
        if multitask_strategy not in ("reject", "interrupt", "rollback"):
            raise UnsupportedStrategyError(...)

        # 只检查内存中的 pending/running。
        # 已持久化但不在本 worker 的 run 无法被当前 worker 取消。
        inflight = [
            r for r in self._runs.values()
            if r.thread_id == thread_id and r.status in (RunStatus.pending, RunStatus.running)
        ]

        # 默认策略：同线程已有运行时直接拒绝。
        if multitask_strategy == "reject" and inflight:
            raise ConflictError(...)

        # 新 run 先写入内存，再同步持久化。
        # 如果持久化失败，finally 回滚内存，避免出现 store 不可见的 ghost run。
        record = RunRecord(...)
        self._runs[run_id] = record
        try:
            await self._persist_new_run_to_store(record)
            persisted = True
        finally:
            if not persisted:
                self._runs.pop(run_id, None)

        # interrupt/rollback 会设置旧 run 的 abort_event 并 cancel asyncio.Task。
        # 真正终态由 worker 捕获 CancelledError 后写入。
        if multitask_strategy in ("interrupt", "rollback") and inflight:
            for r in inflight:
                r.abort_action = multitask_strategy
                r.abort_event.set()
                if r.task is not None and not r.task.done():
                    r.task.cancel()
                r.status = RunStatus.interrupted
                interrupted_records.append(r)

    # 状态持久化放锁外，缩短临界区。
    for interrupted_record in interrupted_records:
        await self._persist_status(interrupted_record, RunStatus.interrupted)

    return record
```

阅读提示：

- 锁保护的是内存状态一致性。
- store 写入失败时必须回滚内存。
- `rollback` 的 checkpoint 恢复不在这里做，而在 `run_agent()` 的取消处理里做。

## 3. `run_agent()`

文件：`backend/packages/harness/deerflow/runtime/runs/worker.py`

```python
async def run_agent(...):
    # 基础设施来自 Gateway lifespan 初始化的 app.state。
    checkpointer = ctx.checkpointer
    store = ctx.store
    event_store = ctx.event_store
    thread_store = ctx.thread_store

    # 有 event_store 时创建 RunJournal。
    # RunJournal 同时作为事件写入器和 LangChain callback。
    if event_store is not None:
        journal = RunJournal(...)

    # 状态从 pending -> running。
    await run_manager.set_status(run_id, RunStatus.running)

    # rollback 需要本轮前的 checkpoint 快照。
    # 若本来没有 checkpoint，rollback 会 delete_thread，恢复为空状态。
    ckpt_tuple = await checkpointer.aget_tuple(...)
    pre_run_snapshot = copy.deepcopy(...)

    # 先发布 metadata，前端立刻知道 run_id/thread_id。
    await bridge.publish(run_id, "metadata", {"run_id": run_id, "thread_id": thread_id})

    # 构造 runtime context。
    # 工具、中间件、用户隔离、沙箱路径都依赖这里的 thread_id/run_id/app_config。
    runtime_ctx = _build_runtime_context(...)
    if journal is not None:
        runtime_ctx["__run_journal"] = journal
    _install_runtime_context(config, runtime_ctx)

    # 手动塞入 LangGraph Runtime。
    # Gateway 不是 langgraph-cli，需要自己安装 __pregel_runtime。
    runtime = Runtime(context=runtime_ctx, store=store)
    config.setdefault("configurable", {})["__pregel_runtime"] = runtime

    # 把 journal 作为 callback 注入，捕获 LLM/tool/chain 事件。
    if journal is not None:
        config.setdefault("callbacks", []).append(journal)

    # 构造 agent。agent_factory 通常是 make_lead_agent。
    runnable_config = RunnableConfig(**config)
    agent = agent_factory(config=runnable_config, app_config=ctx.app_config)

    # 挂载 checkpointer/store 后，LangGraph 才能读写线程状态和 store。
    agent.checkpointer = checkpointer
    agent.store = store

    # 将 DeerFlow stream_mode 转为 LangGraph astream 支持的模式。
    # messages-tuple 是 API 兼容名，内部实际用 messages。
    lg_modes = ...

    # 核心执行循环：每个 chunk 序列化后发布到 StreamBridge。
    async for chunk in agent.astream(graph_input, config=runnable_config, stream_mode=single_mode):
        if record.abort_event.is_set():
            break
        await bridge.publish(run_id, sse_event, serialize(chunk, mode=single_mode))

    # 根据执行结果落最终状态。
    if record.abort_event.is_set():
        ...
    else:
        await run_manager.set_status(run_id, RunStatus.success)

    # finally 总是发布 end，避免 SSE 悬挂。
    await bridge.publish_end(run_id)
```

阅读提示：

- `run_agent()` 是后端最重要函数之一。
- 它不是 agent 逻辑本身，而是 agent 的运行壳：上下文、回调、流、状态、清理都在这里。
- 大部分“为什么工具拿不到 thread_id/run_id”的问题，都要回到 runtime context 安装过程排查。

## 4. `_make_lead_agent()`

文件：`backend/packages/harness/deerflow/agents/lead_agent/agent.py`

```python
def _make_lead_agent(config, *, app_config):
    # 1. 扁平化运行时配置。
    cfg = _get_runtime_config(config)

    # 2. 读取模型、模式、agent 名称等运行参数。
    thinking_enabled = cfg.get("thinking_enabled", True)
    requested_model_name = cfg.get("model_name") or cfg.get("model")
    is_plan_mode = cfg.get("is_plan_mode", False)
    subagent_enabled = cfg.get("subagent_enabled", False)
    agent_name = validate_agent_name(cfg.get("agent_name"))

    # 3. 自定义 agent 配置。
    # bootstrap 模式跳过，因为 bootstrap 是用来创建 agent 的。
    agent_config = load_agent_config(agent_name) if not is_bootstrap else None

    # 4. 模型解析。
    # 请求指定 > agent 配置 > 全局默认。
    model_name = _resolve_model_name(requested_model_name or agent_model_name, app_config=resolved_app_config)

    # 5. metadata + tracing callback 注入。
    config["metadata"].update(...)
    tracing_callbacks = build_tracing_callbacks()
    config["callbacks"] = [*existing, *tracing_callbacks]

    # 6. 技能策略。
    # 技能可限制 allowed-tools，所以工具加载后还要过滤。
    skills_for_tool_policy = _load_enabled_skills_for_tool_policy(...)

    # 7. 工具加载和延迟工具拆分。
    raw_tools = get_available_tools(...)
    filtered = filter_tools_by_skill_allowed_tools(raw_tools + extra_tools, skills_for_tool_policy)
    final_tools, setup = _assemble_deferred(filtered, enabled=resolved_app_config.tool_search.enabled)

    # 8. 中间件链和系统提示。
    middleware = _build_middlewares(...)
    system_prompt = apply_prompt_template(...)

    # 9. 创建 LangChain/LangGraph agent。
    return create_agent(
        model=create_chat_model(..., attach_tracing=False),
        tools=final_tools,
        middleware=middleware,
        system_prompt=system_prompt,
        state_schema=ThreadState,
    )
```

阅读提示：

- 这里是“模型、工具、prompt、中间件、状态 schema”的汇合点。
- 默认 agent、自定义 agent、bootstrap agent 的差异都在这里。
- 如果一个工具没有出现在模型可调用列表，要看 `get_available_tools()`、技能策略过滤和 `_assemble_deferred()`。

## 5. `get_available_tools()`

文件：`backend/packages/harness/deerflow/tools/tools.py`

```python
def get_available_tools(...):
    # 读取 config.tools，并按 group 过滤。
    tool_configs = [tool for tool in config.tools if groups is None or tool.group in groups]

    # local sandbox 模式下默认不暴露 host bash。
    if not is_host_bash_allowed(config):
        tool_configs = [tool for tool in tool_configs if not _is_host_bash_tool(tool)]

    # resolve_variable 把 "module.path:var" 字符串解析为 BaseTool 对象。
    loaded_tools_raw = [(cfg, resolve_variable(cfg.use, BaseTool)) for cfg in tool_configs]

    # 仅异步工具补同步 wrapper，兼容同步 agent 路径。
    loaded_tools = [_ensure_sync_invocable_tool(t) for _, t in loaded_tools_raw]

    # 内置工具、技能管理、子代理、视觉工具按配置追加。
    builtin_tools = BUILTIN_TOOLS.copy()
    if skill_evolution.enabled:
        builtin_tools.append(skill_manage_tool)
    if subagent_enabled:
        builtin_tools.extend(SUBAGENT_TOOLS)
    if model_config.supports_vision:
        builtin_tools.append(view_image_tool)

    # MCP 工具来自启动时缓存，加载后打 tag，供延迟工具拆分识别。
    mcp_tools = get_cached_mcp_tools()
    for t in mcp_tools:
        tag_mcp_tool(t)

    # 最后按工具名去重。
    all_tools = loaded_tools + builtin_tools + mcp_tools + acp_tools
    unique_tools = ...
    return unique_tools
```

阅读提示：

- 工具最终是否绑定模型，不只取决于这里，还取决于技能过滤和 deferred 逻辑。
- `cfg.name` 和 `tool.name` 不一致会告警，但绑定时使用 `tool.name`。

## 6. `ensure_sandbox_initialized_async()`

文件：`backend/packages/harness/deerflow/sandbox/tools.py`

```python
async def ensure_sandbox_initialized_async(runtime):
    # runtime 必须存在，且必须有 state。
    # 工具调用没有 runtime 通常意味着 LangGraph context 安装失败。
    if runtime is None:
        raise SandboxRuntimeError(...)
    if runtime.state is None:
        raise SandboxRuntimeError(...)

    # 已有 sandbox_id 时复用。
    sandbox_state = runtime.state.get("sandbox")
    if sandbox_state is not None:
        sandbox_id = sandbox_state.get("sandbox_id")
        sandbox = get_sandbox_provider().get(sandbox_id)
        if sandbox is not None:
            runtime.context["sandbox_id"] = sandbox_id
            return sandbox

    # 没有 sandbox 时从 runtime.context 或 configurable 解析 thread_id。
    thread_id = runtime.context.get("thread_id") if runtime.context else None
    if thread_id is None:
        thread_id = runtime.config.get("configurable", {}).get("thread_id")
    if thread_id is None:
        raise SandboxRuntimeError("Thread ID not available in runtime context")

    # 异步获取 sandbox，避免阻塞事件循环。
    provider = get_sandbox_provider()
    sandbox_id = await provider.acquire_async(thread_id)

    # 同时写 state 和 context。
    runtime.state["sandbox"] = {"sandbox_id": sandbox_id}
    runtime.context["sandbox_id"] = sandbox_id

    return provider.get(sandbox_id)
```

阅读提示：

- 这个函数是所有沙箱工具的前置门。
- 如果工具报 “Thread ID not available”，优先看 `run_agent()` 是否正确安装 runtime context。

