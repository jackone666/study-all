# 06 长期记忆与开发者画像Store

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 区分"长上下文"和"长期记忆"：前者按 token 涨钱，后者按条目持久化。

- 理解 Store 的数据结构：开发者画像、历史选择、黑名单关键词怎么存、怎么读。

- 掌握记忆注入时机：新会话起来时自动注入到 system prompt，让 Agent "记得你"。

**阅读重点：** 上一章讲了怎么"丢掉"历史消息（压缩）。本章讲的是：在丢掉历史之前，**把值得记住的东西抽出来存好**。两者是一对互补关系——有了长期记忆，上下文才能放心压缩，不怕丢失开发者画像。

---

## 1、本章导读

### 1.1 一个真实的用户体验问题

用户第一次对话：

```
用户：帮我搜ArkUI 状态保存，不要使用废弃 API
Agent：好的，已为你过滤掉废弃 API的API/代码片段...（返回LocalStorage/AppStorage款）
```

用户第二次对话（新会话）：

```
用户：帮我搜ArkUI 状态管理方案
Agent：返回了一堆废弃 APIArkUI 状态管理方案
```

为什么？因为**新会话没有上一次的对话历史**。Agent 不知道用户"不要使用废弃 API"的偏好。

这个问题不能靠"把所有历史消息都保留"来解决——跨会话的消息历史不共享，即使共享了也会让上下文爆炸。

正确的解法是：**把"不要使用废弃 API"这个偏好存到一个独立的长期记忆里，每次新会话起来时自动注入。**

### 1.2 本章先做什么，不做什么

本章完成的是：

1. 理解长期记忆和上下文的本质区别。

1. 看懂 Store 的数据结构和读写接口。

1. 理解记忆注入的时机和方式。

暂时不碰的：

- Store 的持久化后端选型（Redis / Postgres / 文件系统，放项目主线章节）。

- 记忆的自动提取（从对话中自动识别"值得记住的偏好"，涉及 NLU，放高级章节）。

---

## 2、长上下文 ≠ 长期记忆

### 2.1 两个完全不同的数据结构

| 维度 | 长上下文（消息历史） | 长期记忆（Store） |
| --- | --- | --- |
| 数据格式 | 有序消息列表（human/ai/tool） | 结构化条目（key-value） |
| 生命周期 | 一次会话内有效 | 跨会话持久化 |
| 成本模型 | 按 token 计费（越长越贵） | 按存储计费（条目数固定就不涨） |
| 增长方式 | 每轮循环自动追加 | 只在检测到新偏好时才写入 |
| 对模型影响 | 占用注意力窗口 | 只注入相关条目，不占过多窗口 |

### 2.2 互补关系

```
长期记忆 Store（存偏好）    长上下文（存对话过程）
         ↓                           ↓
   新会话时注入              本会话内追加
         ↓                           ↓
   "用户不要使用废弃 API"           "第 3 轮搜了ArkUI 状态管理方案"
         ↓                           ↓
   不随上下文膨胀            会膨胀，需要压缩
```

有了 Store，上下文可以放心压缩——即使丢掉了"用户上次说不要使用废弃 API"这条历史消息，偏好已经存在 Store 里了，下次新会话起来时会自动注入。

---

## 3、Store 的数据结构

### 3.1 偏好条目

每个用户的 Store 里保存的是一组结构化的偏好条目：

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PreferenceEntry:
    """开发者画像的一条记录。"""
    key: str                          # 唯一标识，如 "api_blacklist"
    category: str                     # 分类：preference / history / blacklist
    content: str                      # 偏好内容，如 "不要使用废弃 API"
    source_session: str               # 来源会话 ID
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0           # 置信度（多次提及 → 高置信）
```

### 3.2 一个用户的 Store 长什么样

```yaml
user_id: "user-abc123"
preferences:
  - key: api_blacklist
    category: blacklist
    content: "不接受废弃 API 的 API/代码片段"
    confidence: 1.0

  - key: code_style_preference
    category: preference
    content: "偏好项目现有代码风格、低改动的 ArkUI 方案"
    confidence: 0.8

  - key: target_version
    category: preference
    content: "常用目标版本为 HarmonyOS 5.0 / API 9+"
    confidence: 0.9

  - key: source_preference
    category: preference
    content: "倾向在 OpenHarmony 文档 采纳，因为之前有好的开发体验"
    confidence: 0.6

history:
  - key: last_adopted_solution
    category: history
    content: "上次采纳了 AppStorage 全局状态方案（OpenHarmony 文档）"

  - key: last_search
    category: history
    content: "上次搜索了 ArkUI 状态保存，最终选了 LocalStorage 页面级方案"
```

注意：Store 里存的不是原始对话消息，而是**从对话中提取出来的结构化偏好**。它的 token 数非常小（通常整个 Store 不超过 500 token），不会显著膨胀上下文。

---

## 4、记忆的写入

### 4.1 什么时候写

记忆写入发生在 AgentLoop 的 **Reflect 阶段**——当主 loop 检测到用户表达了明确的偏好时，触发写入：

```python
async def maybe_write_preference(user_message: str, user_id: str):
    """检测用户消息中是否包含值得记住的偏好。"""
    # 简单规则匹配（生产环境可用 NLU 模型）
    blacklist_patterns = ["不要", "不接受", "排除", "别推"]
    preference_patterns = ["喜欢", "偏好", "倾向", "习惯"]

    for pattern in blacklist_patterns:
        if pattern in user_message:
            await store.write(user_id, PreferenceEntry(
                key=f"blacklist_{hash(user_message)[:8]}",
                category="blacklist",
                content=user_message,
                source_session=get_current_thread_id(),
            ))
            return
```

### 4.2 写入时机在链路中的位置

```
用户说 "不要使用废弃 API"
  → 主 loop Think: 识别到这是偏好表达
  → 同时做两件事：
    1. 在当前 Observe 中过滤废弃 API/代码片段（即时生效）
    2. 写入 Store（持久化，下次会话也生效）
```

---

## 5、记忆的读取与注入

### 5.1 注入时机：新会话起来时

每次新会话创建时（`run_agent` 函数开头），从 Store 读取该用户的偏好，注入到 system prompt 末尾：

```python
async def run_agent(query: str, thread_id: str, user_id: str):
    """AgentLoop 执行入口。"""
    # 读取用户开发者画像
    preferences = await store.read(user_id)

    # 格式化成一段文本
    pref_text = format_preferences(preferences)
    # 示例输出：
    # "开发者画像：不接受废弃 API | 偏好项目现有代码风格 | 目标 HarmonyOS 5.0 / API 9+ | 倾向 OpenHarmony 文档"

    # 注入到 system prompt 末尾
    full_prompt = SYSTEM_PROMPT + f"\n\n【用户开发者画像】\n{pref_text}"

    # 创建 AgentLoop 实例（带偏好的 prompt）
    agent = create_react_agent(
        model=get_llm(),
        tools=FULL_TOOL_SET,
        prompt=full_prompt,
    )

    # 执行...
```

### 5.2 注入后的效果

注入前（无记忆）：

```
System: 你是 HarmonyDev 鸿蒙开发助手...
User: 帮我搜ArkUI 状态管理方案
Agent: [返回各种API 约束的ArkUI 状态管理方案，包括废弃 API的]
```

注入后（有记忆）：

```
System: 你是 HarmonyDev 鸿蒙开发助手...
【用户开发者画像】不接受废弃 API | 偏好项目现有代码风格 | 目标 HarmonyOS 5.0 / API 9+

User: 帮我搜ArkUI 状态管理方案
Agent: [自动过滤废弃写法，只推荐AppStorage/LocalStorage/皮质的项目现有代码风格款]
```

用户没有重复说"不要使用废弃 API"，但 Agent 记得。

### 5.3 token 成本

整个偏好注入通常只有 100-300 token（取决于偏好条目数）。相比把所有历史会话都保留（可能几万 token），这种方式：

- token 成本：几百 vs 几万。

- 信息密度：高（只有结论性偏好）vs 低（大量无关对话过程）。

- 时效性：始终最新 vs 可能包含已过时的偏好。

---

## 6、Store 接口设计

### 6.1 核心接口

```python
class PreferenceStore:
    """开发者画像存储的抽象接口。"""

    async def read(self, user_id: str) -> list[PreferenceEntry]:
        """读取某用户的所有偏好条目。"""
        ...

    async def write(self, user_id: str, entry: PreferenceEntry) -> None:
        """写入一条偏好。如果 key 相同则覆盖。"""
        ...

    async def delete(self, user_id: str, key: str) -> None:
        """删除某条偏好（用户主动撤回时）。"""
        ...

    async def read_relevant(self, user_id: str, query: str, top_k: int = 5) -> list[PreferenceEntry]:
        """读取和当前 query 最相关的 top_k 条偏好（向量匹配）。"""
        ...
```

### 6.2 `read_relevant` 为什么重要

如果一个用户积累了 50 条偏好，全部注入会占 2000+ token。`read_relevant` 基于当前 query 做向量匹配，只注入最相关的 5 条：

```
用户搜 "ArkUI 状态管理方案"
  → read_relevant 返回：
    - "不接受废弃 API"（相关：ArkUI 状态管理方案常见废弃 API）
    - "目标 HarmonyOS 5.0 / API 9+"（相关：实现成本约束）
    - "偏好项目现有代码风格"（相关：代码风格约束）
  → 不返回：
    - "上次在 版本迁移说明 用过 FA 模型"（不相关）
    - "喜欢数码产品"（不相关）
```

---

## 7、和上一章压缩的协同

| 上一章（Cache Breakpoint） | 本章（长期记忆 Store） |
| --- | --- |
| 解决"上下文太长" | 解决"跨会话遗忘" |
| 通过压缩/丢弃减少 token | 通过持久化保留关键信息 |
| 作用域：单次会话内 | 作用域：跨会话持久 |
| 对象：消息历史 | 对象：结构化偏好条目 |

两者协同的方式：

```
会话 1：用户说"不要使用废弃 API" → 写入 Store
会话 1 结束：消息历史被丢弃

会话 2 开始：从 Store 读取"不要使用废弃 API" → 注入 system prompt
会话 2：用户搜任何东西，Agent 自动过滤废弃 API
```

---

**本章小结：**

到这里，你应该理解长期记忆在 HarmonyDev 中的作用：

1. 长上下文和长期记忆是两个不同的数据结构：前者按 token 涨钱且只在单会话有效，后者按条目持久化且跨会话共享。

1. Store 里存的是结构化的偏好条目（偏好 / 历史 / 黑名单），不是原始对话消息。

1. 记忆写入发生在 Reflect 阶段（检测到用户表达偏好时），读取发生在新会话起来时（注入 system prompt）。

1. `read_relevant` 按 query 相关性只注入最相关的 5 条偏好，避免注入过多无关信息。

1. 长期记忆和上下文压缩是互补关系：有了 Store 保底，上下文才能放心压缩。

下一章「[AGUI 事件协议与 WebSocket 实时推送](<12-07 AGUI事件协议与WebSocket实时推送.md>)」会讲前端怎么实时看到 Agent 正在干什么——tool_start / assistant_call / task_result 这套事件协议是怎么设计的。
