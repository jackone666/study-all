# Spring Boot 与自动装配

### 1、基础题：Spring Boot 自动装配的原理是什么？@SpringBootApplication 做了什么？

**难度级别**：⭐⭐（@EnableAutoConfiguration、spring.factories/spring/imports、条件注解）

**1️⃣ Common Answer**

@SpringBootApplication 是一个组合注解，包含了 @Configuration、@EnableAutoConfiguration 和 @ComponentScan。自动装配就是 Spring Boot 自动帮你配置好各种 Bean，不用手动写 XML 了。它会读取 spring.factories 文件来加载配置类。

**2️⃣ Impressive Answer**

1. **@SpringBootApplication 三合一**：`@Configuration`（声明配置类）+ `@EnableAutoConfiguration`（开启自动装配）+ `@ComponentScan`（扫描当前包及子包）。

2. **自动装配完整链路**：

  - `@EnableAutoConfiguration` 通过 `@Import(AutoConfigurationImportSelector.class)` 触发。

  - `AutoConfigurationImportSelector` 实现了 `DeferredImportSelector`，在所有 `@Configuration` 类处理完后才执行（保证用户配置优先）。

  - 读取 `META-INF/spring.factories`（Boot 2.x）或 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Boot 3.x）中注册的自动配置类。

  - 每个自动配置类通过**条件注解**决定是否生效。

3. **条件注解是核心**：`@ConditionalOnClass`（类路径存在才生效）、`@ConditionalOnMissingBean`（用户没自定义才生效）、`@ConditionalOnProperty`（配置开关控制）。这保证了"约定优于配置"——有默认值，但用户可以覆盖。

4. **版本差异**：Spring Boot 3.x 废弃了 `spring.factories` 的自动装配入口，迁移到 `.imports` 文件，加载更高效（不再加载所有 key，只加载 AutoConfiguration）。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"三个注解组合" | 完整链路：注解→ImportSelector→文件→条件注解 |
| 技术深度 | 不知道 DeferredImportSelector 的作用 | 清楚延迟导入保证用户配置优先 |
| 实践经验 | 不知道 Boot 3.x 的变化 | 知道两个版本的注册文件差异 |
| 面试官印象 | 背过概念但不深入 | 理解自动装配的设计意图和演进 |

---

### 2、进阶题：如何自定义一个 Spring Boot Starter？

**难度级别**：⭐⭐⭐（AutoConfiguration 类、@ConditionalOnMissingBean、META-INF 配置、属性绑定）

**1️⃣ Common Answer**

就是写一个配置类，然后在 META-INF 下面的 spring.factories 里面注册一下。用 @Bean 定义 Bean，加个 @Configuration 注解。如果用户想自己配置就用 @ConditionalOnMissingBean，这样不会冲突。

**2️⃣ Impressive Answer**

1. **三个核心步骤**：① 写 `XxxAutoConfiguration` 类，用 `@Configuration` + `@ConditionalOnMissingBean` 定义默认 Bean；② 用 `@ConfigurationProperties` 绑定配置项（prefix = "xxx"），支持 application.yml 自定义；③ 在 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Boot 3.x）或 `spring.factories`（Boot 2.x）中注册。

2. **条件注解是关键**：`@ConditionalOnClass` 保证依赖存在时才生效；`@ConditionalOnMissingBean` 让用户自定义 Bean 时自动退位；`@ConditionalOnProperty` 可以让用户通过配置开关控制是否启用。

3. **常见陷阱**：忘记加 `@EnableConfigurationProperties` 导致配置类不生效；Spring Boot 3.x 已废弃 spring.factories 的自动装配入口，必须迁移到新路径。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 步骤混乱，不知道先做什么 | 三步清晰：AutoConfig→属性绑定→注册 |
| 技术深度 | 不知道 Boot 3.x 路径变化 | 知道两个版本的注册文件差异 |
| 实践经验 | 不知道条件注解的具体用法 | 三个条件注解分场景说清楚 |
| 面试官印象 | 能写但不知道原理和兼容性 | 有版本意识，知道条件注解的设计意图 |

---

### 3、进阶题：Spring Boot 的配置加载优先级？多环境配置如何管理？

**难度级别**：⭐⭐⭐（PropertySource 优先级、Profile 机制、配置中心集成）

**1️⃣ Common Answer**

Spring Boot 的配置有优先级，命令行参数最高，然后是 application.yml。可以用 spring.profiles.active 来区分不同环境的配置，比如 dev、test、prod。也可以用 Nacos 做配置中心。

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

2. **Profile 机制**：`spring.profiles.active=dev` 激活 `application-dev.yml`；支持多 Profile 叠加（`dev,local`）；Spring Boot 2.4+ 支持 `spring.config.activate.on-profile` 在同一文件中按 `---` 分隔多环境配置。

3. **配置中心集成**：Nacos/Apollo 作为外部配置源，`bootstrap.yml` 优先于 `application.yml` 加载（用于配置中心连接信息）；支持动态刷新（`@RefreshScope`），无需重启。

4. **Agent 场景**：不同环境的 LLM API Key、模型参数（temperature、max_tokens）、工具启停配置通过 Profile + 配置中心管理，敏感信息（API Key）通过加密配置或 Vault 管理。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"命令行最高" | 完整优先级链，7 层从高到低 |
| 技术深度 | 不知道 bootstrap.yml 的作用 | 清楚配置中心的加载时机和动态刷新 |
| 实践经验 | 没有提到敏感信息管理 | 知道 API Key 加密和 Vault 方案 |
| 面试官印象 | 知道基本用法 | 有多环境配置的完整实践经验 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| @EnableAutoConfiguration 是如何加载 AutoConfiguration 的？ | Starter 的注册原理，考察 Spring Boot 自动装配的 SPI 机制 |
| @Conditional 家族注解有哪些？如何自定义 Condition？ | Starter 核心依赖的条件化装配能力，考察扩展能力 |
| Spring Boot 2.x 升级到 3.x 需要注意哪些自动装配的变化？ | 考察对版本迁移的实际工程经验 |

---

## 3.1 Spring Boot 内嵌容器与启动流程

### 1、基础题：Spring Boot 的启动流程是什么？SpringApplication.run() 内部做了哪些事？

**难度级别**：⭐⭐（SpringApplication 初始化、Environment 准备、ApplicationContext 创建、自动装配、内嵌容器启动）

**1️⃣ Common Answer**

SpringApplication.run() 就是启动 Spring Boot 应用的入口。它会创建 Spring 容器，加载配置，扫描 Bean，然后启动内嵌的 Tomcat。启动完成后会打印 Banner 和启动时间。

**2️⃣ Impressive Answer**

1. **SpringApplication 构造阶段**：

  - 推断应用类型（Servlet / Reactive / None）

  - 通过 SPI 加载 `ApplicationContextInitializer` 和 `ApplicationListener`

  - 推断主配置类（包含 `main` 方法的类）

2. **run() 执行流程**：

```plaintext
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

2. **实践注意**：`refreshContext` 是最耗时的阶段，包含了 Bean 扫描、实例化、AOP 代理创建、内嵌容器启动等所有核心逻辑。启动慢优化应重点关注这个阶段。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"创建容器、启动 Tomcat" | 完整流程 8 个步骤，每步都有对应机制 |
| 技术深度 | 不知道应用类型推断 | 清楚 Servlet/Reactive/None 三种类型 |
| 实践经验 | 没有提到扩展点 | 知道 Initializer、Runner、Listener 三大扩展点 |
| 面试官印象 | 知道入口但不知道内部 | 理解启动流程的完整链路和优化方向 |

---

### 2、进阶题：Spring Boot 内嵌 Tomcat 的启动原理？如何切换为 Undertow/Jetty？

**难度级别**：⭐⭐⭐（ServletWebServerFactory、自动装配条件、性能对比）

**1️⃣ Common Answer**

Spring Boot 内嵌了 Tomcat，不需要外部部署。如果想换成 Undertow，就把 spring-boot-starter-tomcat 排除掉，然后引入 spring-boot-starter-undertow。Undertow 性能好一些。

**2️⃣ Impressive Answer**

1. **内嵌 Tomcat 启动原理**：`ServletWebServerFactoryAutoConfiguration` 通过 `@ConditionalOnClass(Tomcat.class)` 判断类路径上有 Tomcat，自动注册 `TomcatServletWebServerFactory`。在 `refreshContext` 阶段，`ServletWebServerApplicationContext` 调用 `createWebServer()` 创建并启动内嵌容器。

2. **切换方式**：

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

| 维度 | Tomcat | Undertow | Jetty |
| --- | --- | --- | --- |
| IO 模型 | NIO | XNIO（IO/Worker 线程分离） | NIO |
| 长连接 | 一般 | **优秀**（适合 SSE） | 良好 |
| 生态 | 最成熟 | 较新 | 成熟 |
| 内存占用 | 较高 | **较低** | 中等 |

1. **Agent 场景**：SSE 流式输出是长连接，Undertow 的 XNIO 模型更适合——IO 线程只负责接收连接，Worker 线程处理业务，不会因为长连接占满线程池。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了排除依赖 | 原理→切换方式→性能对比→场景选型 |
| 技术深度 | 不知道自动装配的条件判断 | 清楚 @ConditionalOnClass 的工作机制 |
| 实践经验 | 只说"Undertow 性能好" | 有 IO 模型对比和 Agent 场景选型 |
| 面试官印象 | 会切换但不知道原理 | 理解自动装配和容器选型的工程权衡 |

---

### 3、场景题：Agent 服务需要支持高并发 SSE 长连接，如何调优内嵌容器参数？

**难度级别**：⭐⭐⭐（线程池配置、连接超时、NIO 配置、背压处理）

**1️⃣ Common Answer**

可以调大 Tomcat 的线程池，增加最大连接数。设置合理的超时时间，避免连接泄漏。如果并发很高可以考虑换成 Undertow。

**2️⃣ Impressive Answer**

1. **Tomcat 核心参数调优**：

  - `server.tomcat.threads.max=400`（默认 200，SSE 场景需增大）

  - `server.tomcat.threads.min-spare=50`（最小空闲线程）

  - `server.tomcat.max-connections=10000`（默认 8192，长连接场景需增大）

  - `server.tomcat.connection-timeout=60000`（连接超时）

  - `server.tomcat.accept-count=200`（等待队列长度）

2. **SSE 场景的特殊性**：每个 SSE 连接占用一个线程直到完成，200 个线程只能同时处理 200 个 SSE 请求。解决方案：① 增大线程池；② 切换 Undertow（IO/Worker 分离）；③ 使用 WebFlux 响应式方案。

3. **切换 Undertow 的优势配置**：

  - `server.undertow.io-threads=16`（IO 线程，通常等于 CPU 核数）

  - `server.undertow.worker-threads=256`（Worker 线程）

  - IO 线程只负责接收连接和读写数据，Worker 线程处理业务逻辑，长连接不会阻塞新连接的接入。

4. **监控与告警**：配合 Micrometer + Prometheus 暴露 `tomcat.threads.busy`、`tomcat.connections.current` 等指标；设置告警阈值（如线程使用率 > 80%），提前扩容。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"调大线程池" | 具体参数→SSE 特殊性→Undertow 方案→监控 |
| 技术深度 | 不知道 SSE 占线程的问题 | 清楚长连接对线程池的影响和解决方案 |
| 实践经验 | 没有具体参数值 | 有完整的参数配置和监控方案 |
| 面试官印象 | 知道要调优但不具体 | 有生产环境调优经验，考虑周全 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot Actuator 的健康检查和指标暴露？ | 生产环境监控，和容器调优配合使用 |
| Spring Boot 的优雅停机（Graceful Shutdown）如何实现？ | 长连接场景下的停机策略，避免 SSE 连接被强制断开 |
| Spring WebFlux vs Spring MVC 的选型？ | 响应式编程在高并发场景下的替代方案 |

---

## 3.2 优雅停机

### 1、基础题：Spring Boot 的优雅停机（Graceful Shutdown）如何配置？

**难度级别**：⭐⭐（配置方式、停机流程、超时控制）

**1️⃣ Common Answer**

可以在 application.yml 里配置 server.shutdown=graceful，然后设置 spring.lifecycle.timeout-per-shutdown-phase。这样停机的时候会等待请求处理完。

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

2. **超时控制**：

  - `timeout-per-shutdown-phase`：每个阶段的最大等待时间（默认 30s）。

  - 超时后强制停机，未完成的请求会被中断。

3. **版本要求**：Spring Boot 2.3+ 支持优雅停机，Undertow 支持更好（Tomcat 9.0.33+）。

4. **Agent 场景**：SSE 长连接、LLM 调用需要等待完成，避免强制中断导致数据不一致。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了配置 | 配置+停机流程+超时控制+版本要求 |
| 技术深度 | 不知道停机流程 | 清楚四个阶段的停机顺序 |
| 实践经验 | 没有提到版本要求 | 知道不同容器的支持差异 |
| 面试官印象 | 会配置 | 理解优雅停机的完整机制 |

---

### 2、进阶题：优雅停机的底层原理是什么？SmartLifecycle、ContextClosedEvent、ShutdownHook 各自的角色？

**难度级别**：⭐⭐⭐（停机原理、生命周期扩展、JVM Hook）

**1️⃣ Common Answer**

SmartLifecycle 是生命周期接口，可以控制 Bean 的停机顺序。ContextClosedEvent 是容器关闭事件，可以监听。ShutdownHook 是 JVM 的钩子，JVM 关闭时执行。

**2️⃣ Impressive Answer**

1. **底层原理**：

  - JVM 收到 SIGTERM 信号（kill 命令）

  - 触发 Shutdown Hook（Spring 注册的）

  - 调用 `ConfigurableApplicationContext.close()`

  - 发布 `ContextClosedEvent`

  - 停止 Web 容器（拒绝新请求）

  - 销毁 Bean（按 SmartLifecycle 顺序）

  - 关闭容器

2. **SmartLifecycle**：

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

2. **执行顺序**：ShutdownHook → ContextClosedEvent → SmartLifecycle.stop() → @PreDestroy。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了三个名字 | 底层原理+完整代码+执行顺序 |
| 技术深度 | 不知道 SmartLifecycle 的 phase | 清楚停机顺序控制机制 |
| 实践经验 | 没有代码示例 | 有完整的生命周期管理实现 |
| 面试官印象 | 背过概念 | 理解优雅停机的完整机制 |

---

### 3、场景题：Agent 服务发布时有正在进行的 SSE 长连接和 LLM 调用，如何实现无损下线？

**难度级别**：⭐⭐⭐（无损下线、长连接处理、健康检查）

**1️⃣ Common Answer**

配置优雅停机，设置合理的超时时间。SSE 连接会在超时时间内完成。LLM 调用可以用 @PreDestroy 等待完成。健康检查下线前先摘流。

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了配置 | 完整方案+K8s 配置+HealthIndicator+SmartLifecycle |
| 技术深度 | 不知道 K8s 探针机制 | 清楚 readinessProbe 和 terminationGracePeriodSeconds |
| 实践经验 | 没有下线流程 | 有完整的无损下线流程设计 |
| 面试官印象 | 会配置 | 有生产环境无损下线经验 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot Actuator 的健康检查如何实现？ | 无损下线依赖健康检查摘流 |
| Docker/K8s 的生命周期管理？ | 容器化部署的无损下线方案 |
| JVM 的 ShutdownHook 是什么？ | 优雅停机的底层机制 |

---

## 3.3 Actuator 可观测性

### 1、基础题：Spring Boot Actuator 有哪些常用的 Endpoint？如何保护敏感 Endpoint？

**难度级别**：⭐⭐（常用 Endpoint、安全配置、暴露策略）

**1️⃣ Common Answer**

Actuator 有 health、metrics、info、env 等端点。可以用 spring.security配置保护敏感端点，或者只暴露 health 和 info。

**2️⃣ Impressive Answer**

1. **常用 Endpoint**：

  - **health**：健康检查（`/actuator/health`）

  - **metrics**：指标监控（`/actuator/metrics`）

  - **info**：应用信息（`/actuator/info`）

  - **env**：环境变量（`/actuator/env`）

  - **loggers**：日志级别管理（`/actuator/loggers`）

  - **threaddump**：线程 dump（`/actuator/threaddump`）

  - **heapdump**：堆 dump（`/actuator/heapdump`）

2. **暴露配置**：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只列举了几个端点 | 7 个端点+暴露配置+安全保护 |
| 技术深度 | 不知道 show-details 配置 | 清楚 when-authorized 策略 |
| 实践经验 | 没有安全配置代码 | 有完整的 Spring Security 集成 |
| 面试官印象 | 背过端点名 | 理解 Actuator 的安全配置 |

---

### 2、进阶题：如何自定义 HealthIndicator 和 Micrometer 指标？指标如何接入 Prometheus？

**难度级别**：⭐⭐⭐（自定义指标、Micrometer、Prometheus 集成）

**1️⃣ Common Answer**

实现 HealthIndicator 接口，返回 Health 对象。用 MeterRegistry 注册指标，比如 Counter、Gauge。配置 Prometheus 的依赖和端口，然后 Grafana 展示。

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了实现接口 | 完整 HealthIndicator+Metrics+Prometheus+Grafana |
| 技术深度 | 不知道 Micrometer 的 Counter/Gauge | 清楚三种指标类型和 PromQL |
| 实践经验 | 没有完整配置 | 有生产环境监控方案 |
| 面试官印象 | 会自定义指标 | 有完整的可观测性体系 |

---

### 3、场景题：如何用 Actuator 监控 Agent 服务的 LLM 调用成功率、Token 消耗量、工具调用延迟等核心指标？

**难度级别**：⭐⭐⭐（业务指标、标签设计、告警规则）

**1️⃣ Common Answer**

用 Micrometer 的 Counter 记录调用次数，Timer 记录延迟。给指标加上标签，比如模型名称、工具名称。配置 Prometheus 抓取，Grafana 展示。

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 Counter/Timer | 完整指标设计+告警规则+Grafana 面板 |
| 技术深度 | 不知道标签设计原则 | 清楚基数控制和命名规范 |
| 实践经验 | 没有告警规则 | 有完整的监控告警体系 |
| 面试官印象 | 会用 Micrometer | 有生产环境可观测性经验 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Micrometer 的指标类型有哪些？ | 指标基础，Counter/Gauge/Timer/Histogram |
| Prometheus 的 PromQL 语法？ | 查询指标，监控告警的基础 |
| Grafana 如何配置 Dashboard？ | 可视化展示，监控体系的最后一环 |

---

## 3.4 Spring Boot 测试

### 1、基础题：@SpringBootTest 和 @WebMvcTest 有什么区别？各自适用什么场景？

**难度级别**：⭐⭐（集成测试、Slice 测试、Mock 依赖）

**1️⃣ Common Answer**

@SpringBootTest 是启动整个 Spring 容器的集成测试，@WebMvcTest 只测试 Web 层。@WebMvcTest 更快，因为它只加载 Controller 相关的 Bean。@SpringBootTest 适合测试完整流程，@WebMvcTest 适合测试 API。

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

2. **选择原则**：

  - **单元测试**：优先用 Slice 测试（@WebMvcTest、@DataJpaTest）。

  - **集成测试**：用 @SpringBootTest，但尽量减少数量。

  - **测试金字塔**：70% 单元测试 → 20% 集成测试 → 10% 端到端测试。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了区别和适用场景 | 包含代码示例、Slice 测试类型、测试金字塔 |
| 技术深度 | 不知道 Slice 测试的自动 Mock | 清楚 @MockBean 的工作机制 |
| 实践经验 | 没有测试金字塔概念 | 有测试策略和分层测试经验 |
| 面试官印象 | 知道测试注解 | 有完整的测试架构设计能力 |

---

### 2、进阶题：Spring Boot 测试的 Slice 测试（@DataJpaTest、@WebMvcTest 等）是如何实现的？如何 Mock 外部依赖？

**1️⃣ Common Answer**

Slice 测试就是只加载一部分 Bean，不加载整个容器。Mock 外部依赖用 @MockBean 注解，然后用 when().thenReturn() 模拟返回值。

**2️⃣ Impressive Answer**

1. **Slice 测试实现原理**：

  - 通过 `@BootstrapWith` 指定自定义的 `TestContextBootstrapper`。

  - `TestContextBootstrapper` 根据 `@TestConfiguration` 和 `@Import` 过滤 BeanDefinition，只加载特定层的 Bean。

  - 例如 `@WebMvcTest` 只加载 `@Controller`、`@ControllerAdvice`、`@Filter` 等注解的 Bean。

2. **@MockBean 工作机制**：

  - `@MockBean` 通过 `MockitoPostProcessor` 在测试上下文中注册 Mockito Mock 对象。

  - Mock 对象会替换容器中同类型的真实 Bean（包括 @Primary 和 @Qualifier）。

  - 支持按类型、按名称、按限定符匹配要替换的 Bean。

3. **Mock 外部依赖示例**：

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

2. **Mock 静态方法**（Mockito 3.4+）：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 MockBean | 包含实现原理、SpyBean、静态方法 Mock |
| 技术深度 | 不知道 TestContextBootstrapper | 清楚 Slice 测试的过滤机制 |
| 实践经验 | 没有静态方法 Mock | 有完整的 Mock 技术栈经验 |
| 面试官印象 | 会用 Mock | 理解测试框架的底层机制 |

---

### 3、场景题：Agent 服务的工具调用逻辑需要单元测试，但工具调用依赖外部 LLM API，如何用 Mockito + @MockBean 实现隔离测试？

**难度级别**：⭐⭐⭐（隔离测试、Mock 链式调用、参数匹配、异常测试）

**1️⃣ Common Answer**

可以用 @MockBean 把 LLM Provider Mock 掉，然后用 when().thenReturn() 模拟返回值。测试时调用工具执行方法，验证返回结果是否符合预期。

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了基本的 Mock | 包含参数匹配、验证、异常测试、集成测试 |
| 技术深度 | 不知道参数匹配器 | 清楚 Mockito 的完整 API |
| 实践经验 | 没有验证调用次数 | 有完整的测试覆盖经验 |
| 面试官印象 | 会写单元测试 | 有测试驱动开发的工程化能力 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| JUnit 5 的新特性有哪些？ | 单元测试框架的演进 |
| 如何测试私有方法？ | 测试边界情况的讨论 |
| 测试覆盖率如何计算？ | 测试质量的评估指标 |

---

## 3.5 条件注解与自动装配扩展

### 1、基础题：@Conditional 家族注解有哪些？各自的使用场景是什么？

**难度级别**：⭐⭐（条件注解、自动装配条件控制）

**1️⃣ Common Answer**

@ConditionalOnClass 是类路径上有这个类才生效，@ConditionalOnMissingBean 是没有这个 Bean 才生效。这些注解用在自动配置类上，控制 Bean 是否创建。

**2️⃣ Impressive Answer**

1. **类路径条件**：

  - `@ConditionalOnClass`：类路径上存在指定类时生效（如 `@ConditionalOnClass(Tomcat.class)`）

  - `@ConditionalOnMissingClass`：类路径上不存在指定类时生效

2. **Bean 条件**：

  - `@ConditionalOnBean`：容器中存在指定 Bean 时生效

  - `@ConditionalOnMissingBean`：容器中不存在指定 Bean 时生效（**用户自定义优先**的核心机制）

  - `@ConditionalOnSingleCandidate`：容器中只有一个候选 Bean 时生效

3. **配置条件**：

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

2. **Web 条件**：

  - `@ConditionalOnWebApplication`：是 Web 应用时生效

  - `@ConditionalOnNotWebApplication`：不是 Web 应用时生效

3. **自定义 Condition**：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了两个注解 | 6 大类条件注解，覆盖所有场景 |
| 技术深度 | 不知道 matchIfMissing | 清楚各注解的细节参数 |
| 实践经验 | 没有自定义 Condition | 有完整的自定义条件实现 |
| 面试官印象 | 背过注解名 | 理解条件注解的设计意图 |

---

### 2、进阶题：@ConditionalOnMissingBean 的判断时机是什么？为什么用户自定义的 Bean 能覆盖自动配置？

**难度级别**：⭐⭐⭐（Bean 注册顺序、DeferredImportSelector、自动配置优先级）

**1️⃣ Common Answer**

因为用户的 Bean 先注册，自动配置的 Bean 后注册，@ConditionalOnMissingBean 检查到已经有了就不创建了。

**2️⃣ Impressive Answer**

1. **核心机制：DeferredImportSelector**：

  - `AutoConfigurationImportSelector` 实现了 `DeferredImportSelector`，**延迟**到所有 `@Configuration` 类处理完之后才执行。

  - 用户的 `@Configuration` 类（通过 `@ComponentScan` 扫描）先于自动配置类处理。

  - 因此用户的 Bean 先注册到容器，自动配置类执行时 `@ConditionalOnMissingBean` 检查到已有 Bean，跳过创建。

2. **判断时机**：

  - `@ConditionalOnMissingBean` 的判断发生在 **BeanDefinition 注册阶段**，而非 Bean 实例化阶段。

  - `ConditionEvaluator` 在处理每个 `@Bean` 方法时调用 `Condition.matches()`，此时已注册的 BeanDefinition 都可以被检测到。

3. **正确覆盖姿势**：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"先后顺序" | DeferredImportSelector 机制 + 判断时机 + 陷阱 |
| 技术深度 | 不知道 DeferredImportSelector | 清楚延迟导入的设计意图 |
| 实践经验 | 不知道判断发生在哪个阶段 | 清楚 BeanDefinition 注册阶段的判断逻辑 |
| 面试官印象 | 知道结论但不知道原因 | 理解 Spring Boot 自动配置的核心设计 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot 自动装配的完整链路？ | 条件注解是自动装配的核心控制机制 |
| BeanDefinition 的注册流程？ | 条件注解判断发生在 BeanDefinition 注册阶段 |
| 如何自定义一个 Spring Boot Starter？ | Starter 的核心就是条件注解的合理使用 |

---

## 3.6 配置绑定机制

### 1、基础题：@ConfigurationProperties 和 @Value 有什么区别？各自适用什么场景？

**难度级别**：⭐⭐（配置绑定、类型安全、松散绑定）

**1️⃣ Common Answer**

@Value 是注入单个配置项，@ConfigurationProperties 是批量绑定一组配置。@ConfigurationProperties 支持 POJO 绑定，@Value 支持 SpEL 表达式。

**2️⃣ Impressive Answer**

1. **核心区别对比**：

| 维度 | @Value | @ConfigurationProperties |
| --- | --- | --- |
| 绑定粒度 | 单个属性 | 整个前缀下的属性组 |
| 类型安全 | 不支持（运行时失败） | 支持（启动时校验） |
| 松散绑定 | 不支持 | 支持（`server-port` = `serverPort`） |
| SpEL 表达式 | 支持 | 不支持 |
| 元数据提示 | 不支持 | 支持（IDE 自动补全） |
| 适用场景 | 少量、简单配置 | 模块化配置、复杂对象 |

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

2. **@Value 的 SpEL 能力**：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"批量 vs 单个" | 完整对比表 + 代码示例 + 松散绑定规则 |
| 技术深度 | 不知道松散绑定 | 清楚三种命名格式都能绑定 |
| 实践经验 | 没有 @Validated 校验 | 有启动时配置校验的最佳实践 |
| 面试官印象 | 知道区别 | 理解配置绑定的工程化最佳实践 |

---

### 2、进阶题：Spring Boot 的 Environment 抽象是什么？PropertySource 的优先级如何工作？

**难度级别**：⭐⭐⭐（Environment、PropertySource、配置覆盖机制）

**1️⃣ Common Answer**

Environment 是 Spring 的环境抽象，可以获取配置属性。PropertySource 是配置源，有多个配置源时按优先级取值，命令行参数优先级最高。

**2️⃣ Impressive Answer**

1. **Environment 抽象层次**：

  - `Environment` 接口：提供 `getProperty()`、`containsProperty()`、`getActiveProfiles()` 等方法。

  - `ConfigurableEnvironment`：可以添加/删除 `PropertySource`，获取 `MutablePropertySources`。

  - `StandardEnvironment`：非 Web 环境，包含系统属性和环境变量两个 PropertySource。

  - `StandardServletEnvironment`：Web 环境，额外包含 Servlet 配置和上下文参数。

2. **PropertySource 优先级链（从高到低）**：

```plaintext
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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"命令行最高" | 完整优先级链 + Environment 层次 + 自定义扩展 |
| 技术深度 | 不知道 EnvironmentPostProcessor | 清楚配置中心集成的扩展点 |
| 实践经验 | 没有自定义 PropertySource | 有 Nacos 集成的完整实现思路 |
| 面试官印象 | 知道优先级 | 理解 Environment 抽象的扩展机制 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot 配置加载优先级？ | PropertySource 优先级的具体体现 |
| Nacos/Apollo 配置中心如何集成？ | 自定义 PropertySource 的典型应用 |
| @RefreshScope 动态刷新原理？ | 配置变更后如何让 Bean 感知到 |

---

## 3.7 Spring Boot 事件机制

### 1、基础题：Spring Boot 有哪些内置的应用事件？发布顺序是什么？

**难度级别**：⭐⭐（ApplicationEvent、事件发布顺序、监听器）

**1️⃣ Common Answer**

Spring Boot 有 ApplicationStartedEvent、ApplicationReadyEvent 等事件，可以用 @EventListener 监听。启动完成后会发布 ApplicationReadyEvent。

**2️⃣ Impressive Answer**

1. **Spring Boot 启动事件完整顺序**：

```plaintext
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

2. **自定义事件**：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了几个事件名 | 完整顺序 + 两种监听方式 + 注意事项 |
| 技术深度 | 不知道容器刷新前的事件限制 | 清楚哪些事件不能用 @EventListener |
| 实践经验 | 没有自定义事件 | 有完整的自定义事件发布/监听实现 |
| 面试官印象 | 背过事件名 | 理解事件机制的完整链路和限制 |

---

### 2、进阶题：ApplicationRunner 和 CommandLineRunner 有什么区别？执行时机是什么？

**难度级别**：⭐⭐（Runner 接口、启动后执行、执行顺序）

**1️⃣ Common Answer**

ApplicationRunner 和 CommandLineRunner 都是启动完成后执行的，区别是参数类型不同。ApplicationRunner 的参数是 ApplicationArguments，CommandLineRunner 是 String[]。

**2️⃣ Impressive Answer**

1. **核心区别**：

| 维度 | CommandLineRunner | ApplicationRunner |
| --- | --- | --- |
| 参数类型 | `String[]`（原始命令行参数） | `ApplicationArguments`（结构化参数） |
| 参数解析 | 需要手动解析 `--key=value` | 自动解析，支持 `getOptionValues("key")` |
| 适用场景 | 简单脚本、参数不复杂 | 需要解析命名参数的场景 |

1. **执行时机**：在 `ApplicationStartedEvent` 之后、`ApplicationReadyEvent` 之前执行，此时容器已完全刷新，所有 Bean 已就绪。

2. **执行顺序控制**：通过 `@Order` 注解控制多个 Runner 的执行顺序（值越小越先执行）。

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了参数类型区别 | 对比表 + 执行时机 + 顺序控制 + 场景 |
| 技术深度 | 不知道执行时机 | 清楚在哪两个事件之间执行 |
| 实践经验 | 没有 @Order 控制 | 有多 Runner 顺序控制的实践 |
| 面试官印象 | 知道区别 | 理解 Runner 在启动流程中的定位 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot 启动流程？ | 事件和 Runner 都是启动流程的组成部分 |
| @PostConstruct 和 ApplicationRunner 的区别？ | 启动后执行逻辑的不同方式对比 |
| Spring 的事件驱动模型（观察者模式）？ | 事件机制的设计模式基础 |

---

## 3.8 Spring Boot 3.x 新特性

### 1、基础题：Spring Boot 3.x 相比 2.x 有哪些重要变化？

**难度级别**：⭐⭐（版本迁移、Jakarta EE、Java 17 基线）

**1️⃣ Common Answer**

Spring Boot 3.x 要求 Java 17，把 javax 包改成了 jakarta 包。自动配置的注册文件也变了，从 spring.factories 迁移到新的文件。

**2️⃣ Impressive Answer**

1. **基础要求升级**：

  - **Java 17 基线**：不再支持 Java 8/11，可以使用 Record、Sealed Class、Pattern Matching 等新特性。

  - **Jakarta EE 10**：所有 `javax.*` 包迁移到 `jakarta.*`（如 `javax.servlet` → `jakarta.servlet`），这是最大的迁移成本。

  - **Spring Framework 6.x**：底层框架同步升级。

2. **自动配置机制变化**：

  - 废弃 `spring.factories` 的 `EnableAutoConfiguration` 入口。

  - 迁移到 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`。

  - 新增 `@AutoConfiguration` 注解替代 `@Configuration`，语义更清晰。

3. **AOT（Ahead-of-Time）编译支持**：

  - Spring Boot 3.x 内置 AOT 处理器，在构建时分析 Bean 定义，生成静态代码。

  - 为 GraalVM 原生镜像编译提供支持，大幅减少反射使用。

  - `mvn spring-boot:build-image` 可直接构建原生镜像。

4. **可观测性增强**：

  - 内置 Micrometer Tracing（替代 Spring Cloud Sleuth），支持分布式链路追踪。

  - 自动集成 OpenTelemetry，无需额外配置。

5. **其他重要变化**：

  - `HttpExchange` 接口替代 Feign，声明式 HTTP 客户端内置支持。

  - 问题详情（RFC 7807）支持，`ProblemDetail` 标准化错误响应。

  - `@ControllerAdvice` 支持函数式异常处理。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 Java 17 和 jakarta | 5 大变化：基础要求+自动配置+AOT+可观测性+其他 |
| 技术深度 | 不知道 AOT 编译 | 清楚 AOT 对 GraalVM 原生镜像的意义 |
| 实践经验 | 不知道迁移成本 | 知道 javax→jakarta 是最大迁移成本 |
| 面试官印象 | 知道版本号 | 理解版本升级的技术演进方向 |

---

### 2、进阶题：Spring Boot 3.x 的 AOT 编译和 GraalVM 原生镜像是什么？有什么优缺点？

**难度级别**：⭐⭐⭐（AOT、GraalVM、原生镜像、冷启动优化）

**1️⃣ Common Answer**

GraalVM 可以把 Java 程序编译成原生可执行文件，启动速度很快，内存占用少。但是编译时间很长，而且有些反射代码会有问题。

**2️⃣ Impressive Answer**

1. **AOT vs JIT 对比**：

  - **JIT（Just-In-Time）**：运行时编译，启动慢（需要 JVM 预热），但长期运行性能好。

  - **AOT（Ahead-of-Time）**：构建时编译，启动极快（毫秒级），内存占用低，但失去 JIT 优化。

2. **Spring Boot AOT 处理流程**：

```plaintext
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

| 指标 | JVM 模式 | GraalVM 原生镜像 |
| --- | --- | --- |
| 启动时间 | 2-10 秒 | **50-200 毫秒** |
| 内存占用 | 200-500 MB | **50-100 MB** |
| 峰值吞吐量 | 高（JIT 优化） | 较低（无 JIT） |
| 编译时间 | 秒级 | **分钟级** |
| 动态特性 | 完全支持 | 受限（反射需配置） |

1. **Agent 场景适用性**：

  - **适合**：Serverless 函数、CLI 工具、冷启动敏感的场景（如 K8s 快速扩容）。

  - **不适合**：需要动态加载类、大量反射的 Agent 框架（如 LangChain4J 的动态代理）。

2. **常见问题**：反射、动态代理、序列化需要额外配置 `reflect-config.json`；第三方库兼容性问题（需要 GraalVM 支持）。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了优缺点 | AOT 流程 + 性能对比表 + 场景适用性 |
| 技术深度 | 不知道 AOT 处理流程 | 清楚 Spring Boot AOT 的完整编译链路 |
| 实践经验 | 不知道 Agent 场景的适用性 | 有 Serverless vs 长期运行的选型判断 |
| 面试官印象 | 知道原生镜像 | 理解 AOT 的工程权衡 |

---

### 3、场景题：Agent 服务需要快速冷启动（K8s 弹性扩容），如何用 Spring Boot 3.x 优化启动时间？

**难度级别**：⭐⭐⭐（启动优化、懒加载、AOT、类路径扫描优化）

**1️⃣ Common Answer**

可以用 GraalVM 原生镜像，启动很快。也可以开启懒加载，减少启动时加载的 Bean 数量。

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

| 优化手段 | 启动时间 | 适用场景 |
| --- | --- | --- |
| 无优化 | 5-10s | 开发环境 |
| 懒加载 | 2-4s | 生产环境（简单） |
| 排除自动配置 | 1-3s | 生产环境（精细化） |
| AOT 编译（JVM） | 1-2s | 生产环境（推荐） |
| GraalVM 原生镜像 | 50-200ms | Serverless/弹性扩容 |

1. **懒加载的风险**：懒加载会把配置错误推迟到运行时才暴露，建议在测试环境关闭懒加载，生产环境开启。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了两个方案 | 4 层递进优化策略 + 基准测试数据 |
| 技术深度 | 不知道懒加载的风险 | 清楚懒加载推迟错误暴露的问题 |
| 实践经验 | 没有量化数据 | 有各方案的启动时间对比 |
| 面试官印象 | 知道方向 | 有系统性的启动优化方案 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot 2.x 升级到 3.x 的迁移注意事项？ | 版本迁移的工程实践 |
| GraalVM 和 JVM 的区别？ | AOT 编译的底层原理 |
| K8s 的 HPA（水平自动扩缩容）如何配置？ | 弹性扩容场景下的启动时间要求 |

---

## 3.9 Spring Boot 启动优化与性能调优

### 1、基础题：Spring Boot 应用启动慢的常见原因有哪些？如何排查？

**难度级别**：⭐⭐（启动性能、Bean 扫描、自动配置）

**1️⃣ Common Answer**

启动慢可能是 Bean 太多，或者扫描范围太大。可以用 --debug 参数看自动配置报告，找出哪些配置类生效了。

**2️⃣ Impressive Answer**

1. **常见原因分析**：

  - **类路径扫描范围过大**：`@ComponentScan` 扫描了不必要的包，包含大量第三方 jar。

  - **自动配置过多**：加载了不需要的自动配置类（如引入了 spring-boot-starter-data-jpa 但不用数据库）。

  - **Bean 初始化耗时**：某些 Bean 的 `@PostConstruct` 或构造函数有耗时操作（如建立连接、加载模型）。

  - **AOP 代理创建**：大量 `@Transactional`、`@Async` 注解导致代理对象创建耗时。

2. **排查工具**：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"Bean 太多" | 4 大原因 + 排查工具 + 定位方法 |
| 技术深度 | 不知道 ApplicationStartup | 清楚启动耗时分析的完整工具链 |
| 实践经验 | 没有具体排查步骤 | 有系统性的排查方法论 |
| 面试官印象 | 知道方向 | 有生产环境性能排查经验 |

---

### 2、进阶题：Spring Boot DevTools 的热部署原理是什么？为什么生产环境要禁用？

**难度级别**：⭐⭐⭐（类加载器、热部署、双亲委派）

**1️⃣ Common Answer**

DevTools 可以在代码改变后自动重启应用，不用手动重启。生产环境要禁用是因为会影响性能，而且有安全风险。

**2️⃣ Impressive Answer**

1. **热部署核心原理——双类加载器机制**：

  - **Base ClassLoader**：加载不会变化的类（第三方 jar、Spring 框架本身）。

  - **Restart ClassLoader**：加载开发者自己的类（`classpath` 下的 class 文件）。

  - 文件变化时，只丢弃并重建 `Restart ClassLoader`，`Base ClassLoader` 保留，因此比完整重启快得多。

2. **触发机制**：

  - 监听 `classpath` 下的文件变化（IDE 编译后触发）。

  - 默认排除静态资源（`/static`、`/public`、`/templates`）的变化，避免频繁重启。

3. **LiveReload 功能**：DevTools 内置 LiveReload 服务器（端口 35729），浏览器安装插件后，静态资源变化时自动刷新页面（不重启 JVM）。

4. **生产环境禁用的原因**：

  - **性能开销**：文件监听器持续消耗 CPU 和 IO。

  - **类加载器隔离问题**：双类加载器可能导致 `ClassCastException`（同一个类被两个 ClassLoader 加载，类型不兼容）。

  - **安全风险**：LiveReload 服务器暴露额外端口。

  - **自动禁用机制**：DevTools 检测到 `java -jar` 启动时自动禁用（通过检查 jar 包中是否有 `BOOT-INF` 目录判断）。

5. **配置排除**：

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"自动重启" | 双类加载器原理 + LiveReload + 禁用原因 |
| 技术深度 | 不知道双类加载器 | 清楚 Restart ClassLoader 的设计 |
| 实践经验 | 不知道 ClassCastException 风险 | 知道类加载器隔离导致的类型不兼容问题 |
| 面试官印象 | 会用 DevTools | 理解热部署的底层机制和风险 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| JVM 类加载器的双亲委派模型？ | DevTools 热部署打破双亲委派的原理 |
| Spring Boot 懒加载如何配置？ | 启动优化的另一种手段 |
| GraalVM 原生镜像 vs JVM 启动优化？ | 不同场景下的启动优化选型 |

---

## 3.10 @Import 机制原理

### 1、基础题：@Import 注解有哪几种用法？

**难度级别**：⭐⭐（@Import、ImportSelector、ImportBeanDefinitionRegistrar）

**1️⃣ Common Answer**

@Import 可以导入一个配置类，相当于把那个类里的 Bean 都注册进来。Spring Boot 的自动装配就是用 @Import 实现的。

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"导入配置类" | 三种用法递进，覆盖静态/动态/注册三个层次 |
| 技术深度 | 不知道 ImportSelector | 清楚 @EnableAutoConfiguration 的实现原理 |
| 实践经验 | 没有自定义 Selector | 有 LLM Provider 动态选择的完整实现 |
| 面试官印象 | 知道 @Import 能导入 | 理解 Spring 扩展机制的完整层次 |

---

### 2、进阶题：DeferredImportSelector 和 ImportSelector 有什么区别？为什么自动装配要用 DeferredImportSelector？

**难度级别**：⭐⭐⭐（延迟导入、处理顺序、用户配置优先）

**1️⃣ Common Answer**

DeferredImportSelector 是延迟执行的 ImportSelector，会在所有配置类处理完之后才执行。这样可以保证用户自己的配置先生效。

**2️⃣ Impressive Answer**

1. **执行时机对比**：

| 特性 | ImportSelector | DeferredImportSelector |
| --- | --- | --- |
| 执行时机 | 当前 `@Configuration` 类处理时立即执行 | 所有 `@Configuration` 类处理完后延迟执行 |
| 分组支持 | 不支持 | 支持 `getImportGroup()`，同组的 Selector 合并处理 |
| 典型用途 | `@Enable*` 注解的简单导入 | Spring Boot 自动装配 |

1. **为什么自动装配必须用 DeferredImportSelector**：

```plaintext
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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"延迟执行" | 执行时机对比 + 原因分析 + 分组机制 |
| 技术深度 | 不知道为什么要延迟 | 清楚延迟是保证用户配置优先的核心手段 |
| 实践经验 | 不知道 Group 机制 | 知道自动配置类的排序是通过 Group 实现的 |
| 面试官印象 | 知道结论 | 理解设计背后的工程权衡 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot 自动装配的完整链路？ | @Import + DeferredImportSelector 是自动装配的核心 |
| @Enable* 注解的设计模式？ | 模块化开关的设计范式，底层都是 @Import |
| MyBatis 的 @MapperScan 原理？ | ImportBeanDefinitionRegistrar 的典型应用 |

---

## 3.11 Spring Boot SPI 机制原理

### 1、基础题：Spring Boot 的 SPI 机制是什么？spring.factories 是如何被加载的？

**难度级别**：⭐⭐⭐（SPI、SpringFactoriesLoader、类加载机制）

**1️⃣ Common Answer**

spring.factories 是一个配置文件，里面写了要自动加载的类名。Spring Boot 启动时会读取这个文件，然后把里面的类加载进来。这是一种 SPI 机制。

**2️⃣ Impressive Answer**

1. **SPI 机制本质**：SPI（Service Provider Interface）是一种"接口在框架侧定义，实现在使用方提供"的扩展机制。Spring Boot 的 SPI 比 Java 原生 SPI（`ServiceLoader`）更强大，支持按接口类型分组加载。

2. `**SpringFactoriesLoader**` 加载流程：

```plaintext
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

2. **Boot 3.x 的改进**：

```plaintext
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

| 扩展点接口 | 作用 |
| --- | --- |
| `EnableAutoConfiguration` | 自动配置类注册 |
| `ApplicationContextInitializer` | 容器初始化扩展 |
| `ApplicationListener` | 应用事件监听 |
| `SpringApplicationRunListener` | 启动流程监听 |
| `EnvironmentPostProcessor` | 环境后处理 |
| `FailureAnalyzer` | 启动失败分析 |

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"读取文件加载类" | 加载流程 + 缓存机制 + Boot 3.x 改进 + 扩展点类型 |
| 技术深度 | 不知道缓存机制 | 清楚 ClassLoader 级别的缓存设计 |
| 实践经验 | 不知道 Boot 3.x 的变化 | 知道独立文件的性能优化原因 |
| 面试官印象 | 知道 spring.factories | 理解 SPI 机制的完整设计 |

---

### 2、进阶题：如何利用 spring.factories 实现自己的扩展点？EnvironmentPostProcessor 的使用场景？

**难度级别**：⭐⭐⭐（EnvironmentPostProcessor、自定义扩展点、配置加密）

**1️⃣ Common Answer**

在 spring.factories 里注册自己的类，实现对应的接口就可以了。EnvironmentPostProcessor 可以在 Environment 准备好之后修改配置。

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

2. **Agent 场景**：LLM API Key 在配置文件中加密存储（`ENC(xxx)`），通过 `EnvironmentPostProcessor` 在启动时解密，避免明文存储敏感信息。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"实现接口注册" | 完整实现 + 注册方式 + 执行时机限制 |
| 技术深度 | 不知道不能注入 Bean | 清楚容器未创建时的限制 |
| 实践经验 | 没有具体场景 | 有配置解密的生产级实现 |
| 面试官印象 | 知道扩展点存在 | 有安全配置的工程实践 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Java 原生 SPI（ServiceLoader）和 Spring SPI 的区别？ | SPI 机制的对比，Spring SPI 更灵活 |
| Spring Boot 自动装配的完整链路？ | SPI 是自动装配的基础加载机制 |
| 配置中心（Nacos）如何集成到 Spring Boot？ | EnvironmentPostProcessor 的典型应用场景 |

---

## 3.12 refreshContext 核心原理

### 1、基础题：Spring 的 refresh() 方法做了哪些事？Bean 的生命周期是什么？

**难度级别**：⭐⭐⭐（refresh 流程、BeanPostProcessor、Bean 生命周期）

**1️⃣ Common Answer**

refresh() 是 Spring 容器的核心方法，会扫描 Bean、实例化 Bean、注入依赖。Bean 的生命周期包括实例化、属性注入、初始化、使用、销毁几个阶段。

**2️⃣ Impressive Answer**

1. `**refresh()**` 12 个核心步骤：

```plaintext
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

```plaintext
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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"扫描、实例化、注入" | 12 步完整流程 + Bean 生命周期完整链路 |
| 技术深度 | 不知道 BeanFactoryPostProcessor | 清楚 ConfigurationClassPostProcessor 的核心作用 |
| 实践经验 | 不知道哪步最耗时 | 知道 finishBeanFactoryInitialization 是性能瓶颈 |
| 面试官印象 | 背过生命周期 | 理解 refresh 流程的完整机制 |

---

### 2、进阶题：BeanPostProcessor 和 BeanFactoryPostProcessor 有什么区别？各自的典型应用是什么？

**难度级别**：⭐⭐⭐（后处理器、AOP 代理、@Autowired 注入原理）

**1️⃣ Common Answer**

BeanPostProcessor 是 Bean 初始化前后的扩展点，BeanFactoryPostProcessor 是 BeanFactory 级别的扩展点。AOP 就是通过 BeanPostProcessor 实现的。

**2️⃣ Impressive Answer**

1. **核心区别**：

| 维度 | BeanFactoryPostProcessor | BeanPostProcessor |
| --- | --- | --- |
| 作用阶段 | BeanDefinition 注册完成后，Bean 实例化之前 | Bean 实例化之后，初始化前后 |
| 操作对象 | `BeanDefinition`（元数据） | Bean 实例 |
| 典型实现 | `ConfigurationClassPostProcessor`、`PropertySourcesPlaceholderConfigurer` | `AutowiredAnnotationBeanPostProcessor`、`AbstractAutoProxyCreator` |
| 执行时机 | `invokeBeanFactoryPostProcessors()` | `registerBeanPostProcessors()` 注册，Bean 初始化时调用 |

1. **典型应用分析**：

```plaintext
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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"Bean 级别 vs BeanFactory 级别" | 完整对比表 + 典型实现树 + AOP 代理时机 |
| 技术深度 | 不知道 ConfigurationClassPostProcessor | 清楚 Spring 最核心的后处理器是什么 |
| 实践经验 | 不知道 @Transactional 内部调用失效原因 | 能从代理创建时机解释这个经典问题 |
| 面试官印象 | 知道扩展点存在 | 理解 Spring 扩展机制的完整体系 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring 的三级缓存解决循环依赖？ | finishBeanFactoryInitialization 阶段的核心问题 |
| @Transactional 为什么同类内部调用失效？ | BeanPostProcessor 创建代理的机制决定的 |
| Spring AOP 的 CGLIB 和 JDK 动态代理区别？ | AbstractAutoProxyCreator 选择代理方式的逻辑 |

---

## 3.13 外部化配置加载原理（ConfigData API）

### 1、基础题：Spring Boot 的配置文件是如何被加载进来的？Boot 2.x 和 Boot 3.x 的加载机制有什么变化？

**⭐⭐**（ConfigFileApplicationListener、ConfigDataEnvironmentPostProcessor、PropertySource 加载时机）

**Answer：**

Spring Boot 配置加载的核心机制经历了从 Boot 2.x 到 Boot 3.x 的重大重构，主要体现在从 `ConfigFileApplicationListener` 到 ConfigData API 的演进。

**Boot 2.x 机制：**

使用 `ConfigFileApplicationListener` 监听器，在 `ApplicationContextInitializer` 阶段加载配置：

1. **监听器触发**：监听 `ApplicationEnvironmentPreparedEvent` 事件

2. **搜索配置文件**：按优先级搜索 `application.properties/yml`，支持 `file:./config/`、`file:./`、`classpath:/config/`、`classpath:/` 四个位置

3. **PropertySource 加载**：将解析后的配置添加到 `Environment` 的 `PropertySource` 链中

4. **Profile 激活**：根据 `spring.profiles.active` 激活特定 profile 的配置文件

**Boot 3.x 机制：**

引入全新的 ConfigData API，使用 `ConfigDataEnvironmentPostProcessor` 替代监听器模式：

1. **EnvironmentPostProcessor 触发**：在 Spring Boot 启动早期执行

2. **ConfigData 接口**：定义统一的配置数据抽象，支持多种配置源（文件、环境变量、云配置中心等）

3. **ConfigDataLocationResolver**：解析配置位置，返回 `ConfigDataResource`

4. **ConfigDataLoader**：加载具体的配置数据，转换为 `PropertySource`

5. **Import 链**：支持配置文件的嵌套导入（`spring.config.import`）

**核心差异对比：**

| 维度 | Boot 2.x | Boot 3.x |
| --- | --- | --- |
| 触发方式 | 事件监听器 | EnvironmentPostProcessor |
| 配置抽象 | PropertySource | ConfigData + PropertySource |
| 扩展性 | 继承监听器 | 实现 ConfigDataLocationResolver |
| 导入支持 | 不支持配置导入 | 支持 spring.config.import |

---

### 2、进阶题：Spring Boot 的配置加载优先级完整链路是什么？命令行参数、环境变量、application.yml、application-{profile}.yml 的优先级顺序？

**⭐⭐⭐**（PropertySource 优先级、Profile 激活时机、配置覆盖规则）

1️⃣ Common Answer

Spring Boot 配置加载优先级从高到低依次为：命令行参数、环境变量、`application-{profile}.yml`、`application.yml`、默认配置。高优先级的配置会覆盖低优先级的同名配置。Profile 激活后，特定 profile 的配置会覆盖默认配置。

2️⃣ Impressive Answer

Spring Boot 配置加载的优先级链路是一个多层 PropertySource 栈，理解其加载顺序对多环境部署和配置调试至关重要。我从加载时机、优先级规则和实战应用三个维度展开。

**一、完整的加载优先级链路（从高到低）**

```plaintext
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

2. **环境变量**：`SPRING_PROFILES_ACTIVE=prod`

3. **配置文件**：`spring.profiles.active=prod`

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 优先级链路深度 | 仅列出 4-5 个层级 | 完整列出 8 个层级，包括随机数、@PropertySource |
| 加载时机 | 未提及或模糊 | 明确说明在 SpringApplication.run() 极早期完成 |
| Profile 激活方式 | 仅提及配置文件 | 列出 3 种激活方式及其优先级 |
| 实战场景 | 缺少具体案例 | 结合 Agent 服务场景，给出多环境配置示例 |
| 调试技巧 | 无 | 提供 --debug 启动参数调试方法 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| @ConfigurationProperties 和 @Value 的区别？ | 配置绑定的两种方式，和加载机制密切相关 |
| 如何自定义配置源（从数据库加载配置）？ | EnvironmentPostProcessor、ConfigData API 扩展点 |
| Spring Boot 配置的松散绑定规则？ | kebab-case、camelCase、snake_case 属性名转换 |
| 如何实现配置的动态刷新？ | @RefreshScope、ContextRefresher、配置中心集成 |

---

## 3.14 Profiles 机制

### 1、基础题：Spring Boot 的 @Profile 和 spring.profiles.active 是如何工作的？Profile Groups 是什么？

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

### 2、进阶题：多环境配置管理的最佳实践是什么？如何在 Agent 服务中实现 dev/test/prod 三套环境的配置隔离？

**⭐⭐⭐**（application-{profile}.yml 加载机制、Profile 激活方式、配置中心集成）

1️⃣ Common Answer

多环境配置管理主要通过 `application-{profile}.yml` 文件实现。创建 `application-dev.yml`、`application-test.yml`、`application-prod.yml`，通过 `spring.profiles.active` 激活对应环境的配置文件。在 Agent 服务中，dev 环境使用低成本 LLM 模型，test 环境使用测试模型，prod 环境使用生产模型。

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 配置分层 | 简单的文件分离 | 基础配置 + 环境特定 + Profile Groups 三层架构 |
| 激活方式 | 仅提到配置文件激活 | 环境变量优先，适配容器化部署场景 |
| 动态配置 | 未提及 | 集成 Nacos，通过 @RefreshScope 实现热更新 |
| 敏感信息 | 直接写在配置文件中 | 使用密钥管理服务，通过环境变量注入 |
| Agent 场景 | 简单的环境区分 | 针对多组件（LLM、向量库）的 Profile Groups 设计 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot 配置文件的加载优先级是什么？ | 配置文件加载顺序、覆盖机制 |
| @ConditionalOnProfile 和 @Profile 的区别？ | 条件注解的使用场景 |
| 如何实现配置的动态刷新？ | @RefreshScope、配置中心集成 |
| 在 Kubernetes 中如何管理 Spring Boot 的环境配置？ | ConfigMap、Secret、环境变量注入 |

---

## 3.15 多模块 Starter 工程实践

### 1、基础题：自定义 Spring Boot Starter 的标准目录结构和命名规范是什么？spring-boot-autoconfigure 和 spring-boot-starter 模块如何分工？

**⭐⭐**（Starter 命名规范、autoconfigure 模块职责、AutoConfiguration.imports 注册）

**Answer：**

Spring Boot Starter 的标准命名规范为 `xxx-spring-boot-starter`（如 `llm-client-spring-boot-starter`），官方 Starter 则以 `spring-boot-starter-xxx` 命名。

**标准多模块结构：**

```plaintext
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

### 2、进阶题：如何设计一个生产级的 LLM Client Starter？需要考虑哪些工程实践问题？

**⭐⭐⭐**（条件注解、@ConfigurationProperties、HealthIndicator、MeterRegistry、优雅降级）

1️⃣ Common Answer

设计 LLM Client Starter 主要考虑：使用 `@ConditionalOnMissingBean` 实现自动配置、`@ConfigurationProperties` 绑定 API Key 和模型名称、实现 `HealthIndicator` 检查连通性、用 `MeterRegistry` 记录请求耗时。

```java
@Configuration
@ConditionalOnClass(LlmClient.class)
@EnableConfigurationProperties(LlmClientProperties.class)
public class LlmClientAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public LlmClient llmClient(LlmClientProperties properties) {
        return new OpenAiLlmClient(properties);
    }
}
```

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

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 条件装配 | 仅用 @ConditionalOnMissingBean | 多级条件注解，避免不必要的 Bean 创建 |
| 配置管理 | 简单的属性绑定 | JSR-303 校验 + spring-configuration-metadata.json IDE 提示 |
| 健康检查 | 仅检测连通性 | 深度检查：连通性 + 配额 + 限流状态 |
| 指标暴露 | 仅记录请求耗时 | 多维度：耗时、Token 消耗、成功率，支持 Prometheus 集成 |
| 容错机制 | 简单异常处理 | Resilience4j 熔断、降级、重试，提供缓存降级策略 |
| 扩展性 | 无扩展机制 | 拦截器 SPI，支持日志、签名、脱敏等自定义处理 |

---

### 3、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring Boot 自动配置原理？@EnableAutoConfiguration 如何工作？ | Starter 的核心依赖机制 |
| 如何排除某个自动配置类？ | @SpringBootApplication(exclude)、spring.autoconfigure.exclude |
| @ConditionalOnMissingBean 和 @ConditionalOnBean 的区别？ | 前者：Bean 不存在时生效；后者：Bean 存在时生效 |
| @AutoConfiguration 和 @Configuration 的区别？ | Boot 2.7+ 新注解，支持 before/after 控制顺序 |
| 如何调试自动配置的加载过程？ | --debug 启动参数、ConditionEvaluationReport |
