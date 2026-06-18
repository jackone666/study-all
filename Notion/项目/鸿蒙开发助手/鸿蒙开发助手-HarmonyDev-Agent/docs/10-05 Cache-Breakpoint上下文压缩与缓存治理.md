# 05 Cache-Breakpoint上下文压缩与缓存治理

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 理解为什么多轮对话会导致 token 成本失控：每轮循环追加消息，上下文只增不减。

- 掌握"压缩和缓存是同一个问题的两面"这个核心洞察，以及盲目压缩为什么会适得其反。

- 学会 Cache Breakpoint 的设计：把对话切成"缓存区"和"可压缩区"，在不破坏缓存命中率的前提下压缩。

**阅读重点：** 本章是 HarmonyDev 项目里"最不起眼但最关键"的工程层能力。如果你之前做过长对话 Agent 并被 token 成本困扰过，这章会直接对应这个问题。如果没遇到过这个问题，先记住结论：**脱离缓存谈压缩，省下的都是假的。**

---

## 1、本章导读

上几章搭好了 AgentLoop 的决策层（主循环 + 多 Agent fork）和召回层（三塔召回）。但有一个很实际的问题还没解决：

**50+ 轮工具调用之后，上下文里的消息历史可能膨胀到 8 万 token。每次请求模型，这 8 万 token 都要全量发过去。**

这意味着：

- **成本**：按 3 元 / 百万 token 计算，一次请求就是 0.24 元。一天几百次调用，成本飞速膨胀。

- **延迟**：更长的 prompt 意味着更长的首 token 延迟（TTFT）。

- **质量**：关键信息被淹没在中间，模型检索性能下降（Lost in the Middle 效应）。

---

## 2、问题有多痛

### 2.1 HarmonyDev 项目的实测数据

根据 HarmonyDev 项目在构建鸿蒙开发助手 时的实测：

| 场景 | token 膨胀情况 | 成本影响 |
| --- | --- | --- |
| 一次 `doc_search` 返回 100 件API/代码片段 | 可能吃掉 3 万 token | 相当于 10 次普通请求 |
| 一次 `parallel_task_tool` 多源 | 四份结果累计上万行 | 后续每轮都带着这些结果 |
| 10 轮循环后 | 上下文逼近窗口上限 | 触发 InputContentTooLong |

主 loop 调用 `doc_search` 返回 100 件API/代码片段的结构化数据，再调 `solution_compare` 返回多源实现成本——几轮下来，上下文就从几千 token 膨胀到几万。

### 2.2 最直觉的解法：压缩

第一反应通常是：**把历史消息做摘要，减少 token 数。**

```
压缩前：80K token（完整历史）
压缩后：20K token（摘要版）
压缩率：75%
```

听起来省了很多钱。但实测后发现了灾难性问题。

---

## 3、盲目压缩的代价：缓存命中率暴跌

### 3.1 Prompt Cache 是什么

主流 LLM 供应商支持 Prompt Cache 功能——将 system prompt 和对话历史的前缀缓存起来，下次请求如果前缀相同，直接复用 KV Cache：

- **减少 50-80% 的首 token 延迟**

- **降低 40-50% 的 prompt token 成本**

但它有一个苛刻的约束：**缓存只有 5 分钟 TTL，且必须前缀完全匹配。**

### 3.2 压缩为什么会杀死缓存

如果你在每次请求前都对历史做"微压缩"（删掉一些消息、改写一些内容），**前缀就变了**。前缀一变，缓存就失效。

实测结果：

| 方案 | 压缩率 | 缓存命中率 | 综合成本 |
| --- | --- | --- | --- |
| 不压缩 | 0% | 85% | 基准（高但稳定） |
| 盲目压缩 | 30% | 15% | **更高**（缓存全废） |
| Cache-Aware 压缩 | 25% | 80% | **最低** |

**盲目压缩省下的 token 费，全被掉缓存的部分原价输入吃回去了。** 整体成本不降反升。

### 3.3 核心洞察

**压缩和缓存是同一个问题的两面。** 任何压缩方案都必须和 Prompt Cache 命中率放在一起评估。脱离缓存谈压缩效果，就像脱离网络谈序列化方案——可能得出完全错误的结论。

---

## 4、Cache Breakpoint：正确的解法

### 4.1 核心概念

引入一个关键分界线：**Cache Breakpoint**（缓存断点）。

```
对话历史：
[system prompt]          ← 固定不变，始终缓存
[user message 1]         ← 固定不变，始终缓存
[assistant response 1]   ← 固定不变，始终缓存
[tool call 1 result]     ← 固定不变，始终缓存
--- Cache Breakpoint ---  ← 从这里开始可以压缩
[user message 2]         ← 可能被压缩
[assistant response 2]   ← 可能被压缩
[tool call 2 result]     ← 可能被压缩
...
```

**Breakpoint 之前**：绝对不动，保证缓存命中率。
**Breakpoint 之后**：可以自由压缩，不影响缓存复用。

### 4.2 Breakpoint 怎么定位

策略是：**保留最近 K 个工具调用在 Breakpoint 之前**（因为它们最可能被下次请求复用），更早的历史放到 Breakpoint 之后做压缩。

```python
def compute_breakpoint(messages: list, keep_recent: int = 3) -> int:
    """计算 Cache Breakpoint 的位置。

    保留最近 keep_recent 轮工具调用在缓存区，
    更早的历史进入可压缩区。
    """
    tool_call_indices = [
        i for i, msg in enumerate(messages)
        if msg.type == "tool"
    ]

    if len(tool_call_indices) <= keep_recent:
        # 工具调用不多，全部保留在缓存区
        return len(messages)

    # Breakpoint 设在"最近 K 个工具调用"的起始位置
    breakpoint_idx = tool_call_indices[-keep_recent]
    return breakpoint_idx
```

### 4.3 Breakpoint 之后怎么压缩

对 Breakpoint 之后的历史消息，可以用以下策略：

| 策略 | 做法 | 适用场景 |
| --- | --- | --- |
| 截断 | 直接丢弃最早的 N 条消息 | 早期消息已不影响当前任务 |
| 摘要 | 用 LLM 把 N 条消息压缩成一段摘要 | 需要保留关键决策信息 |
| 工具结果精简 | 把大段的 tool_result 只保留关键字段 | 工具返回了过多细节 |

```python
def compress_after_breakpoint(messages: list, breakpoint_idx: int) -> list:
    """压缩 Breakpoint 之后的消息。"""
    cached_part = messages[:breakpoint_idx]       # 不动
    compressible_part = messages[breakpoint_idx:]  # 可压缩

    # 策略：把 tool_result 中超过 500 token 的内容截断

    compressed = [ ]

    for msg in compressible_part:
        if msg.type == "tool" and len(msg.content) > 2000:
            msg = msg.copy()
            msg.content = msg.content[:2000] + "\n[...内容已精简]"
        compressed.append(msg)

    return cached_part + compressed
```

### 4.4 在 Anthropic API 上落地 cache_control

Cache Breakpoint 在概念上很清晰，落到 Anthropic API 的具体写法是 `cache_control` 标记。下面是最小可运行示例：

```python
from anthropic import Anthropic

client = Anthropic()

# 静态/动态分层结构（关键：从前到后内容应该越来越易变）
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
        },
        {
            "type": "text",
            "text": TOOLS_SPEC,
            # cache_control #1：工具定义打缓存（小时级 TTL）
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        },
    ],
    messages=[
        # Cache Breakpoint 之前：早期对话历史
        {
            "role": "user",
            "content": [
                {"type": "text", "text": old_history,
                 # cache_control #2：早期历史打缓存（默认 5 分钟 TTL）
                 "cache_control": {"type": "ephemeral"}},
            ],
        },
        # Cache Breakpoint 之后：可压缩区，不打 cache_control
        *compressed_recent_messages,
        # 当前用户消息：永远变化的部分
        {"role": "user", "content": current_user_msg},
    ],
)

# 响应里能看到缓存命中情况
print(response.usage.cache_creation_input_tokens)   # 写入缓存的 token 数
print(response.usage.cache_read_input_tokens)       # 命中缓存的 token 数
```

落到 API 上有几条**硬约束**必须知道：

| 约束 | 数值 | 踩坑后果 |
| --- | --- | --- |
| 一次请求最多 `cache_control` 标记 | **4 个** | 第 5 个会被忽略，缓存无法写入 |
| 默认 TTL | **5 分钟** | 凌晨低峰期就过期，每天早高峰首请求全部 miss |
| Extended TTL | **1 小时**（`{"type": "ephemeral", "ttl": "1h"}`） | 适合 SYSTEM_PROMPT / TOOLS_SPEC 这类一天不变的内容 |
| 最低写入 token 阈值 | Sonnet 1024、Haiku 2048 | 比阈值短的内容根本不会被写入缓存 |
| 必须前缀完全匹配 | 任何字符变化（包括空格、换行）都会让命中失效 | 不能动态拼时间戳到 SYSTEM_PROMPT 里 |

按“内容易变性”做静态/动态分层是核心心法：

```
[ system prompt + 工具 schema + 知识库摘要 ]   ← cache_control #1（1h TTL，全天不变）
[ 早期对话历史                          ]    ← cache_control #2（5 分钟 TTL，每轮往后挪）
↑ 此线之上是 Cache Breakpoint
[ 最近 K 轮工具调用                       ]   ← 可压缩区，不打 cache_control
[ 当前用户消息                          ]    ← 不缓存，永远变化
```

§4.1 的概念图和这张实现图是同一件事：**「Cache Breakpoint」在工程上就是一个或多个 **`cache_control`** 标记的位置**。§4.2 的 `compute_breakpoint` 函数返回的 `breakpoint_idx`，就是给 messages 数组里某条消息打 `cache_control` 的位置索引。

---

## 5、工具侧防线：从源头控住体积

### 5.1 L0 层：不该进来的别进来

在压缩之前，还有一层更基础的防线：**让工具返回的内容在进入上下文之前就控住体积。**

```
doc_search:
├─ 默认最多返回 20 件API/代码片段（不是 100 件）
├─ 每段候选只保留：标题、来源、API 名、目标版本、可信度
├─ 去掉：完整描述、评论原文、图片 URL
└─ 超出 3000 token 自动截断

solution_compare:
├─ 只返回 top-5 最稳妥的结果
└─ 不返回完整的各资料源原始响应
```

### 5.2 为什么这一层最重要

一个被控住体积的 `doc_search` 返回（3000 token），比让它返回全量数据（15000 token）再事后压缩，**省了一次 LLM 压缩调用的成本**。

投入产出比最高的一层防线。

---

## 6、五层压缩体系全景

Cache Breakpoint 不是孤立的技术点，它是 HarmonyDev 五层压缩体系中的一环：

| 层 | 名称 | 做什么 | 成本 |
| --- | --- | --- | --- |
| L0 | 工具侧防线 | 控制工具返回体积，大内容写文件而非注入上下文 | 零 |
| L1 | 工程手段 | 动态 max_tokens、断点续传、服务端缓存 | 零 |
| L2 | Cache-Aware 微压缩 | 在 Breakpoint 之后做轻度压缩 | 低 |
| L3 | 会话压缩 | 当上下文逼近阈值时，用 LLM 做全量摘要 | 中（一次 LLM 调用） |
| L4 | Session Memory | 持续维护结构化记忆文件，替代全量历史 | 低（增量更新） |

**越往上越"重"（需要 LLM），但压缩效果越好。越往下越"轻"（纯工程），但能解决的问题有限。**

本章讲的 Cache Breakpoint 属于 L2 层。L4 Session Memory 的思路在下一章「长期记忆与开发者画像 Store」里会进一步展开。

---

## 7、关键数据：为什么 Cache Breakpoint 有效

| 指标 | 不压缩 | 盲目压缩 | Cache Breakpoint |
| --- | --- | --- | --- |
| token 数 | 80K | 56K | 60K |
| 压缩率 | 0% | 30% | 25% |
| 缓存命中率 | 85% | 15% | 80% |
| 实际计费 token | 12K | 47.6K | 12K |
| 综合成本 | 基准 | +297% | **-35%** |

关键理解：**实际计费 token = 总 token × (1 - 缓存命中率 × 折扣)**。缓存命中的部分按半价或免费计费，所以命中率才是决定成本的关键变量。

---

**本章小结：**

到这里，你应该理解 HarmonyDev 上下文压缩的核心设计：

1. 多轮对话的上下文只增不减，50 轮后 token 成本会失控。这不是优化问题，是基础设施问题。

1. 盲目压缩会破坏 Prompt Cache 前缀匹配，导致缓存命中率暴跌。省下的压缩费全被原价计费吃回去。

1. Cache Breakpoint 把对话切成"缓存区"和"可压缩区"——断点之前一字不动保缓存，断点之后自由压缩。

1. 工具侧防线（L0）是投入产出比最高的层——从源头控住体积，比事后压缩省一个数量级。

1. 五层压缩体系协同工作，从轻到重逐层兜底。

下一章「[长期记忆与开发者画像 Store](<11-06 长期记忆与开发者画像Store.md>)」会讲一个更彻底的方案：**不靠压缩历史保留信息，而是用一个独立的结构化记忆文件持久化关键信息**，让上下文可以大胆丢弃而不丢失开发者画像。
