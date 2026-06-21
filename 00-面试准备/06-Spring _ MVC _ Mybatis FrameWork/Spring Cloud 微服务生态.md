#### 1、基础题：Spring Cloud Gateway 的工作原理是什么？

**难度级别**：⭐⭐（Predicate、Filter、Route、WebFlux 响应式）

**Answer**

Spring Cloud Gateway 基于 Spring WebFlux 构建，核心是三要素：

- **Predicate（断言）**：匹配请求（路径、方法、Header 等）

- **Filter（过滤器）**：请求/响应预处理（鉴权、限流、日志）

- **Route（路由）**：Predicate + Filter → 转发目标

执行流程：请求 → GatewayFilterChain（过滤器链）→ 目标服务

---

#### 2、进阶题：Spring Cloud Feign 的底层原理是什么？如何实现负载均衡和重试？

**难度级别**：⭐⭐⭐⭐（动态代理、Ribbon/LoadBalancer、Retryer、解码器）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 动态代理生成
- 负载均衡
- Spring Cloud LoadBalancer
- 重试机制
- POST/PUT 等非幂等操作要谨慎重试
- 解码与编码

**2️⃣ Impressive Answer**

1. **动态代理生成**：Feign 启动时扫描@FeignClient 接口，用 JDK 动态代理生成实现类，方法调用被拦截成 HTTP 请求（RequestTemplate）。

1. **负载均衡**：早期用 Ribbon（已废弃），现在用 **Spring Cloud LoadBalancer**。核心是 `LoadBalancerClient.choose(serviceId)` 从注册中心选实例，支持轮询、权重、Zone 感知等策略。

1. **重试机制**：Spring Cloud OpenFeign 默认不重试（幂等 GET 除外），可配置 `Retryer` 定义重试条件（间隔、次数、哪些异常）。但**POST/PUT 等非幂等操作要谨慎重试**，需业务侧保证幂等性。

1. **解码与编码**：请求参数用 Encoder 编码（Form/JSON），响应用 Decoder 解码（Jackson/Gson）。可自定义 Encoder/Decoder 处理特殊格式（如 Protobuf）。

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
说了代理和负载均衡但较浅
</td>
<td>
代理→负载均衡→重试→编解码全链路
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Ribbon 已废弃
</td>
<td>
知道 LoadBalancer 替代方案
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没说重试的风险
</td>
<td>
强调非幂等操作的重试陷阱
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 Feign
</td>
<td>
理解全链路，能处理复杂场景
</td>
</tr>
</table>

---

#### 3、场景题：Agent 调用多个微服务，如何用 Gateway 统一做鉴权和限流？

**难度级别**：⭐⭐⭐⭐（GlobalFilter、Redis 限流、JWT 解析、服务路由）

**Answer**

1. **全局鉴权 Filter**：实现 `GlobalFilter`，在 `filter()` 方法中解析 JWT Token，校验权限；失败直接返回 401，不调用 `chain.filter()`。

1. **限流策略**：基于 Redis + Lua 脚本实现令牌桶/滑动窗口，按用户 ID 或 API Key 限流；超阈值返回 429。

1. **路由隔离**：Agent 相关服务单独分组（如 `agent-service`），Gateway 配置 Predicate 路由到对应服务集群。

1. **降级兜底**：配合 Sentinel 做服务降级，后端服务不可用时返回友好错误，避免 Agent 卡死。

---

#### 4、进阶题：Nacos 作为注册中心和配置中心的核心原理？与 Eureka 的区别？

**难度级别**：⭐⭐⭐（AP vs CP 模式切换、长轮询配置推送、Raft 协议、健康检查机制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 注册中心对比
- Eureka：纯 AP 模式，节点间通过 Peer-to-Peer 复制注册表，网络分区时仍可用但数据可能不一致；客户端定时拉取（默认 30s），感知延迟较高。
- Nacos：临时实例用 AP 模式（Distro 协议），持久实例用 CP 模式（Raft 协议）。支持服务端主动推送（UDP + 长轮询兜底），服务上下线感知延迟低至秒级。

**2️⃣ Impressive Answer**

1. **注册中心对比**：

  - **Eureka**：纯 AP 模式，节点间通过 Peer-to-Peer 复制注册表，网络分区时仍可用但数据可能不一致；客户端定时拉取（默认 30s），感知延迟较高。

  - **Nacos**：临时实例用 AP 模式（Distro 协议），持久实例用 CP 模式（Raft 协议）。支持**服务端主动推送**（UDP + 长轮询兜底），服务上下线感知延迟低至秒级。

1. **配置中心原理**：客户端发起**长轮询**请求（默认 30s 超时），服务端挂起请求；配置变更时立即返回变更的 dataId，客户端再拉取最新配置。比定时轮询更实时，比 WebSocket 更轻量。

1. **健康检查差异**：Eureka 靠客户端心跳（默认 30s）；Nacos 临时实例也靠心跳，但持久实例由**服务端主动探测**（TCP/HTTP），更适合非 Java 服务。

1. **选型建议**：新项目首选 Nacos（注册 + 配置一体化）；Eureka 已停止维护（Netflix OSS 进入维护模式）。

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
只说了 AP/CP 区别
</td>
<td>
注册中心→配置中心→健康检查→选型，全面对比
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Distro 和 Raft 协议
</td>
<td>
清楚临时/持久实例的不同一致性协议
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道长轮询的实现原理
</td>
<td>
能解释配置推送的具体机制
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道 Nacos 比 Eureka 好
</td>
<td>
理解底层协议差异，能做技术选型
</td>
</tr>
</table>

---

#### 5、场景题：Agent 平台有多个版本的模型服务（GPT-4、Claude、本地模型），如何用微服务架构实现灰度路由和流量切换？

**难度级别**：⭐⭐⭐⭐（Gateway 动态路由、权重路由、Header 标签路由、Nacos 元数据）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Gateway 动态路由
- Header 标签路由：请求头带 X-Model-Version: gpt4 时，路由到对应版本的服务实例
- 权重路由：90% 流量走稳定版，10% 走灰度版，通过 Nacos 配置中心动态调整权重
- 用户维度灰度：按用户 ID 哈希取模，保证同一用户始终命中同一版本（避免体验不一致）

**2️⃣ Impressive Answer**

我设计过类似的灰度路由方案，分三层实现：

1. **Nacos 元数据标签**：每个模型服务实例注册时携带元数据（如 `model-version=gpt4`、`canary=true`），Gateway 根据元数据做路由匹配。

```yaml
# Nacos 服务注册元数据
spring:
  cloud:
    nacos:
      discovery:
        metadata:
          model-version: gpt4-turbo
          canary: true
```

1. **Gateway 动态路由**：

  - **Header 标签路由**：请求头带 `X-Model-Version: gpt4` 时，路由到对应版本的服务实例

  - **权重路由**：90% 流量走稳定版，10% 走灰度版，通过 Nacos 配置中心动态调整权重

  - **用户维度灰度**：按用户 ID 哈希取模，保证同一用户始终命中同一版本（避免体验不一致）

1. **动态切换**：路由规则存 Nacos 配置中心，修改后 Gateway 通过长轮询实时感知，**无需重启**即可切换流量比例或全量切换。

1. **回滚机制**：监控灰度版本的错误率和延迟，超过阈值自动回滚到稳定版（配合 Sentinel 熔断）。

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
只说了按比例分流
</td>
<td>
元数据标签→三种路由策略→动态切换→回滚
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Nacos 元数据的用法
</td>
<td>
有具体的配置示例和路由策略
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没考虑用户维度一致性
</td>
<td>
用户 ID 哈希保证体验一致
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道灰度概念
</td>
<td>
有完整的灰度发布方案，考虑了回滚
</td>
</tr>
</table>

---

### 2.6 Spring Bean 作用域与依赖注入

#### 1、基础题：Spring Bean 的作用域有哪些？默认是什么？

**难度级别**：⭐（singleton、prototype、request、session、application）

**Answer**

- **singleton**（默认）：整个容器一个实例

- **prototype**：每次请求新实例

- **request**：每个 HTTP 请求一个实例（Web 环境）

- **session**：每个 Session 一个实例（Web 环境）

- **application**：每个 ServletContext 一个实例

---

[补充下]

#### 2、进阶题：Spring 中@Lazy 注解的作用是什么？如何解决循环依赖？

**难度级别**：⭐⭐⭐⭐（三级缓存、提前暴露、构造器注入失效、@Lazy 原理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 一级缓存：成品 Bean
- 二级缓存：早期暴露的 Bean（未填充属性）
- 三级缓存：ObjectFactory，用于生成 AOP 代理的早期引用

**2️⃣ Impressive Answer**

1. **@Lazy 的本质**：注入一个代理对象，真实 Bean 第一次使用时才创建。可打破循环依赖，也可优化启动速度（大 Bean 懒加载）。

1. **Spring 循环依赖解决方案**：setter/字段注入的循环依赖靠**三级缓存**解决：

  - 一级缓存：成品 Bean

  - 二级缓存：早期暴露的 Bean（未填充属性）

  - 三级缓存：ObjectFactory，用于生成 AOP 代理的早期引用

1. **构造器注入失效原因**：构造器执行时 Bean 还没暴露，无法注入循环依赖。解决：字段/ setter 注入，或其中一个加 `@Lazy`。

1. **最佳实践**：推荐构造器注入（不可变、易测试），循环依赖时局部用@Lazy 打破环，而不是全局改用字段注入。

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
说了@Lazy 和三级缓存但较浅
</td>
<td>
@Lazy 原理→三级缓存→构造器失效→最佳实践
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道三级缓存的具体作用
</td>
<td>
清楚三级缓存各自存放什么
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没说如何优雅解决
</td>
<td>
推荐构造器注入 + 局部@Lazy 的组合
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道现象
</td>
<td>
理解 Spring 设计哲学，有架构权衡能力
</td>
</tr>
</table>

---

#### 3、进阶题：@Autowired、@Resource、@Inject 三种注入方式的区别？Spring 推荐哪种？

**难度级别**：⭐⭐⭐（byType vs byName、JSR-250 vs JSR-330 vs Spring 原生、构造器注入推荐理由）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 三者对比
- Spring 官方推荐构造器注入，理由
- 不可变性：字段可以声明为 final，保证依赖不会被意外修改
- 完整性：对象创建时就注入所有依赖，不会出现"半初始化"状态
- 可测试性：单元测试时直接 new 传参，不依赖 Spring 容器
- 循环依赖暴露：构造器注入会在启动时暴露循环依赖，而不是运行时才发现

**2️⃣ Impressive Answer**

1. **三者对比**：

<table>
<tr>
<td>
维度
</td>
<td>
@Autowired
</td>
<td>
@Resource
</td>
<td>
@Inject
</td>
</tr>
<tr>
<td>
来源
</td>
<td>
Spring 原生
</td>
<td>
JSR-250（Java 标准）
</td>
<td>
JSR-330（Java 标准）
</td>
</tr>
<tr>
<td>
匹配策略
</td>
<td>
先 byType，再 byName
</td>
<td>
先 byName，再 byType
</td>
<td>
先 byType，再 byName
</td>
</tr>
<tr>
<td>
required 属性
</td>
<td>
支持（默认 true）
</td>
<td>
不支持
</td>
<td>
不支持
</td>
</tr>
<tr>
<td>
配合限定符
</td>
<td>
@Qualifier
</td>
<td>
name 属性
</td>
<td>
@Named
</td>
</tr>
</table>

1. **Spring 官方推荐构造器注入**，理由：

  - **不可变性**：字段可以声明为 final，保证依赖不会被意外修改

  - **完整性**：对象创建时就注入所有依赖，不会出现"半初始化"状态

  - **可测试性**：单元测试时直接 new 传参，不依赖 Spring 容器

  - **循环依赖暴露**：构造器注入会在启动时暴露循环依赖，而不是运行时才发现

1. **实践建议**：必选依赖用构造器注入，可选依赖用 setter 注入 + `@Autowired(required=false)`；避免字段注入（虽然代码最少，但可测试性最差）。

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
只说了基本区别
</td>
<td>
对比表格→推荐理由→实践建议
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道匹配策略的差异
</td>
<td>
清楚 byType/byName 的优先级区别
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
只说了&quot;推荐构造器注入&quot;
</td>
<td>
给出 4 个具体理由和必选/可选的区分策略
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道有区别
</td>
<td>
理解设计哲学，有最佳实践意识
</td>
</tr>
</table>

---

#### 4、场景题：Agent 系统中有多个 LLM 客户端实现（OpenAI、Claude、本地模型），如何用 Spring 优雅管理多实现的动态切换？

**难度级别**：⭐⭐⭐（@Qualifier、策略模式 + Map 注入、@ConditionalOnProperty、SPI 机制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 策略模式 + Map 自动注入（最推荐）
- 策略模式 + Map 自动注入
- 动态切换
- 扩展性设计
- 零修改扩展
- 配合 @ConditionalOnProperty

**2️⃣ Impressive Answer**

1. **策略模式 + Map 自动注入**（最推荐）：

```java
public interface LlmClient {
    String getModelName();
    ChatResponse chat(ChatRequest request);
}

@Service
public class LlmRouter {
    private final Map<String, LlmClient> clientMap;

    // Spring 自动将所有 LlmClient 实现注入到 Map 中
    // key = Bean 名称，value = Bean 实例
    public LlmRouter(Map<String, LlmClient> clientMap) {
        this.clientMap = clientMap;
    }

    public ChatResponse route(String modelName, ChatRequest request) {
        LlmClient client = clientMap.get(modelName);
        if (client == null) {
            throw new UnsupportedModelException("不支持的模型: " + modelName);
        }
        return client.chat(request);
    }
}
```

1. **动态切换**：路由策略存 Nacos 配置中心，通过 `@RefreshScope` 实现运行时切换默认模型，无需重启。

1. **扩展性设计**：新增模型只需实现 `LlmClient` 接口并注册为 Spring Bean，路由器自动感知，**零修改扩展**（开闭原则）。

1. **配合 @ConditionalOnProperty**：按环境启停，如测试环境不加载 GPT-4 客户端（节省成本），生产环境全量加载。

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
列举了几种方式但没有组合
</td>
<td>
Map 注入→动态切换→扩展性→环境隔离，完整方案
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Map 自动注入的特性
</td>
<td>
利用 Spring 的 Map&lt;String, Interface&gt; 自动收集所有实现
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没考虑运行时切换
</td>
<td>
配合 Nacos + @RefreshScope 实现热切换
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道策略模式
</td>
<td>
能用 Spring 特性优雅实现，有架构设计能力
</td>
</tr>
</table>

---

### 2.7 响应式编程 Spring WebFlux

#### 1、基础题：Spring WebFlux 和 Spring MVC 有什么区别？

**难度级别**：⭐⭐（阻塞 vs 非阻塞、Reactor、背压、适用场景）

**Answer**

<table>
<tr>
<td>
维度
</td>
<td>
Spring MVC
</td>
<td>
Spring WebFlux
</td>
</tr>
<tr>
<td>
编程模型
</td>
<td>
阻塞式（Servlet）
</td>
<td>
非阻塞响应式（Reactor）
</td>
</tr>
<tr>
<td>
容器
</td>
<td>
Tomcat/Jetty
</td>
<td>
Netty/Undertow
</td>
</tr>
<tr>
<td>
数据流
</td>
<td>
Request → Response
</td>
<td>
Flux/Mono 响应流
</td>
</tr>
<tr>
<td>
适用场景
</td>
<td>
传统 CRUD、IO 密集型
</td>
<td>
高并发、流式处理、SSE
</td>
</tr>
</table>

---

#### 2、进阶题：WebFlux 中的 Mono 和 Flux 是什么？如何处理异常？

**难度级别**：⭐⭐⭐（Reactor、onErrorResume、onErrorReturn、全局异常处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 异常处理策略
- 局部处理：onErrorReturn(默认值)、onErrorResume(恢复流)、onErrorMap(转换异常)
- 全局处理：实现 WebExceptionHandler 或用@ControllerAdvice + @ExceptionHandler（WebFlux 版本）
- finally 语义：doFinally(SignalType→回调)，无论成功/失败都执行

**2️⃣ Impressive Answer**

1. **Mono/Flux 本质**：Reactor 的响应式类型，Mono<T> 表示 0/1 个元素（如 Optional），Flux<T> 表示 0~N 个元素（如 List）。惰性执行，订阅后才触发。

1. **异常处理策略**：

  - **局部处理**：`onErrorReturn(默认值)`、`onErrorResume(恢复流)`、`onErrorMap(转换异常)`

  - **全局处理**：实现 `WebExceptionHandler` 或用`@ControllerAdvice + @ExceptionHandler`（WebFlux 版本）

  - **finally 语义**：`doFinally(SignalType→回调)`，无论成功/失败都执行

1. **背压（Backpressure）**：下游控制上游生产速率，避免内存溢出。Reactor 默认策略是 `onNext` 拉动式，Flux 会自动处理。

1. **Agent 场景**：流式输出（SSE）用 `Flux<ServerSentEvent<String>>`；多工具并行调用用 `Flux.mergeSequential()` 保持顺序，`Flux.combineLatest()` 合并结果。

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
说了 Mono/Flux 和几种处理方式
</td>
<td>
类型定义→异常处理→背压→Agent 场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道背压的概念
</td>
<td>
能解释背压的作用和 Reactor 的实现
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有场景化应用
</td>
<td>
给出 Agent 流式输出和多工具并发的方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 WebFlux
</td>
<td>
理解响应式编程范式，能解决复杂场景
</td>
</tr>
</table>

---

#### 3、容易一起考的题

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
WebFlux 如何集成 MyBatis（非响应式 ORM）？
</td>
<td>
阻塞 ORM 在响应式场景的线程池隔离方案，考察混合架构能力
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@Transactional 在 WebFlux 中如何生效？
</td>
<td>
响应式事务管理器（TransactionalOperator）与传统事务的区别
</td>
<td>
答：MySQL 题要从数据结构、事务隔离、锁/MVCC、执行计划和慢 SQL 优化展开；最后落到 explain、索引设计和业务一致性。
</td>
</tr>
<tr>
<td>
Spring Boot 3 中 WebFlux 和 Virtual Thread 如何选型？
</td>
<td>
考察对 Java 21 虚拟线程与响应式编程的对比理解
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

#### 4、进阶题：WebFlux 的线程模型是什么？为什么不能在响应式链中调用阻塞 API？

**难度级别**：⭐⭐⭐（EventLoop 模型、Scheduler 调度、publishOn/subscribeOn、阻塞检测）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 正确处理阻塞调用
- EventLoop 线程模型
- 非阻塞 I/O + 事件驱动
- 阻塞的致命影响
- 整个服务完全停止响应
- publishOn vs subscribeOn

**2️⃣ Impressive Answer**

1. **EventLoop 线程模型**：Netty 默认创建 `CPU 核心数` 个 EventLoop 线程，每个线程负责多个 Channel 的 I/O 事件。所有请求共享这几个线程，靠**非阻塞 I/O + 事件驱动**实现高并发。

1. **阻塞的致命影响**：假设 4 核 CPU = 4 个 EventLoop 线程，一个阻塞调用占住 1 个线程 500ms，就意味着 25% 的处理能力被浪费。如果 4 个线程都被阻塞，**整个服务完全停止响应**。

1. **正确处理阻塞调用**：

```java
// 错误：直接在响应式链中调用阻塞 API
Mono.just(request)
    .map(req -> jdbcTemplate.query(...));  // 阻塞 EventLoop！

// 正确：用 subscribeOn 切换到阻塞线程池
Mono.fromCallable(() -> jdbcTemplate.query(...))
    .subscribeOn(Schedulers.boundedElastic());  // 切到弹性线程池
```

1. **publishOn vs subscribeOn**：`subscribeOn` 影响整个链的订阅线程（从源头切换）；`publishOn` 影响下游操作的执行线程（从当前位置切换）。阻塞调用用 `subscribeOn`，后续处理切回用 `publishOn`。

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
知道不能阻塞但说不清后果
</td>
<td>
线程模型→阻塞影响量化→正确写法→调度器区别
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 publishOn 和 subscribeOn 的区别
</td>
<td>
清楚两者的作用范围差异
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
只说了&quot;放到线程池&quot;
</td>
<td>
有具体的代码对比（错误 vs 正确）
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道原则
</td>
<td>
能量化阻塞影响，知道如何正确处理
</td>
</tr>
</table>

---

#### 5、场景题：Agent 需要同时调用 3 个外部 API（搜索、天气、数据库），如何用 WebFlux 实现并发调用并合并结果？

**难度级别**：⭐⭐⭐（Mono.zip、Flux.merge、超时控制、fallback 降级）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Mono.zip 并发合并
- 关键设计点
- 独立超时：每个调用设置不同的超时时间（搜索 3s、天气 2s、DB 5s），而非统一超时
- 独立降级：onErrorResume 返回空结果而非抛异常，一个失败不影响其他
- 阻塞隔离：DB 查询是阻塞的，用 subscribeOn(Schedulers.boundedElastic()) 隔离到弹性线程池

**2️⃣ Impressive Answer**

1. **Mono.zip 并发合并**：

```java
public Mono<AgentContext> gatherContext(String query) {
    Mono<SearchResult> searchMono = searchClient.search(query)
        .timeout(Duration.ofSeconds(3))
        .onErrorResume(e -> Mono.just(SearchResult.empty()));

    Mono<WeatherInfo> weatherMono = weatherClient.getWeather(query)
        .timeout(Duration.ofSeconds(2))
        .onErrorResume(e -> Mono.just(WeatherInfo.unavailable()));

    Mono<DbResult> dbMono = Mono.fromCallable(() -> dbService.query(query))
        .subscribeOn(Schedulers.boundedElastic())
        .timeout(Duration.ofSeconds(5))
        .onErrorResume(e -> Mono.just(DbResult.empty()));

    return Mono.zip(searchMono, weatherMono, dbMono)
        .map(tuple -> AgentContext.builder()
            .search(tuple.getT1())
            .weather(tuple.getT2())
            .dbResult(tuple.getT3())
            .build());
}
```

1. **关键设计点**：

  - **独立超时**：每个调用设置不同的超时时间（搜索 3s、天气 2s、DB 5s），而非统一超时

  - **独立降级**：`onErrorResume` 返回空结果而非抛异常，一个失败不影响其他

  - **阻塞隔离**：DB 查询是阻塞的，用 `subscribeOn(Schedulers.boundedElastic())` 隔离到弹性线程池

1. **进阶优化**：如果某个 API 非必需（如天气），可以用 `Mono.zipDelayError()` 延迟错误处理，优先返回已完成的结果；配合 `Mono.firstWithSignal()` 实现"谁先返回用谁"的竞速模式。

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
只说了 Mono.zip
</td>
<td>
完整代码→独立超时/降级→阻塞隔离→进阶优化
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道阻塞调用需要隔离
</td>
<td>
DB 查询用 subscribeOn 切线程池
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
统一超时
</td>
<td>
每个调用独立超时和降级策略
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道 API
</td>
<td>
有生产级的并发编排经验
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| Spring Cloud Gateway 的工作原理是什么？ | Predicate（断言）：匹配请求（路径、方法、Header 等）；Filter（过滤器）：请求/响应预处理（鉴权、限流、日志）；Route（路由）：Predicate + Filter → 转发目标。 |
| Spring Cloud Feign 的底层原理是什么？如何实现负载均衡和重试？ | 动态代理生成：Feign 启动时扫描@FeignClient 接口，用 JDK 动态代理生成实现类，方法调用被拦截成 HTTP 请求（RequestTemplate）；负载均衡：早期用 Ribbon（已废弃），现在用 Spring Cloud LoadBalancer。核心是 LoadBalancerClient.choose(serviceId) 从注册中心选实例，支持轮询、权重、Zone 感知等策略；重试机制：Spring Cloud OpenFeign 默认不重试（幂等 GET 除外），可配置 Retryer 定义重试条件（间隔、次数、哪些异常）。但POST/PUT 等非幂等操作要谨慎重试，需业务侧保证幂等性。 |
| Agent 调用多个微服务，如何用 Gateway 统一做鉴权和限流？ | 全局鉴权 Filter：实现 GlobalFilter，在 filter() 方法中解析 JWT Token，校验权限；失败直接返回 401，不调用 chain.filter()；限流策略：基于 Redis + Lua 脚本实现令牌桶/滑动窗口，按用户 ID 或 API Key 限流；超阈值返回 429；路由隔离：Agent 相关服务单独分组（如 agent-service），Gateway 配置 Predicate 路由到对应服务集群。 |
| Nacos 作为注册中心和配置中心的核心原理？与 Eureka 的区别？ | Eureka：纯 AP 模式，节点间通过 Peer-to-Peer 复制注册表，网络分区时仍可用但数据可能不一致；客户端定时拉取（默认 30s），感知延迟较高；Nacos：临时实例用 AP 模式（Distro 协议），持久实例用 CP 模式（Raft 协议）。支持服务端主动推送（UDP + 长轮询兜底），服务上下线感知延迟低至秒级；配置中心原理：客户端发起长轮询请求（默认 30s 超时），服务端挂起请求；配置变更时立即返回变更的 dataId，客户端再拉取最新配置。比定时轮询更实时，比 WebSocket 更轻量；健康检查差异：Eureka 靠客户端心跳（默认 30s）；Nacos 临时实例也靠心跳，但持久实例由服务端主动探测（TCP/HTTP），更适合非 Java 服务。 |
| Agent 平台有多个版本的模型服务（GPT-4、Claude、本地模型），如何用微服务架构实现灰度路由和流量切换？ | Header 标签路由：请求头带 X-Model-Version: gpt4 时，路由到对应版本的服务实例；权重路由：90% 流量走稳定版，10% 走灰度版，通过 Nacos 配置中心动态调整权重；用户维度灰度：按用户 ID 哈希取模，保证同一用户始终命中同一版本（避免体验不一致）。 |
| Spring Bean 的作用域有哪些？默认是什么？ | singleton：（默认）：整个容器一个实例；prototype：每次请求新实例；request：每个 HTTP 请求一个实例（Web 环境）；session：每个 Session 一个实例（Web 环境）；application：每个 ServletContext 一个实例。 |
| Spring 中@Lazy 注解的作用是什么？如何解决循环依赖？ | 一级缓存：成品 Bean；二级缓存：早期暴露的 Bean（未填充属性）；三级缓存：ObjectFactory，用于生成 AOP 代理的早期引用。 |
| @Autowired、@Resource、@Inject 三种注入方式的区别？Spring 推荐哪种？ | 不可变性：字段可以声明为 final，保证依赖不会被意外修改；完整性：对象创建时就注入所有依赖，不会出现"半初始化"状态；可测试性：单元测试时直接 new 传参，不依赖 Spring 容器；循环依赖暴露：构造器注入会在启动时暴露循环依赖，而不是运行时才发现。 |
| Agent 系统中有多个 LLM 客户端实现（OpenAI、Claude、本地模型），如何用 Spring 优雅管理多实现的动态切换？ | 多 LLM Provider 可以用策略模式管理：所有 Provider 实现同一接口，Spring 注入为 Map，通过模型名、租户配置或路由策略选择具体实现；再配合健康检查、限流、降级和配置中心实现动态切换。 |
| Spring WebFlux 和 Spring MVC 有什么区别？ | WebFlux 基于 Reactor、Mono/Flux 和事件循环，异步非阻塞，适合高并发 I/O、SSE、WebSocket、API 网关和流式处理；Spring MVC 基于 Servlet 线程池和同步阻塞模型，生态成熟、开发简单，适合传统 CRUD、阻塞调用多和业务逻辑复杂的系统。 |
| WebFlux 中的 Mono 和 Flux 是什么？如何处理异常？ | 局部处理：onErrorReturn(默认值)、onErrorResume(恢复流)、onErrorMap(转换异常)；全局处理：实现 WebExceptionHandler 或用@ControllerAdvice + @ExceptionHandler（WebFlux 版本）；finally 语义：doFinally(SignalType→回调)，无论成功/失败都执行。 |
| WebFlux 的线程模型是什么？为什么不能在响应式链中调用阻塞 API？ | EventLoop 线程模型：Netty 默认创建 CPU 核心数 个 EventLoop 线程，每个线程负责多个 Channel 的 I/O 事件。所有请求共享这几个线程，靠非阻塞 I/O + 事件驱动实现高并发；阻塞的致命影响：假设 4 核 CPU = 4 个 EventLoop 线程，一个阻塞调用占住 1 个线程 500ms，就意味着 25% 的处理能力被浪费。如果 4 个线程都被阻塞，整个服务完全停止响应；// 错误：直接在响应式链中调用阻塞 API。 |
| Agent 需要同时调用 3 个外部 API（搜索、天气、数据库），如何用 WebFlux 实现并发调用并合并结果？ | 独立超时：每个调用设置不同的超时时间（搜索 3s、天气 2s、DB 5s），而非统一超时；独立降级：onErrorResume 返回空结果而非抛异常，一个失败不影响其他；阻塞隔离：DB 查询是阻塞的，用 subscribeOn(Schedulers.boundedElastic()) 隔离到弹性线程池。 |
