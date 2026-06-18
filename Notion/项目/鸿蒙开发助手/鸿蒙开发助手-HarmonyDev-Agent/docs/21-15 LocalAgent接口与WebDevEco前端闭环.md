# 15 LocalAgent接口与Web/DevEco前端闭环

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 把第 14 章组装好的主 AgentLoop 接到 FastAPI，落地"启动任务 / WebSocket 推进度 / 取消任务 / 文件下载"四类接口。

- 跑通"用户在浏览器输入 → AGUI 事件流刷屏 → API/代码片段精选建议列表展示"的完整闭环。

- 落地一份够用的 Web/DevEco 面板集成代码——重点不是 UI 细节，而是怎么消费 AGUI 事件流。

- 跑通整套系统的端到端链路：多源鸿蒙开发 query 从启动、检索、合流到最终建议完整闭环。

**阅读重点：** 这是 HarmonyDev 项目的最后一章。建议重点核对端到端链路：启动后端、连接 WebSocket、发起任务、接收 fork 事件、展示最终修复建议。这条事件流把前 14 章的工程能力收束到可观察的闭环里。

---

## 1、本章导读

### 1.1 站在第 14 章的肩膀上

第 14 章已经把 `run_agent(query, thread_id, user_id)` 跑通了——只差一层"对外接口"把它暴露给浏览器。

需要补的是：

| 接口 | 解决什么 |
| --- | --- |
| `POST /api/task` | 启动一次主 AgentLoop，立即返回 thread_id |
| `WS /ws/{tid}` | 长连接，监听 AGUI 事件 |
| `POST /api/task/{tid}/cancel` | 用户主动取消长任务 |
| `GET /api/files/{tid}/{name}` | 下载本次会话生成的补丁 / 报告 |
| `POST /api/upload` | 上传参考文件（如报错日志 / 关键源码片段） |

### 1.2 本章先做什么，不做什么

要做的：

1. 用 FastAPI 落地上述五类接口。

1. 处理 `active_tasks` 任务表 + 取消语义 + WebSocket 重连。

1. 给一份 Web/DevEco 面板的 AGUI 消费骨架（不堆 UI，重点是事件流）。

1. 跑一次端到端 demo，把"多源搜ArkUI 状态保存"的链路跑完。

不做的：

- 完整的 UI / 主题 / 动效——前端实现可以替换，本章只锁住"前后端协议"。

- 鉴权 / 限流 / 多租户隔离——生产化能力，不是入门主线。

---

## 2、FastAPI 服务骨架

### 2.1 应用入口

```python
# app/api/server.py
import asyncio
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.agent.main_agent import run_agent
from app.api.connection import manager
from app.api.context import set_thread_context
from app.api.monitor import monitor
from app.utils.path_utils import (
    ensure_session_dir, ensure_upload_dir, safe_join, OUTPUT_ROOT,
)

app = FastAPI(title="HarmonyDev Agent API")
active_tasks: dict[str, asyncio.Task] = {}

class TaskRequest(BaseModel):
    query: str
    thread_id: str | None = None
    user_id: str | None = None
```

### 2.2 启动任务

```python
@app.post("/api/task")
async def create_task(req: TaskRequest):
    """启动一次主 AgentLoop 后台任务，立即返回不等结果。"""
    thread_id = req.thread_id or uuid.uuid4().hex

    # 同 thread_id 只保留一个活跃任务
    old = active_tasks.get(thread_id)
    if old and not old.done():
        old.cancel()

    async def _runner():
        try:
            await run_agent(req.query, thread_id, user_id=req.user_id)
        except asyncio.CancelledError:
            await monitor.report_error("cancelled", "任务被取消")
            raise
        except Exception as exc:
            await monitor.report_error("internal_error", str(exc))
        finally:
            active_tasks.pop(thread_id, None)

    task = asyncio.create_task(_runner())
    active_tasks[thread_id] = task

    return {"status": "started", "thread_id": thread_id}
```

关键点：

- **HTTP 立刻返回 thread_id**，不等任务结果——避免前端长时间无反馈。

- **同 thread_id 旧任务先 cancel**：用户在前端连发两次相同 thread_id，自动覆盖旧的。

- `asyncio.create_task`** 自动复制 ContextVar 快照**：所以 `_runner` 内部不需要再做 set_thread_context，`run_agent` 会自己处理。

### 2.3 WebSocket 接口

```python
@app.websocket("/ws/{thread_id}")
async def ws_endpoint(websocket: WebSocket, thread_id: str):
    """前端订阅 thread_id 对应的 AGUI 事件流。"""
    await manager.connect(websocket, thread_id)
    try:
        # 通知前端订阅成功
        await websocket.send_json({
            "type": "monitor_event",
            "event": "session_created",
            "message": "会话已创建",
            "data": {"thread_id": thread_id},
        })
        while True:
            data = await websocket.receive_text()
            # 简单的心跳协议
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, thread_id)
```

### 2.4 取消任务

```python
@app.post("/api/task/{thread_id}/cancel")
async def cancel_task(thread_id: str):
    task = active_tasks.get(thread_id)
    if not task or task.done():
        raise HTTPException(404, f"任务 {thread_id} 不存在或已结束")
    task.cancel()
    return {"status": "cancelling", "thread_id": thread_id}
```

`task.cancel()` 会向协程注入 `CancelledError`。`run_agent` 内部任何 `await` 点都会被打断，进入 `_runner` 的 `except CancelledError` 分支推送 `error` 事件。

### 2.5 文件接口

```python
@app.get("/api/files/{thread_id}/{filename}")
async def download_file(thread_id: str, filename: str):
    """下载某次会话生成的产物（建议列表 / PDF）。"""
    session_dir = OUTPUT_ROOT / thread_id
    if not session_dir.exists():
        raise HTTPException(404, "会话不存在")
    target = safe_join(session_dir, filename)   # 防 ../ 越权
    if not target.exists():
        raise HTTPException(404, f"文件不存在：{filename}")
    return FileResponse(target, filename=filename)

@app.post("/api/upload")
async def upload_file(thread_id: str, file: UploadFile = File(...)):
    """上传参考文件（如报错日志 / 关键源码片段）到本次会话目录。"""
    upload_dir = ensure_upload_dir(thread_id)
    target = upload_dir / file.filename
    target.write_bytes(await file.read())
    return {"status": "ok", "path": str(target.relative_to(upload_dir.parent.parent))}
```

`safe_join` 已经在第 10 章实现，防止恶意 filename `../../etc/passwd` 越权读取。

---

## 3、AGUI 事件流前端怎么消费

### 3.1 前后端协议（再次明确）

每条事件统一格式：

```json
{
  "type": "monitor_event",
  "event": "tool_start | tool_end | fork | task_result | error | session_created",
  "message": "正在调用 doc_search",
  "data": {"tool_name": "doc_search", "args": {"query": "...", "source": "harmony_docs"}},
  "timestamp": "2026-06-09T14:23:45.123Z"
}
```

前端只需要根据 `event` 字段做不同展示，不关心后端怎么生成。

### 3.2 React Hook 封装

```typescript
// web-console/src/hooks/useHarmonyDevTask.ts
import { useEffect, useRef, useState } from "react";

export type AguiEvent = {
  event: string;
  message: string;
  data: Record<string, unknown>;
  timestamp: string;
};

export function useHarmonyDevTask() {
  const [threadId, setThreadId] = useState<string | null>(null);

  const [events, setEvents] = useState<AguiEvent[ ]>([ ]);

  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  async function startTask(query: string, userId?: string) {

    setEvents([ ]);

    setFinalAnswer(null);
    setRunning(true);
    const resp = await fetch("/api/task", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, user_id: userId }),
    });
    const { thread_id: tid } = await resp.json();
    setThreadId(tid);
    connectWs(tid);
  }

  function connectWs(tid: string) {
    const ws = new WebSocket(`ws://${location.host}/ws/${tid}`);
    wsRef.current = ws;
    ws.onmessage = (msg) => {
      const payload = JSON.parse(msg.data);
      if (payload.type !== "monitor_event") return;
      setEvents((prev) => [...prev, payload as AguiEvent]);
      if (payload.event === "task_result") {
        setFinalAnswer((payload.data as any).final_answer);
        setRunning(false);
      }
      if (payload.event === "error") {
        setRunning(false);
      }
    };
    ws.onclose = () => {
      // 简单重连
      if (running) {
        setTimeout(() => connectWs(tid), 1000);
      }
    };
  }

  async function cancelTask() {
    if (!threadId) return;
    await fetch(`/api/task/${threadId}/cancel`, { method: "POST" });
  }

  useEffect(() => () => wsRef.current?.close(), [ ]);

  return { threadId, events, finalAnswer, running, startTask, cancelTask };
}
```

### 3.3 事件流可视化（最小骨架）

```tsx
// web-console/src/components/EventStream.tsx
import { AguiEvent } from "../hooks/useHarmonyDevTask";

const EVENT_LABEL: Record<string, string> = {
  session_created: "🟢 会话已创建",
  fork: "🌿 派发子 Agent",
  tool_start: "▶️  工具开始",
  tool_end: "✅ 工具完成",
  task_result: "🎉 任务完成",
  error: "❌ 错误",
};

export function EventStream({ events }: { events: AguiEvent[ ] }) {

  return (
    <div className="event-stream">
      {events.map((e, i) => (
        <div key={i} className={`evt evt-${e.event}`}>
          <span className="time">{e.timestamp.slice(11, 19)}</span>
          <span className="label">{EVENT_LABEL[e.event] ?? e.event}</span>
          <span className="msg">{e.message}</span>
          {e.event === "fork" && (
            <code className="demands">{(e.data as any).demands}</code>
          )}
          {e.event === "tool_end" && (
            <span className="ms">{(e.data as any).duration_ms} ms</span>
          )}
        </div>
      ))}
    </div>
  );
}
```

UI 不堆样式——核心是把 `fork`、`tool_start/end`、`task_result` 三类事件**显式可见**。这正是 AGUI 事件流的真正价值：用户能看见"什么时候 HarmonyDev 自己干、什么时候叫了多个子 Agent"。

### 3.4 主页骨架

```tsx
// web-console/src/App.tsx
import { useState } from "react";
import { useHarmonyDevTask } from "./hooks/useHarmonyDevTask";
import { EventStream } from "./components/EventStream";

export default function App() {
  const { events, finalAnswer, running, startTask, cancelTask } = useHarmonyDevTask();
  const [query, setQuery] = useState("");

  return (
    <div className="app">
      <header><h1>HarmonyDev 鸿蒙开发助手</h1></header>

      <div className="input-bar">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="例如：想实现ArkUI 页面状态恢复方案，目标 HarmonyOS 5.0，不要使用废弃 API"
          disabled={running}
        />
        {running ? (
          <button onClick={cancelTask}>取消</button>
        ) : (
          <button onClick={() => startTask(query, "demo-user")}>发送</button>
        )}
      </div>

      <EventStream events={events} />

      {finalAnswer && (
        <article className="final">
          <h2>修复方案建议列表</h2>
          <div dangerouslySetInnerHTML={{ __html: renderMarkdown(finalAnswer) }} />
        </article>
      )}
    </div>
  );
}
```

`renderMarkdown` 用任意 markdown-it / marked 即可，不再展开。

---

## 4、端到端跑一次

### 4.1 启动后端

```bash
uv run uvicorn app.api.server:app --host 0.0.0.0 --port 8000
```

启动时确认日志里这些组件就位：

```
[INFO] LLM 已初始化（model=qwen3-30b-a3b-instruct）
[INFO] 三塔召回 endpoint 健康
[INFO] Faiss 索引已加载（n=15234）
[INFO] Store 后端：redis（已连接）
[INFO] FastAPI listening on 0.0.0.0:8000
```

### 4.2 启动前端

```bash
cd frontend && pnpm dev
```

打开 `http://localhost:5173\`，输入：

```
我想实现一套ArkUI 页面状态恢复方案，目标 HarmonyOS 5.0，最好不要使用废弃 API，喜欢贴合项目现有代码风格。
```

### 4.3 终端看到的事件流（copy本地输出）

```
14:23:01.001  🟢 会话已创建        thread_id=abc123
14:23:01.420  ▶️  工具开始          planner   args={query: "..."}
14:23:02.140  ✅ 工具完成          planner   720 ms
14:23:02.155  ▶️  工具开始          api_insight  depth=quick
14:23:02.840  ✅ 工具完成          api_insight  685 ms
14:23:02.860  🌿 派发子 Agent       sub-9e1f-d1   demands="harmony_docs ..."
14:23:02.860  🌿 派发子 Agent       sub-7a3c-d1   demands="openharmony_docs ..."
14:23:02.861  🌿 派发子 Agent       sub-4b8d-d1   demands="sample_code ..."
14:23:02.861  🌿 派发子 Agent       sub-2c6e-d1   demands="migration_notes ..."
14:23:02.862  ▶️  工具开始          doc_search source=harmony_docs
14:23:02.862  ▶️  工具开始          doc_search source=openharmony_docs
14:23:02.862  ▶️  工具开始          doc_search source=sample_code
14:23:02.862  ▶️  工具开始          doc_search source=migration_notes
14:23:04.520  ✅ 工具完成          doc_search 1658 ms (harmony_docs)
14:23:04.733  ✅ 工具完成          doc_search 1871 ms (openharmony_docs)
14:23:05.018  ✅ 工具完成          doc_search 2156 ms (sample_code)
14:23:05.221  ✅ 工具完成          doc_search 2359 ms (migration_notes)
14:23:05.500  ▶️  工具开始          solution_compare
14:23:05.626  ✅ 工具完成          solution_compare 126 ms
14:23:05.640  ▶️  工具开始          compat_check
14:23:05.678  ✅ 工具完成          compat_check 38 ms
14:23:05.700  ▶️  工具开始          patch_picker
14:23:05.823  ✅ 工具完成          patch_picker 123 ms
14:23:05.840  ▶️  工具开始          dev_summary
14:23:08.412  ✅ 工具完成          dev_summary 2572 ms
14:23:08.420  🎉 任务完成
```

注意 `🌿 派发子 Agent` 的四条同时刻发生——这是真正的并发。前 14 章铺垫的所有能力，最终汇聚成这一段事件流。

### 4.4 最终回答样例

```markdown
## 推荐 3 个修复方案
1. **LocalStorage 页面级状态保存（sample_code）** — 落地成本 2.4
   - 覆盖页面返回后的 ArkUI 页面状态恢复，不含废弃 API ✓
   - 目标 HarmonyOS 5.0 兼容 ✓
   - 改动集中在单页面，符合"贴合项目现有代码风格"偏好 ✓

2. **AppStorage 全局状态方案（openharmony_docs）** — 落地成本 2.7
   - 适合跨页面共享状态，兼容 Stage 模型 ✓
   - 需要补充生命周期清理，风险中等 ✓
   - 采纳次数 2.4k，可信度 4.7

3. **@Provide/@Consume 组件树状态下发（harmony_docs）** — 落地成本 2.9
   - 适合同一页面组件树内状态同步，非废弃 API ✓
   - 验证耗时约 12 分钟
   - 适合追求低侵入改造的项目

## 已为你避开
- 若干条不兼容写法已过滤
- 8 条超版本约束选项已剔除

## 沉淀偏好（已写入长期记忆）
- 不要使用废弃 API
- 偏好贴合项目现有代码风格
```

---

## 5、上线前的工程建议列表

| 类别 | 检查项 |
| --- | --- |
| 资源限额 | 单 thread_id 并发任务上限 / 单用户每分钟启动任务上限 |
| 容灾 | 三塔召回 / Store / 文档源或工程扫描任一不可用时的降级路径 |
| 观测 | active_tasks 数量 / fork 深度分布 / 单工具 P99 / 任务超时率 |
| 安全 | 上传文件大小限制 / 类型白名单 / safe_join 单元测试 |
| 评测训练 | 高分轨迹沉淀 / Rubric judge 服务部署 / SFT-RL 实验接口预留 |

这些不在项目主线，但生产化时必须补齐。

---

## 6、回头看：8 + 7 章学到了什么

回到第 0 章前言开篇说的"工程进阶线"：

| 章节 | 在最后这条端到端链路里贡献了什么 |
| --- | --- |
| 第 1-3 章 | AgentLoop 范式 + fork 三件事判断 → 主 loop 的"怎么思考" |
| 第 4 章 | 三塔召回 → DocSearch 内部"怎么真的搜得准" |
| 第 5 章 | Cache Breakpoint → 50 轮长对话不爆 token、不掉缓存 |
| 第 6 章 | 长期记忆 Store → 用户"不要使用废弃 API"沉淀下来下次自动生效 |
| 第 7 章 | AGUI 事件协议 → 用户能看到子 Agent 在执行任务 |
| 第 8 章 | Rubric 评测 + 高分轨迹沉淀 + SFT/RL 规划 → 模型行为可持续优化 |
| 第 9-10 章 | 项目地图 + 工程底座 → 把上面 8 章变成可工程化复用的组件 |
| 第 11-13 章 | 9 个工具的真正实现 → 让能力具体可用 |
| 第 14 章 | 主 AgentLoop 组装 + 防失控四件套 → 让系统稳健可上线 |
| 第 15 章 | FastAPI + WebSocket + AGUI 前端 → 让用户能用 |

所谓"AgentLoop + 多 Agent + 三塔召回 + 评测训练"一整套，并不是一个抽象口号——它是 15 章每一章解决的一个具体问题叠加起来的结果。

---

**本章小结：**

到这里，HarmonyDev 项目已经端到端跑通：

- FastAPI 落地启动任务 / WebSocket / 取消 / 上传 / 下载五类接口；

- 主 AgentLoop 通过 `asyncio.create_task` 后台跑，HTTP 立即返回 thread_id 不阻塞前端；

- AGUI 事件协议作为"前后端唯一约定"，前端只需根据 event 类型显示不同的卡片；

- 一条"多源搜ArkUI 状态保存"的 query 让你观察到 4 个 fork 同时发生、4 路 DocSearch 并发、合流后方案对比筛选、最终修复建议展示；

- 上线前还需要补限额 / 容灾 / 观测 / 安全 / 评测训练这些生产化能力，当前文档只保留接口和演进边界。

到此，「鸿蒙开发助手」项目的 15 章主线全部完成。完整梳理后，这不只是一个鸿蒙开发助手 demo，而是把 AgentLoop 范式、多 Agent fork、向量召回、上下文压缩、长期记忆、AGUI、评测训练这一整套工业级能力都装进了同一条业务链路里。当评审继续追问"为什么这条链路这么慢 / 这么贵 / 这么不稳"——你能定位该从哪一层优化。
