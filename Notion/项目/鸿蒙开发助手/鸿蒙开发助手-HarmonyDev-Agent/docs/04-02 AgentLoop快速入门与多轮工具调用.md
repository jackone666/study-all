# 02 AgentLoop快速入门与多轮工具调用

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 搭好本地运行环境，跑通第一个 AgentLoop 最小示例。

- 理解单轮和多轮工具调用在代码层面的区别：消息追加、循环判断、终止条件。

- 掌握 stream 模式下的 chunk 类型，知道前端拿到的每条事件代表什么含义。

**阅读重点：** 先看单轮示例搞清楚"一次完整的 Think → Act → Observe"长什么样，再看多轮示例理解"循环是怎么转起来的"。不要跳着看，顺序很重要。

---

## 1、本章导读

上一章建立了 AgentLoop 的概念模型：Think → Act → Observe → Reflect 循环。但概念终归是概念，不跑一遍代码，很难真正理解"循环在哪发生""终止条件谁来判断"。

本章做两件事：

1. 搭环境，确保模型能调通。

1. 从最简单的单轮示例开始，逐步过渡到多轮循环和 stream 模式。

暂时不碰的：多 Agent fork（第 3 章）、真实文档源和工程扫描接入（第 11 章起）。本章所有示例用轻量实现，专注理解循环本身，真实 API 接入放到第 11 章起。

---

## 2、环境准备

### 2.1 依赖安装

本项目使用 `uv` 管理 Python 环境。进入项目根目录后执行：

```bash
uv sync
```

如果是第一次拉仓库，先确认 Python 版本：

```bash
uv run python -V
# 期望输出: Python 3.10.x 或更高
```

### 2.2 环境变量配置

复制示例文件并填入真实 Key：

```bash
cp .env.example .env
```

`.env` 中需要配置的核心变量：

| 变量名 | 作用 | 示例值 |
| --- | --- | --- |
| `LLM_API_KEY` | 大模型 API Key | `sk-xxxx` |
| `LLM_BASE_URL` | 大模型 API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1\` |
| `LLM_MODEL_NAME` | 模型名称 | `qwen-max` |

### 2.3 模型初始化

项目统一通过 `app/agent/llm.py` 创建模型对象：

```python
# app/agent/llm.py
import os
from langchain_openai import ChatOpenAI

def get_llm():
    """创建统一的大模型对象，所有 AgentLoop 实例共用。"""
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL_NAME", "qwen-max"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=0.1,
    )
```

确认环境可用：

```bash
uv run python -c "from app.agent.llm import get_llm; print(get_llm().invoke('你好').content)"
```

如果能正常输出模型的回复，说明环境搭建完成。

---

## 3、最小示例：单轮 AgentLoop

### 3.1 定义一个模拟工具

先用一个轻量工具来演示循环（内部逻辑后续章节再接真实 API）：

```python
# examples/02_quickstart.py
from langchain_core.tools import tool

@tool
def doc_search(query: str) -> str:
    """在多源开发资料库搜索API/代码片段，返回匹配的API/代码片段列表。"""
    return f"找到 3 条匹配「{query}」的 API/代码片段：LocalStorage 页面状态保存、AppStorage 全局状态、@Provide/@Consume 组件状态下发"
```

`@tool` 装饰器做了三件事：

1. 把函数注册为 LangChain 工具。

1. 自动从函数签名生成 JSON Schema（模型会看到参数名和类型）。

1. 把 docstring 作为工具描述（模型靠这段话决定什么时候调用它）。

### 3.2 组装并运行单轮循环

```python
from app.agent.llm import get_llm
from langgraph.prebuilt import create_react_agent

# 组装 AgentLoop：模型 + 工具集
agent = create_react_agent(
    model=get_llm(),
    tools=[doc_search],
    prompt="你是一个鸿蒙开发助手，用户问你什么你就帮忙搜。",
)

# 执行一次完整循环
result = agent.invoke({"messages": [("user", "帮我搜一下ArkUI 状态管理问题")]})

# 查看最终回复
for msg in result["messages"]:
    print(f"[{msg.type}] {msg.content[:100]}")
```

### 3.3 输出解读

运行后你会看到类似：

```
[human] 帮我搜一下ArkUI 状态管理问题
[ai] (工具调用: doc_search, args: {"query": "ArkUI 状态管理问题"})
[tool] 找到 3 条匹配「ArkUI 状态管理问题」的 API/代码片段：LocalStorage 页面状态保存、AppStorage 全局状态、@Provide/@Consume 组件状态下发
[ai] 帮你找到了 3 条 ArkUI 状态管理问题相关 API/代码片段：LocalStorage 页面状态保存、AppStorage 全局状态、@Provide/@Consume 组件状态下发。需要我帮你方案对比吗？
```

四条消息对应一轮完整循环：

| 消息类型 | 对应阶段 | 内容 |
| --- | --- | --- |
| human | 用户输入 | 原始 query |
| ai | Think | 模型决定调用 `doc_search` |
| tool | Observe | 工具返回的结果 |
| ai | Reflect | 模型基于结果生成最终回答 |

这就是一轮 Think → Act → Observe → Reflect 的完整过程。

---

## 4、多轮循环：Think → Act → Observe → 继续 Think

### 4.1 为什么需要多轮

单轮循环只够处理"搜一下 X"这种简单请求。但如果用户说：

```
帮我搜一下ArkUI 状态管理问题，然后看看哪条方案最稳妥
```

模型需要：

1. 先调 `doc_search` 查 API/代码片段；

1. 看完结果后，再调 `solution_compare` 方案对比；

1. 比完价之后，才能给出最终推荐。

这就需要多轮循环。

### 4.2 增加第二个工具

```python
@tool
def solution_compare(item_name: str) -> str:
    """多源比较实现成本格，返回各资料源对应的兼容性风险的落地成本。"""
    return f"「{item_name}」方案复杂度：HarmonyOS 官方文档 2.8，OpenHarmony 文档 2.1（兼容风险低），示例工程 2.4"
```

### 4.3 多轮运行

```python
agent = create_react_agent(
    model=get_llm(),
    tools=[doc_search, solution_compare],
    prompt="你是一个鸿蒙开发助手。用户的请求可能需要多步完成：先查 API/代码片段，再方案对比。",
)

result = agent.invoke({
    "messages": [("user", "帮我搜 ArkUI 状态保存，然后做多源方案对比")]
})
```

### 4.4 输出解读

```
[human] 帮我搜 ArkUI 状态保存，然后做多源方案对比
[ai] (工具调用: doc_search, args: {"query": "ArkUI 状态保存"})
[tool] 找到 3 条匹配「ArkUI 状态保存」的 API/代码片段：LocalStorage 页面状态保存、AppStorage 全局状态、@Provide/@Consume 组件状态下发
[ai] (工具调用: solution_compare, args: {"item_name": "ArkUI 状态保存"})
[tool] 「ArkUI 状态保存」方案复杂度：HarmonyOS 官方文档 2.8，OpenHarmony 文档 2.1（兼容风险低），示例工程 2.4
[ai] 搜到了 ArkUI 状态保存，修复方案对比结果：OpenHarmony 文档最稳妥（兼容风险低），推荐优先采纳。
```

注意这里有**两次** ai → tool 的循环，最后一条 ai 是最终回答。模型自己决定了"先搜再方案对比"的顺序，以及"对比完成就可以收尾了"。

这就是 AgentLoop 的核心：**循环次数不是你定的，是模型根据任务需要自己决定的。**

---

## 5、stream 模式与 chunk 类型

### 5.1 为什么需要 stream

`invoke()` 是等所有循环跑完才返回。在真实场景里，一次任务可能跑 10+ 秒。如果前端一直没有反馈，用户体验很差。

`astream_events()` 可以在执行过程中逐步推送事件，让前端实时显示"正在搜索""正在方案对比"。

### 5.2 stream 事件类型

```python
async for event in agent.astream_events(
    {"messages": [("user", "帮我搜ArkUI 状态保存")]},
    version="v2",
):
    print(f"[{event['event']}] {event.get('name', '')} {str(event.get('data', ''))[:80]}")
```

你会看到类似事件序列：

| 事件名 | 对应阶段 | 含义 |
| --- | --- | --- |
| `on_chat_model_start` | Think | 模型开始推理 |
| `on_chat_model_stream` | Think | 模型逐 token 输出（流式） |
| `on_tool_start` | Act | 工具开始执行 |
| `on_tool_end` | Observe | 工具返回结果 |
| `on_chat_model_start` | Reflect | 模型再次推理（可能是最终回答） |
| `on_chat_model_end` | 结束 | 本轮循环完成 |

### 5.3 和 AGUI 事件协议的关系

后面第 7 章会讲 AGUI 事件协议。这里先建立一个映射印象：

| LangGraph 原生事件 | AGUI 事件（第 7 章） | 前端展示 |
| --- | --- | --- |
| `on_tool_start` | `tool_start` | "正在调用 DocSearch..." |
| `on_chat_model_start` | `assistant_call` | "Agent 正在思考..." |
| 最终 ai message | `task_result` | 展示最终回答 |

现在不需要深入 AGUI，只需要知道 stream 事件是后面前端实时推送的数据源。

---

## 6、工具声明格式详解

### 6.1 @tool 装饰器的三要素

```python
@tool
def doc_search(query: str, source: str = "all") -> str:
    """在指定资料源搜索API/代码片段。

    Args:
        query: 搜索关键词，如"ArkUI 状态保存"
        source: 目标资料源，可选 harmony_docs/openharmony_docs/sample_code/migration_notes/all
    """
    # 实际实现...
    return "搜索结果"
```

模型看到的是：

| 要素 | 来源 | 模型怎么用 |
| --- | --- | --- |
| 工具名 | 函数名 `doc_search` | 决定调哪个工具 |
| 描述 | docstring 第一行 | 判断"这个工具能干什么" |
| 参数 Schema | 函数签名 + Args 注释 | 知道传什么参数、每个参数什么含义 |

### 6.2 好的工具描述 vs 差的工具描述

| 差 | 好 |
| --- | --- |
| "搜索工具" | "在指定开发资料源搜索API/代码片段，返回API/代码片段名称和实现成本列表" |
| 没有参数说明 | 每个参数都有类型和一句话解释 |
| 返回值不明确 | docstring 里说明"返回 JSON 格式的API/代码片段列表" |

模型是靠工具描述来决定"什么时候该调这个工具"的。描述写得越精准，模型的 Think 阶段决策就越准。

---

## 7、真实鸿蒙开发场景示例

把上面的知识串起来，模拟一个完整的开发场景：

```python
@tool
def planner(user_input: str) -> str:
    """拆解用户的开发需求，提取版本约束、API 约束、Kit 领域等结构化信息。"""
    # 结构化返回
    return "需求拆解：Kit 能力域=ArkUI 状态管理, 目标版本=HarmonyOS 5.0, 偏好=不要使用废弃 API, 代码风格=项目现有代码风格"

@tool
def doc_search(query: str) -> str:
    """搜索API/代码片段。"""
    return f"搜到 5 条匹配「{query}」的 API/代码片段"

@tool
def patch_picker(items: str, preference: str) -> str:
    """根据开发者画像从API/代码片段列表中筛选。"""
    return f"根据偏好「{preference}」，推荐其中 2 条：AppStorage 全局状态方案、LocalStorage 页面状态保存方案"

# HarmonyDev 主 AgentLoop 的 system prompt（七要素结构化模板）
SYSTEM_PROMPT = """<role>
你是 HarmonyDev 鸿蒙开发助手。能力边界：仅负责文档检索 + 方案对比 + 筛选，
不直接替开发者提交代码、不自动推送远端分支、不绕过人工确认。
</role>

<workflow>
对每个用户开发问题，按 Think → Act → Observe → Reflect 推进：
1. Think：拆解需求（Kit 领域 / 版本约束 / API 约束 / 排除项）
2. Act：调工具搜索 / 方案对比
3. Observe：检查工具返回是否覆盖用户全部约束
4. Reflect：信息够了就输出推荐；不够就回到 Think 补
</workflow>

<tool_policy>
- 复杂需求（含多个约束词）必先调 planner，不要直接 doc_search
- doc_search 之后必须调 patch_picker，不准跳过筛选直接给修复建议
- 同一个 query 不要反复调 doc_search（最多 1 次，除非 Reflect 判定需要换关键词）
</tool_policy>

<termination>
满足任一即停止循环：
- 已经返回了 ≤ 5 件最终推荐
- 用户原始约束全部覆盖
- 连续 2 轮 Reflect 都判定“信息已足够”
</termination>

<output_format>
最终输出 JSON：{"items": [...], "reasoning": "..."}。
推荐理由必须显式回应用户的每一条约束（版本约束 / API 约束 / 代码风格）。
</output_format>

<constraints>
- 不准编造API/代码片段名 / 实现成本，所有信息来自工具返回
- 用户的“排除项”（“不要 X”）是硬约束，违反即重新筛选
- 不准擅自加入用户没要求的约束筛选
</constraints>"""

agent = create_react_agent(
    model=get_llm(),
    tools=[planner, doc_search, patch_picker],
    prompt=SYSTEM_PROMPT,
)

result = agent.invoke({
    "messages": [("user", "想实现一套ArkUI 状态管理问题，目标 HarmonyOS 5.0，不要使用废弃 API，偏项目现有代码风格")]
})
```

执行后模型会自主完成三步循环：

```
Think: 需求复杂，先拆解 → Act: 调 planner
Think: 拆解完了，去查 API/代码片段 → Act: 调 doc_search
Think: 搜到了，按偏好筛选 → Act: 调 patch_picker
Reflect: 筛选完了，信息足够，输出最终推荐
```

注意：**你没有硬编码"先调 planner 再调 search 再调 picker"这个顺序**。模型根据 system_prompt 和工具描述自己规划的。这就是 AgentLoop 和 Workflow 的本质区别。

### 7.1 这段 system prompt 为什么这么写

上面那段 prompt 用了 6 个 XML 标签。Anthropic 官方推荐用 XML 做结构化分块，理由是模型对 `<tag>` 边界的识别比 Markdown 标题更稳定。每一段对应 AgentLoop 的一个阶段：

| XML 标签 | 对应 AgentLoop 阶段 | 不写会怎样 |
| --- | --- | --- |
| `<role>` | 全局——身份和能力边界 | 模型可能越界（比如替用户绕过确认直接改代码），或拒绝合理请求 |
| `<workflow>` | Think → Act → Observe → Reflect | 模型不知道每轮该做什么，倾向"一问一答" |
| `<tool_policy>` | Act 阶段——工具调度策略 | 模型可能跳过 planner 直接 doc_search，结果失控 |
| `<termination>` | Reflect 阶段——什么时候停 | 死循环（最常见的 Agent 故障，调试时排第一） |
| `<output_format>` | 最终输出 | 模型自由发挥，下游解析失败 |
| `<constraints>` | 全局——硬约束 | 用户说“不要使用废弃 API”，模型仍可能推荐废弃 API品 |

写 prompt 时还有几条经验：

- `<termination>`** 是新手最容易漏的**：没有显式终止条件，模型会一直 Reflect → Think → Act 循环到 `recursion_limit` 才停，token 全在死循环里烧掉。

- `<tool_policy>`** 不写工具调用顺序，写“调度规则”**：硬编码顺序就退化成 Workflow，破坏了 AgentLoop “自主规划”的本质；写“复杂需求必先调 planner”这种规则才是正确做法。

- `<constraints>`** 里的“不准 X”是硬约束**：模型对否定式指令的遵守率会随上下文变长而下降，所以这里必须显式写出，并放在 prompt 末尾（位置敏感性原则——越靠后的约束遵守率越高）。

后续章节的主 AgentLoop 会沿用这个七要素模板，每一章只补充对应阶段的细节（比如第 4 章在 `<tool_policy>` 里加上 `doc_search` 三塔召回的说明、第 6 章在 `<constraints>` 里注入用户开发者画像）。

---

**本章小结：**

到这里，你应该能跑通 AgentLoop 的基础示例，并理解以下几点：

1. AgentLoop 在代码层面就是一个 `while` 循环：模型生成 → 判断是否调用工具 → 追加结果 → 继续循环。

1. 循环次数由模型自己决定，不需要外部控制。

1. stream 模式可以在循环过程中逐步推送事件，是后面 AGUI 实时推送的基础。

1. 工具声明的质量（名字、描述、参数 Schema）直接影响模型的 Think 决策准确度。

1. 一个真实鸿蒙开发场景可能触发 3-5 次循环，模型自主规划调用顺序。

下一章「[主 AgentLoop 按需 fork 同质子 AgentLoop 的策略与三件事判断](<05-03-0 主AgentLoop按需fork同质子AgentLoop的策略与三件事判断.md>)」会回答一个关键问题：当主 loop 遇到需要并行或隔离的子任务时，怎么 fork 出同质的子 AgentLoop 去执行，以及什么时候该 fork、什么时候自己扛。
