# MCP 定义与设计

#### MCP 的工作原理与使用场景

##### 基础题：MCP 是什么？它解决了什么问题？

**难度级别**：⭐（MCP基础概念）

MCP（Model Context Protocol）是 Anthropic 推出的工具调用标准化协议，核心目标是解决 Agent 工具生态的碎片化问题。传统方式下每个工具有不同的 API 格式、认证方式和错误处理逻辑，集成成本很高。MCP 定义了统一的工具发现、调用和错误处理格式，让 Agent 可以用同一套方式集成任意 MCP 兼容的工具。

---

##### 进阶题：请解释 MCP 的核心工作原理，与传统 API 调用相比有什么优势？在什么场景下应该使用 MCP？

**难度级别**：⭐⭐（MCP三组件架构、工具动态发现、与直接API调用的对比、适用场景）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 首先是核心架构
- 其次是与直接 API 调用的核心差异
- 最后是适用场景

**2️⃣ Impressive Answer**

我会从3个角度思考这个问题：

1. **首先是核心架构**。MCP 由三个组件构成：MCP Client（Agent侧，负责连接Server、管理工具列表、发起调用）、MCP Server（工具侧，提供工具元数据、执行调用、返回结果）、MCP Protocol（标准化通信格式）。启动流程是：Client 连接 Server → Server 返回工具列表（含 name/description/parameters）→ LLM 选择工具 → Client 发起调用 → Server 执行并返回结果。

1. **其次是与直接 API 调用的核心差异**。直接调用 API 需要为每个工具单独开发适配器、手动维护工具列表、各自处理参数验证和错误格式；MCP 是一次集成支持所有 MCP 工具，工具列表动态发现无需手动维护，参数基于 JSON Schema 自动验证，错误格式统一处理。本质上 MCP 把工具集成的"一次性成本"变成了"一次投入、无限复用"。

1. **最后是适用场景**。MCP 特别适合：集成10个以上外部工具的企业级 Agent（大幅降低集成成本）、多个 Agent 共享同一工具库（Server 作为统一提供者，避免重复开发）、工具需要动态更新的场景（新增工具无需重启 Agent）。工具数量少且格式固定时，直接 API 调用反而更简单。

![MCP.jpeg](03-Agent-基础-MCP-定义与设计-image-001.jpg)

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
只说&quot;标准化协议&quot;
</td>
<td>
清楚说明 Client/Server/Protocol 三组件和通信流程
</td>
</tr>
<tr>
<td>
与API对比
</td>
<td>
只说&quot;MCP更简单&quot;
</td>
<td>
从集成成本、工具发现、参数验证、可扩展性四个维度做对比
</td>
</tr>
<tr>
<td>
适用场景
</td>
<td>
只说&quot;多工具集成&quot;
</td>
<td>
给出三个具体场景并说明选择 MCP 的理由
</td>
</tr>
<tr>
<td>
给面试官的印象
</td>
<td>
了解 MCP 的存在
</td>
<td>
理解 MCP 的设计原理，能在实际项目中合理选择使用时机
</td>
</tr>
</table>

---

##### 进阶题：MCP 的三层架构（Host / Client / Server）是如何工作的？

**难度**：⭐⭐（MCP 架构、通信机制、各层职责）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- 各层职责
- MCP 的三层架构各司其职，理解清楚才能正确设计系统
- ```mermaid graph LR subgraph Host["Host（宿主应用）"] LLM["LLM 推理引擎"] MC["MCP Client"] end
- subgraph Servers["MCP Servers"] S1["MCP Server A\n（文件系统）"] S2["MCP Server B\n（数据库）"] S3[...
- LLM --> MC MC -->|stdio / SSE| S1 MC -->|stdio / SSE| S2 MC -->|stdio / SSE| S3 ```
- 层级 职责 典型实现 Host 宿主应用，管理 LLM 和 MCP Client 生命周期 Claude Desktop、IDE 插件、自研 Agent Client 维护与 ...

**2️⃣ Impressive Answer**：

MCP 的三层架构各司其职，理解清楚才能正确设计系统：

```mermaid
graph LR
    subgraph Host["Host（宿主应用）"]
        LLM["LLM 推理引擎"]
        MC["MCP Client"]
    end

    subgraph Servers["MCP Servers"]
        S1["MCP Server A\n（文件系统）"]
        S2["MCP Server B\n（数据库）"]
        S3["MCP Server C\n（Web 搜索）"]
    end

    LLM --> MC
    MC -->|stdio / SSE| S1
    MC -->|stdio / SSE| S2
    MC -->|stdio / SSE| S3
```

**各层职责**：

<table>
<tr>
<td>
层级
</td>
<td>
职责
</td>
<td>
典型实现
</td>
</tr>
<tr>
<td>
<strong>Host</strong>
</td>
<td>
宿主应用，管理 LLM 和 MCP Client 生命周期
</td>
<td>
Claude Desktop、IDE 插件、自研 Agent
</td>
</tr>
<tr>
<td>
<strong>Client</strong>
</td>
<td>
维护与 Server 的连接，转发工具调用请求
</td>
<td>
MCP SDK 内置，通常无需自己实现
</td>
</tr>
<tr>
<td>
<strong>Server</strong>
</td>
<td>
暴露 Resources/Tools/Prompts，处理调用请求
</td>
<td>
开发者自己实现的工具服务
</td>
</tr>
</table>

---

##### 进阶题：MCP 的工具调用和普通 HTTP API 调用有什么本质区别？

**难度**：⭐⭐（协议语义、工具发现、上下文感知、标准化程度）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- 调用方知道要调用什么、参数是什么（硬编码）
- 接口文档给人看，人来决定如何调用
- 无自描述能力，调用方需要提前了解 API
- 动态发现：调用方（LLM）不预先知道有哪些工具，通过 tools/list
- 工具描述（description）给 LLM 看，LLM 自主决定是否调用、如何调用
- 语义自描述：工具有能力，LLM 能理解工具的用途和参数含义

**2️⃣ Impressive Answer**：

两者的本质区别在于**谁是调用方**以及**调用的语义层次**：

**HTTP API（为人/程序设计）**：

- 调用方知道要调用什么、参数是什么（硬编码）

- 接口文档给人看，人来决定如何调用

- 无自描述能力，调用方需要提前了解 API

**MCP Tool（为 LLM 设计）**：

- 调用方（LLM）不预先知道有哪些工具，通过 `tools/list` **动态发现**

- 工具描述（description）给 LLM 看，LLM 自主决定是否调用、如何调用

- 工具有**语义自描述**能力，LLM 能理解工具的用途和参数含义

```
HTTP API 调用流程：
开发者 → 查文档 → 硬编码调用 → 固定结果

MCP Tool 调用流程：
LLM → tools/list 发现工具 → 理解工具语义 → 自主决定调用 → 动态结果
```

**关键差异**：MCP 工具的 `description` 字段是**给 LLM 的自然语言说明**，这是 HTTP API 没有的概念。description 写得好不好，直接影响 LLM 能否正确选择和使用工具。

```java
// 好的 description（LLM 能准确理解）
@Tool(description = "查询指定城市的实时天气，支持中英文城市名，返回温度、湿度、天气状况")

// 差的 description（LLM 可能误用）
@Tool(description = "天气查询")
```

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
核心差异
</td>
<td>
只说了格式不同
</td>
<td>
指出&quot;调用方是 LLM&quot;的本质差异
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
无
</td>
<td>
解释了动态发现和语义自描述
</td>
</tr>
<tr>
<td>
实践洞察
</td>
<td>
无
</td>
<td>
强调 description 质量的重要性
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道两者不同
</td>
<td>
理解 MCP 的设计哲学
</td>
</tr>
</table>

---

##### 进阶题：如何在 SpringAI 中接入 MCP Server？动态工具发现是如何实现的？

**难度**：⭐⭐⭐（MCP Client 接入、动态工具发现、工具注入机制）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- Step1：配置 MCP Client
- Step2：注入工具到 ChatClient
- 动态工具发现的原理
- 动态发现的优势

**2️⃣ Impressive Answer**：

SpringAI 的 MCP Client 接入分三步：

**Step1：配置 MCP Client**

```yaml
spring:
  ai:
    mcp:
      client:
        # 配置多个 MCP Server
        servers:
          weather-server:
            transport: stdio
            command: java
            args: ["-jar", "/path/to/weather-mcp-server.jar"]
          database-server:
            transport: sse
            url: http://localhost:8081/mcp
```

**Step2：注入工具到 ChatClient**

```java
@Service
public class AgentService {

    private final ChatClient chatClient;

    public AgentService(ChatClient.Builder builder,
                        McpSyncClientCustomizer mcpCustomizer) {
        // MCP 工具自动注入到 ChatClient
        this.chatClient = builder
            .defaultAdvisors(new McpToolCallbackAdvisor(mcpCustomizer))
            .build();
    }

    public String chat(String userMessage) {
        return chatClient.prompt()
            .user(userMessage)
            .call()
            .content();
    }
}
```

**动态工具发现的原理**：

```
Agent 启动
  → MCP Client 连接所有配置的 Server
  → 调用每个 Server 的 tools/list 接口
  → 获取工具名称、描述、参数 Schema
  → 转换为 FunctionCallback 注册到 ChatClient
  → LLM 推理时，工具 Schema 自动注入 System Prompt
  → LLM 返回工具调用意图 → MCP Client 路由到对应 Server 执行
```

**动态发现的优势**：新增工具只需在 Server 端注册，Client 无需修改代码，下次连接自动发现。

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
实现深度
</td>
<td>
只说了配置
</td>
<td>
有完整的 YAML + Java 代码
</td>
</tr>
<tr>
<td>
原理理解
</td>
<td>
说&quot;框架自动&quot;
</td>
<td>
解释了 tools/list 发现机制
</td>
</tr>
<tr>
<td>
工程价值
</td>
<td>
无
</td>
<td>
强调了动态发现的扩展性优势
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
用过 MCP
</td>
<td>
理解 MCP 接入的完整链路
</td>
</tr>
</table>

---

##### 进阶题：MCP Server 的三类能力（Resources/Tools/Prompts）有什么区别？

**难度**：⭐⭐（MCP 能力模型、使用场景、设计原则）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- 特点：无副作用，幂等，可缓存
- 示例：读取文件内容、查询数据库记录、获取 API 文档
- 特点：可能修改状态，需要权限控制
- 示例：发送邮件、写入文件、调用外部 API、执行 SQL
- 特点：标准化常用 Prompt，减少重复编写
- 示例：代码审查模板、SQL 生成模板、翻译模板

**2️⃣ Impressive Answer**：

三类能力的核心区别在于**交互模式**：

**Resources（资源）**：只读的数据访问，类似文件系统

- 特点：无副作用，幂等，可缓存

- 示例：读取文件内容、查询数据库记录、获取 API 文档

```json
{
  "uri": "file:///project/README.md",
  "name": "项目说明文档",
  "mimeType": "text/markdown"
}
```

**Tools（工具）**：有副作用的操作执行，类似函数调用

- 特点：可能修改状态，需要权限控制

- 示例：发送邮件、写入文件、调用外部 API、执行 SQL

```json
{
  "name": "send_email",
  "description": "发送邮件给指定收件人",
  "inputSchema": {
    "type": "object",
    "properties": {
      "to": {"type": "string"},
      "subject": {"type": "string"},
      "body": {"type": "string"}
    }
  }
}
```

**Prompts（提示词模板）**：可复用的 Prompt 片段，支持参数化

- 特点：标准化常用 Prompt，减少重复编写

- 示例：代码审查模板、SQL 生成模板、翻译模板

```json
{
  "name": "code_review",
  "description": "代码审查提示词",
  "arguments": [
    {"name": "language", "description": "编程语言"},
    {"name": "code", "description": "待审查代码"}
  ]
}
```

**设计原则**：能用 Resources 就不用 Tools（减少副作用风险）；Prompts 适合团队共享标准化的 Prompt 资产。

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
区分维度
</td>
<td>
只说了用途
</td>
<td>
用&quot;交互模式&quot;和&quot;副作用&quot;来区分
</td>
</tr>
<tr>
<td>
代码示例
</td>
<td>
无
</td>
<td>
有三类能力的 JSON Schema 示例
</td>
</tr>
<tr>
<td>
设计原则
</td>
<td>
无
</td>
<td>
给出了选择建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道三类
</td>
<td>
能指导 MCP Server 设计
</td>
</tr>
</table>

---

##### 进阶题：MCP 和 Function Calling 的本质区别是什么？

**难度**：⭐⭐⭐（协议层 vs 调用层、标准化程度、工具复用性）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- 定义了模型如何描述工具（JSON Schema）和如何返回调用意图
- 每个模型厂商格式不同（OpenAI、Claude、Gemini 各有差异）
- 工具实现和模型强绑定，换模型要改代码
- 定义了 Client 和 Server 之间的完整通信规范（发现、调用、响应）
- 工具实现一次，任何支持 MCP 的模型都能用
- 工具和模型完全解耦

**2️⃣ Impressive Answer**：

两者的区别不是"谁提出的"，而是**所处的抽象层次不同**：

**Function Calling 是"调用约定"**（Call Convention）：

- 定义了模型如何描述工具（JSON Schema）和如何返回调用意图

- 每个模型厂商格式不同（OpenAI、Claude、Gemini 各有差异）

- 工具实现和模型强绑定，换模型要改代码

**MCP 是"通信协议"**（Communication Protocol）：

- 定义了 Client 和 Server 之间的完整通信规范（发现、调用、响应）

- 工具实现一次，任何支持 MCP 的模型都能用

- 工具和模型完全解耦

**类比**：

```
Function Calling ≈ 每家餐厅有自己的点餐方式（有的用 App，有的用纸质菜单）
MCP ≈ 统一的外卖平台协议（美团/饿了么），餐厅接入一次，所有平台都能点
```

**实际影响**：

<table>
<tr>
<td>
对比维度
</td>
<td>
Function Calling
</td>
<td>
MCP
</td>
</tr>
<tr>
<td>
工具复用性
</td>
<td>
低（绑定特定模型/框架）
</td>
<td>
高（跨模型、跨框架）
</td>
</tr>
<tr>
<td>
工具发现
</td>
<td>
静态（代码里写死）
</td>
<td>
动态（运行时 tools/list 发现）
</td>
</tr>
<tr>
<td>
工具生态
</td>
<td>
碎片化
</td>
<td>
统一生态（MCP Server 市场）
</td>
</tr>
<tr>
<td>
实现复杂度
</td>
<td>
低（直接写函数）
</td>
<td>
中（需要实现 MCP Server）
</td>
</tr>
<tr>
<td>
适用场景
</td>
<td>
单模型、快速开发
</td>
<td>
多模型、工具复用、企业级
</td>
</tr>
</table>

**结论**：MCP 不是替代 Function Calling，而是在其上层提供了标准化的工具生态层。底层仍然依赖模型的 Function Calling 能力来触发工具调用。

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
核心洞察
</td>
<td>
只说了谁提出的
</td>
<td>
指出&quot;抽象层次不同&quot;是本质
</td>
</tr>
<tr>
<td>
类比能力
</td>
<td>
无
</td>
<td>
用餐厅/外卖平台类比，易于理解
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
概念层面
</td>
<td>
有详细的对比表格
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道两者
</td>
<td>
理解两者的关系和定位
</td>
</tr>
</table>

---

---

---

##### 场景题：MCP 工具调用的权限控制和安全设计如何做？

**难度**：⭐⭐⭐（工具权限、沙箱隔离、审计日志、最小权限原则）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- 文件系统工具：限制访问路径（只允许访问指定目录）
- 代码执行工具：在容器/JVM 沙箱中运行，限制网络和文件访问
- 数据库工具：使用只读账号，或限制可操作的表

**2️⃣ Impressive Answer**：

MCP 工具的安全设计需要**纵深防御**，从三个层次来考虑：

**1. 工具级权限控制**

```java
@Component
public class McpToolSecurityInterceptor {

    public ToolResult intercept(ToolCall call, ToolExecutor executor) {
        // 工具白名单：只允许调用预定义的工具
        if (!allowedTools.contains(call.getToolName())) {
            return ToolResult.error("工具未授权：" + call.getToolName());
        }

        // 参数安全校验：防止注入攻击
        validateParams(call.getParams());

        // 执行工具
        ToolResult result = executor.execute(call);

        // 审计日志
        auditLogger.log(AuditEvent.builder()
            .toolName(call.getToolName())
            .params(call.getParams())
            .result(result.isSuccess() ? "SUCCESS" : "FAILED")
            .timestamp(Instant.now())
            .build());

        return result;
    }
}
```

**2. 沙箱隔离**

- 文件系统工具：限制访问路径（只允许访问指定目录）

- 代码执行工具：在容器/JVM 沙箱中运行，限制网络和文件访问

- 数据库工具：使用只读账号，或限制可操作的表

**3. 人工确认机制（Human-in-the-Loop）**
高风险操作（删除数据、发送邮件、转账）在执行前暂停，等待人工确认：

```java
if (tool.getRiskLevel() == RiskLevel.HIGH) {
    String confirmationToken = humanApprovalService.requestApproval(call);
    // 等待人工确认，超时则拒绝
    boolean approved = humanApprovalService.waitForApproval(confirmationToken, Duration.ofMinutes(5));
    if (!approved) return ToolResult.error("操作被拒绝或超时");
}
```

**最小权限原则**：每个 MCP Server 只暴露完成任务所需的最小工具集，避免过度授权。

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
防御层次
</td>
<td>
单层（权限校验）
</td>
<td>
三层（权限+沙箱+人工确认）
</td>
</tr>
<tr>
<td>
代码深度
</td>
<td>
无
</td>
<td>
有拦截器和审计日志实现
</td>
</tr>
<tr>
<td>
安全思维
</td>
<td>
被动防御
</td>
<td>
纵深防御 + 最小权限原则
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道要做权限
</td>
<td>
能设计企业级安全方案
</td>
</tr>
</table>

---

##### 场景题：如何用 Java 实现一个 MCP Server？

**难度**：⭐⭐⭐（MCP Server 实现、工具注册、参数 Schema 定义）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- 工具描述（description）要清晰，这是 LLM 选择工具的依据
- 参数 Schema 要精确，减少 LLM 参数生成错误
- 工具执行要有超时和错误处理

**2️⃣ Impressive Answer**：

用 Spring AI 的 MCP Server 支持（`spring-ai-mcp-server`）实现最为简洁：

**Step1：添加依赖**

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-mcp-server-spring-boot-starter</artifactId>
</dependency>
```

**Step2：实现工具**

```java
@Service
public class WeatherMcpServer {

    // 用 @Tool 注解声明 MCP Tool
    @Tool(description = "查询指定城市的实时天气信息")
    public WeatherInfo getWeather(
            @ToolParam(description = "城市名称，如：北京、上海") String city,
            @ToolParam(description = "温度单位：celsius 或 fahrenheit", required = false)
            String unit) {

        // 实际调用天气 API
        return weatherApiClient.query(city, unit != null ? unit : "celsius");
    }

    // 声明 MCP Resource
    @Resource(uri = "weather://cities/list", description = "支持查询的城市列表")
    public String getCityList() {
        return String.join(",", supportedCities);
    }
}
```

**Step3：配置启动方式**

```yaml
spring:
  ai:
    mcp:
      server:
        transport: stdio   # 本地工具用 stdio，远程服务用 sse
        name: weather-mcp-server
        version: 1.0.0
```

**Step4：工具发现流程**

```
Client 连接 → 调用 initialize → 调用 tools/list → 获取所有工具 Schema
→ 注入 LLM System Prompt → LLM 按需调用 → Server 执行并返回结果
```

**关键设计点**：

- 工具描述（description）要清晰，这是 LLM 选择工具的依据

- 参数 Schema 要精确，减少 LLM 参数生成错误

- 工具执行要有超时和错误处理

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
实现深度
</td>
<td>
只说了步骤
</td>
<td>
有完整的代码实现
</td>
</tr>
<tr>
<td>
框架选择
</td>
<td>
无
</td>
<td>
使用 Spring AI MCP 注解式开发
</td>
</tr>
<tr>
<td>
工程细节
</td>
<td>
无
</td>
<td>
提到描述质量影响 LLM 选择工具
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道怎么做
</td>
<td>
能直接上手实现
</td>
</tr>
</table>

---

#### 如何开发和部署自定义的 MCP Server

##### 基础题：MCP Server 最核心的两个接口是什么？

**难度级别**：⭐（MCP Server 接口基础）

MCP Server 最核心的两个接口是 `tools/list` 和 `tools/call`。`tools/list` 返回 Server 提供的所有工具元数据（name、description、inputSchema），让 Agent 知道有哪些工具可用；`tools/call` 负责执行具体的工具调用并返回结果。其余接口（resources/list、prompts/list 等）是可选的，按需实现。

---

##### 进阶题：请介绍如何开发一个自定义的 MCP Server？部署时需要注意什么？如何调试？

**难度级别**：⭐⭐⭐（核心接口、开发流程、部署方式、调试工具）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 首先是开发流程
- 其次是部署方式的选择
- 最后是调试

**2️⃣ Impressive Answer**

我会从3个角度思考这个问题：

1. **首先是开发流程**。用 Python MCP SDK 开发，核心是用 `@app.tool()` 装饰器定义工具，装饰器里写清楚 name、description 和 inputSchema（JSON Schema 格式）。工具函数本身就是普通的 async 函数，返回 TextContent 或 structured result。SDK 会自动把这些工具注册到 `tools/list` 和 `tools/call` 接口上。

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("my-server")

@app.tool()
async def query_customer(customer_id: str) -> TextContent:
    """根据ID查询客户信息"""
    result = await db.query(customer_id)
    return TextContent(type="text", text=str(result))
```

1. **其次是部署方式的选择**。本地部署走 stdio 传输，Agent 和 Server 在同一台机器，延迟低、安全性高，适合开发和单机场景；远程部署走 HTTP，适合多 Agent 共享工具的场景，需要额外处理认证、限流和网络问题。生产环境远程部署必须配置认证防止未授权访问，并做好限流和熔断保护 Server。

1. **最后是调试**。官方提供 MCP Inspector 工具，可以连接 Server 查看工具列表、测试单个工具调用、查看完整的请求响应日志。调试时重点测试边界情况：空参数、超大参数、错误类型参数，确保 Server 的错误处理逻辑符合 MCP 协议规范。

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
核心接口
</td>
<td>
只说&quot;几个接口&quot;
</td>
<td>
明确 tools/list 和 tools/call 是核心，其余可选
</td>
</tr>
<tr>
<td>
开发方式
</td>
<td>
只说&quot;用SDK&quot;
</td>
<td>
给出装饰器定义工具的具体写法和结构
</td>
</tr>
<tr>
<td>
部署选择
</td>
<td>
只说&quot;本地或远程&quot;
</td>
<td>
说明两种方式的优缺点和适用场景，指出远程部署的安全要求
</td>
</tr>
<tr>
<td>
调试手段
</td>
<td>
只说&quot;看日志&quot;
</td>
<td>
MCP Inspector + 边界用例测试的完整调试方法
</td>
</tr>
<tr>
<td>
给面试官的印象
</td>
<td>
了解 MCP Server 概念
</td>
<td>
有完整的从开发到部署的实践经验
</td>
</tr>
</table>

---

##### 场景题：开发了一个 MCP Server 提供数据库查询工具，上线后 Agent 调用响应很慢，如何排查优化？

**难度级别**：⭐⭐⭐（性能排查、工具链路分析、MCP Server 优化）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 分三段排查：第一段是 MCP 调用链路，用 MCP Inspector 记录 tools/call 的端到端耗时，判断瓶颈在网络传输还是 Server 内部处理；第二段是 Se...

**2️⃣ Impressive Answer**

分三段排查：第一段是 MCP 调用链路，用 MCP Inspector 记录 tools/call 的端到端耗时，判断瓶颈在网络传输还是 Server 内部处理；第二段是 Server 内部，在工具函数里加计时日志，分离出"数据库查询耗时"和"结果序列化耗时"；第三段是数据库层，检查查询是否命中索引、是否有 N+1 查询问题。找到瓶颈后针对性优化：查询慢加索引或查询缓存（对相同参数的查询结果缓存一段时间）；序列化慢优化返回数据结构、减少不必要字段；网络延迟高把 Server 部署在离 Agent 更近的位置或改用 stdio 本地通信。

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
排查思路
</td>
<td>
猜测瓶颈
</td>
<td>
分段拆解链路，定位到具体瓶颈
</td>
</tr>
<tr>
<td>
优化方向
</td>
<td>
只想到索引和缓存
</td>
<td>
查询优化 + 序列化优化 + 部署优化多维度
</td>
</tr>
<tr>
<td>
工具使用
</td>
<td>
未提及
</td>
<td>
MCP Inspector + 埋点日志定量分析
</td>
</tr>
</table>

---

##### 容易一起考的题

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
MCP 的 transport 有哪些类型？各自适用什么场景？
</td>
<td>
部署方式的底层机制，stdio vs HTTP 的选择依据
</td>
<td>
答：MCP 的价值是把模型和外部工具/资源解耦，用统一协议暴露 tool、resource 和 prompt；面试里重点讲标准化接入、权限边界和可维护性。
</td>
</tr>
<tr>
<td>
如何给 MCP 工具的描述写得更好，让 LLM 更准确地选用？
</td>
<td>
工具的 description 和 inputSchema 质量直接影响 LLM 的工具选择准确率
</td>
<td>
答：工具 description 要写清使用场景、输入输出、限制和反例，让模型知道什么时候该用、什么时候不该用。
</td>
</tr>
<tr>
<td>
如何对 MCP Server 做认证和权限控制？
</td>
<td>
远程部署 MCP Server 的安全必要条件
</td>
<td>
答：MCP 的价值是把模型和外部工具/资源解耦，用统一协议暴露 tool、resource 和 prompt；面试里重点讲标准化接入、权限边界和可维护性。
</td>
</tr>
</table>

---

**两种通信方式**：

- **stdio**：本地进程间通信，Server 作为子进程启动，适合本地工具（文件系统、本地数据库）

- **SSE（Server-Sent Events）**：HTTP 长连接，适合远程服务、云端工具

**关键流程**：

```
1. Host 启动时，MCP Client 连接所有配置的 Server
2. Client 调用 tools/list 获取所有可用工具的 Schema
3. LLM 推理时，工具 Schema 注入 System Prompt
4. LLM 决定调用某工具 → Client 转发到对应 Server → 返回结果
```

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
架构理解
</td>
<td>
只说了三层名称
</td>
<td>
清晰描述了各层职责和交互流程
</td>
</tr>
<tr>
<td>
可视化
</td>
<td>
无
</td>
<td>
有 mermaid 架构图
</td>
</tr>
<tr>
<td>
技术细节
</td>
<td>
只提到通信方式
</td>
<td>
解释了工具发现（tools/list）机制
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道概念
</td>
<td>
能设计 MCP 接入方案
</td>
</tr>
</table>

---

##### 场景题：如何设计一个支持多租户的 MCP Server？

**难度**：⭐⭐⭐（多租户隔离、上下文传递、权限控制、数据隔离）

**1️⃣ Common Answer**：

重点总结（便于面试记忆）：

- 在无状态协议上实现有状态的租户隔离
- 身份认证（Who am I？）
- 数据隔离（What can I see？）
- 工具权限（What can I do？）

**2️⃣ Impressive Answer**：

多租户 MCP Server 的核心挑战是**在无状态协议上实现有状态的租户隔离**，需要从三个层次设计：

**1. 身份认证（Who am I？）**
MCP 协议本身不包含认证，需要在传输层注入租户信息：

```java
// SSE 传输：通过 HTTP Header 传递租户信息
@Component
public class McpTenantFilter implements Filter {
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) {
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        String tenantId = httpRequest.getHeader("X-Tenant-Id");
        String token = httpRequest.getHeader("Authorization");

        // 验证 token 并绑定租户上下文
        TenantContext.set(tenantService.authenticate(tenantId, token));
        try {
            chain.doFilter(request, response);
        } finally {
            TenantContext.clear();  // 防止线程污染
        }
    }
}
```

**2. 数据隔离（What can I see？）**

```java
@Tool(description = "查询当前租户的订单列表")
public List<Order> listOrders(
        @ToolParam(description = "页码") int page,
        @ToolParam(description = "每页数量") int size) {

    // 自动注入当前租户 ID，不允许跨租户查询
    String tenantId = TenantContext.get().getTenantId();
    return orderRepository.findByTenantId(tenantId, PageRequest.of(page, size));
}
```

**3. 工具权限（What can I do？）**
不同租户可能有不同的工具权限（如免费版 vs 企业版）：

```java
@Component
public class TenantAwareToolFilter {
    public List<ToolDefinition> filterTools(List<ToolDefinition> allTools, String tenantId) {
        TenantPlan plan = tenantService.getPlan(tenantId);
        return allTools.stream()
            .filter(tool -> plan.hasPermission(tool.getName()))
            .toList();
    }
}
```

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
设计层次
</td>
<td>
只说了传 ID
</td>
<td>
认证+数据隔离+工具权限三层设计
</td>
</tr>
<tr>
<td>
代码深度
</td>
<td>
无
</td>
<td>
有完整的多租户实现
</td>
</tr>
<tr>
<td>
工程细节
</td>
<td>
无
</td>
<td>
注意到 ThreadLocal 清理防止线程污染
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道要隔离
</td>
<td>
能设计企业级多租户方案
</td>
</tr>
</table>

##### 场景题：公司有一套内部系统（CRM、ERP、文档服务），需要让 Agent 能调用，如何设计接入方案？

**难度级别**：⭐⭐（MCP Server 设计、工具发现、安全认证）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 推荐用 MCP 方案：为 CRM、ERP、文档服务分别实现一个 MCP Server，每个 Server 暴露该系统的核心操作作为 tool（比如 CRM 的 query_cu...
- `mermaid flowchart LR A[Agent\nMCP Client] -->|tools/list\ntools/call| CRM[CRM\nMCP Serv...

**2️⃣ Impressive Answer**

推荐用 MCP 方案：为 CRM、ERP、文档服务分别实现一个 MCP Server，每个 Server 暴露该系统的核心操作作为 tool（比如 CRM 的 `query_customer`、`update_contact`）。Agent 侧用 MCP Client 统一接入所有 Server，动态获取工具列表。这样的好处是：各系统团队各自维护自己的 MCP Server，Agent 侧无需改动即可感知工具更新；内网部署走 stdio 传输，延迟低；认证在 Server 层统一处理，Agent 不需要管各系统的鉴权细节。后续新增系统只需新增一个 MCP Server，扩展成本极低。

```mermaid
flowchart LR
    A[Agent\nMCP Client] -->|tools/list\ntools/call| CRM[CRM\nMCP Server]
    A --> ERP[ERP\nMCP Server]
    A --> DOC[文档服务\nMCP Server]
    CRM --- crm_api[(CRM API)]
    ERP --- erp_api[(ERP API)]
    DOC --- doc_api[(文档 API)]
```

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
架构思路
</td>
<td>
每个系统写工具函数
</td>
<td>
MCP Server 隔离各系统，Agent 统一接入
</td>
</tr>
<tr>
<td>
可维护性
</td>
<td>
工具变化需改 Agent 代码
</td>
<td>
各系统独立维护 Server，Agent 自动感知
</td>
</tr>
<tr>
<td>
扩展性
</td>
<td>
新增系统要改 Agent
</td>
<td>
新增 MCP Server 即可，Agent 侧零改动
</td>
</tr>
</table>

---

##### 容易一起考的题

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
Function Calling 和 MCP 有什么区别？
</td>
<td>
Function Calling 是 LLM 侧的工具调用机制，MCP 是工具集成的标准化协议，两者互补
</td>
<td>
答：工具调用题要讲 schema 描述、参数校验、权限控制、超时重试、幂等和观测；核心是让模型会选、会用、用错能兜底。
</td>
</tr>
<tr>
<td>
如何实现工具的动态注册与发现？
</td>
<td>
MCP 动态发现机制的核心价值，对比静态工具注册的局限性
</td>
<td>
答：工具调用题要讲 schema 描述、参数校验、权限控制、超时重试、幂等和观测；核心是让模型会选、会用、用错能兜底。
</td>
</tr>
<tr>
<td>
Agent 如何处理工具调用的认证与授权？
</td>
<td>
MCP Server 层统一处理认证，是 MCP 相比直接 API 调用的重要优势
</td>
<td>
答：工具调用题要讲 schema 描述、参数校验、权限控制、超时重试、幂等和观测；核心是让模型会选、会用、用错能兜底。
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| MCP 的工作原理与使用场景 | 首先是核心架构：MCP 由三个组件构成：MCP Client（Agent侧，负责连接Server、管理工具列表、发起调用）、MCP Server（工具侧，提供工具元数据、执行调用、返回结果）、MCP Protocol（标准化通信格式）。启动流程是：Client 连接 Server → Server 返回工具列表（含 name/description/parameters）→ LLM 选择工具 → Client 发起调用 → Server 执行并返回结果；其次是与直接 API 调用的核心差异：直接调用 API 需要为每个工具单独开发适配器、手动维护工具列表、各自处理参数验证和错误格式；MCP 是一次集成支持所有 MCP 工具，工具列表动态发现无需手动维护，参数基于 JSON Schema 自动验证，错误格式统一处理。本质上 MCP 把工具集成的"一次性成本"变成了"一次投入、无限复用"；最后是适用场景：MCP 特别适合：集成10个以上外部工具的企业级 Agent（大幅降低集成成本）、多个 Agent 共享同一工具库（Server 作为统一提供者，避免重复开发）、工具需要动态更新的场景（新增工具无需重启 Agent）。工具数量少且格式固定时，直接 API 调用反而更简单。 |
| MCP 是什么？它解决了什么问题？ | MCP（Model Context Protocol）是 Anthropic 推出的工具调用标准化协议，核心目标是解决 Agent 工具生态的碎片化问题。传统方式下每个工具有不同的 API 格式、认证方式和错误处理逻辑，集成成本很高。MCP 定义了统一的工具发现、调用和错误处理格式，让 Agent 可以用同一套方式集成任意 MCP 兼容的工具。 |
| 请解释 MCP 的核心工作原理，与传统 API 调用相比有什么优势？在什么场景下应该使用 MCP？ | 首先是核心架构：MCP 由三个组件构成：MCP Client（Agent侧，负责连接Server、管理工具列表、发起调用）、MCP Server（工具侧，提供工具元数据、执行调用、返回结果）、MCP Protocol（标准化通信格式）。启动流程是：Client 连接 Server → Server 返回工具列表（含 name/description/parameters）→ LLM 选择工具 → Client 发起调用 → Server 执行并返回结果；其次是与直接 API 调用的核心差异：直接调用 API 需要为每个工具单独开发适配器、手动维护工具列表、各自处理参数验证和错误格式；MCP 是一次集成支持所有 MCP 工具，工具列表动态发现无需手动维护，参数基于 JSON Schema 自动验证，错误格式统一处理。本质上 MCP 把工具集成的"一次性成本"变成了"一次投入、无限复用"；最后是适用场景：MCP 特别适合：集成10个以上外部工具的企业级 Agent（大幅降低集成成本）、多个 Agent 共享同一工具库（Server 作为统一提供者，避免重复开发）、工具需要动态更新的场景（新增工具无需重启 Agent）。工具数量少且格式固定时，直接 API 调用反而更简单。 |
| MCP 的三层架构（Host / Client / Server）是如何工作的？ | Host上，职责是宿主应用，管理 LLM 和 MCP Client 生命周期，典型实现是Claude Desktop、IDE 插件、自研 Agent；Client上，职责是维护与 Server 的连接，转发工具调用请求，典型实现是MCP SDK 内置，通常无需自己实现；Server上，职责是暴露 Resources/Tools/Prompts，处理调用请求，典型实现是开发者自己实现的工具服务。 |
| MCP 的工具调用和普通 HTTP API 调用有什么本质区别？ | 调用方知道要调用什么、参数是什么（硬编码）；接口文档给人看，人来决定如何调用；无自描述能力，调用方需要提前了解 API；调用方（LLM）不预先知道有哪些工具，通过 tools/list 动态发现；工具描述（description）给 LLM 看，LLM 自主决定是否调用、如何调用。 |
| 如何在 SpringAI 中接入 MCP Server？动态工具发现是如何实现的？ | SpringAI 的 MCP Client 接入分三步：；args: ["-jar", "/path/to/weather-mcp-server.jar"]；url: http://localhost:8081/mcp。 |
| MCP Server 的三类能力（Resources/Tools/Prompts）有什么区别？ | 特点：无副作用，幂等，可缓存；示例：读取文件内容、查询数据库记录、获取 API 文档；特点：可能修改状态，需要权限控制；示例：发送邮件、写入文件、调用外部 API、执行 SQL；特点：标准化常用 Prompt，减少重复编写。 |
| MCP 和 Function Calling 的本质区别是什么？ | 定义了模型如何描述工具（JSON Schema）和如何返回调用意图；每个模型厂商格式不同（OpenAI、Claude、Gemini 各有差异）；工具实现和模型强绑定，换模型要改代码；定义了 Client 和 Server 之间的完整通信规范（发现、调用、响应）；工具实现一次，任何支持 MCP 的模型都能用。 |
| MCP 工具调用的权限控制和安全设计如何做？ | 文件系统工具：限制访问路径（只允许访问指定目录）；代码执行工具：在容器/JVM 沙箱中运行，限制网络和文件访问；数据库工具：使用只读账号，或限制可操作的表。 |
| 如何用 Java 实现一个 MCP Server？ | 工具描述（description）要清晰，这是 LLM 选择工具的依据；参数 Schema 要精确，减少 LLM 参数生成错误；工具执行要有超时和错误处理。 |
| 如何开发和部署自定义的 MCP Server | 首先是开发流程：用 Python MCP SDK 开发，核心是用 @app.tool() 装饰器定义工具，装饰器里写清楚 name、description 和 inputSchema（JSON Schema 格式）。工具函数本身就是普通的 async 函数，返回 TextContent 或 structured result。SDK 会自动把这些工具注册到 tools/list 和 tools/call 接口上；from mcp.server import Server；from mcp.types import Tool, TextContent。 |
| MCP Server 最核心的两个接口是什么？ | MCP Server 最核心的两个接口是 tools/list 和 tools/call。tools/list 返回 Server 提供的所有工具元数据（name、description、inputSchema），让 Agent 知道有哪些工具可用；tools/call 负责执行具体的工具调用并返回结果。其余接口（resources/list、prompts/list 等）是可选的，按需实现。 |
| 请介绍如何开发一个自定义的 MCP Server？部署时需要注意什么？如何调试？ | 首先是开发流程：用 Python MCP SDK 开发，核心是用 @app.tool() 装饰器定义工具，装饰器里写清楚 name、description 和 inputSchema（JSON Schema 格式）。工具函数本身就是普通的 async 函数，返回 TextContent 或 structured result。SDK 会自动把这些工具注册到 tools/list 和 tools/call 接口上；from mcp.server import Server；from mcp.types import Tool, TextContent。 |
| 开发了一个 MCP Server 提供数据库查询工具，上线后 Agent 调用响应很慢，如何排查优化？ | 分三段排查：第一段是 MCP 调用链路，用 MCP Inspector 记录 tools/call 的端到端耗时，判断瓶颈在网络传输还是 Server 内部处理；第二段是 Server 内部，在工具函数里加计时日志，分离出"数据库查询耗时"和"结果序列化耗时"；第三段是数据库层，检查查询是否命中索引、是否有 N+1 查询问题。找到瓶颈后针对性优化：查询慢加索引或查询缓存（对相同参数的查询结果缓存一段时间）；序列化慢优化返回数据结构、减少不必要字段；网络延迟高把 Server 部署在离 Agent 更近的位置或改用 stdio 本地通信。 |
| 如何设计一个支持多租户的 MCP Server？ | 多租户 MCP Server 的核心挑战是在无状态协议上实现有状态的租户隔离，需要从三个层次设计：；MCP 协议本身不包含认证，需要在传输层注入租户信息：；// SSE 传输：通过 HTTP Header 传递租户信息。 |
| 公司有一套内部系统（CRM、ERP、文档服务），需要让 Agent 能调用，如何设计接入方案？ | 推荐用 MCP 方案：为 CRM、ERP、文档服务分别实现一个 MCP Server，每个 Server 暴露该系统的核心操作作为 tool（比如 CRM 的 query_customer、update_contact）。Agent 侧用 MCP Client 统一接入所有 Server，动态获取工具列表。这样的好处是：各系统团队各自维护自己的 MCP Server，Agent 侧无需改动即可感知工具更新；内网部署走 stdio 传输，延迟低；认证在 Server 层统一处理，Agent 不需要管各系统的鉴权细节。后续新增系统只需新增一个 MCP Server，扩展成本极低；A[Agent\nMCP Client] -->\|tools/list\ntools/call\| CRM[CRM\nMCP Server]；A --> ERP[ERP\nMCP Server]。 |
