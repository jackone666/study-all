#### 1、基础题：Spring Boot 自动装配的原理是什么？@SpringBootApplication 做了什么？

**难度级别**：⭐⭐（@EnableAutoConfiguration、spring.factories/spring/imports、条件注解）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 自动装配完整链路
- @EnableAutoConfiguration 通过 @Import(AutoConfigurationImportSelector.class) 触发。
- AutoConfigurationImportSelector 实现了 DeferredImportSelector，在所有 @Configuration 类处理完后才执行（保...
- 读取 META-INF/spring.factories（Boot 2.x）或 META-INF/spring/org.springframework.boot.autocon...
- 条件注解：每个自动配置类通过决定是否生效。

**2️⃣ Impressive Answer**
1. **@SpringBootApplication 三合一**：`@Configuration`（声明配置类）+ `@EnableAutoConfiguration`（开启自动装配）+ `@ComponentScan`（扫描当前包及子包）。
1. **自动装配完整链路**：
  - `@EnableAutoConfiguration` 通过 `@Import(AutoConfigurationImportSelector.class)` 触发。
  - `AutoConfigurationImportSelector` 实现了 `DeferredImportSelector`，在所有 `@Configuration` 类处理完后才执行（保证用户配置优先）。
  - 读取 `META-INF/spring.factories`（Boot 2.x）或 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Boot 3.x）中注册的自动配置类。
  - 每个自动配置类通过**条件注解**决定是否生效。
1. **条件注解是核心**：`@ConditionalOnClass`（类路径存在才生效）、`@ConditionalOnMissingBean`（用户没自定义才生效）、`@ConditionalOnProperty`（配置开关控制）。这保证了"约定优于配置"——有默认值，但用户可以覆盖。
1. **版本差异**：Spring Boot 3.x 废弃了 `spring.factories` 的自动装配入口，迁移到 `.imports` 文件，加载更高效（不再加载所有 key，只加载 AutoConfiguration）。

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
只说了&quot;三个注解组合&quot;
</td>
<td>
完整链路：注解→ImportSelector→文件→条件注解
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 DeferredImportSelector 的作用
</td>
<td>
清楚延迟导入保证用户配置优先
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道 Boot 3.x 的变化
</td>
<td>
知道两个版本的注册文件差异
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过概念但不深入
</td>
<td>
理解自动装配的设计意图和演进
</td>
</tr>
</table>

---

#### 2、进阶题：如何自定义一个 Spring Boot Starter？

**难度级别**：⭐⭐⭐（AutoConfiguration 类、@ConditionalOnMissingBean、META-INF 配置、属性绑定）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三个核心步骤
- 条件注解是关键
- 常见陷阱

**2️⃣ Impressive Answer**
1. **三个核心步骤**：① 写 `XxxAutoConfiguration` 类，用 `@Configuration` + `@ConditionalOnMissingBean` 定义默认 Bean；② 用 `@ConfigurationProperties` 绑定配置项（prefix = "xxx"），支持 application.yml 自定义；③ 在 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Boot 3.x）或 `spring.factories`（Boot 2.x）中注册。
1. **条件注解是关键**：`@ConditionalOnClass` 保证依赖存在时才生效；`@ConditionalOnMissingBean` 让用户自定义 Bean 时自动退位；`@ConditionalOnProperty` 可以让用户通过配置开关控制是否启用。
1. **常见陷阱**：忘记加 `@EnableConfigurationProperties` 导致配置类不生效；Spring Boot 3.x 已废弃 spring.factories 的自动装配入口，必须迁移到新路径。

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
步骤混乱，不知道先做什么
</td>
<td>
三步清晰：AutoConfig→属性绑定→注册
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Boot 3.x 路径变化
</td>
<td>
知道两个版本的注册文件差异
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道条件注解的具体用法
</td>
<td>
三个条件注解分场景说清楚
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
能写但不知道原理和兼容性
</td>
<td>
有版本意识，知道条件注解的设计意图
</td>
</tr>
</table>

---

#### 3、进阶题：Spring Boot 的配置加载优先级？多环境配置如何管理？

**难度级别**：⭐⭐⭐（PropertySource 优先级、Profile 机制、配置中心集成）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 配置加载优先级（从高到低）
- 命令行参数（--server.port=8081）
- Java 系统属性（-Dserver.port=8081）
- 系统环境变量（SERVER_PORT=8081）
- application-{profile}.yml（激活的 Profile 配置）
- application.yml（默认配置）

**2️⃣ Impressive Answer**
1. **配置加载优先级（从高到低）**：
  - 命令行参数（`--server.port=8081`）
  - Java 系统属性（`-Dserver.port=8081`）
  - 系统环境变量（`SERVER_PORT=8081`）
  - `application-{profile}.yml`（激活的 Profile 配置）
  - `application.yml`（默认配置）
  - `@PropertySource` 注解引入的配置
  - 代码中的默认值

**核心原则**：外部化配置优先于内部配置，Profile 配置优先于默认配置。
1. **Profile 机制**：`spring.profiles.active=dev` 激活 `application-dev.yml`；支持多 Profile 叠加（`dev,local`）；Spring Boot 2.4+ 支持 `spring.config.activate.on-profile` 在同一文件中按 `---` 分隔多环境配置。
1. **配置中心集成**：Nacos/Apollo 作为外部配置源，`bootstrap.yml` 优先于 `application.yml` 加载（用于配置中心连接信息）；支持动态刷新（`@RefreshScope`），无需重启。
1. **Agent 场景**：不同环境的 LLM API Key、模型参数（temperature、max_tokens）、工具启停配置通过 Profile + 配置中心管理，敏感信息（API Key）通过加密配置或 Vault 管理。

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
只说了&quot;命令行最高&quot;
</td>
<td>
完整优先级链，7 层从高到低
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 bootstrap.yml 的作用
</td>
<td>
清楚配置中心的加载时机和动态刷新
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到敏感信息管理
</td>
<td>
知道 API Key 加密和 Vault 方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道基本用法
</td>
<td>
有多环境配置的完整实践经验
</td>
</tr>
</table>

---

#### 4、容易一起考的题

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
@EnableAutoConfiguration 是如何加载 AutoConfiguration 的？
</td>
<td>
Starter 的注册原理，考察 Spring Boot 自动装配的 SPI 机制
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@Conditional 家族注解有哪些？如何自定义 Condition？
</td>
<td>
Starter 核心依赖的条件化装配能力，考察扩展能力
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：Starter 核心依赖的条件化装配能力，考察扩展能力，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring Boot 2.x 升级到 3.x 需要注意哪些自动装配的变化？
</td>
<td>
考察对版本迁移的实际工程经验
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.1 Spring Boot 内嵌容器与启动流程

#### 1、基础题：Spring Boot 的启动流程是什么？SpringApplication.run() 内部做了哪些事？

**难度级别**：⭐⭐（SpringApplication 初始化、Environment 准备、ApplicationContext 创建、自动装配、内嵌容器启动）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- SpringApplication 构造阶段
- run() 执行流程
- 推断应用类型（Servlet / Reactive / None）
- 通过 SPI 加载 ApplicationContextInitializer 和 ApplicationListener
- 推断主配置类（包含 main 方法的类）

**2️⃣ Impressive Answer**
1. **SpringApplication 构造阶段**：
  - 推断应用类型（Servlet / Reactive / None）
  - 通过 SPI 加载 `ApplicationContextInitializer` 和 `ApplicationListener`
  - 推断主配置类（包含 `main` 方法的类）
1. **run() 执行流程**：

```
创建 SpringApplicationRunListeners（发布启动事件）
→ 准备 Environment（加载配置文件、系统变量）
→ 打印 Banner
→ 创建 ApplicationContext（根据应用类型选择实现类）
→ prepareContext（注册 BeanDefinition、执行 Initializer）
→ refreshContext（核心：Bean 实例化、自动装配、内嵌容器启动）
→ afterRefresh（执行 ApplicationRunner / CommandLineRunner）
→ 发布 ApplicationReadyEvent
```
1. **关键扩展点**：`ApplicationContextInitializer`（容器创建后、刷新前执行）、`ApplicationRunner`（启动完成后执行）、`SpringApplicationRunListener`（各阶段事件监听）。
1. **实践注意**：`refreshContext` 是最耗时的阶段，包含了 Bean 扫描、实例化、AOP 代理创建、内嵌容器启动等所有核心逻辑。启动慢优化应重点关注这个阶段。

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
只说了&quot;创建容器、启动 Tomcat&quot;
</td>
<td>
完整流程 8 个步骤，每步都有对应机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道应用类型推断
</td>
<td>
清楚 Servlet/Reactive/None 三种类型
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到扩展点
</td>
<td>
知道 Initializer、Runner、Listener 三大扩展点
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道入口但不知道内部
</td>
<td>
理解启动流程的完整链路和优化方向
</td>
</tr>
</table>

---

#### 2、进阶题：Spring Boot 内嵌 Tomcat 的启动原理？如何切换为 Undertow/Jetty？

**难度级别**：⭐⭐⭐（ServletWebServerFactory、自动装配条件、性能对比）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 切换方式
- 性能对比
- 内嵌 Tomcat 启动原理
- Agent 场景

**2️⃣ Impressive Answer**
1. **内嵌 Tomcat 启动原理**：`ServletWebServerFactoryAutoConfiguration` 通过 `@ConditionalOnClass(Tomcat.class)` 判断类路径上有 Tomcat，自动注册 `TomcatServletWebServerFactory`。在 `refreshContext` 阶段，`ServletWebServerApplicationContext` 调用 `createWebServer()` 创建并启动内嵌容器。
1. **切换方式**：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-undertow</artifactId>
</dependency>
```
1. **性能对比**：

<table>
<tr>
<td>
维度
</td>
<td>
Tomcat
</td>
<td>
Undertow
</td>
<td>
Jetty
</td>
</tr>
<tr>
<td>
IO 模型
</td>
<td>
NIO
</td>
<td>
XNIO（IO/Worker 线程分离）
</td>
<td>
NIO
</td>
</tr>
<tr>
<td>
长连接
</td>
<td>
一般
</td>
<td>
<strong>优秀</strong>（适合 SSE）
</td>
<td>
良好
</td>
</tr>
<tr>
<td>
生态
</td>
<td>
最成熟
</td>
<td>
较新
</td>
<td>
成熟
</td>
</tr>
<tr>
<td>
内存占用
</td>
<td>
较高
</td>
<td>
<strong>较低</strong>
</td>
<td>
中等
</td>
</tr>
</table>
1. **Agent 场景**：SSE 流式输出是长连接，Undertow 的 XNIO 模型更适合——IO 线程只负责接收连接，Worker 线程处理业务，不会因为长连接占满线程池。

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
只说了排除依赖
</td>
<td>
原理→切换方式→性能对比→场景选型
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道自动装配的条件判断
</td>
<td>
清楚 @ConditionalOnClass 的工作机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
只说&quot;Undertow 性能好&quot;
</td>
<td>
有 IO 模型对比和 Agent 场景选型
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会切换但不知道原理
</td>
<td>
理解自动装配和容器选型的工程权衡
</td>
</tr>
</table>

---

#### 3、场景题：Agent 服务需要支持高并发 SSE 长连接，如何调优内嵌容器参数？

**难度级别**：⭐⭐⭐（线程池配置、连接超时、NIO 配置、背压处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- Tomcat 核心参数调优
- 切换 Undertow 的优势配置
- server.tomcat.threads.max=400（默认 200，SSE 场景需增大）
- server.tomcat.threads.min-spare=50（最小空闲线程）
- server.tomcat.max-connections=10000（默认 8192，长连接场景需增大）
- server.tomcat.connection-timeout=60000（连接超时）

**2️⃣ Impressive Answer**
1. **Tomcat 核心参数调优**：
  - `server.tomcat.threads.max=400`（默认 200，SSE 场景需增大）
  - `server.tomcat.threads.min-spare=50`（最小空闲线程）
  - `server.tomcat.max-connections=10000`（默认 8192，长连接场景需增大）
  - `server.tomcat.connection-timeout=60000`（连接超时）
  - `server.tomcat.accept-count=200`（等待队列长度）
1. **SSE 场景的特殊性**：每个 SSE 连接占用一个线程直到完成，200 个线程只能同时处理 200 个 SSE 请求。解决方案：① 增大线程池；② 切换 Undertow（IO/Worker 分离）；③ 使用 WebFlux 响应式方案。
1. **切换 Undertow 的优势配置**：
  - `server.undertow.io-threads=16`（IO 线程，通常等于 CPU 核数）
  - `server.undertow.worker-threads=256`（Worker 线程）
  - IO 线程只负责接收连接和读写数据，Worker 线程处理业务逻辑，长连接不会阻塞新连接的接入。
1. **监控与告警**：配合 Micrometer + Prometheus 暴露 `tomcat.threads.busy`、`tomcat.connections.current` 等指标；设置告警阈值（如线程使用率 > 80%），提前扩容。

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
只说了&quot;调大线程池&quot;
</td>
<td>
具体参数→SSE 特殊性→Undertow 方案→监控
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 SSE 占线程的问题
</td>
<td>
清楚长连接对线程池的影响和解决方案
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有具体参数值
</td>
<td>
有完整的参数配置和监控方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道要调优但不具体
</td>
<td>
有生产环境调优经验，考虑周全
</td>
</tr>
</table>

---

#### 4、容易一起考的题

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
Spring Boot Actuator 的健康检查和指标暴露？
</td>
<td>
生产环境监控，和容器调优配合使用
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
Spring Boot 的优雅停机（Graceful Shutdown）如何实现？
</td>
<td>
长连接场景下的停机策略，避免 SSE 连接被强制断开
</td>
<td>
答：配置方式；停机流程；超时控制；停止接受新请求（Tomcat/Undertow 拒绝新连接）
</td>
</tr>
<tr>
<td>
Spring WebFlux vs Spring MVC 的选型？
</td>
<td>
响应式编程在高并发场景下的替代方案
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.2 优雅停机

#### 1、基础题：Spring Boot 的优雅停机（Graceful Shutdown）如何配置？

**难度级别**：⭐⭐（配置方式、停机流程、超时控制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 配置方式
- 停机流程
- 超时控制
- 停止接受新请求（Tomcat/Undertow 拒绝新连接）
- 等待进行中的请求完成（最多等待 timeout-per-shutdown-phase）
- 销毁 Bean（调用 @PreDestroy、DisposableBean.destroy()）

**2️⃣ Impressive Answer**
1. **配置方式**：

```yaml
server:
  shutdown: graceful  # 启用优雅停机

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s  # 每个阶段超时时间
```
1. **停机流程**：
  - 停止接受新请求（Tomcat/Undertow 拒绝新连接）
  - 等待进行中的请求完成（最多等待 timeout-per-shutdown-phase）
  - 销毁 Bean（调用 @PreDestroy、DisposableBean.destroy()）
  - 关闭容器
1. **超时控制**：
  - `timeout-per-shutdown-phase`：每个阶段的最大等待时间（默认 30s）。
  - 超时后强制停机，未完成的请求会被中断。
1. **版本要求**：Spring Boot 2.3+ 支持优雅停机，Undertow 支持更好（Tomcat 9.0.33+）。
1. **Agent 场景**：SSE 长连接、LLM 调用需要等待完成，避免强制中断导致数据不一致。

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
只说了配置
</td>
<td>
配置+停机流程+超时控制+版本要求
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道停机流程
</td>
<td>
清楚四个阶段的停机顺序
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到版本要求
</td>
<td>
知道不同容器的支持差异
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会配置
</td>
<td>
理解优雅停机的完整机制
</td>
</tr>
</table>

---

#### 2、进阶题：优雅停机的底层原理是什么？SmartLifecycle、ContextClosedEvent、ShutdownHook 各自的角色？

**难度级别**：⭐⭐⭐（停机原理、生命周期扩展、JVM Hook）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 底层原理
- SmartLifecycle
- ContextClosedEvent
- ShutdownHook
- JVM 收到 SIGTERM 信号（kill 命令）
- 触发 Shutdown Hook（Spring 注册的）

**2️⃣ Impressive Answer**
1. **底层原理**：
  - JVM 收到 SIGTERM 信号（kill 命令）
  - 触发 Shutdown Hook（Spring 注册的）
  - 调用 `ConfigurableApplicationContext.close()`
  - 发布 `ContextClosedEvent`
  - 停止 Web 容器（拒绝新请求）
  - 销毁 Bean（按 SmartLifecycle 顺序）
  - 关闭容器
1. **SmartLifecycle**：
  - **作用**：控制 Bean 的启动和停机顺序，支持异步停机。
  - **方法**：`start()`（启动）、`stop()`（停机）、`isAutoStartup()`（是否自动启动）、`getPhase()`（阶段值，越小越先停）。
  - **示例**：

```java
@Component
public class LLMConnectionPool implements SmartLifecycle {

    private boolean isRunning = false;

    @Override
    public void start() {
        isRunning = true;
        // 初始化连接池
    }

    @Override
    public void stop() {
        isRunning = false;
        // 等待进行中的请求完成
        shutdown(Duration.ofSeconds(30));
    }

    @Override
    public int getPhase() {
        return 1; // 较小值，优先停机
    }

    @Override
    public boolean isRunning() {
        return isRunning;
    }
}
```
1. **ContextClosedEvent**：
  - **作用**：容器关闭时发布的事件，可以监听执行清理逻辑。
  - **示例**：

```java
@Component
public class ShutdownListener {

    @EventListener(ContextClosedEvent.class)
    public void onContextClosed() {
        log.info("Context is closing, performing cleanup...");
        // 清理资源
    }
}
```
1. **ShutdownHook**：
  - **作用**：JVM 级别的钩子，在 JVM 退出前执行。
  - **Spring 注册**：`SpringApplication.registerShutdownHook()`（默认启用）。
  - **注意**：只能注册一次，重复注册会覆盖。
1. **执行顺序**：ShutdownHook → ContextClosedEvent → SmartLifecycle.stop() → @PreDestroy。

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
只说了三个名字
</td>
<td>
底层原理+完整代码+执行顺序
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 SmartLifecycle 的 phase
</td>
<td>
清楚停机顺序控制机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有代码示例
</td>
<td>
有完整的生命周期管理实现
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过概念
</td>
<td>
理解优雅停机的完整机制
</td>
</tr>
</table>

---

#### 3、场景题：Agent 服务发布时有正在进行的 SSE 长连接和 LLM 调用，如何实现无损下线？

**难度级别**：⭐⭐⭐（无损下线、长连接处理、健康检查）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 无损下线完整方案
- K8s 无损下线配置
- 自定义 HealthIndicator
- SmartLifecycle 控制停机顺序
- 下线流程
- name: agent

**2️⃣ Impressive Answer**
1. **无损下线完整方案**：

```yaml
server:
  shutdown: graceful
  undertow:
    no-request-timeout: 30s  # Undertow 无请求超时

spring:
  lifecycle:
    timeout-per-shutdown-phase: 60s

management:
  endpoints:
    web:
      exposure:
        include: health,shutdown
  endpoint:
    health:
      probes:
        enabled: true  # 启用 K8s 探针
    shutdown:
      enabled: true  # 启用停机端点
```
1. **K8s 无损下线配置**：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: agent-pod
spec:
  containers:
  - name: agent
    image: agent:latest
    lifecycle:
      preStop:
        exec:
          command: ["curl", "-XPOST", "http://localhost:8080/actuator/shutdown"]
    readinessProbe:
      httpGet:
        path: /actuator/health/readiness
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 5
    livenessProbe:
      httpGet:
        path: /actuator/health/liveness
        port: 8080
      initialDelaySeconds: 60
      periodSeconds: 10
  terminationGracePeriodSeconds: 90  # 总停机超时时间
```
1. **自定义 HealthIndicator**：

```java
@Component
public class AgentHealthIndicator implements HealthIndicator {

    @Autowired
    private LLMClient llmClient;

    @Override
    public Health health() {
        Health.Builder builder = Health.up();

        // 检查 LLM 连接
        if (!llmClient.isHealthy()) {
            builder.down().withDetail("llm", "connection failed");
        }

        // 检查进行中的请求
        int activeRequests = getActiveRequestCount();
        if (activeRequests > 100) {
            builder.down().withDetail("requests", activeRequests);
        }

        return builder.build();
    }
}
```
1. **SmartLifecycle 控制停机顺序**：

```java
@Component
public class SSEConnectionManager implements SmartLifecycle {

    private final Set<SseEmitter> activeEmitters = ConcurrentHashMap.newKeySet();

    @Override
    public int getPhase() {
        return Integer.MAX_VALUE; // 最后停机
    }

    @Override
    public void stop() {
        // 等待所有 SSE 连接完成
        activeEmitters.forEach(emitter -> {
            try {
                emitter.complete();
            } catch (Exception e) {
                log.error("Failed to complete emitter", e);
            }
        });

        // 等待最多 30 秒
        awaitTermination(Duration.ofSeconds(30));
    }
}
```
1. **下线流程**：
  - K8s 发送 SIGTERM
  - ReadinessProbe 返回 false，摘流
  - PreStop 调用停机端点
  - Web 容器拒绝新请求
  - 等待进行中的请求完成（SSE、LLM 调用）
  - LLM 连接池关闭
  - Pod 终止

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
只说了配置
</td>
<td>
完整方案+K8s 配置+HealthIndicator+SmartLifecycle
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 K8s 探针机制
</td>
<td>
清楚 readinessProbe 和 terminationGracePeriodSeconds
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有下线流程
</td>
<td>
有完整的无损下线流程设计
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会配置
</td>
<td>
有生产环境无损下线经验
</td>
</tr>
</table>

---

#### 4、容易一起考的题

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
Spring Boot Actuator 的健康检查如何实现？
</td>
<td>
无损下线依赖健康检查摘流
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Docker/K8s 的生命周期管理？
</td>
<td>
容器化部署的无损下线方案
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：容器化部署的无损下线方案，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
JVM 的 ShutdownHook 是什么？
</td>
<td>
优雅停机的底层机制
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：优雅停机的底层机制，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

### 3.3 Actuator 可观测性

#### 1、基础题：Spring Boot Actuator 有哪些常用的 Endpoint？如何保护敏感 Endpoint？

**难度级别**：⭐⭐（常用 Endpoint、安全配置、暴露策略）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 常用 Endpoint
- 暴露配置
- 安全保护
- Agent 场景
- health：健康检查（/actuator/health）
- metrics：指标监控（/actuator/metrics）

**2️⃣ Impressive Answer**
1. **常用 Endpoint**：
  - **health**：健康检查（`/actuator/health`）
  - **metrics**：指标监控（`/actuator/metrics`）
  - **info**：应用信息（`/actuator/info`）
  - **env**：环境变量（`/actuator/env`）
  - **loggers**：日志级别管理（`/actuator/loggers`）
  - **threaddump**：线程 dump（`/actuator/threaddump`）
  - **heapdump**：堆 dump（`/actuator/heapdump`）
1. **暴露配置**：

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics  # 只暴露安全端点
        exclude: env,heapdump,threaddump  # 排除敏感端点
  endpoint:
    health:
      show-details: when-authorized  # 只对授权用户显示详情
```
1. **安全保护**：

```java
@Configuration
public class ActuatorSecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .requestMatcher(EndpointRequest.toAnyEndpoint())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(EndpointRequest.to("health", "info")).permitAll()
                .anyRequest().hasRole("ADMIN")
            )
            .httpBasic(withDefaults());

        return http.build();
    }
}
```
1. **Agent 场景**：
  - 暴露 `health`、`metrics` 给监控系统
  - 保护 `env`、`heapdump` 避免敏感信息泄露
  - 自定义健康检查（LLM 连接、工具调用成功率）

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
只列举了几个端点
</td>
<td>
7 个端点+暴露配置+安全保护
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 show-details 配置
</td>
<td>
清楚 when-authorized 策略
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有安全配置代码
</td>
<td>
有完整的 Spring Security 集成
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过端点名
</td>
<td>
理解 Actuator 的安全配置
</td>
</tr>
</table>

---

#### 2、进阶题：如何自定义 HealthIndicator 和 Micrometer 指标？指标如何接入 Prometheus？

**难度级别**：⭐⭐⭐（自定义指标、Micrometer、Prometheus 集成）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 自定义 HealthIndicator
- 自定义 Micrometer 指标
- Prometheus 集成
- Prometheus 配置
- Grafana Dashboard
- job_name: 'agent-service'

**2️⃣ Impressive Answer**
1. **自定义 HealthIndicator**：

```java
@Component
public class LLMHealthIndicator implements HealthIndicator {

    @Autowired
    private LLMClient llmClient;

    @Override
    public Health health() {
        try {
            // 检查 LLM 连接
            boolean healthy = llmClient.ping();

            if (healthy) {
                return Health.up()
                    .withDetail("model", llmClient.getModel())
                    .withDetail("latency", llmClient.getAvgLatency())
                    .build();
            } else {
                return Health.down()
                    .withDetail("error", "LLM connection failed")
                    .build();
            }
        } catch (Exception e) {
            return Health.down(e).build();
        }
    }
}
```
1. **自定义 Micrometer 指标**：

```java
@Component
public class ToolCallMetrics {

    private final Counter toolCallCounter;
    private final Timer toolCallTimer;
    private final Gauge activeConnections;

    public ToolCallMetrics(MeterRegistry registry) {
        this.toolCallCounter = Counter.builder("tool.call.count")
            .description("Total tool calls")
            .tag("type", "all")
            .register(registry);

        this.toolCallTimer = Timer.builder("tool.call.duration")
            .description("Tool call duration")
            .register(registry);

        this.activeConnections = Gauge.builder("llm.active.connections",
            llmClient, LLMClient::getActiveConnections)
            .register(registry);
    }

    public void recordToolCall(String toolName, long duration, boolean success) {
        toolCallCounter.increment(
            Tags.of("tool", toolName, "status", success ? "success" : "error"));

        toolCallTimer.record(duration, TimeUnit.MILLISECONDS);
    }
}
```
1. **Prometheus 集成**：

```yaml
# pom.xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>

# application.yml
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  metrics:
    export:
      prometheus:
        enabled: true
    tags:
      application: ${spring.application.name}
      environment: ${spring.profiles.active}
```
1. **Prometheus 配置**：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agent-service'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['localhost:8080']
```
1. **Grafana Dashboard**：
  - 工具调用 QPS（`rate(tool.call.count[1m])`）
  - 工具调用延迟 P95（`histogram_quantile(0.95, rate(tool.call.duration_bucket[5m]))`）
  - LLM 活跃连接数（`llm_active_connections`）

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
只说了实现接口
</td>
<td>
完整 HealthIndicator+Metrics+Prometheus+Grafana
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Micrometer 的 Counter/Gauge
</td>
<td>
清楚三种指标类型和 PromQL
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有完整配置
</td>
<td>
有生产环境监控方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会自定义指标
</td>
<td>
有完整的可观测性体系
</td>
</tr>
</table>

---

#### 3、场景题：如何用 Actuator 监控 Agent 服务的 LLM 调用成功率、Token 消耗量、工具调用延迟等核心指标？

**难度级别**：⭐⭐⭐（业务指标、标签设计、告警规则）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 指标设计
- Prometheus 告警规则
- Grafana Dashboard 面板
- 指标最佳实践
- name: agent_alerts
- alert: LLMLowSuccessRate

**2️⃣ Impressive Answer**
1. **指标设计**：

```java
@Component
public class AgentMetrics {

    // LLM 调用成功率
    private final Counter llmCallCounter;

    // Token 消耗量
    private final Counter tokenConsumption;

    // 工具调用延迟
    private final Timer toolCallTimer;

    // 工具调用失败率
    private final Counter toolFailureCounter;

    public AgentMetrics(MeterRegistry registry) {
        this.llmCallCounter = Counter.builder("llm.call.count")
            .description("LLM call count")
            .tag("type", "all")
            .register(registry);

        this.tokenConsumption = Counter.builder("llm.token.consumption")
            .description("Token consumption")
            .register(registry);

        this.toolCallTimer = Timer.builder("tool.call.duration")
            .description("Tool call duration")
            .register(registry);

        this.toolFailureCounter = Counter.builder("tool.call.failure")
            .description("Tool call failure count")
            .register(registry);
    }

    public void recordLLMCall(String model, boolean success, int tokens) {
        llmCallCounter.increment(
            Tags.of("model", model, "status", success ? "success" : "error"));

        if (success) {
            tokenConsumption.increment(
                Tags.of("model", model), tokens);
        }
    }

    public void recordToolCall(String tool, long duration, boolean success) {
        toolCallTimer.record(duration, TimeUnit.MILLISECONDS,
            Tags.of("tool", tool));

        if (!success) {
            toolFailureCounter.increment(Tags.of("tool", tool));
        }
    }
}
```
1. **Prometheus 告警规则**：

```yaml
groups:
  - name: agent_alerts
    rules:
      # LLM 调用成功率低于 95%
      - alert: LLMLowSuccessRate
        expr: |
          sum(rate(llm_call_count{status="success"}[5m]))
          / sum(rate(llm_call_count[5m])) < 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM success rate below 95%"

      # Token 消耗量异常增长
      - alert: HighTokenConsumption
        expr: rate(llm_token_consumption[1h]) > 10000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Token consumption rate too high"

      # 工具调用延迟 P95 超过 5s
      - alert: ToolCallHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(tool_call_duration_bucket[5m])) > 5000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Tool call P95 latency over 5s"
```
1. **Grafana Dashboard 面板**：

```json
{
  "panels": [
    {
      "title": "LLM 调用成功率",
      "targets": [
        {
          "expr": "sum(rate(llm_call_count{status=\"success\"}[5m])) / sum(rate(llm_call_count[5m]))"
        }
      ]
    },
    {
      "title": "Token 消耗量",
      "targets": [
        {
          "expr": "sum(rate(llm_token_consumption[5m])) by (model)"
        }
      ]
    },
    {
      "title": "工具调用延迟 P95",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(tool_call_duration_bucket[5m])) by (le, tool))"
        }
      ]
    }
  ]
}
```
1. **指标最佳实践**：
  - **标签设计**：`model`（模型名称）、`tool`（工具名称）、`status`（成功/失败）
  - **基数控制**：避免高基数标签（如 user_id）
  - **指标命名**：使用下划线分隔，单位后缀（`_bytes`, `_seconds`）

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
只说了 Counter/Timer
</td>
<td>
完整指标设计+告警规则+Grafana 面板
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道标签设计原则
</td>
<td>
清楚基数控制和命名规范
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有告警规则
</td>
<td>
有完整的监控告警体系
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 Micrometer
</td>
<td>
有生产环境可观测性经验
</td>
</tr>
</table>

---

#### 4、容易一起考的题

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
Micrometer 的指标类型有哪些？
</td>
<td>
指标基础，Counter/Gauge/Timer/Histogram
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：指标基础，Counter/Gauge/Timer/Histogram，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Prometheus 的 PromQL 语法？
</td>
<td>
查询指标，监控告警的基础
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
Grafana 如何配置 Dashboard？
</td>
<td>
可视化展示，监控体系的最后一环
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
</table>

---

### 3.4 Spring Boot 测试

#### 1、基础题：@SpringBootTest 和 @WebMvcTest 有什么区别？各自适用什么场景？

**难度级别**：⭐⭐（集成测试、Slice 测试、Mock 依赖）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- @SpringBootTest
- @WebMvcTest
- 其他 Slice 测试
- 选择原则
- 启动完整容器：加载整个应用上下文（包括 Controller、Service、Repository 等）。
- 适用场景：端到端测试、集成测试、需要测试多个组件协作的场景。

**2️⃣ Impressive Answer**
1. **@SpringBootTest**：
  - **启动完整容器**：加载整个应用上下文（包括 Controller、Service、Repository 等）。
  - **适用场景**：端到端测试、集成测试、需要测试多个组件协作的场景。
  - **缺点**：启动慢，依赖真实的外部服务（数据库、Redis 等）。

```java
@SpringBootTest
@AutoConfigureMockMvc
public class AgentIntegrationTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    public void testExecuteTool() throws Exception {
        mockMvc.perform(post("/api/agent/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"tool\":\"weather\",\"params\":{\"city\":\"杭州\"}}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.result").exists());
    }
}
```
1. **@WebMvcTest**：
  - **Slice 测试**：只加载 Web 层（Controller、ControllerAdvice、Filter 等），不加载 Service 和 Repository。
  - **自动 Mock**：Service 层的 Bean 自动被 Mock，需要用 @MockBean 模拟行为。
  - **适用场景**：单元测试 Controller、测试 API 输入输出、验证异常处理。

```java
@WebMvcTest(AgentController.class)
public class AgentControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AgentService agentService;

    @Test
    public void testExecuteTool() throws Exception {
        when(agentService.executeTool(any()))
            .thenReturn(ToolResult.success("result"));

        mockMvc.perform(post("/api/agent/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"tool\":\"weather\",\"params\":{\"city\":\"杭州\"}}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.result").value("result"));
    }
}
```
1. **其他 Slice 测试**：
  - `@DataJpaTest`：只测试 JPA 层，自动配置嵌入式数据库（H2）。
  - `@JsonTest`：只测试 JSON 序列化/反序列化。
  - `@WebFluxTest`：测试 WebFlux Controller。
1. **选择原则**：
  - **单元测试**：优先用 Slice 测试（@WebMvcTest、@DataJpaTest）。
  - **集成测试**：用 @SpringBootTest，但尽量减少数量。
  - **测试金字塔**：70% 单元测试 → 20% 集成测试 → 10% 端到端测试。

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
只说了区别和适用场景
</td>
<td>
包含代码示例、Slice 测试类型、测试金字塔
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Slice 测试的自动 Mock
</td>
<td>
清楚 @MockBean 的工作机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有测试金字塔概念
</td>
<td>
有测试策略和分层测试经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道测试注解
</td>
<td>
有完整的测试架构设计能力
</td>
</tr>
</table>

---

#### 2、进阶题：Spring Boot 测试的 Slice 测试（@DataJpaTest、@WebMvcTest 等）是如何实现的？如何 Mock 外部依赖？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- Slice 测试实现原理
- @MockBean 工作机制
- Mock 外部依赖示例
- @SpyBean vs @MockBean
- Mock 静态方法（Mockito 3.4+）
- 通过 @BootstrapWith 指定自定义的 TestContextBootstrapper。

**2️⃣ Impressive Answer**
1. **Slice 测试实现原理**：
  - 通过 `@BootstrapWith` 指定自定义的 `TestContextBootstrapper`。
  - `TestContextBootstrapper` 根据 `@TestConfiguration` 和 `@Import` 过滤 BeanDefinition，只加载特定层的 Bean。
  - 例如 `@WebMvcTest` 只加载 `@Controller`、`@ControllerAdvice`、`@Filter` 等注解的 Bean。
1. **@MockBean 工作机制**：
  - `@MockBean` 通过 `MockitoPostProcessor` 在测试上下文中注册 Mockito Mock 对象。
  - Mock 对象会替换容器中同类型的真实 Bean（包括 @Primary 和 @Qualifier）。
  - 支持按类型、按名称、按限定符匹配要替换的 Bean。
1. **Mock 外部依赖示例**：

```java
@WebMvcTest(AgentController.class)
public class AgentControllerTest {
    @MockBean
    private AgentService agentService;

    @MockBean
    private LLMProvider llmProvider;  // Mock 外部 LLM 服务

    @Test
    public void testExecuteTool() {
        // Mock Service 层
        when(agentService.executeTool(any()))
            .thenReturn(ToolResult.success("result"));

        // Mock 外部 LLM 服务
        when(llmProvider.chat(anyString(), anyString()))
            .thenReturn("AI response");
    }
}
```
1. **@SpyBean vs @MockBean**：
  - `@MockBean`：完全 Mock，所有方法默认返回默认值（null、0、false）。
  - `@SpyBean`：部分 Mock，真实方法会被调用，可以 `when(spy.method()).thenCallRealMethod()`。
1. **Mock 静态方法**（Mockito 3.4+）：

```java
@Test
public void testStaticMethod() {
    try (MockedStatic<UUID> mocked = mockStatic(UUID.class)) {
        mocked.when(UUID::randomUUID).thenReturn(uuid);
        // 测试代码
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
结构性
</td>
<td>
只说了 MockBean
</td>
<td>
包含实现原理、SpyBean、静态方法 Mock
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 TestContextBootstrapper
</td>
<td>
清楚 Slice 测试的过滤机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有静态方法 Mock
</td>
<td>
有完整的 Mock 技术栈经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 Mock
</td>
<td>
理解测试框架的底层机制
</td>
</tr>
</table>

---

#### 3、场景题：Agent 服务的工具调用逻辑需要单元测试，但工具调用依赖外部 LLM API，如何用 Mockito + @MockBean 实现隔离测试？

**难度级别**：⭐⭐⭐（隔离测试、Mock 链式调用、参数匹配、异常测试）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 工具调用服务设计
- 隔离测试实现
- 参数匹配器
- 验证调用次数和顺序
- 集成测试（@SpringBootTest）

**2️⃣ Impressive Answer**
1. **工具调用服务设计**：

```java
@Service
public class ToolExecutor {
    private final LLMProvider llmProvider;

    public ToolExecutor(LLLMProvider llmProvider) {
        this.llmProvider = llmProvider;
    }

    public ToolResult execute(ToolCall call) {
        try {
            String prompt = buildPrompt(call);
            String response = llmProvider.chat(prompt, call.getModel());
            return parseResponse(response);
        } catch (LLMException e) {
            return ToolResult.error(e.getMessage());
        }
    }
}
```
1. **隔离测试实现**：

```java
@ExtendWith(MockitoExtension.class)
public class ToolExecutorTest {

    @Mock
    private LLMProvider llmProvider;

    @InjectMocks
    private ToolExecutor toolExecutor;

    @Test
    public void testExecuteSuccess() {
        // 准备测试数据
        ToolCall call = ToolCall.builder()
            .tool("weather")
            .params(Map.of("city", "杭州"))
            .build();

        // Mock 外部依赖
        when(llmProvider.chat(
            startsWith("查询杭州的天气"),
            eq("gpt-4")
        )).thenReturn("{\"temperature\": 25, \"weather\": \"晴\"}");

        // 执行测试
        ToolResult result = toolExecutor.execute(call);

        // 验证结果
        assertThat(result.isSuccess()).isTrue();
        assertThat(result.getData()).containsEntry("temperature", 25);

        // 验证 Mock 被调用
        verify(llmProvider, times(1))
            .chat(anyString(), eq("gpt-4"));
    }

    @Test
    public void testExecuteFailure() {
        ToolCall call = ToolCall.builder()
            .tool("weather")
            .params(Map.of("city", "杭州"))
            .build();

        // Mock 异常情况
        when(llmProvider.chat(anyString(), anyString()))
            .thenThrow(new LLMException("API rate limit exceeded"));

        ToolResult result = toolExecutor.execute(call);

        assertThat(result.isError()).isTrue();
        assertThat(result.getError()).contains("rate limit");
    }

    @Test
    public void testExecuteWithMultipleCalls() {
        // Mock 多次调用返回不同结果
        when(llmProvider.chat(anyString(), anyString()))
            .thenReturn("{\"result\": \"first\"}")
            .thenReturn("{\"result\": \"second\"}");

        ToolResult result1 = toolExecutor.execute(call1);
        ToolResult result2 = toolExecutor.execute(call2);

        assertThat(result1.getData()).containsEntry("result", "first");
        assertThat(result2.getData()).containsEntry("result", "second");
    }
}
```
1. **参数匹配器**：

```java
// 精确匹配
when(llmProvider.chat("exact prompt", "gpt-4")).thenReturn(...);

// 任意参数
when(llmProvider.chat(anyString(), anyString())).thenReturn(...);

// 部分匹配
when(llmProvider.chat(
    startsWith("查询"),
    endsWith("-4")
)).thenReturn(...);

// 自定义匹配器
when(llmProvider.chat(argThat(prompt -> prompt.length() > 10), anyString()))
    .thenReturn(...);
```
1. **验证调用次数和顺序**：

```java
// 验证调用次数
verify(llmProvider, times(2)).chat(anyString(), anyString());
verify(llmProvider, never()).chat(eq("forbidden"), anyString());
verify(llmProvider, atLeastOnce()).chat(anyString(), anyString());

// 验证调用顺序
InOrder inOrder = inOrder(llmProvider);
inOrder.verify(llmProvider).chat(eq("first"), anyString());
inOrder.verify(llmProvider).chat(eq("second"), anyString());
```
1. **集成测试（@SpringBootTest）**：

```java
@SpringBootTest
@AutoConfigureMockMvc
public class ToolExecutionIntegrationTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private LLMProvider llmProvider;

    @Test
    public void testToolExecutionApi() throws Exception {
        when(llmProvider.chat(anyString(), anyString()))
            .thenReturn("{\"result\": \"test\"}");

        mockMvc.perform(post("/api/tools/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"tool\":\"weather\",\"params\":{\"city\":\"杭州\"}}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data.result").value("test"));
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
结构性
</td>
<td>
只说了基本的 Mock
</td>
<td>
包含参数匹配、验证、异常测试、集成测试
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道参数匹配器
</td>
<td>
清楚 Mockito 的完整 API
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有验证调用次数
</td>
<td>
有完整的测试覆盖经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会写单元测试
</td>
<td>
有测试驱动开发的工程化能力
</td>
</tr>
</table>

---

#### 4、容易一起考的题

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
JUnit 5 的新特性有哪些？
</td>
<td>
单元测试框架的演进
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：单元测试框架的演进，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何测试私有方法？
</td>
<td>
测试边界情况的讨论
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：测试边界情况的讨论，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
测试覆盖率如何计算？
</td>
<td>
测试质量的评估指标
</td>
<td>
答：LLM-as-Judge 要先定义评分 Rubric，再处理位置偏差、冗长偏差和自我偏差；工程上用多 Judge 投票和人工 Golden Set 做校准。
</td>
</tr>
</table>

---

### 3.5 条件注解与自动装配扩展

#### 1、基础题：@Conditional 家族注解有哪些？各自的使用场景是什么？

**难度级别**：⭐⭐（条件注解、自动装配条件控制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 类路径条件
- Bean 条件
- 配置条件
- 环境条件
- Web 条件
- 自定义 Condition

**2️⃣ Impressive Answer**
1. **类路径条件**：
  - `@ConditionalOnClass`：类路径上存在指定类时生效（如 `@ConditionalOnClass(Tomcat.class)`）
  - `@ConditionalOnMissingClass`：类路径上不存在指定类时生效
1. **Bean 条件**：
  - `@ConditionalOnBean`：容器中存在指定 Bean 时生效
  - `@ConditionalOnMissingBean`：容器中不存在指定 Bean 时生效（**用户自定义优先**的核心机制）
  - `@ConditionalOnSingleCandidate`：容器中只有一个候选 Bean 时生效
1. **配置条件**：
  - `@ConditionalOnProperty`：配置文件中存在指定属性且值匹配时生效

```java
// 通过配置开关控制功能启停
@ConditionalOnProperty(
    prefix = "agent.tool",
    name = "enabled",
    havingValue = "true",
    matchIfMissing = true  // 没有配置时默认生效
)
@Bean
public WeatherTool weatherTool() {
    return new WeatherTool();
}
```
1. **环境条件**：
  - `@ConditionalOnExpression`：SpEL 表达式为 true 时生效
  - `@Profile`：激活指定 Profile 时生效（本质是 `@Conditional(ProfileCondition.class)`）
1. **Web 条件**：
  - `@ConditionalOnWebApplication`：是 Web 应用时生效
  - `@ConditionalOnNotWebApplication`：不是 Web 应用时生效
1. **自定义 Condition**：

```java
public class OnLLMProviderCondition implements Condition {

    @Override
    public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        Environment env = context.getEnvironment();
        String provider = env.getProperty("agent.llm.provider");
        // 只有配置了 provider 才加载对应的 Bean
        return provider != null && !provider.isEmpty();
    }
}

@Conditional(OnLLMProviderCondition.class)
@Bean
public LLMClient llmClient() {
    return new LLMClient();
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
结构性
</td>
<td>
只说了两个注解
</td>
<td>
6 大类条件注解，覆盖所有场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 matchIfMissing
</td>
<td>
清楚各注解的细节参数
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有自定义 Condition
</td>
<td>
有完整的自定义条件实现
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过注解名
</td>
<td>
理解条件注解的设计意图
</td>
</tr>
</table>

---

#### 2、进阶题：@ConditionalOnMissingBean 的判断时机是什么？为什么用户自定义的 Bean 能覆盖自动配置？

**难度级别**：⭐⭐⭐（Bean 注册顺序、DeferredImportSelector、自动配置优先级）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 核心机制：DeferredImportSelector
- 判断时机
- 正确覆盖姿势
- 延迟：AutoConfigurationImportSelector 实现了 DeferredImportSelector，到所有 @Configuration 类处理完之后才...
- 用户的 @Configuration 类（通过 @ComponentScan 扫描）先于自动配置类处理。
- 因此用户的 Bean 先注册到容器，自动配置类执行时 @ConditionalOnMissingBean 检查到已有 Bean，跳过创建。

**2️⃣ Impressive Answer**
1. **核心机制：DeferredImportSelector**：
  - `AutoConfigurationImportSelector` 实现了 `DeferredImportSelector`，**延迟**到所有 `@Configuration` 类处理完之后才执行。
  - 用户的 `@Configuration` 类（通过 `@ComponentScan` 扫描）先于自动配置类处理。
  - 因此用户的 Bean 先注册到容器，自动配置类执行时 `@ConditionalOnMissingBean` 检查到已有 Bean，跳过创建。
1. **判断时机**：
  - `@ConditionalOnMissingBean` 的判断发生在 **BeanDefinition 注册阶段**，而非 Bean 实例化阶段。
  - `ConditionEvaluator` 在处理每个 `@Bean` 方法时调用 `Condition.matches()`，此时已注册的 BeanDefinition 都可以被检测到。
1. **正确覆盖姿势**：

```java
// 用户自定义配置，覆盖自动配置的 DataSource
@Configuration
public class MyDataSourceConfig {

    @Bean
    // 不需要加任何条件注解，因为自动配置的 DataSource 有 @ConditionalOnMissingBean
    public DataSource dataSource() {
        return new HikariDataSource(myConfig());
    }
}
```
1. **常见陷阱**：`@ConditionalOnMissingBean` 只检查当前已注册的 BeanDefinition，如果两个自动配置类都没有 `@ConditionalOnMissingBean` 保护，会导致 Bean 重复注册冲突。

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
只说了&quot;先后顺序&quot;
</td>
<td>
DeferredImportSelector 机制 + 判断时机 + 陷阱
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 DeferredImportSelector
</td>
<td>
清楚延迟导入的设计意图
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道判断发生在哪个阶段
</td>
<td>
清楚 BeanDefinition 注册阶段的判断逻辑
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道结论但不知道原因
</td>
<td>
理解 Spring Boot 自动配置的核心设计
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
Spring Boot 自动装配的完整链路？
</td>
<td>
条件注解是自动装配的核心控制机制
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
BeanDefinition 的注册流程？
</td>
<td>
条件注解判断发生在 BeanDefinition 注册阶段
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
如何自定义一个 Spring Boot Starter？
</td>
<td>
Starter 的核心就是条件注解的合理使用
</td>
<td>
答：三个核心步骤；条件注解是关键；常见陷阱
</td>
</tr>
</table>

---

### 3.6 配置绑定机制

#### 1、基础题：@ConfigurationProperties 和 @Value 有什么区别？各自适用什么场景？

**难度级别**：⭐⭐（配置绑定、类型安全、松散绑定）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 核心区别对比
- @ConfigurationProperties 最佳实践
- @Value 的 SpEL 能力

**2️⃣ Impressive Answer**
1. **核心区别对比**：

<table>
<tr>
<td>
维度
</td>
<td>
@Value
</td>
<td>
@ConfigurationProperties
</td>
</tr>
<tr>
<td>
绑定粒度
</td>
<td>
单个属性
</td>
<td>
整个前缀下的属性组
</td>
</tr>
<tr>
<td>
类型安全
</td>
<td>
不支持（运行时失败）
</td>
<td>
支持（启动时校验）
</td>
</tr>
<tr>
<td>
松散绑定
</td>
<td>
不支持
</td>
<td>
支持（<code>server-port</code> = <code>serverPort</code>）
</td>
</tr>
<tr>
<td>
SpEL 表达式
</td>
<td>
支持
</td>
<td>
不支持
</td>
</tr>
<tr>
<td>
元数据提示
</td>
<td>
不支持
</td>
<td>
支持（IDE 自动补全）
</td>
</tr>
<tr>
<td>
适用场景
</td>
<td>
少量、简单配置
</td>
<td>
模块化配置、复杂对象
</td>
</tr>
</table>
1. **@ConfigurationProperties 最佳实践**：

```java
@ConfigurationProperties(prefix = "agent.llm")
@Validated  // 开启 JSR-303 校验
public class LLMProperties {

    @NotBlank
    private String apiKey;

    @Min(1)
    @Max(4096)
    private int maxTokens = 2048;

    private double temperature = 0.7;

    private List<String> models = new ArrayList<>();

    // getter/setter 省略
}

// 注册到容器（二选一）
@EnableConfigurationProperties(LLMProperties.class)
// 或者在类上加 @Component
```
1. **松散绑定规则**：`agent.llm.api-key`、`agent.llm.apiKey`、`AGENT_LLM_API_KEY`（环境变量）都能绑定到 `apiKey` 字段。
1. **@Value 的 SpEL 能力**：

```java
// 支持默认值
@Value("${agent.timeout:30}")
private int timeout;

// 支持 SpEL 表达式
@Value("#{${agent.weights}}")
private Map<String, Double> weights;
```
1. **Agent 场景**：LLM 配置（API Key、模型参数、超时）用 `@ConfigurationProperties` 统一管理，支持多环境切换和配置校验，避免启动后才发现配置错误。

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
只说了&quot;批量 vs 单个&quot;
</td>
<td>
完整对比表 + 代码示例 + 松散绑定规则
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道松散绑定
</td>
<td>
清楚三种命名格式都能绑定
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有 @Validated 校验
</td>
<td>
有启动时配置校验的最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道区别
</td>
<td>
理解配置绑定的工程化最佳实践
</td>
</tr>
</table>

---

#### 2、进阶题：Spring Boot 的 Environment 抽象是什么？PropertySource 的优先级如何工作？

**难度级别**：⭐⭐⭐（Environment、PropertySource、配置覆盖机制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- Environment 抽象层次
- PropertySource 优先级链（从高到低）
- 自定义 PropertySource
- Environment 接口：提供 getProperty()、containsProperty()、getActiveProfiles() 等方法。
- ConfigurableEnvironment：可以添加/删除 PropertySource，获取 MutablePropertySources。
- StandardEnvironment：非 Web 环境，包含系统属性和环境变量两个 PropertySource。

**2️⃣ Impressive Answer**
1. **Environment 抽象层次**：
  - `Environment` 接口：提供 `getProperty()`、`containsProperty()`、`getActiveProfiles()` 等方法。
  - `ConfigurableEnvironment`：可以添加/删除 `PropertySource`，获取 `MutablePropertySources`。
  - `StandardEnvironment`：非 Web 环境，包含系统属性和环境变量两个 PropertySource。
  - `StandardServletEnvironment`：Web 环境，额外包含 Servlet 配置和上下文参数。
1. **PropertySource 优先级链（从高到低）**：

```
命令行参数（CommandLinePropertySource）
  ↓
Servlet 配置参数（ServletConfig/ServletContext）
  ↓
JNDI 属性
  ↓
Java 系统属性（System.getProperties()）
  ↓
系统环境变量（System.getenv()）
  ↓
application-{profile}.yml（激活的 Profile）
  ↓
application.yml（默认配置）
  ↓
@PropertySource 注解引入的配置
  ↓
默认属性（SpringApplication.setDefaultProperties()）
```
1. **自定义 PropertySource**：

```java
@Component
public class NacosPropertySourceLoader implements EnvironmentPostProcessor {

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment,
                                       SpringApplication application) {
        // 从 Nacos 加载配置，插入到高优先级位置
        Map<String, Object> nacosProperties = loadFromNacos();
        MapPropertySource nacosSource =
            new MapPropertySource("nacos", nacosProperties);

        // addFirst 保证 Nacos 配置优先级最高（仅次于命令行）
        environment.getPropertySources().addFirst(nacosSource);
    }
}
```
1. **EnvironmentPostProcessor 注册**：在 `META-INF/spring.factories` 中注册（Boot 2.x）或 `META-INF/spring/org.springframework.boot.env.EnvironmentPostProcessor.imports`（Boot 3.x）。

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
只说了&quot;命令行最高&quot;
</td>
<td>
完整优先级链 + Environment 层次 + 自定义扩展
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 EnvironmentPostProcessor
</td>
<td>
清楚配置中心集成的扩展点
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有自定义 PropertySource
</td>
<td>
有 Nacos 集成的完整实现思路
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道优先级
</td>
<td>
理解 Environment 抽象的扩展机制
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
Spring Boot 配置加载优先级？
</td>
<td>
PropertySource 优先级的具体体现
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Nacos/Apollo 配置中心如何集成？
</td>
<td>
自定义 PropertySource 的典型应用
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：自定义 PropertySource 的典型应用，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
@RefreshScope 动态刷新原理？
</td>
<td>
配置变更后如何让 Bean 感知到
</td>
<td>
答：多模态输入先做解析和标准化，把图片、语音、文档转成文本、结构化字段或 embedding，再进入检索、规划和推理链路。
</td>
</tr>
</table>

---

### 3.7 Spring Boot 事件机制

#### 1、基础题：Spring Boot 有哪些内置的应用事件？发布顺序是什么？

**难度级别**：⭐⭐（ApplicationEvent、事件发布顺序、监听器）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- Spring Boot 启动事件完整顺序
- 监听方式
- 自定义事件

**2️⃣ Impressive Answer**
1. **Spring Boot 启动事件完整顺序**：

```
ApplicationStartingEvent        → SpringApplication.run() 刚开始，容器还未创建
ApplicationEnvironmentPreparedEvent → Environment 准备完成，配置已加载
ApplicationContextInitializedEvent  → ApplicationContext 创建完成，Initializer 执行完
ApplicationPreparedEvent        → BeanDefinition 加载完成，Bean 还未实例化
ApplicationStartedEvent         → refreshContext 完成，Bean 已实例化
ApplicationReadyEvent           → Runner 执行完成，应用完全就绪
ApplicationFailedEvent          → 启动失败时发布
```
1. **监听方式**：

```java
// 方式一：@EventListener 注解（容器刷新后的事件）
@Component
public class AgentStartupListener {

    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady(ApplicationReadyEvent event) {
        // 应用完全就绪后，预热 LLM 连接池
        llmClient.warmUp();
    }
}

// 方式二：实现 ApplicationListener 接口（可监听容器刷新前的事件）
public class EnvironmentPreparedListener
        implements ApplicationListener<ApplicationEnvironmentPreparedEvent> {

    @Override
    public void onApplicationEvent(ApplicationEnvironmentPreparedEvent event) {
        // 容器刷新前，可以修改 Environment
        ConfigurableEnvironment env = event.getEnvironment();
        // 动态注入配置
    }
}
```
1. **注意事项**：`ApplicationStartingEvent` 和 `ApplicationEnvironmentPreparedEvent` 发布时容器还未创建，**不能用 @EventListener**，必须通过 `SpringApplication.addListeners()` 或 `spring.factories` 注册。
1. **自定义事件**：

```java
// 定义事件
public class LLMCallCompletedEvent extends ApplicationEvent {
    private final String model;
    private final int tokensUsed;

    public LLMCallCompletedEvent(Object source, String model, int tokensUsed) {
        super(source);
        this.model = model;
        this.tokensUsed = tokensUsed;
    }
}

// 发布事件
@Autowired
private ApplicationEventPublisher eventPublisher;

eventPublisher.publishEvent(new LLMCallCompletedEvent(this, "gpt-4", 512));

// 监听事件
@EventListener
public void onLLMCallCompleted(LLMCallCompletedEvent event) {
    metricsService.recordTokenUsage(event.getModel(), event.getTokensUsed());
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
结构性
</td>
<td>
只说了几个事件名
</td>
<td>
完整顺序 + 两种监听方式 + 注意事项
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道容器刷新前的事件限制
</td>
<td>
清楚哪些事件不能用 @EventListener
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有自定义事件
</td>
<td>
有完整的自定义事件发布/监听实现
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过事件名
</td>
<td>
理解事件机制的完整链路和限制
</td>
</tr>
</table>

---

#### 2、进阶题：ApplicationRunner 和 CommandLineRunner 有什么区别？执行时机是什么？

**难度级别**：⭐⭐（Runner 接口、启动后执行、执行顺序）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 核心区别
- 执行时机
- 执行顺序控制
- Agent 场景

**2️⃣ Impressive Answer**
1. **核心区别**：

<table>
<tr>
<td>
维度
</td>
<td>
CommandLineRunner
</td>
<td>
ApplicationRunner
</td>
</tr>
<tr>
<td>
参数类型
</td>
<td>
<code>String[]</code>（原始命令行参数）
</td>
<td>
<code>ApplicationArguments</code>（结构化参数）
</td>
</tr>
<tr>
<td>
参数解析
</td>
<td>
需要手动解析 <code>--key=value</code>
</td>
<td>
自动解析，支持 <code>getOptionValues(&quot;key&quot;)</code>
</td>
</tr>
<tr>
<td>
适用场景
</td>
<td>
简单脚本、参数不复杂
</td>
<td>
需要解析命名参数的场景
</td>
</tr>
</table>
1. **执行时机**：在 `ApplicationStartedEvent` 之后、`ApplicationReadyEvent` 之前执行，此时容器已完全刷新，所有 Bean 已就绪。
1. **执行顺序控制**：通过 `@Order` 注解控制多个 Runner 的执行顺序（值越小越先执行）。

```java
@Component
@Order(1)
public class DatabaseInitRunner implements ApplicationRunner {

    @Override
    public void run(ApplicationArguments args) throws Exception {
        // 先初始化数据库
        if (args.containsOption("init-db")) {
            databaseService.initialize();
        }
    }
}

@Component
@Order(2)
public class LLMWarmUpRunner implements CommandLineRunner {

    @Override
    public void run(String... args) throws Exception {
        // 后预热 LLM 连接
        llmClient.warmUp();
    }
}
```
1. **Agent 场景**：启动时预加载 Embedding 模型、预热向量数据库连接、初始化工具注册表，避免第一次请求时的冷启动延迟。

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
只说了参数类型区别
</td>
<td>
对比表 + 执行时机 + 顺序控制 + 场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道执行时机
</td>
<td>
清楚在哪两个事件之间执行
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有 @Order 控制
</td>
<td>
有多 Runner 顺序控制的实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道区别
</td>
<td>
理解 Runner 在启动流程中的定位
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
Spring Boot 启动流程？
</td>
<td>
事件和 Runner 都是启动流程的组成部分
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@PostConstruct 和 ApplicationRunner 的区别？
</td>
<td>
启动后执行逻辑的不同方式对比
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：启动后执行逻辑的不同方式对比，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring 的事件驱动模型（观察者模式）？
</td>
<td>
事件机制的设计模式基础
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.8 Spring Boot 3.x 新特性

#### 1、基础题：Spring Boot 3.x 相比 2.x 有哪些重要变化？

**难度级别**：⭐⭐（版本迁移、Jakarta EE、Java 17 基线）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 基础要求升级
- 自动配置机制变化
- AOT（Ahead-of-Time）编译支持
- 可观测性增强
- 其他重要变化
- Java 17 基线：不再支持 Java 8/11，可以使用 Record、Sealed Class、Pattern Matching 等新特性。

**2️⃣ Impressive Answer**
1. **基础要求升级**：
  - **Java 17 基线**：不再支持 Java 8/11，可以使用 Record、Sealed Class、Pattern Matching 等新特性。
  - **Jakarta EE 10**：所有 `javax.*` 包迁移到 `jakarta.*`（如 `javax.servlet` → `jakarta.servlet`），这是最大的迁移成本。
  - **Spring Framework 6.x**：底层框架同步升级。
1. **自动配置机制变化**：
  - 废弃 `spring.factories` 的 `EnableAutoConfiguration` 入口。
  - 迁移到 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`。
  - 新增 `@AutoConfiguration` 注解替代 `@Configuration`，语义更清晰。
1. **AOT（Ahead-of-Time）编译支持**：
  - Spring Boot 3.x 内置 AOT 处理器，在构建时分析 Bean 定义，生成静态代码。
  - 为 GraalVM 原生镜像编译提供支持，大幅减少反射使用。
  - `mvn spring-boot:build-image` 可直接构建原生镜像。
1. **可观测性增强**：
  - 内置 Micrometer Tracing（替代 Spring Cloud Sleuth），支持分布式链路追踪。
  - 自动集成 OpenTelemetry，无需额外配置。
1. **其他重要变化**：
  - `HttpExchange` 接口替代 Feign，声明式 HTTP 客户端内置支持。
  - 问题详情（RFC 7807）支持，`ProblemDetail` 标准化错误响应。
  - `@ControllerAdvice` 支持函数式异常处理。

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
只说了 Java 17 和 jakarta
</td>
<td>
5 大变化：基础要求+自动配置+AOT+可观测性+其他
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 AOT 编译
</td>
<td>
清楚 AOT 对 GraalVM 原生镜像的意义
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道迁移成本
</td>
<td>
知道 javax→jakarta 是最大迁移成本
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道版本号
</td>
<td>
理解版本升级的技术演进方向
</td>
</tr>
</table>

---

#### 2、进阶题：Spring Boot 3.x 的 AOT 编译和 GraalVM 原生镜像是什么？有什么优缺点？

**难度级别**：⭐⭐⭐（AOT、GraalVM、原生镜像、冷启动优化）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- AOT vs JIT 对比
- Spring Boot AOT 处理流程
- 性能对比
- Agent 场景适用性
- JIT（Just-In-Time）：运行时编译，启动慢（需要 JVM 预热），但长期运行性能好。
- AOT（Ahead-of-Time）：构建时编译，启动极快（毫秒级），内存占用低，但失去 JIT 优化。

**2️⃣ Impressive Answer**
1. **AOT vs JIT 对比**：
  - **JIT（Just-In-Time）**：运行时编译，启动慢（需要 JVM 预热），但长期运行性能好。
  - **AOT（Ahead-of-Time）**：构建时编译，启动极快（毫秒级），内存占用低，但失去 JIT 优化。
1. **Spring Boot AOT 处理流程**：

```
mvn spring-boot:process-aot
  ↓
AOT 处理器分析 BeanDefinition
  ↓
生成静态 Bean 注册代码（替代反射）
  ↓
生成 GraalVM 反射配置（reflect-config.json）
  ↓
GraalVM native-image 编译
  ↓
原生可执行文件（无需 JVM）
```
1. **性能对比**：

<table>
<tr>
<td>
指标
</td>
<td>
JVM 模式
</td>
<td>
GraalVM 原生镜像
</td>
</tr>
<tr>
<td>
启动时间
</td>
<td>
2-10 秒
</td>
<td>
<strong>50-200 毫秒</strong>
</td>
</tr>
<tr>
<td>
内存占用
</td>
<td>
200-500 MB
</td>
<td>
<strong>50-100 MB</strong>
</td>
</tr>
<tr>
<td>
峰值吞吐量
</td>
<td>
高（JIT 优化）
</td>
<td>
较低（无 JIT）
</td>
</tr>
<tr>
<td>
编译时间
</td>
<td>
秒级
</td>
<td>
<strong>分钟级</strong>
</td>
</tr>
<tr>
<td>
动态特性
</td>
<td>
完全支持
</td>
<td>
受限（反射需配置）
</td>
</tr>
</table>
1. **Agent 场景适用性**：
  - **适合**：Serverless 函数、CLI 工具、冷启动敏感的场景（如 K8s 快速扩容）。
  - **不适合**：需要动态加载类、大量反射的 Agent 框架（如 LangChain4J 的动态代理）。
1. **常见问题**：反射、动态代理、序列化需要额外配置 `reflect-config.json`；第三方库兼容性问题（需要 GraalVM 支持）。

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
只说了优缺点
</td>
<td>
AOT 流程 + 性能对比表 + 场景适用性
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 AOT 处理流程
</td>
<td>
清楚 Spring Boot AOT 的完整编译链路
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道 Agent 场景的适用性
</td>
<td>
有 Serverless vs 长期运行的选型判断
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道原生镜像
</td>
<td>
理解 AOT 的工程权衡
</td>
</tr>
</table>

---

#### 3、场景题：Agent 服务需要快速冷启动（K8s 弹性扩容），如何用 Spring Boot 3.x 优化启动时间？

**难度级别**：⭐⭐⭐（启动优化、懒加载、AOT、类路径扫描优化）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 启动优化分层策略
- 第二层：减少类路径扫描范围
- 第三层：排除不需要的自动配置
- 第四层：AOT + 原生镜像（终极方案）
- 启动时间基准测试

**2️⃣ Impressive Answer**
1. **启动优化分层策略**：

```yaml
# 第一层：懒加载（最简单，效果明显）
spring:
  main:
    lazy-initialization: true  # 所有 Bean 延迟到第一次使用时初始化
```
1. **第二层：减少类路径扫描范围**：

```java
@SpringBootApplication(scanBasePackages = "com.example.agent")
// 精确指定扫描包，避免扫描整个类路径
```
1. **第三层：排除不需要的自动配置**：

```java
@SpringBootApplication(exclude = {
    DataSourceAutoConfiguration.class,    // 不用数据库
    SecurityAutoConfiguration.class,      // 不用 Security
    FlywayAutoConfiguration.class         // 不用数据库迁移
})
```
1. **第四层：AOT + 原生镜像（终极方案）**：

```xml
<!-- pom.xml -->
<plugin>
    <groupId>org.graalvm.buildtools</groupId>
    <artifactId>native-maven-plugin</artifactId>
</plugin>
```

```bash
# 构建原生镜像
mvn -Pnative spring-boot:build-image

# 启动时间从 5s → 100ms
```
1. **启动时间基准测试**：

<table>
<tr>
<td>
优化手段
</td>
<td>
启动时间
</td>
<td>
适用场景
</td>
</tr>
<tr>
<td>
无优化
</td>
<td>
5-10s
</td>
<td>
开发环境
</td>
</tr>
<tr>
<td>
懒加载
</td>
<td>
2-4s
</td>
<td>
生产环境（简单）
</td>
</tr>
<tr>
<td>
排除自动配置
</td>
<td>
1-3s
</td>
<td>
生产环境（精细化）
</td>
</tr>
<tr>
<td>
AOT 编译（JVM）
</td>
<td>
1-2s
</td>
<td>
生产环境（推荐）
</td>
</tr>
<tr>
<td>
GraalVM 原生镜像
</td>
<td>
50-200ms
</td>
<td>
Serverless/弹性扩容
</td>
</tr>
</table>
1. **懒加载的风险**：懒加载会把配置错误推迟到运行时才暴露，建议在测试环境关闭懒加载，生产环境开启。

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
只说了两个方案
</td>
<td>
4 层递进优化策略 + 基准测试数据
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道懒加载的风险
</td>
<td>
清楚懒加载推迟错误暴露的问题
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有量化数据
</td>
<td>
有各方案的启动时间对比
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道方向
</td>
<td>
有系统性的启动优化方案
</td>
</tr>
</table>

---

#### 4、容易一起考的题

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
Spring Boot 2.x 升级到 3.x 的迁移注意事项？
</td>
<td>
版本迁移的工程实践
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
GraalVM 和 JVM 的区别？
</td>
<td>
AOT 编译的底层原理
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：AOT 编译的底层原理，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
K8s 的 HPA（水平自动扩缩容）如何配置？
</td>
<td>
弹性扩容场景下的启动时间要求
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：弹性扩容场景下的启动时间要求，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

### 3.9 Spring Boot 启动优化与性能调优

#### 1、基础题：Spring Boot 应用启动慢的常见原因有哪些？如何排查？

**难度级别**：⭐⭐（启动性能、Bean 扫描、自动配置）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 常见原因分析
- 排查工具
- Spring Boot 启动耗时分析
- 快速定位方法
- 类路径扫描范围过大：@ComponentScan 扫描了不必要的包，包含大量第三方 jar。
- 自动配置过多：加载了不需要的自动配置类（如引入了 spring-boot-starter-data-jpa 但不用数据库）。

**2️⃣ Impressive Answer**
1. **常见原因分析**：
  - **类路径扫描范围过大**：`@ComponentScan` 扫描了不必要的包，包含大量第三方 jar。
  - **自动配置过多**：加载了不需要的自动配置类（如引入了 spring-boot-starter-data-jpa 但不用数据库）。
  - **Bean 初始化耗时**：某些 Bean 的 `@PostConstruct` 或构造函数有耗时操作（如建立连接、加载模型）。
  - **AOP 代理创建**：大量 `@Transactional`、`@Async` 注解导致代理对象创建耗时。
1. **排查工具**：

```bash
# 开启启动时间详细日志
java -jar app.jar --debug

# 使用 Spring Boot Actuator 的 startup 端点
management.endpoint.startup.enabled=true
# GET /actuator/startup 查看每个步骤的耗时
```
1. **Spring Boot 启动耗时分析**：

```java
// 自定义 ApplicationStartup 记录启动步骤耗时
@SpringBootApplication
public class AgentApplication {

    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(AgentApplication.class);
        // 记录详细的启动步骤
        app.setApplicationStartup(new BufferingApplicationStartup(2048));
        app.run(args);
    }
}
```
1. **快速定位方法**：
  - 看 `refreshContext` 耗时（Bean 实例化阶段）
  - 用 `@PostConstruct` 打时间戳，找出耗时的 Bean 初始化
  - 检查是否有同步的网络调用（如启动时连接外部服务）

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
只说了&quot;Bean 太多&quot;
</td>
<td>
4 大原因 + 排查工具 + 定位方法
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ApplicationStartup
</td>
<td>
清楚启动耗时分析的完整工具链
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有具体排查步骤
</td>
<td>
有系统性的排查方法论
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道方向
</td>
<td>
有生产环境性能排查经验
</td>
</tr>
</table>

---

#### 2、进阶题：Spring Boot DevTools 的热部署原理是什么？为什么生产环境要禁用？

**难度级别**：⭐⭐⭐（类加载器、热部署、双亲委派）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 热部署核心原理——双类加载器机制
- 触发机制
- 生产环境禁用的原因
- 配置排除
- Base ClassLoader：加载不会变化的类（第三方 jar、Spring 框架本身）。
- Restart ClassLoader：加载开发者自己的类（classpath 下的 class 文件）。

**2️⃣ Impressive Answer**
1. **热部署核心原理——双类加载器机制**：
  - **Base ClassLoader**：加载不会变化的类（第三方 jar、Spring 框架本身）。
  - **Restart ClassLoader**：加载开发者自己的类（`classpath` 下的 class 文件）。
  - 文件变化时，只丢弃并重建 `Restart ClassLoader`，`Base ClassLoader` 保留，因此比完整重启快得多。
1. **触发机制**：
  - 监听 `classpath` 下的文件变化（IDE 编译后触发）。
  - 默认排除静态资源（`/static`、`/public`、`/templates`）的变化，避免频繁重启。
1. **LiveReload 功能**：DevTools 内置 LiveReload 服务器（端口 35729），浏览器安装插件后，静态资源变化时自动刷新页面（不重启 JVM）。
1. **生产环境禁用的原因**：
  - **性能开销**：文件监听器持续消耗 CPU 和 IO。
  - **类加载器隔离问题**：双类加载器可能导致 `ClassCastException`（同一个类被两个 ClassLoader 加载，类型不兼容）。
  - **安全风险**：LiveReload 服务器暴露额外端口。
  - **自动禁用机制**：DevTools 检测到 `java -jar` 启动时自动禁用（通过检查 jar 包中是否有 `BOOT-INF` 目录判断）。
1. **配置排除**：

```yaml
spring:
  devtools:
    restart:
      exclude: static/**,public/**,templates/**
      additional-paths: src/main/java  # 额外监听路径
    livereload:
      enabled: false  # 禁用 LiveReload
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
结构性
</td>
<td>
只说了&quot;自动重启&quot;
</td>
<td>
双类加载器原理 + LiveReload + 禁用原因
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道双类加载器
</td>
<td>
清楚 Restart ClassLoader 的设计
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道 ClassCastException 风险
</td>
<td>
知道类加载器隔离导致的类型不兼容问题
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 DevTools
</td>
<td>
理解热部署的底层机制和风险
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
JVM 类加载器的双亲委派模型？
</td>
<td>
DevTools 热部署打破双亲委派的原理
</td>
<td>
答：工具调用题要讲 schema 描述、参数校验、权限控制、超时重试、幂等和观测；核心是让模型会选、会用、用错能兜底。
</td>
</tr>
<tr>
<td>
Spring Boot 懒加载如何配置？
</td>
<td>
启动优化的另一种手段
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
GraalVM 原生镜像 vs JVM 启动优化？
</td>
<td>
不同场景下的启动优化选型
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：不同场景下的启动优化选型，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

### 3.10 @Import 机制原理

#### 1、基础题：@Import 注解有哪几种用法？

**难度级别**：⭐⭐（@Import、ImportSelector、ImportBeanDefinitionRegistrar）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 直接导入配置类
- ImportSelector
- ImportBeanDefinitionRegistrar

**2️⃣ Impressive Answer**

`@Import` 有三种用法，复杂度递增：
1. **直接导入配置类**：最简单，等价于在当前配置类中声明那个类。

```java
@Configuration
@Import(DataSourceConfig.class)  // 直接导入另一个配置类
public class AppConfig {}
```
1. **ImportSelector**：动态决定导入哪些类，返回类名数组。`@EnableAutoConfiguration` 就是这种方式。

```java
public class LLMProviderSelector implements ImportSelector {

    @Override
    public String[] selectImports(AnnotationMetadata importingClassMetadata) {
        // 根据注解元数据动态决定导入哪个实现类
        Map<String, Object> attrs = importingClassMetadata
            .getAnnotationAttributes(EnableLLM.class.getName());
        String provider = (String) attrs.get("provider");

        return switch (provider) {
            case "openai" -> new String[]{OpenAIConfig.class.getName()};
            case "claude" -> new String[]{ClaudeConfig.class.getName()};
            default -> new String[]{DefaultLLMConfig.class.getName()};
        };
    }
}

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Import(LLMProviderSelector.class)
public @interface EnableLLM {
    String provider() default "openai";
}
```
1. **ImportBeanDefinitionRegistrar**：最灵活，可以直接操作 `BeanDefinitionRegistry`，动态注册任意 BeanDefinition（MyBatis 的 `@MapperScan` 就是这种方式）。

```java
public class ToolRegistrar implements ImportBeanDefinitionRegistrar {

    @Override
    public void registerBeanDefinitions(AnnotationMetadata metadata,
                                        BeanDefinitionRegistry registry) {
        // 扫描所有 @Tool 注解的类，动态注册为 Bean
        ClassPathScanningCandidateComponentProvider scanner =
            new ClassPathScanningCandidateComponentProvider(false);
        scanner.addIncludeFilter(new AnnotationTypeFilter(Tool.class));

        for (BeanDefinition bd : scanner.findCandidateComponents("com.example.tools")) {
            registry.registerBeanDefinition(bd.getBeanClassName(), bd);
        }
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
结构性
</td>
<td>
只说了&quot;导入配置类&quot;
</td>
<td>
三种用法递进，覆盖静态/动态/注册三个层次
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ImportSelector
</td>
<td>
清楚 @EnableAutoConfiguration 的实现原理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有自定义 Selector
</td>
<td>
有 LLM Provider 动态选择的完整实现
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道 @Import 能导入
</td>
<td>
理解 Spring 扩展机制的完整层次
</td>
</tr>
</table>

---

#### 2、进阶题：DeferredImportSelector 和 ImportSelector 有什么区别？为什么自动装配要用 DeferredImportSelector？

**难度级别**：⭐⭐⭐（延迟导入、处理顺序、用户配置优先）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 执行时机对比
- 为什么自动装配必须用 DeferredImportSelector
- 分组机制（Group）

**2️⃣ Impressive Answer**
1. **执行时机对比**：

<table>
<tr>
<td>
特性
</td>
<td>
ImportSelector
</td>
<td>
DeferredImportSelector
</td>
</tr>
<tr>
<td>
执行时机
</td>
<td>
当前 <code>@Configuration</code> 类处理时立即执行
</td>
<td>
所有 <code>@Configuration</code> 类处理完后延迟执行
</td>
</tr>
<tr>
<td>
分组支持
</td>
<td>
不支持
</td>
<td>
支持 <code>getImportGroup()</code>，同组的 Selector 合并处理
</td>
</tr>
<tr>
<td>
典型用途
</td>
<td>
<code>@Enable*</code> 注解的简单导入
</td>
<td>
Spring Boot 自动装配
</td>
</tr>
</table>
1. **为什么自动装配必须用 DeferredImportSelector**：

```
用户配置类（@ComponentScan 扫描）
    ↓ 先处理
用户的 @Bean DataSource 注册到容器
    ↓
DeferredImportSelector 延迟执行
    ↓
DataSourceAutoConfiguration 处理
    ↓
@ConditionalOnMissingBean(DataSource.class) → 检测到已有 DataSource → 跳过
```

如果用 `ImportSelector`（立即执行），自动配置类会在用户配置类之前处理，`@ConditionalOnMissingBean` 检测不到用户的 Bean，导致自动配置的 Bean 和用户的 Bean 冲突。
1. **分组机制（Group）**：`DeferredImportSelector.Group` 允许多个 Selector 的结果合并排序，`AutoConfigurationImportSelector` 实现了 `AutoConfigurationGroup`，负责对所有自动配置类按 `@AutoConfigureOrder` 和 `@AutoConfigureBefore/After` 排序。

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
只说了&quot;延迟执行&quot;
</td>
<td>
执行时机对比 + 原因分析 + 分组机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道为什么要延迟
</td>
<td>
清楚延迟是保证用户配置优先的核心手段
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道 Group 机制
</td>
<td>
知道自动配置类的排序是通过 Group 实现的
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道结论
</td>
<td>
理解设计背后的工程权衡
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
Spring Boot 自动装配的完整链路？
</td>
<td>
@Import + DeferredImportSelector 是自动装配的核心
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@Enable* 注解的设计模式？
</td>
<td>
模块化开关的设计范式，底层都是 @Import
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：模块化开关的设计范式，底层都是 @Import，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
MyBatis 的 @MapperScan 原理？
</td>
<td>
ImportBeanDefinitionRegistrar 的典型应用
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.11 Spring Boot SPI 机制原理

#### 1、基础题：Spring Boot 的 SPI 机制是什么？spring.factories 是如何被加载的？

**难度级别**：⭐⭐⭐（SPI、SpringFactoriesLoader、类加载机制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- SpringFactoriesLoader 加载流程
- Boot 3.x 的改进
- spring.factories 支持的扩展点类型

**2️⃣ Impressive Answer**
1. **SPI 机制本质**：SPI（Service Provider Interface）是一种"接口在框架侧定义，实现在使用方提供"的扩展机制。Spring Boot 的 SPI 比 Java 原生 SPI（`ServiceLoader`）更强大，支持按接口类型分组加载。
1. `**SpringFactoriesLoader**` 加载流程：

```
SpringFactoriesLoader.loadFactoryNames(EnableAutoConfiguration.class, classLoader)
  ↓
扫描所有 jar 包中的 META-INF/spring.factories
  ↓
解析 Properties 文件，按 key（接口全限定名）分组
  ↓
返回对应 key 下的所有实现类名列表
  ↓
通过反射实例化（loadInstantiatedFactories）
```
1. **缓存机制**：`SpringFactoriesLoader` 内部有 `cache`（`Map<ClassLoader, MultiValueMap<String, String>>`），同一个 ClassLoader 只解析一次，后续从缓存读取，避免重复 IO。
1. **Boot 3.x 的改进**：

```
# Boot 2.x：spring.factories（所有 key 都在一个文件，全量加载）
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
  com.example.FooAutoConfiguration,\
  com.example.BarAutoConfiguration

# Boot 3.x：独立文件（按需加载，只加载 AutoConfiguration）
# META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.FooAutoConfiguration
com.example.BarAutoConfiguration
```

Boot 3.x 的改进：不再把所有扩展点放在一个文件，避免加载不需要的扩展点，启动更快。
1. **spring.factories 支持的扩展点类型**：

<table>
<tr>
<td>
扩展点接口
</td>
<td>
作用
</td>
</tr>
<tr>
<td>
<code>EnableAutoConfiguration</code>
</td>
<td>
自动配置类注册
</td>
</tr>
<tr>
<td>
<code>ApplicationContextInitializer</code>
</td>
<td>
容器初始化扩展
</td>
</tr>
<tr>
<td>
<code>ApplicationListener</code>
</td>
<td>
应用事件监听
</td>
</tr>
<tr>
<td>
<code>SpringApplicationRunListener</code>
</td>
<td>
启动流程监听
</td>
</tr>
<tr>
<td>
<code>EnvironmentPostProcessor</code>
</td>
<td>
环境后处理
</td>
</tr>
<tr>
<td>
<code>FailureAnalyzer</code>
</td>
<td>
启动失败分析
</td>
</tr>
</table>

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
只说了&quot;读取文件加载类&quot;
</td>
<td>
加载流程 + 缓存机制 + Boot 3.x 改进 + 扩展点类型
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道缓存机制
</td>
<td>
清楚 ClassLoader 级别的缓存设计
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道 Boot 3.x 的变化
</td>
<td>
知道独立文件的性能优化原因
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道 spring.factories
</td>
<td>
理解 SPI 机制的完整设计
</td>
</tr>
</table>

---

#### 2、进阶题：如何利用 spring.factories 实现自己的扩展点？EnvironmentPostProcessor 的使用场景？

**难度级别**：⭐⭐⭐（EnvironmentPostProcessor、自定义扩展点、配置加密）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- EnvironmentPostProcessor 典型场景——配置解密
- 注册方式
- 执行时机
- 不能注入 Bean
- Agent 场景

**2️⃣ Impressive Answer**
1. **EnvironmentPostProcessor 典型场景——配置解密**：

```java
public class EncryptedPropertyDecryptor implements EnvironmentPostProcessor {

    private static final String ENCRYPTED_PREFIX = "ENC(";

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment,
                                       SpringApplication application) {
        MutablePropertySources sources = environment.getPropertySources();

        // 遍历所有 PropertySource，解密 ENC(...) 格式的配置值
        Map<String, Object> decryptedProperties = new HashMap<>();
        for (PropertySource<?> source : sources) {
            if (source instanceof MapPropertySource mapSource) {
                mapSource.getSource().forEach((key, value) -> {
                    if (value instanceof String strValue
                            && strValue.startsWith(ENCRYPTED_PREFIX)) {
                        String encrypted = strValue.substring(4, strValue.length() - 1);
                        decryptedProperties.put(key, decrypt(encrypted));
                    }
                });
            }
        }

        if (!decryptedProperties.isEmpty()) {
            // 插入到最高优先级，覆盖原始加密值
            sources.addFirst(new MapPropertySource("decrypted", decryptedProperties));
        }
    }

    private String decrypt(String encrypted) {
        // 调用 KMS 或本地密钥解密
        return AESUtil.decrypt(encrypted, getSecretKey());
    }
}
```
1. **注册方式**：

```properties
# META-INF/spring.factories（Boot 2.x）
org.springframework.boot.env.EnvironmentPostProcessor=\
  com.example.EncryptedPropertyDecryptor

# META-INF/spring/org.springframework.boot.env.EnvironmentPostProcessor.imports（Boot 3.x）
com.example.EncryptedPropertyDecryptor
```
1. **执行时机**：`EnvironmentPostProcessor` 在 `ApplicationEnvironmentPreparedEvent` 发布后执行，此时 `application.yml` 已加载，但 Spring 容器还未创建，**不能注入 Bean**。
1. **Agent 场景**：LLM API Key 在配置文件中加密存储（`ENC(xxx)`），通过 `EnvironmentPostProcessor` 在启动时解密，避免明文存储敏感信息。

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
只说了&quot;实现接口注册&quot;
</td>
<td>
完整实现 + 注册方式 + 执行时机限制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道不能注入 Bean
</td>
<td>
清楚容器未创建时的限制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有具体场景
</td>
<td>
有配置解密的生产级实现
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道扩展点存在
</td>
<td>
有安全配置的工程实践
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
Java 原生 SPI（ServiceLoader）和 Spring SPI 的区别？
</td>
<td>
SPI 机制的对比，Spring SPI 更灵活
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Spring Boot 自动装配的完整链路？
</td>
<td>
SPI 是自动装配的基础加载机制
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
配置中心（Nacos）如何集成到 Spring Boot？
</td>
<td>
EnvironmentPostProcessor 的典型应用场景
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.12 refreshContext 核心原理

#### 1、基础题：Spring 的 refresh() 方法做了哪些事？Bean 的生命周期是什么？

**难度级别**：⭐⭐⭐（refresh 流程、BeanPostProcessor、Bean 生命周期）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- refresh() 12 个核心步骤
- Bean 完整生命周期
- 最关键的两个步骤
- invokeBeanFactoryPostProcessors：ConfigurationClassPostProcessor 在这里解析 @Configuration、@Co...
- finishBeanFactoryInitialization：遍历所有非懒加载单例 BeanDefinition，依次实例化，这是启动最耗时的阶段。

**2️⃣ Impressive Answer**
1. `**refresh()**` 12 个核心步骤：

```
prepareRefresh()              → 设置启动时间、激活标志、初始化属性源
obtainFreshBeanFactory()      → 创建/刷新 BeanFactory，加载 BeanDefinition
prepareBeanFactory()          → 配置 BeanFactory（ClassLoader、BeanPostProcessor、内置 Bean）
postProcessBeanFactory()      → 子类扩展点（Web 容器注册 Servlet 相关 Bean）
invokeBeanFactoryPostProcessors() → 执行 BeanFactoryPostProcessor（@Configuration 解析、@ComponentScan 扫描）
registerBeanPostProcessors()  → 注册 BeanPostProcessor（AOP、@Autowired 注入等）
initMessageSource()           → 初始化国际化
initApplicationEventMulticaster() → 初始化事件广播器
onRefresh()                   → 子类扩展（Web 容器：创建并启动内嵌 Tomcat）
registerListeners()           → 注册 ApplicationListener
finishBeanFactoryInitialization() → 实例化所有非懒加载的单例 Bean（最耗时）
finishRefresh()               → 发布 ContextRefreshedEvent，启动 Lifecycle Bean
```
1. **Bean 完整生命周期**：

```
实例化（Constructor）
  ↓
属性注入（@Autowired、@Value）
  ↓
Aware 接口回调（BeanNameAware、ApplicationContextAware 等）
  ↓
BeanPostProcessor.postProcessBeforeInitialization()  ← AOP 代理在这里创建
  ↓
@PostConstruct / InitializingBean.afterPropertiesSet() / init-method
  ↓
BeanPostProcessor.postProcessAfterInitialization()
  ↓
Bean 就绪，放入单例缓存（singletonObjects）
  ↓
使用阶段
  ↓
@PreDestroy / DisposableBean.destroy() / destroy-method
```
1. **最关键的两个步骤**：
  - `invokeBeanFactoryPostProcessors`：`ConfigurationClassPostProcessor` 在这里解析 `@Configuration`、`@ComponentScan`、`@Import`、`@Bean`，注册所有 BeanDefinition。
  - `finishBeanFactoryInitialization`：遍历所有非懒加载单例 BeanDefinition，依次实例化，这是启动最耗时的阶段。

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
只说了&quot;扫描、实例化、注入&quot;
</td>
<td>
12 步完整流程 + Bean 生命周期完整链路
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 BeanFactoryPostProcessor
</td>
<td>
清楚 ConfigurationClassPostProcessor 的核心作用
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道哪步最耗时
</td>
<td>
知道 finishBeanFactoryInitialization 是性能瓶颈
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过生命周期
</td>
<td>
理解 refresh 流程的完整机制
</td>
</tr>
</table>

---

#### 2、进阶题：BeanPostProcessor 和 BeanFactoryPostProcessor 有什么区别？各自的典型应用是什么？

**难度级别**：⭐⭐⭐（后处理器、AOP 代理、@Autowired 注入原理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 核心区别
- 典型应用分析
- AOP 代理创建时机
- 替换容器中的原始 Bean

**2️⃣ Impressive Answer**
1. **核心区别**：

<table>
<tr>
<td>
维度
</td>
<td>
BeanFactoryPostProcessor
</td>
<td>
BeanPostProcessor
</td>
</tr>
<tr>
<td>
作用阶段
</td>
<td>
BeanDefinition 注册完成后，Bean 实例化之前
</td>
<td>
Bean 实例化之后，初始化前后
</td>
</tr>
<tr>
<td>
操作对象
</td>
<td>
<code>BeanDefinition</code>（元数据）
</td>
<td>
Bean 实例
</td>
</tr>
<tr>
<td>
典型实现
</td>
<td>
<code>ConfigurationClassPostProcessor</code>、<code>PropertySourcesPlaceholderConfigurer</code>
</td>
<td>
<code>AutowiredAnnotationBeanPostProcessor</code>、<code>AbstractAutoProxyCreator</code>
</td>
</tr>
<tr>
<td>
执行时机
</td>
<td>
<code>invokeBeanFactoryPostProcessors()</code>
</td>
<td>
<code>registerBeanPostProcessors()</code> 注册，Bean 初始化时调用
</td>
</tr>
</table>
1. **典型应用分析**：

```
BeanFactoryPostProcessor 典型应用：
├── ConfigurationClassPostProcessor
│   └── 解析 @Configuration、@ComponentScan、@Import、@Bean
│       注册所有 BeanDefinition（这是 Spring 最核心的后处理器）
└── PropertySourcesPlaceholderConfigurer
    └── 替换 BeanDefinition 中的 ${...} 占位符

BeanPostProcessor 典型应用：
├── AutowiredAnnotationBeanPostProcessor
│   └── 处理 @Autowired、@Value 注入（postProcessBeforeInitialization）
├── CommonAnnotationBeanPostProcessor
│   └── 处理 @PostConstruct、@PreDestroy、@Resource
└── AbstractAutoProxyCreator（AOP 核心）
    └── postProcessAfterInitialization 中判断是否需要代理
        如果需要，返回 CGLIB/JDK 动态代理对象替换原始 Bean
```
1. **AOP 代理创建时机**：`AbstractAutoProxyCreator.postProcessAfterInitialization()` 中，检查 Bean 是否匹配任何 Advisor（切面），如果匹配则创建代理对象，**替换容器中的原始 Bean**。这就是为什么 `@Transactional` 方法在同一个类内部调用不生效——内部调用绕过了代理。

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
只说了&quot;Bean 级别 vs BeanFactory 级别&quot;
</td>
<td>
完整对比表 + 典型实现树 + AOP 代理时机
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ConfigurationClassPostProcessor
</td>
<td>
清楚 Spring 最核心的后处理器是什么
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道 @Transactional 内部调用失效原因
</td>
<td>
能从代理创建时机解释这个经典问题
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道扩展点存在
</td>
<td>
理解 Spring 扩展机制的完整体系
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
Spring 的三级缓存解决循环依赖？
</td>
<td>
finishBeanFactoryInitialization 阶段的核心问题
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
@Transactional 为什么同类内部调用失效？
</td>
<td>
BeanPostProcessor 创建代理的机制决定的
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Spring AOP 的 CGLIB 和 JDK 动态代理区别？
</td>
<td>
AbstractAutoProxyCreator 选择代理方式的逻辑
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.13 外部化配置加载原理（ConfigData API）

#### 1、基础题：Spring Boot 的配置文件是如何被加载进来的？Boot 2.x 和 Boot 3.x 的加载机制有什么变化？

**⭐⭐**（ConfigFileApplicationListener、ConfigDataEnvironmentPostProcessor、PropertySource 加载时机）

**Answer：**

Spring Boot 配置加载的核心机制经历了从 Boot 2.x 到 Boot 3.x 的重大重构，主要体现在从 `ConfigFileApplicationListener` 到 ConfigData API 的演进。

**Boot 2.x 机制：**

使用 `ConfigFileApplicationListener` 监听器，在 `ApplicationContextInitializer` 阶段加载配置：
1. **监听器触发**：监听 `ApplicationEnvironmentPreparedEvent` 事件
1. **搜索配置文件**：按优先级搜索 `application.properties/yml`，支持 `file:./config/`、`file:./`、`classpath:/config/`、`classpath:/` 四个位置
1. **PropertySource 加载**：将解析后的配置添加到 `Environment` 的 `PropertySource` 链中
1. **Profile 激活**：根据 `spring.profiles.active` 激活特定 profile 的配置文件

**Boot 3.x 机制：**

引入全新的 ConfigData API，使用 `ConfigDataEnvironmentPostProcessor` 替代监听器模式：
1. **EnvironmentPostProcessor 触发**：在 Spring Boot 启动早期执行
1. **ConfigData 接口**：定义统一的配置数据抽象，支持多种配置源（文件、环境变量、云配置中心等）
1. **ConfigDataLocationResolver**：解析配置位置，返回 `ConfigDataResource`
1. **ConfigDataLoader**：加载具体的配置数据，转换为 `PropertySource`
1. **Import 链**：支持配置文件的嵌套导入（`spring.config.import`）

**核心差异对比：**

<table>
<tr>
<td>
维度
</td>
<td>
Boot 2.x
</td>
<td>
Boot 3.x
</td>
</tr>
<tr>
<td>
触发方式
</td>
<td>
事件监听器
</td>
<td>
EnvironmentPostProcessor
</td>
</tr>
<tr>
<td>
配置抽象
</td>
<td>
PropertySource
</td>
<td>
ConfigData + PropertySource
</td>
</tr>
<tr>
<td>
扩展性
</td>
<td>
继承监听器
</td>
<td>
实现 ConfigDataLocationResolver
</td>
</tr>
<tr>
<td>
导入支持
</td>
<td>
不支持配置导入
</td>
<td>
支持 spring.config.import
</td>
</tr>
</table>

---

#### 2、进阶题：Spring Boot 的配置加载优先级完整链路是什么？命令行参数、环境变量、application.yml、application-{profile}.yml 的优先级顺序？

**⭐⭐⭐**（PropertySource 优先级、Profile 激活时机、配置覆盖规则）

1️⃣ Common Answer

重点总结（便于面试记忆）：
- 一、完整的加载优先级链路（从高到低）
- 二、Profile 激活和配置覆盖规则
- 命令行参数
- 环境变量
- 配置文件
- 三、Agent 服务场景实战

2️⃣ Impressive Answer

Spring Boot 配置加载的优先级链路是一个多层 PropertySource 栈，理解其加载顺序对多环境部署和配置调试至关重要。我从加载时机、优先级规则和实战应用三个维度展开。

**一、完整的加载优先级链路（从高到低）**

```
优先级 1：命令行参数（Command Line Args）
  格式：--server.port=8080，PropertySource 名称：commandLineArgs

优先级 2：环境变量（Environment Variables）
  格式：SERVER_PORT=8080（自动转换），支持绑定到嵌套属性

优先级 3：JVM 系统属性（System Properties）
  格式：-Dserver.port=8080

优先级 4：随机数配置（random.*）
  示例：app.id=${random.value}

优先级 5：外部配置文件（Profile 特定）
  file:./config/application-{profile}.yml
  file:./application-{profile}.yml
  classpath:/config/application-{profile}.yml
  classpath:/application-{profile}.yml

优先级 6：外部配置文件（默认）
  file:./config/application.yml → classpath:/application.yml

优先级 7：@PropertySource 注解

优先级 8：默认属性（Default Properties）
  SpringApplication.setDefaultProperties()
```

**二、Profile 激活和配置覆盖规则**

Profile 的激活方式（优先级从高到低）：
1. **命令行参数**：`--spring.profiles.active=prod`
1. **环境变量**：`SPRING_PROFILES_ACTIVE=prod`
1. **配置文件**：`spring.profiles.active=prod`

覆盖规则：Profile 特定配置覆盖默认配置的同名属性，未定义的属性继承默认值，命令行参数始终最高优先级。

**三、Agent 服务场景实战**

```yaml
# application.yml（基础配置）
agent:
  model: "gpt-4"
  temperature: 0.7

# application-prod.yml（生产环境覆盖）
agent:
  timeout: 30000
  maxConcurrent: 10

# 启动命令（最高优先级，紧急调整）
java -jar agent-service.jar --spring.profiles.active=prod --agent.timeout=60000
```

调试技巧：通过 `--debug` 启动参数，Spring Boot 会打印完整的 `ConditionEvaluationReport` 和 PropertySource 栈。

3️⃣ Key Differences

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
优先级链路深度
</td>
<td>
仅列出 4-5 个层级
</td>
<td>
完整列出 8 个层级，包括随机数、@PropertySource
</td>
</tr>
<tr>
<td>
加载时机
</td>
<td>
未提及或模糊
</td>
<td>
明确说明在 SpringApplication.run() 极早期完成
</td>
</tr>
<tr>
<td>
Profile 激活方式
</td>
<td>
仅提及配置文件
</td>
<td>
列出 3 种激活方式及其优先级
</td>
</tr>
<tr>
<td>
实战场景
</td>
<td>
缺少具体案例
</td>
<td>
结合 Agent 服务场景，给出多环境配置示例
</td>
</tr>
<tr>
<td>
调试技巧
</td>
<td>
无
</td>
<td>
提供 --debug 启动参数调试方法
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
@ConfigurationProperties 和 @Value 的区别？
</td>
<td>
配置绑定的两种方式，和加载机制密切相关
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：配置绑定的两种方式，和加载机制密切相关，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何自定义配置源（从数据库加载配置）？
</td>
<td>
EnvironmentPostProcessor、ConfigData API 扩展点
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：EnvironmentPostProcessor、ConfigData API 扩展点，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring Boot 配置的松散绑定规则？
</td>
<td>
kebab-case、camelCase、snake_case 属性名转换
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
如何实现配置的动态刷新？
</td>
<td>
@RefreshScope、ContextRefresher、配置中心集成
</td>
<td>
答：PropertySource 优先级链（从高到低）；配置覆盖规则；@RefreshScope 动态刷新；动态刷新实现细节
</td>
</tr>
</table>

---

### 3.14 Profiles 机制

#### 1、基础题：Spring Boot 的 @Profile 和 spring.profiles.active 是如何工作的？Profile Groups 是什么？

**⭐⭐**（@Profile 注解、spring.profiles.active、spring.profiles.include、Profile Groups）

**Answer：**

**1. @Profile 注解的工作原理**

`@Profile` 可以标注在 `@Configuration`、`@Component`、`@Bean` 方法上，只有当指定的 Profile 处于激活状态时，对应的 Bean 才会被注册到容器中。底层通过 `@Conditional(ProfileCondition.class)` 实现。

```java
@Configuration
@Profile("dev")
public class DevConfig {
    @Bean
    public LlmClient devLlmClient() {
        return new OpenAiLlmClient("gpt-3.5-turbo"); // 开发环境用低成本模型
    }
}

@Configuration
@Profile("prod")
public class ProdConfig {
    @Bean
    public LlmClient prodLlmClient() {
        return new OpenAiLlmClient("gpt-4"); // 生产环境用高质量模型
    }
}
```

**2. Profile 激活方式（优先级从高到低）**

```bash
# 命令行参数（最高优先级）
java -jar app.jar --spring.profiles.active=prod

# 环境变量
export SPRING_PROFILES_ACTIVE=prod

# 配置文件
spring.profiles.active: dev

# 代码编程式激活
SpringApplication app = new SpringApplication(MyApplication.class);
app.setAdditionalProfiles("dev");
```

**3. spring.profiles.include**

`spring.profiles.include` 用于无条件激活指定的 Profile，适用于所有环境都需要的基础配置：

```yaml
spring:
  profiles:
    active: dev
    include: common,logging  # 无论激活哪个环境，都会加载这两个 Profile
```

**4. Profile Groups（Boot 2.4+）**

Profile Groups 允许将多个 Profile 组合成一个逻辑组，简化配置管理：

```yaml
spring:
  profiles:
    group:
      prod: "prod,db-prod,cache-prod"
      dev: "dev,db-dev,cache-dev"
```

激活 `prod` 时，会同时激活 `prod`、`db-prod`、`cache-prod` 三个 Profile，避免手动激活多个 Profile。

---

#### 2、进阶题：多环境配置管理的最佳实践是什么？如何在 Agent 服务中实现 dev/test/prod 三套环境的配置隔离？

**⭐⭐⭐**（application-{profile}.yml 加载机制、Profile 激活方式、配置中心集成）

1️⃣ Common Answer

重点总结（便于面试记忆）：
- 配置分层、环境隔离、配置中心集成、敏感信息保护
- 第一，采用配置分层架构，避免重复配置。
- 第二，容器化部署使用环境变量激活 Profile。
- 第三，集成配置中心实现动态配置。
- 第四，敏感信息使用密钥管理服务。

2️⃣ Impressive Answer

多环境配置管理的最佳实践需要从**配置分层、环境隔离、配置中心集成、敏感信息保护**四个维度系统设计。

**第一，采用配置分层架构，避免重复配置。**

基础配置放在 `application.yml`，所有环境共用；环境特定配置放在 `application-{profile}.yml`，只覆盖差异化部分。结合 Profile Groups 管理多组件配置：

```yaml
# application.yml - 基础配置
spring:
  application:
    name: agent-service
  profiles:
    group:
      dev: "dev,llm-dev,vector-dev"
      prod: "prod,llm-prod,vector-prod"

agent:
  max-concurrent-tasks: 100
  timeout-seconds: 300
```

```yaml
# application-dev.yml - 开发环境差异配置
agent:
  llm:
    model: gpt-4o-mini    # 降低成本
    api-key: ${LLM_API_KEY_DEV}
  vector:
    host: localhost
    collection: agent_dev
logging:
  level:
    com.example.agent: DEBUG
```

```yaml
# application-prod.yml - 生产环境差异配置
agent:
  llm:
    model: qwen-max       # 高质量模型
    api-key: ${LLM_API_KEY_PROD}
  vector:
    host: milvus-prod.internal
    collection: agent_prod
```

**第二，容器化部署使用环境变量激活 Profile。**

```bash
# Kubernetes ConfigMap
apiVersion: v1
kind: ConfigMap
data:
  SPRING_PROFILES_ACTIVE: "prod"
```

**第三，集成配置中心实现动态配置。**

对于 Agent 服务这类需要频繁调整参数的场景（如 LLM 温度、最大 Token 数），集成 Nacos 配置中心，通过 `@RefreshScope` 实现热更新，无需重启服务：

```java
@RestController
@RefreshScope
public class AgentController {
    @Value("${agent.llm.temperature}")
    private double temperature;
}
```

**第四，敏感信息使用密钥管理服务。**

LLM API Key、向量数据库密码等敏感信息绝不写入配置文件，通过环境变量或 Kubernetes Secret 注入：

```yaml
agent:
  llm:
    api-key: ${LLM_API_KEY}  # 从环境变量读取，不硬编码
```

3️⃣ Key Differences

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
配置分层
</td>
<td>
简单的文件分离
</td>
<td>
基础配置 + 环境特定 + Profile Groups 三层架构
</td>
</tr>
<tr>
<td>
激活方式
</td>
<td>
仅提到配置文件激活
</td>
<td>
环境变量优先，适配容器化部署场景
</td>
</tr>
<tr>
<td>
动态配置
</td>
<td>
未提及
</td>
<td>
集成 Nacos，通过 @RefreshScope 实现热更新
</td>
</tr>
<tr>
<td>
敏感信息
</td>
<td>
直接写在配置文件中
</td>
<td>
使用密钥管理服务，通过环境变量注入
</td>
</tr>
<tr>
<td>
Agent 场景
</td>
<td>
简单的环境区分
</td>
<td>
针对多组件（LLM、向量库）的 Profile Groups 设计
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
Spring Boot 配置文件的加载优先级是什么？
</td>
<td>
配置文件加载顺序、覆盖机制
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@ConditionalOnProfile 和 @Profile 的区别？
</td>
<td>
条件注解的使用场景
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：条件注解的使用场景，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何实现配置的动态刷新？
</td>
<td>
@RefreshScope、配置中心集成
</td>
<td>
答：PropertySource 优先级链（从高到低）；配置覆盖规则；@RefreshScope 动态刷新；动态刷新实现细节
</td>
</tr>
<tr>
<td>
在 Kubernetes 中如何管理 Spring Boot 的环境配置？
</td>
<td>
ConfigMap、Secret、环境变量注入
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.15 多模块 Starter 工程实践

#### 1、基础题：自定义 Spring Boot Starter 的标准目录结构和命名规范是什么？spring-boot-autoconfigure 和 spring-boot-starter 模块如何分工？

**⭐⭐**（Starter 命名规范、autoconfigure 模块职责、AutoConfiguration.imports 注册）

**Answer：**

Spring Boot Starter 的标准命名规范为 `xxx-spring-boot-starter`（如 `llm-client-spring-boot-starter`），官方 Starter 则以 `spring-boot-starter-xxx` 命名。

**标准多模块结构：**

```
llm-client-spring-boot-starter/
├── llm-client-spring-boot-autoconfigure/   # 自动配置模块
│   ├── src/main/java/
│   │   └── com/example/llm/autoconfigure/
│   │       ├── LlmClientAutoConfiguration.java
│   │       └── LlmClientProperties.java
│   └── src/main/resources/META-INF/spring/
│       └── org.springframework.boot.autoconfigure.AutoConfiguration.imports
└── llm-client-spring-boot-starter/         # 启动器模块（仅 pom.xml）
    └── pom.xml
```

**模块分工：**
- `**autoconfigure**` 模块：包含所有自动配置逻辑（`@Configuration` 类）、配置属性类（`@ConfigurationProperties`）、核心功能组件，通过 `AutoConfiguration.imports`（Boot 2.7+）或 `spring.factories`（旧版本）注册
- `**starter**` 模块：仅包含 `pom.xml`，声明对 `autoconfigure` 模块和实际依赖库的依赖，提供"一个依赖引入所有功能"的体验

**注册方式：**

```properties
# META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports（Boot 2.7+）
com.example.llm.autoconfigure.LlmClientAutoConfiguration
```

---

#### 2、进阶题：如何设计一个生产级的 LLM Client Starter？需要考虑哪些工程实践问题？

**⭐⭐⭐**（条件注解、@ConfigurationProperties、HealthIndicator、MeterRegistry、优雅降级）

1️⃣ Common Answer

重点总结（便于面试记忆）：
- 稳定性、可观测性、可扩展性
- 第一，智能化的条件装配与配置管理。
- 第二，可观测性建设（健康检查 + 指标）。
- 第三，优雅降级与容错机制。
- 第四，扩展性设计（拦截器机制）。
- 开箱即用

2️⃣ Impressive Answer

设计生产级 LLM Client Starter 需要从**稳定性、可观测性、可扩展性**三个维度系统考虑，我从以下四个方面展开。

**第一，智能化的条件装配与配置管理。**

使用多级条件注解实现灵活装配，配置属性类加 JSR-303 校验：

```java
@Configuration
@ConditionalOnClass({LlmClient.class, OpenAiApi.class})
@EnableConfigurationProperties(LlmClientProperties.class)
@AutoConfigureBefore(WebMvcAutoConfiguration.class)
public class LlmClientAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(prefix = "llm.client", name = "enabled", havingValue = "true", matchIfMissing = true)
    public LlmClient llmClient(LlmClientProperties properties,
                               ObjectProvider<List<LlmClientInterceptor>> interceptorsProvider) {
        OpenAiLlmClient client = new OpenAiLlmClient(properties);
        client.setInterceptors(interceptorsProvider.getIfAvailable());
        return client;
    }
}
```

```java
@ConfigurationProperties(prefix = "llm.client")
@Validated
public class LlmClientProperties {

    @NotBlank
    private String apiKey;

    @NotBlank
    private String model = "gpt-3.5-turbo";

    @Min(1000) @Max(120000)
    private Duration timeout = Duration.ofSeconds(30);

    @Min(1) @Max(10)
    private Integer maxRetries = 3;
}
```

**第二，可观测性建设（健康检查 + 指标）。**

实现深度健康检查，不仅检测连通性，还检测配额和限流状态：

```java
public class LlmClientHealthIndicator implements HealthIndicator {

    @Override
    public Health health() {
        try {
            LlmModelsResponse response = client.listModels();
            return Health.up()
                .withDetail("model", properties.getModel())
                .withDetail("quota", response.getQuota())
                .build();
        } catch (RateLimitException e) {
            return Health.down()
                .withDetail("error", "Rate limit exceeded")
                .withDetail("retryAfter", e.getRetryAfter())
                .build();
        }
    }
}
```

指标暴露涵盖请求耗时、Token 消耗、成功率：

```java
Timer.builder("llm.client.request.duration")
    .tag("model", client.getModel())
    .register(registry);

Counter.builder("llm.client.tokens.used")
    .tag("type", "prompt")
    .register(registry);
```

**第三，优雅降级与容错机制。**

使用 Resilience4j 实现熔断、重试，当熔断器打开时返回缓存结果：

```java
@Bean
public LlmClient resilientLlmClient(LlmClient delegate, LlmClientProperties properties) {
    CircuitBreakerConfig config = CircuitBreakerConfig.custom()
        .failureRateThreshold(50)
        .waitDurationInOpenState(Duration.ofSeconds(30))
        .build();

    RetryConfig retryConfig = RetryConfig.custom()
        .maxAttempts(properties.getMaxRetries())
        .retryOnException(e -> e instanceof TimeoutException || e instanceof RateLimitException)
        .build();

    return new ResilientLlmClient(delegate,
        CircuitBreaker.of("llmClient", config),
        Retry.of("llmClient", retryConfig));
}
```

**第四，扩展性设计（拦截器机制）。**

提供拦截器 SPI，支持自定义请求/响应处理（日志、签名、脱敏等）：

```java
public interface LlmClientInterceptor {
    default LlmRequest beforeRequest(LlmRequest request) { return request; }
    default LlmResponse afterResponse(LlmRequest request, LlmResponse response) { return response; }
    default void onError(LlmRequest request, Exception e) {}
}
```

**总结：** 生产级 Starter 设计的核心是**开箱即用**与**生产就绪**的平衡。通过条件装配实现按需加载，通过健康检查和指标实现可观测性，通过熔断降级保障稳定性，通过拦截器机制提供扩展性。

3️⃣ Key Differences

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
条件装配
</td>
<td>
仅用 @ConditionalOnMissingBean
</td>
<td>
多级条件注解，避免不必要的 Bean 创建
</td>
</tr>
<tr>
<td>
配置管理
</td>
<td>
简单的属性绑定
</td>
<td>
JSR-303 校验 + spring-configuration-metadata.json IDE 提示
</td>
</tr>
<tr>
<td>
健康检查
</td>
<td>
仅检测连通性
</td>
<td>
深度检查：连通性 + 配额 + 限流状态
</td>
</tr>
<tr>
<td>
指标暴露
</td>
<td>
仅记录请求耗时
</td>
<td>
多维度：耗时、Token 消耗、成功率，支持 Prometheus 集成
</td>
</tr>
<tr>
<td>
容错机制
</td>
<td>
简单异常处理
</td>
<td>
Resilience4j 熔断、降级、重试，提供缓存降级策略
</td>
</tr>
<tr>
<td>
扩展性
</td>
<td>
无扩展机制
</td>
<td>
拦截器 SPI，支持日志、签名、脱敏等自定义处理
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
Spring Boot 自动配置原理？@EnableAutoConfiguration 如何工作？
</td>
<td>
Starter 的核心依赖机制
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
如何排除某个自动配置类？
</td>
<td>
@SpringBootApplication(exclude)、spring.autoconfigure.exclude
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@ConditionalOnMissingBean 和 @ConditionalOnBean 的区别？
</td>
<td>
前者：Bean 不存在时生效；后者：Bean 存在时生效
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@AutoConfiguration 和 @Configuration 的区别？
</td>
<td>
Boot 2.7+ 新注解，支持 before/after 控制顺序
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：Boot 2.7+ 新注解，支持 before/after 控制顺序，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何调试自动配置的加载过程？
</td>
<td>
--debug 启动参数、ConditionEvaluationReport
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：--debug 启动参数、ConditionEvaluationReport，最后补一个风险点或优化手段。
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| Spring Boot 自动装配的原理是什么？@SpringBootApplication 做了什么？ | EnableAutoConfiguration 通过 @Import(AutoConfigurationImportSelector.class) 触发；AutoConfigurationImportSelector 实现了 DeferredImportSelector，在所有 @Configuration 类处理完后才执行（保证用户配置优先）；读取 META-INF/spring.factories（Boot 2.x）或 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports（Boot 3.x）中注册的自动配置类；每个自动配置类通过条件注解决定是否生效。 |
| 如何自定义一个 Spring Boot Starter？ | 三个核心步骤：① 写 XxxAutoConfiguration 类，用 @Configuration + @ConditionalOnMissingBean 定义默认 Bean；② 用 @ConfigurationProperties 绑定配置项（prefix = "xxx"），支持 application.yml 自定义；③ 在 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports（Boot 3.x）或 spring.factories（Boot 2.x）中注册；条件注解是关键：@ConditionalOnClass 保证依赖存在时才生效 |
| Spring Boot 的配置加载优先级？多环境配置如何管理？ | 命令行参数（--server.port=8081）；Java 系统属性（-Dserver.port=8081）；系统环境变量（SERVER_PORT=8081）；application-{profile}.yml（激活的 Profile 配置）；application.yml（默认配置）。 |
| Spring Boot 内嵌容器与启动流程 | 推断应用类型（Servlet / Reactive / None）；通过 SPI 加载 ApplicationContextInitializer 和 ApplicationListener；推断主配置类（包含 main 方法的类）。 |
| Spring Boot 的启动流程是什么？SpringApplication.run() 内部做了哪些事？ | 推断应用类型（Servlet / Reactive / None）；通过 SPI 加载 ApplicationContextInitializer 和 ApplicationListener；推断主配置类（包含 main 方法的类）。 |
| Spring Boot 内嵌 Tomcat 的启动原理？如何切换为 Undertow/Jetty？ | IO 模型上，Tomcat是NIO，Undertow是XNIO（IO/Worker 线程分离）；长连接上，Tomcat是一般，Undertow是优秀（适合 SSE）；生态上，Tomcat是最成熟，Undertow是较新；内存占用上，Tomcat是较高，Undertow是较低。 |
| Agent 服务需要支持高并发 SSE 长连接，如何调优内嵌容器参数？ | 高并发 SSE 要调大 Tomcat 最大线程、最小空闲线程、最大连接数、accept 队列和连接超时，同时评估是否切到 Undertow/WebFlux；更关键的是避免业务线程被 LLM 调用长期占用，并做好限流、心跳和断线清理。 |
| Spring Boot 的优雅停机（Graceful Shutdown）如何配置？ | 停止接受新请求（Tomcat/Undertow 拒绝新连接）；等待进行中的请求完成（最多等待 timeout-per-shutdown-phase）；销毁 Bean（调用 @PreDestroy、DisposableBean.destroy()）；timeout-per-shutdown-phase：每个阶段的最大等待时间（默认 30s）；超时后强制停机，未完成的请求会被中断。 |
| 优雅停机的底层原理是什么？SmartLifecycle、ContextClosedEvent、ShutdownHook 各自的角色？ | JVM 收到 SIGTERM 信号（kill 命令）；触发 Shutdown Hook（Spring 注册的）；调用 ConfigurableApplicationContext.close()；发布 ContextClosedEvent；停止 Web 容器（拒绝新请求）。 |
| Agent 服务发布时有正在进行的 SSE 长连接和 LLM 调用，如何实现无损下线？ | K8s 发送 SIGTERM；ReadinessProbe 返回 false，摘流；PreStop 调用停机端点；等待进行中的请求完成（SSE、LLM 调用）。 |
| Actuator 可观测性 | health：健康检查（/actuator/health）；metrics：指标监控（/actuator/metrics）；info：应用信息（/actuator/info）；env：环境变量（/actuator/env）；loggers：日志级别管理（/actuator/loggers）。 |
| Spring Boot Actuator 有哪些常用的 Endpoint？如何保护敏感 Endpoint？ | health：健康检查（/actuator/health）；metrics：指标监控（/actuator/metrics）；info：应用信息（/actuator/info）；env：环境变量（/actuator/env）；loggers：日志级别管理（/actuator/loggers）。 |
| @SpringBootTest 和 @WebMvcTest 有什么区别？各自适用什么场景？ | 启动完整容器：加载整个应用上下文（包括 Controller、Service、Repository 等）；：端到端测试、集成测试、需要测试多个组件协作的场景；缺点：启动慢，依赖真实的外部服务（数据库、Redis 等）；Slice 测试：只加载 Web 层（Controller、ControllerAdvice、Filter 等），不加载 Service 和 Repository；自动 Mock：Service 层的 Bean 自动被 Mock，需要用 @MockBean 模拟行为。 |
| Spring Boot 测试的 Slice 测试（@DataJpaTest、@WebMvcTest 等）是如何实现的？如何 Mock 外部依赖？ | 通过 @BootstrapWith 指定自定义的 TestContextBootstrapper；TestContextBootstrapper 根据 @TestConfiguration 和 @Import 过滤 BeanDefinition，只加载特定层的 Bean；例如 @WebMvcTest 只加载 @Controller、@ControllerAdvice、@Filter 等注解的 Bean |
| @Conditional 家族注解有哪些？各自的使用场景是什么？ | ConditionalOnClass：类路径上存在指定类时生效（如 @ConditionalOnClass(Tomcat.class)） |
| @ConditionalOnMissingBean 的判断时机是什么？为什么用户自定义的 Bean 能覆盖自动配置？ | AutoConfigurationImportSelector 实现了 DeferredImportSelector，延迟到所有 @Configuration 类处理完之后才执行；用户的 @Configuration 类（通过 @ComponentScan 扫描）先于自动配置类处理；因此用户的 Bean 先注册到容器，自动配置类执行时 @ConditionalOnMissingBean 检查到已有 Bean，跳过创建 |
| @ConfigurationProperties 和 @Value 有什么区别？各自适用什么场景？ | Value 适合注入单个配置并支持 SpEL，但不支持松散绑定和类型安全校验，配置错误通常到运行时才暴露 |
| Spring Boot 的 Environment 抽象是什么？PropertySource 的优先级如何工作？ | Environment 接口：提供 getProperty()、containsProperty()、getActiveProfiles() 等方法；ConfigurableEnvironment：可以添加/删除 PropertySource，获取 MutablePropertySources；StandardEnvironment：非 Web 环境，包含系统属性和环境变量两个 PropertySource；StandardServletEnvironment：Web 环境，额外包含 Servlet 配置和上下文参数。 |
| Spring Boot 事件机制 | ApplicationStartingEvent → SpringApplication.run() 刚开始，容器还未创建；ApplicationEnvironmentPreparedEvent → Environment 准备完成，配置已加载；ApplicationContextInitializedEvent → ApplicationContext 创建完成，Initializer 执行完。 |
| Spring Boot 有哪些内置的应用事件？发布顺序是什么？ | ApplicationStartingEvent → SpringApplication.run() 刚开始，容器还未创建；ApplicationEnvironmentPreparedEvent → Environment 准备完成，配置已加载；ApplicationContextInitializedEvent → ApplicationContext 创建完成，Initializer 执行完。 |
| ApplicationRunner 和 CommandLineRunner 有什么区别？执行时机是什么？ | ApplicationRunner 和 CommandLineRunner 都在 Spring Boot 启动完成、ApplicationContext 就绪后执行，区别是 ApplicationRunner 接收解析后的 ApplicationArguments，适合读取 option/non-option 参数，CommandLineRunner 接收原始 String[]，适合简单命令行参数处理。 |
| Spring Boot 3.x 相比 2.x 有哪些重要变化？ | Java 17 基线：不再支持 Java 8/11，可以使用 Record、Sealed Class、Pattern Matching 等新特性；Jakarta EE 10：所有 javax.* 包迁移到 jakarta.*（如 javax.servlet → jakarta.servlet），这是最大的迁移成本；Spring Framework 6.x：底层框架同步升级；废弃 spring.factories 的 EnableAutoConfiguration 入口；迁移到 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports。 |
| Spring Boot 3.x 的 AOT 编译和 GraalVM 原生镜像是什么？有什么优缺点？ | JIT（Just-In-Time）：运行时编译，启动慢（需要 JVM 预热），但长期运行性能好；AOT（Ahead-of-Time）：构建时编译，启动极快（毫秒级），内存占用低，但失去 JIT 优化；适合：Serverless 函数、CLI 工具、冷启动敏感的场景（如 K8s 快速扩容）；不适合：需要动态加载类、大量反射的 Agent 框架（如 LangChain4J 的动态代理）。 |
| Agent 服务需要快速冷启动（K8s 弹性扩容），如何用 Spring Boot 3.x 优化启动时间？ | 无优化：5-10s：开发环境；懒加载：2-4s：生产环境（简单）；排除自动配置：1-3s：生产环境（精细化）；AOT 编译（JVM）：1-2s：生产环境（推荐）；GraalVM 原生镜像：50-200ms：Serverless/弹性扩容。 |
| Spring Boot 启动优化与性能调优 | 类路径扫描范围过大：@ComponentScan 扫描了不必要的包，包含大量第三方 jar；自动配置过多：加载了不需要的自动配置类（如引入了 spring-boot-starter-data-jpa 但不用数据库）；Bean 初始化耗时：某些 Bean 的 @PostConstruct 或构造函数有耗时操作（如建立连接、加载模型）；AOP 代理创建：大量 @Transactional、@Async 注解导致代理对象创建耗时；看 refreshContext 耗时（Bean 实例化阶段）。 |
| Spring Boot 应用启动慢的常见原因有哪些？如何排查？ | 类路径扫描范围过大：@ComponentScan 扫描了不必要的包，包含大量第三方 jar；自动配置过多：加载了不需要的自动配置类（如引入了 spring-boot-starter-data-jpa 但不用数据库）；Bean 初始化耗时：某些 Bean 的 @PostConstruct 或构造函数有耗时操作（如建立连接、加载模型）；AOP 代理创建：大量 @Transactional、@Async 注解导致代理对象创建耗时；看 refreshContext 耗时（Bean 实例化阶段）。 |
| Spring Boot DevTools 的热部署原理是什么？为什么生产环境要禁用？ | Base ClassLoader：加载不会变化的类（第三方 jar、Spring 框架本身）；Restart ClassLoader：加载开发者自己的类（classpath 下的 class 文件）；文件变化时，只丢弃并重建 Restart ClassLoader，Base ClassLoader 保留，因此比完整重启快得多；监听 classpath 下的文件变化（IDE 编译后触发）；默认排除静态资源（/static、/public、/templates）的变化，避免频繁重启。 |
| @Import 机制原理 | Import 有三种用法，复杂度递增：；直接导入配置类：最简单，等价于在当前配置类中声明那个类 |
| @Import 注解有哪几种用法？ | Import 有三种用法，复杂度递增：；直接导入配置类：最简单，等价于在当前配置类中声明那个类 |
| DeferredImportSelector 和 ImportSelector 有什么区别？为什么自动装配要用 DeferredImportSelector？ | 执行时机上，ImportSelector是当前 @Configuration 类处理时立即执行，DeferredImportSelector是所有 @Configuration 类处理完后延迟执行；分组支持上，ImportSelector是不支持，DeferredImportSelector是支持 getImportGroup()，同组的 Selector 合并处理；典型用途上，ImportSelector是@Enable* 注解的简单导入，DeferredImportSelector是Spring Boot 自动装配。 |
| Spring Boot SPI 机制原理 | EnableAutoConfiguration：自动配置类注册；ApplicationContextInitializer：容器初始化扩展；ApplicationListener：应用事件监听；SpringApplicationRunListener：启动流程监听；EnvironmentPostProcessor：环境后处理；FailureAnalyzer：启动失败分析。 |
| Spring Boot 的 SPI 机制是什么？spring.factories 是如何被加载的？ | EnableAutoConfiguration：自动配置类注册；ApplicationContextInitializer：容器初始化扩展；ApplicationListener：应用事件监听；SpringApplicationRunListener：启动流程监听；EnvironmentPostProcessor：环境后处理；FailureAnalyzer：启动失败分析。 |
| refreshContext 核心原理 | invokeBeanFactoryPostProcessors：ConfigurationClassPostProcessor 在这里解析 @Configuration、@ComponentScan、@Import、@Bean，注册所有 BeanDefinition；finishBeanFactoryInitialization：遍历所有非懒加载单例 BeanDefinition，依次实例化，这是启动最耗时的阶段；prepareRefresh() → 设置启动时间、激活标志、初始化属性源；obtainFreshBeanFactory() → 创建/刷新 BeanFactory，加载 BeanDefinition。 |
| Spring 的 refresh() 方法做了哪些事？Bean 的生命周期是什么？ | invokeBeanFactoryPostProcessors：ConfigurationClassPostProcessor 在这里解析 @Configuration、@ComponentScan、@Import、@Bean，注册所有 BeanDefinition；finishBeanFactoryInitialization：遍历所有非懒加载单例 BeanDefinition，依次实例化，这是启动最耗时的阶段；prepareRefresh() → 设置启动时间、激活标志、初始化属性源；obtainFreshBeanFactory() → 创建/刷新 BeanFactory，加载 BeanDefinition。 |
| BeanPostProcessor 和 BeanFactoryPostProcessor 有什么区别？各自的典型应用是什么？ | BeanFactoryPostProcessor 在 Bean 实例化前修改 BeanDefinition，适合改元数据和属性定义；BeanPostProcessor 在 Bean 实例化后、初始化前后增强 Bean 实例，AOP、代理包装、初始化增强通常依赖它。 |
| 外部化配置加载原理（ConfigData API） | Spring Boot 配置加载的优先级链路是一个多层 PropertySource 栈，理解其加载顺序对多环境部署和配置调试至关重要。我从加载时机、优先级规则和实战应用三个维度展开；优先级 1：命令行参数（Command Line Args）；格式：--server.port=8080，PropertySource 名称：commandLineArgs。 |
| Spring Boot 的配置文件是如何被加载进来的？Boot 2.x 和 Boot 3.x 的加载机制有什么变化？ | 触发方式上，Boot 2.x是事件监听器，Boot 3.x是EnvironmentPostProcessor；配置抽象上，Boot 2.x是PropertySource，Boot 3.x是ConfigData + PropertySource；扩展性上，Boot 2.x是继承监听器，Boot 3.x是实现 ConfigDataLocationResolver；导入支持上，Boot 2.x是不支持配置导入，Boot 3.x是支持 spring.config.import。 |
| Spring Boot 的配置加载优先级完整链路是什么？命令行参数、环境变量、application.yml、application-{profile}.yml 的优先级顺序？ | Spring Boot 配置加载的优先级链路是一个多层 PropertySource 栈，理解其加载顺序对多环境部署和配置调试至关重要。我从加载时机、优先级规则和实战应用三个维度展开；优先级 1：命令行参数（Command Line Args）；格式：--server.port=8080，PropertySource 名称：commandLineArgs。 |
| Profiles 机制 | 多环境配置管理的最佳实践需要从配置分层、环境隔离、配置中心集成、敏感信息保护四个维度系统设计；基础配置放在 application.yml，所有环境共用；环境特定配置放在 application-{profile}.yml，只覆盖差异化部分。结合 Profile Groups 管理多组件配置：；dev: "dev,llm-dev,vector-dev"。 |
| Spring Boot 的 @Profile 和 spring.profiles.active 是如何工作的？Profile Groups 是什么？ | Profile 可以标注在 @Configuration、@Component、@Bean 方法上，只有当指定的 Profile 处于激活状态时，对应的 Bean 才会被注册到容器中。底层通过 @Conditional(ProfileCondition.class) 实现；Profile 激活方式（优先级从高到低）；spring.profiles.include。 |
| 多环境配置管理的最佳实践是什么？如何在 Agent 服务中实现 dev/test/prod 三套环境的配置隔离？ | 多环境配置管理的最佳实践需要从配置分层、环境隔离、配置中心集成、敏感信息保护四个维度系统设计；基础配置放在 application.yml，所有环境共用；环境特定配置放在 application-{profile}.yml，只覆盖差异化部分。结合 Profile Groups 管理多组件配置：；dev: "dev,llm-dev,vector-dev"。 |
| 多模块 Starter 工程实践 | 生产级 LLM Client Starter 要分 starter 和 autoconfigure 两层：starter 只声明依赖，autoconfigure 提供条件装配、配置属性、客户端 Bean、重试限流、监控指标和健康检查；设计重点是可插拔、可观测、配置校验和默认值安全。 |
| 自定义 Spring Boot Starter 的标准目录结构和命名规范是什么？spring-boot-autoconfigure 和 spring-boot-starter 模块如何分工？ | autoconfigure 模块：包含所有自动配置逻辑（@Configuration 类）、配置属性类（@ConfigurationProperties）、核心功能组件，通过 AutoConfiguration.imports（Boot 2.7+）或 spring.factories（旧版本）注册；starter 模块：仅包含 pom.xml，声明对 autoconfigure 模块和实际依赖库的依赖，提供"一个依赖引入所有功能"的体验；Spring Boot Starter 的标准命名规范为 xxx-spring-boot-starter（如 llm-client-spring-boot-starter），官方 Starter 则以 spring-boot-starter-xxx 命名。 |
| 如何设计一个生产级的 LLM Client Starter？需要考虑哪些工程实践问题？ | 生产级 LLM Client Starter 要分 starter 和 autoconfigure 两层：starter 只声明依赖，autoconfigure 提供条件装配、配置属性、客户端 Bean、重试限流、监控指标和健康检查；设计重点是可插拔、可观测、配置校验和默认值安全。 |
