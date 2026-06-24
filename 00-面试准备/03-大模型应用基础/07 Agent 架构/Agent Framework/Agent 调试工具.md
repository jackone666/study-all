## **LangSmith 的 Trace 分析与 Agent 调试最佳实践**

#### 1、基础题：LangSmith 的 Trace 是什么？

**难度级别**：⭐（考察要点：Trace 树形结构、Run/Span 概念、可观测性）

LangSmith 是专为 LLM 应用设计的可观测性平台。一次 Agent 运行对应一个根 Trace，下面挂着多个 Run（Span）。树形结构从上到下是：Chain Run → LLM Run（记录完整 Prompt 和 Response）/ Tool Run（记录输入参数和返回结果）。每个 LLM Run 会记录 messages 列表、模型参数、Token 消耗、延迟和错误信息，解决了 LLM 应用执行过程"黑盒"难以定位问题的痛点。

---

#### 2、进阶题：如何用 LangSmith 定位 Agent 运行中的问题，并利用它做 Prompt 版本优化和成本分析？

**难度级别**：⭐⭐（考察要点：Trace 树形模型、问题定位步骤、Dataset 评估流程、Token 成本分析指标）

**1️⃣ Common Answer**

LangSmith 可以看到每次运行的日志，哪步出错了可以点进去看。可以创建数据集来比较不同 Prompt 的效果，也可以看 Token 消耗来控制成本。

**2️⃣ Impressive Answer**

我会从 3 个角度来说：

1. **首先说问题定位的实战流程**。排查流程是：先看根 Trace 状态，如果是 Error 直接看错误堆栈确定哪个 Run 失败了；展开失败的 LLM Run，查看实际发送给模型的完整 Prompt，很多时候问题出在上下文拼接错误或 Tool 返回格式不对，导致后续 LLM 收到了"脏数据"；对比相邻几次 Run 的 Prompt 差异，找出状态变化节点。举个真实案例：Agent 无限循环调用同一工具，在 LangSmith 里可以清晰看到 Tool Run 和 LLM Run 的交替次数，以及每次 LLM 的 reasoning，发现是工具错误信息没被正确处理，LLM 误判任务未完成。

2. **其次说 Prompt 版本对比**。LangSmith 的 Dataset 功能可以把历史 Trace 里的输入输出对存为评估集，对不同版本 Prompt 跑同一批数据，在 Experiments 面板直观对比结果。配合 `evaluate()` API 加自定义评估函数（用 LLM-as-Judge 打分），形成半自动的 Prompt 迭代流程，避免"感觉改好了"的主观判断。

3. **最后说成本分析**。重点关注两个指标：单次 Agent 运行的平均 Token 数（判断 Prompt 是否过长）和 Tool 调用次数（调用过多往往意味着规划效率低）。发现异常后结合 Trace 定位具体哪个节点在"浪费" Token。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 停留在"可以看日志"层面 | 描述了 Trace 树形数据模型和每个 Run 记录的具体字段 |
| 实践经验 | 无具体排查流程 | 给出完整定位步骤和真实的无限循环排查案例 |
| 思考维度 | 把 LangSmith 当查日志工具 | 理解其在 Prompt 迭代和成本优化中的工程价值 |
| 给面试官的印象 | 知道这个工具但没深入用过 | 有完整的 LLM 应用可观测性实践经验 |

---

#### 3、场景题：Agent 在生产环境偶发性输出异常，如何用 LangSmith 系统性排查？

**难度级别**：⭐⭐（考察要点：过滤异常 Trace、Prompt 回溯分析、Dataset 构建与回归测试）

**1️⃣ Common Answer**

可以在 LangSmith 里过滤出出错的 Trace，看看哪步出了问题，然后修改 Prompt 再测试。

**2️⃣ Impressive Answer**

偶发性异常的排查核心是：把偶发问题变成可复现问题，再变成可量化问题。

具体步骤：先用 LangSmith 的过滤器筛选出状态为 Error 或特定时间段的异常 Trace，找出共同特征（比如特定类型的用户输入、特定工具调用后触发）；把触发异常的输入收集到 Dataset 里，作为回归测试集；修改 Prompt 或逻辑后，用 `evaluate()` 跑整个 Dataset，用 LLM-as-Judge 打分，量化修复效果，避免"修好了一个、搞坏了另一个"的问题。这样把一次性排查变成持续质量保障的闭环。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 看日志改 Prompt | 给出系统性排查流程：定位→归因→构建 Dataset→量化验证 |
| 实践经验 | 无闭环思路 | 把偶发问题转化为可量化的回归测试，形成质量保障闭环 |
| 思考维度 | 被动修 bug | 主动建立持续监控和验证机制 |
| 给面试官的印象 | 会基本操作 | 有生产环境 LLM 应用质量保障的完整经验 |

---

#### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| LLM-as-Judge 的评估方法是什么？ | LangSmith 自定义评估函数的核心技术，决定 Prompt 实验的评判质量 |
| Agent 的 Token 成本如何优化？ | LangSmith 是发现 Token 浪费节点的关键工具 |
| OpenTelemetry 和 LangSmith 有什么区别？ | 通用可观测性 vs LLM 专用可观测性，帮助理解 LangSmith 的定位 |

## Agent 健壮性与高级优化

### DSPy 的自动化 Prompt 优化原理

---

#### 1、基础题：DSPy 解决了什么问题？

**难度级别**：⭐（考察要点：手动 Prompt 工程的痛点、自动化优化的核心思路）

传统 Prompt 工程本质上是"手动梯度下降"，每次模型版本更新或任务变化都要人工重新调整 Prompt，既费时又不可复现。DSPy 把 LLM 程序变成可编译、可优化的模块化系统，用优化器自动搜索最优的 Prompt 配置，将 Prompt 工程从手工艺变成可量化、可迭代的工程实践。

---

#### 2、进阶题：DSPy 的 Signature、Module、Optimizer 三个核心概念是什么，BootstrapFewShot 和 MIPRO 的工作原理有何不同？

**难度级别**：⭐⭐⭐（考察要点：Signature 声明 IO 契约、Module 组合多个 Predict/CoT、BootstrapFewShot 自举 few-shot、MIPRO 贝叶斯搜索 instruction）

**1️⃣ Common Answer**

Signature 定义输入输出类型，Module 是把多个 LLM 调用组合在一起的模块，Optimizer 负责自动找最好的 Prompt。BootstrapFewShot 会从训练数据里自动生成 few-shot 示例，MIPRO 用更复杂的算法优化 Prompt。

**2️⃣ Impressive Answer**

我会从 3 个角度来回答：

1. **首先说 Signature 的核心设计理念**。Signature 是声明式的 IO 契约，你只描述"做什么"（输入是什么、输出是什么），不写具体 Prompt 措辞。实际的 Prompt 构造由 DSPy 在编译时自动完成，并且可以被优化器修改。这个设计的价值是把"程序逻辑"和"Prompt 表达"解耦，类比编程里分离接口和实现。

2. **其次说 Module 的组合能力**。Module 是 DSPy 中类比神经网络层的概念，内置 `dspy.Predict`（基础调用）、`dspy.ChainOfThought`（自动加入 reasoning 字段激活 CoT）、`dspy.ReAct`（内置 ReAct 循环）。可以把多个 Module 组合成复杂程序，比如 RAG Pipeline 里组合 Retrieve 和 ChainOfThought，整个 pipeline 作为一个整体被优化器优化。

3. **最后说两种 Optimizer 的原理差异**。BootstrapFewShot 是自举优化：让 Module 对训练集跑推理，把通过评估指标的样本收集起来作为 few-shot 示例注入 Prompt，本质是"让模型先试，把成功案例加回 Prompt"的迭代。实现简单、成本低，适合快速迭代。MIPRO（Multi-prompt Instruction PRoposal Optimizer）更进一步，不只优化 few-shot 示例，还会优化 Signature 的 instruction 部分（告诉 LLM 怎么做任务的措辞），用贝叶斯优化在 Prompt 空间搜索，比暴力搜索高效，适合对性能要求更高、可接受更多计算成本的场景。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 描述功能层面，未解释底层原理 | 解释了 BootstrapFewShot 的自举机制和 MIPRO 的贝叶斯搜索原理 |
| 实践经验 | 无代码示例和适用场景分析 | 分析了 DSPy 适用场景（有评估指标+有训练数据）和局限性 |
| 思考维度 | 将 DSPy 定位为"自动写 Prompt 的工具" | 理解"可编译 LLM 程序"的核心设计哲学，类比神经网络优化 |
| 给面试官的印象 | 知道 DSPy 存在但没深入研究 | 有深入原理理解，能判断在什么场景引入 DSPy |

---

#### 3、场景题：团队的 RAG 问答系统 Prompt 很难手动调优，考虑引入 DSPy，需要满足什么前提条件？

**难度级别**：⭐⭐⭐（考察要点：评估指标可量化、训练数据规模、优化计算成本、适用场景判断）

**1️⃣ Common Answer**

引入 DSPy 需要有训练数据，还要定义评估指标，然后让优化器自动跑就行。

**2️⃣ Impressive Answer**

引入 DSPy 有几个关键前提要先评估，不满足的话引入反而是浪费。

第一，**必须有可量化的评估指标**。DSPy 优化器靠指标函数判断哪个 Prompt 更好，如果你的任务是创意写作、开放对话这种难以量化的场景，DSPy 发挥不了作用。RAG 问答场景通常可以用 Answer Correctness、Faithfulness 等指标，配合 LLM-as-Judge 实现，这个条件满足。

第二，**需要一定规模的训练数据**。至少几十个有标注的问答对，用于 BootstrapFewShot 的自举和优化效果评估。如果数据太少，优化器的搜索空间不足，结果不可信。

第三，**要接受更高的优化计算成本**。优化过程需要多次调用 LLM（尤其是 MIPRO），成本比手动调 Prompt 高很多。如果任务是高频、对延迟敏感的实时接口，这个成本可能不可接受，换成离线批量优化后部署固定 Prompt 会更合适。满足这三个条件，引入 DSPy 的收益才能超过成本。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 给出引入步骤，无前提条件分析 | 从评估指标、数据规模、计算成本三个维度给出前提判断 |
| 实践经验 | 无局限性认知 | 明确指出 DSPy 不适合的场景（创意任务、无评估指标） |
| 思考维度 | "引入 = 更好" | 引入框架要先评估 ROI，成本不合适宁可不引入 |
| 给面试官的印象 | 知道 DSPy 能用 | 有完整的技术选型判断力，理解工具适用边界 |

---

#### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| LLM-as-Judge 的评估方法是什么？ | DSPy Optimizer 的评估函数通常基于 LLM-as-Judge，是 DSPy 能运转的前提 |
| Few-shot Prompting 的原理是什么？ | BootstrapFewShot 的优化目标就是自动找到最好的 few-shot 示例 |
| 贝叶斯优化在超参数搜索中的应用？ | MIPRO 使用贝叶斯优化搜索 Prompt 空间，理解贝叶斯优化原理有助于理解 MIPRO 的高效性 |

---

### 从零构建轻量级 Agent 的核心组件设计

---

#### 1、基础题：ReAct Agent 的核心循环逻辑是什么？

**难度级别**：⭐（考察要点：Thought-Action-Observation 循环、终止条件、工具注册）

ReAct Agent 的核心是一个循环：让 LLM 输出 Thought（思考过程）和 Action（调用哪个工具、传什么参数）；执行工具得到 Observation（结果）；把 Observation 加入对话历史，再次调用 LLM；重复直到 LLM 输出 Final Answer。工具用字典注册（key 是工具名，value 是函数），循环靠 `max_steps` 上限防止死循环。

---

#### 2、进阶题：如何不依赖任何框架从零实现一个 ReAct Agent，工具注册与动态调用如何设计，何时应该引入框架？

**难度级别**：⭐⭐⭐（考察要点：装饰器+字典的工具注册模式、Prompt 格式设计、输出解析、框架引入复杂度阈值）

**1️⃣ Common Answer**

从零实现 Agent 就是写一个循环，让 LLM 决定调哪个工具，执行完把结果给 LLM，一直到任务完成。工具用字典存起来，key 是工具名，value 是函数。复杂了再引入框架。

**2️⃣ Impressive Answer**

我会从 3 个角度来回答：

1. **首先说工具注册系统的设计**。用装饰器 + 字典的模式：定义一个全局 `_TOOL_REGISTRY` 字典，写一个 `@tool` 装饰器，被装饰的函数自动注册进去，存函数引用、description 和参数 schema。调用工具时从字典里取函数动态执行：`_TOOL_REGISTRY[tool_name]["function"](**tool_input)`。这个模式的优点是注册和调用完全解耦，新增工具只需加装饰器，主循环代码不需要改。

2. **其次说 ReAct 循环的关键工程细节**。Prompt 设计要引导 LLM 输出结构化的 `Thought / Action / Action Input` 格式；输出解析用正则匹配提取工具名和参数；`stop=["Observation:"]` 让 LLM 在该停的地方停，等我们填充工具结果再继续。边界情况要处理：JSON 解析失败、工具不存在、达到 max_steps 上限。这些边界情况不处理，Agent 在真实环境里必然频繁崩溃。

3. **最后说引入框架的判断标准**。当需求超出以下阈值时，自建的维护成本就超过了引入框架的学习成本：需要流式输出 Token、需要对话状态持久化、需要多 Agent 并发编排、需要 Trace 可观测性、需要复用工具生态。超过 2-3 个需求就该引入 LangChain/LangGraph。但如果是单一、高频、对延迟敏感的场景（内容审核、简单分类），保持自建轻量实现往往更好。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 描述思路但无可运行代码 | 给出装饰器注册系统和 ReAct 循环的完整设计，含边界处理 |
| 实践经验 | 未涉及输出解析、错误处理等工程细节 | 处理了 JSON 解析失败、工具不存在、max_steps 等边界情况 |
| 思考维度 | "复杂了就引入框架"的模糊判断 | 给出具体的复杂度阈值，量化引入框架的触发条件 |
| 给面试官的印象 | 理解 Agent 概念但未实际动手写过 | 从零实现过 Agent，理解框架底层机制，有清晰的技术选型判断力 |

---

#### 3、场景题：自建 Agent 在生产环境中遇到 LLM 输出格式不稳定导致解析失败，如何处理？

**难度级别**：⭐⭐⭐（考察要点：输出解析容错、structured output / function calling 的替代方案、降级策略）

**1️⃣ Common Answer**

可以在解析失败时让 LLM 重新输出，在 Prompt 里提示它按正确格式来，或者多试几次。

**2️⃣ Impressive Answer**

输出格式不稳定是自建 Agent 最常见的生产问题，有两个层次的解法。

第一，**从根本上用 Structured Output 代替 Prompt 约束格式**。OpenAI 的 `response_format={"type": "json_schema", ...}` 或者 Function Calling 机制，能在模型层保证输出格式，从根本上消除正则解析失败的问题。这是最推荐的方案，把工具调用的参数解析交给模型层保证，不依赖脆弱的正则匹配。

第二，**如果必须用文本解析，加好兜底逻辑**。解析失败时给 LLM 发一条修正消息"请按规定格式输出"，最多重试 2 次；连续失败后返回降级回复，而不是让调用方看到异常。同时把解析失败的原始输出记录下来，用于后续优化 Prompt 或 stop sequence 配置。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 靠 Prompt 约束格式 | 指出 Structured Output/Function Calling 是根本解法 |
| 实践经验 | 无降级策略 | 给出完整的容错链路：重试 → 降级 → 记录日志 |
| 思考维度 | 被动修复 | 主动用模型层能力消除解析不稳定的根本原因 |
| 给面试官的印象 | 知道基本处理方式 | 有生产环境 Agent 可靠性建设的完整经验 |

---

#### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| OpenAI Function Calling 和 ReAct Prompting 有什么区别？ | Function Calling 是解决自建 Agent 输出解析不稳定的根本方案，两者都是工具调用机制 |
| LangChain 的 Tool 系统底层是怎么工作的？ | 理解了自建工具注册系统，才能理解 LangChain Tool 帮你封装了什么 |
| 何时该自建 Agent 而不是用框架？ | 本题的核心判断，框架引入的复杂度阈值和选型原则 |
