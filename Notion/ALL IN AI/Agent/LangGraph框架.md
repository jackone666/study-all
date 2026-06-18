# 什么是LangGraph？

LangGraph 是 LangChain团队 发布的一个多智能体工作流框架。

![](LangGraph框架-image.png)

### LangGraph 的核心功能

* **持久执行：构建能够在失败后持续运行、长时间运行并从中断处恢复的代理。**

* **人机交互：通过在任何时候检查和修改代理状态，融入人工监督。**

* **综合记忆：** **创建具有短期工作记忆以进行持续推理和跨会话长时记忆的有状态代理。**

* **使用LangSmith调试：通过可视化工具深入了解复杂代理行为，追踪执行路径、捕获状态转移，并提供详细的运行时指标。**

* **简易部署：借助可扩展的基础架构，自信地部署复杂的代理系统，该基础架构旨在应对有状态、长时间运行的工作流所面临的独特挑战。**

# LangGraph和LangChain的区别

LangGraph和LangChain是两个相关但不同的工具，都来自LangChain生态系统。

## LangChain

LangChain是一个用于构建大语言模型应用程序的框架

* **线性工作流**：主要支持顺序执行的链式操作

* **组件库**：提供丰富的预构建组件，如提示模板、向量存储、检索器等

* **简单集成**：易于快速原型开发和简单的LLM应用

* **抽象层**：为不同的LLM提供统一接口

* **中间件：提供十多种预构建中间件和自定义中间件去进行Agent执行中的拦截**

## LangGraph

LangGraph是LangChain团队开发的更高级工具，专门用于构建复杂的多智能体系统：

* **图状工作流**：支持复杂的分支、循环和条件逻辑

* **状态管理**：内置强大的状态管理机制

* **多智能体协作**：原生支持多个AI智能体之间的交互

* **复杂决策流**：可以根据条件动态选择执行路径

* **持久化**：支持长时间运行的工作流和状态持久化

## 主要区别

**复杂性处理**：

* LangChain适合简单到中等复杂度的应用

* LangGraph专为复杂的多步骤、多智能体场景设计

**工作流结构**：

* LangChain主要是链式（Chain）结构

* LangGraph是图状（Graph）结构，支持任意的节点连接

![](LangGraph框架-mermaid-diagram-2026-04-12-143930.png)

# LangGraph安装

```python
 pip install -U "langgraph"
```

# LangGraph基础知识（核心概念）

## <span style="color: rgb(216,57,49); background-color: inherit">Graph（流程图）</span>

LangGraph 的核心是将代理工作流程建模为图表。您可以使用三个关键组件来定义代理的行为：

1. `State`：表示应用程序当前快照的共享数据结构。它可以是任何 Python 类型，但通常是 `TypedDict`或 Pydantic `BaseModel`。

2. `Nodes`：用于编码代理逻辑的 Python 函数。它们接收当前值`State`作为输入，执行一些计算，并返回更新后的`State`。

3. `Edges`：根据当前条件确定下一步执行哪个操作的 Python 函数`State`。它们可以是条件分支或固定转换。

通过组合`Nodes`和`Edges`，您可以创建复杂的循环工作流，使其`State`随时间推移而演化。然而，真正的强大之处在于 LangGraph 对 的管理方式`State`。需要强调的是：`Nodes`和`Edges`只不过是 Python 函数而已——它们可以包含 LLM 代码，也可以只是经典的 Python 代码。

简而言之：节点负责工作，边负责告诉下一步做什么。

![](LangGraph框架-image-1.png)

### 状态图

`StateGraph` 类是主要使用的图形类。这是由用户定义的 `State` 对象参数化的。

通俗来说，它是一张**流程图 + 状态管理系统**，定义了：

1. 哪些步骤（节点）要执行？

2. 每一步之间怎么跳转（边）？

3. 整个流程中数据状态如何流动和更新（状态）？

**为什么叫“状态图”而不是“流程图”？**

LangGraph 不只是流程控制，还强调：

* 每个节点执行前、执行后都可以**访问和修改状态**（state）

* 状态是图的“血液”，在节点之间流动

* **节点的跳转可以依据状态来判断**（如条件跳转）

所以叫做 **State Graph（有状态的流程图）**，而不是“静态流程图”。

```python
from typing import TypedDict
from langgraph.graph import StateGraph

# 定义状态结构
class MyState(TypedDict):
    question: str
    answer: str

# 定义节点函数
def search_node(state):
    return {"answer": "这是答案"}

# 创建状态图
builder = StateGraph(state_schema=MyState)
# 添加一个节点
builder.add_node("search", search_node)
# 第一个要调用的节点
builder.set_entry_point("search")
# 要构建图，首先要定义状态，然后添加节点和边，最后进行编译，会进行基本的检查
graph = builder.compile()

# 执行图
result = graph.invoke({"question": "什么是状态图？"})
print(result["answer"])  # 输出：这是答案
```

## <span style="color: rgb(216,57,49); background-color: inherit">State（状态）</span>

在使用 LangGraph 构建流程图之前，**第一件事**就是定义图的状态 `State`。这是整个图运行中用于**共享和传递信息**的核心机制。

### **什么是 State？**

LangGraph 中的 **State** 是图中所有节点（Node）之间传递数据的**模式结构**，可以类比为一个共享的上下文字典，它包含输入、输出、中间变量等。

定义 State 时，需要包含两个部分：

1. **Schema（模式）**：指定 State 的字段结构（可以用 `TypedDict` 或 `Pydantic`）

```python
# langgraph推荐使用TypedDict
"""
1. TypedDict 是标准库的一部分（来自 typing 模块），零依赖，零性能开销而 Pydantic 会在每一步创建模型实例，会增加运行时负担
2. LangGraph 中的 State 实质就是一个字典（dict），而 TypedDict 就是“有类型注解的 dict”，与 LangGraph 的执行机制无缝对接，而 Pydantic 是类结构，需要 .dict() 转换，略显多余
"""
from typing import TypedDict


class State1(TypedDict):
    user_input: str

# 使用 pydantic 可以进行参数校验和提供默认值
from pydantic import BaseModel


class State2(BaseModel):
    question: str
    result: str = ""
```

* **多个模式（Multiple Schemas）：**&#x5728;大多数情况下，LangGraph 使用一个统一的 State 模式。但你也可以设置“输入模式”和“输出模式”分开

  * 输入模式：接收用户输入的字段（如 `question`）

  * 输出模式：只保留最终输出的字段（如 `final_answer`）

```python
from typing import TypedDict
from langgraph.graph import StateGraph


# 1. 定义输入、输出、图内部的状态结构

# 输入字段：用户的问题
class InputState(TypedDict):
    question: str


# 中间状态：包括中间结果
class InternalState(TypedDict):
    question: str
    search_result: str
    final_answer: str


# 输出字段：只想返回最终答案
class OutputState(TypedDict):
    final_answer: str


# 2. 定义节点函数（中间节点用中间字段）
def search_node(state: InternalState) -> dict:
    return {"search_result": f"搜索了：{state['question']}"}


def answer_node(state: InternalState) -> dict:
    return {"final_answer": f"根据搜索结果：{state['search_result']}，这是答案"}


# 3. 创建 StateGraph，显式指定输入/输出 Schema
builder = StateGraph(state_schema=InternalState, 
                     input_schema=InputState, 
                     output_schema=OutputState)

# 4. 添加节点
builder.add_node("search", search_node)
builder.add_node("answer", answer_node)

# 5. 配置流程
builder.set_entry_point("search")
builder.add_edge("search", "answer")

# 6. 编译并执行图
app = builder.compile()

result = app.invoke({"question": "什么是LangGraph？"})

print(result)  # {'final_answer': '根据搜索结果：搜索了：什么是LangGraph？，这是答案'}
```

* **Reducer（归并函数）**：在 LangGraph 中，所有节点返回的都是“局部更新结果”，**Reducer 是用于合并多个节点输出更新的机制**。 **将每个节点返回的“局部状态更新”统一合并进全局的 State。**

![](LangGraph框架-diagram.png)

```python
from typing import Annotated 
from typing_extensions import TypedDict 
from operator import add 

class State(TypedDict):     
    foo: int     
    bar: Annotated[list[str], add] # 每条消息是 {role, content}，会自动追加到列表末尾
```

### 使用图形状态中的消息

**为什么要使用消息？**

大多数现代 LLM 提供商都提供聊天模型接口，接受消息列表作为输入。LangChain`ChatModel`尤其接受对象列表`Message`作为输入。这些消息有多种形式，例如`HumanMessage`（用户输入）或`AIMessage`（LLM 响应）。

**在图表中使用消息**

在许多情况下，将之前的对话历史记录以消息列表的形式存储在图状态中会很有帮助。为此，我们可以向图状态添加一个键（通道），该键存储`Message`对象列表，并使用 Reducer 函数对其进行注释。Reducer 函数对于指示图如何`Message`在每次状态更新（例如，当节点发送更新时）时更新状态中的对象列表至关重要。如果您未指定 Reducer，则每次状态更新都会用最新提供的值覆盖消息列表。如果您只想将消息附加到现有列表中，可以使用`operator.add`。

```python
operator 是 Python 的一个内置模块，把常见的运算符（如 +、-、==、getitem 等）变成了函数，方便函数式编程和高阶函数使用。
```

```python
from typing import TypedDict
from langgraph.graph import StateGraph
from typing import Annotated
import operator


# 定义状态结构   如果定义的是list[dict]，会覆盖之前的数据
class ChatState(TypedDict):
    messages: Annotated[list, operator.add]  # 每条消息是 {role, content}，会自动追加到列表末尾


# 节点函数：添加用户问题
def user_input_node(state: ChatState) -> dict:
    user_msg = {"role": "user", "content": "什么是LangGraph？"}
    return {"messages": [user_msg]}


# 节点函数：添加助手回复
def assistant_node(state: ChatState) -> dict:
    reply = {"role": "assistant", "content": "LangGraph 是一个有状态的图编排框架。"}
    return {"messages": [reply]}


# 构建状态图
builder = StateGraph(state_schema=ChatState)
builder.add_node("user_input", user_input_node)
builder.add_node("assistant_reply", assistant_node)
builder.set_entry_point("user_input")
builder.add_edge("user_input", "assistant_reply")

graph = builder.compile()

result = graph.invoke({"messages": []})
print(result["messages"])
```

有场景可能还需要手动更新图状态中的消息（例如，人机交互）。
如果想去修改之前的某一个状态，但使用 `operator.add`，您发送到图的手动状态更新将被附加到现有消息列表中，而不是更新现有消息。


为了避免这种情况，您需要一个能够跟踪消息 ID 并在更新时覆盖现有消息的 Reducer。
为此，您可以使用预构建 `add_messages` 函数。
对于新消息，它只会附加到现有列表中，但它也会正确处理现有消息的更新。

```python
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

### MessagesState

由于在状态中包含消息列表非常常见，因此存在一个名为`MessagesState`的预建状态，它使使用消息变得非常简单。该状态`MessagesState`使用单个键定义`messages`，该键是对象列表`AnyMessage`并使用`add_messages`。通常，需要跟踪的状态不仅仅是消息，因此我们看到人们将这个状态子类化并添加更多字段，例如：

```python
from langgraph.graph import MessagesState

# 和上述代码不同会在State类中自动维护一个messages 字段，不需要显示创建
class State(MessagesState):
    documents: list[str]
```

## <span style="color: rgb(216,57,49); background-color: inherit">Node（节点）</span>

**节点（Nodes）是图中执行逻辑的基本单位**。每个节点表示一个**函数步骤、处理阶段或子逻辑流程**，多个节点通过边连接成有向图，组成一个完整的有状态计算流程。

**LangGraph 中的节点就是你定义的一个函数（或 Runnable 对象）**，用于接收状态、执行逻辑，并返回更新后的状态

```python
def my_node(state: dict) -> dict:
    # 处理输入状态，并返回更新字段
    return {"new_key": "new_value"}
    
# LangGraph 会自动用 reducer 把这些更新合并进全局状态。
```

### `START`节点

Node`START`是一个特殊节点，表示将用户输入发送到图的节点。引用此节点的主要目的是确定应首先调用哪些节点。

```plain&#x20;text
from langgraph.graph import START

graph.add_edge(START, "node_a")
```

### `END`节点

Node`END`是一个特殊节点，表示终端节点。当需要指示哪些边在完成后没有操作时，可以引用此节点。

```plain&#x20;text
from langgraph.graph import END

graph.add_edge("node_a", END)
```

### 并行运行节点

```python
import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    # The operator.add reducer fn makes this append-only
    aggregate: Annotated[list, operator.add]

def a(state: State):
    print(f'Adding "A" to {state["aggregate"]}')
    return {"aggregate": ["A"]}

def b(state: State):
    print(f'Adding "B" to {state["aggregate"]}')
    return {"aggregate": ["B"]}

def c(state: State):
    print(f'Adding "C" to {state["aggregate"]}')
    return {"aggregate": ["C"]}

def d(state: State):
    print(f'Adding "D" to {state["aggregate"]}')
    return {"aggregate": ["D"]}

builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.add_node(c)
builder.add_node(d)
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "d")
builder.add_edge("c", "d")
builder.add_edge("d", END)
graph = builder.compile()

print(graph.invoke({"aggregate": ["start"]}))
```

## <span style="color: rgb(216,57,49); background-color: inherit">Edge（边/跳转）</span>

**Edge（边）** 是连接节点的通道，表示图中**节点之间的执行跳转关系**。你可以把它理解为「节点执行完之后，下一步去哪，是构成 LangGraph 流程图的核心。

> **Edge 是 LangGraph 中连接两个节点的“执行路径”**，控制流程的走向。

* 普通边：直接从一个节点到下一个节点。

```python
graph.add_edge("节点A", "节点B")
```

* 条件边：调用一个函数来确定下一步要去哪个节点。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END


class MyState(TypedDict):
    type: str
    result: str


def judge_node(state: MyState):
    """节点函数：可以做一些预处理"""
    return state  # 保持状态不变，只是路由


def route_condition(state: MyState):
    """条件函数：只负责路由决策"""
    if state["type"] == "a":
        return "a"
    elif state["type"] == "b":
        return "b"
    else:
        return "default"


def node_a(state):
    return {"result": "走了 A 分支"}


def node_b(state):
    return {"result": "走了 B 分支"}


def node_default(state):
    return {"result": "走了默认分支"}


# 构建图
graph = StateGraph(state_schema=MyState)
# 定义节点
graph.add_node("judge_node", judge_node)
graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.add_node("default", node_default)
# 定义开始节点
graph.set_entry_point("judge_node")

# 使用不同的函数作为条件函数
graph.add_conditional_edges("judge_node", route_condition, {
    "a": "a",
    "b": "b",
    "default": "default"
})

# 添加结束边
graph.add_edge("a", END)
graph.add_edge("b", END)
graph.add_edge("default", END)

app = graph.compile()

# 测试
print("测试 A:", app.invoke({"type": "a", "result": ""}))
```

* 入口点：当图开始运行时首先运行的第一个（些）节点。

```python
from langgraph.graph import START

graph.add_edge(START, "node_a")
```

* 条件入口点：调用一个函数来确定当用户输入到达时首先调用哪个节点。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END


class MyState(TypedDict):
    user_type: str  # "vip", "normal", "guest"
    message: str
    result: str


# 定义不同的处理节点
def vip_service(state):
    """VIP 用户服务"""
    return {"result": f"VIP专享服务: {state['message']}"}


def normal_service(state):
    """普通用户服务"""
    return {"result": f"标准服务: {state['message']}"}


def guest_service(state):
    """游客服务"""
    return {"result": f"游客服务(功能受限): {state['message']}"}


# 条件入口点函数
def route_by_user_type(state):
    """根据用户类型路由到不同的服务"""
    user_type = state["user_type"]

    if user_type == "vip":
        return "vip_service"
    elif user_type == "normal":
        return "normal_service"
    else:
        return "guest_service"


# 构建图
workflow = StateGraph(state_schema=MyState)

# 添加节点
workflow.add_node("vip_service", vip_service)
workflow.add_node("normal_service", normal_service)
workflow.add_node("guest_service", guest_service)

# 设置条件入口点 - 关键部分！
workflow.set_conditional_entry_point(
    route_by_user_type,  # 条件函数
    {
        "vip_service": "vip_service",
        "normal_service": "normal_service",
        "guest_service": "guest_service"
    }
)

# 添加结束边
workflow.add_edge("vip_service", END)
workflow.add_edge("normal_service", END)
workflow.add_edge("guest_service", END)

# 编译图
app = workflow.compile()
# 测试 VIP 用户
result1 = app.invoke({
    "user_type": "vip",
    "message": "我要退款",
    "result": ""
})
print("VIP用户:", result1)
```

## <span style="color: rgb(216,57,49); background-color: inherit">Send发送</span>

默认情况下，`Nodes`和`Edges`是提前定义的，并在相同的共享状态下运行。但是，在某些情况下，确切的边无法提前知道，并且可能希望同时存在`State`的不同版本。

`send("节点名", 更新数据)` 的作用是：告诉 LangGraph 把这部分更新数据发送给指定节点，让它继续执行。

### 主要用途

1. **条件路由**：根据某些条件将消息发送到不同的节点（可以直接用条件边实现，没必要用send）

2. **并行处理**：同时向多个节点发送消息 （核心）

3. **动态工作流**：根据运行时状态决定消息的发送目标

**和add\_conditional\_edges两者通常在需要并发处理的时候配合使用**

#### Map-Reduce模式

**Map-Reduce&#x20;**&#x662F;一种经典的并行计算模式，特别适合处理大规模数据。

**Map-Reduce** 将复杂的数据处理任务分解为两个阶段：

1. **Map阶段**：将大任务分解为多个小任务，并行处理

2. **Reduce阶段**：将所有小任务的结果合并成最终结果

```python
"""
LangGraph Map-Reduce 简单案例：数字求和
把一堆数字分给多个worker算平方，然后把结果加起来
"""
from typing import Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from typing import TypedDict, List

# 状态定义
class State(TypedDict):
    numbers: List[int]        # 输入的数字
    results: Annotated[list[int], operator.add]        # worker的结果
    final_sum: int           # 最终求和

# 1. Map阶段：分发数字
def split_numbers(state: State):
    """把数字分发给不同的worker"""
    numbers = state["numbers"]
    print(f"分发数字: {numbers}")

    # 每个数字发给一个worker
    return [Send("worker", {"number": num}) for num in numbers]

# 2. Worker阶段：计算平方
def calculate_square(state: State):
    """每个worker计算一个数字的平方"""
    number = state["number"]
    square = number * number
    print(f"Worker: {number}² = {square}")
    return {"results": [square]}

# 3. Reduce阶段：求和
def sum_results(state: State):
    """把所有结果加起来"""
    results = state.get("results", [])
    total = sum(results)
    print(f"求和: {results} = {total}")
    return {"final_sum": total}

# 构建图
def create_simple_graph():
    graph = StateGraph(State)

    # 添加节点
    graph.add_node("splitter", lambda s: s)  # 分发器
    graph.add_node("worker", calculate_square)  # 工作节点
    graph.add_node("summer", sum_results)      # 求和器

    # 连接节点
    graph.add_edge(START, "splitter")
    graph.add_conditional_edges("splitter", split_numbers, ["worker"])  # Map阶段
    graph.add_edge("worker", "summer")  # Worker完成后求和
    graph.add_edge("summer", END)

    return graph.compile()

# 运行例子
def run_example():
    app = create_simple_graph()

    # 测试数据
    initial_state = {
        "numbers": [1, 2, 3, 4, 5],
        "results": [],
        "final_sum": 0
    }

    print("开始计算...")
    print("任务：计算每个数字的平方，然后求和")
    print()

    # 运行
    result = app.invoke(initial_state)
    print(result)

if __name__ == "__main__":
    run_example()
```

## `Command`<span style="color: rgb(216,57,49); background-color: inherit">命令</span>

Command 是 LangGraph 中用于**控制图执行流程、更新图状态，并支持人机交互、工具调用的标准化对象。**

### 核心作用：

**第一，更新图的运行状态；**

**第二，控制图的执行流向（指定下一个或多个执行节点）；**

**第三，衔接中断恢复、工具调用、人机交互等场景**。

### command参数拆解

`update`：应用状态更新（类似于从节点返回更新）。

`goto`：导航到特定节点（类似于 条件边）。

`graph`：在从 子图 导航时定位到父图。

`resume`：在 中断 后提供一个值以继续执行。



### 在什么情况下使用

**从节点返回：**&#x4F7F;用 `update`、`goto` 和 `graph` 将状态更新与控制流结合。

**interrupt（人机交互）输入到`invoke`或`stream`**：在使用**interrupt**中断后使用`resume`继续执行

**从工具返回：**&#x7C7B;似于从节点返回，结合工具内部的状态更新和控制流。

> 在节点函数中返回时`Command`，必须添加返回类型注释，其中包含节点路由到的节点名称列表，例如`Command[Literal["my_other_node"]]`。这对于图形渲染是必需的，它告诉 LangGraph 当前节点可以导航到`my_other_node`。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.types import Command, Send
from typing import Literal


class MyState(TypedDict):
    type: str
    text: str
    result: str


def judge_node(state: MyState) -> Command[Literal["a", "b", "default"]]:
    """条件函数：使用Command进行路由和状态更新"""
    if state["type"] == "a":
        return Command(update={"text": "走了 A 分支"}, goto="a")
    elif state["type"] == "b":
        return Command(update={"text": "走了 B 分支"}, goto="b")
    else:
        return Command(update={"text": "走了默认分支"}, goto="default")


def node_a(state):
    return {"result": f"A节点处理: {state['text']}"}


def node_b(state):
    return {"result": f"B节点处理: {state['text']}"}


def node_default(state):
    return {"result": f"默认节点处理: {state['text']}"}


# 构建图
graph = StateGraph(state_schema=MyState)
graph.add_node("judge_node", judge_node)
graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.add_node("default", node_default)

graph.set_entry_point("judge_node")

# 添加结束边
graph.add_edge("a", END)
graph.add_edge("b", END)
graph.add_edge("default", END)

app = graph.compile()

# 测试
print("测试 A:", app.invoke({"type": "a", "text": "", "result": ""}))
print("测试 B:", app.invoke({"type": "b", "text": "", "result": ""}))
print("测试其他:", app.invoke({"type": "default", "text": "", "result": ""}))
```

### 什么时候应该使用`Command`而不是条件边？

`Command`当需要**同时**更新图形状态**和**路由到其他节点时使用。例如，在实现多代理切换时，需要路由到其他代理并向该代理传递一些信息。在进行command更新状态的时候，更新的属性必须符合初始化状态的内容

使用条件边在节点之间有条件地路由而不更新状态。

**<span style="color: rgb(216,57,49); background-color: inherit">（注意：如果你只需要用路由功能不去更新状态的话，请直接用条件边！！！）</span>**

## 运行时配置`Runtime` &#x20;

创建图时，还可以标记图的某些部分是可配置的。这样做通常是为了方便在模型或系统提示之间切换。这允许创建单个“认知架构”（图），但拥有多个不同的实例。

**在运行图时提供额外的“配置参数”而不是“状态参数”**，并且通过类型约束这些参数。

**传递非图状态的依赖信息，为节点提供执行所需的辅助资源，同时不干扰图状态的正常流转和更新**。

```python
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing import TypedDict

# 定义状态结构
class MyState(TypedDict):
    question: str
    answer: str

# 定义配置结构
class MyContext:
    language: str  # 配置中包含语言选项，比如 "en" 或 "zh"

# 节点函数可以访问 runtime 参数  runtime 可以访问上下文和内存存储
def step1(state: MyState, runtime: Runtime[MyContext]):
    if runtime.context["language"] == "zh":
        answer = "你好！"
    else:
        answer = "Hello!"
    return {"answer": answer}

# 构建图..
graph = StateGraph(state_schema=MyState, context_schema=MyContext)
graph.add_node("step1", step1)
graph.set_entry_point("step1")

# 编译
app = graph.compile()

# 执行时传入 config 参数（区分于 state）
result = app.invoke({"question": "Hi"}, context={"language": "zh"})
print(result)  # => {"question": "Hi", "answer": "你好！"}
```

在运行时指定llm

```python
from langgraph.graph import MessagesState
from langgraph.runtime import Runtime
from langgraph.graph import END, StateGraph, START
from typing_extensions import TypedDict


class MyContext(TypedDict):
    model: str


MODELS = {
    "anthropic": "anthropic:claude-3-5-haiku-latest",
    "openai": "openai:gpt-4.1-mini",
}


def call_model(state: MessagesState, runtime: Runtime[MyContext]):
    model = ""
    if runtime.context:
        model = runtime.context["model"]
        model = MODELS[model]
    return {"messages": {"role": "assistant", "content": model}}


builder = StateGraph(MessagesState, context_schema=MyContext)
builder.add_node("model", call_model)
builder.add_edge(START, "model")
builder.add_edge("model", END)

graph = builder.compile()

# 问题
input_message = {"role": "user", "content": "hi"}
# 没有配置时，使用默认值（Anthropic）
response_1 = graph.invoke({"messages": [input_message]})
# 切换成 openai
context = {"model": "openai"}
response_2 = graph.invoke({"messages": [input_message]}, context=context)

print(response_1)
print(response_2)
```

### 递归限制

递归限制设置图在单次执行中可以执行的最大超步数。一旦达到限制，LangGraph 将出现`GraphRecursionError`。默认情况下，此值设置为 1000 步。可以在运行时在任何图上设置递归限制，并将其传递给`.invoke`/`.stream`通过配置字典。

```python
import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.managed.is_last_step import RemainingSteps

class State(TypedDict):
    aggregate: Annotated[list, operator.add]
    remaining_steps: RemainingSteps

def a(state: State):
    print(f'Node A sees {state["aggregate"]}')
    return {"aggregate": ["A"]}

def b(state: State):
    print(f'Node B sees {state["aggregate"]}')
    return {"aggregate": ["B"]}

# Define nodes
builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)

# Define edges
def route(state: State) -> Literal["b", END]:
    if state["remaining_steps"] <= 2:
        return END
    else:
        return "b"

builder.add_edge(START, "a")
builder.add_conditional_edges("a", route)
builder.add_edge("b", "a")
graph = builder.compile()

# Test it out
result = graph.invoke({"aggregate": []}, {"recursion_limit": 10})
print(result)
```

## <span style="color: rgb(216,57,49); background-color: inherit">重试策略</span>

### 为什么需要重试策略？

1. **LLM API 超时**或达到速率限制（Rate Limit）。

2. **数据库连接**瞬时抖动。

3. **网络请求**失败（5xx 错误）。

在 LangGraph 中，我们通过 `add_node` 的 `retry_policy` 参数来增强节点的健壮性。

```python
默认异常类，出现以下的异常会自动重试

ValueError,
TypeError,
ArithmeticError,
ImportError,
LookupError,
NameError,
SyntaxError,
RuntimeError,
ReferenceError,
StopIteration,
StopAsyncIteration,
OSError,
```

```python
from langgraph.types import RetryPolicy  
# 使用默认策略（自动过滤掉无法通过重试解决的错误，如 SyntaxError） 
builder.add_node("agent", agent_node, retry_policy=RetryPolicy())
```

```python
import sqlite3
from langchain.chat_models import init_chat_model
from langgraph.graph import END, MessagesState, StateGraph, START
from langgraph.types import RetryPolicy
from langchain_community.utilities import SQLDatabase
from langchain.messages import AIMessage, HumanMessage
from langgraph.runtime import Runtime
from dotenv import load_dotenv

load_dotenv()

db = SQLDatabase.from_uri("sqlite:///:memory:")
model = init_chat_model("deepseek-chat")


def query_database(state: MessagesState, runtime: Runtime):
    print(f"正在尝试第 {runtime.execution_info.node_attempt} 次查询...")
    # 手动抛出一个异常来强制触发重试
    if runtime.execution_info.node_attempt < 3:
        print("模拟数据库连接失败...")
        raise sqlite3.OperationalError("Database connection lost")

    query_result = db.run("SELECT 1;")  # 模拟成功
    return {"messages": [AIMessage(content=str(query_result))]}


def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}


# Define a new graph
builder = StateGraph(MessagesState)
builder.add_node(
    "query_database",
    query_database,
    retry_policy=RetryPolicy(retry_on=[sqlite3.OperationalError, sqlite3.IntegrityError]),  # 可以自己设定需要触发的异常类
)
builder.add_node("model", call_model, retry_policy=RetryPolicy(max_attempts=5))  # 重试次数
builder.add_edge(START, "model")
builder.add_edge("model", "query_database")
builder.add_edge("query_database", END)
graph = builder.compile()

response = graph.invoke({"messages": [HumanMessage(content="你好呀？")]})
print(response)
```

可以通过`Runtime` 对象，允许节点在运行时“查看”自己的执行状态。

![](LangGraph框架-image-2.png)

## 可视化图表

```python
"""
LangGraph Map-Reduce 简单案例：数字求和
把一堆数字分给多个worker算平方，然后把结果加起来
"""
from typing import Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, List


# 状态定义
class State(TypedDict):
    numbers: List[int]  # 输入的数字
    number: int
    results: Annotated[list[int], operator.add]  # worker的结果
    final_sum: int  # 最终求和


# 1. Map阶段：分发数字
def split_numbers(state: State):
    """把数字分发给不同的worker"""
    numbers = state["numbers"]
    print(f"📦 分发数字: {numbers}")

    # 每个数字发给一个worker
    return [Send("worker", {"number": num}) for num in numbers]


# 2. Worker阶段：计算平方
def calculate_square(state: State):
    """每个worker计算一个数字的平方"""
    number = state["number"]
    square = number * number
    print(f"⚡ Worker: {number}² = {square}")
    return {"results": [square]}


# 3. Reduce阶段：求和
def sum_results(state: State):
    """把所有结果加起来"""
    results = state.get("results", [])
    total = sum(results)
    print(f"📊 求和: {results} = {total}")
    return {"final_sum": total}


# 构建图
def create_simple_graph():
    graph = StateGraph(State)

    # 添加节点
    graph.add_node("splitter", lambda s: s)  # 分发器
    graph.add_node("worker", calculate_square)  # 工作节点
    graph.add_node("summer", sum_results)  # 求和器

    # 连接节点
    graph.add_edge(START, "splitter")
    graph.add_conditional_edges("splitter", split_numbers, ["worker"])  # Map阶段
    graph.add_edge("worker", "summer")  # Worker完成后求和
    graph.add_edge("summer", END)

    return graph.compile()


# 运行例子
def run_example():
    app = create_simple_graph()

    # 测试数据
    initial_state = {
        "numbers": [1, 2, 3, 4, 5],
        "results": [],
        "final_sum": 0
    }

    print("🚀 开始计算...")
    print("任务：计算每个数字的平方，然后求和")
    print()

    # 运行
    app.invoke(initial_state)

    # 方法1：可视化成png图片
    # from IPython.display import Image, display
    # display(
    #     Image(
    #         app.get_graph().draw_mermaid_png(output_file_path="./send并行.png")
    #     )
    # )
    # 方法2：转换成 Mermaid 语法
    print(app.get_graph().draw_mermaid())

if __name__ == "__main__":
    run_example()
```

# <span style="color: rgb(216,57,49); background-color: inherit">子图</span>

LangGraph子图（Subgraph）是一种模块化的图结构，允许您将复杂的工作流分解为更小的、可重用的组件。就像函数在编程中的作用一样，子图提供了封装和复用的能力。

![](LangGraph框架-image-3.png)

## 子图的优势

1. **代码复用**：避免重复编写相同的逻辑

2. **清晰的架构**：将复杂流程分解为清晰的模块

3. **易于维护**：修改子图只需在一个地方进行

4. **团队协作**：不同团队可以独立开发不同的子图

5. **测试友好**：可以单独测试子图的功能

## 两种状态通讯

### **1.共享状态键（Shared State Keys）**

父图和子图在其状态模式中有共享的状态键。在这种情况下，您可以将子图作为节点包含在父图中。

```python
from langgraph.graph import StateGraph, MessagesState, START
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='qwen-plus-2025-01-25')


# 创建子图
def subplot(state: MessagesState) -> MessagesState:
    # 获取大模型回答的内容进行摘要总结
    answer = state["messages"][-1].content
    summary_prompt = f"请用一句话总结下面这句话：\n\n答：{answer}"
    response = llm.invoke(summary_prompt)
    return {"messages": state["messages"] + [response]}


summary_subgraph = (
    StateGraph(state_schema=MessagesState)
    .add_node("subplot", subplot)
    .add_edge(START, "subplot")
    .compile()
)


# 创建父图

def llm_answer_node(state: MessagesState) -> MessagesState:
    # 使用大模型进行回答
    answer = llm.invoke(state["messages"])
    print("父图输出", answer)
    return {"messages": state["messages"] + [answer]}


parent_graph = (
    StateGraph(MessagesState)
    .add_node("llm_answer", llm_answer_node)
    .add_node("summarize_subgraph", summary_subgraph)
    .add_edge(START, "llm_answer")
    .add_edge("llm_answer", "summarize_subgraph")
    .compile()
)

# 测试
input_state = {
    "messages": [{"role": "user", "content": "langgraph是什么？"}],
}
result = parent_graph.invoke(input_state)
print(result)
```

### 2.不同状态模式（Different State Schemas）

父图和子图有不同的模式（状态模式中没有共享的状态键）。在这种情况下，您必须在父图的节点内部调用子图：这在父图和子图有不同状态模式且需要在调用子图前后转换状态时很有用。

```python
from langgraph.graph import StateGraph, MessagesState, START
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='qwen-plus-2025-01-25')


# 创建子图
class SubgraphMessagesState(TypedDict):
    subgraph_messages: Annotated[list[AnyMessage], add_messages]


def subplot(state: SubgraphMessagesState) -> SubgraphMessagesState:
    # 获取大模型回答的内容进行摘要总结
    answer = state["subgraph_messages"][-1].content
    summary_prompt = f"请用一句话总结下面这句话：\n\n答：{answer}"
    response = llm.invoke(summary_prompt)
    print("\n\n")
    print("子图中问题和输出:", state["subgraph_messages"] + [response])
    return {"subgraph_messages": [response]}


summary_subgraph = (
    StateGraph(state_schema=SubgraphMessagesState)
    .add_node("subplot", subplot)
    .add_edge(START, "subplot")
    .compile()
)


# 创建父图

def llm_answer_node(state: MessagesState) -> MessagesState:
    # 使用大模型进行回答
    answer = llm.invoke(state["messages"])
    print("父图中问题和输出:", state["messages"] + [answer])
    # 转换状态格式
    summary_result = summary_subgraph.invoke({"subgraph_messages": state["messages"] + [answer]})
    return {"messages": state["messages"] + [answer]+ [summary_result["subgraph_messages"][2]]}


parent_graph = (
    StateGraph(state_schema=MessagesState)
    .add_node("llm_answer", llm_answer_node)
    .add_edge(START, "llm_answer")
    .compile()
)

# 测试输入
input_state = {
    "messages": [{"role": "user", "content": "langgraph是什么？"}],
}
result = parent_graph.invoke(input_state)
print("最终结果：", result)
```

总结：**小型项目或快速原型常用“添加子图作为节点（共享状态）”**，而**大型、生产级系统更倾向于“调用节点内的子图（状态转换）”**。

# <span style="color: rgb(216,57,49); background-color: inherit">持久性（重点）</span>

检查点（Checkpointing）是 LangGraph 持久性的核心机制。它允许你在图执行过程中的任何点保存状态，并在需要时恢复。

![](LangGraph框架-image-4.png)

## 核心概念

* **检查点(Checkpoint)**: 图状态的快照

* **线程(Thread)**: 用于访问检查点的唯一标识

* **检查点保存器(Checkpointer)**: 负责保存和恢复状态的组件

  ## 线程(Threads)

线程是检查点保存器保存的每个检查点分配的唯一 ID 或线程标识符

当使用检查点调用图表时，**必须**指定`thread_id`作为`configurable`配置部分的一部分：

```python
# 调用图时必须指定 thread_id
config = {"configurable": {"thread_id": "unique_thread_id"}}
result = graph.invoke(input_data, config=config)
```

### 特点

* 每个线程代表一个独立的对话或执行上下文

* 线程允许在图执行后访问图的状态

* 支持多个并发线程

```python
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
import os
from dotenv import load_dotenv

load_dotenv()

class MyState(MessagesState):
    result: str

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='MiniMax-M2.1')


async def process_message(state: MessagesState):
    response = await llm.ainvoke(state["messages"])
    return {"messages": response}

async def optimize_message(state: MessagesState):
    messages = state["messages"] + [{"role": "system", "content": "请用幽默的形式回复用户"}]
    response = await llm.ainvoke(messages)
    return {"messages": response}


builder = StateGraph(state_schema=MyState)
builder.add_node("process_message", process_message)
builder.add_node("optimize_message", optimize_message)
builder.add_edge(START, "process_message")
builder.add_edge("process_message", "optimize_message")
builder.add_edge("optimize_message", END)



# 没有使用持久性
# graph = builder.compile()

# input_message = {"role": "user", "content": "你好呀！我的名字叫初见"}
# result = graph.invoke({"messages": [input_message]})
# result["messages"][-1].pretty_print()
#
# input_message = {"role": "user", "content": "我的名字叫什么?"}
# result = graph.invoke({"messages": [input_message]})
# result["messages"][-1].pretty_print()

async def main():
    # 创建内存检查点进行持久化存储
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "user_123"}}

    input_message = {"role": "user", "content": "你好呀！我的名字叫初见"}
    result = await graph.ainvoke({"messages": [input_message]}, config)
    result["messages"][-1].pretty_print()


    input_message = {"role": "user", "content": "我的名字叫什么？"}
    result = await graph.ainvoke({"messages": [input_message]}, config)
    result["messages"][-1].pretty_print()

if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
```

## 检查点

检查点是在每个超级步骤中保存的图状态的快照，由`StateSnapshot`具有以下关键属性的对象表示：

* `config`：与此检查点相关的配置。

* `metadata`：与此检查点相关的元数据。

* `values`：当前 `State` 的值。也就是图执行到目前为止，所有变量的状态值（如 `"messages"`, `"steps"`, `"results"` 等字段的值）。

* `next`图中接下来要执行的节点名称的元组。

* `tasks`：包含具体要执行的任务的详细信息，用 `PregelTask` 类型表示。比 `next` 更详细

### LangGraph 中检查点的作用

|                  |                                          |
| ---------------- | ---------------------------------------- |
| 功能               | 描述                                       |
| 🌟 容错恢复          | 如果执行中断（如容器崩溃、任务超时），可以从上次保存的状态恢复，不用重跑整个流程 |
| 💾 状态追踪/审计       | 可以记录每一步节点执行时的中间状态，方便 Debug、回溯和监控         |
| 🔁 实现有状态的异步/长流程图 | 对于多轮对话、多阶段任务，检查点使 LangGraph 支持状态持久化和任务跟踪 |

### 本质理解

> LangGraph 中的图是围绕 **`State` 状态对象** 构建的：
>
> > 每个节点执行时会读取当前State，并返回State的局部更新，这些更新会被合并到全局State中。
>
> 所谓的“检查点”就是：
>
> > **在某个节点运行后，把当时的 `State` 存起来**（比如存到数据库或磁盘）
>
> 然后如果下次因为任何原因中断或重新运行，只需：
>
> > **加载上次的检查点状态 `State`，重新进入图流程**
>
### 获取状态内容

```python
import asyncio

from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.chat_models import init_chat_model
# 导入内存检查点对象   短期记忆
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
import os

load_dotenv()

# 初始化模型
llm = init_chat_model(
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    base_url=os.getenv('DASHSCOPE_BASE_URL'),
    model_provider="openai",
    model="kimi-k2.5"  # 在做智能体的时候，最好去选择模型效果好一点
)


# 创建子图
# 创建子图
def sub_plot(state: MessagesState):
    # 总结父图中模型生成的文档
    content = state["messages"][-1].content  # 获取最新一条消息
    summary_prompt = f"请用一句话总结以下内容：\n\n {content}"
    response = llm.invoke(summary_prompt)
    return {"messages": response}


# 初始化子图
summary_subgraph = (
    StateGraph(state_schema=MessagesState)
    .add_node("subplot", sub_plot)
    .add_edge(START, "subplot")
    .compile()
)


# 创建父图
def llm_answer_node(state: MessagesState):
    answer = llm.invoke(state["messages"])
    # print("父图的中使用模型回复用户问题", answer)
    return {"messages": answer}


checkpointer = InMemorySaver()
# 初始化父图
parent_graph = (
    StateGraph(MessagesState)
    .add_node("llm_answer", llm_answer_node)
    .add_node("summarize_subgraph", summary_subgraph)  # 将子图当作父图的一个节点
    .add_edge(START, "llm_answer")
    .add_edge("llm_answer", "summarize_subgraph")
    .add_edge("summarize_subgraph", END)
    .compile(checkpointer=checkpointer)
)
# 定义config
config = {"configurable": {"thread_id": "12345"}}
# 测试输入
input_state = {
    "messages": [{"role": "user", "content": "langgraph是什么？请用100字介绍"}],
}
result = parent_graph.invoke(input_state, config=config)
# print(result)

# 获取状态   get_state()   获取之前thread_id已经完成任务的所有保存的内容
# print(parent_graph.get_state(config))

print("================状态历史记录=================")
"""
可以通过调用 获取给定线程的图形执行的完整历史记录graph.get_state_history(config)。
这将返回与配置中提供的线程 ID 关联的对象列表StateSnapshot。
重要的是，检查点将按时间顺序排序，最新的检查点 /StateSnapshot将位于列表中的第一个。

注意：这里采用的是共享状态的子图，可以将子图的内容持久化，如果使用的是不同状态的就需要分别存储
"""

history = list(parent_graph.get_state_history(config))
for idx, snapshot in enumerate(history):
    print(f"Step {idx}:")
    print(f"  Checkpoint ID: {snapshot.config['configurable']['checkpoint_id']}")
    print(f"  Node: {snapshot.metadata.get('source')}")
    print(f"  Messages: {[m.content for m in snapshot.values['messages']]}")
    print("")

print("================重放机制=================")
# 任务执行完成之后，将中间的重要步骤给用户查看，用户就可以决定从某些步骤中重新开始执行
# 注意：必须传递这些内容 thread_id， checkpoint_id
# 通过thread_id定位到某次会话，通过checkpoint_id定位到对应的节点
# 重放是会在原有的基础上生成一个新的检查点分支

# 获取step2当前的checkpoint_id，
step2_level_checkpoint = None
if history:
    step2_level_checkpoint = list(history)[1].config['configurable']['checkpoint_id']

# 重新创建一个config内容，其中指定checkpoint_id就能从指定的这个checkpoint_id节点开始重播
config1 = {"configurable": {"thread_id": "12345", "checkpoint_id": step2_level_checkpoint}}

new_result = parent_graph.invoke(None, config=config1)
print("重播后的内容")
print(new_result)

history = list(parent_graph.get_state_history(config))
for idx, snapshot in enumerate(history):
    print(f"Step {idx}:")
    print(f"  Checkpoint ID: {snapshot.config['configurable']['checkpoint_id']}")
    print(f"  Node: {snapshot.metadata.get('source')}")
    print(f"  Messages: {[m.content for m in snapshot.values['messages']]}")
    print("")
```

![](LangGraph框架-image-5.png)

## 更新对应状态

使用 `graph.update_state()` 方法编辑图状态。

**更新对应状态，就是手动修改线程里的状态数据。它不会删除历史，只会生成新的检查点。你可以改消息、改工具结果、加用户信息、删内容、覆盖内容。更新完之后，下一次 run 就从新状态继续执行。这是实现人工介入、调试、纠错的核心功能。**

### 方法参数

1. **config**

* 必须包含 `thread_id` 指定要更新的线程

* 可选包含 `checkpoint_id` 来分叉选定的检查点

- **values**

* 用于更新状态的值

* 更新会传递给 reducer 函数（如果定义了）

* 没有 reducer 的通道会被覆盖

- **as\_node**

* 可选参数，指定更新来自哪个节点

* 影响下一步执行的节点

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict
from typing import Annotated
from operator import add


class TaskState(TypedDict):
    task_id: str  # 任务id
    title: str  # 标题
    assignee: str  # 接收任务的人
    priority: int  # 优先级
    comments: Annotated[list, add]  # 评论
    status: str  # 状态


def create_task(state: TaskState):
    """创建任务"""
    print(123456789)
    return {
        "status": "进行中",
        "comments": [f"任务 '{state['title']}' 已创建，分配给 {state['assignee']}"]
    }


def update_task(state: TaskState):
    """更新任务"""

    return {
        "status": "已更新",
        "comments": ["任务状态已更新"]
    }


def plan_task(state: TaskState):
    """准备任务完成"""
    return {
        "status": "已准备",
        "comments": [f"任务 '{state['title']}' 已准备"]
    }


# 创建任务管理流程
workflow = StateGraph(state_schema=TaskState)
workflow.add_node("create", create_task)
workflow.add_node("update", update_task)
workflow.add_node("complete", plan_task)
workflow.add_edge(START, "create")
workflow.add_edge("create", "update")
workflow.add_edge("update", "complete")
workflow.add_edge("complete", END)

checkpointer = InMemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# 创建任务
config = {"configurable": {"thread_id": "task_001"}}
result = app.invoke({
    "task_id": "T001",
    "title": "开发注册功能",
    "assignee": "张三",
    "priority": 1,
    "comments": [],
    "status": "待分配"
}, config)

print("=== 任务创建完成 ===")
print(f"状态: {result['status']}")
print("评论:", result['comments'])

# 演示 as_node 参数, 或者指定某个具体检查点的config去进行更新
# 本质是创建了一个新的检查点，再次调用invoke方法会从新的检查点继续执行剩下流程
history = list(app.get_state_history(config))
before_complete = next(s for s in history if s.next == ("complete",))
print("\n=== 使用 as_node 参数 ===")
app.update_state(before_complete.config, {
    "status": "已更新",
    "comments": ["自动通知：任务优先级提升"],
    "priority": 3
}, as_node="update")
# 执行一次流程（推进图的流程到下一个状态
final_result = app.invoke(None, config)
# 查看最终状态
final_state = app.get_state(config)
print("最终状态:", final_result["status"])
print("完整评论:", final_result["comments"])

# 手动更新状态 - 添加评论
print("\n=== 手动添加评论 ===")
app.update_state(config, {
    "comments": ["项目经理：请在周五前完成"],
    "priority": 2
})

# 查看更新后的状态
updated_state = app.get_state(config)
print(f"优先级: {updated_state.values['priority']}")
print("所有评论:", updated_state.values['comments'])

# 继续更新 - 添加更多评论
print("\n=== 添加更多评论 ===")
app.update_state(config, {
    "comments": ["张三：已完成开发"],
    "status": "开发完成"
})

# 查看最终状态
final_state = app.get_state(config)
print(f"最终状态: {final_state.values['status']}")
print("完整评论历史:", final_state.values['comments'])
```

![](LangGraph框架-mermaid-diagram-2026-04-16-204854.png)

## 记忆存储

![](LangGraph框架-image-6.png)

状态模式指定在图执行时填充的键集合。但如果我们想在线程之间保留信息怎么办？



Store 主要是存储用户画像【用户的行为习惯，用户的爱好、用户相关的一些重要的功能】

langgraph中对应store的介绍，就是为了跨会话知道之前用户的信息

### Store 接口

* 检查点保存器单独无法跨线程共享信息

* Store 接口解决了这个问题

* 可以在所有聊天对话中保留用户特定信息

### 基础用法

每种内存类型都是一个具有特定属性的 Python 类（`Item`）。我们可以通过上述转换将其作为字典访问`.dict`。它具有以下属性：

* `value`：此内存的值（本身就是一个字典）

* `key`：此命名空间中此内存的唯一键

* `namespace`：字符串列表，此内存类型的命名空间

* `created_at`：此内存创建的时间戳

* `updated_at`：此内存更新的时间戳

```python
print("-" * 8, "基础用法", "-" * 8)
from langgraph.store.memory import InMemoryStore
import uuid

# 创建存储
# in_memory_store = InMemoryStore()
#
# # 定义命名空间
# namespace_for_memory = ("user_id", "memories")
#
# # 存储记忆
# memory_id = str(uuid.uuid4())
# memory = {"hobby": "篮球、音乐、美食、编程..."}
# in_memory_store.put(namespace_for_memory, memory_id, memory)
#
# # 搜索记忆
# memories = in_memory_store.search(namespace_for_memory)
# # 打印数据
# print(memories[-1].dict())

print("-" * 8, "语义搜索", "-" * 8)
from langchain_huggingface import HuggingFaceEmbeddings

namespace_for_memory = ("user_id", "memories")

store = InMemoryStore(
    index={
        "embed": HuggingFaceEmbeddings(model_name=r"D:\llm\Local_model\BAAI\bge-large-zh-v1___5"),
        "dims": 1024,
        "fields": ["hobby", "food_preference"]
    }
)

# 3. 存储数据并检查
memory_id_1 = str(uuid.uuid4())
memory_1 = {"hobby": "我的爱好是：篮球、音乐、美食、编程..."}
store.put(namespace_for_memory, memory_id_1, memory_1)
print(f"✓ 存储 hobby 记忆: {memory_id_1}")

memory_id_2 = str(uuid.uuid4())
memory_2 = {"food_preference": "我最喜欢的美食是：臭豆腐、小龙虾、红烧肉..."}
store.put(namespace_for_memory, memory_id_2, memory_2)
print(f"✓ 存储 food_preference 记忆: {memory_id_2}")

# 4. 检查存储的数据
print("\n=== 调试信息 ===")
print(f"Namespace: {namespace_for_memory}")
print(f"存储的记忆数量: {len(store.search(namespace_for_memory))}")

# 5. 搜索测试
print("\n=== 搜索测试 ===")

# 测试 1: 搜索食物偏好
print("搜索: 用户喜欢吃什么？")
memories = store.search(
    namespace_for_memory,
    query="用户喜欢吃什么？",
    limit=3
)
print(f"搜索结果数量: {len(memories)}")
if memories:
    print(f"最相关结果: {memories[0].dict()}")
else:
    print("没有找到结果")

# 测试 2: 搜索爱好
print("\n搜索: 用户的爱好有哪些？")
memories = store.search(
    namespace_for_memory,
    query="用户的爱好有哪些？",
    limit=3
)
print(f"搜索结果数量: {len(memories)}")
if memories:
    print(f"最相关结果: {memories[0].dict()}")
else:
    print("没有找到结果")
```

### langgraph中使用存储功能

```python
from typing import Annotated, List
from typing_extensions import TypedDict
from operator import add
import uuid
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

# 初始化大模型
llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='qwen-plus-2025-01-25')


# 定义状态结构
class MessagesState(TypedDict):
    messages: Annotated[List[BaseMessage], add]


# 创建检查点保存器和内存存储
checkpointer = InMemorySaver()
in_memory_store = InMemoryStore()


# 聊天机器人节点  *代表后面的参数必须使用显示写出参数名称  store=in_memory_store
def chatbot(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    """主聊天机器人节点，处理用户消息并生成回复"""

    # 获取用户ID和最新消息
    user_id = config["configurable"]["user_id"]
    last_message = state["messages"][-1]

    # 定义内存命名空间
    namespace = (user_id, "memories")

    # 简单的聊天逻辑
    user_input = last_message.content.lower()
    # 将聊天历史获取并组装提示词
    memories = store.search(namespace)
    memory_text = "\n".join(m.value["memory"] for m in memories)
    prompt = f"请参考聊天记录：{memory_text}\n\nHuman: {user_input}\nAI:"

    response = llm.invoke(prompt).content

    # 存储对应的问题和答案
    memory = f"问题：{user_input} --- 答案:{response}"
    memory_id = str(uuid.uuid4())
    store.put(namespace, memory_id, {"memory": memory})
    # 返回AI消息
    return {"messages": [AIMessage(content=response)]}


# 创建图
def create_persistent_graph():
    """创建持久化的聊天机器人图"""

    # 创建状态图
    workflow = StateGraph(MessagesState)
    # 添加节点
    workflow.add_node("chatbot", chatbot)
    # 添加边
    workflow.add_edge(START, "chatbot")
    workflow.add_edge("chatbot", END)

    # 编译图，使用检查点保存器和存储
    graph = workflow.compile(checkpointer=checkpointer, store=in_memory_store)

    return graph


# 工具函数：显示状态历史
def show_state_history(graph, config):
    """显示状态历史"""
    print("\n=== 状态历史 ===")
    history = graph.get_state_history(config)
    for i, snapshot in enumerate(history):
        print(f"\n步骤 {i}:")
        print(f"  配置: {snapshot.config}")
        print(f"  值: {snapshot.values}")
        print(f"  下一步: {snapshot.next}")
        print(f"  元数据: {snapshot.metadata}")


# 工具函数：显示存储的记忆
def show_memories(store, user_id):
    """显示用户的所有记忆"""
    print(f"\n=== 用户 {user_id} 的记忆 ===")
    namespace = (user_id, "memories")
    memories = store.search(namespace)

    if memories:
        for memory in memories:
            print(f"记忆ID: {memory.key}")
            print(f"内容: {memory.value}")
            print(f"创建时间: {memory.created_at}")
            print(f"更新时间: {memory.updated_at}")
            print("---")
    else:
        print("没有找到记忆")


# 主程序
def main():
    # 创建图
    graph = create_persistent_graph()

    # 用户配置
    user_id = "user_123"
    thread_id = "conversation_1"

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id
        }
    }

    print("=== LangGraph 持久化聊天机器人 ===")
    print("输入 'quit' 退出，'history' 查看状态历史，'memories' 查看记忆")

    while True:
        user_input = input("\n用户: ").strip()

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'history':
            show_state_history(graph, config)
            continue
        elif user_input.lower() == 'memories':
            show_memories(in_memory_store, user_id)
            continue

        # 创建用户消息
        initial_state = {
            "messages": [HumanMessage(content=user_input)]
        }

        # 运行图
        try:
            result = graph.invoke(initial_state, config)

            # 显示AI回复
            ai_message = result["messages"][-1]
            print(f"AI: {ai_message.content}")

        except Exception as e:
            print(f"错误: {e}")

    print("\n=== 最终状态 ===")
    final_state = graph.get_state(config)
    print(f"最终状态: {final_state.values}")

    print("\n=== 所有记忆 ===")
    show_memories(in_memory_store, user_id)


# 演示不同线程间的记忆共享
def demo_cross_thread_memory():
    """演示跨线程记忆共享"""
    print("\n=== 跨线程记忆共享演示 ===")

    graph = create_persistent_graph()
    user_id = "user_456"

    # 第一个对话线程
    config1 = {
        "configurable": {
            "thread_id": "thread_1",
            "user_id": user_id
        }
    }

    print("线程1 - 建立记忆:")
    result1 = graph.invoke({
        "messages": [HumanMessage(content="我叫Alice，我喜欢音乐")]
    }, config1)
    print(f"AI: {result1['messages'][-1].content}")

    # 第二个对话线程（相同用户）
    config2 = {
        "configurable": {
            "thread_id": "thread_2",
            "user_id": user_id
        }
    }

    print("\n线程2 - 访问记忆:")
    result2 = graph.invoke({
        "messages": [HumanMessage(content="你还记得我吗？")]
    }, config2)
    print(f"AI: {result2['messages'][-1].content}")

    # 显示共享的记忆
    show_memories(in_memory_store, user_id)


if __name__ == "__main__":
    # 运行主程序
    main()

    # 演示跨线程记忆共享
    demo_cross_thread_memory()
```

**InMemorySaver和InMemoryStore的使用场景**：

InMemorySaver短期记忆：存储每个节点执行完成之后的状态（聊天历史）

InMemoryStore长期记忆：跨会话（线程），存储用户相关的内容

# 流式输出

LangGraph 实施了流式系统来显示实时更新，从而实现响应迅速且透明的用户体验。

LangGraph 的流式传输系统可将图形运行的实时反馈显示到您的应用中。

**流式输出在LangGraph中的重要性：**

⚡ 用户立即看到反馈

🎯 减少等待时间

💾 节省内存使用

😊 提升用户体验

将以下一个或多个流模式作为列表传递给`stream()`或`astream()`方法：

## 流输出格式（V2版本）

> 需要 LangGraph >= 1.1。

`v2`版本主要就是统一不同流式输出的返回格式，每个数据块都是一个`StreamPart`结构一致的字典。

**和v1版本的区别：**

## 几种模式代码详解

```python
from typing import Annotated
import operator
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Send
from typing import TypedDict, List

"""---------------------------values、updates、debug模式---------------------------"""


# 状态定义
class State(TypedDict):
    numbers: List[int]  # 输入的数字
    results: Annotated[list[int], operator.add]  # worker的结果
    final_sum: int  # 最终求和


# 1. Map阶段：分发数字
def split_numbers(state: State):
    """把数字分发给不同的worker"""
    numbers = state["numbers"]

    # 每个数字发给一个worker
    return [Send("worker", {"number": num}) for num in numbers]


# 2. Worker阶段：计算平方
def calculate_square(state: State):
    """每个worker计算一个数字的平方"""
    number = state["number"]
    square = number * number
    return {"results": [square]}


# 3. Reduce阶段：求和
def sum_results(state: State):
    """把所有结果加起来"""
    results = state.get("results", [])
    total = sum(results)
    return {"final_sum": total}


# 构建图
def create_simple_graph():
    graph = StateGraph(state_schema=State)

    # 添加节点
    graph.add_node("splitter", lambda s: s)  # 分发器
    graph.add_node("worker", calculate_square)  # 工作节点
    graph.add_node("summer", sum_results)  # 求和器

    # 连接节点
    graph.add_edge(START, "splitter")
    graph.add_conditional_edges("splitter", split_numbers, ["worker"])  # Map阶段
    graph.add_edge("worker", "summer")  # Worker完成后求和
    graph.add_edge("summer", END)

    return graph.compile()


"""---------------------------messages模式---------------------------"""
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

llm1 = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                       base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                       model_provider="openai",
                       model='MiniMax-M2.1')

class MyState(TypedDict):
    question: str
    results: str


def generate_answer(state: MyState):
    question = state["question"]
    answer = llm1.invoke([
        {"role": "user", "content": f"{question}"}
    ])
    return {"answer": answer.content}

def generate_answer1(state: MyState):
    answer = llm1.invoke([
        {"role": "user", "content": f"你好"}
    ])
    return {"answer": answer.content}


# 构建图
def create_llm_graph():
    graph = StateGraph(state_schema=MyState)

    # 添加节点
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("generate_answer1", generate_answer1)

    # 连接节点
    graph.add_edge(START, "generate_answer")
    graph.add_edge("generate_answer", "generate_answer1")
    graph.add_edge("generate_answer", END)

    return graph.compile()


"""---------------------------自定义模式---------------------------"""

from langgraph.config import get_stream_writer
import time


# 定义状态
class FileState(TypedDict):
    filename: str  # 文件名称
    content: str  # 文件内容
    word_count: int  # 内容数量
    processed: bool  # 是否处理完成


def read_file(state: FileState):
    """步骤1：读取文件"""
    writer = get_stream_writer()
    # 发送开始信息
    writer({"step": "读取文件", "status": "开始", "progress": 0})
    time.sleep(1)

    # 发送进度信息
    writer({"step": "读取文件", "status": "正在读取...", "progress": 50})
    time.sleep(1)

    # 模拟文件内容
    content = "这是一个示例文件，包含一些文本内容。"

    # 发送完成信息
    writer({
        "step": "读取文件",
        "status": "完成",
        "progress": 100,
        "data": {"size": len(content)}
    })

    return {"content": content}


def count_words(state: FileState):
    """步骤2：统计字数"""
    writer = get_stream_writer()
    writer({"step": "统计字数", "status": "开始", "progress": 0})
    time.sleep(0.5)

    writer({"step": "统计字数", "status": "正在分析...", "progress": 30})
    time.sleep(1)

    writer({"step": "统计字数", "status": "计算中...", "progress": 70})
    time.sleep(0.5)

    # 计算字数
    word_count = len(state["content"])

    writer({
        "step": "统计字数",
        "status": "完成",
        "progress": 100,
        "data": {"word_count": word_count}
    })

    return {"word_count": word_count}


def finalize_processing(state: FileState):
    """步骤3：完成处理"""
    writer = get_stream_writer()
    writer({"step": "完成处理", "status": "生成报告", "progress": 50})
    time.sleep(1)

    writer({
        "step": "完成处理",
        "status": "全部完成",
        "progress": 100,
        "data": {
            "filename": state["filename"],
            "total_chars": state["word_count"],
            "summary": f"文件 {state['filename']} 处理完成，共 {state['word_count']} 个字符"
        }
    })

    return {"processed": True}


# 构建图
def create_custom_graph():
    graph = (
        StateGraph(state_schema=FileState)
        .add_node("read_file", read_file)
        .add_node("count_words", count_words)
        .add_node("finalize", finalize_processing)
        .add_edge(START, "read_file")
        .add_edge("read_file", "count_words")
        .add_edge("count_words", "finalize")
        .compile()
    )
    return graph


"""---------------------------checkpoints、tasks模式---------------------------"""
# 需要提供检查点
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='MiniMax-M2.1')


# 创建子图
def subplot(state: MessagesState) -> MessagesState:
    # 获取大模型回答的内容进行摘要总结
    answer = state["messages"][-1].content
    summary_prompt = f"请用一句话总结下面这句话：\n\n答：{answer}"
    response = llm.invoke(summary_prompt)
    return {"messages": [response]}


summary_subgraph = (
    StateGraph(state_schema=MessagesState)
    .add_node("subplot", subplot)
    .add_edge(START, "subplot")
    .add_edge("subplot", END)
    .compile()
)


# 创建父图
def llm_answer_node(state: MessagesState) -> MessagesState:
    # 使用大模型进行回答
    answer = llm.invoke(state["messages"])
    return {"messages": [answer]}


checkpointer = InMemorySaver()

# 构建图
def create_check_tasks_graph():
    parent_graph = (
        StateGraph(MessagesState)
        .add_node("llm_answer", llm_answer_node)
        .add_node("summarize_subgraph", summary_subgraph)
        .add_edge(START, "llm_answer")
        .add_edge("llm_answer", "summarize_subgraph")
        .compile(checkpointer=checkpointer)
    )
    return parent_graph


# 运行例子
def run_example():
    app = create_simple_graph()  # values、updates、debug模式案例
    app1 = create_llm_graph()  # messages模式
    app2 = create_custom_graph()  # 自定义模式
    app3 = create_check_tasks_graph()  # checkpoints、tasks模式

    # 测试数据
    initial_state = {
        "numbers": [1, 2, 3, 4, 5],
        "results": [],
        "final_sum": 0
    }

    # print("====================VALUES模式=====================")
    # for result in app.stream(initial_state, stream_mode="values", version="v2"):
    #     print(result)
    #
    # print("====================UPDATES模式=====================")
    # for result in app.stream(initial_state, stream_mode="updates", version="v2"):
    #     print(result)
    #
    # print("====================DEBUG模式=====================")
    # for result in app.stream(initial_state, stream_mode="debug", version="v2"):
    #     print(result)

    # print("====================MESSAGES模式=====================")
    # for chunk in app1.stream({"question": "什么是状态图？"}, stream_mode="messages", version="v2"):
    #     if chunk["type"] == "messages":
    #         result, metadata = chunk["data"]
    #         if metadata["langgraph_node"] == "generate_answer":
    #             print(result.content, end="", flush=True)
    #         # print(metadata)

    # print("====================CUSTOM模式=====================")
    # # 初始状态
    # initial_state1 = {
    #     "filename": "example.txt",
    #     "content": "",
    #     "word_count": 0,
    #     "processed": False
    # }
    # # 使用Custom模式运行
    # for chunk in app2.stream(initial_state1, stream_mode="custom", version="v2"):
    #     if chunk["type"] == "custom":
    #         data = chunk["data"]
    #         step = data.get("step", "")  # 当前步骤
    #         status = data.get("status", "")  # 目前状态
    #         progress = data.get("progress", 0)  # 完成进度
    #         data_result = data.get("data", {})  # 最终数据
    #
    #         # 显示进度
    #         progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
    #         print(f"\n[{step}] {status}")
    #         print(f"进度: [{progress_bar}] {progress}%")
    #
    #         # 显示额外数据
    #         if data_result:
    #             for key, value in data_result.items():
    #                 print(f"{key}: {value}")

    print("====================checkpoints、tasks模式=====================")

    config = {"configurable": {"thread_id": "1"}}
    # 测试输入
    input_state = {
        "messages": [{"role": "user", "content": "langgraph是什么？请用100字介绍"}],
    }

    for chunk in app3.stream(
            input_state,
            config,
            stream_mode="tasks",  # tasks  |  checkpoints
            subgraphs=True  # 如果要子图也进行流式输出，需要开启
    ):
        print(chunk)



if __name__ == "__main__":
    run_example()
```

## 融合多种模式

可以传递一个列表作为`stream_mode`参数来同时传输多种模式

输出将是流模式名称和`(mode, chunk)`

```python
from typing import TypedDict
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
import os

load_dotenv()


# ==========================================
# 1. 定义状态和工具
# ==========================================

class EditorState(TypedDict):
    topic: str  # 主题
    content: str  # 生成的内容
    score: int  # 评分
    status: str  # 当前状态描述


llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                       base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                       model_provider="openai",
                       model='qwen-plus-2025-07-28', )


# ==========================================
# 2. 定义节点逻辑
# ==========================================

def write_article(state: EditorState):
    """节点1：负责写文章（耗时操作，会有流式输出）"""
    topic = state["topic"]
    # 这里我们用 invoke，依靠 stream_mode="messages" 来捕获流
    response = llm.invoke(f"请写一段关于'{topic}'的短文，50字左右。")
    return {
        "content": response.content,
        "status": "写作完成"
    }


def review_article(state: EditorState):
    """节点2：负责打分（逻辑操作，瞬间完成）"""
    # 简单模拟打分逻辑
    content_len = len(state["content"])
    score = min(100, content_len * 2)
    return {
        "score": score,
        "status": "评分完成"
    }


# ==========================================
# 3. 构建图
# ==========================================

workflow = StateGraph(EditorState)

workflow.add_node("writer", write_article)
workflow.add_node("reviewer", review_article)

workflow.add_edge(START, "writer")
workflow.add_edge("writer", "reviewer")
workflow.add_edge("reviewer", END)

app = workflow.compile()


# ==========================================
# 4. 核心：融合流式输出处理
# ==========================================

def run_mixed_mode_demo():
    inputs = {
        "topic": "人工智能的未来",
        "content": "",
        "score": 0,
        "status": "开始任务"
    }

    print(f"🚀 任务启动：主题 - {inputs['topic']}\n")
    print("-" * 50)

    # 🌟 关键点：传入一个列表 ["messages", "updates", "values"]
    # 这样 app.stream 会返回一个元组：(mode, chunk)
    for mode, chunk in app.stream(inputs, stream_mode=["messages", "updates", "values"]):

        # --- 模式 A: Messages (处理打字机效果) ---
        if mode == "messages":
            # chunk 结构是 (message, metadata)
            message, metadata = chunk
            # 只显示 AI 生成的内容，过滤掉系统消息等
            if message.content:
                print(message.content, end="", flush=True)

        # --- 模式 B: Updates (处理节点完成通知) ---
        elif mode == "updates":
            # chunk 是该节点刚刚更新的字段
            # 这里的 chunk 类似于Key-Value：{'writer': {'content': '...', 'status': '...'}}
            node_name = list(chunk.keys())[0]
            updates = chunk[node_name]
            print(f"\n\n✅ [节点完成] {node_name} -> 状态: {updates.get('status')}")
            if "score" in updates:
                print(f"📊 [评分结果] 得分: {updates['score']}")
            print("-" * 50)  # 分割线

        # --- 模式 C: Values (处理全局状态快照) ---
        elif mode == "values":
            # chunk 是当前的完整 State
            print(f"\n📦 [全量状态快照] {chunk}")

    print("\n🎉 流程结束！")


if __name__ == "__main__":
    run_mixed_mode_demo()
```

## 从工具中流式传输数据

```python
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.config import get_stream_writer
from langchain_core.tools import tool
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='qwen-plus-2025-01-25')


# 定义工具函数
@tool
def search_web(query: str):
    """搜索网络信息的工具"""
    writer = get_stream_writer()
    writer({"step": "搜索", "status": "请等待...", "progress": 0})
    time.sleep(0.5)

    writer({"step": "搜索", "status": "请等待...", "progress": 50})
    time.sleep(0.5)

    writer({
        "step": "搜索",
        "status": "完成",
        "progress": 100,
        "data": {"结果": TavilySearch().invoke(query)}
    })


@tool
def get_data_tool():
    """获取目前日期的工具"""
    return datetime.now().date()


tools = [search_web, get_data_tool]

system_prompt = """你是一个智能助手。你有以下工具可以使用：

1. search_web: 用于搜索互联网获取最新信息，特别是产品价格、新闻、实时数据等
2. get_current_date: 获取今天的日期

重要规则：
- 当用户询问产品价格、最新信息、新闻等需要实时数据的问题时，必须使用search_web工具
- 当用户询问时间或日期时，使用相应的时间工具
- 如果你的知识库中没有准确或最新的信息，应该使用搜索工具
- 优先使用工具获取准确信息，而不是依赖可能过时的训练数据

请根据用户问题选择合适的工具来获取准确答案。"""

agent = create_react_agent(model=llm,
                           tools=tools,
                           prompt=system_prompt
                           )

for chunk in agent.stream({"messages": [{"role": "user", "content": "小米yu7价格"}]}, stream_mode="custom"):
    step = chunk.get("step", "")
    status = chunk.get("status", "")
    progress = chunk.get("progress", 0)
    data = chunk.get("data", {})

    # 显示进度
    progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
    print(f"\n[{step}] {status}")
    print(f"进度: [{progress_bar}] {progress}%")

    # 显示额外数据
    if data:
        for key, value in data.items():
            print(f"📊 {key}: {value}")
```

## 禁用特定聊天模型的流式传输

如果您的应用程序将支持流式传输的模型与不支持流式传输的模型混合使用，则可能需要明确禁用不支持流式传输的模型。

```python
model = init_chat_model(    
    "anthropic:claude-3-7-sonnet-latest",    
    disable_streaming=True 
)
```

# **<span style="color: rgb(216,57,49); background-color: inherit">记忆（重点）</span>**

对于人工智能代理来说，记忆至关重要，因为它能让它们记住之前的交互，从反馈中学习，并适应用户的偏好。随着代理需要处理更复杂的任务，并进行大量的用户交互，这种能力对于效率和用户满意度都至关重要。

* 短期记忆（或线程范围的记忆）通过维护会话中的消息历史记录来跟踪正在进行的对话。LangGraph 将短期记忆作为代理状态的一部分进行管理。状态使用检查点持久化到数据库中，以便线程可以随时恢复。短期记忆会在图被调用或某个步骤完成时更新，并且在每个步骤开始时读取状态。

* 长期记忆跨会话存储用户特定或应用程序级别的数据，并在对话线程之间共享。它可以在任何时间、任何线程中调用。记忆的作用域是任何自定义命名空间，而不仅仅是单个线程 ID。LangGraph 提供存储，方便您保存和调用长期记忆。

![](LangGraph框架-image-7.png)

## 使用redis作为存储

```python
pip install -U langgraph-checkpoint-redis
```

```python
import uuid
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore
from langgraph.runtime import Runtime
from dataclasses import dataclass

load_dotenv()

# --- 1. 初始化模型 ---
llm = init_chat_model(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_provider="openai",
    model='MiniMax-M2.1'
)


@dataclass
class Context:
    user_id: str


# --- 2. 定义节点逻辑 ---
def call_model(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    namespace = ("memories", user_id)

    # 检索长期记忆
    last_user_msg = state["messages"][-1].content
    memories = runtime.store.search(namespace, query=str(last_user_msg))
    info = "\n".join([d.value["data"] for d in memories])

    system_msg = f"你是一个有帮助的助手。已知用户信息: {info}"

    # 逻辑存储：如果用户说“记住...”，则存入 Store
    if "记住" in last_user_msg:
        # 简单提取“记住”后面的内容（实际生产可用LLM提取）
        memory_content = last_user_msg.replace("记住", "").strip("：: ")
        runtime.store.put(namespace, str(uuid.uuid4()), {"data": memory_content})
        print(f"--- [系统日志] 已存入长期记忆: {memory_content} ---")

    response = llm.invoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )
    return {"messages": response}


# --- 3. 构建图 ---
DB_URI = "redis://localhost:6379"

# 使用 context manager 保持连接
with RedisStore.from_conn_string(DB_URI) as store, \
        RedisSaver.from_conn_string(DB_URI) as checkpointer:
    # 第一次初始化的时候需要
    checkpointer.setup()
    store.setup()

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    graph = builder.compile(checkpointer=checkpointer, store=store)

    # --- 4. 交互循环 ---
    current_thread_id = "1"
    current_user_id = "user_v1"

    print("=== LangGraph 交互系统 ===")
    print("指令说明: 输入 'switch' 切换会话, 'exit' 退出程序")

    while True:
        prompt = f"\n[当前线程: {current_thread_id}] 用户: "
        user_input = input(prompt).strip()

        if user_input.lower() == 'exit':
            break

        if user_input.lower() == 'switch':
            new_id = input("请输入新的 Thread ID (例如 1, 2, 3): ")
            current_thread_id = new_id
            print(f"--- 已切换到线程 {current_thread_id} ---")
            continue

        if not user_input:
            continue

        # 构建配置
        config = {
            "configurable": {
                "thread_id": current_thread_id,
                "user_id": current_user_id,
            }
        }

        # 执行流式输出（使用 values 模式）
        # 注意：由于我们要手动输入，每次流只传入当前这一条消息
        for chunk in graph.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config,
                context=Context(user_id=current_user_id),
                stream_mode="messages",
                version="v2"
        ):
            if chunk["type"] == "messages":
                result, metadata = chunk["data"]
                print(result.content, end="", flush=True)
```

## **使用Postgres作为存储**

下载postgresSql，数据库存储是的加密数据。

```python
# 1.使用docker下载对应镜像
docker pull postgres:alpine # 这边使用的是体积更小的镜像

# 2.运行对应镜像
docker run -id --name=postgresql -v postgre-data:/var/lib/postgresql/data -p 5432:5432 -e POSTGRES_PASSWORD=123456 -e LANG=C.UTF-8 postgres:alpine

```

```python
pip install -U "psycopg[binary,pool]" langgraph-checkpoint-postgres
```

```python
import uuid
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.runtime import Runtime
from dataclasses import dataclass

load_dotenv()

# --- 1. 初始化模型 ---
llm = init_chat_model(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_provider="openai",
    model='MiniMax-M2.1'
)


@dataclass
class Context:
    user_id: str


# --- 2. 定义节点逻辑 ---
def call_model(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    namespace = ("memories", user_id)

    # 检索长期记忆
    last_user_msg = state["messages"][-1].content
    memories = runtime.store.search(namespace, query=str(last_user_msg))
    info = "\n".join([d.value["data"] for d in memories])

    system_msg = f"你是一个有帮助的助手。已知用户信息: {info}"

    # 逻辑存储：如果用户说“记住...”，则存入 Store
    if "记住" in last_user_msg:
        # 简单提取“记住”后面的内容（实际生产可用LLM提取）
        memory_content = last_user_msg.replace("记住", "").strip("：: ")
        runtime.store.put(namespace, str(uuid.uuid4()), {"data": memory_content})
        print(f"--- [系统日志] 已存入长期记忆: {memory_content} ---")

    response = llm.invoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )
    return {"messages": response}


# --- 3. 构建图 ---
DB_URI = "postgresql://postgres:123456@localhost:5432/postgres?sslmode=disable"

# 使用 context manager 保持连接
with PostgresStore.from_conn_string(DB_URI) as store, \
        PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # 第一次初始化的时候需要
    checkpointer.setup()
    store.setup()

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    graph = builder.compile(checkpointer=checkpointer, store=store)

    # --- 4. 交互循环 ---
    current_thread_id = "1"
    current_user_id = "user_v1"

    print("=== LangGraph 交互系统 ===")
    print("指令说明: 输入 'switch' 切换会话, 'exit' 退出程序")

    while True:
        prompt = f"\n[当前线程: {current_thread_id}] 用户: "
        user_input = input(prompt).strip()

        if user_input.lower() == 'exit':
            break

        if user_input.lower() == 'switch':
            new_id = input("请输入新的 Thread ID (例如 1, 2, 3): ")
            current_thread_id = new_id
            print(f"--- 已切换到线程 {current_thread_id} ---")
            continue

        if not user_input:
            continue

        # 构建配置
        config = {
            "configurable": {
                "thread_id": current_thread_id,
                "user_id": current_user_id,
            }
        }

        # 执行流式输出（使用 values 模式）
        # 注意：由于我们要手动输入，每次流只传入当前这一条消息
        for chunk in graph.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config,
                context=Context(user_id=current_user_id),
                stream_mode="messages",
                version="v2"
        ):
            if chunk["type"] == "messages":
                result, metadata = chunk["data"]
                print(result.content, end="", flush=True)
```

**生产环境推荐配置：短期记忆用redis + 长期记忆用postgres**

### 具有语义搜索的记忆

```python
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chat_models import init_chat_model
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.graph import START, MessagesState, StateGraph
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='qwen-plus-2025-01-25')

# 加载嵌入模型
embeddings = HuggingFaceEmbeddings(model_name=r"D:\llm\Local_model\BAAI\bge-large-zh-v1___5")
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1024,
    }
)

store.put(("memories", "user_123"), "1", {"text": "我喜欢吃披萨"})
store.put(("memories", "user_123"), "2", {"text": "我喜欢吃红烧肉"})
store.put(("memories", "user_123"), "3", {"text": "我的职业是程序员"})

def chat(state, *, store: BaseStore):
    # 根据用户的最后一条消息进行搜索
    items = store.search(
        ("memories","user_123"), query=state["messages"][-1].content, limit=2
    )
    print(items)
    memories = "\n".join(item.value["text"] for item in items)
    memories = f"## 用户记忆\n{memories}" if memories else ""
    response = llm.invoke(
        [
            {"role": "system", "content": f"你是一个乐于助人的助手.\n{memories}"},
    
        ] + state["messages"]
    )
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node(chat)
builder.add_edge(START, "chat")
graph = builder.compile(store=store)

for message, metadata in graph.stream(
    input={"messages": [{"role": "user", "content": "我饿了？"}]},
    stream_mode="messages",
):
    print(message.content, end="")
```

## 管理短期记忆

启用短期记忆后，长对话可能会超出 LLM 的上下文窗口。常见的解决方案如下：

* 修剪消息：删除前 N 条或后 N 条消息（在调用 LLM 之前）

* 从 LangGraph 状态中永久删除消息

* 总结消息：总结历史记录中较早的消息，并用摘要替换它们

* 管理检查点以存储和检索消息历史记录

* 自定义策略（例如，消息过滤等）

### 修剪消息

大多数 LLM 都有一个最大支持的上下文窗口（以 token 为单位）。决定何时截断消息的一种方法是计算消息历史记录中的 token 数量，并在接近该限制时进行截断。

```python
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, MessagesState
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='MiniMax-M2.1')


def call_llm(state: MessagesState):
    messages = trim_messages(
        state["messages"],
        strategy="last",  # 修剪策略（last从末尾，first从开头， middle从中间）
        token_counter=count_tokens_approximately,  # 用来估算token数量
        max_tokens=100,  # 修剪后的消息总 token 不超过 200
        start_on="human",  # 控制从哪一类消息开始截取（从最后一个 human 消息开始往前保留）
        end_on=("human", "ai"),  # 允许哪些角色作为修剪终点
    )
    print("修剪后的消息：", messages)
    response = llm.invoke(messages)
    return {"messages": [response]}


checkpointer = InMemorySaver()
builder = StateGraph(MessagesState)
builder.add_node(call_llm)
builder.add_edge(START, "call_llm")
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}
graph.invoke({"messages": "我的名字叫初见"}, config)
graph.invoke({"messages": "帮我家的猫写一首诗"}, config)
graph.invoke({"messages": "现在对狗做一样的事情"}, config)
final_response = graph.invoke({"messages": "我的名字叫什么?"}, config)

print("最终消息：")
print(final_response["messages"])
```

### 删除消息

可以从图表状态中删除消息，以管理消息历史记录。当您想要移除特定消息或清除整个消息历史记录时，此功能非常有用。

```python
from langchain_core.messages import RemoveMessage
from langgraph.graph import StateGraph, START, MessagesState
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='qwen-plus-2025-01-25')


def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # 删除最早的两条消息
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}
    return None


def call_llm(state: MessagesState):
    response = llm.invoke(state["messages"])
    return {"messages": response}


builder = StateGraph(MessagesState)
builder.add_sequence([call_llm, delete_messages])
builder.add_edge(START, "call_llm")

checkpointer = InMemorySaver()
app = builder.compile(checkpointer=checkpointer)

config = {
    "configurable": {
        "thread_id": "1"
    }
}

for event in app.stream(
        {"messages": [{"role": "user", "content": "你好呀，我是初见哦"}]},
        config,
        stream_mode="values"
):
    print([(message.type, message.content) for message in event["messages"]])

for event in app.stream(
        {"messages": [{"role": "user", "content": "我的名字是什么？"}]},
        config,
        stream_mode="values"
):
    # 最终回复会把最开始的两条消息删除
    print([(message.type, message.content) for message in event["messages"]])
```

### 总结消息

修剪或删除消息的问题在于，可能会因剔除消息队列而丢失信息。因此，一些应用程序受益于一种更复杂的方法，即使用聊天模型来汇总消息历史记录。

![](LangGraph框架-image-8.png)

下载模块

```python
pip install langmem
```

```python
from typing import Any, TypedDict
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langmem.short_term.summarization import SummarizationNode, RunningSummary
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer  # 给RunningSummary加到检查点的序列化中
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='MiniMax-M2.1')

# 创建一个专用于摘要的模型实例，限制输出最多 128 tokens
summarization_model = llm.bind(max_tokens=128)  # 是控制MiniMax-M2.1最大的输出


# 定义状态结构，包含对话历史和摘要上下文
class State(MessagesState):
    context: dict[str, RunningSummary]  # 用于存储用户摘要记忆（running_summary）


# 定义输入格式，传给 call_model 函数使用
class LLMInputState(TypedDict):
    summarized_messages: list[AnyMessage]  # 已被压缩/摘要过的消息
    context: dict[str, RunningSummary]


# 首次生成摘要
initial_summary_prompt = ChatPromptTemplate.from_template(
    """请阅读以下对话内容，并生成一个简洁的摘要，用于帮助理解对话的主要内容：

对话内容：
{messages}

摘要："""
)

# 在已有摘要基础上追加新的对话内容，更新摘要
existing_summary_prompt = ChatPromptTemplate.from_template(
    """【重要】你需要生成一个新的摘要来完全替换旧的摘要，而不是在旧摘要后面追加内容。

旧的摘要（将被完全替换）：
{existing_summary}

新发生的对话：
{messages}

请根据旧摘要和新对话，生成一个全新的、精简的摘要。新摘要必须：
1. 覆盖所有关键信息（用户身份、重要问题、关键结论）
2. 只输出摘要本身，不要有任何额外说明

新摘要：""")

# 用于最终调用模型之前，将摘要和剩余消息一起传入模型
final_prompt = ChatPromptTemplate.from_template(
    """你是一位智能助理。以下是用户和你的对话摘要，可帮助你快速理解上下文：

摘要：
{summary}

这是对话中未被总结的新消息，请继续处理这些信息：
{messages}
"""
)
# 创建摘要节点：超过一定 token 数时会对历史消息自动进行摘要
summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,  # 使用近似 token 计算
    model=summarization_model,  # 使用绑定了 max_tokens 的模型
    max_tokens=200,  # 在进行摘要之前，传给模型的输入上下文的最大token长度限制
    max_tokens_before_summary=50,  # 超过这个数就会触发摘要
    max_summary_tokens=128,  # 每次摘要最多保留 128 tokens
    initial_summary_prompt=initial_summary_prompt,  # 首次生成摘要的提示词
    existing_summary_prompt=existing_summary_prompt,  # 更新摘要的提示词
    final_prompt=final_prompt  # 模型回答问题之前参考的摘要上下文的提示词
)


# max_tokens：在进入摘要模型之前：已有的摘要+用户问题<=200
# max_tokens_before_summary：当前对话[AI, Human, tools, AI, Human, tools]tokens长度大于50就触发摘要
# max_summary_tokens：摘要的长度 128 tokens

# 做对话的应用，max_tokens_before_summary=2000左右；max_tokens=3000-6000左右；max_summary_tokens=1000左右

# 摘要 + 用户的问题 -> llm摘要   # 摘要 + 用户的问题在重新进行摘要不能超过200token，超过的会被舍弃掉

# 本质是维护了一个摘要字段，每次摘要都是把  新摘要+原有的摘要（追加）

# 开发一个专门做摘要的子图（公用的摘要工具）
# 1.控制阈值
# 2.用llm去进行摘要（保存到数据库中，加载已有的摘要）
# 3.返回当前摘要的内容给主节点      cursor，对话超出多少之后，也是做摘要

# 每个会话，限制一个长度


# 模型调用节点：对压缩过的历史消息进行问答
def call_llm(state: LLMInputState):
    response = llm.invoke(state["summarized_messages"])
    for i, msg in enumerate(state["summarized_messages"]):
        print(f"  [{i}] {msg.type}: {msg.content}...")

    print(f"messages : {[response]}")
    print(f"context : {state.get('context', {})}")
    print("-" * 60)
    return {
        "messages": [response],
        "context": state.get("context", {})  # 把上下文原样返回，里面就有摘要
    }


# 使用内存存储器（可换成 Redis/Postgres）
checkpointer = InMemorySaver(serde=JsonPlusSerializer(allowed_msgpack_modules=[RunningSummary])) # 给RunningSummary加到检查点的序列化中

# 构建 LangGraph 的流程图
builder = StateGraph(State)

# 添加两个节点：摘要节点 和 模型调用节点
builder.add_node(call_llm)
builder.add_node("summarize", summarization_node)

# 定义边：从 START 开始 → 先摘要 → 再模型调用
builder.add_edge(START, "summarize")
builder.add_edge("summarize", "call_llm")

# 编译图
graph = builder.compile(checkpointer=checkpointer)

# ========== 流程调用 ==========
config = {"configurable": {"thread_id": "1"}}  # 每个线程维护一个上下文

# 第1轮：告诉模型「我叫小明」
graph.invoke({"messages": "你好，我叫初见，我是一个大模型开发"}, config)

# 第2轮：要求写一首猫的诗
graph.invoke({"messages": "请写一首关于猫的诗"}, config)

# 第3轮：让它对狗做一样的事
graph.invoke({"messages": "现在也请为狗写一首诗"}, config)

# 第4轮：问它「我叫什么名字？」
final_response = graph.invoke({"messages": "你还记得我叫什么名字吗？"}, config)

# 输出最终回复
final_response["messages"][-1].pretty_print()

# 输出摘要内容（短期记忆）
print("\n摘要记忆内容（summary）:", final_response)
```

# 工具

**工具**封装了可调用函数及其输入模式。这些可以传递给兼容的聊天模型，让模型决定是否调用工具以及使用哪些参数。

![](LangGraph框架-image-9.png)

## 预建工具

LangChain 为常见的外部系统（包括 API、数据库、文件系统和 Web 数据）提供预构建的工具集成。

浏览[集成目录](https://python.langchain.com/docs/integrations/tools/)以查找可用的工具。

常见类别：

* **搜索**：Bing、SerpAPI、Tavily

* **代码执行**：Python REPL、Node.js REPL

* **数据库**：SQL、MongoDB、Redis

* **Web 数据**：抓取和浏览

* **API**：OpenWeatherMap、NewsAPI等。

## 自定义工具

使用@tool装饰器来定义工具

```python
from langchain.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """将两个数目相乘."""
    return a * b


# 运行工具
print(multiply.invoke({"a": 6, "b": 7}))  # returns 42

tool_call = {
    "type": "tool_call",
    "id": "1",
    "args": {"a": 42, "b": 7}
}
print(multiply.invoke(tool_call))

print("=" * 8, "在工作流中使用", "=" * 8)

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_tavily import TavilySearch


@tool
def tavily_search_tool(query: str) -> str:
    """这是一个搜索工具"""
    tool_instance = TavilySearch()
    return tool_instance.run(query)

# 执行工具的节点
tool_node = ToolNode([tavily_search_tool])
# 绑定工具到模型
model_with_tools = llm.bind_tools([tavily_search_tool])


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)

# 定义节点和边
builder.add_node("call_model", call_model)  
builder.add_node("tools", tool_node)

builder.add_edge(START, "call_model")  # 模型因为绑定了工具，决定是否要使用工具，返回：tool message
builder.add_conditional_edges("call_model", should_continue, ["tools", END])
builder.add_edge("tools", "call_model")

graph = builder.compile()

print(graph.invoke({"messages": [{"role": "user", "content": "上海的天气?"}]}))
```

> 用户输入："上海的天气？"
>
> &#x20;       ↓
>
> 🧠 call\_model 节点
>
> * 使用绑定了工具的 LLM（model\_with\_tools）调用模型
>
> * 模型判断是否需要工具（如搜索）
>
> * 如果有 tool\_calls，走向 tools 节点
>
> * 否则直接结束
>
>   &#x20;     ↓
>
> 🔧 tools 节点（ToolNode）
>
> * 检查模型返回是否有 tool\_calls（如 tavily\_search\_tool）
>
> * 执行对应工具（如 TavilySearch.run(query)）
>
> * 工具执行结果构建成 AI Message 返回
>
>   &#x20;     ↓
>
> 🧠 再次回到 call\_model（循环处理新消息）
>
> * 把 tool\_result 消息输入给模型，继续推理
>
> &#x20;     ↓
>
> ✅ END（当模型不再调用工具，流程结束）

## 工具定制

### 参数说明

```python
from langchain_core.tools import tool

@tool("multiply_tool", parse_docstring=True)
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First operand
        b: Second operand
    """
    return a * b
```

### 显式输入模式

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class MultiplyInputSchema(BaseModel):
    """Multiply two numbers"""
    # 通过创建一个类继承BaseModel去作为参数验证和工具描述
    a: int = Field(description="First operand")
    b: int = Field(description="Second operand")

@tool("multiply_tool", args_schema=MultiplyInputSchema)
def multiply(a: int, b: int) -> int:
    return a * b
```

## 上下文管理

LangGraph 中的工具有时需要上下文数据，例如仅在运行时使用的参数（例如，用户 ID 或会话详细信息、状态等），这些数据不应由模型控制。LangGraph 提供了三种方法来管理此类上下文：

### 短期记忆

短期记忆保持在单次执行期间发生变化的**动态状态**

```python
import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

load_dotenv()

# 1. 初始化模型
llm = init_chat_model(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_provider="openai",
    model='MiniMax-M2.1'
)


# 2. 定义状态 (State)
class CustomState(MessagesState):
    user_name: str


# 3. 定义工具
@tool
def get_user_name(runtime: ToolRuntime) -> str:
    """从状态中检索当前用户名。"""
    # 在 LangGraph 中，可以通过 InjectedState 注入整个状态
    return runtime.state.get("user_name", "未知用户")


@tool
def update_user_name(new_name: str, runtime: ToolRuntime) -> Command:
    """更新短期记忆中的用户名。"""
    print(f"--- 触发更新用户名工具: {new_name} ---")
    # Command 会在工具执行完后直接作用于 Graph 的 State
    return Command(
        update={
            "user_name": new_name,
            "messages": [
                ToolMessage(
                    content=f"姓名已经更改成： {new_name}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


tools = [get_user_name, update_user_name]
llm_with_tools = llm.bind_tools(tools)


# 4. 定义节点函数
def call_model(state: CustomState):
    """模型决策节点"""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# 5. 构建图 (Workflow)
workflow = StateGraph(CustomState)

# 添加处理节点
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# 设置连线
workflow.add_edge(START, "agent")

# 动态决定：是去执行工具还是直接结束
workflow.add_conditional_edges(
    "agent",
    tools_condition,  # 内置函数：判断消息中是否有 tool_calls
    {"tools": "tools", "__end__": END},
)

# 工具执行完后回到 agent，让模型根据工具结果说话
workflow.add_edge("tools", "agent")

# 6. 编译并运行
checkpointer = InMemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# --- 测试运行 ---
config = {"configurable": {"thread_id": "1"}}

print("\n--- 第一次对话 ---")
input_1 = {"messages": [{"role": "user", "content": "我的名字是初见"}]}
for event in app.stream(input_1, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

print("\n--- 查看当前 State 中的 user_name ---")
print(f"State Name: {app.get_state(config).values.get('user_name')}")

print("\n--- 第二次对话 ---")
input_2 = {"messages": [{"role": "user", "content": "我的名字是什么?"}]}
for event in app.stream(input_2, config, stream_mode="values"):
    event["messages"][-1].pretty_print()
```

### 长期记忆

使用长期记忆来存储对话中特定于用户或应用程序的数据。这对于像聊天机器人这样的应用程序非常有用。

要使用长期记忆，需要：

1. 配置存储以在调用之间保留数据。

2. 使用该`ToolRuntime`功能从工具或提示中访问store。

```python
from langchain.tools import tool, ToolRuntime
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(api_key=os.getenv("DASHSCOPE_API_KEY"),
                      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                      model_provider="openai",
                      model='MiniMax-M2.1')


class UserInfo(TypedDict):
    name: str
    language: str


@tool
def update_user_info(user_info: UserInfo, runtime: ToolRuntime) -> str:
    """更新用户信息"""
    print("工具被调用，接收到的 user_info：", user_info)
    user_id = runtime.config.get("configurable").get("user_id")

    runtime.store.put(("users",), user_id, user_info)
    return "用户信息更新成功"


@tool
def get_user_info(runtime: ToolRuntime) -> str:
    """查找用户信息."""
    user_id = runtime.config.get("configurable").get("user_id")
    user_info = runtime.store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"


tools = [update_user_info, get_user_info]
llm_with_tools = llm.bind_tools(tools)


# 4. 定义节点
def call_model(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# 5. 构建图
workflow = StateGraph(MessagesState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))  # ToolNode 会自动处理 store 的传递

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# 6. 初始化存储与持久化器
# 创建内存存储对象
store = InMemoryStore()
# 创建内存持久化器
checkpointer = InMemorySaver()

# 存储初始化用户信息
store.put(
    ("users",),
    "user_123",
    {
        "name": "初见",
        "language": "中文",
    }
)

# 预存初始数据
store.put(("users",), "user_123", {"name": "初见", "language": "中文"})

# 编译图 (关键：传入 store)
app = workflow.compile(checkpointer=checkpointer, store=store)

# --- 模拟运行 ---
config = {"configurable": {"thread_id": "thread_1", "user_id": "user_123"}}

print("\n=== 任务 1: 查询初始信息 ===")
for event in app.stream({"messages": [{"role": "user", "content": "查询用户信息"}]}, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

print("\n=== 任务 2: 更新信息 ===")
# 模拟用户说：我的名字叫李铭，使用的语言是西班牙语
for event in app.stream({"messages": [{"role": "user", "content": "我的名字叫李铭，使用的语言是西班牙语"}]}, config,
                        stream_mode="values"):
    event["messages"][-1].pretty_print()

print("\n=== 任务 3: 再次查询 (验证长期记忆) ===")
for event in app.stream({"messages": [{"role": "user", "content": "我现在的名字和语言是什么？"}]}, config,
                        stream_mode="values"):
    event["messages"][-1].pretty_print()
```

# 人机交互

要在代理或工作流中审核、编辑和批准工具调用，请使用中断来暂停图表并等待人工输入。中断使用 LangGraph 的持久层（该层会保存图表状态）无限期暂停图表执行，直到恢复为止。

## 暂停使用`interrupt`

动态中断（也称为动态断点）根据图表的当前状态触发。您可以通过在适当的位置调用`interrupt`函数来设置动态中断。图表将暂停，以便人工干预，然后根据人工输入恢复图表。这对于审批、编辑或收集其他上下文等任务非常有用。

```python
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
import os

load_dotenv()
llm = init_chat_model(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_provider="openai",
        model='MiniMax-M2.1',
        temperature=0.7
    )


"""
    interrupt_before AI 已经干完活了（写了代码、写了邮件），你只是想在它造成后果（部署代码、发送邮件）之前检查一下。
    关键用作审核、拦截
"""

def writer_node(state: MessagesState):
    """节点 A: 负责写内容"""
    print("[Writer]: 正在撰写推文...")
    msg = llm.invoke([{"role": "user", "content": "写一条关于学习Python的幽默推文，50字以内"}])
    return {"messages": [msg]}


def publisher_node(state: MessagesState):
    """节点 B: 负责发布 (副作用)"""
    content = state["messages"][-1].content
    print(f"\n[Publisher]: 推文已发布到互联网: \n{content}")
    return {"messages": [AIMessage(content="发布成功")]}


# --- 构建图 ---

builder = StateGraph(MessagesState)
builder.add_node("writer", writer_node)
builder.add_node("publisher", publisher_node)

builder.add_edge(START, "writer")
builder.add_edge("writer", "publisher")
builder.add_edge("publisher", END)

# 核心配置：在进入 publisher 之前必须暂停！
checkpointer = MemorySaver()
# 在进入publisher这个节点之前先进行人工审核
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["publisher"])


# --- 运行逻辑 ---

def run_demo_1():
    print("\n=== 案例 1: interrupt_before (审核模式) ===")
    config = {"configurable": {"thread_id": "tweet_1"}}

    # 1. 启动：它会跑完 writer，然后在 publisher 门口停下
    print(">>> 启动任务...")
    graph.invoke({"messages": []}, config)

    # 2. 检查状态
    snapshot = graph.get_state(config)
    ai_draft = snapshot.values["messages"][-1].content

    print(f"\n[人类审核员]: 看到 AI 写了: {ai_draft}")
    user_input = input("是否批准? (y=批准 / 输入文字=修改并发布): ").strip()

    # 3. 处理决策
    if user_input.lower() == 'y':
        print("批准！放行...")
        # 传入 None 表示继续执行原计划
        graph.invoke(None, config)
    else:
        print("修改中...")
        # 修改状态：用人类的话替换 AI 的话
        new_msg = AIMessage(content=user_input)
        graph.update_state(config, {"messages": [new_msg]}, as_node="writer")

        print("修改完成，放行...")
        graph.invoke(None, config)


"""
    interrupt 函数 AI 正在执行一个复杂的长任务，跑到第 3 步发现缺个 API Key，或者缺个参数，它需要停下来找你要，拿到后继续跑第 4 步。
    关键用作填空
"""
# --- 节点定义 ---
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

# 1. 定义 State：我们需要一个字段来在节点间传递 days
class TripState(TypedDict):
    messages: Annotated[list, add_messages]
    days: str  # 新增字段，用来存储天数

# --- 节点 1: 负责开场白 (副作用) ---
def start_node(state: TripState):
    # 这里放你只想执行一次的代码
    print("\n[AI]: 收到，正在为你规划去‘云南’的旅行...")
    # 这个节点不返回 messages，只负责打印和过渡
    return {}

# --- 节点 2: 负责提问 + 生成 ---
def planner_node(state: TripState):
    # 1. 中断逻辑
    # 第一次运行：在这里暂停
    # 恢复运行：直接从这里拿到值，继续往下走，不会回头去跑 start_node
    days = interrupt("请问你打算去几天？")

    print(f"[AI]: 收到，{days}天。正在生成行程...")

    # 2. 生成逻辑
    # (这里为了演示简单，直接返回文本，实际可用 LLM)
    content = f"这是为你生成的云南 {days} 天行程：大理 -> 丽江 -> 香格里拉..."
    return {"messages": [AIMessage(content=content)], "days": days}

# --- 构建图 ---
builder_2 = StateGraph(TripState)

builder_2.add_node("start", start_node)
builder_2.add_node("planner", planner_node)

# 连线： Start -> Planner -> End
builder_2.add_edge(START, "start")
builder_2.add_edge("start", "planner")
builder_2.add_edge("planner", END)

checkpointer_2 = MemorySaver()
graph_2 = builder_2.compile(checkpointer=checkpointer_2)


# --- 运行逻辑 ---

def run_demo_2():
    print("\n=== 案例 2: interrupt 函数 (填空模式) ===")
    config = {"configurable": {"thread_id": "trip_1"}}

    print(">>> 启动任务...")
    # 1. 第一次运行
    for chunk in graph_2.stream({"messages": []}, config, stream_mode="values", version="v2"):
        type = chunk["type"]
        ns = chunk["ns"]
        data = chunk["data"]
        # 目前是V2版本可以在流式输出中进行获取
        interrupts = chunk["interrupts"]
        if interrupts:

            print(f"\n[系统暂停] AI 询问: {interrupts[0].value}")

            # 3. 获取人类回答
            answer = input("回答: ")   # 114行day变量就是用户的输入

            print("恢复执行...")
            # 4. 恢复执行：使用 Command 将答案传回给节点内部的 days 变量   核心点
            res = graph_2.invoke(Command(resume=answer), config)
            print(res)

        # print(f"{chunk}")

    # # 2. 捕获中断
    # snapshot = graph_2.get_state(config)
    #
    # # 检查是否有中断任务
    # if snapshot.tasks and snapshot.tasks[0].interrupts:
    #     # 获取 interrupt("...") 里的问题
    #     question = snapshot.tasks[0].interrupts[0].value
    #     print(f"\n[系统暂停] AI 询问: {question}")
    #
    #     # 3. 获取人类回答
    #     answer = input("回答: ")   # 114行day变量就是用户的输入
    #
    #     print("恢复执行...")
    #     # 4. 恢复执行：使用 Command 将答案传回给节点内部的 days 变量
    #     res = graph_2.invoke(Command(resume=answer), config)
    #     print(res)


if __name__ == "__main__":
    # run_demo_1()
    run_demo_2()
```

> **注意：**&#x5C31;开发者体验而言，中断类似于 Python 的 input() 函数，但它们不会自动从中断点恢复执行。相反，它们会重新运行发生中断的整个节点。因此，**中断通常最好放置在节点的起始位置或专用节点中。**

# 多智能体系统

代理是一种使用 LLM 来决定应用程序控制流的系统。随着这些系统的开发，它们可能会随着时间的推移变得更加复杂，从而更难以管理和扩展。例如，您可能会遇到以下问题：

* 代理可以使用的工具太多，无法决定下一步调用哪个工具

* 环境变得过于复杂，单个代理无法跟踪

* 系统中需要多个专业领域（例如规划师、研究员、数学专家等）

为了解决这些问题，您可以考虑将应用程序拆分成多个较小的独立代理，并将它们组合成一个**多代理系统**。这些独立代理可以像提示符和 LLM 调用一样简单，也可以像ReAct代理一样复杂（甚至更多！）。

使用多代理系统的主要好处是：

* **模块化**：独立的代理使得代理系统的开发、测试和维护变得更加容易。

* **专业化**：您可以创建专注于特定领域的专家代理，这有助于提高整体系统性能。

* **控制**：您可以明确控制代理如何通信。

![](LangGraph框架-image-10.png)

在多代理系统中，有几种连接代理的方法：

* **网络（交接）**：每个代理都可以与其他代理通信。任何代理都可以决定接下来要呼叫哪个代理。

* **主管代理**：每个代理只与一个主管代理进行通信。主管代理负责决定接下来应该调用哪个代理。

* **主管（工具调用）**：这是主管架构的一个特例。单个代理可以表示为工具。在这种情况下，主管代理使用工具调用 LLM 来决定调用哪些代理工具，以及传递给这些代理的参数。

* **分层结构**：你可以定义一个多智能体系统，其中包含多个主管的主管。这是主管架构的泛化，允许更复杂的控制流。

* **自定义多代理工作流**：每个代理仅与一部分代理进行通信。流程的某些部分是确定性的，只有部分代理可以决定接下来要调用哪些其他代理。

## 交接（Handoffs）

### 交接概念

在多智能体架构中，智能体可以表示为图节点。每个智能体节点执行其步骤，并决定是完成执行还是路由至其他智能体，包括可能路由至自身（例如，循环运行）。多智能体交互中一种常见的模式是**切换**，即一个智能体将控制权移交给另一个智能体

### 基础交接示例

**在线订餐系统**

**场景描述**：顾客下单 → 订单处理 → 支付处理 → 配送安排

````python
import json
import random
import re
from typing import Literal, TypedDict, Annotated
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# --- 1. 配置与模拟数据 ---

# 模拟数据库：菜单与价格
MENU_DB = {
    "汉堡": 25.0,
    "芝士汉堡": 28.0,
    "薯条": 12.0,
    "可乐": 8.0,
    "雪碧": 8.0,
    "炸鸡": 35.0
}

# 初始化大模型
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model='kimi-k2.5',
    temperature=0.5
)


# --- 2. 工具函数 ---

def parse_json_output(text: str) -> dict:
    """
    鲁棒的JSON解析器：自动清洗Markdown标记，处理常见的LLM格式问题
    """
    try:
        # 移除 ```json 和 ``` 标记
        cleaned_text = re.sub(r'```json\s*', '', text)
        cleaned_text = re.sub(r'```', '', cleaned_text)
        return json.loads(cleaned_text.strip())
    except Exception as e:
        print(f"JSON解析警告: {e}, 原始内容: {text[:50]}...")
        return {}


# 封装调用模型的方法
def call_llm(system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        llm.temperature = temperature
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"


# 定义state
class OrderState(TypedDict):
    customer_name: str  # 客户姓名
    # 使用 add_messages 保留对话历史
    messages: Annotated[list[BaseMessage], add_messages]
    order_items: list  # 结构: [{"name": "汉堡", "price": 25.0}]
    raw_order_text: str  # 用户原始输入
    total_amount: float  # 总金额
    payment_status: str  # 支付结果
    delivery_address: str  # 配送地址
    order_status: str  # 订单状态
    llm_analysis: dict  # 大模型返回的分析结果


# 定义节点

def order_receiver(state: OrderState) -> Command[Literal["payment_processor", "order_validator"]]:
    # 1.获取用户的原始输入
    raw_order_text = state["raw_order_text"]
    customer_name = state["customer_name"]  # 用户名称
    print(f"正在处理{customer_name}的需求:{raw_order_text}")

    # 如果已经有 items（可能是重试或手动输入的），跳过解析
    if state.get("order_items") and not raw_order_text:
        total = sum(item['price'] for item in state['order_items'])
        return Command(goto="payment_processor", update={"total_amount": total})

    # 2.调用模型进行意图拆解
    system_prompt = f"""你是一个餐厅订单解析员。
    当前菜单包括：{', '.join(MENU_DB.keys())}。
    请分析用户输入，提取菜品。如果用户说的菜不在菜单里，请标记为未知。

    返回严格的JSON格式：
    {{
        "items_identified": ["菜名1", "菜名2"],
        "unknown_items": ["不在菜单的词"],
        "intent_clarity": "high/medium/low",
        "missing_info": "缺少的关键信息(如地址等)"
    }}"""
    llm_response = call_llm(system_prompt, raw_order_text)
    analysis = parse_json_output(llm_response)

    print(f"模型分析后得到的内容:{analysis}")
    # 3.将识别出来的菜名映射成订单
    identified_names = analysis.get("items_identified")

    new_order_items = []  # 当前用户所需要买的商品-价格

    for name in identified_names:
        # 简单的模糊匹配逻辑（实际项目中可用向量搜索）
        if name in MENU_DB:
            new_order_items.append({"name": name, "price": MENU_DB[name]})
        else:
            # 尝试查找最接近的菜单项（简化版）
            for menu_item in MENU_DB:
                if menu_item in name or name in menu_item:
                    new_order_items.append({"name": menu_item, "price": MENU_DB[menu_item]})
                    break

    # 计算总金额
    total = sum(item['price'] for item in new_order_items)

    # 检查是否有未知商品   大于0就代表有不属于我们的商品
    has_unknown_items = len(analysis.get("unknown_items")) > 0

    # 检查是否完全没识别出商品
    no_valid_items = len(new_order_items) == 0

    # 检查置信度
    is_unclear = analysis.get("intent_clarity") == "low"

    # 只要满足以上三种的任意一种条件就需要去往验证节点
    if has_unknown_items or no_valid_items or is_unclear:
        # 构建提示消息
        if has_unknown_items:
            msg_content = f"系统检测到未知商品：{', '.join(analysis['unknown_items'])}，需要确认。"
        elif no_valid_items:
            msg_content = "没能识别出具体菜品。"
        else:
            msg_content = "订单信息不明确。"

        return Command(
            goto="order_validator",
            update={
                "order_status": "解析存疑",
                "llm_analysis": analysis,
                "messages": [AIMessage(content=msg_content)]
            }
        )
    # 完全准备就绪后就去往支付节点
    return Command(
        goto="payment_processor",
        update={
            "order_items": new_order_items,
            "total_amount": total,
            "order_status": "待支付",
            "llm_analysis": analysis,
            "messages": [AIMessage(content=f"已生成订单：{[i['name'] for i in new_order_items]}，总价：{total}元")]
        }
    )


def order_validator(state: OrderState) -> Command[Literal["payment_processor", END]]:
    """
    订单验证节点：处理异常或信息缺失
    """
    print("[验证] 正在检查订单完整性...")
    analysis = state.get("llm_analysis", {})
    order_items = state.get("order_items", [])

    # 简单的验证逻辑：如果有未知商品或金额为0
    unknowns = analysis.get("unknown_items", [])

    if unknowns:
        error_msg = f"抱歉，我们暂时不提供：{', '.join(unknowns)}。请重新下单。"
        return Command(
            goto=END,
            update={
                "order_status": "验证失败",
                "messages": [AIMessage(content=error_msg)]
            }
        )

    if not order_items:
        return Command(
            goto=END,
            update={
                "order_status": "空订单",
                "messages": [AIMessage(content="未能识别任何有效菜品，流程结束。")]
            }
        )

    # 如果验证通过（比如虽然有小问题但可忽略）
    return Command(
        goto="payment_processor",
        update={"messages": [AIMessage(content="经二次验证，订单有效。")]}
    )


def payment_processor(state: OrderState) -> Command[Literal["delivery_scheduler", END]]:
    """
    支付节点
    """
    amount = state.get("total_amount", 0)
    print(f"[支付] 正在处理金额: {amount}元")

    # 模拟支付
    if amount > 1000:  # 假设大额风控
        return Command(
            goto=END,
            update={
                "payment_status": "拒绝",
                "messages": [AIMessage(content="金额过大，支付被系统拒绝。")]
            }
        )

    return Command(
        goto="delivery_scheduler",
        update={
            "payment_status": "成功",
            "messages": [AIMessage(content="支付成功！")]
        }
    )


def delivery_scheduler(state: OrderState) -> Command[Literal[END]]:
    """
    配送节点
    """
    address = state.get("delivery_address", "未填写地址")
    items = [i['name'] for i in state.get('order_items', [])]

    # 使用 LLM 生成最终通知
    prompt = f"""为客户生成一条外卖配送通知。
    菜品：{', '.join(items)}
    地址：{address}
    风格：热情、期待。"""

    msg = call_llm(prompt, "生成通知", temperature=0.7)
    print(f"[配送] {msg}")

    return Command(
        goto=END,
        update={
            "order_status": "配送中",
            "messages": [AIMessage(content=msg)]
        }
    )


# --- 5. 构建图 ---

builder = StateGraph(OrderState)
builder.add_node("order_receiver", order_receiver)
builder.add_node("order_validator", order_validator)
builder.add_node("payment_processor", payment_processor)
builder.add_node("delivery_scheduler", delivery_scheduler)

builder.add_edge(START, "order_receiver")

# 没有固定对应的边

graph = builder.compile()


# --- 6. 测试运行 ---

print("--- 测试用例 1: 纯自然语言输入 (自动解析) ---")
test_input = {
    "customer_name": "李四",
    "raw_order_text": "你好，我想要两个汉堡和一杯可乐，送到科技园A栋。",
    "delivery_address": "科技园A栋",  # 实际场景中这个也应该由LLM提取
    "messages": [],
    "order_items": []  # 故意留空，测试自动解析
}

try:
    final_state = graph.invoke(test_input)
    print("\n流程结束")
    print(f"最终状态: {final_state['order_status']}")
    print(f"最终金额: {final_state['total_amount']}")
    print(f"订单内容: {final_state['order_items']}")
except Exception as e:
    print(f"运行出错: {e}")

print("\n--- 测试用例 2: 包含不在菜单的商品 ---")
test_input_2 = {
    "customer_name": "王五",
    "raw_order_text": "来一份披萨和一杯可乐。",  # 披萨不在菜单里
    "messages": [],
    "order_items": []
}

try:
    final_state_2 = graph.invoke(test_input_2)
    print(f"\n最终状态: {final_state_2['order_status']}")
    # 应该打印出验证失败的消息
    print(f"系统回复: {final_state_2['messages'][-1].content}")
except Exception as e:
    print(f"运行出错: {e}")
````

### 交接的关键要点

* 任务超出当前智能体能力范围

* 需要专业化处理

* 错误处理和重试机制

* 工作流程的自然转换点

### 工具进行交接（重点）

![](LangGraph框架-mermaid-diagram-2026-04-22-165101.png)



```python
from typing_extensions import Literal

from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage, HumanMessage
from langgraph.types import Command
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 初始化大模型
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model='MiniMax-M2.1',
    temperature=0.7
)


def make_handoff_tool(*, agent_name: str):
    """
    创建一个工具交接函数，用于在代理之间进行转接

    Args:
        agent_name (str): 目标代理的名称

    Returns:
        tool: 返回一个可以执行代理转接的工具函数
    """
    # 根据目标代理名称动态生成工具名称
    tool_name = f"transfer_to_{agent_name}"

    @tool(tool_name)
    def handoff_to_agent(
            runtime: ToolRuntime
    ):
        """请求另一个代理的帮助进行任务交接"""

        # 返回Command对象，用于导航到父图中的另一个代理节点
        return Command(
            # 导航到目标代理节点
            goto=agent_name,
            # 在父图中执行导航
            graph=Command.PARENT,
            # 更新状态：将完整的消息历史传递给目标代理，并添加工具消息
            # 这确保了聊天历史的完整性和有效性
            update={"messages": runtime.state["messages"] + [
                ToolMessage(name=tool_name, content=f"成功转接到 {agent_name} 代理，请开始进行乘法运算",
                            tool_call_id=runtime.tool_call_id)]},
        )

    return handoff_to_agent


def make_agent(model, tools, system_prompt=None):
    """
    创建一个智能代理，能够使用工具并在需要时进行代理转接

    Args:
        model: 语言模型实例
        tools: 代理可用的工具列表
        system_prompt: 系统提示词，定义代理的角色和行为

    Returns:
        compiled_graph: 编译后的代理图
    """
    # 将工具绑定到模型上
    model_with_tools = model.bind_tools(tools)

    # 创建工具节点
    tool_node = ToolNode(tools)

    def call_model(state: MessagesState) -> Command[Literal["call_tools", END]]:
        """
        调用语言模型生成响应

        Args:
            state: 当前消息状态

        Returns:
            Command: 如果需要调用工具则转到call_tools，否则结束
        """
        messages = state["messages"]
        # 如果有系统提示词，将其添加到消息开头
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        # 调用绑定了工具的模型
        response = model_with_tools.invoke(messages)

        # 检查模型是否决定使用工具
        if len(response.tool_calls) > 0:
            # 如果有工具调用，转到工具执行节点
            return Command(goto="call_tools", update={"messages": [response]})

        # 如果没有工具调用，直接返回响应消息
        return {"messages": [response]}

    # 构建代理的内部图结构
    graph = StateGraph(MessagesState)

    # 添加模型调用节点和工具调用节点
    graph.add_node("call_model", call_model)
    graph.add_node("call_tools", tool_node)

    # 设置图的边：从开始到模型调用，从工具调用回到模型调用
    graph.add_edge(START, "call_model")
    graph.add_conditional_edges(
        "call_model",
        tools_condition,  # 内置函数：判断消息中是否有 tool_calls
        {"tools": "call_tools", "__end__": END},
    )

    graph.add_edge("call_tools", "call_model")

    # 编译并返回图
    return graph.compile()


def pretty_print_stream(chunk):
    """
    流式输出美化工具
    """
    # StreamPart 对象包含三个核心属性
    msg_type = chunk["type"]  # str: 'updates', 'metadata', 'values' 等
    ns =  chunk["ns"]  # tuple: 命名空间
    data =  chunk["data"]  # Any: 更新的具体内容
    for node_name, node_update in data.items():
        # 1. 打印节点标题（区分是谁在干活）
        print(f"\n正在运行节点: [{node_name}]")
        print("-" * 30)

        # 2. 检查是否有消息更新
        if "messages" in node_update:
            for msg in node_update["messages"]:
                # --- 核心提取逻辑 ---

                # 如果是 AI 说的话
                if msg.type == "ai":
                    if msg.content:
                        print(f"AI: {msg.content.strip()}")
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"[工具调用] 执行 {tc['name']}，参数: {tc['args']}")

                # 如果是工具返回的结果
                elif msg.type == "tool":
                    print(f"[工具结果] 得到: {msg.content}")

                # 如果是人类的输入
                elif msg.type == "human":
                    print(f"用户: {msg.content}")



# ============= 定义数学工具 =============

@tool
def add(a: int, b: int) -> int:
    """执行两个数字的加法运算"""
    result = a + b
    print(f"执行加法: {a} + {b} = {result}")
    return result


@tool
def multiply(a: int, b: int) -> int:
    """执行两个数字的乘法运算"""
    result = a * b
    print(f"执行乘法: {a} × {b} = {result}")
    return result


@tool
def subtract(a: int, b: int) -> int:
    """执行两个数字的减法运算"""
    result = a - b
    print(f"执行减法: {a} - {b} = {result}")
    return result


@tool
def divide(a: int, b: int) -> float:
    """执行两个数字的除法运算"""
    if b == 0:
        return "错误：不能除以零"
    result = a / b
    print(f"执行除法: {a} ÷ {b} = {result}")
    return result


# ============= 演示单个代理 =============

def demo_single_agent():
    """演示单个具有所有数学工具的代理"""
    print("=" * 60)
    print("演示：单个数学代理")
    print("=" * 60)

    # 创建一个拥有所有数学工具的代理
    math_agent = make_agent(
        llm,
        [add, multiply, subtract, divide],
        system_prompt="你是一个数学专家，可以执行各种数学运算。请一步步解决问题。"
    )

    print("问题: 计算 (3 + 5) × 12")
    print()

    # 运行代理并显示结果
    for chunk in math_agent.stream({"messages": [("user", "计算 (3 + 5) × 12")]}):
        pretty_print_stream(chunk)


# ============= 演示多代理协作 =============

def demo_multi_agent_collaboration():
    """演示多个专业代理之间的协作"""
    print("=" * 60)
    print("演示：多代理协作系统")
    print("=" * 60)

    # 创建加法专家代理
    addition_expert = make_agent(
        llm,
        [add, subtract, make_handoff_tool(agent_name="multiplication_expert")],
        system_prompt="""你是加法和减法专家。你精通加法和减法运算，必须使用工具去计算加法。
            当你完成加法或减法运算后，如果后续还需要乘法或除法运算，
            请立即使用 transfer_to_multiplication_expert 工具转接给乘法专家。
            不要尝试自己完成乘法运算。"""
    )

    # 创建乘法专家代理
    multiplication_expert = make_agent(
        llm,
        [multiply, divide, make_handoff_tool(agent_name="addition_expert")],
        system_prompt="""你是乘法和除法专家。你精通乘法和除法运算。
            当你接收到需要乘法运算的任务时，必须使用工具执行乘法运算。
            如果后续还需要加法或减法运算，请使用transfer_to_addition_expert工具转接给加法专家。
            当前任务：执行乘法运算并给出最终答案。"""
    )

    # 构建多代理协作图
    builder = StateGraph(MessagesState)

    # 添加两个专家代理节点
    builder.add_node("addition_expert", addition_expert)
    builder.add_node("multiplication_expert", multiplication_expert)

    # 设置入口点为加法专家
    builder.add_edge(START, "addition_expert")

    # 编译协作图
    collaboration_graph = builder.compile()

    print("问题: 计算 (3 + 5) × 12")
    print("加法专家将处理加法，然后转接给乘法专家处理乘法")
    print()

    # 运行协作图并显示子图中的所有更新
    for chunk in collaboration_graph.stream(
            {"messages": [HumanMessage(content="请计算 (3 + 5) × 12")]},
            subgraphs=True,  # 包含子图更新
            version="v2",
            stream_mode="updates"
    ):
        pretty_print_stream(chunk)


# ============= 更复杂的协作示例 =============

def demo_complex_collaboration():
    """演示更复杂的多步骤协作"""
    print("=" * 60)
    print("演示：复杂多步协作")
    print("=" * 60)

    # 创建基础运算专家
    basic_math_expert = make_agent(
        llm,
        [add, subtract, make_handoff_tool(agent_name="advanced_math_expert")],
        system_prompt="""你是基础数学专家。你的唯一职责是执行“加法(add)”和“减法(subtract)”。
        执行逻辑规范：
        1. 观察算式，如果存在可以直接进行的加法或减法（尤其是括号内的），请立即调用工具计算。
        2. 严禁尝试口算，必须通过工具获得结果。
        3. 严禁执行乘法或除法。如果你发现当前步骤必须先进行乘除法才能继续，请立即转接给高级专家。
        4. 只要你刚刚完成了一步加/减法计算，请停下来观察剩下的算式：
           - 如果剩下的算式里还有你能算的加减法，继续算。
           - 如果剩下的部分只涉及乘除法，立即转接到 advanced_math_expert。
        不要道歉，不要解释，只负责计算或转接。"""
    )

    # 创建高级运算专家
    advanced_math_expert = make_agent(
        llm,
        [multiply, divide, make_handoff_tool(agent_name="basic_math_expert")],
        system_prompt="""你是高级数学专家。你的唯一职责是执行“乘法(multiply)”和“除法(divide)”。
        执行逻辑规范：
        1. 观察算式，如果你发现当前必须先执行加法或减法（例如括号内的内容尚未解出），请立即转接到 basic_math_expert。
        2. 如果当前步骤可以直接进行乘法或除法，请立即调用工具计算。
        3. 严禁尝试口算，必须通过工具获得结果。
        4. 只要你刚刚完成了一步乘/除法计算，请停下来观察剩下的算式：
           - 如果剩下的算式需要基础运算（加减），立即转接到 basic_math_expert。
           - 如果剩下的全是乘除，继续计算直到得出最终结果。
        你的目标是完成计算，但在遇到加减法时要坚决交接，不要自己通过“口算”来跳过步骤。"""
    )

    # 构建协作图
    builder = StateGraph(MessagesState)
    builder.add_node("basic_math_expert", basic_math_expert)
    builder.add_node("advanced_math_expert", advanced_math_expert)
    builder.add_edge(START, "basic_math_expert")

    complex_graph = builder.compile()

    print("复杂问题: 计算 ((10 + 5) × 3 - 8) ÷ 2")
    print("将需要多次代理转接来完成计算")
    print()

    for chunk in complex_graph.stream(
            {"messages": [HumanMessage(content="请逐步计算 ((10 + 5) × 3 - 8) ÷ 2")]},
            subgraphs=True,
            version="v2",
            stream_mode="updates"
    ):
        pretty_print_stream(chunk)



# ============= 主程序入口 =============

def main():
    """主程序，运行所有演示"""
    print("LangGraph工具交接案例演示")
    print("展示单代理和多代理协作的数学计算系统")
    print()

    try:
        # 演示1：单个代理
        # demo_single_agent()
        #
        # print("\n" + "-" * 20 + "\n")

        # 演示2：多代理协作
        # demo_multi_agent_collaboration()

        # print("\n" + "-" * 20 + "\n")
        #
        # # 演示3：复杂协作
        demo_complex_collaboration()

    except Exception as e:
        print(f"运行出错: {e}")


if __name__ == "__main__":
    main()
```

## 如何构建多智能体应用

### 自定义主管架构（重点）

```python
from typing import Literal
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.tools import tool
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# ==============================================================================
# 数据定义 (模拟数据库)
# ==============================================================================

# 知识库: 技术问题的解决方案映射
# Key: 问题关键词 (小写), Value: 解决方案
KNOWLEDGE_BASE = {
    "login": "请清除浏览器缓存并重新登录，或重置密码。",
    "payment": "请检查银行卡余额，确认交易状态，或联系银行。",
    "bug": "我们已记录此问题，技术团队将在24小时内处理。",
    "network": "请检查网络连接，或尝试切换网络环境。",
    "performance": "建议清理缓存、重启应用或检查系统资源使用情况。"
}

# 产品列表: 产品ID -> 产品信息
# 包含名称、价格、功能列表
PRODUCTS = {
    "basic": {"name": "基础版", "price": 99, "features": ["基础功能", "邮件支持"]},
    "pro": {"name": "专业版", "price": 299, "features": ["高级功能", "优先支持", "API访问"]},
    "enterprise": {"name": "企业版", "price": 999, "features": ["企业功能", "专属客服", "定制开发"]}
}

# 用户数据库: 用户ID -> 用户信息
# 包含套餐、状态、支持级别、余额
USER_DATABASE = {
    "user123": {"plan": "pro", "status": "active", "support_level": "premium", "balance": 500},
    "user456": {"plan": "basic", "status": "active", "support_level": "standard", "balance": 100}
}

# ==============================================================================
# LLM 初始化
# ==============================================================================

# 创建 Qwen 模型实例
# 使用阿里云 DashScope API 兼容 OpenAI 接口
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="MiniMax-M2.1",
    temperature=0.1  # 低温度，保持回答确定性
)

# ==============================================================================
# 工具定义 (使用 @tool 装饰器)
# ==============================================================================

# ----------------------------------------------------------------------
# 技术支持工具 (tech_agent 使用)
# ----------------------------------------------------------------------

@tool
def search_knowledge_base(query: str) -> str:
    """
    搜索技术知识库，查找解决方案

    Args:
        query: 用户的问题描述

    Returns:
        str: 从知识库中找到的解决方案，或提示创建工单
    """
    print(f"[Tech] 搜索知识库: {query}")

    # 将查询转为小写进行匹配
    query_lower = query.lower()
    results = []

    # 遍历知识库，查找匹配的问题
    for issue, solution in KNOWLEDGE_BASE.items():
        if issue in query_lower:
            results.append(f"{issue}: {solution}")

    # 如果找到匹配项，返回所有解决方案
    if results:
        return "找到以下解决方案:\n" + "\n".join(results)

    # 未找到匹配，返回创建工单提示
    return "未在知识库中找到相关解决方案，建议创建技术工单进行人工处理。"

# ----------------------------------------------------------------------
# 技术支持工具: 创建工单 (tech_agent 使用)
# ----------------------------------------------------------------------

@tool
def create_support_ticket(issue_description: str, priority: str = "normal") -> str:
    """
    创建技术支持工单

    Args:
        issue_description: 问题描述
        priority: 优先级 (normal/high/urgent)

    Returns:
        str: 工单创建成功信息，包含工单ID
    """
    import uuid

    # 生成唯一工单ID: TICKET-XXXXXXXX 格式
    ticket_id = f"TICKET-{str(uuid.uuid4())[:8].upper()}"
    print(f"[Tech] 创建工单: {ticket_id}")

    return f"已创建支持工单: {ticket_id}\n问题描述: {issue_description}\n优先级: {priority}\n我们的技术团队将在24小时内处理您的问题。"

# ----------------------------------------------------------------------
# 销售工具: 获取产品信息 (sales_agent 使用)
# ----------------------------------------------------------------------

@tool
def get_product_info(product_query: str = "") -> str:
    """
    获取产品信息和价格

    Args:
        product_query: 产品查询词（可选），支持产品ID或名称

    Returns:
        str: 产品信息列表，包含价格和功能
    """
    print(f"[Sales] 查询产品: {product_query or '全部'}")

    # 如果没有指定查询词，返回所有产品
    if not product_query:
        result = "我们的产品线包括:\n\n"
        for key, product in PRODUCTS.items():
            result += f"**{product['name']}** - ¥{product['price']}/月\n"
            result += f"功能: {', '.join(product['features'])}\n\n"
        return result

    # 根据查询词查找匹配的产品
    query_lower = product_query.lower()
    for key, product in PRODUCTS.items():
        if key in query_lower or product["name"] in query_lower:
            return (
                f"**{product['name']}**\n"
                f"价格: ¥{product['price']}/月\n"
                f"功能: {', '.join(product['features'])}"
            )

    return f"未找到关于'{product_query}'的产品信息。请查看我们的完整产品列表。"

# ----------------------------------------------------------------------
# 销售工具: 计算升级费用 (sales_agent 使用)
# ----------------------------------------------------------------------

@tool
def calculate_upgrade_cost(current_plan: str, target_plan: str) -> str:
    """
    计算升级费用

    Args:
        current_plan: 当前套餐ID
        target_plan: 目标套餐ID

    Returns:
        str: 升级费用计算结果，包含新增功能列表
    """
    print(f"[Sales] 计算升级: {current_plan} -> {target_plan}")

    # 验证套餐ID有效性
    if current_plan not in PRODUCTS or target_plan not in PRODUCTS:
        return "无效的套餐类型。请检查套餐名称。"

    # 获取当前和目标套餐的价格
    current_price = PRODUCTS[current_plan]["price"]
    target_price = PRODUCTS[target_plan]["price"]

    # 如果目标价格不高于当前价格，无需升级费用
    if target_price <= current_price:
        return (
            f"目标套餐 ({PRODUCTS[target_plan]['name']}) "
            f"价格不高于当前套餐 ({PRODUCTS[current_plan]['name']})，无需升级费用。"
        )

    # 计算升级费用
    upgrade_cost = target_price - current_price

    # 计算新增功能
    new_features = set(PRODUCTS[target_plan]["features"]) - set(PRODUCTS[current_plan]["features"])

    return (
        f"升级费用计算:\n"
        f"当前套餐: {PRODUCTS[current_plan]['name']} (¥{current_price}/月)\n"
        f"目标套餐: {PRODUCTS[target_plan]['name']} (¥{target_price}/月)\n"
        f"升级费用: ¥{upgrade_cost}/月\n\n"
        f"新增功能: {', '.join(new_features)}"
    )

# ----------------------------------------------------------------------
# 管理工具: 查询账户信息 (admin_agent 使用)
# ----------------------------------------------------------------------

@tool
def get_user_account_info(user_id: str) -> str:
    """
    查询用户账户信息

    Args:
        user_id: 用户ID

    Returns:
        str: 用户账户详细信息
    """
    print(f"[Admin] 查询账户: {user_id}")

    # 验证用户ID是否提供
    if not user_id:
        return "请提供您的用户ID以查询账户信息。"

    # 从数据库查找用户
    if user_id in USER_DATABASE:
        user_info = USER_DATABASE[user_id]
        return (
            f"账户信息:\n"
            f"用户ID: {user_id}\n"
            f"当前套餐: {user_info['plan']}\n"
            f"账户状态: {user_info['status']}\n"
            f"支持级别: {user_info['support_level']}\n"
            f"账户余额: ¥{user_info['balance']}"
        )

    return f"未找到用户ID '{user_id}' 的账户信息。"

# ----------------------------------------------------------------------
# 管理工具: 处理退款请求 (admin_agent 使用)
# ----------------------------------------------------------------------

@tool
def process_refund_request(user_id: str, reason: str) -> str:
    """
    处理退款请求

    Args:
        user_id: 用户ID
        reason: 退款原因

    Returns:
        str: 退款申请结果
    """
    print(f"[Admin] 处理退款: {user_id}")

    # 验证用户ID有效性
    if not user_id or user_id not in USER_DATABASE:
        return "请提供有效的用户ID以处理退款请求。"

    user_info = USER_DATABASE[user_id]

    # 检查账户状态
    if user_info["status"] != "active":
        return "只有活跃账户才能申请退款。"

    # 计算退款金额（按月费计算）
    refund_amount = PRODUCTS[user_info["plan"]]["price"]

    return (
        f"退款申请已提交:\n"
        f"用户ID: {user_id}\n"
        f"退款原因: {reason}\n"
        f"退款金额: ¥{refund_amount}\n"
        f"处理时间: 3-5个工作日\n"
        f"退款将原路返回到您的支付账户。"
    )

# ==============================================================================
# 创建子图 (每个子Agent一个子图)
# ==============================================================================

# ----------------------------------------------------------------------
# 子图1: 技术支持 Agent
# 负责处理: 报错、bug、故障、登录问题、网络问题等
# ----------------------------------------------------------------------

def create_tech_agent_subgraph():
    """
    创建技术支持Agent子图

    子图结构:
        START -> tech_model -> (tools_condition) -> tech_tools -> tech_model -> END
                                    |
                                    v
                                   END (无工具调用时)

    工具:
        - search_knowledge_base: 搜索知识库
        - create_support_ticket: 创建工单

    Returns:
        Compiled graph: 编译后的子图，可被主图调用
    """

    # 定义该子图使用的工具列表
    tech_tools = [search_knowledge_base, create_support_ticket]

    # 定义 LLM 调用节点
    # 功能: 调用 LLM，让 LLM 决定是否需要调用工具
    def tech_model_node(state: MessagesState):
        """
        技术Agent的模型节点

        Args:
            state: 包含消息历史的状态

        Returns:
            dict: 更新后的状态，包含 LLM 响应
        """
        print("[Tech] LLM 决策...")

        # 系统提示词：指导 LLM 如何使用工具
        system_prompt = """你是一个技术支持助手。

        工具使用规则：
        1. 首先使用 search_knowledge_base 搜索知识库，查找解决方案
        2. 如果知识库找到了答案，直接返回给用户
        3. 如果知识库找不到答案（返回"未在知识库中找到..."），则使用 create_support_ticket 创建工单

        回答要求：
        - 如果知识库有答案，简明扼要地告诉用户
        - 如果知识库没有答案，创建工单并告知用户工单ID"""
        # 使用系统提示词 + 用户消息
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        ai_message = llm.bind_tools(tech_tools).invoke(messages)
        return {"messages": [ai_message]}

    # 创建状态图
    builder = StateGraph(MessagesState)

    # 添加节点:
    # 1. tech_model: LLM 决策节点
    # 2. tech_tools: 工具执行节点 (由 ToolNode 自动处理工具调用)
    builder.add_node("tech_model", tech_model_node)
    builder.add_node("tech_tools", ToolNode(tech_tools))

    # 添加边:
    # 1. START -> tech_model: 起点到 LLM 节点
    builder.add_edge(START, "tech_model")

    # 2. tech_model -> 条件边: LLM 决定是调用工具还是结束
    #    tools_condition 会检查 LLM 输出是否有 tool_calls
    #    - 如果有: 路由到 tech_tools
    #    - 如果没有: 路由到 END
    builder.add_conditional_edges(
        "tech_model",
        tools_condition,
        {"tools": "tech_tools", END: END}
    )

    # 3. tech_tools -> tech_model: 工具执行完后返回 LLM 形成循环
    builder.add_edge("tech_tools", "tech_model")

    return builder.compile()

# ----------------------------------------------------------------------
# 子图2: 销售 Agent
# 负责处理: 价格咨询、套餐升级、产品信息、购买咨询等
# ----------------------------------------------------------------------

def create_sales_agent_subgraph():
    """
    创建销售Agent子图

    工具:
        - get_product_info: 获取产品信息
        - calculate_upgrade_cost: 计算升级费用

    子图结构与 Tech Agent 相同
    """
    sales_tools = [get_product_info, calculate_upgrade_cost]

    def sales_model_node(state: MessagesState):
        print("[Sales] LLM 决策...")
        ai_message = llm.bind_tools(sales_tools).invoke(state["messages"])
        return {"messages": [ai_message]}

    builder = StateGraph(MessagesState)
    builder.add_node("sales_model", sales_model_node)
    builder.add_node("sales_tools", ToolNode(sales_tools))

    builder.add_edge(START, "sales_model")
    builder.add_conditional_edges(
        "sales_model",
        tools_condition,
        {"tools": "sales_tools", END: END}
    )
    builder.add_edge("sales_tools", "sales_model")

    return builder.compile()

# ----------------------------------------------------------------------
# 子图3: 客户管理 Agent
# 负责处理: 余额查询、账户信息、退款申请等
# ----------------------------------------------------------------------

def create_admin_agent_subgraph():
    """
    创建客户管理Agent子图

    工具:
        - get_user_account_info: 查询账户信息
        - process_refund_request: 处理退款

    子图结构与 Tech Agent 相同
    """
    admin_tools = [get_user_account_info, process_refund_request]

    def admin_model_node(state: MessagesState):
        print("[Admin] LLM 决策...")
        ai_message = llm.bind_tools(admin_tools).invoke(state["messages"])
        return {"messages": [ai_message]}

    builder = StateGraph(MessagesState)
    builder.add_node("admin_model", admin_model_node)
    builder.add_node("admin_tools", ToolNode(admin_tools))

    builder.add_edge(START, "admin_model")
    builder.add_conditional_edges(
        "admin_model",
        tools_condition,
        {"tools": "admin_tools", END: END}
    )
    builder.add_edge("admin_tools", "admin_model")

    return builder.compile()

# ==============================================================================
# 创建主管图 (支持循环协调)
# ==============================================================================

# ----------------------------------------------------------------------
# 主管节点: 负责任务分配和协调
# 使用 LLM 做意图识别，支持多任务循环协调
# ----------------------------------------------------------------------

def create_supervisor_graph():
    """
    创建主管Graph - 协调所有子Agent的任务

    复杂问题示例: "我想了解专业版的价格，另外查一下我的余额"
    - 涉及: 销售问题(价格) + 管理问题(余额)
    - 需要循环调用: supervisor -> sales -> supervisor -> admin -> supervisor -> END

    主管状态 (SupervisorState):
        - messages: 消息列表 (从 MessagesState 继承)
        - pending_tasks: 待处理任务队列 ['tech', 'sales', 'admin']
        - completed_tasks: 已完成任务列表
        - current_agent: 当前正在执行的 Agent

    Returns:
        Compiled graph: 编译后的主管图
    """

    # 先创建三个子图
    tech_subgraph = create_tech_agent_subgraph()
    sales_subgraph = create_sales_agent_subgraph()
    admin_subgraph = create_admin_agent_subgraph()

    # 定义主管状态类型
    # 继承 MessagesState，获得 messages 通道和 add_messages reducer
    class SupervisorState(MessagesState):
        """
        主管状态: 包含消息和任务追踪信息

        Attributes:
            current_agent: 当前执行的 Agent 名称
            pending_tasks: 待处理的任务队列 (关键！用于循环协调)
            completed_tasks: 已完成的任务列表
            next_agent: 下一个要执行的 Agent 名称（由 supervisor_node 设置）
        """
        current_agent: str
        pending_tasks: list[str]
        completed_tasks: list[str]
        next_agent: str | None = None

    def supervisor_node(state: SupervisorState) -> dict:
        """
        主管节点 - 负责任务识别和分配

        工作流程:
            1. 如果有待处理任务(PendingTasks)，取出第一个任务执行
            2. 如果没有待处理任务（首次），使用 LLM 做意图识别
            3. 将所有识别的任务填入 pending_tasks（除第一个外）
            4. 返回第一个任务名称

        关键改进: 使用 LLM 做意图识别，不再用关键词匹配

        Args:
            state: 当前状态

        Returns:
            dict: 状态更新，包含 pending_tasks 和 next_agent
        """
        pending = state.get("pending_tasks", [])
        completed = state.get("completed_tasks", [])
        messages = state["messages"]
        last_msg = messages[-1] if messages else None

        # ========== 情况1: 还有待处理任务，从队列取第一个执行 ==========
        if pending:
            next_task = pending[0]  # 取出队首任务
            remaining = pending[1:]  # 剩余任务
            print(f"\n[Supervisor] 取出待处理任务: {next_task}, 剩余: {remaining}")
            return {
                "pending_tasks": remaining,
                "next_agent": next_task  # 标记下一个要执行的 Agent
            }

        # ========== 情况2: 没有待处理任务，使用提示词做 LLM 意图识别 ==========
        if isinstance(last_msg, HumanMessage):
            print(f"\n[Supervisor] 使用 LLM 进行意图识别...")

            # 意图识别提示词
            routing_prompt = f"""你是意图识别专家。根据用户消息，决定调用哪个 Agent 来处理。

            Agent 类型：
            - tech_agent: 技术支持（报错、bug、故障、登录问题、网络问题、性能问题、技术咨询等）
            - sales_agent: 销售服务（价格咨询、套餐升级、产品信息、购买咨询、升级费用等）
            - admin_agent: 账户管理（查询余额、账户信息、退款申请、账户状态等）

            注意：一个问题可能需要多个 Agent 处理。

            用户消息: {last_msg.content}

            请分析用户消息，返回需要调用的 Agent 列表（最多3个，按处理顺序排列）。
            只返回 Agent 名称，用逗号分隔。例如：tech_agent,sales_agent"""

            # 调用 LLM 获取意图识别结果
            response = llm.invoke(routing_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 解析 LLM 返回的 Agent 列表
            new_tasks = []
            for agent in ["tech_agent", "sales_agent", "admin_agent"]:
                if agent in response_text and agent not in completed:
                    new_tasks.append(agent)

            # 如果 LLM 返回了有效任务
            if new_tasks:
                print(f"[Supervisor] LLM 识别到任务: {new_tasks}")
                next_task = new_tasks[0]
                remaining = new_tasks[1:]
                return {
                    "pending_tasks": remaining,
                    "next_agent": next_task
                }

        # ========== 情况3: 没有新任务 ==========
        print("\n[Supervisor] 所有任务已完成，结束对话")
        return {"pending_tasks": [], "next_agent": None}

    def route_by_pending(state: SupervisorState) -> Literal["tech_agent", "sales_agent", "admin_agent", END]:
        """
        根据 pending_tasks 状态路由到对应的 Agent

        工作流程:
            1. 检查 next_agent 字段（由 supervisor_node 设置）
            2. 返回对应的 Agent 节点或 END

        Args:
            state: 当前状态

        Returns:
            str: 下一个节点的名称
        """
        next_agent = state.get("next_agent")
        if next_agent == "tech_agent":
            return "tech_agent"
        elif next_agent == "sales_agent":
            return "sales_agent"
        elif next_agent == "admin_agent":
            return "admin_agent"
        else:
            return END

    def call_tech_agent(state: SupervisorState) -> SupervisorState:
        """
        调用技术子Agent

        执行流程:
            1. 调用 tech_subgraph 子图
            2. 获取子图执行结果
            3. 返回更新后的状态，让 supervisor 决定下一步

        Args:
            state: 当前状态

        Returns:
            SupervisorState: 更新后的状态
        """
        print("[Supervisor] 调用 Tech 子图...")

        pending = state.get("pending_tasks", [])
        completed = state.get("completed_tasks", [])

        result = tech_subgraph.invoke({"messages": state["messages"]})

        return {
            "messages": result["messages"],
            "pending_tasks": pending,  # 保持 pending 不变，让 supervisor 取出下一个
            "completed_tasks": completed + ["tech"],
            "current_agent": "tech"
        }

    def call_sales_agent(state: SupervisorState) -> SupervisorState:
        """
        调用销售子Agent

        执行流程与 call_tech_agent 相同
        """
        print("[Supervisor] 调用 Sales 子图...")

        pending = state.get("pending_tasks", [])
        completed = state.get("completed_tasks", [])

        result = sales_subgraph.invoke({"messages": state["messages"]})

        return {
            "messages": result["messages"],
            "pending_tasks": pending,
            "completed_tasks": completed + ["sales"],
            "current_agent": "sales"
        }

    def call_admin_agent(state: SupervisorState) -> SupervisorState:
        """
        调用客户管理子Agent

        执行流程与 call_tech_agent 相同
        """
        print("[Supervisor] 调用 Admin 子图...")

        pending = state.get("pending_tasks", [])
        completed = state.get("completed_tasks", [])

        result = admin_subgraph.invoke({"messages": state["messages"]})

        return {
            "messages": result["messages"],
            "pending_tasks": pending,
            "completed_tasks": completed + ["admin"],
            "current_agent": "admin"
        }

    # 创建主管图
    builder = StateGraph(SupervisorState)

    # 添加所有节点
    builder.add_node("supervisor", supervisor_node)  # 主管节点
    builder.add_node("tech_agent", call_tech_agent)  # 技术子Agent
    builder.add_node("sales_agent", call_sales_agent)  # 销售子Agent
    builder.add_node("admin_agent", call_admin_agent)  # 管理子Agent

    # 添加边
    builder.add_edge(START, "supervisor")  # 起点到主管

    # supervisor_node 更新状态后，由 route_by_pending 根据 next_agent 路由
    builder.add_conditional_edges(
        "supervisor",
        route_by_pending,
        {
            "tech_agent": "tech_agent",
            "sales_agent": "sales_agent",
            "admin_agent": "admin_agent",
            END: END
        }
    )

    # ========== 子Agent完成后，如果有待处理任务则返回supervisor继续 ==========
    # 关键：pending_tasks 在 call_xxx_agent 返回时已更新
    builder.add_edge("tech_agent", "supervisor")
    builder.add_edge("sales_agent", "supervisor")
    builder.add_edge("admin_agent", "supervisor")

    return builder.compile()

# ==============================================================================
# 测试运行
# ==============================================================================

def run_examples():
    """
    运行测试示例

    测试场景:
        1. 技术问题: 登录 + 报错
        2. 销售问题: 产品价格咨询
        3. 管理问题: 账户余额查询
        4. 混合问题(循环协调): 价格 + 余额查询 - 需要多次循环协调
    """
    print("=" * 70)
    print("主管架构多智能体系统 (支持循环协调多任务)")
    print("=" * 70)

    # 编译主管图
    graph = create_supervisor_graph()

    # 定义测试用例
    test_cases = [
        {"message": "我的应用登录有问题，显示error 500"},
        {"message": "我想了解专业版的价格"},
        {"message": "查询一下我的余额，用户ID是user123"},
        {"message": "我想了解专业版的价格，另外查一下我的余额，用户ID是user123"},  # 复杂多任务
    ]

    # 遍历测试用例
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"测试案例 {i}")
        print(f"{'=' * 70}")
        print(f"用户: {test_case['message']}")
        print("-" * 50)

        # 构建初始状态
        initial_state = {
            "messages": [HumanMessage(content=test_case["message"])],
            "current_agent": "supervisor",
            "pending_tasks": [],
            "completed_tasks": [],
            "next_agent": None
        }

        try:
            # 执行图
            result = graph.invoke(initial_state)

            # 打印结果
            print("\nAI 回复:")
            for msg in result["messages"]:
                if isinstance(msg, AIMessage) and msg.content:
                    print(f"  {msg.content}")

            # 打印已完成的任务
            print(f"\n已完成任务: {result.get('completed_tasks', [])}")

        except Exception as e:
            print(f"处理失败: {e}")
            import traceback
            traceback.print_exc()

# ==============================================================================
# 程序入口  
# ==============================================================================

if __name__ == "__main__":
    run_examples()

```

交接和主管不同的使用场景：

交接：流程明确的任务，不需要并行决策，每个Agent依赖性强

主管：并行任务分配，需要有一个决策的路由节点，有一点的容错



混合使用：主管去接受请求，分解子任务，按顺序指派给交接最后汇总。（子图是走交接，父子图是主管架构）





### 预构建主管架构

```python
pip install langgraph-supervisor
```

```python
from typing import List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_provider="openai",
    model='kimi-k2.5'
)

# ============================================================================
# 模拟数据库
# ============================================================================

MOCK_ORDERS = {
    "ORD001": {
        "order_id": "ORD001",
        "customer": "张三",
        "product": "iPhone 15 Pro",
        "quantity": 1,
        "price": 8999.0,
        "status": "已发货",
        "tracking": "SF1234567890",
        "order_date": "2024-12-01"
    },
    "ORD002": {
        "order_id": "ORD002",
        "customer": "李四",
        "product": "MacBook Pro",
        "quantity": 1,
        "price": 15999.0,
        "status": "处理中",
        "tracking": None,
        "order_date": "2024-12-10"
    },
    "ORD003": {
        "order_id": "ORD003",
        "customer": "王五",
        "product": "AirPods Pro",
        "quantity": 2,
        "price": 3998.0,
        "status": "已完成",
        "tracking": "YTO9876543210",
        "order_date": "2024-11-25"
    }
}

MOCK_PRODUCTS = {
    "手机": [
        {"name": "iPhone 15 Pro", "price": 8999, "stock": 50, "rating": 4.8},
        {"name": "小米14 Ultra", "price": 5999, "stock": 100, "rating": 4.7},
        {"name": "华为Mate 60", "price": 6999, "stock": 30, "rating": 4.9}
    ],
    "电脑": [
        {"name": "MacBook Pro", "price": 15999, "stock": 20, "rating": 4.9},
        {"name": "ThinkPad X1", "price": 12999, "stock": 35, "rating": 4.6},
        {"name": "Dell XPS 15", "price": 13999, "stock": 25, "rating": 4.7}
    ],
    "耳机": [
        {"name": "AirPods Pro", "price": 1999, "stock": 200, "rating": 4.8},
        {"name": "索尼WH-1000XM5", "price": 2499, "stock": 80, "rating": 4.9},
        {"name": "Bose QC45", "price": 2299, "stock": 60, "rating": 4.7}
    ]
}

# ============================================================================
# 任务管理
# ============================================================================

class TaskStatus(Enum):
    PENDING = "待处理"
    COMPLETED = "已完成"
    FAILED = "失败"

@dataclass
class ServiceTask:
    task_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    result: str = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()

# ============================================================================
# 工具函数
# ============================================================================

@tool
def query_order(order_id: str) -> str:
    """查询订单信息"""

    order_id = order_id.strip().upper()

    if order_id in MOCK_ORDERS:
        order = MOCK_ORDERS[order_id]
        result = f"""订单信息查询结果

订单号: {order['order_id']}
客户姓名: {order['customer']}
商品名称: {order['product']}
购买数量: {order['quantity']}
订单金额: ¥{order['price']:,.2f}
订单状态: {order['status']}
下单日期: {order['order_date']}"""

        if order['tracking']:
            result += f"\n物流单号: {order['tracking']}\n物流状态: 运输中，预计3-5天送达"

        return result
    else:
        return f"未找到订单号 {order_id}，请检查订单号是否正确"

@tool
def check_logistics(tracking_number: str) -> str:
    """查询物流信息"""
    return f"""物流信息查询

物流单号: {tracking_number}
当前状态: 运输中

物流轨迹:
• 2024-12-10 14:30 - 已揽收
• 2024-12-10 18:45 - 到达转运中心
• 2024-12-11 08:20 - 运输中
• 2024-12-11 15:00 - 到达目的地城市
• 预计送达: 2024-12-12

配送员: 王师傅
联系电话: 138****5678"""

@tool
def search_products(category: str, max_price: float = None) -> str:
    """搜索产品"""
    if category not in MOCK_PRODUCTS:
        return f"未找到类别 '{category}'，可选类别: 手机、电脑、耳机"

    products = MOCK_PRODUCTS[category]

    if max_price:
        products = [p for p in products if p['price'] <= max_price]

    if not products:
        return f"在 {category} 类别中未找到符合条件的产品"

    result = f"{category} 产品推荐\n\n"

    for i, product in enumerate(products, 1):
        result += f"{i}. {product['name']}\n"
        result += f"价格: ¥{product['price']:,}\n"
        result += f"库存: {product['stock']} 件\n"
        result += f"评分: {product['rating']}/5.0\n"
        result += f"{'推荐' if product['rating'] >= 4.8 else '👍 不错'}\n\n"

    return result

@tool
def compare_products(product_names: str) -> str:
    """比较产品"""
    names = [n.strip() for n in product_names.split(',')]

    result = "产品对比分析\n\n"

    found_products = []
    for category, products in MOCK_PRODUCTS.items():
        for product in products:
            if product['name'] in names:
                found_products.append(product)

    if len(found_products) < 2:
        return "请提供至少两个有效的产品名称进行对比"

    result += "| 产品名称 | 价格 | 库存 | 评分 |\n"
    result += "|---------|------|------|------|\n"

    for product in found_products:
        result += f"| {product['name']} | ¥{product['price']:,} | {product['stock']} | {product['rating']} |\n"

    best = max(found_products, key=lambda x: x['rating'])
    cheapest = min(found_products, key=lambda x: x['price'])

    result += f"\n推荐建议:\n"
    result += f"• 性价比之选: {cheapest['name']} (¥{cheapest['price']:,})\n"
    result += f"• 口碑最佳: {best['name']} (评分 {best['rating']})\n"

    return result

@tool
def submit_return_request(order_id: str, reason: str) -> str:
    """提交退货申请"""
    order_id = order_id.strip().upper()

    if order_id not in MOCK_ORDERS:
        return f"订单号 {order_id} 不存在"

    order = MOCK_ORDERS[order_id]
    return_id = f"RET-{uuid.uuid4().hex[:8].upper()}"

    return f"""退货申请已提交

退货单号: {return_id}
订单号: {order_id}
商品名称: {order['product']}
退货原因: {reason}
申请时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

处理流程:
1. 申请已提交   
2. 等待审核 (1-2个工作日)
3. 审核通过后安排上门取件
4. 收到商品后退款

预计退款时间: 3-7个工作日
客服电话: 400-123-4567"""

@tool
def submit_complaint(complaint_type: str, description: str) -> str:
    """提交投诉"""
    complaint_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"

    return f"""投诉已受理

投诉单号: {complaint_id}
投诉类型: {complaint_type}
投诉内容: {description}
受理时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

处理承诺:
• 24小时内专人联系
• 3个工作日内给出处理方案
• 全程跟踪直至问题解决

客服热线: 400-123-4567"""

# ============================================================================
# 创建智能体
# ============================================================================

def create_order_agent():
    """订单查询智能体"""
    return create_agent(
        model=llm,
        tools=[query_order, check_logistics],
        system_prompt=(
            "你是订单查询专员。\n"
            "使用工具查询实际数据，用中文回复。\n"
            "获得结果后直接回复，不要调用其他工具。"
        ),
        name="order_agent"
    )

def create_recommend_agent():
    """产品推荐智能体"""
    return create_agent(
        model=llm,
        tools=[search_products, compare_products],
        system_prompt=(
            "你是产品推荐专员。\n"
            "使用工具搜索实际产品数据，用中文回复。\n"
            "获得结果后直接回复，不要调用其他工具。"
        ),
        name="recommend_agent"
    )

def create_service_agent():
    """售后服务智能体"""
    return create_agent(
        model=llm,
        tools=[submit_return_request],
        system_prompt=(
            "你是售后服务专员。\n"
            "使用工具提交实际申请，用中文回复。\n"
            "获得结果后直接回复，不要调用其他工具。"
        ),
        name="service_agent"
    )

def create_complaint_agent():
    """投诉处理智能体"""
    return create_agent(
        model=llm,
        tools=[submit_complaint],
        system_prompt=(
            "你是投诉处理专员。\n"
            "使用工具提交实际投诉记录，用中文回复。\n"
            "获得结果后直接回复，不要调用其他工具。"
        ),
        name="complaint_agent"
    )

# ============================================================================
# 优化的客户服务系统
# ============================================================================

class CustomerServiceSystem:
    """客户服务系统"""

    def __init__(self):
        self.tasks: List[ServiceTask] = []
        self.supervisor = self._create_supervisor()

    def _create_supervisor(self):
        """创建supervisor"""
        return create_supervisor(
            model=llm,
            agents=[
                create_order_agent(),
                create_recommend_agent(),
                create_service_agent(),
                create_complaint_agent()
            ],
            prompt=(
                "你是客户服务主管，协调四个团队:\n"
                "• order_agent - 订单查询、物流追踪\n"
                "• recommend_agent - 产品推荐、产品对比\n"
                "• service_agent - 退换货、售后服务\n"
                "• complaint_agent - 投诉受理、问题反馈\n\n"
                "根据需求选择合适团队，直接转发结果。\n"
                "不要总结或改写，专员完成后任务即结束。"
            ),
            add_handoff_back_messages=True,  # 关键：禁用回传
            output_mode="full_history"
        ).compile()

    def add_task(self, description: str) -> str:
        """添加任务"""
        task = ServiceTask(
            task_id=f"TASK-{len(self.tasks) + 1:03d}",
            description=description
        )
        self.tasks.append(task)
        print(f"[{task.task_id}] {description[:50]}...")
        return task.task_id

    def add_batch_tasks(self, descriptions: List[str]):
        """批量添加任务"""
        print(f"\n添加 {len(descriptions)} 个任务")
        print("=" * 60)
        for desc in descriptions:
            self.add_task(desc)
        print("=" * 60)

    def process_all_tasks(self):
        """处理所有任务"""
        pending_tasks = [t for t in self.tasks if t.status == TaskStatus.PENDING]

        if not pending_tasks:
            print("没有待处理的任务")
            return

        print(f"处理 {len(pending_tasks)} 个任务")
        print("=" * 60)

        for i, task in enumerate(pending_tasks, 1):
            print(f"\n[{i}/{len(pending_tasks)}] {task.task_id}: {task.description}")
            print("-" * 60)

            try:
                # 使用 invoke() 获取完整结果
                result = self.supervisor.invoke({"messages": [HumanMessage(content=task.description)]})

                print("\n" + "=" * 70)
                print("多智能体协作流程解析")
                print("=" * 70)

                # 用于记录流程步骤
                steps = []  # (step_num, agent, action, content)
                current_agent = "用户"
                step_num = 0

                # 用于去重
                seen_tools = set()
                seen_transfers = set()

                if "messages" in result:
                    for msg in result["messages"]:
                        msg_type = type(msg).__name__
                        msg_name = getattr(msg, 'name', None) or getattr(msg, 'type', 'unknown')

                        # 人类消息
                        if isinstance(msg, HumanMessage):
                            current_agent = "用户"
                            content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                            steps.append((step_num, current_agent, "输入", content))
                            step_num += 1

                        # AI 消息 - 检查工具调用
                        elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_name = tc.get('name', 'unknown')

                                # 判断是 Agent 转移还是工具调用
                                if 'transfer' in tool_name.lower():
                                    if 'back' in tool_name.lower():
                                        # 转移回 supervisor
                                        current_agent = msg_name
                                        if tool_name not in seen_transfers:
                                            seen_transfers.add(tool_name)
                                            steps.append((step_num, current_agent, "转移回", f"→ {tool_name}"))
                                            step_num += 1
                                else:
                                    # 工具调用
                                    current_agent = msg_name
                                    args_str = str(tc.get('args', {}))[:50]
                                    if tool_name not in seen_tools:
                                        seen_tools.add(tool_name)
                                        steps.append((step_num, current_agent, "工具调用", f"{tool_name}({args_str})"))
                                        step_num += 1

                        # 工具消息 - 工具返回结果
                        elif isinstance(msg, ToolMessage):
                            tool_name = getattr(msg, 'name', 'unknown')
                            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                            content = content.replace('\n', ' ')  # 单行显示
                            steps.append((step_num, current_agent, "结果返回", content))
                            step_num += 1

                        # AI 消息 - 最终回复（无工具调用）
                        elif hasattr(msg, 'content') and msg.content and msg_name != 'unknown':
                            # 跳过转移消息和空消息
                            if 'transfer' not in msg.content.lower() and msg.content.strip():
                                current_agent = msg_name
                                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                                content = content.replace('\n', ' ')
                                steps.append((step_num, current_agent, "最终回复", content))
                                step_num += 1

                # 打印流程
                print()
                for step in steps:
                    step_num, agent, action, content = step
                    print(f"步骤 {step_num}: [{agent}]")
                    print(f"  {action}: {content}")
                    print()

                # 统计信息
                print("=" * 70)
                print("统计信息")
                print("=" * 70)

                # 统计 Agent 调用
                agent_calls = {}
                tool_calls_count = {}
                for step in steps:
                    _, agent, action, _ = step
                    if agent not in ["用户"]:
                        if "工具调用" in action:
                            tool_name = action.split("(")[0].replace("工具调用", "").strip()
                            tool_calls_count[tool_name] = tool_calls_count.get(tool_name, 0) + 1
                        else:
                            agent_calls[agent] = agent_calls.get(agent, 0) + 1

                print(f"Agent 调用顺序: {' → '.join(agent_calls.keys())}")
                print(f"工具调用次数: {len(seen_tools)}")
                if tool_calls_count:
                    print("工具使用明细:")
                    for tool, count in tool_calls_count.items():
                        print(f"  • {tool}: {count}次")

                # 保存结果
                task.status = TaskStatus.COMPLETED

                print("\n任务完成")
                print("=" * 70)

            except Exception as e:
                print(f"失败: {e}")
                task.status = TaskStatus.FAILED
                import traceback
                traceback.print_exc()
                print("=" * 60)

        self.print_summary()

    def print_summary(self):
        """打印摘要"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

        print(f"\n摘要: 总计 {total} | 完成 {completed} | 失败 {failed}")

# ============================================================================
# 演示
# ============================================================================

def run_demo():
    """运行演示"""
    print("智能客户服务系统")
    print("=" * 60)

    system = CustomerServiceSystem()

    tasks = [
        # "我想查询订单号 ORD001 的物流信息",
        "我想买一部5000-7000元的手机，有什么推荐？然后还想查询一下订单号 ORD001 的物流信息",
        # "我的订单 ORD002 想申请退货，商品有质量问题",
        # "请帮我对比 iPhone 15 Pro 和 小米14 Ultra",
        # "快递员态度很差，而且送货延迟了3天，我要投诉"
    ]

    system.add_batch_tasks(tasks)
    system.process_all_tasks()

def main():
    try:
        run_demo()
    except Exception as e:
        print(f"程序错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

```

langgraph何时使用：当业务流程清晰，且复杂需要更精细的手动控制

create\_agent: 简单业务，create\_agent里面是一个黑盒，你不能控制Agent的下一步该做什么。（不可控）

