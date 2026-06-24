# CrewAI

## CrewAI 工作流编排

### CrewAI 的角色 - 任务 - 流程设计模式

![image.png](07-Agent-架构-Agent-Framework-CrewAI-image-001.png)

#### 1、基础题：CrewAI 中的 Crew、Task、Agent 三者是什么关系？⭐⭐

**难度级别**：⭐⭐（Crew 是编排容器、Task 是工作单元、Agent 是执行者、一对多关系）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 职责分层
- 映射关系
- 执行流程
- Crew：编排容器，负责整体流程控制、任务调度、结果聚合
- Task：工作单元，有明确的描述、预期输出、所属 Agent
- Agent：执行者，有角色设定、目标、工具集、LLM 配置

**2️⃣ Impressive Answer**

三者的关系可以从**职责分层**和**映射关系**两个维度理解：

1. **职责分层**

  - **Crew**：编排容器，负责整体流程控制、任务调度、结果聚合

  - **Task**：工作单元，有明确的描述、预期输出、所属 Agent

  - **Agent**：执行者，有角色设定、目标、工具集、LLM 配置

1. **映射关系**

  - 一个 Crew 包含多个 Task（有序或无序列表）

  - 一个 Task 只能分配给一个 Agent（一对一）

  - 一个 Agent 可以执行多个 Task（一对多）

1. **执行流程**

  - Crew 启动后，按 Task 定义的顺序（或并行策略）依次触发

  - 每个 Task 执行时，所属 Agent 用自己的工具集和 LLM 完成目标

  - Task 的输出作为上下文传递给后续 Task（上下文链）

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
结构性
</td>
<td>
只说&quot;包含关系&quot;，无职责区分
</td>
<td>
从职责分层 + 映射关系两维说明
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不了解上下文链传递机制
</td>
<td>
明确 Task 输出作为后续上下文
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道基本概念，但关系模糊
</td>
<td>
清晰理解三者的设计意图和协作方式
</td>
</tr>
</table>

---

#### 2、进阶题：CrewAI 的 Process 有 Sequential 和 Hierarchical 两种，有什么区别？⭐⭐⭐

**难度级别**：⭐⭐⭐（流程模式选择、任务依赖管理、适用场景）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Sequential（顺序流程）
- Hierarchical（层级流程）
- 选型建议
- 任务按定义顺序依次执行，前一个任务的输出自动注入下一个任务的上下文
- 所有 Agent 平级，没有协调者，适合线性工作流（如：调研→写作→审核）
- 优点：简单可控，调试方便；缺点：无法处理动态分支和循环

**2️⃣ Impressive Answer**

两种 Process 的核心区别在**任务调度策略**和**Agent 协作模式**：

1. **Sequential（顺序流程）**

  - 任务按定义顺序依次执行，前一个任务的输出自动注入下一个任务的上下文

  - 所有 Agent 平级，没有协调者，适合线性工作流（如：调研→写作→审核）

  - 优点：简单可控，调试方便；缺点：无法处理动态分支和循环

1. **Hierarchical（层级流程）**

  - 有一个 Manager Agent 作为协调者，负责任务分配和结果聚合

  - Worker Agent 向 Manager 汇报，Manager 可以动态决定下一步

  - 适合复杂场景：任务之间有依赖、需要条件分支、可能迭代返工

  - 优点：灵活性高；缺点：Manager 是单点瓶颈，调试复杂

1. **选型建议**

  - 流程固定、无分支：选 Sequential

  - 需要动态决策、多轮迭代：选 Hierarchical

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
结构性
</td>
<td>
只说了字面意思，无实质区别
</td>
<td>
从调度策略、协作模式、优缺点对比
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不了解上下文注入和 Manager 角色
</td>
<td>
明确 Sequential 上下文链、Hierarchical Manager 协调
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无选型建议
</td>
<td>
给出清晰的场景匹配原则
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
概念模糊
</td>
<td>
有实际使用经验，能指导选型
</td>
</tr>
</table>

---

#### 3、场景题：用 CrewAI 实现一个"市场调研报告生成"流程，如何设计 Task 依赖和上下文传递？⭐⭐⭐

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 任务拆解（4 个 Task）
- 依赖定义
- 上下文注入
- Task1（市场数据收集）：搜索竞品官网、行业报告、社交媒体，输出原始数据汇总
- Task2（数据清洗与分析）：提取关键指标（价格、功能、用户评价），输出结构化分析表
- Task3（趋势洞察）：基于分析表，识别市场空白和机会点，输出洞察结论

**2️⃣ Impressive Answer**

设计思路从**任务拆解、依赖定义、上下文注入**三步展开：

1. **任务拆解（4 个 Task）**

  - Task1（市场数据收集）：搜索竞品官网、行业报告、社交媒体，输出原始数据汇总

  - Task2（数据清洗与分析）：提取关键指标（价格、功能、用户评价），输出结构化分析表

  - Task3（趋势洞察）：基于分析表，识别市场空白和机会点，输出洞察结论

  - Task4（报告撰写）：整合以上所有输出，生成完整的 Markdown 报告

1. **依赖定义**

  - Task2 依赖 Task1 的输出（context=[task1]）

  - Task3 依赖 Task2 的输出（context=[task2]）

  - Task4 依赖 Task2 和 Task3 的输出（context=[task2, task3]）

1. **上下文注入**

  - CrewAI 中 Task 的 `context` 参数接收 Task 列表，自动将这些 Task 的输出拼接后注入当前任务的 expected_output 描述中

  - 注意上下文长度限制，如果前置 Task 输出过长，需要在 Task 描述中明确要求"输出精简摘要"

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
结构性
</td>
<td>
只说&quot;传给下一个&quot;，无具体设计
</td>
<td>
4 步任务拆解 + 依赖定义 + 上下文注入
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不了解 context 参数用法
</td>
<td>
明确 context 接收 Task 列表，自动拼接注入
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无上下文长度意识
</td>
<td>
提到输出过长需精简摘要
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
有基本概念，但设计不完整
</td>
<td>
有完整的设计思路和实践细节
</td>
</tr>
</table>

---

#### 4、进阶题：CrewAI 的 Memory 机制（短期记忆、长期记忆、实体记忆）如何工作？对多轮任务执行有什么影响？⭐⭐⭐

**难度级别**：⭐⭐⭐（Memory 机制、多轮任务、上下文传递）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 短期记忆
- 长期记忆
- 实体记忆
- 基于 Token 窗口的上下文记忆，在单次 Crew 执行过程中维护
- 使用 RAGCallbackHandler 捕获每个 Task 的输入输出，存储在内存中
- 后续 Task 可通过 memory.read() 获取历史上下文，自动注入到 Prompt 中

**2️⃣ Impressive Answer**

CrewAI 的 Memory 机制是支持多 Agent 协作和多轮任务执行的核心能力，通过三种类型的记忆实现不同层次的信息持久化和复用。

1. **短期记忆**

  - 基于 Token 窗口的上下文记忆，在单次 Crew 执行过程中维护

  - 使用 `RAGCallbackHandler` 捕获每个 Task 的输入输出，存储在内存中

  - 后续 Task 可通过 `memory.read()` 获取历史上下文，自动注入到 Prompt 中

  - 适用于单次会话内的任务依赖，如 Task A 的输出作为 Task B 的输入

1. **长期记忆**

  - 基于 Vector Database 的持久化存储（支持 Chroma、Pinecone、Redis Vector）

  - 使用 Embedding 模型将 Task 结果向量化存储，支持语义检索

  - 通过 `LongTermMemory` 类实现，跨 Crew 执行会话共享历史经验

  - 典型应用场景：代码审查 Agent 记住之前发现的模式，市场调研 Agent 积累行业知识

1. **实体记忆**

  - 基于 NER（命名实体识别）的结构化记忆，提取关键实体（人名、公司名、技术术语）

  - 使用 `EntityMemory` 类维护实体关系图谱，支持实体消歧和关联查询

  - 通过 `EntityExtractor` 从对话中提取实体，存储为 JSON 格式

  - 实际案例：客服 Agent 记住用户偏好、产品 Agent 维护产品知识图谱

**对多轮任务执行的影响：**

```python
from crewai import Agent, Task, Crew, Process
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory

# 配置三种记忆
memory_config = {
    "short_term": ShortTermMemory(),
    "long_term": LongTermMemory(
        storage_backend="chroma",
        embedding_model="text-embedding-3-small"
    ),
    "entity": EntityMemory(
        entity_extractor="openai",
        enable_entity_graph=True
    )
}

# 创建带记忆的 Agent
researcher = Agent(
    role="研究员",
    goal="收集并分析市场数据",
    memory=memory_config  # 绑定记忆配置
)

# Task 依赖记忆
task1 = Task(
    description="收集 2024 年 AI 市场数据",
    expected_output="JSON 格式的市场数据"
)

task2 = Task(
    description="基于 task1 的数据，分析增长趋势",
    context=[task1],  # 明确依赖关系
    expected_output="趋势分析报告"
)

crew = Crew(
    agents=[researcher],
    tasks=[task1, task2],
    process=Process.sequential,
    memory=True  # 启用记忆
)
```

**关键影响：**

- **上下文传递**：Task 间自动传递历史信息，减少重复输入

- **知识积累**：长期记忆让 Agent 越用越聪明，积累领域知识

- **一致性保证**：实体记忆确保多轮对话中实体指代一致

- **性能权衡**：记忆占用 Token 空间，需设置 `max_token_limit` 控制成本

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
结构性
</td>
<td>
随意罗列三种记忆，无逻辑层次
</td>
<td>
按记忆类型分层讲解，每类包含机制、实现、场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
仅描述功能，无技术细节
</td>
<td>
涉及 RAG、Vector DB、NER、Embedding 等核心技术
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
泛泛而谈&quot;要注意控制性能&quot;
</td>
<td>
提供完整代码示例，说明配置参数和实际应用场景
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
候选人了解概念但缺乏深入理解
</td>
<td>
候选人有扎实的工程实践能力，能落地复杂功能
</td>
</tr>
</table>

---

#### 5、进阶题：CrewAI 中如何自定义 Tool 并绑定给特定 Agent？Tool 的错误处理机制是怎样的？⭐⭐⭐

**难度级别**：⭐⭐⭐（Tool 自定义、Agent 绑定、错误处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 自定义 Tool 的实现方式
- Tool 绑定给特定 Agent
- Tool 的错误处理机制
- Tool 内部捕获可预期的错误（网络超时��API 限流），返回友好提示
- 抛出 ToolExecutionError 让 Agent 感知工具失败
- 设置合理的 max_execution_time 和 max_iter 避免无限重试

**2️⃣ Impressive Answer**

CrewAI 的 Tool 机制是 Agent 扩展能力的核心，通过自定义 Tool 可以让 Agent 调用外部 API、数据库、本地服务等。Tool 的正确实现和错误处理直接影响 Agent 的稳定性。

1. **自定义 Tool 的实现方式**

CrewAI 提供两种自定义 Tool 的方式：

**方式一：继承 **`BaseTool` 类（推荐用于复杂场景）

```python
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests

class DatabaseSearchInput(BaseModel):
    """数据库搜索工具的输入参数"""
    query: str = Field(description="搜索查询语句")
    limit: int = Field(default=10, description="返回结果数量限制")

class DatabaseSearchTool(BaseTool):
    name: str = "database_search"
    description: str = "用于搜索数据库中的数据"
    args_schema: Type[BaseModel] = DatabaseSearchInput

    def _run(self, query: str, limit: int = 10) -> str:
        """同步执行数据库搜索"""
        try:
            results = self._execute_query(query, limit)
            return f"查询成功，找到 {len(results)} 条记录"
        except Exception as e:
            return f"查询失败：{str(e)}"

    async def _arun(self, query: str, limit: int = 10) -> str:
        """异步执行（可选）"""
        return self._run(query, limit)

    def _execute_query(self, query: str, limit: int) -> list:
        # 实际的数据库查询实现
        pass
```

**方式二：使用 **`@tool` 装饰器（推荐用于简单场景）

```python
from crewai.tools import tool

@tool("weather_search")
def weather_search(location: str) -> str:
    """搜索指定位置的天气信息"""
    try:
        response = requests.get(
            f"https://api.weather.com/v1/current?location={location}"
        )
        data = response.json()
        return f"{location} 当前温度：{data['temp']}°C"
    except requests.RequestException as e:
        raise ToolExecutionError(f"天气 API 调用失败：{str(e)}")
```

1. **Tool 绑定给特定 Agent**

```python
from crewai import Agent, Task, Crew

# 创建自定义 Tool 实例
db_tool = DatabaseSearchTool()
weather_tool = weather_search

# 绑定给不同的 Agent
data_analyst = Agent(
    role="数据分析师",
    goal="分析数据库中的业务数据",
    backstory="你擅长 SQL 查询和数据分析",
    tools=[db_tool],  # 只绑定数据库工具
    verbose=True
)

market_researcher = Agent(
    role="市场研究员",
    goal="收集市场信息和天气数据",
    backstory="你擅长市场调研和数据分析",
    tools=[db_tool, weather_tool],  # 绑定多个工具
    verbose=True
)

# Task 中 Agent 只能调用自己绑定的 Tool
task1 = Task(
    description="查询最近一个月的销售额数据",
    agent=data_analyst  # 只能使用 db_tool
)

task2 = Task(
    description="结合天气数据分析销售趋势",
    agent=market_researcher  # 可以使用 db_tool 和 weather_tool
)
```

1. **Tool 的错误处理机制**

CrewAI 提供多层错误处理机制：

**第一层：Tool 内部错误处理**

```python
from crewai.tools import ToolExecutionError

class RobustDatabaseTool(BaseTool):
    def _run(self, query: str) -> str:
        try:
            results = self._execute_query(query)
            return self._format_results(results)
        except ConnectionError:
            # 连接错误，返回友好提示
            return "数据库连接失败，请检查网络"
        except QuerySyntaxError:
            # SQL 语法错误，返回具体建议
            return f"SQL 语法错误：{str(e)}，建议检查查询语句"
        except Exception as e:
            # 未知错误，抛出给上层处理
            raise ToolExecutionError(f"工具执行失败：{str(e)}")
```

**第二层：Agent 级别的错误处理**

```python
resilient_agent = Agent(
    role="容错 Agent",
    goal="即使工具失败也能完成任务",
    tools=[db_tool],
    max_execution_time=60,  # 最大执行时间
    max_iter=5,  # 最大重试次数
    allow_delegation=False  # 禁止委托，避免错误传播
)
```

**第三层：Crew 级别的错误处理**

```python
from crewai import Crew, Process

crew = Crew(
    agents=[data_analyst, market_researcher],
    tasks=[task1, task2],
    process=Process.sequential,
    verbose=True,
    # 错误处理配置
    step_callback=lambda x: print(f"Step completed: {x}"),
    memory=True
)

# 执行时捕获错误
try:
    result = crew.kickoff()
except Exception as e:
    print(f"Crew 执行失败：{str(e)}")
    # 错误恢复逻辑
```

**最佳实践：**

- Tool 内部捕获可预期的错误（网络超时��API 限流），返回友好提示

- 抛出 `ToolExecutionError` 让 Agent 感知工具失败

- 设置合理的 `max_execution_time` 和 `max_iter` 避免无限重试

- 使用 `verbose=True` 查看详细日志，便于调试

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
结构性
</td>
<td>
混乱描述，无代码示例
</td>
<td>
分层讲解：Tool 实现 → Agent 绑定 → 错误处理
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
仅提到继承和 try-except
</td>
<td>
涉及 Pydantic 验证、异步支持、多层错误处理机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
泛泛而谈&quot;有重试机制&quot;
</td>
<td>
提供完整可运行的代码示例，包含参数配置和最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
候选人了解基础用法
</td>
<td>
候选人有丰富的实战经验，能处理复杂工程问题
</td>
</tr>
</table>

---

#### 6、场景题：用 CrewAI 实现一个多 Agent 代码审查系统（代码分析 Agent、安全审查 Agent、性能审查 Agent、汇总 Agent），如何设计 Agent 角色、Task 依赖和输出格式？⭐⭐⭐⭐

**难度级别**：⭐⭐⭐⭐（多 Agent 协作、任务编排、系统设计）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Agent 角色设计
- Task 依赖关系设计
- Crew 配置和执行
- 输出格式标准化
- 代码质量：{quality_score}/100
- 安全性：{security_score}/100

**2️⃣ Impressive Answer**

设计多 Agent 代码审查系统需要考虑 Agent 角色分工、Task 依赖关系、输出格式标准化、错误处理等核心问题。以下是基于 CrewAI 的完整设计方案。

1. **Agent 角色设计**

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import ast
import re

# 工具：代码静态分析
@tool("code_analyzer")
def analyze_code_structure(code: str) -> str:
    """分析代码结构，返回函数、类、复杂度等信息"""
    try:
        tree = ast.parse(code)
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        complexity = len([node for node in ast.walk(tree) if isinstance(node, ast.If)])
        return f"函数数量：{len(functions)}，类数量：{len(classes)}，复杂度：{complexity}"
    except SyntaxError:
        return "代码语法错误"

# 工具：安全漏洞扫描
@tool("security_scanner")
def scan_security_issues(code: str) -> str:
    """扫描常见安全问题：SQL注入、XSS、硬编码密钥等"""
    issues = []
    if re.search(r"execute\([^)]*\+", code):
        issues.append("存在 SQL 注入风险")
    if re.search(r"(password|secret|api_key)\s*=\s*['\"][^'\"]+['\"]", code, re.IGNORECASE):
        issues.append("存在硬编码密钥")
    if "eval(" in code:
        issues.append("使用 eval() 存在安全风险")
    return "; ".join(issues) if issues else "未发现安全问题"

# Agent 1：代码质量分析师
code_quality_analyst = Agent(
    role="代码质量分析师",
    goal="评估代码的可读性、可维护性和规范性",
    backstory="""你是一位资深的代码审查专家，擅长识别代码质量问题。
    你关注命名规范、代码重复、复杂度、注释完整性等维度。
    你会给出具体的改进建议和示例代码。""",
    tools=[analyze_code_structure],
    verbose=True,
    max_execution_time=30
)

# Agent 2：安全审查专家
security_reviewer = Agent(
    role="安全审查专家",
    goal="识别代码中的安全漏洞和风险",
    backstory="""你是一位安全专家，熟悉 OWASP Top 10 安全漏洞。
    你能识别 SQL 注入、XSS、CSRF、硬编码密钥、不安全的加密等安全问题。
    你会给出修复方案和安全最佳实践建议。""",
    tools=[scan_security_issues],
    verbose=True,
    max_execution_time=30
)

# Agent 3：性能优化专家
performance_reviewer = Agent(
    role="性能优化专家",
    goal="分析代码的性能瓶颈和优化空间",
    backstory="""你是一位性能优化专家，熟悉常见的性能问题模式。
    你能识别循环嵌套、重复查询、内存泄漏、算法复杂度等问题。
    你会给出具体的优化建议和性能对比数据。""",
    verbose=True,
    max_execution_time=30
)

# Agent 4：审查结果汇总师
result_summarizer = Agent(
    role="审查结果汇总师",
    goal="整合三个维度的审查结果，生成综合报告",
    backstory="""你是一位技术文档专家，擅长将技术审查结果整理成清晰的报告。
    你会按照严重程度对问题进行分类，给出优先级建议。
    你会生成结构化的报告，包含问题描述、影响范围、修复建议。""",
    verbose=True,
    max_execution_time=20
)
```

1. **Task 依赖关系设计**

使用 Hierarchical Process 实现并行执行和结果汇总：

```python
# Task 1：代码质量审查（独立执行）
code_quality_task = Task(
    description="""
    分析以下代码的质量问题：
    {code}

    请从以下维度进行评估：
    1. 命名规范（变量、函数、类名是否语义化）
    2. 代码重复（是否有重复的逻辑可以抽取）
    3. 复杂度控制（函数长度、嵌套层次是否合理）
    4. 注释完整性（关键逻辑是否有注释）

    输出格式：JSON
    """,
    agent=code_quality_analyst,
    expected_output="JSON 格式的代码质量评估报告"
)

# Task 2：安全审查（独立执行）
security_task = Task(
    description="""
    审查以下代码的安全问题：
    {code}

    请检查以下安全风险：
    1. SQL 注入漏洞
    2. XSS 跨站脚本攻击
    3. 硬编码密钥或敏感信息
    4. 不安全的加密算法
    5. 未经验证的输入

    输出格式：JSON
    """,
    agent=security_reviewer,
    expected_output="JSON 格式的安全审查报告"
)

# Task 3：性能审查（独立执行）
performance_task = Task(
    description="""
    分析以下代码的性能问题：
    {code}

    请关注以下性能维度：
    1. 算法复杂度（时间复杂度、空间复杂度）
    2. 循环嵌套（是否存在不必要的嵌套）
    3. 数据库查询（是否存在 N+1 查询）
    4. 内存使用（是否存在内存泄漏风险）

    输出格式：JSON
    """,
    agent=performance_reviewer,
    expected_output="JSON 格式的性能分析报告"
)

# Task 4：结果汇总（依赖前三个 Task）
summary_task = Task(
    description="""
    整合以下三个维度的审查结果，生成综合报告：

    请按以下格式生成报告：

    # 代码审查综合报告

    ## 总体评分
    - 代码质量：{quality_score}/100
    - 安全性：{security_score}/100
    - 性能：{performance_score}/100

    ## 关键问题（按严重程度排序）

    ### 🔴 Critical（必须立即修复）
    ### 🟡 High（本周内修复）
    ### 🟢 Medium（下个迭代修复）

    ## 修复优先级建议
    """,
    agent=result_summarizer,
    context=[code_quality_task, security_task, performance_task],
    expected_output="Markdown 格式的综合审查报告"
)
```

1. **Crew 配置和执行**

```python
# 创建 Crew，使用 Hierarchical Process
code_review_crew = Crew(
    agents=[
        code_quality_analyst,
        security_reviewer,
        performance_reviewer,
        result_summarizer
    ],
    tasks=[
        code_quality_task,
        security_task,
        performance_task,
        summary_task
    ],
    process=Process.hierarchical,  # 层级式流程
    verbose=True,
    memory=True,  # 启用记忆，支持上下文传递
    manager_llm="gpt-4",  # Manager Agent 使用更强的模型
    planning=True  # 启用任务规划
)

# 执行代码审查
code_to_review = """
public class UserService {
    public User getUserById(String id) {
        String sql = "SELECT * FROM user WHERE id = " + id;
        return jdbcTemplate.queryForObject(sql, User.class);
    }

    public List<User> getAllUsers() {
        List<String> ids = getUserIds();
        for (String id : ids) {
            User user = getUserById(id);
            users.add(user);
        }
        return users;
    }
}
"""

# 启动审查
try:
    result = code_review_crew.kickoff(
        inputs={"code": code_to_review}
    )
    print("代码审查完成！")
    print(result)
except Exception as e:
    print(f"审查失败：{str(e)}")
```

1. **输出格式标准化**

定义统一的 JSON Schema 确保各 Agent 输出格式一致：

```python
from pydantic import BaseModel, Field
from typing import List

class CodeIssue(BaseModel):
    type: str = Field(description="问题类型")
    severity: str = Field(description="严重程度：critical/high/medium/low")
    description: str = Field(description="问题描述")
    suggestion: str = Field(description="修复建议")
    line: int = Field(description="代码行号")

class ReviewResult(BaseModel):
    score: int = Field(description="评分（0-100）")
    issues: List[CodeIssue] = Field(description="问题列表")
    positive_points: List[str] = Field(description="优点列表")
```

**关键设计要点：**

- **并行执行**：三个审查 Agent 并行工作，提高效率

- **标准化输出**：统一 JSON Schema，便于汇总处理

- **严重程度分级**：Critical/High/Medium/Low，明确优先级

- **上下文传递**：通过 `context` 参数传递前序 Task 结果

- **错误隔离**：单个 Agent 失败不影响其他 Agent 执行

- **可扩展性**：易于添加新的审查维度（如测试覆盖率 Agent）

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
结构性
</td>
<td>
简单罗列四个 Agent，无详细设计
</td>
<td>
完整的系统设计：Agent 角色 → Task 依赖 → 输出格式 → 执行流程
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
仅提到&quot;配置合适的 Prompt&quot;
</td>
<td>
提供完整代码实现，包含工具、Agent、Task、Crew 的详细配置
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
泛泛而谈&quot;并行执行、汇总结果&quot;
</td>
<td>
使用 Hierarchical Process、JSON Schema 验证、错误处理等工程实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
候选人了解基本概念
</td>
<td>
候选人有系统设计能力，能落地复杂多 Agent 系统
</td>
</tr>
</table>

### **CrewAI 的核心概念与角色驱动的任务编排**

#### **1、基础题：CrewAI 的四层结构分别是什么？**

**难度级别**：⭐（考察要点：Crew/Agent/Task/Process 各层职责）

CrewAI 由四层构成：Crew 是最顶层的团队容器，负责把 Agent、Task、Process 组合在一起；Agent 定义角色画像（role、goal、backstory）和可用工具；Task 定义具体工作单元（做什么、期望输出、由谁做）；Process 控制任务的执行策略，主要是 Sequential 和 Hierarchical 两种。

---

#### **2、进阶题：CrewAI 的 Sequential 和 Hierarchical 两种 Process 模式有什么区别，与 LangGraph 相比设计哲学有何不同？**

**难度级别**：⭐⭐（考察要点：Sequential 顺序流水线、Hierarchical Manager Agent 动态调度、声明式 vs 图式抽象层次对比）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 首先说两种 Process 模式的核心区别
- 其次说 CrewAI 的设计本质
- 最后说与 LangGraph 的抽象层次差异

**2️⃣ Impressive Answer**

我会从 3 个角度来回答：

1. **首先说两种 Process 模式的核心区别**。Sequential 严格按 Task 列表顺序执行，前一个任务的输出自动作为下一个任务的上下文，适合"数据收集 → 分析 → 报告"这种有明确依赖链的流水线场景，可预测性强。Hierarchical 则由框架自动创建一个 Manager Agent，基于当前状态动态决定调用哪个 Agent 执行哪个 Task，适合任务边界不清晰、需要动态调度的场景，但 Manager 的行为有不确定性。

1. **其次说 CrewAI 的设计本质**。Agent 里的 backstory 字段本质上是通过 System Prompt 让 LLM 进行角色扮演，让同一个底层模型表现出差异化的专业能力；Task 的 `expected_output` 约束了 LLM 的输出格式，减少后续解析的不确定性。理解这两点，才算真正理解 CrewAI 的设计意图。

1. **最后说与 LangGraph 的抽象层次差异**。CrewAI 是声明式、高抽象层，只需描述"有哪些角色、有哪些任务"，内部的 Prompt 构造和循环控制都由框架处理，上手快但灵活性受限。LangGraph 是图式、低抽象层，需要显式定义节点、边和条件路由，开发成本高但可以精确控制状态流转，更适合生产环境的关键业务。选型建议：多专家角色协作的明确任务用 CrewAI，需要精确状态管理和错误恢复的用 LangGraph。

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
停留在概念列举，无设计意图分析
</td>
<td>
解释了 backstory 的 Prompt 本质、expected_output 的约束作用
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无场景举例
</td>
<td>
给出了 Sequential 适合流水线、Hierarchical 适合动态调度的判断
</td>
</tr>
<tr>
<td>
思考维度
</td>
<td>
简化为&quot;简单 vs 复杂&quot;
</td>
<td>
从抽象层次（声明式 vs 图式）精准对比，给出选型建议
</td>
</tr>
<tr>
<td>
给面试官的印象
</td>
<td>
了解基本概念，没用过的感觉
</td>
<td>
有实际使用经验，理解框架设计取舍
</td>
</tr>
</table>

---

#### **3、场景题：在 CrewAI Hierarchical 模式下，Manager Agent 行为不可预测怎么处理？**

**难度级别**：⭐⭐（考察要点：backstory 和 Task description 约束、manager_llm 配置、生产环境稳定性）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Hierarchical 模式不可预测的根本原因是 Manager Agent 的决策完全依赖 LLM 推理，没有硬约束。有几个应对策略
- 第一，在每个 Agent 的 backstory 和每个 Task 的 description 里明确写清楚"什么条件下由谁处理"，把业务规则注入 Prompt，相当于给 Ma...
- 第二，为 Manager 单独配置更强的 manager_llm（比如 GPT-4o），它的规划能力决定整个协作质量。
- 第三，如果场景有明确的依赖顺序，优先选 Sequential，确实需要动态调度再用 Hierarchical。生产环境里，Hierarchical 更适合"探索性研究"类任务...

**2️⃣ Impressive Answer**

Hierarchical 模式不可预测的根本原因是 Manager Agent 的决策完全依赖 LLM 推理，没有硬约束。有几个应对策略：

第一，在每个 Agent 的 backstory 和每个 Task 的 description 里明确写清楚"什么条件下由谁处理"，把业务规则注入 Prompt，相当于给 Manager 写操作手册。

第二，为 Manager 单独配置更强的 `manager_llm`（比如 GPT-4o），它的规划能力决定整个协作质量。

第三，如果场景有明确的依赖顺序，优先选 Sequential，确实需要动态调度再用 Hierarchical。生产环境里，Hierarchical 更适合"探索性研究"类任务，而非关键业务流程。

**3️⃣ Key Differences**

<table>
<tr>
<td>
维度
</td>
<td>
Common Answer
</td>
<td>
Impressive Answer
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
只知道改描述或换模式
</td>
<td>
分析了不可预测的根本原因，给出针对性的多层解法
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体配置细节
</td>
<td>
提到 manager_llm 独立配置，区分了适用场景
</td>
</tr>
<tr>
<td>
思考维度
</td>
<td>
被动应对
</td>
<td>
从框架设计层理解问题，主动设计约束策略
</td>
</tr>
<tr>
<td>
给面试官的印象
</td>
<td>
会基本配置
</td>
<td>
有 CrewAI 生产踩坑经验
</td>
</tr>
</table>

---

#### **4、容易一起考的题**

<table>
<tr>
<td>
关联题
</td>
<td>
和本题的关系
</td>
<td>
参考答案
</td>
</tr>
<tr>
<td>
CrewAI vs LangGraph 如何选型？
</td>
<td>
两者抽象层次不同，是 CrewAI 定位理解的核心对比维度
</td>
<td>
答：选型看流程复杂度：CrewAI 更适合角色清晰、顺序协作的任务，配置简单；LangGraph 更适合有分支、循环、状态持久化和人工介入的复杂流程。面试里要补一句：简单协作用 CrewAI，复杂状态机用 LangGraph。
</td>
</tr>
<tr>
<td>
LLM 角色扮演（System Prompt）原理是什么？
</td>
<td>
backstory 本质是 System Prompt 注入，理解此原理才能写好 Agent 配置
</td>
<td>
答：角色扮演本质是通过 System Prompt/backstory 约束模型的目标、身份、边界和输出风格；写得好能提升一致性，风险是过度拟人或约束不清导致越权。
</td>
</tr>
<tr>
<td>
AutoGen 和 CrewAI 都是多 Agent 框架，区别在哪？
</td>
<td>
AutoGen 对话驱动、CrewAI 角色驱动，适用场景和设计哲学都不同
</td>
<td>
答：AutoGen 偏对话驱动，多个 Agent 通过消息协商推进；CrewAI 偏角色和任务驱动，用 Role、Task、Crew 编排流程。前者更灵活，后者更结构化。
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| CrewAI 的角色 - 任务 - 流程设计模式 | Crew：编排容器，负责整体流程控制、任务调度、结果聚合；Task：工作单元，有明确的描述、预期输出、所属 Agent；Agent：执行者，有角色设定、目标、工具集、LLM 配置；一个 Crew 包含多个 Task（有序或无序列表）；一个 Task 只能分配给一个 Agent（一对一）。 |
| CrewAI 中的 Crew、Task、Agent 三者是什么关系？ | Crew：编排容器，负责整体流程控制、任务调度、结果聚合；Task：工作单元，有明确的描述、预期输出、所属 Agent；Agent：执行者，有角色设定、目标、工具集、LLM 配置；一个 Crew 包含多个 Task（有序或无序列表）；一个 Task 只能分配给一个 Agent（一对一）。 |
| CrewAI 的 Process 有 Sequential 和 Hierarchical 两种，有什么区别？ | 任务按定义顺序依次执行，前一个任务的输出自动注入下一个任务的上下文；所有 Agent 平级，没有协调者，适合线性工作流（如：调研→写作→审核）；优点：简单可控，调试方便；缺点：无法处理动态分支和循环；有一个 Manager Agent 作为协调者，负责任务分配和结果聚合；Worker Agent 向 Manager 汇报，Manager 可以动态决定下一步。 |
| 用 CrewAI 实现一个"市场调研报告生成"流程，如何设计 Task 依赖和上下文传递？ | Task1（市场数据收集）：搜索竞品官网、行业报告、社交媒体，输出原始数据汇总；Task2（数据清洗与分析）：提取关键指标（价格、功能、用户评价），输出结构化分析表；Task3（趋势洞察）：基于分析表，识别市场空白和机会点，输出洞察结论；Task4（报告撰写）：整合以上所有输出，生成完整的 Markdown 报告；Task2 依赖 Task1 的输出（context=[task1]）。 |
| CrewAI 的 Memory 机制（短期记忆、长期记忆、实体记忆）如何工作？对多轮任务执行有什么影响？ | 基于 Token 窗口的上下文记忆，在单次 Crew 执行过程中维护；使用 RAGCallbackHandler 捕获每个 Task 的输入输出，存储在内存中；后续 Task 可通过 memory.read() 获取历史上下文，自动注入到 Prompt 中；适用于单次会话内的任务依赖，如 Task A 的输出作为 Task B 的输入；基于 Vector Database 的持久化存储（支持 Chroma、Pinecone、Redis Vector）。 |
| CrewAI 中如何自定义 Tool 并绑定给特定 Agent？Tool 的错误处理机制是怎样的？ | Tool 内部捕获可预期的错误（网络超时��API 限流），返回友好提示；抛出 ToolExecutionError 让 Agent 感知工具失败；设置合理的 max_execution_time 和 max_iter 避免无限重试；使用 verbose=True 查看详细日志，便于调试。 |
| 用 CrewAI 实现一个多 Agent 代码审查系统（代码分析 Agent、安全审查 Agent、性能审查 Agent、汇总 Agent），如何设计 Agent 角色、Task 依赖和输出格式？ | 代码质量：{quality_score}/100；安全性：{security_score}/100；性能：{performance_score}/100；并行执行：三个审查 Agent 并行工作，提高效率；标准化输出：统一 JSON Schema，便于汇总处理。 |
| CrewAI 的四层结构分别是什么？ | CrewAI 由四层构成：Crew 是最顶层的团队容器，负责把 Agent、Task、Process 组合在一起；Agent 定义角色画像（role、goal、backstory）和可用工具；Task 定义具体工作单元（做什么、期望输出、由谁做）；Process 控制任务的执行策略，主要是 Sequential 和 Hierarchical 两种。 |
| CrewAI 的 Sequential 和 Hierarchical 两种 Process 模式有什么区别，与 LangGraph 相比设计哲学有何不同？ | 首先说两种 Process 模式的核心区别：Sequential 严格按 Task 列表顺序执行，前一个任务的输出自动作为下一个任务的上下文，适合"数据收集 → 分析 → 报告"这种有明确依赖链的流水线场景，可预测性强。Hierarchical 则由框架自动创建一个 Manager Agent，基于当前状态动态决定调用哪个 Agent 执行哪个 Task，适合任务边界不清晰、需要动态调度的场景，但 Manager 的行为有不确定性；其次说 CrewAI 的设计本质：Agent 里的 backstory 字段本质上是通过 System Prompt 让 LLM 进行角色扮演，让同一个底层模型表现出差异化的专业能力；Task 的 expected_output 约束了 LLM 的输出格式，减少后续解析的不确定性。理解这两点，才算真正理解 CrewAI 的设计意图；最后说与 LangGraph 的抽象层次差异：CrewAI 是声明式、高抽象层，只需描述"有哪些角色、有哪些任务"，内部的 Prompt 构造和循环控制都由框架处理，上手快但灵活性受限。LangGraph 是图式、低抽象层，需要显式定义节点、边和条件路由，开发成本高但可以精确控制状态流转，更适合生产环境的关键业务。选型建议：多专家角色协作的明确任务用 CrewAI，需要精确状态管理和错误恢复的用 LangGraph。 |
| 在 CrewAI Hierarchical 模式下，Manager Agent 行为不可预测怎么处理？ | Hierarchical 模式不可预测的根本原因是 Manager Agent 的决策完全依赖 LLM 推理，没有硬约束。有几个应对策略：；第一，在每个 Agent 的 backstory 和每个 Task 的 description 里明确写清楚"什么条件下由谁处理"，把业务规则注入 Prompt，相当于给 Manager 写操作手册；第二，为 Manager 单独配置更强的 manager_llm（比如 GPT-4o），它的规划能力决定整个协作质量。 |
