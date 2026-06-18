# 03-1 架构选型与 fork 子AgentLoop

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 理解为什么 HarmonyDev 的主智能体范式选 AgentLoop，而不是 PAE（Plan-and-Execute）。

- 理解为什么 HarmonyDev 的多 Agent 协同选**同质子 AgentLoop fork**，而不是 Supervisor-Workers / Network / Hierarchical 这些常见多 Agent 架构。

- 看清两个选型背后是同一个核心理由：**鸿蒙开发场景的子目标是"边走边长"的，不是"开局就能列完"的。**

**阅读重点：** 这一章是一节"为什么不那样做"的对比课。第 3 章已经讲了"什么时候 fork"，本章再退一步讲"为什么是 fork、为什么是 AgentLoop"。建议读完后能用一段话回答"如果让你给一个对话式鸿蒙开发助手 选范式，你会怎么选、为什么"——这是面试 / 评审里最常被追问的题目。

---

## 1、本章导读

### 1.1 这两个问题为什么放一起讲

第 1 章给了 AgentLoop 的范式定义、第 3 章给了"主 loop fork 同质子 AgentLoop"的协同机制。但在面试 / 团队评审里，最常被追问的是这两个：

```
Q1: 你们为什么用 AgentLoop？为什么不直接 Plan-and-Execute？
Q2: 多 Agent 你们为什么用同质 fork？为什么不预定义一组异构 worker？
```

这两个问题表面上是两个，**根上其实是同一个**——

> **鸿蒙开发场景里，下一步该干什么是"边走边长出来"的，不是"开局就能列完"的。**

只要这一条立住，AgentLoop 比 PAE 强、同质 fork 比异构 worker 强，都自然成立。

### 1.2 本章先做什么，不做什么

要做的：

1. 把 AgentLoop 和 PAE 摆在一起对比，给出选型决策表。

1. 把同质 fork 和主流多 Agent 架构（Supervisor-Workers / Network / Hierarchical）摆在一起对比。

1. 用一条 HarmonyDev 真实 query 跑两遍，看不同范式的链路差别。

不做的：

- 不重新讲 AgentLoop 的定义（第 1 章已讲）。

- 不重新讲 fork 三件事判断（第 3 章已讲）。

---

## 2、AgentLoop vs PAE：为什么主范式选 AgentLoop

### 2.1 PAE（Plan-and-Execute）是什么

PAE 是早期非常流行的 Agent 范式，结构很清晰：

```
Step 1: Planner  -> 一次性产出完整 plan（一串子任务建议列表）
Step 2: Executor -> 按 plan 顺序执行每一步
Step 3: 全部跑完后回答用户
```

PAE 的**核心假设是**：开局就能把完整 plan 列出来。

放在很多偏静态、目标明确的任务上（如"查 5 个网页 → 汇总成 PDF"），PAE 跑得又稳又快——因为 plan 里的每一步彼此独立、没有"看了上一步结果再决定下一步"的需求。

### 2.2 但开发场景违反了 PAE 的核心假设

回到 HarmonyDev 的真实 query：

```
"想实现一套ArkUI 页面状态恢复方案，目标 HarmonyOS 5.0，最好不要使用废弃 API，喜欢贴合项目现有代码风格。"
```

如果用 PAE，Planner 在开局会产出类似这样的 plan：

```
1. 在 harmony_docs 搜ArkUI 状态管理问题
2. 在 openharmony_docs 搜ArkUI 状态管理问题
3. 在 sample_code 搜ArkUI 状态管理问题
4. 在 migration_notes 搜ArkUI 状态管理问题
5. 修复方案对比
6. 做兼容性检查
7. 给修复建议
```

看起来很顺。但只要执行下去，麻烦立刻就来：

| 中途出现的情况 | PAE 的处理 | 应该怎么做 |
| --- | --- | --- |
| harmony_docs 搜出来 80% 都是废弃写法 | 继续按原 plan 跑剩下三个平台 | 立刻调 APIInsight 看Kit 领域典型API 约束，调整搜索词 |
| openharmony_docs 数据返回特别快但都是杂牌 | 不会动态加一步"看一下官方变更说明 / 社区 Issue" | 临时加一次 WebSearch 兜底 |
| 4 类资料源合流后发现没有任何API/代码片段落在目标 HarmonyOS 5.0 内 | 仍然按原 plan 方案对比 / 做兼容性检查 / 出建议列表 | 反思版本约束是否应放宽、或调换Kit 领域 |
| 用户上一轮记忆里有"不要使用废弃 API"，但 plan 里没有体现 | plan 不会自动包含历史偏好 | 主 loop 在每一轮 Think 都要把偏好考虑进去 |

PAE 的根本问题是 **plan 一旦定下就难以反悔**。任何"看了中间结果再决定"的能力，都需要用复杂的 re-plan 机制硬补——而 re-plan 本身又是一次"开局列 plan"。

### 2.3 AgentLoop 的应对

AgentLoop 的核心循环是 Think → Act → Observe → Reflect。它的关键不在"循环"本身，而在 **每一轮的 Think 都是基于"截止当前看到的所有信息"重新做决策**。

换句话说：

| 维度 | PAE | AgentLoop |
| --- | --- | --- |
| 决策时机 | 开局一次性 | 每一轮 Think 都重新决策 |
| 决策依据 | 用户原始 query | query + 截止当前所有 Observation + 长期记忆 |
| 应对意外 | re-plan（贵，且容易丢上下文） | 自然在下一轮 Think 里调整 |
| 多轮交互 | 不天然支持 | 天然支持（每轮就是一次决策） |
| 模型 reasoning | 主要给 Planner，Executor 弱化 | 每一轮都用 |

放回 HarmonyDev 上面那个 query，AgentLoop 链路是：

```
Think 1: 缺Kit 能力常识 -> Act: api_insight   -> Observe: 组合方案通常含ArkUI 状态管理方案/路由返回处理/LocalStorage 状态持久化
Think 2: 信息够了，可以并行搜 -> Act: task_tool ×4 -> Observe: 4 路候选
Think 3: 80 件里只有 14 件落在版本约束 -> Act: solution_compare -> Observe: 多源 Top-12
Think 4: 算落地成本 -> Act: compat_check -> Observe: Top-12 的落地成本
Think 5: 应用"不要使用废弃 API"硬约束 + "项目现有代码风格"软偏好 -> Act: patch_picker
Think 6: 信息已足够 -> Act: dev_summary（终结）
```

每一轮 Think 都在"截止当前已知的事实 + 开发者画像 + 长期记忆"上做下一步决策。出意外不需要 re-plan，下一轮自动就处理了。

### 2.4 选型决策表

| 你面对的任务长这样 | 推荐范式 |
| --- | --- |
| 子任务建议列表开局就能列完，彼此独立，不依赖中间结果 | PAE |
| 子任务依赖中间结果 / 开发者画像 / 长期记忆，需要边走边调整 | AgentLoop ✅ |
| 任务里包含"看了 A 的结果再决定要不要做 B" | AgentLoop ✅ |
| 多轮对话场景（用户会随时补充约束） | AgentLoop ✅ |

HarmonyDev 是后三类的叠加。**所以 AgentLoop 是必选，不是可选。**

### 2.5 但 AgentLoop 也不是没代价

为了客观，列一下 AgentLoop 的代价：

| 代价 | 是什么 | HarmonyDev 怎么消化 |
| --- | --- | --- |
| 多次 LLM 推理 | 每一轮 Think 都是一次 LLM 调用，token 比 PAE 多 | Cache Breakpoint（第 5 章）保命中率 |
| 决策不稳定 | 模型每轮独立决策，可能在两个工具间反复横跳 | LoopDetector（第 14 章）触发收敛提示 |
| 链路偏长 | 比 PAE 多 1-2 轮 Think | 系统 prompt 里写明终结性工具优先调用 |

工程上能消化掉这些代价，所以"AgentLoop + 防失控四件套"是更平衡的选择。

---

## 3、subAgent fork vs 其它多 Agent 架构

### 3.1 主流的几种多 Agent 架构

业界谈"多 Agent"，最常见的是这四类（LangGraph 文档里都各自有模板）：

| 架构 | 长什么样 |
| --- | --- |
| Supervisor-Workers | 1 个 Supervisor + N 个角色固定的 Worker（如 DocAgent / CompatAgent） |
| Network | N 个 Agent 自由互相喊话，没有固定主从 |
| Hierarchical | 多层主从，第一层 Supervisor 把任务交给第二层 Supervisor 再下放 |
| 同质 fork（本项目） | 1 个主 AgentLoop + 按需 fork 同质子 AgentLoop |

### 3.2 Supervisor-Workers 的硬伤

这是最广为传播的多 Agent 架构。表面上很合理：每个 Worker 专精一件事。

但放到 HarmonyDev 上立刻暴露问题：

**问题 1：worker 的边界要硬编码**

```
DocAgent:    工具集 = [doc_search]
CompatAgent: 工具集 = [solution_compare, compat_check]
PickerAgent: 工具集 = [patch_picker, dev_summary]
```

那 APIInsight 该归谁？WebSearch 该归谁？Planner 该归谁？每加一类需求就要重新切边界。

**问题 2：Supervisor 不知道 Worker 拿到了什么细节**

Supervisor 只能看到 Worker 的"最终回报字符串"。如果 CompatAgent 算出 80 件候选都超版本约束，Supervisor 没法立刻让 DocAgent 调一个更宽的 query——它得重新 dispatch 一次 DocAgent，重复整个对话。

**问题 3：每个 Worker 都要单独维护一份 prompt**

```
DocAgent    system prompt: 800 字
CompatAgent system prompt: 600 字
PickerAgent system prompt: 700 字
共 3 份 prompt，每次升级都要同步改 3 处
```

HarmonyDev 改一次"fork 三件事判断"的措辞，Supervisor-Workers 架构下要改 3-4 个 worker 的 prompt；同质 fork 架构只改 1 份。

### 3.3 Network（自由对话）的硬伤

Network 架构里没有固定主从，多个 Agent 互相 @。优点是灵活、能涌现。

放到开发场景里：

| 表面优势 | 实际表现 |
| --- | --- |
| 涌现式协作 | 在一个目标明确的开发任务上，"涌现"等于"发散" |
| 灵活性高 | 没人决定何时收敛，多 Agent 互相吹来吹去 |
| 适合开放讨论 | 开发 query 不是开放讨论，是"给我建议列表" |

更现实的问题是 **token 爆炸**：每个 Agent 都要看其他 Agent 的发言，N 个 Agent 互相喊话上下文是 N² 增长。HarmonyDev 4 路并行、每路 20 件API/代码片段 ×100 字 ≈ 8000 token——Network 架构下每个 Agent 都要扛这 8000 token，4 个 Agent 一起 32000 token 起步。

### 3.4 Hierarchical 多层主从的硬伤

Hierarchical 在某些复杂任务上有合理性（如"先大公司团队级分配，再小组级分配"）。但开发场景：

| 维度 | Hierarchical 的问题 |
| --- | --- |
| 决策权下沉 | 开发者画像"不要使用废弃 API"，是该第一层还是第二层 Supervisor 应用？ |
| 层级越深越僵 | 每多一层就多一次 LLM 调用 + 一次上下文打包 |
| 错误定位困难 | bad case 出在哪一层？要查一长串 trace |

它适合"组织结构复杂、子任务种类很多"的场景。HarmonyDev 任务种类就 9 个工具，硬塞两层 Supervisor 是过度设计。

### 3.5 同质 fork 为什么"刚刚好"

回头看同质 fork 在前面三种架构的问题上各自给出的答案：

| 上面三种架构的问题 | 同质 fork 的答案 |
| --- | --- |
| Worker 边界要硬编码 | 没有 Worker，子 = 主的克隆，能力边界一样 |
| Supervisor 看不到 Worker 细节 | 子做完返回"提炼字符串"，主可以看 task_tool 的返回值 |
| 每个 Worker 单独维护 prompt | 全系统 1 份 system prompt + 1 份工具集 |
| Network 容易发散 / token 爆炸 | 子任务一旦完成立即收尾，不会"互相喊话" |
| Hierarchical 决策权下沉 | 决策权始终在主 loop，子只是"代理执行" |
| 任务种类多带来层级膨胀 | 没有层级，要不要 fork 是动态决定的（三件事判断） |

**同质 fork 的核心 idea**：

> 子任务和主任务是同一种思考——只是范围更小、上下文更隔离。 
> 既然是同一种思考，那子 Agent 就该用同一份 prompt、同一个 LLM、同一份工具集。 
> "fork 一份自己"远比"维护一组异构 Worker"更低成本也更稳。

### 3.6 同质 fork 的"边界"

为了客观，同质 fork **不是万能的**。它在两类场景下不够用：

| 场景 | 更合适的架构 |
| --- | --- |
| 子任务需要完全不同的模型（如代码 Agent 需要 codellama） | Supervisor + 异构 Worker |
| 子任务需要完全不同的工具集（如安全审查需要禁用网络） | Supervisor + 异构 Worker |
| 子任务彼此需要持续对话、协商（如团队 brainstorm） | Network |

HarmonyDev 不在这三类里——它的子任务始终是"在某个平台 / 某个API 能力下做一段相同形态的检索 / 决策"，所以同质 fork 是匹配的。

---

## 4、用一条 query 跑三遍：直观对比

用 HarmonyDev 那条经典 query：

```
想实现一套ArkUI 页面状态恢复方案，目标 HarmonyOS 5.0，最好不要使用废弃 API，喜欢贴合项目现有代码风格。
```

### 4.1 PAE 视角

```
Planner: 列 plan（7 步）→ 执行 → 中途遇到 大量废弃写法仍然按 plan 跑 → 最后建议列表里废弃写法占多数 → 用户不满意 → re-plan → token 翻倍
```

### 4.2 Supervisor + 异构 Worker 视角

```
Supervisor: dispatch DocAgent
DocAgent: 调 doc_search ×4，回报 4 段候选（合并字符串很大）
Supervisor: dispatch CompatAgent
CompatAgent: 方案对比 + 做兼容性检查，回报 Top-12
Supervisor: dispatch PickerAgent（但发现 PickerAgent 的 prompt 不知道开发者画像"不要使用废弃 API"，因为偏好是 Supervisor 注入的）
Supervisor: 改 dispatch 时把偏好塞进 message 里
PickerAgent: 筛选
Supervisor: 汇总输出
```

每一次 dispatch 都要重新打包上下文，且 worker prompt 维护点多。

### 4.3 同质 fork 视角（HarmonyDev 选）

```
主 loop Think 1: 缺Kit 能力常识 → api_insight
主 loop Think 2: 4 路并行 → task_tool ×4 fork 同质子（每个子用主的同一套 prompt + 工具集）
4 个子 loop 各自完成 doc_search → 回报字符串
主 loop Think 3: 方案对比 → solution_compare
主 loop Think 4: 做兼容性检查 → compat_check
主 loop Think 5: 偏好（来自 system prompt 注入的 Store）+ 筛选 → patch_picker
主 loop Think 6: 收尾 → dev_summary
```

只有 1 份 prompt、1 个工具集。子 Agent 的能力和主完全一致，因此可以放心地让它内部"自主决策"——比如某个子 Agent 在 harmony_docs 看到都是废弃写法，它能自己再调一次 api_insight 调整搜索词。

---

## 5、把这两个选型和后面章节关联起来

这一章给的两个结论会在后面章节被反复印证：

| 后续章节 | 印证哪一点 |
| --- | --- |
| 第 5 章 Cache Breakpoint | AgentLoop 多轮 Think 不爆 token / 不掉缓存的工程兜底 |
| 第 6 章 长期记忆 Store | 每一轮 Think 都能拿到开发者画像，PAE 做不到这一点 |
| 第 7 章 AGUI 事件协议 | fork 事件让用户看见"子 Agent 在执行任务"，是同质 fork 的天然展示 |
| 第 11 章 DocSearch + 多源 fork | 同质 fork 第一次真正在工程里跑起来 |
| 第 14 章 防 fork 失控四件套 | 同质 fork 也有代价——把代价工程化兜住 |

---

## 6、选型时的三个常见反问

最后给三个面试 / 评审里高频出现的反问，预先想清楚。

**反问 1：AgentLoop 每轮调 LLM，是不是太贵了？**

> 是更贵，但 Cache Breakpoint + KV cache 命中率优化能压下来 50%+ token 成本。比起 PAE re-plan 时整个 plan 重新生成，AgentLoop 的边际成本更可控。

**反问 2：同质子 Agent 都是主的克隆，那它能力上和主一样，不就是"主自己干"吗？为什么还要 fork？**

> 因为 fork 不是为了"得到一个更强的子"，而是为了"上下文隔离 + 并行 + 子任务能自主多轮决策"。三件事判断（第 3 章）就是用来判断哪些子任务值得 fork 的。

**反问 3：异构 Worker 的好处是"专精"，难道你不要专精吗？**

> HarmonyDev 的"专精"放在工具层，不在 Agent 层。9 个工具就是 9 种专精能力（Planner / DocSearch / SolutionCompare / ...）。把专精堆在工具上比堆在 Worker 上更可组合——任何一个 Agent（主或子）都能调任何一个工具。

---

**本章小结：**

到这里，你应该能用一段话讲清楚 HarmonyDev 的两个核心选型：

- **AgentLoop > PAE**：鸿蒙开发的子目标是"边走边长"的，每一轮 Think 都需要基于当前所有 Observation + 开发者画像重新决策；PAE 的 plan 一定下来就难反悔，re-plan 的代价比 AgentLoop 一轮 Think 更高。

- **同质 fork > 异构 Worker / Network / Hierarchical**：子任务和主任务是同一种思考，只是范围更窄、上下文更隔离；用同一份 prompt + 同一份工具集 fork 一份自己，比维护一组异构 Worker 更低成本也更稳。

- 两个选型背后是同一个理由：**子任务的形状不是开局就能列完的，而是边走边长出来的。**

下一章「[LLM 三塔召回与工程语义双通道](<07-04-0 鸿蒙开发助手三塔召回与工程语义.md>)」会进入第 4 章，把"想要项目现有代码风格""不要使用废弃 API"这种语义和个性化偏好怎么真的搜得准——给 DocSearch 这一段配上检索能力的发动机。
