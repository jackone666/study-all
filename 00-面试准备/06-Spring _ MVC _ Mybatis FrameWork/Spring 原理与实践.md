## IoC 容器与 AOP 原理

### 4.1 Bean 生命周期

#### 1、基础题：Spring IoC 容器的工作原理是什么？Bean 的生命周期有哪些阶段？

**难度级别**：⭐⭐（BeanDefinition、实例化、属性注入、初始化回调、销毁）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- Bean 生命周期完整链路
- IoC 核心原理
- 实例化阶段
- 属性赋值阶段
- 初始化阶段
- 使用阶段

**2️⃣ Impressive Answer**
1. **IoC 核心原理**：IoC（Inversion of Control）是将对象的创建和依赖关系管理从代码中转移到容器。Spring 通过 `BeanDefinition` 描述 Bean 的元数据（类名、作用域、依赖关系等），容器根据 BeanDefinition 完成 Bean 的创建和装配。
1. **Bean 生命周期完整链路**：
1. **实例化阶段**：通过构造器或工厂方法创建 Bean 实例
1. **属性赋值阶段**：Spring 对 Bean 的属性进行依赖注入（@Autowired、@Value）
1. **初始化阶段**：执行各种初始化回调（@PostConstruct、InitializingBean.afterPropertiesSet、init-method）
1. **使用阶段**：Bean 在容器中被应用程序使用
1. **销毁阶段**：容器关闭时执行销毁回调（@PreDestroy、DisposableBean.destroy、destroy-method）
1. **关键扩展点**：`BeanPostProcessor` 是最核心的扩展点，AOP 代理、@Autowired 注入、@Async 异步都是通过它实现的。理解生命周期就是理解 Spring 的扩展能力。
1. **实践注意**：`@PostConstruct` 在属性注入之后执行，可以安全使用注入的依赖；但此时 AOP 代理还未创建，不要在 `@PostConstruct` 中依赖 AOP 行为。

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
只说了&quot;创建、初始化、销毁&quot;
</td>
<td>
完整链路 8 个阶段，每步都有对应机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 BeanPostProcessor 的作用
</td>
<td>
清楚 AOP 代理在 postProcessAfterInitialization 创建
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
知道 @PostConstruct 和 AOP 的时序关系
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
理解生命周期的设计意图和扩展能力
</td>
</tr>
</table>

---

#### 2、进阶题：BeanPostProcessor、InitializingBean、@PostConstruct 的执行顺序是什么？各自的应用场景？

**难度级别**：⭐⭐⭐（执行顺序、扩展点对比、实际应用）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 执行顺序
- BeanPostProcessor 应用
- InitializingBean 应用
- @PostConstruct 应用

**2️⃣ Impressive Answer**
1. **执行顺序**：实例化 → 属性赋值 → BeanPostProcessor.postProcessBeforeInitialization → @PostConstruct → InitializingBean.afterPropertiesSet → init-method → BeanPostProcessor.postProcessAfterInitialization
1. **BeanPostProcessor 应用**：在初始化前后对 Bean 进行增强，如 AOP 代理创建、属性校验、日志记录等
1. **InitializingBean 应用**：实现接口的 afterPropertiesSet 方法，依赖注入完成后执行必要初始化
1. **@PostConstruct 应用**：JSR-250 标准，用于依赖注入完成后的初始化逻辑，推荐使用注解而非接口

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
顺序混乱，不知道先后
</td>
<td>
清晰的 6 步执行链路
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 BeanPostProcessor 的全局性
</td>
<td>
区分了全局增强 vs 单 Bean 初始化
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到优先级控制
</td>
<td>
知道 @Order、@DependsOn 的用法
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
记忆混乱
</td>
<td>
理解执行顺序和各扩展点的定位
</td>
</tr>
</table>

---

#### 3、场景题：Agent 的 LLM 客户端 Bean 需要在启动时预热连接池，如何利用 Bean 生命周期钩子实现？

**难度级别**：⭐⭐⭐（生命周期钩子、连接池预热）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 选择 @PostConstruct
- 预热逻辑
- 异常处理
- 优雅降级

**2️⃣ Impressive Answer**
1. **选择 @PostConstruct**：在 LLM 客户端 Bean 中添加 @PostConstruct 注解的方法
1. **预热逻辑**：方法中调用客户端发送少量测试请求（如健康检查），建立连接池连接
1. **异常处理**：捕获预热异常，记录日志并决定是否阻止 Bean 创建
1. **优雅降级**：预热失败时标记 Bean 为降级状态，运行时重试预热

```java
@Component
public class LLMClient {

    @PostConstruct
    public void warmUp() {
        try {
            // 发送健康检查请求预热连接池
            client.healthCheck();
            log.info("LLM client connection pool warmed up successfully");
        } catch (Exception e) {
            log.error("LLM client warm up failed, will retry at runtime", e);
            // 可选择抛出异常阻止 Bean 创建
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
简单描述，无代码示例
</td>
<td>
完整方案设计，包含代码实现
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
仅提及预热概念
</td>
<td>
包含异常处理、降级策略
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无生产环境考虑
</td>
<td>
考虑日志、重试、降级等生产实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
基础理解，缺乏工程思维
</td>
<td>
具备生产环境问题解决能力
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
Spring 三级缓存与循环依赖如何解决？
</td>
<td>
生命周期中的实例化阶段涉及循环依赖处理
</td>
<td>
答：三级缓存各自作用；为什么需要三级而非两级；AOP 代理场景；singletonObjects（一级）：Map，存放完全初始化的 Bean，getBean() 默认从这里获取。
</td>
</tr>
<tr>
<td>
@DependsOn 如何控制 Bean 加载顺序？
</td>
<td>
生命周期扩展点，解决依赖顺序问题
</td>
<td>
答：顺序性通常靠同一业务 key 路由到同一分区保证；跨分区无法全局有序，只能做局部顺序或业务补偿。
</td>
</tr>
<tr>
<td>
Spring Bean 的作用域有哪些？Prototype 的生命周期有什么不同？
</td>
<td>
不同作用域的生命周期管理差异
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 4.2 三级缓存与循环依赖

#### 1、基础题：什么是 Spring 的循环依赖？Spring 是如何解决的？

**难度级别**：⭐⭐（循环依赖定义、三级缓存、setter 注入解决）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 解决机制（三级缓存）
- 解决流程
- 一级缓存（singletonObjects）：存放完全初始化好的 Bean
- 二级缓存（earlySingletonObjects）：存放提前暴露的 Bean（实例化但未初始化）
- 三级缓存（singletonFactories）：存放 Bean 工厂，用于生成提前暴露的对象（可能包含 AOP 代理）
- 创建 A，实例化后放入三级缓存

**2️⃣ Impressive Answer**
1. **循环依赖定义**：A → B → A（直接循环）或 A → B → C → A（间接循环）。Spring 只能解决**单例 Bean 的 setter 注入循环依赖**，构造器注入和 Prototype 不支持。
1. **解决机制（三级缓存）**：
  - **一级缓存（singletonObjects）**：存放完全初始化好的 Bean
  - **二级缓存（earlySingletonObjects）**：存放提前暴露的 Bean（实例化但未初始化）
  - **三级缓存（singletonFactories）**：存放 Bean 工厂，用于生成提前暴露的对象（可能包含 AOP 代理）
1. **解决流程**：
  - 创建 A，实例化后放入三级缓存
  - 注入 B，发现 B 依赖 A
  - 从三级缓存获取 A 的工厂，创建提前暴露对象，放入二级缓存，从三级缓存移除
  - B 初始化完成，注入给 A
  - A 初始化完成，放入一级缓存，从二级缓存移除
1. **为什么需要三级**：二级缓存只能存普通对象，三级缓存可以存工厂，支持在循环依赖时提前创建 AOP 代理（如 @Async、@Transactional）。

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
只说了&quot;三级缓存&quot;
</td>
<td>
三级缓存定义+解决流程+为什么需要三级
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道三级缓存各自作用
</td>
<td>
清楚每级缓存的作用和 AOP 代理场景
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
不知道构造器注入不支持
</td>
<td>
区分了 setter 和构造器注入的差异
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
理解循环依赖的完整解决机制
</td>
</tr>
</table>

---

#### 2、进阶题：Spring 三级缓存（singletonObjects/earlySingletonObjects/singletonFactories）各自的作用是什么？为什么需要三级而不是两级？

**难度级别**：⭐⭐⭐（三级缓存作用、AOP 代理、两级缓存问题）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三级缓存各自作用
- 为什么需要三级而非两级
- AOP 代理场景
- singletonObjects（一级）：Map，存放完全初始化的 Bean，getBean() 默认从这里获取。
- earlySingletonObjects（二级）：Map，存放实例化但未初始化的 Bean，用于循环依赖注入。
- singletonFactories（三级）：Map>，存放 Bean 工厂，延迟创建提前暴露对象（支持 AOP 代理）。

**2️⃣ Impressive Answer**
1. **三级缓存各自作用**：
  - **singletonObjects（一级）**：`Map<String, Object>`，存放完全初始化的 Bean，getBean() 默认从这里获取。
  - **earlySingletonObjects（二级）**：`Map<String, Object>`，存放实例化但未初始化的 Bean，用于循环依赖注入。
  - **singletonFactories（三级）**：`Map<String, ObjectFactory<?>>`，存放 Bean 工厂，延迟创建提前暴露对象（支持 AOP 代理）。
1. **为什么需要三级而非两级**：
  - **两级缓存问题**：如果只有两级，必须在实例化时就创建 AOP 代理，但此时还没确定是否需要代理（可能后续的 BeanPostProcessor 决定不代理）。
  - **三级缓存优势**：三级缓存存的是工厂，只有真正发生循环依赖时才调用工厂创建代理，避免不必要的代理创建。
1. **AOP 代理场景**：

```java
// A 被 @Transactional 注解，需要代理
@Component
public class A {
    @Autowired private B b;
}

@Component
@Transactional
public class B {
    @Autowired private A a;
}

// 流程：
// 1. 创建 A，实例化，工厂放入三级缓存
// 2. 注入 B，发现 B 依赖 A
// 3. 调用三级缓存工厂，创建 A 的代理对象，放入二级缓存
// 4. B 拿到 A 的代理，初始化完成
// 5. A 拿到 B，初始化完成，放入一级缓存
```
1. **构造器注入无法解决**：构造器注入在实例化阶段就需要依赖对象，此时对象还未创建，无法提前暴露。

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
只说了三级缓存名字
</td>
<td>
每级缓存的作用+为什么需要三级
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 AOP 代理的时机
</td>
<td>
清楚三级缓存支持延迟代理创建
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
有完整的 AOP 循环依赖流程
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过定义
</td>
<td>
理解三级缓存的设计意图
</td>
</tr>
</table>

---

#### 3、场景题：Agent 服务中 ToolRegistry 和 AgentExecutor 互相依赖导致循环依赖，如何设计规避？

**难度级别**：⭐⭐⭐（循环依赖规避、设计模式、延迟加载）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 方案一：@Lazy 延迟加载（推荐）
- 方案二：事件驱动解耦（推荐）
- 方案三：抽取中间层（最佳）
- 方案对比
- @Lazy：简单，但掩盖设计问题
- 事件驱动：解耦彻底，但增加复杂度

**2️⃣ Impressive Answer**
1. **方案一：@Lazy 延迟加载（推荐）**

```java
@Component
public class ToolRegistry {
    @Autowired
    @Lazy  // 延迟注入，避免循环依赖
    private AgentExecutor executor;
}

@Component
public class AgentExecutor {
    @Autowired
    private ToolRegistry registry;
}
```
1. **方案二：事件驱动解耦（推荐）**

```java
@Component
public class ToolRegistry implements ApplicationListener<AgentReadyEvent> {
    private AgentExecutor executor;

    @Override
    public void onApplicationEvent(AgentReadyEvent event) {
        this.executor = event.getExecutor();
    }
}

@Component
public class AgentExecutor implements InitializingBean {
    @Autowired
    private ToolRegistry registry;

    @Override
    public void afterPropertiesSet() {
        // 发布事件，通知 ToolRegistry
        ApplicationContext.publishEvent(new AgentReadyEvent(this));
    }
}
```
1. **方案三：抽取中间层（最佳）**

```java
// 抽取工具接口，避免直接依赖
public interface ToolInvoker {
    ToolResult invoke(ToolRequest request);
}

@Component
public class ToolRegistry implements ToolInvoker {
    // 只依赖接口，不依赖 AgentExecutor
}

@Component
public class AgentExecutor {
    @Autowired
    private ToolInvoker invoker;  // 注入接口，不依赖 ToolRegistry
}
```
1. **方案对比**：
  - @Lazy：简单，但掩盖设计问题
  - 事件驱动：解耦彻底，但增加复杂度
  - 抽取接口：符合依赖倒置原则，推荐

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
只说了 @Lazy
</td>
<td>
三种方案+完整代码+对比分析
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道事件驱动解耦
</td>
<td>
知道依赖倒置原则的应用
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有方案对比
</td>
<td>
有设计权衡和推荐方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用但不深入
</td>
<td>
有架构设计能力
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
@Autowired 和 @Resource 的区别？
</td>
<td>
依赖注入方式，循环依赖和注入方式相关
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：依赖注入方式，循环依赖和注入方式相关，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring Bean 的作用域有哪些？
</td>
<td>
不同作用域的循环依赖处理策略不同
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Spring 事务 @Transactional 为什么不能用于 private 方法？
</td>
<td>
AOP 代理机制，和循环依赖中的代理创建相关
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
</table>

---

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

#### 3、进阶题：@Autowired、@Resource、@Inject 三种注入方式的区别？什么时候用构造器注入？

**难度级别**：⭐⭐⭐（按类型注入 vs 按名称注入、JSR-250/JSR-330 规范、构造器注入不可变性）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三种注入方式对比
- 构造器注入的四大优势
- 不可变性：依赖声明为 final，对象创建后不可修改，线程安全。
- 避免 NPE：构造器注入保证依赖在使用前一定已注入，不会出现字段为 null 的情况。
- 便于单测：不依赖 Spring 容器，直接 new 传入 mock 对象即可测试。
- 暴露设计问题：构造器参数过多时，说明类职责过重，提醒重构。

**2️⃣ Impressive Answer**
1. **三种注入方式对比**：

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
Spring 框架
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
先按类型，再按名称
</td>
<td>
先按名称，再按类型
</td>
<td>
按类型（同 @Autowired）
</td>
</tr>
<tr>
<td>
必要性
</td>
<td>
<code>required=false</code> 可选注入
</td>
<td>
无此属性
</td>
<td>
无此属性
</td>
</tr>
<tr>
<td>
配合限定
</td>
<td>
<code>@Qualifier</code>
</td>
<td>
<code>name</code> 属性
</td>
<td>
<code>@Named</code>
</td>
</tr>
</table>
1. **构造器注入的四大优势**：
  - **不可变性**：依赖声明为 `final`，对象创建后不可修改，线程安全。
  - **避免 NPE**：构造器注入保证依赖在使用前一定已注入，不会出现字段为 null 的情况。
  - **便于单测**：不依赖 Spring 容器，直接 `new` 传入 mock 对象即可测试。
  - **暴露设计问题**：构造器参数过多时，说明类职责过重，提醒重构。
1. **Spring 官方推荐**：Spring 4.3+ 单构造器可省略 @Autowired；Spring 团队明确推荐构造器注入作为首选方式。
1. **Agent 场景**：工具注册器需要注入多个 `ToolProvider` 实现时，用构造器注入 `List<ToolProvider>` 保证不可变性，配合 `@Qualifier` 或 `@Primary` 控制优先级。

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
零散说了几个区别
</td>
<td>
表格对比 + 四大优势，结构清晰
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
清楚先按类型/名称的匹配顺序
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
只说&quot;官方推荐&quot;
</td>
<td>
解释推荐的四个具体原因
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道有三种但说不清区别
</td>
<td>
有选型依据，理解设计意图
</td>
</tr>
</table>

---

### 3.6 Spring 依赖注入方式

#### 1、基础题：Spring 的依赖注入有哪几种方式？@Autowired 和 @Resource 有什么区别？

**难度级别**：⭐⭐（构造器注入、Setter 注入、字段注入、注解差异）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三种注入方式
- @Autowired vs @Resource 核心区别
- 构造器注入：通过构造函数注入，依赖对象在 Bean 创建时就必须提供，保证 Bean 不可变且完全初始化。
- Setter 注入：通过 setter 方法注入，依赖对象可以在 Bean 创建后设置，支持可选依赖和循环依赖。
- 字段注入：直接在字段上加 @Autowired，不推荐使用——无法进行单元测试（无法 mock 依赖）、隐藏依赖关系、违反单一职责原则。
- 来源不同：@Autowired 是 Spring 注解，@Resource 是 JSR-250 标准（JDK 自带）。

**2️⃣ Impressive Answer**
1. **三种注入方式**：
  - **构造器注入**：通过构造函数注入，依赖对象在 Bean 创建时就必须提供，保证 Bean 不可变且完全初始化。
  - **Setter 注入**：通过 setter 方法注入，依赖对象可以在 Bean 创建后设置，支持可选依赖和循环依赖。
  - **字段注入**：直接在字段上加 @Autowired，不推荐使用——无法进行单元测试（无法 mock 依赖）、隐藏依赖关系、违反单一职责原则。
1. **@Autowired vs @Resource 核心区别**：
  - **来源不同**：@Autowired 是 Spring 注解，@Resource 是 JSR-250 标准（JDK 自带）。
  - **匹配策略**：@Autowired 默认按类型匹配（byType），类型冲突时按 @Qualifier 指定名称；@Resource 默认按名称匹配（byName），找不到名称再按类型。
  - **注入位置**：@Autowired 可以用在构造器、字段、方法、参数上；@Resource 只能用在字段和 setter 方法上。
1. **最佳实践**：优先使用**构造器注入**（强制依赖、不可变、便于测试），可选依赖用 Setter 注入，避免字段注入。Spring 4.3+ 单构造器可省略 @Autowired。

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
简单列举三种方式
</td>
<td>
区分匹配策略、注入位置、最佳实践
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道字段注入的缺点
</td>
<td>
清楚构造器注入的优势和字段注入的问题
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到 Spring 4.3+ 的特性
</td>
<td>
知道省略 @Autowired 的版本特性
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
有编码规范意识，理解设计权衡
</td>
</tr>
</table>

---

#### 2、进阶题：Spring 的依赖注入底层是如何实现的？AutowiredAnnotationBeanPostProcessor 的工作原理？

**难度级别**：⭐⭐⭐（BeanPostProcessor、依赖解析、三级缓存）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- AutowiredAnnotationBeanPostProcessor 工作流程
- 依赖解析完整链路
- 关键细节
- 注册阶段：实现了 MergedBeanDefinitionPostProcessor，在 Bean 定义合并后（postProcessMergedBeanDefinition）...
- 注入阶段：实现了 InstantiationAwareBeanPostProcessor，在 Bean 实例化后、属性填充前（postProcessProperties）执行注...
- 懒加载支持：@Lazy 注解会生成代理对象，延迟到实际使用时才注入真实 Bean。

**2️⃣ Impressive Answer**
1. **AutowiredAnnotationBeanPostProcessor 工作流程**：
  - **注册阶段**：实现了 `MergedBeanDefinitionPostProcessor`，在 Bean 定义合并后（postProcessMergedBeanDefinition）扫描类中的 @Autowired、@Value、@Inject 注解，构建注入元数据（InjectionMetadata）缓存。
  - **注入阶段**：实现了 `InstantiationAwareBeanPostProcessor`，在 Bean 实例化后、属性填充前（postProcessProperties）执行注入逻辑。
1. **依赖解析完整链路**：

```
AutowiredAnnotationBeanPostProcessor.postProcessProperties()
→ 遍历 InjectionMetadata 中的注入点
→ DependencyDescriptor.resolveDependency()
→ DefaultListableBeanFactory.doResolveDependency()
→ 根据类型查找候选 Bean（findAutowireCandidates）
→ 如果有多个候选，按 @Qualifier、@Primary、优先级排序
→ 从三级缓存获取/创建 Bean
```
1. **关键细节**：
  - **懒加载支持**：@Lazy 注解会生成代理对象，延迟到实际使用时才注入真实 Bean。
  - **循环依赖处理**：构造器注入无法解决循环依赖（因为 Bean 还没创建），Setter/字段注入通过三级缓存解决。
  - **Optional 支持**：@Autowired + Optional<T> 允许依赖不存在时注入 Optional.empty()。
1. **Agent 场景**：LLM Provider 接口有多个实现（OpenAIProvider、ClaudeProvider、QwenProvider），通过 @Qualifier("openai") 或 @Primary 指定默认实现，避免 `NoUniqueBeanDefinitionException`。

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
只说了&quot;扫描注入&quot;
</td>
<td>
完整链路：注册→注入→依赖解析→三级缓存
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道两个 PostProcessor 接口
</td>
<td>
清楚 MergedBeanDefinition 和 InstantiationAware 的作用
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到 @Lazy 和 Optional
</td>
<td>
知道循环依赖的限制和解决方式
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道有这个类
</td>
<td>
理解依赖注入的完整生命周期
</td>
</tr>
</table>

---

#### 3、场景题：Agent 服务中有多个 LLM Provider 实现（OpenAI、Claude、通义千问），如何用 Spring 依赖注入实现策略模式动态切换？

**难度级别**：⭐⭐⭐（策略模式、@Conditional、动态切换、配置驱动）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 策略模式设计
- 动态切换方案二：配置驱动 + @Conditional
- 动态切换方案一：Map 注入
- 多租户场景

**2️⃣ Impressive Answer**
1. **策略模式设计**：

```java
// 统一接口
public interface LLMProvider {
    String chat(String prompt, String model);
}

// 多个实现
@Service("openai")
public class OpenAIProvider implements LLMProvider { ... }

@Service("claude")
public class ClaudeProvider implements LLMProvider { ... }

@Service("qwen")
public class QwenProvider implements LLMProvider { ... }
```
1. **动态切换方案一：Map 注入**（推荐）

```java
@Service
public class AgentService {
    private final Map<String, LLMProvider> providerMap;

    @Autowired
    public AgentService(Map<String, LLMProvider> providerMap) {
        this.providerMap = providerMap; // 自动注入所有实现，key = bean name
    }

    public String execute(String prompt, String providerName) {
        LLMProvider provider = providerMap.get(providerName);
        if (provider == null) {
            throw new IllegalArgumentException("Provider not found: " + providerName);
        }
        return provider.chat(prompt, getModel(providerName));
    }
}
```
1. **动态切换方案二：配置驱动 + @Conditional**

```yaml
agent:
  llm:
    provider: openai  # 动态切换
```

```java
@Configuration
public class LLMConfig {
    @Bean
    @ConditionalOnProperty(name = "agent.llm.provider", havingValue = "openai")
    public LLMProvider openaiProvider() { return new OpenAIProvider(); }

    @Bean
    @ConditionalOnProperty(name = "agent.llm.provider", havingValue = "claude")
    public LLMProvider claudeProvider() { return new ClaudeProvider(); }
}
```
1. **多租户场景**：不同租户使用不同 Provider，通过 ThreadLocal + Map 实现：

```java
@Service
public class TenantLLMProvider {
    private final Map<String, LLMProvider> providerMap;

    public String chat(String prompt) {
        String tenantId = TenantContext.getTenantId();
        String providerName = tenantConfigService.getProvider(tenantId);
        return providerMap.get(providerName).chat(prompt);
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
只说了接口+实现
</td>
<td>
Map 注入、配置驱动、多租户三种方案
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Map 自动注入机制
</td>
<td>
清楚 Spring 的 Map/List 自动注入特性
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有多租户场景
</td>
<td>
有生产环境多租户隔离经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用策略模式
</td>
<td>
有动态切换和多租户的完整方案
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
@Qualifier 和 @Primary 的区别是什么？
</td>
<td>
多个 Bean 时的冲突解决策略
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Spring 如何解决循环依赖？
</td>
<td>
依赖注入的边界情况
</td>
<td>
答：三级缓存的核心作用；一级缓存 singletonObjects：存放完全初始化好的 Bean（实例化+属性填充+初始化完成）。；二级缓存 earlySingletonObjects：存放提前暴露的半成品 Bean（已实例化但未填充属性），用于解决循环依赖。；三级缓存 singletonFactories：存放 ObjectFactory 工厂，用于生成提前暴露的 Bean，关键是可能生成 AOP 代理对象。
</td>
</tr>
<tr>
<td>
@Lazy 注解的作用是什么？
</td>
<td>
延迟注入和循环依赖的解决方案
</td>
<td>
答：一级缓存：成品 Bean；二级缓存：早期暴露的 Bean（未填充属性）；三级缓存：ObjectFactory，用于生成 AOP 代理的早期引用
</td>
</tr>
</table>

---

### 3.7 Spring Cache 缓存抽象

#### 1、基础题：Spring Cache 的 @Cacheable、@CachePut、@CacheEvict 分别有什么作用？

**难度级别**：⭐⭐（缓存注解、缓存策略、key 生成）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三个核心注解
- 关键参数
- 使用示例
- @Cacheable：先查缓存，命中则直接返回，不命中则执行方法并将结果存入缓存。适用于读多写少的查询方法。
- @CachePut：每次都执行方法，然后将结果存入缓存（覆盖旧值）。适用于需要更新缓存的写操作。
- @CacheEvict：删除缓存（可以指定 key 或 allEntries=true 清空整个缓存区）。适用于删除或更新操作，保证数据一致性。

**2️⃣ Impressive Answer**
1. **三个核心注解**：
  - **@Cacheable**：先查缓存，命中则直接返回，不命中则执行方法并将结果存入缓存。适用于读多写少的查询方法。
  - **@CachePut**：**每次都执行方法**，然后将结果存入缓存（覆盖旧值）。适用于需要更新缓存的写操作。
  - **@CacheEvict**：删除缓存（可以指定 key 或 allEntries=true 清空整个缓存区）。适用于删除或更新操作，保证数据一致性。
1. **关键参数**：
  - `value/cacheNames`：指定缓存区名称（如 "users"、"tools"）。
  - `key`：缓存 key 的 SpEL 表达式（如 `#userId`、`#user.id`），默认是方法参数。
  - `condition`：满足条件才缓存（如 `condition = "#userId > 1000"`）。
  - `unless`：不满足条件才缓存（如 `unless = "#result == null"`）。
1. **使用示例**：

```java
@Cacheable(value = "users", key = "#userId", unless = "#result == null")
public User getUser(Long userId) { ... }

@CachePut(value = "users", key = "#user.id")
public User updateUser(User user) { ... }

@CacheEvict(value = "users", key = "#userId")
public void deleteUser(Long userId) { ... }

@Caching(evict = {
    @CacheEvict(value = "users", key = "#userId"),
    @CacheEvict(value = "userOrders", allEntries = true)
})
public void deleteUserAndOrders(Long userId) { ... }
```
1. **注意事项**：@Cacheable 和 @CachePut 不能用在同一个类的方法上互相调用（因为 Spring AOP 代理限制，内部调用不会触发缓存逻辑）。

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
简单描述三个注解
</td>
<td>
包含关键参数、SpEL 表达式、@Caching 组合
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道内部调用不生效
</td>
<td>
清楚 AOP 代理限制和解决方案
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有具体代码示例
</td>
<td>
有完整的 CRUD 缓存示例
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
有生产环境缓存实践经验
</td>
</tr>
</table>

---

#### 2、进阶题：Spring Cache 的底层抽象是什么？如何集成 Redis 作为缓存后端？CacheManager 的工作原理？

**难度级别**：⭐⭐⭐（Cache 接口、CacheManager、序列化、过期策略）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 核心抽象
- 集成 Redis 完整配置
- CacheManager 工作原理
- 序列化选择
- Cache 接口：定义缓存的基本操作（get、put、evict、clear），实现类有 ConcurrentMapCache（本地内存）、RedisCache（Redis）、...
- CacheManager 接口：管理多个 Cache 实例，根据 cacheName 获取对应的 Cache。

**2️⃣ Impressive Answer**
1. **核心抽象**：
  - **Cache 接口**：定义缓存的基本操作（get、put、evict、clear），实现类有 `ConcurrentMapCache`（本地内存）、`RedisCache`（Redis）、`CaffeineCache`（Caffeine）。
  - **CacheManager 接口**：管理多个 Cache 实例，根据 cacheName 获取对应的 Cache。
1. **集成 Redis 完整配置**：

```java
@Configuration
@EnableCaching
public class CacheConfig {
    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))  // 默认过期时间
            .serializeKeysWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJackson2JsonRedisSerializer()));

        Map<String, RedisCacheConfiguration> cacheConfigurations = new HashMap<>();
        cacheConfigurations.put("users", config.entryTtl(Duration.ofHours(1)));
        cacheConfigurations.put("tools", config.entryTtl(Duration.ofMinutes(10)));

        return RedisCacheManager.builder(factory)
            .cacheDefaults(config)
            .withInitialCacheConfigurations(cacheConfigurations)
            .transactionAware()  // 支持事务，事务回滚时清除缓存
            .build();
    }
```
1. **CacheManager 工作原理**：
  - 启动时根据 @Cacheable 的 value/cacheNames 创建对应的 Cache 实例。
  - 运行时根据 cacheName 从 CacheManager 获取 Cache，然后执行缓存操作。
  - RedisCache 的 key 生成规则：`缓存区名::实际key`（如 `users::1001`）。
1. **序列化选择**：
  - **StringRedisSerializer**：key 序列化，可读性好。
  - **GenericJackson2JsonRedisSerializer**：value 序列化，支持对象类型信息（但会存储 @class 字段）。
  - **Jackson2JsonRedisSerializer**：value 序列化，不存储类型信息（需要指定 Class）。
1. **Agent 场景**：工具调用结果缓存时，key 使用 `toolName::hash(params)`（参数哈希避免 key 过长），value 使用 JSON 序列化，过期时间根据工具特性设置（如天气 10 分钟，搜索 1 小时）。

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
只说了引入依赖
</td>
<td>
完整配置：TTL、序列化、多缓存区、事务支持
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 key 生成规则
</td>
<td>
清楚 Redis 的 key 命名和序列化选择
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到过期策略
</td>
<td>
有不同缓存区的差异化 TTL 配置
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 Redis 缓存
</td>
<td>
有生产环境缓存架构设计能力
</td>
</tr>
</table>

---

#### 3、场景题：Agent 的工具调用结果需要缓存（相同参数的工具调用直接返回缓存），如何用 Spring Cache 实现并设置合理的过期策略？

**难度级别**：⭐⭐⭐（参数哈希、TTL 策略、缓存穿透、降级）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 工具调用缓存设计
- 差异化 TTL 策略（根据工具特性）
- 差异化 TTL 策略
- 防止缓存穿透
- 缓存降级
- 监控与告警

**2️⃣ Impressive Answer**
1. **工具调用缓存设计**：

```java
@Service
public class ToolExecutor {

    @Cacheable(
        value = "toolResults",
        key = "#toolName + '::' + #params.hashCode()",
        unless = "#result == null || #result.error != null"
    )
    public ToolResult executeTool(String toolName, Map<String, Object> params) {
        // 调用外部工具 API
    }

    @CacheEvict(value = "toolResults", key = "#toolName + '::' + #params.hashCode()")
    public void invalidateTool(String toolName, Map<String, Object> params) {
        // 手动清除缓存
    }
}
```
1. **差异化 TTL 策略**（根据工具特性）：

```java
@Bean
public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
    Map<String, RedisCacheConfiguration> configs = new HashMap<>();

    // 天气工具：数据变化快，短 TTL
    configs.put("weather", config.entryTtl(Duration.ofMinutes(10)));

    // 搜索工具：数据相对稳定，长 TTL
    configs.put("search", config.entryTtl(Duration.ofHours(1)));

    // 知识库查询：数据稳定，超长 TTL
    configs.put("kb", config.entryTtl(Duration.ofHours(24)));

    // 计算工具：结果不变，永久缓存
    configs.put("calculator", config.entryTtl(Duration.ofDays(7)));

    return RedisCacheManager.builder(factory)
        .withInitialCacheConfigurations(configs)
        .build();
}
```
1. **防止缓存穿透**：工具调用失败时不缓存（unless 条件），避免缓存空值导致后续请求一直失败。
1. **缓存降级**：Redis 不可用时降级到本地缓存（Caffeine），保证服务可用性：

```java
@Configuration
public class CacheConfig {
    @Bean
    @Primary
    public CacheManager compositeCacheManager(
            RedisCacheManager redisCacheManager,
            CaffeineCacheManager caffeineCacheManager) {
        return new CompositeCacheManager(
            caffeineCacheManager,  // 本地缓存优先
            redisCacheManager      // Redis 缓存
        );
    }
}
```
1. **监控与告警**：通过 Micrometer 暴露 `cache.hits`、`cache.misses`、`cache.puts` 指标，计算缓存命中率；设置告警（命中率 < 60% 时检查 TTL 策略）。

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
只说了 @Cacheable
</td>
<td>
参数哈希→差异化 TTL→防穿透→降级→监控
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道参数哈希和缓存穿透
</td>
<td>
清楚缓存设计的完整链路
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有差异化 TTL 和降级
</td>
<td>
有生产环境多级缓存和监控经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用基础缓存
</td>
<td>
有完整的缓存架构设计能力
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
Redis 的持久化机制（RDB、AOF）是什么？
</td>
<td>
缓存后端的数据可靠性
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
如何解决缓存雪崩、缓存击穿、缓存穿透？
</td>
<td>
缓存三大经典问题
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
Spring @Transactional 和缓存如何配合？
</td>
<td>
事务回滚时缓存一致性问题
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
</table>

---

### 3.8 Spring 异步编程

#### 1、基础题：@Async 注解如何使用？需要哪些前置配置？

**难度级别**：⭐⭐（@EnableAsync、线程池配置、返回值）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 前置配置
- 自定义线程池配置
- 使用方式
- 注意事项
- 在启动类或配置类上加 @EnableAsync 注解。
- 配置线程池（可选，默认使用 SimpleAsyncTaskExecutor，每次创建新线程，不推荐）。

**2️⃣ Impressive Answer**
1. **前置配置**：
  - 在启动类或配置类上加 `@EnableAsync` 注解。
  - 配置线程池（可选，默认使用 `SimpleAsyncTaskExecutor`，每次创建新线程，不推荐）。
1. **自定义线程池配置**：

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("taskExecutor")
    public ThreadPoolTaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);      // 核心线程数
        executor.setMaxPoolSize(50);       // 最大线程数
        executor.setQueueCapacity(200);    // 队列容量
        executor.setKeepAliveSeconds(60);  // 空闲线程存活时间
        executor.setThreadNamePrefix("async-");
        executor.setRejectedExecutionHandler(
            new ThreadPoolExecutor.CallerRunsPolicy());  // 拒绝策略
        executor.initialize();
        return executor;
    }
}
```
1. **使用方式**：

```java
@Service
public class AsyncService {

    @Async("taskExecutor")  // 指定线程池
    public void asyncMethod() {
        // 异步执行
    }

    @Async
    public CompletableFuture<String> asyncWithReturn() {
        return CompletableFuture.completedFuture("result");
    }
}
```
1. **注意事项**：
  - @Async 不能用在同一个类的方法上互相调用（AOP 代理限制）。
  - 异步方法的异常无法被调用方捕获，需要通过 `AsyncUncaughtExceptionHandler` 处理。
  - 返回 `CompletableFuture` 可以链式调用和组合多个异步任务。

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
只说了加注解
</td>
<td>
完整配置：@EnableAsync→线程池→使用方式→注意事项
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道默认线程池的问题
</td>
<td>
清楚 SimpleAsyncTaskExecutor 的缺陷
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有线程池参数配置
</td>
<td>
有生产环境线程池调优经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 @Async
</td>
<td>
有异步编程的完整实践经验
</td>
</tr>
</table>

---

#### 2、进阶题：@Async 的底层实现原理是什么？如何自定义线程池？异步方法的异常如何处理？

**难度级别**：⭐⭐⭐（AOP 代理、AsyncAnnotationBeanPostProcessor、异常处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 底层实现原理
- 线程池选择策略
- 异常处理机制
- @EnableAsync 导入 AsyncConfigurationSelector，注册 ProxyAsyncConfiguration。
- AsyncAnnotationBeanPostProcessor 扫描 @Async 注解，为 Bean 创建 AOP 代理。
- 代理拦截器 AnnotationAsyncExecutionInterceptor 将方法调用提交到线程池执行。

**2️⃣ Impressive Answer**
1. **底层实现原理**：
  - `@EnableAsync` 导入 `AsyncConfigurationSelector`，注册 `ProxyAsyncConfiguration`。
  - `AsyncAnnotationBeanPostProcessor` 扫描 @Async 注解，为 Bean 创建 AOP 代理。
  - 代理拦截器 `AnnotationAsyncExecutionInterceptor` 将方法调用提交到线程池执行。
1. **线程池选择策略**：
  - 如果 @Async 指定了线程池名称，使用指定的线程池。
  - 如果未指定，查找名为 `taskExecutor` 的 `TaskExecutor` Bean。
  - 如果没有，使用默认的 `SimpleAsyncTaskExecutor`（每次创建新线程）。
1. **异常处理机制**：
  - **无返回值方法**：异常无法被调用方捕获，需要全局处理器：

```java
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) -> {
            log.error("Async method error: {}", method.getName(), ex);
            // 发送告警、记录日志等
        };
    }
}
```
- **有返回值方法**：异常封装在 `CompletableFuture` 中，调用方通过 `exceptionally()` 处理：

```java
@Async
public CompletableFuture<String> asyncMethod() {
    return CompletableFuture.supplyAsync(() -> {
        throw new RuntimeException("error");
    });
}

// 调用方
asyncMethod()
    .exceptionally(ex -> {
        log.error("Error", ex);
        return "fallback";
    });
```
1. **事务与异步**：@Async 和 @Transactional 不能同时用在同一个方法上（异步方法在新线程执行，事务上下文丢失）。如果需要事务，在异步方法内部调用的方法上加 @Transactional。

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
只说了 AOP
</td>
<td>
完整链路：注解→配置→代理→拦截器→线程池
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道异常处理的两种方式
</td>
<td>
清楚无返回值和有返回值的异常处理差异
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到事务问题
</td>
<td>
知道 @Async 和 @Transactional 的冲突
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 @Async
</td>
<td>
理解异步编程的底层机制和边界情况
</td>
</tr>
</table>

---

#### 3、场景题：Agent 并行调用多个工具（如同时查询天气、搜索知识库、查询数据库），如何用 @Async + CompletableFuture 实现并行工具调用？

**难度级别**：⭐⭐⭐（并行执行、超时控制、结果聚合、异常处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 异步工具调用设计
- 并行调用与结果聚合
- 线程池配置（工具调用场景）

**2️⃣ Impressive Answer**
1. **异步工具调用设计**：

```java
@Service
public class AgentToolService {

    @Async("toolExecutor")
    public CompletableFuture<ToolResult> queryWeather(Map<String, Object> params) {
        WeatherResult result = weatherService.query(params);
        return CompletableFuture.completedFuture(result);
    }

    @Async("toolExecutor")
    public CompletableFuture<ToolResult> searchKb(Map<String, Object> params) {
        SearchResult result = kbService.search(params);
        return CompletableFuture.completedFuture(result);
    }

    @Async("toolExecutor")
    public CompletableFuture<ToolResult> queryDatabase(Map<String, Object> params) {
        DbResult result = dbService.query(params);
        return CompletableFuture.completedFuture(result);
    }
}
```
1. **并行调用与结果聚合**：

```java
@Service
public class AgentExecutor {

    public List<ToolResult> executeParallel(List<ToolCall> calls) {
        List<CompletableFuture<ToolResult>> futures = calls.stream()
            .map(call -> switch (call.getType()) {
                case "weather" -> toolService.queryWeather(call.getParams())
                    .exceptionally(ex -> ToolResult.error(ex));
                case "kb" -> toolService.searchKb(call.getParams())
                    .exceptionally(ex -> ToolResult.error(ex));
                case "db" -> toolService.queryDatabase(call.getParams())
                    .exceptionally(ex -> ToolResult.error(ex));
                default -> CompletableFuture.completedFuture(ToolResult.error("Unknown type"));
            })
            .toList();

        // 等待所有任务完成（带超时）
        CompletableFuture<Void> allOf = CompletableFuture.allOf(
            futures.toArray(new CompletableFuture[0])
        );

        try {
            allOf.get(30, TimeUnit.SECONDS);  // 30 秒超时
        } catch (TimeoutException e) {
            log.warn("Tool execution timeout");
            futures.forEach(f -> f.cancel(true));
        }

        // 收集结果
        return futures.stream()
            .map(CompletableFuture::join)
            .toList();
    }
}
```
1. **线程池配置**（工具调用场景）：

```java
@Bean("toolExecutor")
public ThreadPoolTaskExecutor toolExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(20);      // 核心线程数（根据工具数量）
    executor.setMaxPoolSize(100);      // 最大线程数（峰值并发）
    executor.setQueueCapacity(500);    // 队列容量
    executor.setKeepAliveSeconds(120); // 空闲线程存活时间
    executor.setThreadNamePrefix("tool-async-");
    executor.setRejectedExecutionHandler(
        new ThreadPoolExecutor.CallerRunsPolicy());
    executor.initialize();
    return executor;
}
```
1. **超时与降级**：使用 `orTimeout` 设置单个工具超时，使用 ` exceptionally` 提供降级结果：

```java
@Async("toolExecutor")
public CompletableFuture<ToolResult> queryWeatherWithTimeout(Map<String, Object> params) {
    return CompletableFuture.supplyAsync(() -> {
        return weatherService.query(params);
    }, taskExecutor)
    .orTimeout(10, TimeUnit.SECONDS)  // 单个工具 10 秒超时
    .exceptionally(ex -> ToolResult.fallback("Weather service unavailable"));
}
```
1. **监控与告警**：通过 Micrometer 暴露 `async.task.duration`、`async.task.success`、`async.task.failure` 指标；设置告警（失败率 > 5% 时检查工具可用性）。

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
只说了 @Async + allOf
</td>
<td>
完整方案：异步方法→并行调用→超时→降级→监控
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道超时控制和降级
</td>
<td>
清楚 CompletableFuture 的链式调用和异常处理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有线程池参数配置
</td>
<td>
有生产环境并发调优经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用异步编程
</td>
<td>
有完整的并发编程和容错方案
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
CompletableFuture 的常用方法有哪些？
</td>
<td>
异步编程的核心 API
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：异步编程的核心 API，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
线程池的拒绝策略有哪些？
</td>
<td>
高并发场景下的资源管理
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：高并发场景下的资源管理，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何实现异步任务的链式调用和组合？
</td>
<td>
复杂业务场景的异步编排
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：复杂业务场景的异步编排，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

### 4.3 AOP 原理

#### 4、进阶题：Spring AOP 的两种代理方式（JDK 动态代理 vs CGLIB）有什么区别？

**难度级别**：⭐⭐⭐（接口代理 vs 类代理、ASM 字节码、自调用失效问题、@Transactional 失效场景）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 代理机制不同
- Spring 的选择策略
- 自调用失效是核心陷阱
- @Transactional 失效场景

**2️⃣ Impressive Answer**
1. **代理机制不同**：JDK 动态代理基于接口，运行时通过反射生成代理类，要求目标类必须实现接口；CGLIB 通过 ASM 字节码框架生成目标类的子类，不依赖接口，但 final 类/方法无法代理。
1. **Spring 的选择策略**：Spring Boot 2.x 起默认优先使用 CGLIB（`spring.aop.proxy-target-class=true`），减少因没有接口导致代理失败的问题；也可以强制指定。
1. **自调用失效是核心陷阱**：同一个 Bean 内部方法 A 调用方法 B，B 上的 AOP 不生效，因为调用绕过了代理对象，直接走 `this`；解决方案是注入自身代理（`AopContext.currentProxy()`）或拆分到另一个 Bean。
1. **@Transactional 失效场景**：private 方法不能被 CGLIB 子类重写，方法必须是 public 且非 final；另外同类自调用也会导致事务失效。

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
只说了表面区别，没有逻辑层次
</td>
<td>
分四点，机制→策略→陷阱→实战，层层递进
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Spring Boot 2.x 默认 CGLIB
</td>
<td>
说出版本变化、ASM、AopContext 解决方案
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提自调用失效的解决方法
</td>
<td>
给出 AopContext 和拆 Bean 两种修复方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道区别但不知道坑
</td>
<td>
有踩坑经验，理解代理原理，能防患于未然
</td>
</tr>
</table>

---

#### 2、进阶题：Spring AOP 的完整执行链路是什么？ProxyFactory、PointcutAdvisor、MethodInterceptor 各自的角色？

**难度级别**：⭐⭐⭐（AOP 链路、核心组件、责任链模式）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 完整执行链路
- 核心组件角色
- 代码示例
- ProxyFactory：代理工厂，根据 Advisor 创建代理对象（JDK 或 CGLIB）。
- PointcutAdvisor：切面定义，包含 Pointcut（切点，匹配哪些方法）和 Advice（通知，做什么）。
- MethodInterceptor：方法拦截器，Advice 的实现，负责拦截方法调用（如 MethodBeforeAdviceInterceptor）。

**2️⃣ Impressive Answer**
1. **完整执行链路**：

```
调用代理方法
→ ReflectiveMethodInvocation.proceed()
→ 按顺序执行 Interceptor 链
  → ExposeInvocationInterceptor（暴露当前调用）
  → MethodBeforeAdvice（前置通知）
  → 目标方法
  → AfterReturningAdvice（后置通知）
  → AfterThrowingAdvice（异常通知）
  → AfterAdvice（最终通知）
→ 返回结果
```
1. **核心组件角色**：
  - **ProxyFactory**：代理工厂，根据 Advisor 创建代理对象（JDK 或 CGLIB）。
  - **PointcutAdvisor**：切面定义，包含 Pointcut（切点，匹配哪些方法）和 Advice（通知，做什么）。
  - **MethodInterceptor**：方法拦截器，Advice 的实现，负责拦截方法调用（如 `MethodBeforeAdviceInterceptor`）。
  - **AdvisedSupport**：持有所有 Advisor 和配置信息。
1. **责任链模式**：`ReflectiveMethodInvocation` 维护 interceptorList 和 currentIndex，`proceed()` 递归调用下一个拦截器。
1. **代码示例**：

```java
// AOP 执行链路示例
Proxy proxy = ProxyFactory.getProxy(classLoader, interfaces);
proxy.method() →
  ReflectiveMethodInvocation.proceed() →
    interceptor1.invoke() →
      interceptor2.invoke() →
        target.method() →
      interceptor2.invoke() →
    interceptor1.invoke() →
  result
```
1. **Agent 场景**：`ToolCallInterceptor` 拦截工具调用方法，记录耗时、捕获异常、重试逻辑。

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
只说了三个组件
</td>
<td>
完整链路+责任链模式+代码示例
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道责任链模式
</td>
<td>
清楚 ReflectiveMethodInvocation 的递归机制
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
有完整的执行流程图
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过组件名
</td>
<td>
理解 AOP 的完整执行机制
</td>
</tr>
</table>

---

#### 3、场景题：如何用 Spring AOP 实现 Agent 工具调用的统一耗时监控和异常捕获？

**难度级别**：⭐⭐⭐（自定义切面、注解驱动、异常处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 自定义注解
- 切面实现
- 使用示例
- 监控指标
- tool.call.duration：工具调用耗时（P50/P95/P99）
- tool.call.count：工具调用次数（成功/失败）

**2️⃣ Impressive Answer**
1. **自定义注解**：

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface ToolCall {
    String toolName() default "";
    int maxRetries() default 0;
}
```
1. **切面实现**：

```java
@Aspect
@Component
@Slf4j
public class ToolCallAspect {

    @Autowired
    private MeterRegistry meterRegistry;

    @Around("@annotation(toolCall)")
    public Object monitorToolCall(ProceedingJoinPoint pjp, ToolCall toolCall) throws Throwable {
        String toolName = toolCall.toolName().isEmpty()
            ? pjp.getSignature().getName()
            : toolCall.toolName();

        Timer.Sample sample = Timer.start(meterRegistry);
        long startTime = System.currentTimeMillis();

        try {
            // 重试逻辑
            int retries = toolCall.maxRetries();
            Throwable lastException = null;

            for (int i = 0; i <= retries; i++) {
                try {
                    Object result = pjp.proceed();

                    // 记录成功指标
                    sample.stop(Timer.builder("tool.call.duration")
                        .tag("tool", toolName)
                        .tag("status", "success")
                        .register(meterRegistry));

                    meterRegistry.counter("tool.call.count",
                        "tool", toolName, "status", "success").increment();

                    return result;
                } catch (Exception e) {
                    lastException = e;
                    if (i < retries) {
                        log.warn("Tool call failed, retrying {}/{}", i + 1, retries, e);
                        Thread.sleep(100 * (i + 1)); // 指数退避
                    }
                }
            }

            throw lastException;

        } catch (Throwable e) {
            // 记录失败指标
            sample.stop(Timer.builder("tool.call.duration")
                .tag("tool", toolName)
                .tag("status", "error")
                .register(meterRegistry));

            meterRegistry.counter("tool.call.count",
                "tool", toolName, "status", "error").increment();

            log.error("Tool call failed: {}", toolName, e);
            throw e;
        }
    }
}
```
1. **使用示例**：

```java
@Service
public class WeatherService {

    @ToolCall(toolName = "weather_query", maxRetries = 2)
    public WeatherResult queryWeather(String city) {
        // 调用天气 API
        return weatherApi.query(city);
    }
}
```
1. **监控指标**：
  - `tool.call.duration`：工具调用耗时（P50/P95/P99）
  - `tool.call.count`：工具调用次数（成功/失败）
  - 配合 Prometheus + Grafana 可视化监控

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
只说了 @Around
</td>
<td>
自定义注解+完整切面+重试逻辑+指标监控
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道指标监控
</td>
<td>
有 Micrometer + Prometheus 集成
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有重试逻辑
</td>
<td>
有指数退避重试和完整异常处理
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 AOP 但不深入
</td>
<td>
有生产环境完整的监控方案
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
Spring 事务 @Transactional 的实现原理？
</td>
<td>
AOP 的典型应用场景，考察对 AOP 的理解
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
<tr>
<td>
JDK 动态代理和 CGLIB 的性能对比？
</td>
<td>
代理方式的选择，和 AOP 代理创建相关
</td>
<td>
答：成本优化先拆 Token、模型、工具和重试四类开销，再用缓存、小模型路由、Prompt 压缩、批处理和限流降级优化。
</td>
</tr>
<tr>
<td>
@AspectJ 注解有哪些？各自的执行顺序？
</td>
<td>
AOP 切面编程的基础知识
</td>
<td>
答：顺序性通常靠同一业务 key 路由到同一分区保证；跨分区无法全局有序，只能做局部顺序或业务补偿。
</td>
</tr>
</table>

---

#### 4、场景题：Agent 的工具调用需要统一做鉴权和耗时日志，如何用 AOP 实现？

**难度级别**：⭐⭐⭐（自定义注解 + @Around、切点表达式、ProceedingJoinPoint、异常处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 定义标记注解
- @Around 统一拦截
- 鉴权逻辑
- 日志结构化

**2️⃣ Impressive Answer**
1. **定义标记注解**：自定义 `@ToolAuth(permission="xxx")`，标注在需要鉴权的工具方法上，便于精确切入，不污染无关方法。
1. **@Around 统一拦截**：用 `@Around("@annotation(toolAuth)")` 匹配注解，在 `ProceedingJoinPoint.proceed()` 前后分别做鉴权和耗时统计；用 `try-finally` 确保耗时日志必然记录，不受异常影响。
1. **鉴权逻辑**：proceed 前从上下文（ThreadLocal 或请求头）取 token，校验失败直接抛 `AuthException`，不执行工具；鉴权通过才放行。
1. **日志结构化**：记录工具名（`joinPoint.getSignature().getName()`）、入参摘要、耗时、是否成功，便于后续 tracing 关联；生产上配合 MDC 注入 traceId。

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
@Before/@After 分散，逻辑割裂
</td>
<td>
@Around 统一，try-finally 保证完整性
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道自定义注解切点的好处
</td>
<td>
注解驱动切点，精准、低侵入、易扩展
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有考虑异常时耗时丢失的问题
</td>
<td>
finally 块保证耗时必记，考虑到异常路径
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 AOP 但没有工程化意识
</td>
<td>
注解 + 切面 + 结构化日志，有生产落地思维
</td>
</tr>
</table>

---

#### 5、容易一起考的题

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
Spring 事务为什么在同类方法自调用时失效？
</td>
<td>
AOP 代理自调用失效的直接应用，考察对代理机制的深度理解
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
<tr>
<td>
BeanPostProcessor 和 AOP 的关系是什么？
</td>
<td>
AOP 代理本质上是通过 BeanPostProcessor 创建的，考察 Spring 扩展点体系
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@Transactional 和自定义 AOP 切面的执行顺序如何控制？
</td>
<td>
考察 @Order 注解和 Ordered 接口在多切面场景下的优先级控制
</td>
<td>
答：顺序性通常靠同一业务 key 路由到同一分区保证；跨分区无法全局有序，只能做局部顺序或业务补偿。
</td>
</tr>
</table>

---

### 4.4 @Transactional 失效场景

#### 1、基础题：@Transactional 注解有哪些常见的失效场景？

**难度级别**：⭐⭐（方法修饰符、异常类型、自调用、传播机制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 方法修饰符问题
- 异常类型问题
- 自调用问题
- 传播机制问题
- 事务管理器配置
- 数据库引擎不支持

**2️⃣ Impressive Answer**
1. **方法修饰符问题**：`@Transactional` 只能作用于 `public` 方法，`private`、`protected`、`package-private` 会失效（Spring AOP 代理限制）。
1. **异常类型问题**：默认只回滚 `RuntimeException` 和 `Error`，检查型异常（如 `IOException`）不回滚。需指定 `rollbackFor = Exception.class`。
1. **自调用问题**：同一个类内部方法调用不经过代理，事务失效。

```java
@Service
public class UserService {
    @Transactional
    public void methodA() {
        methodB(); // 事务失效，直接调用不经过代理
    }

    @Transactional
    public void methodB() { }
}
```

```
解决：注入自己或用 `AopContext.currentProxy()`。
```
1. **传播机制问题**：`NOT_SUPPORTED`、`NEVER` 会挂起当前事务；嵌套事务（`NESTED`）需要数据库支持（如 MySQL）。
1. **事务管理器配置**：多数据源时未指定 `@Transactional(transactionManager = "xxxTransactionManager")`。
1. **数据库引擎不支持**：如 MySQL 的 MyISAM 引擎不支持事务。

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
零散列举了几个
</td>
<td>
6 个场景，每个都有解释和解决方案
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道自调用原理
</td>
<td>
清楚代理机制导致自调用失效
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
有自调用问题的解决方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过场景
</td>
<td>
理解失效原理和解决方案
</td>
</tr>
</table>

---

#### 2、进阶题：Spring 事务的 7 种传播机制分别是什么？REQUIRED 和 REQUIRES_NEW 的区别？

**难度级别**：⭐⭐⭐（传播机制、事务隔离、嵌套事务）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 7 种传播机制
- REQUIRED vs REQUIRES_NEW
- 嵌套事务（NESTED）场景
- Agent 场景
- REQUIRED：（默认）：如果当前有事务，加入；否则新建。
- REQUIRES_NEW：总是新建事务，挂起当前事务。

**2️⃣ Impressive Answer**
1. **7 种传播机制**：
  - **REQUIRED**（默认）：如果当前有事务，加入；否则新建。
  - **REQUIRES_NEW**：总是新建事务，挂起当前事务。
  - **SUPPORTS**：如果当前有事务，加入；否则非事务执行。
  - **NOT_SUPPORTED**：总是非事务执行，挂起当前事务。
  - **MANDATORY**：必须当前有事务，否则抛异常。
  - **NEVER**：必须非事务执行，否则抛异常。
  - **NESTED**：嵌套事务，当前有事务时创建 savepoint，失败回滚到 savepoint。
1. **REQUIRED vs REQUIRES_NEW**：
  - **REQUIRED**：加入外层事务，内外层一起提交或回滚。
  - **REQUIRES_NEW**：独立事务，外层失败不影响内层，内层失败不影响外层（除非异常传播）。
1. **嵌套事务（NESTED）场景**：

```java
@Transactional
public void outer() {
    try {
        inner(); // 嵌套事务，失败只回滚 inner
    } catch (Exception e) {
        // outer 可以继续执行
    }
}

@Transactional(propagation = Propagation.NESTED)
public void inner() {
    // 失败回滚到 savepoint
}
```
1. **Agent 场景**：
  - **REQUIRED**：Agent 执行流程（工具调用→结果存储→状态更新）在一个事务中，保证一致性。
  - **REQUIRES_NEW**：记录审计日志（即使主流程失败，日志也要记录）。
  - **NESTED**：批量处理工具调用，单个失败不影响其他。

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
只说了两个传播机制
</td>
<td>
7 种传播机制+对比+嵌套事务示例
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 NESTED 的 savepoint 机制
</td>
<td>
清楚嵌套事务的回滚机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有场景应用
</td>
<td>
有 Agent 事务边界设计
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过传播机制
</td>
<td>
理解传播机制的实际应用
</td>
</tr>
</table>

---

#### 3、场景题：Agent 执行多步骤任务（工具调用→结果存储→状态更新），如何设计事务边界保证数据一致性？

**难度级别**：⭐⭐⭐（事务边界设计、异常处理、补偿机制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 方案一：单事务（简单场景）
- 方案二：独立事务 + 补偿（复杂场景）
- 方案三：Saga 模式（长流程）
- 选型建议
- 单事务：所有操作在同一个数据库，简单场景
- 独立事务：涉及外部调用，需要部分成功

**2️⃣ Impressive Answer**
1. **方案一：单事务（简单场景）**

```java
@Service
public class AgentExecutor {

    @Transactional(rollbackFor = Exception.class)
    public AgentResult execute(AgentRequest request) {
        // 1. 工具调用
        ToolResult toolResult = toolCallService.call(request.getTool());

        // 2. 结果存储
        executionRepository.save(toolResult);

        // 3. 状态更新
        agentRepository.updateStatus(request.getAgentId(), "COMPLETED");

        return AgentResult.success(toolResult);
    }
}
```
1. **方案二：独立事务 + 补偿（复杂场景）**

```java
@Service
public class AgentExecutor {

    @Transactional(rollbackFor = Exception.class)
    public AgentResult execute(AgentRequest request) {
        ToolResult toolResult = null;

        try {
            // 1. 工具调用（可能调用外部服务，不放在事务中）
            toolResult = toolCallService.call(request.getTool());

            // 2. 结果存储（独立事务）
            saveExecution(toolResult);

            // 3. 状态更新（独立事务）
            updateAgentStatus(request.getAgentId(), "COMPLETED");

            return AgentResult.success(toolResult);

        } catch (Exception e) {
            // 补偿：回滚状态
            updateAgentStatus(request.getAgentId(), "FAILED");
            throw e;
        }
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void saveExecution(ToolResult result) {
        executionRepository.save(result);
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void updateAgentStatus(String agentId, String status) {
        agentRepository.updateStatus(agentId, status);
    }
}
```
1. **方案三：Saga 模式（长流程）**

```java
@Service
public class AgentSaga {

    public AgentResult execute(AgentRequest request) {
        List<SagaStep> steps = Arrays.asList(
            new ToolCallStep(request),
            new SaveExecutionStep(),
            new UpdateStatusStep("COMPLETED")
        );

        return sagaExecutor.execute(steps, new AgentCompensation(request));
    }
}

// 补偿操作
public class AgentCompensation implements Compensable {
    public void compensate(AgentRequest request) {
        updateAgentStatus(request.getAgentId(), "FAILED");
        deleteExecution(request.getExecutionId());
    }
}
```
1. **选型建议**：
  - 单事务：所有操作在同一个数据库，简单场景
  - 独立事务：涉及外部调用，需要部分成功
  - Saga：长流程、多服务、需要补偿机制

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
只说了单事务
</td>
<td>
三种方案+完整代码+选型建议
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Saga 模式
</td>
<td>
清楚不同场景的事务边界设计
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有补偿机制
</td>
<td>
有完整的补偿和回滚策略
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 @Transactional
</td>
<td>
有分布式事务设计能力
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
Spring 事务隔离级别有哪些？
</td>
<td>
事务并发控制，和事务传播机制配套
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
<tr>
<td>
数据库事务的 ACID 特性？
</td>
<td>
事务理论基础，理解事务的必要性
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
<tr>
<td>
分布式事务解决方案有哪些？
</td>
<td>
跨服务事务，和事务边界设计相关
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
</table>

---

#### 6、进阶题：BeanPostProcessor 和 BeanFactoryPostProcessor 的区别？各自的典型应用场景？

**难度级别**：⭐⭐⭐（扩展点体系、Bean 定义修改 vs 实例增强、AOP 代理创建时机）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 作用时机不同
- 定义加载完成后、实例化之前
- 实例化之后、初始化前后
- 典型应用
- AOP 代理创建时机
- 使用注意

**2️⃣ Impressive Answer**
1. **作用时机不同**：`BeanFactoryPostProcessor` 在 Bean **定义加载完成后、实例化之前**执行，操作的是 `BeanDefinition`（元数据）；`BeanPostProcessor` 在 Bean **实例化之后、初始化前后**执行，操作的是 Bean 实例本身。
1. **典型应用**：`BeanFactoryPostProcessor` 的经典实现是 `PropertySourcesPlaceholderConfigurer`，负责解析 `${}` 占位符替换配置值；`BeanPostProcessor` 的经典实现是 `AutowiredAnnotationBeanPostProcessor`（处理 @Autowired 注入）和 `AbstractAutoProxyCreator`（创建 AOP 代理）。
1. **AOP 代理创建时机**：AOP 代理是在 `BeanPostProcessor.postProcessAfterInitialization()` 阶段创建的，这就是为什么 `BeanFactoryPostProcessor` 中注入的 Bean 不会被 AOP 代理——它们在代理创建之前就已经实例化了。
1. **使用注意**：`BeanFactoryPostProcessor` 中不要提前触发 Bean 实例化（如 getBean()），否则这些 Bean 会跳过后续的 BeanPostProcessor 处理链，导致注入、AOP 等功能失效。

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
只说了&quot;前后处理&quot;，没有区分操作对象
</td>
<td>
清晰区分：操作 BeanDefinition vs 操作 Bean 实例
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 AOP 代理的创建时机
</td>
<td>
能解释为什么 BeanFactoryPostProcessor 中的 Bean 不被代理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到具体实现类
</td>
<td>
举出 PropertySourcesPlaceholderConfigurer、AutowiredAnnotationBeanPostProcessor 等经典实现
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道有两个扩展点
</td>
<td>
理解 Spring 容器启动的完整生命周期，能避免扩展点误用
</td>
</tr>
</table>

---

#### 7、场景题：如何实现一个自定义注解，让 Agent 的工具方法自动注册到工具列表中？

**难度级别**：⭐⭐⭐（自定义 BeanPostProcessor + 注解扫描 + 注册表模式）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- BeanPostProcessor 自动扫描
- 定义工具注解
- 参数自动提取
- 生产级考虑

**2️⃣ Impressive Answer**
1. **定义工具注解**：`@AgentTool(name="search", description="搜索工具")`，标注在方法上，携带工具名称和描述信息，用于生成 Function Definition 给模型。
1. **BeanPostProcessor 自动扫描**：

```java
@Component
public class AgentToolRegistrar implements BeanPostProcessor {
    private final ToolRegistry registry;@
    Overridepublic Object postProcessAfterInitialization(Object bean, String beanName) {
        for(Method method: bean.getClass().getDeclaredMethods()) {
            AgentTool annotation = method.getAnnotation(AgentTool.class);
            if(annotation != null) {
                ToolDefinition definition = ToolDefinition.builder().name(annotation.name()).description(annotation.description()).parameters(extractParameters(method)).executor((args) - > ReflectionUtils.invokeMethod(method, bean, args)).build();
                registry.register(definition);
            }
        }
        return bean;
    }
}
```

```

```
1. **参数自动提取**：通过反射读取方法参数的类型和 `@Param` 注解，自动生成 JSON Schema，减少手动维护成本。
1. **生产级考虑**：加 `@Order(Ordered.LOWEST_PRECEDENCE)` 确保在 AOP 代理之后执行（扫描的是代理后的 Bean）；工具注册表支持热更新，配合配置中心动态启停工具。

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
思路正确但缺少细节
</td>
<td>
注解定义→扫描注册→参数提取→生产考虑，完整链路
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道扫描时机和 AOP 的关系
</td>
<td>
明确 @Order 保证在代理之后扫描
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
只说了 Map 存储
</td>
<td>
有 ToolDefinition 结构化设计和反射调用
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 BeanPostProcessor
</td>
<td>
能设计完整的工具注册框架，有架构能力
</td>
</tr>
</table>

---

### 2.3 Spring 事务管理

#### 1、基础题：@Transactional 注解的作用是什么？Spring 事务的传播机制有哪些？

**难度级别**：⭐⭐（事务边界、PROPAGATION\_REQUIRED、PROPAGATION\_REQUIRES\_NEW、隔离级别）

**Answer**

@Transactional 是 Spring 声明式事务的核心注解，标记在方法或类上，Spring 会通过 AOP 代理在方法执行前后自动开启/提交/回滚事务。

**传播机制（8 种）**：
- **REQUIRED**（默认）：当前有事务就加入，没有就新建
- **REQUIRES\_NEW**：不管有没有事务，都新建一个（当前事务会被挂起）
- **SUPPORTS**：有事务就加入，没有就以非事务方式执行
- **NOT\_SUPPORTED**：以非事务方式执行，如果有事务就挂起
- **MANDATORY**：必须有事务，否则抛异常
- **NEVER**：必须没有事务，否则抛异常
- **NESTED**：嵌套事务，基于 Savepoint 实现，可部分回滚

**隔离级别**：DEFAULT（数据库默认）、READ\_UNCOMMITTED、READ\_COMMITTED、REPEATABLE\_READ、SERIALIZABLE

---

#### 2、进阶题：@Transactional 在什么情况下会失效？

**难度级别**：⭐⭐⭐⭐（自调用、非 public 方法、异常类型、代理机制、异步方法）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 自调用失效（最常见）
- 访问权限限制
- 异常类型不匹配
- 捕获异常未抛出
- 异步方法失效

**2️⃣ Impressive Answer**

我从 5 个维度梳理@Transactional 失效场景：
1. **自调用失效（最常见）**：同一个 Bean 内部方法 A 调用带@Transactional 的方法 B，B 的事务不生效。原因：AOP 代理对象才是事务载体，自调用走的是 `this.B()`，绕过了代理。解决：注入自身代理调用，或用 `AopContext.currentProxy()`。
1. **访问权限限制**：@Transactional 只能标注在 public 方法上。protected/private 方法即使加上也不会生效，因为 Spring AOP 默认只代理 public 方法。
1. **异常类型不匹配**：默认只回滚 RuntimeException 和 Error。如果抛的是受检异常（Checked Exception），需要显式指定 `@Transactional(rollbackFor = Exception.class)`。
1. **捕获异常未抛出**：方法内部 try-catch 把异常吞了，事务管理器感知不到异常，自然不会回滚。解决：catch 后手动调用 `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`。
1. **异步方法失效**：@Async 方法的事务 propagation 可能不符合预期，因为异步方法在另一个线程执行，事务上下文无法传递。解决：在异步方法上单独加@Transactional。

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
覆盖面
</td>
<td>
只说了 3 种常见情况
</td>
<td>
系统梳理 5 大类失效场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
知道现象但说不清原理
</td>
<td>
每个场景都解释根本原因
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有给出解决方案
</td>
<td>
每个失效都有对应的修复方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
踩过一些坑但不系统
</td>
<td>
有系统性总结，能预判和规避问题
</td>
</tr>
</table>

---

#### 3、场景题：Agent 执行多步工具调用，如何保证部分失败时数据一致性？

**难度级别**：⭐⭐⭐⭐（分布式事务、Saga 模式、补偿机制、本地事务表）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 长事务 + 跨服务
- 本地事务兜底
- 事务消息表
- 跨服务 Saga 模式
- 幂等 + 重试
- 本地消息表 + 事务性轮询

**2️⃣ Impressive Answer**

这个问题本质是**长事务 + 跨服务**的场景，我分三层设计：
1. **本地事务兜底**：单服务内多步操作（如写 DB + 发消息）用 `@Transactional` 保证原子性；消息发送用**事务消息表**，本地事务提交后由定时任务异步投递，保证最终一致。
1. **跨服务 Saga 模式**：Agent 多步工具调用涉及多个微服务时，用 Saga 编排：每个步骤有正向操作和补偿操作，步骤 3 失败则逆向执行步骤 2→1 的补偿。Spring Cloud State Machine 或自研引擎可实现。
1. **幂等 + 重试**：每个工具调用设计幂等性（唯一键/状态机），失败后安全重试；配合**本地消息表 + 事务性轮询**，确保补偿操作必然执行。
1. **用户感知设计**：长事务不阻塞 HTTP 响应，采用异步回调或 SSE 推送执行进度，用户可随时查看中间状态。

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
问题拆解
</td>
<td>
只说了@Transactional 和 Seata
</td>
<td>
分层设计：本地→跨服务→用户体验
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Saga 和补偿机制
</td>
<td>
熟悉 Saga 模式、事务消息表、幂等设计
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有考虑长事务的用户体验
</td>
<td>
提出异步回调 + SSE 推送方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道分布式事务概念
</td>
<td>
有长链路事务落地经验，考虑周全
</td>
</tr>
</table>

---

#### 4、进阶题：Spring 事务的底层实现原理？TransactionManager 和 TransactionSynchronizationManager 的作用？

**难度级别**：⭐⭐⭐（PlatformTransactionManager、ThreadLocal 绑定连接、事务同步回调）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- PlatformTransactionManager 三板斧
- TransactionSynchronizationManager 的核心作用
- 同一个 Connection
- 事务同步回调
- 声明式事务的 AOP 实现

**2️⃣ Impressive Answer**
1. **PlatformTransactionManager 三板斧**：`getTransaction()`（获取/创建事务）、`commit()`、`rollback()`。`DataSourceTransactionManager` 实现中，`getTransaction()` 从 DataSource 获取 Connection 并设置 `autoCommit=false`，然后将 Connection 绑定到 ThreadLocal。
1. **TransactionSynchronizationManager 的核心作用**：通过 ThreadLocal 维护当前线程的事务资源（Connection、Session 等）和同步回调。`@Transactional` 方法内所有 DAO 操作通过 `DataSourceUtils.getConnection()` 获取的都是**同一个 Connection**，这就是事务生效的根本原因。
1. **事务同步回调**：`TransactionSynchronization` 接口提供 `beforeCommit()`、`afterCommit()`、`afterCompletion()` 等钩子。典型应用：事务提交后发消息（避免事务未提交就发消息导致消费者查不到数据）。

```java
TransactionSynchronizationManager.registerSynchronization(
  new TransactionSynchronization() {
    @Override
    public void afterCommit() {
        messageProducer.send(event);  // 事务提交后才发消息
    }
});
```
1. **声明式事务的 AOP 实现**：`TransactionInterceptor`（MethodInterceptor）拦截 @Transactional 方法，调用 TransactionManager 管理事务生命周期，本质是 AOP + 模板方法模式。

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
只说了 TransactionManager 的职责
</td>
<td>
Manager→ThreadLocal 绑定→同步回调→AOP 实现，全链路
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Connection 如何绑定到线程
</td>
<td>
清楚 ThreadLocal + DataSourceUtils 的协作机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没提到事务同步回调
</td>
<td>
有 afterCommit 发消息的实战经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道有 TransactionManager
</td>
<td>
理解事务底层实现，能解释&quot;为什么事务能生效&quot;
</td>
</tr>
</table>

---

#### 5、场景题：Agent 执行工具调用时需要"部分提交"，前 3 步成功就保存，第 4 步失败不影响前 3 步，如何设计？

**难度级别**：⭐⭐⭐⭐（REQUIRES\_NEW、编程式事务、Savepoint、事务模板）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 方案一：REQUIRES\_NEW 独立事务
- 方案二：编程式事务 + Savepoint
- 方案三：TransactionTemplate 分段提交
- 选型建议

**2️⃣ Impressive Answer**

这个问题有三种方案，适用不同场景：

**方案一：REQUIRES\_NEW 独立事务**

```java
@Service
public class ToolExecutionService {
  @Transactional(propagation = Propagation.REQUIRES_NEW)
  public StepResult executeStep(ToolStep step) {
      // 每步独立事务，成功即提交
      return toolInvoker.invoke(step);
  }
}
```

优点：简单直接；缺点：每步一个连接，连接池压力大。

**方案二：编程式事务 + Savepoint**

```java
public void executeWorkflow(List<ToolStep> steps) {
  TransactionStatus status = transactionManager.getTransaction(new DefaultTransactionDefinition());
  for (int i = 0; i < steps.size(); i++) {
      Object savepoint = status.createSavepoint();
      try {
          toolInvoker.invoke(steps.get(i));
          // 成功则释放 savepoint，继续
          status.releaseSavepoint(savepoint);
      } catch (Exception e) {
          // 失败则回滚到 savepoint，前面的步骤不受影响
          status.rollbackToSavepoint(savepoint);
          recordFailure(steps.get(i), e);
      }
  }
  transactionManager.commit(status);  // 统一提交成功的步骤
}
```

优点：单连接，性能好；缺点：需要数据库支持 Savepoint（MySQL InnoDB 支持）。

**方案三：TransactionTemplate 分段提交** 每 N 步用 `TransactionTemplate.execute()` 包一次，兼顾性能和隔离性。

**选型建议**：步骤间无依赖用方案一（简单）；步骤间有依赖且需要部分回滚用方案二（精细）；批量处理用方案三（折中）。

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
方案数量
</td>
<td>
只说了 REQUIRES\_NEW
</td>
<td>
三种方案对比，各有适用场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Savepoint
</td>
<td>
有 Savepoint 的完整代码实现
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没考虑连接池压力
</td>
<td>
分析了每种方案的优缺点
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
只会一种方案
</td>
<td>
能根据场景选型，有工程权衡能力
</td>
</tr>
</table>

### 2.4 Spring 循环依赖

#### 1、进阶题：Spring 如何解决循环依赖？三级缓存的作用分别是什么？

**难度级别**：⭐⭐⭐（三级缓存、singletonObjects、earlySingletonObjects、singletonFactories、提前暴露）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三级缓存的核心作用
- 一级缓存 singletonObjects：存放完全初始化好的 Bean（实例化+属性填充+初始化完成）。
- 二级缓存 earlySingletonObjects：存放提前暴露的半成品 Bean（已实例化但未填充属性），用于解决循环依赖。
- 三级缓存 singletonFactories：存放 ObjectFactory 工厂，用于生成提前暴露的 Bean，关键是可能生成 AOP 代理对象。

**2️⃣ Impressive Answer**
1. **三级缓存的核心作用**：
  - **一级缓存 singletonObjects**：存放完全初始化好的 Bean（实例化+属性填充+初始化完成）。
  - **二级缓存 earlySingletonObjects**：存放提前暴露的半成品 Bean（已实例化但未填充属性），用于解决循环依赖。
  - **三级缓存 singletonFactories**：存放 ObjectFactory 工厂，用于生成提前暴露的 Bean，**关键是可能生成 AOP 代理对象**。
1. **循环依赖解决流程**：A 创建时发现依赖 B → 暴露 A 的 ObjectFactory 到三级缓存 → B 创建时发现依赖 A → 从三级缓存获取 A 的 ObjectFactory → 生成 A 的早期引用（如果是 AOP 则生成代理）→ 放入二级缓存 → B 完成初始化 → A 完成初始化 → A 从二级缓存移到一级缓存。
1. **为什么需要三级而非两级**：如果 A 需要被 AOP 代理，代理对象必须在实例化后、初始化前创建。三级缓存中的 ObjectFactory 延迟执行，只有真正发生循环依赖时才创建代理，避免无循环依赖时也创建代理的性能浪费。两级缓存无法做到这个延迟创建。
1. **Prototype 无法解决**：Prototype 作用域的 Bean 不缓存，每次都创建新实例，Spring 不解决其循环依赖，会直接抛异常。

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
只说了三级缓存的名字
</td>
<td>
清晰解释每级缓存的作用和时机
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道为什么需要三级
</td>
<td>
解释了 ObjectFactory 延迟创建代理的设计
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没提到 Prototype 无法解决
</td>
<td>
知道 Prototype 循环依赖会直接报错
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过概念但理解不深
</td>
<td>
理解设计意图，知道延迟创建的优化
</td>
</tr>
</table>

---

#### 2、进阶题：为什么构造器注入无法解决循环依赖？@Lazy 如何解决？

**难度级别**：⭐⭐⭐（构造器注入时机、代理延迟加载、Provider 模式）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 其他延迟加载方案
- ObjectProvider：注入 ObjectProvider，调用 getObject() 时才获取 Bean。
- ApplicationContext.getBean()：在需要时手动从容器获取，但增加了容器耦合。
- @Autowired(required = false)：设为非必须，配合 @PostConstruct 延迟初始化。

**2️⃣ Impressive Answer**
1. **构造器注入无法解决的根本原因**：构造器注入在**实例化阶段**就需要依赖对象，此时 Bean 还没创建完成，无法提前暴露到三级缓存。而 Setter 注入在实例化之后、属性填充阶段才需要依赖，此时已经可以提前暴露了。
1. **@Lazy 的解决原理**：注入的不是真实 Bean，而是一个 CGLIB 生成的代理对象。首次调用代理方法时，代理才从 Spring 容器获取真实 Bean。这样在构造阶段只需要一个代理占位，不触发真实 Bean 的创建，打破了循环依赖。
1. **其他延迟加载方案**：
  - `ObjectProvider<T>`：注入 ObjectProvider，调用 `getObject()` 时才获取 Bean。
  - `ApplicationContext.getBean()`：在需要时手动从容器获取，但增加了容器耦合。
  - `@Autowired(required = false)`：设为非必须，配合 `@PostConstruct` 延迟初始化。
1. **最佳实践**：优先通过重构消除循环依赖（提取中间层、事件驱动），而非用 @Lazy 绕过。@Lazy 只是技术手段，治标不治本，可能掩盖设计问题。

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
只说了构造器阶段需要依赖
</td>
<td>
区分实例化阶段和属性填充阶段
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 CGLIB 代理的具体机制
</td>
<td>
解释代理延迟获取真实 Bean 的原理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
只提到 @Lazy
</td>
<td>
给出多种延迟加载方案和最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道现象但不知道原理
</td>
<td>
理解设计权衡，有架构思维
</td>
</tr>
</table>

---

#### 3、场景题：Spring Boot 2.6+ 默认禁止循环依赖，如何优雅地重构消除循环依赖？

**难度级别**：⭐⭐⭐（依赖倒置、事件驱动解耦、中间层抽取）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 重构方案一：提取中间层
- 重构方案二：事件驱动解耦
- 重构方案三：依赖倒置

**2️⃣ Impressive Answer**
1. **Spring Boot 2.6 的变化**：`spring.main.allow-circular-references` 默认从 `true` 改为 `false`，强制要求消除循环依赖，这是为了推动更健康的架构设计。
1. **重构方案一：提取中间层**

```java
// 原始：A 依赖 B，B 依赖 A
// 重构：A 依赖 C，B 依赖 C
@Service
public class SharedService {
    // A 和 B 的公共逻辑
}
```

```
适用于 A 和 B 有公共依赖的场景。
```
1. **重构方案二：事件驱动解耦**

```java
@Service
public class AgentService {
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    public void executeAgent() {
        // 执行逻辑
        eventPublisher.publishEvent(new AgentCompletedEvent(data));
    }
}

@Service
public class ToolService {
    @EventListener
    public void handleAgentCompleted(AgentCompletedEvent event) {
        // 响应事件，不直接依赖 AgentService
    }
}
```

```
适用于异步场景，降低耦合。
```
1. **重构方案三：依赖倒置**

```java
public interface ToolExecutor {
    void execute(ToolRequest request);
}

@Service
public class AgentService {
    private final ToolExecutor executor;  // 依赖接口
}

@Service
public class ToolService implements ToolExecutor {
    // 不依赖 AgentService
}
```

```
适用于需要双向协作但可以抽象接口的场景。
```
1. **Agent 场景实战**：AgentService 和 ToolService 互相依赖时，通过 `ToolRegistry` 中间层解耦，ToolService 注册自己到 Registry，AgentService 从 Registry 获取工具，不直接依赖 ToolService。

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
只说了&quot;提取公共 Bean&quot;
</td>
<td>
三种方案，每种都有完整代码示例
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道事件驱动的优势
</td>
<td>
解释事件驱动解耦的原理和适用场景
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 场景的具体解耦方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道要重构但不会设计
</td>
<td>
能根据场景选型，有架构设计能力
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
Spring 三级缓存中 ObjectFactory 和 AOP 代理的关系？
</td>
<td>
深入理解为什么需要三级缓存而非两级
</td>
<td>
答：三级缓存各自作用；为什么需要三级而非两级；AOP 代理场景；singletonObjects（一级）：Map，存放完全初始化的 Bean，getBean() 默认从这里获取。
</td>
</tr>
<tr>
<td>
@DependsOn 注解的作用和使用场景？
</td>
<td>
Bean 初始化顺序控制，和循环依赖的区别
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Spring 的 Bean 作用域（Singleton/Prototype）对循环依赖的影响？
</td>
<td>
Prototype 作用域无法解决循环依赖
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

## Spring 容器启动与配置体系

### Spring 容器启动与配置体系

#### 1、基础题：@Configuration 和 @Component 的区别？@Bean 方法的 Full 模式代理机制？

**难度级别**：⭐⭐（配置类 vs 普通组件、CGLIB 代理、Lite 模式）

**Answer**
1. **@Configuration vs @Component**：
  - `@Configuration` 是配置类，Spring 会用 CGLIB 代理，保证 `@Bean` 方法调用返回同一个实例。
  - `@Component` 是普通组件，`@Bean` 方法每次调用都会创建新实例。
1. **Full 模式代理机制**：
  - `@Configuration` 默认是 Full 模式，Spring 生成子类代理，拦截 `@Bean` 方法调用，从容器获取已注册的 Bean。
  - 如果配置类没有 `@Bean` 方法互相调用，可以用 `@Configuration(proxyBeanMethods = false)` 切换到 Lite 模式，避免代理开销。
1. **代码示例**：

```java
@Configuration
public class AppConfig {
    @Bean
    public DataSource dataSource() { return new HikariDataSource(); }

    @Bean
    public JdbcTemplate jdbcTemplate() {
        // Full 模式：调用 dataSource() 返回同一个实例
        return new JdbcTemplate(dataSource());
    }
}
```

---

#### 2、进阶题：Spring 容器 refresh() 的 12 个核心步骤是什么？

**难度级别**：⭐⭐⭐⭐（容器启动流程、BeanFactoryPostProcessor、BeanPostProcessor、单例初始化）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 关键理解
- 第 5 步 invokeBeanFactoryPostProcessors 是最关键的，@Configuration、@ComponentScan 都在这里解析。
- 第 11 步 finishBeanFactoryInitialization 完成 Bean 的完整生命周期（包括 AOP 代理）。
- 第 12 步 finishRefresh 后，容器就完全就绪了。

**2️⃣ Impressive Answer**
1. **prepareRefresh()**：准备刷新上下文，设置启动时间、初始化属性源、验证必需属性。
1. **obtainFreshBeanFactory()**：创建 BeanFactory，加载 BeanDefinition（解析 @Component、@Bean 等）。
1. **prepareBeanFactory()**：配置 BeanFactory，注册 BeanPostProcessor（如 ApplicationContextAwareProcessor）、设置类加载器。
1. **postProcessBeanFactory()**：子类扩展点，可以修改 BeanFactory（如添加 Web 环境特有的 Scope）。
1. **invokeBeanFactoryPostProcessors()**：执行 BeanFactoryPostProcessor（如 @PropertySource、@ConfigurationClassPostProcessor 解析配置类）。
1. **registerBeanPostProcessors()**：注册 BeanPostProcessor（如 AutowiredAnnotationBeanPostProcessor、CommonAnnotationBeanPostProcessor）。
1. **initMessageSource()**：初始化国际化资源（MessageSource）。
1. **initApplicationEventMulticaster()**：初始化事件广播器（ApplicationEventMulticaster）。
1. **onRefresh()**：子类扩展点，创建 Web 容器（如 Tomcat、Jetty）。
1. **registerListeners()**：注册监听器，广播早期事件。
1. **finishBeanFactoryInitialization()**：初始化所有非懒加载的单例 Bean（实例化、属性注入、初始化回调）。
1. **finishRefresh()**：完成刷新，发布 ContextRefreshedEvent，启动生命周期 Bean（如 SmartLifecycle）。
1. **关键理解**：
  - 第 5 步 `invokeBeanFactoryPostProcessors` 是最关键的，`@Configuration`、`@ComponentScan` 都在这里解析。
  - 第 11 步 `finishBeanFactoryInitialization` 完成 Bean 的完整生命周期（包括 AOP 代理）。
  - 第 12 步 `finishRefresh` 后，容器就完全就绪了。
1. **Agent 场景**：在 `onRefresh()` 步骤启动 Agent Server（如 gRPC Server），在 `finishRefresh()` 后发布 `AgentReadyEvent`，通知下游服务 Agent 已就绪。

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
只说了&quot;加载 Bean、创建 Bean&quot;
</td>
<td>
完整 12 步，每步都有明确作用
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 BeanFactoryPostProcessor 的执行时机
</td>
<td>
清楚配置解析在第 5 步，Bean 初始化在第 11 步
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Web 容器启动
</td>
<td>
知道 onRefresh() 启动 Tomcat，finishRefresh() 发布事件
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过流程但不理解
</td>
<td>
理解容器启动的设计意图和扩展点
</td>
</tr>
</table>

---

#### 3、场景题：Agent 平台多环境配置如何用 @Profile + @ConditionalOnProperty 管理？

**难度级别**：⭐⭐⭐（环境隔离、条件装配、配置优先级）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- @Profile 环境隔离
- @ConditionalOnProperty 功能开关
- 组合使用

**2️⃣ Impressive Answer**
1. **@Profile 环境隔离**：

```java
@Profile("dev")
@Configuration
public class DevConfig {
    @Bean
    public LLMProvider mockLLM() {
        return new MockLLMProvider();  // 开发环境用 Mock
    }
}

@Profile("prod")
@Configuration
public class ProdConfig {
    @Bean
    public LLMProvider openaiLLM() {
        return new OpenAIProvider();  // 生产环境用真实 LLM
    }
}

// 激活环境
@SpringBootApplication
public class AgentApplication {
    public static void main(String[] args) {
        SpringApplication.run(AgentApplication.class, "--spring.profiles.active=dev");
    }
}
```
1. **@ConditionalOnProperty 功能开关**：

```java
@Configuration
public class ToolConfig {
    @Bean
    @ConditionalOnProperty(name = "agent.tools.enabled", havingValue = "true")
    public ToolRegistry toolRegistry() {
        return new DefaultToolRegistry();  // 工具功能开启时才加载
    }

    @Bean
    @ConditionalOnMissingBean(ToolRegistry.class)
    public ToolRegistry emptyToolRegistry() {
        return new EmptyToolRegistry();  // 工具功能关闭时用空实现
    }
}

// application-dev.yml
agent:
  tools:
    enabled: true  // 开发环境开启工具

// application-prod.yml
agent:
  tools:
    enabled: false  // 生产环境关闭工具
```
1. **组合使用**：

```java
@Profile("dev")
@ConditionalOnProperty(name = "agent.mock.enabled")
@Configuration
public class DevMockConfig {
    // 仅在 dev 环境且 agent.mock.enabled=true 时生效
}
```
1. **配置优先级**：`application-{profile}.yml` > `application.yml`，环境特定配置会覆盖默认配置。
1. **Agent 场景实战**：开发环境用 `@Profile("dev")` + Mock LLM + 本地向量库，测试环境用真实 LLM + 测试向量库，生产环境用企业级 LLM + 云向量库，通过 `@ConditionalOnProperty` 控制审计日志、计费等功能的开关。

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
只说了&quot;区分环境&quot;
</td>
<td>
@Profile 和 @ConditionalOnProperty 结合使用，有完整代码
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道配置优先级
</td>
<td>
解释环境配置覆盖默认配置的机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 平台多环境配置的完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道注解但不会组合使用
</td>
<td>
能设计灵活的多环境配置方案
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
@Import 注解的三种用法（普通类、ImportSelector、ImportBeanDefinitionRegistrar）？
</td>
<td>
动态注册 Bean 的扩展方式
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Spring Boot 的自动配置原理（spring.factories / AutoConfiguration.imports）？
</td>
<td>
基于条件装配的自动配置机制
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
BeanFactoryPostProcessor 和 BeanPostProcessor 的区别？
</td>
<td>
容器启动流程中的两个关键扩展点
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 3.2 Spring 设计模式与扩展点

#### 1、基础题：Spring 中用到了哪些设计模式？举例说明

**难度级别**：⭐⭐（工厂、单例、代理、模板方法、观察者、策略、适配器）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 工厂模式
- 单例模式
- 代理模式
- 模板方法模式
- 观察者模式
- 策略模式

**2️⃣ Impressive Answer**

Spring 框架是设计模式的教科书级应用，我从 7 个核心模式来说：
1. **工厂模式**：`BeanFactory` / `ApplicationContext` 是 Bean 的工厂，根据 BeanDefinition 创建对象。`FactoryBean` 接口让用户自定义复杂 Bean 的创建逻辑。
1. **单例模式**：Bean 默认 Singleton 作用域，通过三级缓存（`singletonObjects`）保证全局唯一。不是传统的私有构造器单例，而是容器级别的单例。
1. **代理模式**：AOP 的核心，JDK 动态代理（接口）和 CGLIB（类）。`@Transactional`、`@Async`、`@Cacheable` 都是通过代理实现的。
1. **模板方法模式**：`JdbcTemplate`、`RestTemplate`、`TransactionTemplate`——定义算法骨架，子类/回调实现具体步骤。
1. **观察者模式**：`ApplicationEvent` + `ApplicationListener`，事件发布-订阅机制，实现组件间松耦合通信。
1. **策略模式**：`Resource` 接口的多种实现（`ClassPathResource`、`FileSystemResource`、`UrlResource`），根据前缀自动选择策略。
1. **适配器模式**：`HandlerAdapter` 适配不同类型的 Controller（注解式、实现 Controller 接口式），统一调用接口。

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
零散列举了几个
</td>
<td>
7 个模式，每个都有具体类名和解释
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 FactoryBean 和 BeanFactory 的区别
</td>
<td>
区分了容器级单例和传统单例
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
只说了名字没有解释
</td>
<td>
每个模式都关联到具体的 Spring 组件
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过设计模式名称
</td>
<td>
理解 Spring 如何运用设计模式，有架构视角
</td>
</tr>
</table>

---

## Spring 事件机制

### Spring 事件机制

#### 2、进阶题：Spring 的事件机制（ApplicationEvent）如何实现？同步还是异步？

**难度级别**：⭐⭐⭐（ApplicationEventPublisher、ApplicationEventMulticaster、@EventListener、@Async）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 异步化方案
- 方式一：@EventListener + @Async，需要 @EnableAsync 开启异步支持。
- 方式二：配置 ApplicationEventMulticaster 的 TaskExecutor，全局异步。
- 注意：异步事件的异常不会传播到发布者，需要在监听器内部单独处理。

**2️⃣ Impressive Answer**
1. **发布与监听**：`ApplicationEventPublisher.publishEvent()` 发布事件；监听方式有两种：`@EventListener` 注解（推荐）或实现 `ApplicationListener<T>` 接口。
1. **默认同步执行**：`SimpleApplicationEventMulticaster` 默认在发布线程中依次调用所有监听器。这意味着监听器抛异常会影响发布者，耗时操作会阻塞主流程。
1. **异步化方案**：
  - **方式一**：`@EventListener` + `@Async`，需要 `@EnableAsync` 开启异步支持。
  - **方式二**：配置 `ApplicationEventMulticaster` 的 `TaskExecutor`，全局异步。
  - **注意**：异步事件的异常不会传播到发布者，需要在监听器内部单独处理。
1. **事务事件**：`@TransactionalEventListener(phase = AFTER_COMMIT)` 保证事务提交后才触发监听器，避免"事务未提交，消费者查不到数据"的问题。这是发消息场景的最佳实践。
1. **执行顺序**：多个监听器通过 `@Order` 控制顺序；同步场景下按 Order 值从小到大执行。

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
只说了&quot;发布-订阅&quot;
</td>
<td>
同步→异步→事务事件→执行顺序，层层递进
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道同步的风险
</td>
<td>
清楚异常传播和阻塞问题
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没提到事务事件
</td>
<td>
知道 AFTER_COMMIT 的最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用但不深入
</td>
<td>
理解事件机制的设计权衡和生产注意事项
</td>
</tr>
</table>

---

#### 3、场景题：如何用 Spring 事件机制实现 Agent 工具调用的审计日志？

**难度级别**：⭐⭐⭐（事件驱动解耦、异步审计、结构化日志）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 定义审计事件
- 多监听器各司其职
- 审计日志监听器：@EventListener + @Async，异步写入审计日志表（DB）。
- 实时分析监听器：推送到 Kafka，供实时数据分析平台消费。
- 告警监听器：检测异常调用（如耗时 > 阈值、连续失败），触发告警通知。

**2️⃣ Impressive Answer**
1. **定义审计事件**：

```java
@Data
public class ToolInvocationEvent extends ApplicationEvent {
    private String toolName;
    private Object[] arguments;
    private Object result;
    private long durationMs;
    private String userId;
    private String traceId;
    private boolean success;
}
```
1. **AOP 切面发布事件**：在 `@Around` 切面中，工具调用完成后 `publishEvent`，将调用信息封装为事件。切面只负责发布，不关心后续处理。
1. **多监听器各司其职**：
  - **审计日志监听器**：`@EventListener` + `@Async`，异步写入审计日志表（DB）。
  - **实时分析监听器**：推送到 Kafka，供实时数据分析平台消费。
  - **告警监听器**：检测异常调用（如耗时 > 阈值、连续失败），触发告警通知。
1. **核心优势**：工具调用逻辑和审计逻辑**完全解耦**。新增审计需求（如合规审计、成本统计）只需加一个监听器，不修改任何已有代码，符合开闭原则。
1. **生产考虑**：异步监听器配置独立线程池，避免审计任务影响业务线程；监听器内部做好异常处理和重试，保证审计数据不丢失。

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
只说了&quot;发事件、写数据库&quot;
</td>
<td>
事件定义→AOP 发布→多监听器→生产考虑
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道多监听器的好处
</td>
<td>
清楚开闭原则和解耦优势
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没考虑线程池隔离
</td>
<td>
有独立线程池和异常处理方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
能实现基本功能
</td>
<td>
有完整的审计架构设计，考虑扩展性
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
Spring 的 Aware 接口有哪些？各自的作用？
</td>
<td>
Spring 扩展点体系的一部分，考察对容器感知能力的理解
</td>
<td>
答：多模态输入先做解析和标准化，把图片、语音、文档转成文本、结构化字段或 embedding，再进入检索、规划和推理链路。
</td>
</tr>
<tr>
<td>
@Order 和 Ordered 接口如何控制 Bean 的加载顺序？
</td>
<td>
多个监听器/切面的执行顺序控制
</td>
<td>
答：顺序性通常靠同一业务 key 路由到同一分区保证；跨分区无法全局有序，只能做局部顺序或业务补偿。
</td>
</tr>
<tr>
<td>
Spring SPI 机制（spring.factories）和 Java SPI 的区别？
</td>
<td>
扩展点加载机制的对比
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

#### 1、基础题：ApplicationEvent 和 @EventListener 的基本用法？

**难度级别**：⭐⭐（事件发布、事件监听、解耦）

**Answer**
1. **自定义事件**：

```java
public class AgentCompletedEvent extends ApplicationEvent {
    private final String agentId;
    private final AgentResult result;

    public AgentCompletedEvent(Object source, String agentId, AgentResult result) {
        super(source);
        this.agentId = agentId;
        this.result = result;
    }
}
```
1. **发布事件**：

```java
@Service
public class AgentService {
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    public AgentResult execute(String agentId, AgentRequest request) {
        AgentResult result = doExecute(request);
        eventPublisher.publishEvent(new AgentCompletedEvent(this, agentId, result));
        return result;
    }
}
```
1. **监听事件**：

```java
@Component
public class AgentEventListener {
    @EventListener
    public void handleAgentCompleted(AgentCompletedEvent event) {
        System.out.println("Agent " + event.getAgentId() + " completed");
    }
}
```

---

#### 2、进阶题：同步事件 vs 异步事件（@Async）的区别？@TransactionalEventListener 的作用？

**难度级别**：⭐⭐⭐（事件同步性、事务绑定、异步线程池）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 同步事件
- 异步事件
- @TransactionalEventListener
- 线程池配置
- 默认行为，发布事件的线程立即执行所有监听器。
- 优点：事务一致性，监听器可以回滚事务。

**2️⃣ Impressive Answer**
1. **同步事件**：
  - 默认行为，发布事件的线程立即执行所有监听器。
  - 优点：事务一致性，监听器可以回滚事务。
  - 缺点：阻塞主流程，影响性能。
1. **异步事件**：

```java
@Component
public class AsyncEventListener {
    @Async("eventExecutor")  // 指定线程池
    @EventListener
    public void handleAsync(AgentCompletedEvent event) {
        // 异步执行，不阻塞主流程
    }
}
```

```
- 优点：解耦、提升性能，适合日志、通知等非核心流程。
- 缺点：监听器无法回滚主事务，需要处理事务一致性。
```
1. **@TransactionalEventListener**：

```java
@Component
public class TransactionalEventListener {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleAfterCommit(AgentCompletedEvent event) {
        // 事务提交后才执行，确保数据已持久化
    }
}
```

```
- 支持阶段：`BEFORE_COMMIT`、`AFTER_COMMIT`、`AFTER_ROLLBACK`、`AFTER_COMPLETION`。
- 场景：事务提交后发送通知、同步到下游系统。
```
1. **线程池配置**：

```java
@Configuration
@EnableAsync
public class AsyncConfig {
    @Bean("eventExecutor")
    public Executor eventExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("event-");
        return executor;
    }
}
```
1. **Agent 场景实战**：Agent 执行完成后，同步事件更新数据库状态，异步事件记录日志、发送通知，`@TransactionalEventListener` 在事务提交后同步到审计系统。

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
只说了&quot;同步 vs 异步&quot;
</td>
<td>
解释三种事件机制，每种都有代码示例
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @TransactionalEventListener 的阶段
</td>
<td>
清楚事务绑定和事务阶段的选择
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 事件处理的完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道基本用法但不会选型
</td>
<td>
能根据场景选择合适的事件机制
</td>
</tr>
</table>

---

#### 3、场景题：Agent 工具调用完成后如何用事件机制解耦通知下游（日志、计费、审计）？

**难度级别**：⭐⭐⭐（事件驱动、解耦、异步处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 定义事件
- 发布事件
- 监听器解耦
- 解耦：工具执行逻辑和日志、计费、审计逻辑完全分离。
- 扩展：新增下游处理只需添加监听器，无需修改工具执行代码。
- 性能：异步处理不阻塞主流程。

**2️⃣ Impressive Answer**
1. **定义事件**：

```java
public class ToolCallCompletedEvent extends ApplicationEvent {
    private final String toolId;
    private final ToolRequest request;
    private final ToolResponse response;
    private final long duration;

    public ToolCallCompletedEvent(Object source, String toolId,
                                  ToolRequest request, ToolResponse response, long duration) {
        super(source);
        this.toolId = toolId;
        this.request = request;
        this.response = response;
        this.duration = duration;
    }
}
```
1. **发布事件**：

```java
@Service
public class ToolExecutor {
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    public ToolResponse execute(String toolId, ToolRequest request) {
        long start = System.currentTimeMillis();
        ToolResponse response = doExecute(toolId, request);
        long duration = System.currentTimeMillis() - start;
        eventPublisher.publishEvent(new ToolCallCompletedEvent(this, toolId, request, response, duration));
        return response;
    }
}
```
1. **监听器解耦**：

```java
@Component
public class ToolCallListeners {

    // 日志监听器（同步，确保日志不丢失）
    @EventListener
    public void logToolCall(ToolCallCompletedEvent event) {
        log.info("Tool {} executed in {}ms", event.getToolId(), event.getDuration());
    }

    // 计费监听器（异步，不阻塞主流程）
    @Async("billingExecutor")
    @EventListener(condition = "#event.response.success")
    public void chargeToolUsage(ToolCallCompletedEvent event) {
        billingService.charge(event.getToolId(), event.getDuration());
    }

    // 审计监听器（事务提交后执行）
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void auditToolCall(ToolCallCompletedEvent event) {
        auditService.record(event.getToolId(), event.getRequest(), event.getResponse());
    }
}
```
1. **优势**：
  - 解耦：工具执行逻辑和日志、计费、审计逻辑完全分离。
  - 扩展：新增下游处理只需添加监听器，无需修改工具执行代码。
  - 性能：异步处理不阻塞主流程。
1. **Agent 场景实战**：Agent 调用工具后，通过事件机制通知日志系统记录调用链、计费系统计算费用、审计系统记录操作，工具执行代码保持简洁，易于维护。

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
只说了&quot;发布事件、监听事件&quot;
</td>
<td>
完整事件驱动架构，包含同步、异步、事务绑定
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @EventListener 的条件过滤
</td>
<td>
使用 condition 过滤成功调用，异步计费
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 工具调用事件处理的完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道事件驱动但不会设计
</td>
<td>
能设计解耦的事件驱动架构
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
Spring 事件监听器的执行顺序（@Order）？
</td>
<td>
多个监听器的执行顺序控制
</td>
<td>
答：顺序性通常靠同一业务 key 路由到同一分区保证；跨分区无法全局有序，只能做局部顺序或业务补偿。
</td>
</tr>
<tr>
<td>
@Async 的线程池如何配置和监控？
</td>
<td>
异步事件需要合理配置线程池
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
Spring 事件和消息队列（如 Kafka）的区别？
</td>
<td>
进程内事件 vs 进程间消息传递
</td>
<td>
答：Kafka 里 Topic 是逻辑主题，Partition 是物理并行单元，Consumer Group 内一个分区同一时刻只分给一个消费者。
</td>
</tr>
</table>

---

## Spring 条件装配与自动配置

### Spring 条件装配与自动配置

#### 1、基础题：@Conditional 系列注解有哪些？各自触发条件？

**难度级别**：⭐⭐（条件装配、类路径判断、Bean 存在性判断）

**Answer**
1. **@Conditional**：核心注解，配合 Condition 接口实现自定义条件。
1. **常用条件注解**：
  - `@ConditionalOnClass`：类路径存在指定类。
  - `@ConditionalOnMissingClass`：类路径不存在指定类。
  - `@ConditionalOnBean`：容器中存在指定 Bean。
  - `@ConditionalOnMissingBean`：容器中不存在指定 Bean。
  - `@ConditionalOnProperty`：配置属性满足条件。
  - `@ConditionalOnExpression`：SpEL 表达式为 true。
  - `@ConditionalOnWebApplication`：Web 环境。
  - `@ConditionalOnNotWebApplication`：非 Web 环境。
1. **示例**：

```java
@Configuration
public class LLMConfig {
    @Bean
    @ConditionalOnClass(name = "com.openai.OpenAI")
    public LLMProvider openaiLLM() {
        return new OpenAIProvider();  // 类路径存在 OpenAI 类时才创建
    }

    @Bean
    @ConditionalOnMissingBean(LLMProvider.class)
    public LLMProvider mockLLM() {
        return new MockLLMProvider();  // 没有 LLMProvider 时才创建
    }
}
```

---

#### 2、进阶题：Spring Boot 自动配置的原理（spring.factories / AutoConfiguration.imports）？

**难度级别**：⭐⭐⭐⭐（自动配置机制、条件装配、EnableAutoConfiguration）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 自动配置原理
- spring.factories 示例（Spring Boot 2.7 之前）
- AutoConfiguration.imports 示例（Spring Boot 2.7+）
- 自动配置类示例
- 调试自动配置
- Spring Boot 启动时，通过 @EnableAutoConfiguration 导入 AutoConfigurationImportSelector。

**2️⃣ Impressive Answer**
1. **自动配置原理**：
  - Spring Boot 启动时，通过 `@EnableAutoConfiguration` 导入 `AutoConfigurationImportSelector`。
  - `AutoConfigurationImportSelector` 从 `META-INF/spring.factories`（Spring Boot 2.7 之前）或 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Spring Boot 2.7+）加载自动配置类。
  - 自动配置类使用 `@Conditional` 系列注解，根据类路径、配置、Bean 存在性等条件决定是否生效。
1. **spring.factories 示例**（Spring Boot 2.7 之前）：

```properties
# META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
com.example.agent.autoconfigure.AgentAutoConfiguration,\
com.example.agent.autoconfigure.ToolAutoConfiguration
```
1. **AutoConfiguration.imports 示例**（Spring Boot 2.7+）：

```properties
# META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.agent.autoconfigure.AgentAutoConfiguration
com.example.agent.autoconfigure.ToolAutoConfiguration
```
1. **自动配置类示例**：

```java
@Configuration
@ConditionalOnClass(AgentService.class)
@ConditionalOnProperty(prefix = "agent", name = "enabled", havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(AgentProperties.class)
public class AgentAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public AgentService agentService(AgentProperties properties) {
        return new AgentService(properties);
    }

    @Bean
    @ConditionalOnProperty(prefix = "agent.tools", name = "enabled", havingValue = "true")
    public ToolRegistry toolRegistry() {
        return new DefaultToolRegistry();
    }
}
```
1. **调试自动配置**：
  - 启动参数：`--debug` 或 `--logging.level.org.springframework.boot.autoconfigure=DEBUG`。
  - 查看报告：启动日志会输出哪些自动配置类生效/未生效。
1. **Agent 场景实战**：自定义 Agent Starter，通过自动配置让用户只需引入依赖和配置 `agent.enabled=true`，就能开箱即用 Agent 功能。

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
只说了&quot;加载 spring.factories&quot;
</td>
<td>
完整自动配置流程，包含条件装配和调试
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 AutoConfiguration.imports 的变化
</td>
<td>
清楚 Spring Boot 2.7+ 的变化
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent Starter 的自动配置实现
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
理解自动配置的设计意图和实现机制
</td>
</tr>
</table>

---

#### 3、场景题：如何自定义一个 Spring Boot Starter，让 Agent 工具库开箱即用？

**难度级别**：⭐⭐⭐（Starter 开发、自动配置、属性绑定）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 项目结构
- 属性配置类
- 自动配置类
- AutoConfiguration.imports
- 用户使用
- search-tool

**2️⃣ Impressive Answer**
1. **项目结构**：

```
agent-spring-boot-starter/
├── src/main/java/
│   └── com/example/agent/
│       ├── autoconfigure/
│       │   └── AgentAutoConfiguration.java
│       ├── properties/
│       │   └── AgentProperties.java
│       └── service/
│           └── AgentService.java
└── src/main/resources/
    └── META-INF/
        └── spring/
            └── org.springframework.boot.autoconfigure.AutoConfiguration.imports
```
1. **属性配置类**：

```java
@ConfigurationProperties(prefix = "agent")
public class AgentProperties {
    private boolean enabled = true;
    private String llmProvider = "openai";
    private String apiKey;
    private double temperature = 0.7;
    private Tools tools = new Tools();

    public static class Tools {
        private boolean enabled = true;
        private List<String> includes = new ArrayList<>();
        private List<String> excludes = new ArrayList<>();

        // getters and setters
    }

    // getters and setters
}
```
1. **自动配置类**：

```java
@Configuration
@ConditionalOnClass(AgentService.class)
@ConditionalOnProperty(prefix = "agent", name = "enabled", havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(AgentProperties.class)
public class AgentAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public AgentService agentService(AgentProperties properties) {
        return new AgentService(properties);
    }

    @Bean
    @ConditionalOnProperty(prefix = "agent.tools", name = "enabled", havingValue = "true")
    public ToolRegistry toolRegistry(AgentProperties properties) {
        DefaultToolRegistry registry = new DefaultToolRegistry();
        properties.getTools().getIncludes().forEach(registry::register);
        return registry;
    }
}
```
1. **AutoConfiguration.imports**：

```properties
com.example.agent.autoconfigure.AgentAutoConfiguration
```
1. **用户使用**：

```xml
<!-- pom.xml -->
<dependency>
    <groupId>com.example</groupId>
    <artifactId>agent-spring-boot-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
# application.yml
agent:
  enabled: true
  llm-provider: openai
  api-key: ${OPENAI_API_KEY}
  temperature: 0.7
  tools:
    enabled: true
    includes:
      - search-tool
      - calculator-tool
```

```java
@Service
public class UserService {
    @Autowired
    private AgentService agentService;  // 直接注入使用
}
```
1. **Agent 场景实战**：开发 `agent-tool-spring-boot-starter`，自动注册常用工具（搜索、计算、天气等），用户只需引入依赖和配置工具列表，就能在 Agent 中使用这些工具。

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
只说了&quot;写自动配置类&quot;
</td>
<td>
完整 Starter 开发流程，包含项目结构和使用示例
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @ConfigurationProperties 的用法
</td>
<td>
清楚属性绑定和条件装配的结合
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent Tool Starter 的完整实现
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道概念但不会开发
</td>
<td>
能独立开发 Spring Boot Starter
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
@SpringBootApplication 注解的三个核心注解是什么？
</td>
<td>
理解自动配置的入口
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
如何排除自动配置类（@EnableAutoConfiguration.exclude）？
</td>
<td>
精细化控制自动配置
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：精细化控制自动配置，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
@ConditionalOnProperty 的 matchIfMissing 参数作用？
</td>
<td>
配置不存在时的默认行为
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：配置不存在时的默认行为，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

## Spring Bean 作用域与代理

### Spring Bean 作用域与代理

#### 1、基础题：Bean 的 6 种作用域分别是什么？各自适用场景？

**难度级别**：⭐⭐（作用域、生命周期、适用场景）

**Answer**
1. **6 种作用域**：
  - `singleton`：单例，容器中只有一个实例（默认）。
  - `prototype`：原型，每次请求创建新实例。
  - `request`：请求，每个 HTTP 请求一个实例（Web 环境）。
  - `session`：会话，每个 HTTP Session 一个实例（Web 环境）。
  - `application`：应用，ServletContext 生命周期内一个实例（Web 环境）。
  - `websocket`：WebSocket，每个 WebSocket 一个实例（Web 环境）。
1. **适用场景**：
  - `singleton`：无状态服务（如 Service、Repository）。
  - `prototype`：有状态对象（如命令对象、表单对象）。
  - `request`：请求相关数据（如用户信息、请求参数）。
  - `session`：会话相关数据（如购物车、用户登录信息）。
  - `application`：全局共享数据（如配置缓存、统计计数器）。
1. **示例**：

```java
@Scope("prototype")
@Component
public class ToolRequest {
    private String toolId;
    private Map<String, Object> parameters;
}
```

---

#### 2、进阶题：Singleton Bean 注入 Prototype Bean 的陷阱？@Lookup 和 ObjectProvider 如何解决？

**难度级别**：⭐⭐⭐⭐（作用域代理、依赖注入陷阱、解决方案）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 解决方案一：@Lookup 注解
- 解决方案二：ObjectProvider
- 解决方案三：@Scope 代理
- Singleton Bean 只初始化一次，注入的 Prototype Bean 也只创建一次。
- 后续使用 toolRequest 时，仍然是同一个实例，违背了 Prototype 的设计意图。
- Spring 会生成 CGLIB 子类，覆盖 getToolRequest() 方法，每次调用都从容器获取新实例。

**2️⃣ Impressive Answer**
1. **陷阱**：

```java
@Component
@Scope("singleton")
public class AgentService {
    @Autowired
    private ToolRequest toolRequest;  // Prototype Bean

    public void execute() {
        // 每次都是同一个 toolRequest 实例，不是新的！
    }
}
```

```
- Singleton Bean 只初始化一次，注入的 Prototype Bean 也只创建一次。
- 后续使用 `toolRequest` 时，仍然是同一个实例，违背了 Prototype 的设计意图。
```
1. **解决方案一：@Lookup 注解**：

```java
@Component
@Scope("singleton")
public abstract class AgentService {

    public void execute() {
        ToolRequest toolRequest = getToolRequest();  // 每次调用都返回新实例
    }

    @Lookup
    protected abstract ToolRequest getToolRequest();  // Spring 会生成子类实现
}
```

```
- Spring 会生成 CGLIB 子类，覆盖 `getToolRequest()` 方法，每次调用都从容器获取新实例。
```
1. **解决方案二：ObjectProvider**：

```java
@Component
@Scope("singleton")
public class AgentService {
    @Autowired
    private ObjectProvider<ToolRequest> toolRequestProvider;

    public void execute() {
        ToolRequest toolRequest = toolRequestProvider.getObject();  // 每次获取新实例
    }
}
```

```
- `ObjectProvider` 是延迟获取 Bean 的工具，每次调用 `getObject()` 都会从容器获取新实例。
```
1. **解决方案三：@Scope 代理**：

```java
@Component
@Scope(value = ConfigurableBeanFactory.SCOPE_PROTOTYPE, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class ToolRequest {
}
```

```
- Spring 会生成代理对象，每次调用代理对象的方法时，都会从容器获取新的目标对象。
```
1. **Agent 场景实战**：AgentService 是 Singleton，每次调用工具时需要新的 ToolRequest（Prototype），使用 `ObjectProvider<ToolRequest>` 动态获取新实例。

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
只说了&quot;用 @Lookup 或 ObjectProvider&quot;
</td>
<td>
三种解决方案，每种都有完整代码和原理
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @Lookup 的 CGLIB 实现
</td>
<td>
解释代理机制和延迟获取的原理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 工具请求的场景化解决方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道解决方案但不懂原理
</td>
<td>
理解作用域陷阱的设计原因和解决思路
</td>
</tr>
</table>

---

#### 3、场景题：Agent 会话级别的上下文（如对话历史）如何用 Session 作用域 Bean 管理？

**难度级别**：⭐⭐⭐（Session 作用域、会话管理、上下文隔离）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- Session 作用域 Bean
- 在 Service 中使用
- 代理模式
- Session 销毁
- proxyMode = ScopedProxyMode.TARGET_CLASS：Spring 生成 CGLIB 代理，代理对象持有 Session 引用。
- 每次调用代理对象的方法时，代理会从当前 Session 获取对应的真实 Bean。

**2️⃣ Impressive Answer**
1. **Session 作用域 Bean**：

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_SESSION, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class AgentSessionContext {
    private List<Message> conversationHistory = new ArrayList<>();
    private String userId;
    private Map<String, Object> metadata = new HashMap<>();

    public void addMessage(Message message) {
        conversationHistory.add(message);
    }

    public List<Message> getConversationHistory() {
        return Collections.unmodifiableList(conversationHistory);
    }

    // getters and setters
}
```
1. **在 Service 中使用**：

```java
@Service
public class AgentService {
    @Autowired
    private AgentSessionContext sessionContext;  // 代理对象

    public AgentResponse chat(AgentRequest request) {
        // 每次请求都会从当前 Session 获取对应的上下文
        sessionContext.addMessage(new Message("user", request.getContent()));

        AgentResponse response = doChat(request);

        sessionContext.addMessage(new Message("assistant", response.getContent()));
        return response;
    }
}
```
1. **代理模式**：
  - `proxyMode = ScopedProxyMode.TARGET_CLASS`：Spring 生成 CGLIB 代理，代理对象持有 Session 引用。
  - 每次调用代理对象的方法时，代理会从当前 Session 获取对应的真实 Bean。
1. **Session 销毁**：

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_SESSION, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class AgentSessionContext implements HttpSessionListener {

    @PreDestroy
    public void cleanup() {
        // Session 销毁时清理资源
        conversationHistory.clear();
    }
}
```
1. **Agent 场景实战**：每个用户的 Agent 对话历史存储在 Session 作用域 Bean 中，不同用户的对话完全隔离，Session 过期后自动清理上下文，避免内存泄漏。

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
只说了&quot;用 Session 作用域&quot;
</td>
<td>
完整 Session 上下文管理，包含代理和清理
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ScopedProxyMode 的作用
</td>
<td>
解释代理模式和 Session 绑定的原理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 会话管理的完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道作用域但不会设计
</td>
<td>
能设计会话级别的上下文管理方案
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
Singleton Bean 注入 Request 作用域 Bean 如何解决？
</td>
<td>
类似作用域陷阱，解决方案相同
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@RefreshScope 的实现原理？
</td>
<td>
基于 Scope 代理的动态刷新机制
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：基于 Scope 代理的动态刷新机制，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring 的 ThreadLocal 和 Session 作用域的区别？
</td>
<td>
线程隔离 vs 会话隔离
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

## Spring 配置属性绑定

### Spring 配置属性绑定

#### 1、基础题：@Value、@ConfigurationProperties、Environment 三种配置读取方式的区别？

**难度级别**：⭐⭐（配置读取、类型安全、松散绑定）

**Answer**
1. **@Value**：
  - 读取单个配置值，支持 SpEL 表达式。
  - 示例：`@Value("${agent.api-key}")`。
1. **@ConfigurationProperties**：
  - 批量绑定配置到 Bean，支持类型安全、松散绑定、JSR-303 校验。
  - 示例：`@ConfigurationProperties(prefix = "agent")`。
1. **Environment**：
  - 编程式读取配置，可以访问所有属性源。
  - 示例：`environment.getProperty("agent.api-key")`。
1. **选择建议**：
  - 少量配置用 `@Value`。
  - 批量配置用 `@ConfigurationProperties`（推荐）。
  - 动态读取用 `Environment`。

---

#### 2、进阶题：PropertySource 的加载优先级？如何实现配置动态刷新（@RefreshScope）？

**难度级别**：⭐⭐⭐⭐（配置优先级、动态刷新、Scope 代理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- PropertySource 加载优先级（从高到低）
- @RefreshScope 动态刷新
- 配置中心集成
- 动态刷新限制
- 原理：@RefreshScope 基于 GenericScope，Bean 是代理对象，配置变更时销毁旧 Bean，创建新 Bean。
- 触发：通过 /actuator/refresh 端点或配置中心（如 Nacos、Apollo）推送变更。

**2️⃣ Impressive Answer**
1. **PropertySource 加载优先级**（从高到低）：
  1. 命令行参数（`--agent.api-key=xxx`）
  1. ServletConfig 初始化参数
  1. ServletContext 初始化参数
  1. JNDI `java:comp/env`
  1. JVM 系统属性（`System.getProperties()`）
  1. 操作系统环境变量
  1. JAR 包外的 `application-{profile}.properties`
  1. JAR 包内的 `application-{profile}.properties`
  1. JAR 包外的 `application.properties`
  1. JAR 包内的 `application.properties`
  1. `@PropertySource` 注解
  1. 默认属性
1. **@RefreshScope 动态刷新**：

```java
@RefreshScope  // 配置变更时刷新 Bean
@ConfigurationProperties(prefix = "agent")
@Component
public class AgentProperties {
    private String apiKey;
    private double temperature;

    // getters and setters
}
```

```
- 原理：`@RefreshScope` 基于 `GenericScope`，Bean 是代理对象，配置变更时销毁旧 Bean，创建新 Bean。
- 触发：通过 `/actuator/refresh` 端点或配置中心（如 Nacos、Apollo）推送变更。
```
1. **配置中心集成**：

```java
@Configuration
@EnableDiscoveryClient
public class ConfigClientConfig {
    // Nacos 配置中心
}
```

```yaml
# bootstrap.yml
spring:
  cloud:
    nacos:
      config:
        server-addr: ${NACOS_SERVER}
        namespace: ${NAMESPACE}
        group: ${GROUP}
        data-id: agent-config.yaml
        auto-refresh: true  # 自动刷新
```
1. **动态刷新限制**：
  - `@Value` 注入的值不会自动刷新（需要重新绑定）。
  - `@ConfigurationProperties` 绑定的 Bean 会自动刷新。
  - 静态变量、构造器注入的值不会刷新。
1. **Agent 场景实战**：Agent 的 LLM 配置（模型名、temperature、API Key）通过 Nacos 配置中心管理，使用 `@RefreshScope` 实现动态热更新，无需重启服务。

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
只说了&quot;命令行 &gt; 环境变量 &gt; 配置文件&quot;
</td>
<td>
完整 12 级优先级，每级都有明确来源
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @RefreshScope 的代理原理
</td>
<td>
解释 GenericScope 的代理机制和刷新流程
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合配置中心
</td>
<td>
给出 Nacos 配置中心的集成方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道优先级但不深入
</td>
<td>
理解配置加载的设计意图和动态刷新机制
</td>
</tr>
</table>

---

#### 3、场景题：Agent 的 LLM 配置（模型名、temperature、API Key）如何用配置中心动态热更新？

**难度级别**：⭐⭐⭐（配置中心、动态刷新、@RefreshScope）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 配置类定义
- 使用配置
- Nacos 配置中心集成
- 手动刷新
- 监听配置变更

**2️⃣ Impressive Answer**
1. **配置类定义**：

```java
@RefreshScope  // 动态刷新
@ConfigurationProperties(prefix = "agent.llm")
@Component
@Validated
public class LLmProperties {
    @NotBlank
    private String provider = "openai";

    @NotBlank
    private String apiKey;

    @Min(0) @Max(2)
    private double temperature = 0.7;

    private int maxTokens = 2048;

    private Map<String, String> customParams = new HashMap<>();

    // getters and setters
}
```
1. **使用配置**：

```java
@Service
public class LLMService {
    @Autowired
    private LLMProperties llmProperties;  // 代理对象

    public String chat(String prompt) {
        // 每次调用都会从代理获取最新配置
        return llmProperties.getProvider().equals("openai")
            ? callOpenAI(prompt)
            : callClaude(prompt);
    }
}
```
1. **Nacos 配置中心集成**：

```yaml
# bootstrap.yml
spring:
  application:
    name: agent-service
  cloud:
    nacos:
      config:
        server-addr: 127.0.0.1:8848
        namespace: dev
        group: AGENT_GROUP
        data-id: agent-service.yaml
        auto-refresh: true  # 自动刷新
        file-extension: yaml
```

```yaml
# Nacos 配置：agent-service.yaml
agent:
  llm:
    provider: openai
    api-key: sk-xxx
    temperature: 0.7
    max-tokens: 2048
```
1. **手动刷新**：

```bash
# 调用刷新端点
curl -X POST http://localhost:8080/actuator/refresh
```
1. **监听配置变更**：

```java
@Component
public class ConfigChangeListener {

    @EventListener
    public void onRefreshScopeRefreshed(RefreshScopeRefreshedEvent event) {
        log.info("Configuration refreshed: {}", event.getName());
        // 可以在这里做额外的处理，比如重新初始化连接池
    }
}
```
1. **Agent 场景实战**：Agent 服务部署到生产环境后，通过 Nacos 配置中心动态调整 LLM 的 temperature 和 maxTokens，优化回答质量，无需重启服务，实现零停机配置更新。

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
只说了&quot;用 @RefreshScope&quot;
</td>
<td>
完整配置中心集成方案，包含 Nacos 和手动刷新
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 auto-refresh 的机制
</td>
<td>
解释 Nacos 的长轮询监听机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent LLM 配置热更新的完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道注解但不会集成
</td>
<td>
能设计生产级的配置管理方案
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
@ConfigurationProperties 的松散绑定规则？
</td>
<td>
支持驼峰、下划线、连字符等多种格式
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：支持驼峰、下划线、连字符等多种格式，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
@Value 支持的 SpEL 表达式有哪些？
</td>
<td>
动态计算配置值
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：动态计算配置值，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring Cloud Config 和 Nacos 的区别？
</td>
<td>
配置中心选型
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

## Spring 异步与调度

### Spring 异步与调度

#### 1、基础题：@Scheduled 注解如何使用？cron 表达式如何编写？

**难度级别**：⭐⭐（@EnableScheduling、fixedRate、fixedDelay、cron）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三种调度方式
- 常用 Cron 示例
- 0 0 2 * * ?：每天凌晨 2 点
- 0 0/5 * * * ?：每 5 分钟
- 0 0 12 ? * MON-FRI：周一到周五中午 12 点
- 0 0 12 L * ?：每月最后一天中午 12 点

**2️⃣ Impressive Answer**
1. **前置配置**：在启动类或配置类上加 `@EnableScheduling` 注解。
1. **三种调度方式**：

```java
@Scheduled(fixedRate = 5000)  // 固定频率（上次开始后 5 秒执行，不考虑上次的执行时间）
public void fixedRateTask() { ... }

@Scheduled(fixedDelay = 5000)  // 固定延迟（上次结束后 5 秒执行）
public void fixedDelayTask() { ... }

@Scheduled(initialDelay = 1000, fixedRate = 5000)  // 初始延迟 1 秒，然后每 5 秒执行
public void initialDelayTask() { ... }

@Scheduled(cron = "0 0 2 * * ?")  // 每天凌晨 2 点执行
public void cronTask() { ... }
```
1. **Cron 表达式格式**：`秒分时日月周 [年]`

<table>
<tr>
<td>
字段
</td>
<td>
允许值
</td>
<td>
特殊字符
</td>
</tr>
<tr>
<td>
秒
</td>
<td>
0-59
</td>
<td>
<code>, - * /</code>
</td>
</tr>
<tr>
<td>
分
</td>
<td>
0-59
</td>
<td>
<code>, - * /</code>
</td>
</tr>
<tr>
<td>
时
</td>
<td>
0-23
</td>
<td>
<code>, - * /</code>
</td>
</tr>
<tr>
<td>
日
</td>
<td>
1-31
</td>
<td>
<code>, - * / ? L W C</code>
</td>
</tr>
<tr>
<td>
月
</td>
<td>
1-12
</td>
<td>
<code>, - * /</code>
</td>
</tr>
<tr>
<td>
周
</td>
<td>
1-7
</td>
<td>
<code>, - * / ? L C #</code>
</td>
</tr>
</table>
1. **常用 Cron 示例**：
  - `0 0 2 * * ?`：每天凌晨 2 点
  - `0 0/5 * * * ?`：每 5 分钟
  - `0 0 12 ? * MON-FRI`：周一到周五中午 12 点
  - `0 0 12 L * ?`：每月最后一天中午 12 点
  - `0 15 10 ? * 6L`：每月最后一个周五上午 10:15
1. **注意事项**：默认单线程执行，上一个任务未完成时下一个任务会阻塞。需要并行执行时配置线程池。

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
简单描述三种方式
</td>
<td>
包含参数含义、Cron 格式、常用示例
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道单线程阻塞问题
</td>
<td>
清楚默认单线程和线程池配置
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有 Cron 示例
</td>
<td>
有生产环境 Cron 表达式经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 @Scheduled
</td>
<td>
理解定时任务的配置和限制
</td>
</tr>
</table>

---

#### 2、进阶题：Spring 定时任务的底层实现是什么？TaskScheduler 和 ThreadPoolTaskScheduler 的关系？分布式环境下如何避免重复执行？

**难度级别**：⭐⭐⭐（TaskScheduler、线程池配置、分布式锁、XXL-Job）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 底层实现原理
- TaskScheduler 层次结构
- 线程池配置
- 分布式环境避免重复执行
- @EnableScheduling 导入 SchedulingConfiguration，注册 ScheduledAnnotationBeanPostProcessor。
- ScheduledAnnotationBeanPostProcessor 扫描 @Scheduled 注解，注册定时任务到 TaskScheduler。

**2️⃣ Impressive Answer**
1. **底层实现原理**：
  - `@EnableScheduling` 导入 `SchedulingConfiguration`，注册 `ScheduledAnnotationBeanPostProcessor`。
  - `ScheduledAnnotationBeanPostProcessor` 扫描 @Scheduled 注解，注册定时任务到 `TaskScheduler`。
  - `TaskScheduler` 根据调度策略（fixedRate、fixedDelay、cron）提交任务到线程池执行。
1. **TaskScheduler 层次结构**：
  - `TaskScheduler`：定时任务调度接口，定义了 `schedule()`、`scheduleAtFixedRate()` 等方法。
  - `ThreadPoolTaskScheduler`：基于 `ThreadPoolTaskExecutor` 的实现，支持并行执行。
  - `ConcurrentTaskScheduler`：基于 `ScheduledExecutorService` 的实现。
1. **线程池配置**：

```java
@Configuration
@EnableScheduling
public class ScheduleConfig {

    @Bean
    public TaskScheduler taskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(10);           // 线程池大小
        scheduler.setThreadNamePrefix("scheduled-");
        scheduler.setRejectedExecutionHandler(
            new ThreadPoolExecutor.CallerRunsPolicy());
        scheduler.setWaitForTasksToCompleteOnShutdown(true);  // 优雅停机
        scheduler.setAwaitTerminationSeconds(60);
        scheduler.initialize();
        return scheduler;
    }
}
```
1. **分布式环境避免重复执行**：
    **方案一：分布式锁（Redis）**

```java
@Scheduled(cron = "0 0 2 * * ?")
public void dailyCleanup() {
    String lockKey = "lock:daily:cleanup";
    try {
        boolean locked = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "1", Duration.ofHours(1));
        if (!locked) {
            log.info("Task already running on another instance");
            return;
        }
        // 执行任务
        cleanupExpiredData();
    } finally {
        redisTemplate.delete(lockKey);
    }
}
```

```
**方案二：数据库唯一约束**
```

```java
@Scheduled(cron = "0 0 2 * * ?")
public void dailyCleanup() {
    try {
        taskExecutionRepository.insert("daily:cleanup", LocalDateTime.now());
    } catch (DuplicateKeyException e) {
        log.info("Task already running on another instance");
        return;
    }
    // 执行任务
    cleanupExpiredData();
}
```

```
**方案三：XXL-Job / ElasticJob**（推荐）：使用分布式调度框架，支持分片广播、故障转移、动态配置。
```
1. **Agent 场景**：定期清理过期对话记录、刷新工具列表、统计 Token 消耗。使用 XXL-Job 的分片广播功能，每个实例处理部分数据，提升效率。

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
只说了底层和分布式锁
</td>
<td>
完整方案：原理→线程池→分布式锁→XXL-Job
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 TaskScheduler 层次
</td>
<td>
清楚接口和实现的关系
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到 XXL-Job
</td>
<td>
有生产环境分布式调度框架经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道定时任务
</td>
<td>
有分布式定时任务的完整方案
</td>
</tr>
</table>

---

#### 2、进阶题：@Async 的线程池隔离如何配置？@Async 和事务的关系？

**难度级别**：⭐⭐⭐（线程池配置、事务传播、异步事务）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 线程池隔离配置
- 指定线程池
- @Async 和事务的关系
- 异步事务的注意事项
- 不会：异步方法继承调用方的事务，因为不在同一个线程。
- 异步方法需要自己开启事务（@Transactional）。

**2️⃣ Impressive Answer**
1. **线程池隔离配置**：

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("agentExecutor")
    public Executor agentExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("agent-async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }

    @Bean("toolExecutor")
    public Executor toolExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(50);
        executor.setThreadNamePrefix("tool-async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.AbortPolicy());
        executor.initialize();
        return executor;
    }
}
```
1. **指定线程池**：

```java
@Service
public class AgentService {
    @Async("agentExecutor")  // 使用 agentExecutor 线程池
    public CompletableFuture<AgentResult> executeAsync(AgentRequest request) {
        return CompletableFuture.completedFuture(doExecute(request));
    }
}

@Service
public class ToolService {
    @Async("toolExecutor")  // 使用 toolExecutor 线程池
    public CompletableFuture<ToolResponse> callAsync(ToolRequest request) {
        return CompletableFuture.completedFuture(doCall(request));
    }
}
```
1. **@Async 和事务的关系**：
  - 异步方法**不会**继承调用方的事务，因为不在同一个线程。
  - 异步方法需要自己开启事务（`@Transactional`）。
  - 示例：

```java
@Service
public class AgentService {
    @Transactional
    public AgentResult execute(AgentRequest request) {
        // 主事务
        AgentResult result = doExecute(request);
        agentRepository.save(result);  // 在主事务中

        asyncService.saveAsync(result);  // 异步方法，不在主事务中
        return result;
    }
}

@Service
public class AsyncService {
    @Async
    @Transactional  // 需要自己开启事务
    public void saveAsync(AgentResult result) {
        asyncRepository.save(result);  // 在独立事务中
    }
}
```
1. **异步事务的注意事项**：
  - 异步方法无法回滚主事务。
  - 主事务无法感知异步方法的异常。
  - 如果需要事务一致性，应该使用同步方法或分布式事务。
1. **Agent 场景实战**：Agent 执行完成后，异步保存日志到数据库（`@Async("agentExecutor")`），异步发送通知（`@Async("notificationExecutor")`），两者使用不同的线程池隔离，避免互相影响。

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
只说了&quot;用 @Async 指定线程池&quot;
</td>
<td>
完整线程池隔离配置，包含拒绝策略
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道异步事务的传播机制
</td>
<td>
解释异步方法不会继承主事务的原因
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 异步任务的线程池隔离方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道注解但不会配置
</td>
<td>
能设计生产级的异步任务方案
</td>
</tr>
</table>

---

#### 3、场景题：Agent 需要定期清理过期的对话记录、定期刷新工具列表、定期统计 Token 消耗，如何用 Spring 定时任务实现并保证分布式环境下不重复执行？

**难度级别**：⭐⭐⭐（多任务调度、分布式锁、故障转移、监控）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 定时任务设计
- 分布式锁实现（使用 Shedlock）
- 故障转移与重试
- 监控与告警

**2️⃣ Impressive Answer**
1. **定时任务设计**：

```java
@Component
public class AgentScheduledTasks {

    // 每天凌晨 3 点清理过期对话（保留 30 天）
    @Scheduled(cron = "0 0 3 * * ?")
    @SchedulerLock(name = "cleanupExpiredConversations",
                  lockAtMostFor = "2h", lockAtLeastFor = "1h")
    public void cleanupExpiredConversations() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(30);
        int deleted = conversationRepository.deleteByCreatedAtBefore(cutoff);
        log.info("Deleted {} expired conversations", deleted);
    }

    // 每小时刷新工具列表
    @Scheduled(cron = "0 0 * * * ?")
    @SchedulerLock(name = "refreshToolList",
                  lockAtMostFor = "55m", lockAtLeastFor = "50m")
    public void refreshToolList() {
        List<ToolDefinition> tools = toolRegistry.fetchLatestTools();
        toolRegistry.updateTools(tools);
        log.info("Refreshed {} tools", tools.size());
    }

    // 每天凌晨 4 点统计 Token 消耗
    @Scheduled(cron = "0 0 4 * * ?")
    @SchedulerLock(name = "aggregateTokenUsage",
                  lockAtMostFor = "1h", lockAtLeastFor = "50m")
    public void aggregateTokenUsage() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        TokenUsageReport report = tokenUsageService.aggregate(yesterday);
        reportService.save(report);
        log.info("Token usage report: {}", report);
    }
}
```
1. **分布式锁实现**（使用 Shedlock）：

```java
@Configuration
@EnableSchedulerLock(defaultLockAtMostFor = "1h", defaultLockAtLeastFor = "50m")
public class ShedlockConfig {
    @Bean
    public LockProvider lockProvider(DataSource dataSource) {
        return new JdbcTemplateLockProvider(
            JdbcTemplateLockProvider.Configuration.builder()
                .withJdbcTemplate(new JdbcTemplate(dataSource))
                .usingDbTime()
                .build()
        );
    }
}
```
1. **故障转移与重试**：

```java
@Scheduled(cron = "0 0 3 * * ?")
@Retryable(maxAttempts = 3, backoff = @Backoff(delay = 1000))
public void cleanupExpiredConversations() {
    try {
        // 执行任务
    } catch (Exception e) {
        log.error("Task failed, will retry", e);
        throw e;  // 触发重试
    }
}

@Recover
public void recover(Exception e) {
    log.error("Task failed after 3 retries, sending alert", e);
    alertService.send("Scheduled task failed: " + e.getMessage());
}
```
1. **监控与告警**：

```java
@Scheduled(cron = "0 0 3 * * ?")
public void cleanupExpiredConversations() {
    Timer.Sample sample = Timer.start(meterRegistry);
    try {
        // 执行任务
        sample.stop(Timer.builder("scheduled.task.duration")
            .tag("task", "cleanupConversations")
            .register(meterRegistry));
        meterRegistry.counter("scheduled.task.success",
            "task", "cleanupConversations").increment();
    } catch (Exception e) {
        meterRegistry.counter("scheduled.task.failure",
            "task", "cleanupConversations").increment();
        throw e;
    }
}
```
1. **优雅停机**：配置 `setWaitForTasksToCompleteOnShutdown(true)`，停机时等待正在执行的任务完成。

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
只说了三个定时任务
</td>
<td>
完整方案：任务设计→分布式锁→重试→监控→停机
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Shedlock 和重试
</td>
<td>
清楚分布式锁和故障转移机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有监控和告警
</td>
<td>
有生产环境定时任务的完整运维经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会写定时任务
</td>
<td>
有分布式定时任务的工程化能力
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
XXL-Job 的核心原理是什么？
</td>
<td>
分布式调度框架的对比
</td>
<td>
答：分布式题先明确一致性、可用性和性能目标，再讲协议或方案；落地时补超时、重试、幂等、监控和故障恢复。
</td>
</tr>
<tr>
<td>
如何实现定时任务的动态配置？
</td>
<td>
生产环境的灵活调度需求
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：生产环境的灵活调度需求，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring Boot 的优雅停机如何实现？
</td>
<td>
定时任务的停机策略
</td>
<td>
答：配置方式；停机流程；超时控制；停止接受新请求（Tomcat/Undertow 拒绝新连接）
</td>
</tr>
</table>

---

#### 3、场景题：Agent 批量工具调用如何用 @Async + CompletableFuture 实现并发执行，控制超时和异常？

**难度级别**：⭐⭐⭐⭐（并发控制、超时处理、异常处理、CompletableFuture）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 异步工具调用
- 批量并发调用
- 超时控制
- 异常处理

**2️⃣ Impressive Answer**
1. **异步工具调用**：

```java
@Service
public class ToolService {
    @Async("toolExecutor")
    public CompletableFuture<ToolResponse> callAsync(ToolRequest request) {
        try {
            ToolResponse response = doCall(request);
            return CompletableFuture.completedFuture(response);
        } catch (Exception e) {
            return CompletableFuture.failedFuture(e);
        }
    }
}
```
1. **批量并发调用**：

```java
@Service
public class AgentService {
    @Autowired
    private ToolService toolService;

    public Map<String, ToolResponse> batchCall(List<ToolRequest> requests, long timeout, TimeUnit unit) {
        // 1. 提交所有异步任务
        List<CompletableFuture<ToolResponse>> futures = requests.stream()
            .map(toolService::callAsync)
            .toList();

        // 2. 等待所有完成，设置超时
        CompletableFuture<Void> allFutures = CompletableFuture.allOf(
            futures.toArray(new CompletableFuture[0])
        );

        try {
            allFutures.get(timeout, unit);
        } catch (TimeoutException e) {
            // 超时处理
            futures.forEach(f -> f.cancel(true));
            throw new AgentException("Tool call timeout", e);
        } catch (Exception e) {
            throw new AgentException("Tool call failed", e);
        }

        // 3. 收集结果
        Map<String, ToolResponse> results = new HashMap<>();
        for (int i = 0; i < requests.size(); i++) {
            ToolRequest request = requests.get(i);
            CompletableFuture<ToolResponse> future = futures.get(i);
            try {
                ToolResponse response = future.get();
                results.put(request.getToolId(), response);
            } catch (Exception e) {
                // 单个工具失败，记录但不影响其他工具
                log.error("Tool {} failed: {}", request.getToolId(), e.getMessage());
                results.put(request.getToolId(), ToolResponse.failed(e));
            }
        }

        return results;
    }
}
```
1. **超时控制**：

```java
@Service
public class ToolService {
    @Async("toolExecutor")
    public CompletableFuture<ToolResponse> callAsyncWithTimeout(ToolRequest request, long timeout, TimeUnit unit) {
        return CompletableFuture.supplyAsync(() -> doCall(request))
            .orTimeout(timeout, unit)  // 单个调用超时
            .exceptionally(e -> {
                if (e instanceof TimeoutException) {
                    return ToolResponse.timeout();
                }
                return ToolResponse.failed(e);
            });
    }
}
```
1. **异常处理**：

```java
@Service
public class AgentService {
    public Map<String, ToolResponse> batchCallWithErrorHandling(List<ToolRequest> requests) {
        List<CompletableFuture<ToolResponse>> futures = requests.stream()
            .map(toolService::callAsync)
            .toList();

        CompletableFuture<Void> allFutures = CompletableFuture.allOf(
            futures.toArray(new CompletableFuture[0])
        ).exceptionally(e -> {
            // 全局异常处理
            log.error("Batch tool call failed: {}", e.getMessage());
            return null;
        });

        allFutures.join();  // 等待所有完成

        // 收集结果，处理异常
        return futures.stream()
            .collect(Collectors.toMap(
                f -> f.join().getToolId(),
                f -> {
                    try {
                        return f.join();
                    } catch (Exception e) {
                        return ToolResponse.failed(e);
                    }
                }
            ));
    }
}
```
1. **Agent 场景实战**：Agent 需要同时调用搜索工具、计算工具、天气工具获取信息，使用 `@Async` 并发执行，设置 5 秒超时，单个工具失败不影响其他工具，最后聚合所有结果返回给 LLM。

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
只说了&quot;用 CompletableFuture.allOf&quot;
</td>
<td>
完整批量并发方案，包含超时和异常处理
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 orTimeout 的用法
</td>
<td>
解释单调用超时和整体超时的区别
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 批量工具调用的完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道 CompletableFuture 但不会设计
</td>
<td>
能设计生产级的并发控制方案
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
@Scheduled 的 cron 表达式语法？
</td>
<td>
定时任务的时间配置
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：定时任务的时间配置，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
CompletableFuture 的常用方法（thenApply、thenCompose、exceptionally）？
</td>
<td>
异步编程的组合式 API
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：异步编程的组合式 API，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring 的线程池监控和调优？
</td>
<td>
生产环境线程池管理
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
</table>

---

## Spring 测试体系

### Spring 测试体系

#### 1、基础题：@SpringBootTest vs @WebMvcTest vs @DataJpaTest 的区别？

**难度级别**：⭐⭐（测试切片、集成测试、单元测试）

**Answer**
1. **@SpringBootTest**：
  - 完整集成测试，启动整个 Spring 上下文。
  - 适合测试完整流程，但启动慢。
1. **@WebMvcTest**：
  - Web 层切片测试，只加载 Controller 相关的 Bean。
  - 适合测试 Controller，启动快。
1. **@DataJpaTest**：
  - 数据访问层切片测试，只加载 Repository 相关的 Bean。
  - 适合测试 Repository，自动配置内存数据库。
1. **选择建议**：
  - 测试 Controller 用 `@WebMvcTest`。
  - 测试 Repository 用 `@DataJpaTest`。
  - 测试完整流程用 `@SpringBootTest`。

---

#### 2、进阶题：如何用 @MockBean 和 @SpyBean 隔离外部依赖？两者的区别？

**难度级别**：⭐⭐⭐（Mock 隔离、Spy 部分模拟、测试隔离）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- @MockBean 完全模拟
- @SpyBean 部分模拟
- 区别对比
- Mock LLM 响应
- @MockBean：完全模拟，所有方法都需要 Mock，适合隔离外部依赖。
- @SpyBean：部分模拟，可以调用真实方法，适合需要部分真实行为的场景。

**2️⃣ Impressive Answer**
1. **@MockBean 完全模拟**：

```java
@WebMvcTest(AgentController.class)
public class AgentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean  // 完全 Mock，所有方法都是模拟的
    private AgentService agentService;

    @Test
    public void testChat() throws Exception {
        // Mock 返回值
        when(agentService.chat(any()))
            .thenReturn(AgentResponse.success("Hello"));

        mockMvc.perform(post("/api/agent/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"prompt\":\"Hi\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").value("Hello"));
    }
}
```
1. **@SpyBean 部分模拟**：

```java
@SpringBootTest
public class AgentServiceTest {

    @Autowired
    private AgentService agentService;

    @SpyBean  // 部分 Mock，真实方法可以调用
    private LLMService llmService;

    @Test
    public void testChat() {
        // Mock LLM 调用，但其他方法真实执行
        when(llmService.chat(any()))
            .thenReturn(LLMResponse.success("Hello"));

        AgentResponse response = agentService.chat(new AgentRequest("Hi"));
        assertEquals("Hello", response.getContent());
    }
}
```
1. **区别对比**：
  - `@MockBean`：完全模拟，所有方法都需要 Mock，适合隔离外部依赖。
  - `@SpyBean`：部分模拟，可以调用真实方法，适合需要部分真实行为的场景。
1. **Mock LLM 响应**：

```java
@WebMvcTest(AgentController.class)
public class AgentControllerTest {

    @MockBean
    private AgentService agentService;

    @Test
    public void testChatWithToolCall() {
        // Mock Agent 调用工具
        ToolResponse toolResponse = ToolResponse.success("Weather: Sunny");
        when(agentService.callTool("weather-tool", any()))
            .thenReturn(CompletableFuture.completedFuture(toolResponse));

        // Mock LLM 响应
        when(agentService.chat(any()))
            .thenReturn(AgentResponse.success("Today is sunny"));

        // 测试完整流程
    }
}
```
1. **Agent 场景实战**：测试 Agent 工具调用链路时，用 `@MockBean` Mock 掉 LLMService 和 ToolService，模拟工具调用和 LLM 响应，验证 Agent 的决策逻辑，无需真实调用外部服务。

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
只说了&quot;@MockBean 完全 Mock，@SpyBean 部分 Mock&quot;
</td>
<td>
完整测试示例，包含 Mock 和 Spy 的使用场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道测试切片的隔离机制
</td>
<td>
解释 @WebMvcTest 只加载 Controller 的原理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 工具调用链路的测试方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道注解但不会设计测试
</td>
<td>
能设计完整的测试隔离方案
</td>
</tr>
</table>

---

#### 3、场景题：如何对 Agent 工具调用链路做集成测试，Mock LLM 响应并验证工具调用顺序？

**难度级别**：⭐⭐⭐⭐（集成测试、Mock 链路、验证顺序、InOrder）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 集成测试类
- 验证工具调用参数
- 验证调用次数
- 异常场景测试

**2️⃣ Impressive Answer**
1. **集成测试类**：

```java
@SpringBootTest
@AutoConfigureMockMvc
public class AgentIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private LLMService llmService;

    @MockBean
    private ToolService toolService;

    @Captor
    private ArgumentCaptor<ToolRequest> toolRequestCaptor;

    @Test
    public void testAgentToolCallSequence() throws Exception {
        // 1. Mock LLM 响应：第一次请求要求调用工具
        LLMResponse llmResponse1 = LLMResponse.builder()
            .content("I need to search for information")
            .toolCalls(List.of(
                ToolCall.builder().toolId("search-tool").parameters(Map.of("query", "Java")).build()
            ))
            .build();
        when(llmService.chat(any())).thenReturn(llmResponse1);

        // 2. Mock 工具响应
        ToolResponse toolResponse = ToolResponse.success("Java is a programming language");
        when(toolService.call(any())).thenReturn(CompletableFuture.completedFuture(toolResponse));

        // 3. Mock LLM 响应：第二次请求基于工具结果回答
        LLMResponse llmResponse2 = LLMResponse.builder()
            .content("Java is a programming language created by Sun Microsystems")
            .build();
        when(llmService.chat(any())).thenReturn(llmResponse2);

        // 4. 执行 Agent 调用
        mockMvc.perform(post("/api/agent/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"prompt\":\"What is Java?\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").value("Java is a programming language created by Sun Microsystems"));

        // 5. 验证工具调用顺序
        InOrder inOrder = inOrder(llmService, toolService);

        // 验证：第一次调用 LLM
        inOrder.verify(llmService).chat(argThat(req ->
            req.getPrompt().equals("What is Java?")
        ));

        // 验证：调用工具
        inOrder.verify(toolService).call(argThat(req ->
            req.getToolId().equals("search-tool") &&
            req.getParameters().get("query").equals("Java")
        ));

        // 验证：第二次调用 LLM（包含工具结果）
        inOrder.verify(llmService).chat(argThat(req ->
            req.getMessages().stream().anyMatch(msg ->
                msg.getContent().contains("Java is a programming language")
            )
        ));
    }
}
```
1. **验证工具调用参数**：

```java
@Test
public void testToolCallParameters() {
    // ... Mock 设置

    mockMvc.perform(post("/api/agent/chat")
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"prompt\":\"Search for Java\"}"))
        .andExpect(status().isOk());

    // 验证工具调用参数
    verify(toolService).call(toolRequestCaptor.capture());
    ToolRequest capturedRequest = toolRequestCaptor.getValue();

    assertEquals("search-tool", capturedRequest.getToolId());
    assertEquals("Java", capturedRequest.getParameters().get("query"));
}
```
1. **验证调用次数**：

```java
@Test
public void testToolCallCount() {
    // ... Mock 设置

    mockMvc.perform(post("/api/agent/chat")
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"prompt\":\"Search for Java\"}"))
        .andExpect(status().isOk());

    // 验证工具只调用了一次
    verify(toolService, times(1)).call(any());

    // 验证 LLM 调用了两次（初始请求 + 工具结果后的请求）
    verify(llmService, times(2)).chat(any());
}
```
1. **异常场景测试**：

```java
@Test
public void testToolCallFailure() throws Exception {
    // Mock 工具调用失败
    when(toolService.call(any()))
        .thenReturn(CompletableFuture.failedFuture(new RuntimeException("Tool failed")));

    // 验证 Agent 能够处理工具失败
    mockMvc.perform(post("/api/agent/chat")
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"prompt\":\"Search for Java\"}"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.content").value("Sorry, I encountered an error"));
}
```
1. **Agent 场景实战**：测试 Agent 的工具调用决策逻辑，Mock LLM 响应要求调用工具，Mock 工具返回结果，验证 Agent 是否正确调用工具、是否将工具结果传递给 LLM、最终回答是否符合预期。

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
只说了&quot;用 InOrder 验证顺序&quot;
</td>
<td>
完整集成测试，包含 Mock、验证、异常场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ArgumentCaptor 的用法
</td>
<td>
解释参数捕获和验证的机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有结合 Agent 场景
</td>
<td>
给出 Agent 工具调用链路的完整测试方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道测试注解但不会设计
</td>
<td>
能设计复杂的集成测试场景
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
@TestConfiguration 和 @TestPropertySource 的作用？
</td>
<td>
测试专用配置和属性覆盖
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：测试专用配置和属性覆盖，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
MockMvc 的使用方法和常用断言？
</td>
<td>
Web 层测试的核心工具
</td>
<td>
答：工具调用题要讲 schema 描述、参数校验、权限控制、超时重试、幂等和观测；核心是让模型会选、会用、用错能兜底。
</td>
</tr>
<tr>
<td>
Spring Test 的事务管理（@Transactional）？
</td>
<td>
测试事务回滚，避免污染数据库
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
</table>

---

### 3.2 Spring MVC 全局异常处理

#### 1、基础题：@ExceptionHandler 和 @ControllerAdvice 是什么？如何做全局异常处理？

**难度级别**：⭐⭐（异常处理、统一响应格式）

**Answer**
1. **@ExceptionHandler**：用于处理 Controller 方法抛出的特定异常，可以返回自定义的响应。
1. **@ControllerAdvice**：全局异常处理注解，标注在类上，该类中的 `@ExceptionHandler` 方法会应用到所有 Controller。
1. **全局异常处理示例**：

```java
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(Exception.class)
    @ResponseBody
    public ResponseEntity<ErrorResponse> handleException(Exception e) {
        ErrorResponse error = ErrorResponse.builder()
            .code(500)
            .message("Internal Server Error")
            .build();
        return ResponseEntity.status(500).body(error);
    }
}
```

---

#### 2、进阶题：Spring MVC 异常处理的优先级链是什么？多个 @ControllerAdvice 的执行顺序如何控制？

**难度级别**：⭐⭐⭐（异常处理优先级、@Order、HandlerExceptionResolver）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 异常处理优先级链
- @ControllerAdvice 的执行顺序
- 自定义 HandlerExceptionResolver
- 实践建议
- 默认顺序：Spring 按照类的名称字母顺序排序。
- @Order 控制：使用 @Order 注解指定优先级，值越小优先级越高。

**2️⃣ Impressive Answer**
1. **异常处理优先级链**：

```
Controller 方法内的 @ExceptionHandler
    → Controller 类内的 @ExceptionHandler
    → @ControllerAdvice 中的 @ExceptionHandler（按 @Order 排序）
    → HandlerExceptionResolver（自定义异常解析器）
    → 默认异常处理（返回 500 错误）
```
1. **@ControllerAdvice 的执行顺序**：
  - **默认顺序**：Spring 按照类的名称字母顺序排序。
  - **@Order 控制**：使用 `@Order` 注解指定优先级，值越小优先级越高。
  - **@Priority**：JSR-250 的 `@Priority` 注解也可以控制顺序。
1. **精确匹配优先**：`@ExceptionHandler` 会优先匹配最具体的异常类型。例如：

```java
@ExceptionHandler({BusinessException.class, RuntimeException.class})
public ResponseEntity<ErrorResponse> handleBusinessException(BusinessException e) {
    // 如果抛出 BusinessException，会进入这里
    return ResponseEntity.badRequest().body(ErrorResponse.from(e));
}

@ExceptionHandler(Exception.class)
public ResponseEntity<ErrorResponse> handleException(Exception e) {
    // 其他异常进入这里
    return ResponseEntity.internalServerError().body(ErrorResponse.from(e));
}
```
1. **自定义 HandlerExceptionResolver**：

```java
@Component
public class CustomExceptionResolver implements HandlerExceptionResolver {

    @Override
    public ModelAndView resolveException(HttpServletRequest request,
            HttpServletResponse response, Object handler, Exception ex) {
        // 自定义异常处理逻辑
        if (ex instanceof BusinessException) {
            response.setStatus(400);
            return new ModelAndView(new MappingJackson2JsonView(ErrorResponse.from(ex)));
        }
        return null;  // 返回 null 表示不处理，交给下一个 Resolver
    }
}
```
1. **实践建议**：
  - **分层处理**：业务异常用 `@ControllerAdvice` 统一处理，系统异常用 `HandlerExceptionResolver` 处理。
  - **精确匹配**：`@ExceptionHandler` 尽量精确匹配异常类型，避免用 `Exception.class` 兜底。
  - **响应格式**：统一错误响应格式，便于前端处理。

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
只说了&quot;就近原则&quot;
</td>
<td>
完整优先级链：Controller → @ControllerAdvice → Resolver
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @Order 的作用
</td>
<td>
解释 @Order 和精确匹配的优先级机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到自定义 Resolver
</td>
<td>
知道如何扩展异常处理机制
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
理解异常处理的设计和扩展机制
</td>
</tr>
</table>

---

#### 3、场景题：Agent 调用 LLM 超时、工具执行失败、参数校验失败，如何统一封装错误响应格式？

**难度级别**：⭐⭐⭐（异常分类、统一响应、错误码设计）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 定义错误码枚举
- 自定义异常类
- 统一响应格式
- 全局异常处理器
- Controller 使用示例
- 实践优化

**2️⃣ Impressive Answer**
1. **定义错误码枚举**：

```java
public enum ErrorCode {
    SUCCESS(0, "Success"),
    BAD_REQUEST(400, "Bad Request"),
    UNAUTHORIZED(401, "Unauthorized"),
    LLM_TIMEOUT(1001, "LLM call timeout"),
    TOOL_EXECUTION_FAILED(1002, "Tool execution failed"),
    VALIDATION_FAILED(1003, "Parameter validation failed"),
    INTERNAL_ERROR(500, "Internal server error");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public int getCode() { return code; }
    public String getMessage() { return message; }
}
```
1. **自定义异常类**：

```java
public class AgentException extends RuntimeException {
    private final ErrorCode errorCode;

    public AgentException(ErrorCode errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() { return errorCode; }
}

public class LlmTimeoutException extends AgentException {
    public LlmTimeoutException(String message) {
        super(ErrorCode.LLM_TIMEOUT, message);
    }
}

public class ToolExecutionException extends AgentException {
    public ToolExecutionException(String message) {
        super(ErrorCode.TOOL_EXECUTION_FAILED, message);
    }
}
```
1. **统一响应格式**：

```java
@Data
@Builder
public class ApiResponse<T> {
    private int code;
    private String message;
    private T data;

    public static <T> ApiResponse<T> success(T data) {
        return ApiResponse.<T>builder()
            .code(ErrorCode.SUCCESS.getCode())
            .message(ErrorCode.SUCCESS.getMessage())
            .data(data)
            .build();
    }

    public static <T> ApiResponse<T> error(ErrorCode errorCode, String message) {
        return ApiResponse.<T>builder()
            .code(errorCode.getCode())
            .message(message)
            .build();
    }
}
```
1. **全局异常处理器**：

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(LlmTimeoutException.class)
    public ApiResponse<Void> handleLlmTimeout(LlmTimeoutException e) {
        log.error("LLM timeout: {}", e.getMessage());
        return ApiResponse.error(e.getErrorCode(), e.getMessage());
    }

    @ExceptionHandler(ToolExecutionException.class)
    public ApiResponse<Void> handleToolExecution(ToolExecutionException e) {
        log.error("Tool execution failed: {}", e.getMessage());
        return ApiResponse.error(e.getErrorCode(), e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ApiResponse<Void> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage)
            .collect(Collectors.joining(", "));
        log.error("Validation failed: {}", message);
        return ApiResponse.error(ErrorCode.VALIDATION_FAILED, message);
    }

    @ExceptionHandler(Exception.class)
    public ApiResponse<Void> handleException(Exception e) {
        log.error("Unexpected error", e);
        return ApiResponse.error(ErrorCode.INTERNAL_ERROR, "Internal server error");
    }
}
```
1. **Controller 使用示例**：

```java
@RestController
@RequestMapping("/api/agent")
public class AgentController {

    @Autowired
    private LlmService llmService;

    @Autowired
    private ToolService toolService;

    @PostMapping("/chat")
    public ApiResponse<ChatResponse> chat(@Valid @RequestBody ChatRequest request) {
        try {
            // 调用 LLM
            ChatResponse response = llmService.chat(request);
            return ApiResponse.success(response);
        } catch (TimeoutException e) {
            throw new LlmTimeoutException("LLM call timeout: " + e.getMessage());
        }
    }

    @PostMapping("/tool")
    public ApiResponse<ToolResponse> executeTool(@Valid @RequestBody ToolRequest request) {
        try {
            ToolResponse response = toolService.execute(request);
            return ApiResponse.success(response);
        } catch (Exception e) {
            throw new ToolExecutionException("Tool execution failed: " + e.getMessage());
        }
    }
}
```
1. **实践优化**：
  - **错误码国际化**：错误消息支持多语言，根据请求头 `Accept-Language` 返回对应语言。
  - **错误详情**：开发环境返回详细错误栈，生产环境返回通用错误消息。
  - **监控告警**：对 LLM 超时、工具失败等异常进行监控和告警。

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
只说了&quot;用 @ExceptionHandler 捕获&quot;
</td>
<td>
完整方案：错误码枚举、自定义异常、统一响应
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道异常分类和错误码设计
</td>
<td>
精细异常分类，支持国际化
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有考虑监控和告警
</td>
<td>
提到开发/生产环境差异化、监控告警
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
能写出基础异常处理
</td>
<td>
能设计生产级的异常处理体系
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
如何实现参数校验（@Valid）？
</td>
<td>
@ExceptionHandler 可以处理校验异常
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：@ExceptionHandler 可以处理校验异常，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何实现自定义错误码？
</td>
<td>
错误码设计是异常处理的一部分
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：错误码设计是异常处理的一部分，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何实现异常监控和告警？
</td>
<td>
异常处理需要配合监控系统
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
</table>

---

### 3.3 Spring 配置管理与 Environment

#### 1、基础题：@Value、@ConfigurationProperties、Environment 三种读取配置的方式有什么区别？

**难度级别**：⭐⭐（配置注入、类型安全、松耦合）

**Answer**
1. **@Value**：直接注入单个配置值，支持 SpEL 表达式，适合简单配置。
1. **@ConfigurationProperties**：批量注入配置到 Bean，类型安全，支持嵌套对象，适合复杂配置。
1. **Environment**：编程式读取配置，灵活但繁琐，适合动态读取。
1. **区别**：
  - `@Value` 适合单个值，`@ConfigurationProperties` 适合批量配置。
  - `@ConfigurationProperties` 支持类型转换和校验，`@Value` 不支持。
  - `Environment` 可以在运行时动态读取，`@Value` 和 `@ConfigurationProperties` 是启动时注入。

---

#### 2、进阶题：Spring 的 PropertySource 优先级链是什么？如何实现配置的动态刷新（@RefreshScope）？

**难度级别**：⭐⭐⭐（配置优先级、动态刷新、Spring Cloud Config）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- PropertySource 优先级链（从高到低）
- 配置覆盖规则
- @RefreshScope 动态刷新
- 动态刷新实现细节
- 实践注意
- 后加载的优先级高：后面的 PropertySource 会覆盖前面的同名属性。

**2️⃣ Impressive Answer**
1. **PropertySource 优先级链**（从高到低）：

```
命令行参数（--server.port=8081）
    → ServletConfig 初始化参数
    → ServletContext 初始化参数
    → JNDI（java:comp/env）
    → JVM 系统属性（System.getProperties()）
    → 操作系统环境变量
    → RandomValuePropertySource（random.*）
    → JAR 包外的 application-{profile}.properties
    → JAR 包内的 application-{profile}.properties
    → JAR 包外的 application.properties
    → JAR 包内的 application.properties
    → @PropertySource 注解指定的配置文件
    → 默认属性（SpringApplication.setDefaultProperties）
```
1. **配置覆盖规则**：
  - **后加载的优先级高**：后面的 PropertySource 会覆盖前面的同名属性。
  - **Profile 优先**：激活的 Profile 配置会覆盖默认配置。
  - **命令行参数最高**：方便运维临时调整配置。
1. **@RefreshScope 动态刷新**：
  - **原理**：`@RefreshScope` 标注的 Bean 会被代理，配置刷新时，代理会重新创建 Bean 实例，注入新的配置值。
  - **使用**：

```java
@RefreshScope
@Component
@ConfigurationProperties(prefix = "agent.llm")
public class LlmConfig {
    private String apiKey;
    private String model;
    // getters and setters
}
```
- **刷新触发**：调用 `/actuator/refresh` 端点，Spring Cloud Config 会重新加载配置并刷新 `@RefreshScope` Bean。
1. **动态刷新实现细节**：
  - **RefreshScope**：是一个自定义 Scope，维护了一个 `Bean` 的缓存，刷新时清除缓存。
  - **ContextRefresher**：刷新 `Environment`，重新加载 PropertySource。
  - **Lifecycle**：销毁旧 Bean，创建新 Bean，重新注入依赖。
1. **实践注意**：
  - **限制**：`@RefreshScope` 只能刷新 `@Value` 和 `@ConfigurationProperties` 注入的配置，不能刷新 `@Bean` 方法的参数。
  - **性能**：频繁刷新会影响性能，建议配合消息队列实现配置变更通知。
  - **兼容性**：`@RefreshScope` 是 Spring Cloud 的功能，需要引入 `spring-cloud-context` 依赖。

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
只说了&quot;命令行参数 &gt; 环境变量&quot;
</td>
<td>
完整优先级链，12 个层级
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @RefreshScope 的原理
</td>
<td>
解释代理机制和缓存清除
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到刷新的限制和性能
</td>
<td>
知道刷新的限制和性能影响
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道基本优先级
</td>
<td>
理解配置加载和刷新的底层机制
</td>
</tr>
</table>

---

#### 3、场景题：Agent 的 LLM API Key、模型参数需要多环境隔离 + 运行时热更新，如何设计配置方案？

**难度级别**：⭐⭐⭐（多环境配置、动态刷新、安全隔离）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 多环境配置设计
- 配置类设计
- 动态刷新实现
- 配置热更新触发方式
- 安全隔离
- 配置验证

**2️⃣ Impressive Answer**
1. **多环境配置设计**：

```yaml
# application-common.yml（公共配置）
agent:
  llm:
    timeout: 30000
    max-retries: 3

# application-dev.yml（开发环境）
spring:
  profiles: dev
agent:
  llm:
    api-key: ${LLM_API_KEY:sk-dev-xxx}
    model: gpt-4
    endpoint: https://api.openai.com/v1

# application-prod.yml（生产环境）
spring:
  profiles: prod
agent:
  llm:
    api-key: ${LLM_API_KEY}  # 从环境变量读取，不在配置文件中硬编码
    model: gpt-4-turbo
    endpoint: https://api.openai.com/v1
```
1. **配置类设计**：

```java
@RefreshScope
@Component
@ConfigurationProperties(prefix = "agent.llm")
@Validated
public class LlmConfig {

    @NotBlank(message = "API Key cannot be blank")
    private String apiKey;

    @NotBlank(message = "Model cannot be blank")
    private String model;

    @NotBlank(message = "Endpoint cannot be blank")
    private String endpoint;

    @Min(value = 1000, message = "Timeout must be at least 1000ms")
    private Integer timeout = 30000;

    @Min(value = 0, message = "Max retries must be non-negative")
    private Integer maxRetries = 3;

    // getters and setters
}
```
1. **动态刷新实现**：

```java
@RestController
@RequestMapping("/api/admin/config")
public class ConfigController {

    @Autowired
    private LlmConfig llmConfig;

    @Autowired
    private ContextRefresher contextRefresher;

    @PostMapping("/refresh")
    public ApiResponse<Void> refreshConfig() {
        // 刷新配置
        Set<String> refreshedKeys = contextRefresher.refresh();
        log.info("Refreshed config keys: {}", refreshedKeys);
        return ApiResponse.success(null);
    }

    @GetMapping("/llm")
    public ApiResponse<LlmConfig> getLlmConfig() {
        return ApiResponse.success(llmConfig);
    }
}
```
1. **配置热更新触发方式**：
  - **手动触发**：调用 `/api/admin/config/refresh` 端点。
  - **自动触发**：配置中心（如 Nacos、Apollo）推送配置变更，监听变更事件自动刷新。
  - **定时刷新**：定时任务检查配置变更，自动刷新。
1. **安全隔离**：
  - **敏感配置加密**：使用 Jasypt 加密 API Key，配置文件中存储加密值。

```yaml
agent:
  llm:
    api-key: ENC(encrypted-api-key)
```
- **环境变量注入**：生产环境的 API Key 通过环境变量注入，不在配置文件中暴露。
- **权限控制**：配置刷新接口需要管理员权限，防止未授权访问。
1. **配置验证**：

```java
@Component
public class ConfigValidator implements ApplicationListener<EnvironmentChangeEvent> {

    @Autowired
    private LlmConfig llmConfig;

    @Override
    public void onApplicationEvent(EnvironmentChangeEvent event) {
        if (event.getKeys().contains("agent.llm.api-key")) {
            // 验证 API Key 是否有效
            if (!llmConfig.getApiKey().startsWith("sk-")) {
                log.error("Invalid API Key format");
                throw new IllegalStateException("Invalid API Key");
            }
        }
    }
}
```
1. **实践优化**：
  - **配置中心**：使用 Nacos、Apollo 等配置中心，支持配置版本管理、灰度发布。
  - **配置审计**：记录配置变更历史，支持回滚。
  - **降级策略**：配置刷新失败时，使用旧配置，避免服务不可用。

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
只说了&quot;多配置文件 + @RefreshScope&quot;
</td>
<td>
完整方案：多环境、动态刷新、安全隔离、验证
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道配置加密和验证
</td>
<td>
使用 Jasypt 加密，配置变更事件监听
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有考虑配置中心和审计
</td>
<td>
提到 Nacos/Apollo、配置审计、降级策略
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
能实现基础多环境配置
</td>
<td>
能设计生产级的配置管理方案
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
如何实现配置加密（Jasypt）？
</td>
<td>
敏感配置需要加密存储
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：敏感配置需要加密存储，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何实现配置中心（Nacos/Apollo）？
</td>
<td>
配置热更新的高级方案
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：配置热更新的高级方案，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何实现配置的版本管理和回滚？
</td>
<td>
配置审计和回滚是配置管理的重要功能
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：配置审计和回滚是配置管理的重要功能，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

### 3.4 Spring 异步与线程池

#### 1、基础题：@Async 注解的作用是什么？如何配置自定义线程池？

**难度级别**：⭐⭐（异步执行、线程池配置）

**Answer**
1. **@Async 作用**：将方法标记为异步执行，调用时会立即返回，方法在独立线程中执行。
1. **配置自定义线程池**：

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("taskExecutor")
    public TaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.initialize();
        return executor;
    }
}
```
1. **使用示例**：

```java
@Service
public class AsyncService {

    @Async("taskExecutor")
    public CompletableFuture<String> asyncMethod() {
        // 异步执行
        return CompletableFuture.completedFuture("done");
    }
}
```

---

#### 2、进阶题：@Async 的实现原理是什么（AOP + TaskExecutor）？为什么 @Async 在同类自调用时失效？

**难度级别**：⭐⭐⭐（AOP 代理、自调用失效、CGLIB）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- @Async 的实现原理
- 同类自调用失效原因
- AopContext 解决方案
- 线程池选择
- 异常处理
- AOP 代理：@Async 是一个 AOP 注解，Spring 会为标注了 @Async 的 Bean 创建代理（JDK 动态代理或 CGLIB）。

**2️⃣ Impressive Answer**
1. **@Async 的实现原理**：
  - **AOP 代理**：`@Async` 是一个 AOP 注解，Spring 会为标注了 `@Async` 的 Bean 创建代理（JDK 动态代理或 CGLIB）。
  - **拦截器**：`AsyncAnnotationBeanPostProcessor` 会注册一个 `AnnotationAsyncExecutionInterceptor`，拦截 `@Async` 方法调用。
  - **TaskExecutor**：拦截器将方法调用包装成 `Runnable`，提交到 `TaskExecutor` 线程池执行。
  - **返回值处理**：如果方法返回 `CompletableFuture`，拦截器会等待异步执行完成并返回结果。
1. **同类自调用失效原因**：
  - **代理机制**：Spring AOP 是基于代理的，只有通过代理调用的方法才会被拦截。
  - **自调用绕过代理**：在同一个类中，`this.asyncMethod()` 是直接调用，绕过了代理，因此 `@Async` 不生效。
  - **解决方案**：
    - **注入自己**：通过 `ApplicationContext` 获取代理 Bean，调用代理的方法。
    - **拆分方法**：将异步方法拆分到另一个类中。
    - **AopContext**：使用 `AopContext.currentProxy()` 获取当前代理。
1. **AopContext 解决方案**：

```java
@Service
public class AsyncService {

    @Async
    public CompletableFuture<String> asyncMethod() {
        return CompletableFuture.completedFuture("done");
    }

    public void callAsyncMethod() {
        // 获取代理，调用异步方法
        AsyncService proxy = (AsyncService) AopContext.currentProxy();
        proxy.asyncMethod();
    }
}
```

注意：需要配置 `@EnableAspectJAutoProxy(exposeProxy = true)`。
1. **线程池选择**：
  - **默认线程池**：Spring Boot 默认使用 `SimpleAsyncTaskExecutor`，每次调用创建新线程，不推荐生产使用。
  - **自定义线程池**：推荐配置 `ThreadPoolTaskExecutor`，复用线程，提高性能。
  - **线程池隔离**：不同业务使用不同线程池，避免相互影响。
1. **异常处理**：

```java
@Async
public CompletableFuture<String> asyncMethodWithException() {
    try {
        // 异步逻辑
        return CompletableFuture.completedFuture("done");
    } catch (Exception e) {
        return CompletableFuture.failedFuture(e);
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
只说了&quot;AOP 代理&quot;
</td>
<td>
完整原理：AOP 代理、拦截器、TaskExecutor
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道自调用失效的原因
</td>
<td>
解释代理机制和自调用绕过代理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到线程池选择和异常处理
</td>
<td>
知道线程池隔离、异常处理、AopContext
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道 @Async 的基本用法
</td>
<td>
理解 @Async 的底层机制和最佳实践
</td>
</tr>
</table>

---

#### 3、场景题：Agent 并发调用多个工具（并行 Tool Call），如何用 Spring 异步 + CompletableFuture 实现并发编排，并处理部分失败？

**难度级别**：⭐⭐⭐（并发编排、部分失败、超时控制）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 工具调用服务
- 并发编排
- 超时控制
- 部分失败处理
- 线程池配置
- 实践优化

**2️⃣ Impressive Answer**
1. **工具调用服务**：

```java
@Service
public class ToolService {

    @Autowired
    private TaskExecutor toolExecutor;

    @Async("toolExecutor")
    public CompletableFuture<ToolResult> callTool(ToolRequest request) {
        try {
            // 调用工具
            ToolResult result = doCallTool(request);
            return CompletableFuture.completedFuture(result);
        } catch (Exception e) {
            return CompletableFuture.failedFuture(e);
        }
    }

    private ToolResult doCallTool(ToolRequest request) {
        // 实际工具调用逻辑
        return ToolResult.builder()
            .name(request.getName())
            .data("result")
            .build();
    }
}
```
1. **并发编排**：

```java
@Service
public class AgentOrchestrator {

    @Autowired
    private ToolService toolService;

    public CompletableFuture<AgentResponse> orchestrateTools(List<ToolRequest> requests) {
        // 并发调用所有工具
        List<CompletableFuture<ToolResult>> futures = requests.stream()
            .map(toolService::callTool)
            .collect(Collectors.toList());

        // 等待所有任务完成（包括失败的任务）
        CompletableFuture<Void> allFutures = CompletableFuture.allOf(
            futures.toArray(new CompletableFuture[0])
        );

        // 处理结果
        return allFutures.thenApply(v -> {
            List<ToolResult> results = futures.stream()
                .map(future -> {
                    try {
                        return future.get();
                    } catch (Exception e) {
                        return ToolResult.builder()
                            .name("failed")
                            .error(e.getMessage())
                            .build();
                    }
                })
                .collect(Collectors.toList());

            return AgentResponse.builder()
                .results(results)
                .build();
        });
    }
}
```
1. **超时控制**：

```java
public CompletableFuture<AgentResponse> orchestrateToolsWithTimeout(
        List<ToolRequest> requests, long timeout, TimeUnit unit) {

    List<CompletableFuture<ToolResult>> futures = requests.stream()
        .map(request -> toolService.callTool(request)
            .orTimeout(timeout, unit)  // 单个工具超时
            .exceptionally(e -> ToolResult.builder()
                .name(request.getName())
                .error("Timeout")
                .build()))
        .collect(Collectors.toList());

    // 整体超时
    CompletableFuture<Void> allFutures = CompletableFuture.allOf(
        futures.toArray(new CompletableFuture[0])
    ).orTimeout(timeout * futures.size(), unit);

    return allFutures.thenApply(v -> {
        List<ToolResult> results = futures.stream()
            .map(future -> future.join())
            .collect(Collectors.toList());

        return AgentResponse.builder()
            .results(results)
            .build();
    });
}
```
1. **部分失败处理**：

```java
public CompletableFuture<AgentResponse> orchestrateToolsWithPartialFailure(
        List<ToolRequest> requests) {

    List<CompletableFuture<ToolResult>> futures = requests.stream()
        .map(request -> toolService.callTool(request)
            .handle((result, e) -> {
                if (e != null) {
                    return ToolResult.builder()
                        .name(request.getName())
                        .error(e.getMessage())
                        .build();
                }
                return result;
            }))
        .collect(Collectors.toList());

    return CompletableFuture.allOf(
        futures.toArray(new CompletableFuture[0])
    ).thenApply(v -> {
        List<ToolResult> results = futures.stream()
            .map(CompletableFuture::join)
            .collect(Collectors.toList());

        // 检查是否有失败的工具
        boolean hasFailure = results.stream()
            .anyMatch(r -> r.getError() != null);

        return AgentResponse.builder()
            .results(results)
            .hasFailure(hasFailure)
            .build();
    });
}
```
1. **线程池配置**：

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("toolExecutor")
    public TaskExecutor toolExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("tool-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```
1. **实践优化**：
  - **熔断降级**：使用 Resilience4j 实现熔断，连续失败时快速失败。
  - **限流**：限制并发工具调用的数量，避免资源耗尽。
  - **重试**：对失败的工具调用进行重试，提高成功率。

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
只说了&quot;@Async + CompletableFuture.allOf&quot;
</td>
<td>
完整方案：超时控制、部分失败处理、线程池配置
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道如何处理部分失败
</td>
<td>
使用 handle 方法处理异常，支持部分失败
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到熔断、限流、重试
</td>
<td>
提到 Resilience4j、限流、重试
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
能实现基础并发调用
</td>
<td>
能设计生产级的并发编排方案
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
CompletableFuture 的常用方法有哪些？
</td>
<td>
并发编排的核心 API
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：并发编排的核心 API，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
如何实现线程池监控？
</td>
<td>
线程池配置需要监控
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
如何实现异步任务的超时和重试？
</td>
<td>
并发调用的容错机制
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：并发调用的容错机制，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

### 3.5 Spring 事务底层原理

#### 1、基础题：编程式事务（TransactionTemplate）和声明式事务（@Transactional）的区别是什么？

**难度级别**：⭐⭐（事务管理、编程式 vs 声明式）

**Answer**
1. **编程式事务（TransactionTemplate）**：在代码中显式管理事务，使用 `TransactionTemplate.execute()` 包裹事务代码。
1. **声明式事务（@Transactional）**：通过注解声明事务，Spring AOP 自动管理事务，代码更简洁。
1. **区别**：
  - **编程式**：灵活但繁琐，适合复杂事务逻辑。
  - **声明式**：简洁但不够灵活，适合大多数场景。

---

#### 2、进阶题：Spring 事务的底层实现原理是什么？TransactionInterceptor + PlatformTransactionManager + ThreadLocal 如何协作？

**难度级别**：⭐⭐⭐（AOP 代理、事务管理器、ThreadLocal）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- Spring 事务的底层实现
- 事务执行流程
- ThreadLocal 的作用
- 事务传播机制
- 事务失效场景
- AOP 代理：@Transactional 是一个 AOP 注解，Spring 会为标注了 @Transactional 的 Bean 创建代理。

**2️⃣ Impressive Answer**
1. **Spring 事务的底层实现**：
  - **AOP 代理**：`@Transactional` 是一个 AOP 注解，Spring 会为标注了 `@Transactional` 的 Bean 创建代理。
  - **TransactionInterceptor**：拦截 `@Transactional` 方法调用，在方法执行前开启事务，执行后提交或回滚事务。
  - **PlatformTransactionManager**：事务管理器，负责事务的开启、提交、回滚。常用实现：
    - `DataSourceTransactionManager`：JDBC 事务管理器。
    - `JpaTransactionManager`：JPA 事务管理器。
    - `JtaTransactionManager`：JTA 分布式事务管理器。
  - **ThreadLocal**：`TransactionSynchronizationManager` 使用 `ThreadLocal` 绑定数据库连接和事务状态，确保同一个事务使用同一个连接。
1. **事务执行流程**：

```
请求 → TransactionInterceptor 拦截
    → PlatformTransactionManager.getTransaction()（开启事务）
    → TransactionSynchronizationManager.bindResource()（绑定连接到 ThreadLocal）
    → 执行目标方法
    → PlatformTransactionManager.commit()（提交事务）
    → TransactionSynchronizationManager.unbindResource()（解除绑定）
```
1. **ThreadLocal 的作用**：
  - **绑定连接**：将数据库连接绑定到当前线程，确保同一个事务的所有操作使用同一个连接。
  - **事务状态**：保存事务状态（是否活跃、是否只读、隔离级别等）。
  - **线程隔离**：每个线程有独立的事务上下文，互不干扰。
1. **事务传播机制**：
  - **REQUIRED**（默认）：如果当前存在事务，加入事务；否则创建新事务。
  - **REQUIRES_NEW**：创建新事务，如果当前存在事务，挂起当前事务。
  - **SUPPORTS**：如果当前存在事务，加入事务；否则非事务执行。
  - **NOT_SUPPORTED**：非事务执行，如果当前存在事务，挂起当前事务。
  - **MANDATORY**：必须在一个已有事务中执行，否则抛出异常。
  - **NEVER**：不能在事务中执行，否则抛出异常。
  - **NESTED**：如果当前存在事务，嵌套事务执行；否则创建新事务。
1. **事务失效场景**：
  - **自调用**：同类中非事务方法调用事务方法，绕过了代理。
  - **异常处理**：异常被捕获未抛出，事务不会回滚。
  - **private 方法**：`@Transactional` 标注在 `private` 方法上无效。
  - **final 方法**：CGLIB 代理无法继承 `final` 方法，事务失效。
  - **多线程**：新线程无法获取主线程的事务上下文。

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
只说了&quot;AOP + TransactionManager&quot;
</td>
<td>
完整流程：AOP 代理、拦截器、ThreadLocal 绑定
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ThreadLocal 的作用
</td>
<td>
解释 ThreadLocal 绑定连接和事务状态
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到事务传播和失效场景
</td>
<td>
详细说明 7 种传播机制和 5 种失效场景
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道事务的基本原理
</td>
<td>
理解事务的底层机制和边界条件
</td>
</tr>
</table>

---

#### 3、场景题：Agent 执行完工具调用后需要在事务提交后才发消息（避免消息先到但数据未提交），如何用 TransactionSynchronization 实现？

**难度级别**：⭐⭐⭐（事务同步、消息发送、事务提交后执行）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- TransactionSynchronization 实现
- 封装 TransactionSynchronization 工具类
- 使用工具类
- 事务回滚处理
- 实践优化
- @TransactionalEventListener（Spring 4.2+）

**2️⃣ Impressive Answer**
1. **TransactionSynchronization 实现**：

```java
@Service
public class AgentService {

    @Autowired
    private MessageProducer messageProducer;

    @Transactional
    public void executeToolAndSendMessage(ToolRequest request) {
        // 1. 执行工具调用（事务操作）
        ToolResult result = toolService.execute(request);

        // 2. 注册事务同步器
        TransactionSynchronizationManager.registerSynchronization(
            new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    // 事务提交后才发消息
                    messageProducer.send(result);
                }

                @Override
                public void afterCompletion(int status) {
                    // 事务完成后清理资源
                    if (status == STATUS_ROLLED_BACK) {
                        log.warn("Transaction rolled back, message not sent");
                    }
                }
            });

        // 3. 返回结果
        return result;
    }
}
```
1. **封装 TransactionSynchronization 工具类**：

```java
@Component
public class TransactionHelper {

    public void afterCommit(Runnable callback) {
        if (TransactionSynchronizationManager.isActualTransactionActive()) {
            TransactionSynchronizationManager.registerSynchronization(
                new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        callback.run();
                    }
                });
        } else {
            // 如果没有事务，直接执行
            callback.run();
        }
    }

    public void afterCompletion(Runnable callback) {
        if (TransactionSynchronizationManager.isActualTransactionActive()) {
            TransactionSynchronizationManager.registerSynchronization(
                new TransactionSynchronization() {
                    @Override
                        public void afterCompletion(int status) {
                            callback.run();
                        }
                    });
        } else {
            callback.run();
        }
    }
}
```
1. **使用工具类**：

```java
@Service
public class AgentService {

    @Autowired
    private TransactionHelper transactionHelper;

    @Autowired
    private MessageProducer messageProducer;

    @Transactional
    public void executeToolAndSendMessage(ToolRequest request) {
        // 执行工具调用
        ToolResult result = toolService.execute(request);

        // 注册事务提交后回调
        transactionHelper.afterCommit(() -> {
            messageProducer.send(result);
        });

        return result;
    }
}
```
1. **事务回滚处理**：

```java
@Transactional
public void executeToolAndSendMessage(ToolRequest request) {
    ToolResult result = toolService.execute(request);

    transactionHelper.afterCompletion(status -> {
        if (status == TransactionSynchronization.STATUS_COMMITTED) {
            // 事务提交成功，发送消息
            messageProducer.send(result);
        } else if (status == TransactionSynchronization.STATUS_ROLLED_BACK) {
            // 事务回滚，记录日志或发送补偿消息
            log.warn("Transaction rolled back for tool: {}", request.getName());
            messageProducer.sendCompensation(result);
        }
    });

    return result;
}
```
1. **实践优化**：
  - **异步发送**：事务提交后异步发送消息，避免阻塞事务提交。
  - **消息幂等**：确保消息幂等，避免重复发送。
  - **补偿机制**：如果消息发送失败，需要补偿机制（重试或人工介入）。
1. **@TransactionalEventListener（Spring 4.2+）**：

```java
@Component
public class TransactionEventPublisher {

    @Autowired
    private ApplicationEventPublisher eventPublisher;

    @Transactional
    public void executeToolAndSendMessage(ToolRequest request) {
        ToolResult result = toolService.execute(request);

        // 发布事务事件
        eventPublisher.publishEvent(new ToolCompletedEvent(result));

        return result;
    }
}

@Component
public class TransactionEventListener {

    @Autowired
    private MessageProducer messageProducer;

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleToolCompleted(ToolCompletedEvent event) {
        // 事务提交后才执行
        messageProducer.send(event.getResult());
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
只说了&quot;注册 TransactionSynchronization&quot;
</td>
<td>
完整方案：工具类封装、回滚处理、异步发送
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 @TransactionalEventListener
</td>
<td>
介绍 Spring 4.2+ 的事件驱动事务同步
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有考虑异步发送和幂等
</td>
<td>
提到异步发送、消息幂等、补偿机制
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
能实现基础事务同步
</td>
<td>
能设计生产级的事务同步方案
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
事务的隔离级别有哪些？
</td>
<td>
事务管理的重要概念
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
<tr>
<td>
如何实现分布式事务（Seata）？
</td>
<td>
事务管理的进阶话题
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
<tr>
<td>
如何优化事务性能（减少事务范围）？
</td>
<td>
事务性能优化的最佳实践
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
</table>

---

### 2.4 Spring 容器启动流程

#### 1、基础题：ApplicationContext 和 BeanFactory 的区别是什么？

**难度级别**：⭐（容器接口、功能增强、国际化支持）

**Answer**
1. **BeanFactory**：是 Spring 容器的**基础接口**，提供了最核心的 Bean 容器能力（getBean、containsBean 等），采用**延迟加载**策略（Lazy Init），只有在第一次 getBean 时才创建 Bean 实例，启动速度快，适合资源受限场景。
1. **ApplicationContext**：是 BeanFactory 的**子接口**，在基础功能上做了大量增强：
  - **国际化支持**：MessageSource 接口，支持 i18n
  - **事件发布**：ApplicationEventPublisher，支持事件监听机制
  - **资源加载**：ResourceLoader，支持从 classpath、URL 等加载资源
  - **环境抽象**：Environment，支持 profile、配置属性
  - **预实例化**：默认在容器启动时创建所有 singleton Bean（可通过 lazy-init 覆盖）
1. **选择建议**：开发中优先使用 ApplicationContext（如 ClassPathXmlApplicationContext、AnnotationConfigApplicationContext），BeanFactory 主要在框架内部使用。

---

#### 2、进阶题：Spring 容器的 refresh() 方法做了哪些事？核心步骤是什么？

**难度级别**：⭐⭐⭐（容器启动12步骤、BeanDefinition加载、BeanFactoryPostProcessor、BeanPostProcessor）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 12 个核心步骤
- 关键扩展点
- 步骤⑤：BeanFactoryPostProcessor 可以修改 BeanDefinition（如 @ConfigurationClassPostProcessor 处理 @...
- 步骤⑥：BeanPostProcessor 在 Bean 创建前后拦截，AOP 代理在 postProcessAfterInitialization 创建
- 步骤⑪：真正的 Bean 实例化，包括依赖注入、初始化回调

**2️⃣ Impressive Answer**
1. **refresh() 核心定位**：`AbstractApplicationContext.refresh()` 是容器启动的**模板方法**，定义了容器启动的完整流程，12 个步骤环环相扣，确保容器正确初始化。
1. **12 个核心步骤**：

```
① prepareRefresh()：准备刷新环境，设置启动时间、初始化属性源
② obtainFreshBeanFactory()：创建 BeanFactory，加载 BeanDefinition（解析 @Component、@Bean）
③ prepareBeanFactory()：配置 BeanFactory（注册 Aware 接口、设置类加载器）
④ postProcessBeanFactory()：子类扩展点，允许修改 BeanFactory
⑤ invokeBeanFactoryPostProcessors()：执行 BeanFactoryPostProcessor（如 @PropertySource 解析）
⑥ registerBeanPostProcessors()：注册 BeanPostProcessor（AOP、@Autowired 都依赖它）
⑦ initMessageSource()：初始化国际化资源
⑧ initApplicationEventMulticaster()：初始化事件广播器
⑨ onRefresh()：子类扩展点，如 Web 容器启动
⑩ registerListeners()：注册事件监听器
⑪ finishBeanFactoryInitialization()：实例化所有非延迟加载的 singleton Bean（核心步骤）
⑫ finishRefresh()：发布 ContextRefreshedEvent，容器启动完成
```
1. **关键扩展点**：
  - **步骤⑤**：`BeanFactoryPostProcessor` 可以修改 BeanDefinition（如 @ConfigurationClassPostProcessor 处理 @Configuration）
  - **步骤⑥**：`BeanPostProcessor` 在 Bean 创建前后拦截，AOP 代理在 `postProcessAfterInitialization` 创建
  - **步骤⑪**：真正的 Bean 实例化，包括依赖注入、初始化回调
1. **实践注意**：如果容器启动慢，可以检查是否有过多的 Bean 在步骤⑪被预实例化，或者 BeanPostProcessor 执行时间过长。

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
只说了&quot;加载配置、创建 Bean&quot;
</td>
<td>
完整 12 步骤，每步都有明确职责
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 BeanFactoryPostProcessor 和 BeanPostProcessor 的区别
</td>
<td>
清楚两者在不同步骤执行，作用不同
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
知道如何通过扩展点定制容器启动流程
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过概念但说不清细节
</td>
<td>
理解容器启动的设计思路和关键机制
</td>
</tr>
</table>

---

#### 3、场景题：如何在 Spring 容器完全启动后执行初始化逻辑？ApplicationRunner、CommandLineRunner、@EventListener(ContextRefreshedEvent) 有什么区别？

**难度级别**：⭐⭐⭐（容器启动后回调、执行顺序、参数差异、适用场景）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- ApplicationRunner
- CommandLineRunner
- @EventListener(ContextRefreshedEvent)
- 接口定义：run(ApplicationArguments args)
- 参数：ApplicationArguments 封装了命令行参数（支持 --key=value 格式，可获取非选项参数）
- 推荐场景：需要解析命令行参数的初始化逻辑

**2️⃣ Impressive Answer**
1. **三种方式的执行时机**：都在容器启动完成后执行，但执行顺序和适用场景不同。
1. **ApplicationRunner**：
  - **接口定义**：`run(ApplicationArguments args)`
  - **参数**：`ApplicationArguments` 封装了命令行参数（支持 `--key=value` 格式，可获取非选项参数）
  - **推荐场景**：需要解析命令行参数的初始化逻辑

```java
@Component
public class DataInitializer implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) throws Exception {
        if (args.containsOption("init-data")) {
            // 执行数据初始化
        }
    }
}
```
1. **CommandLineRunner**：
  - **接口定义**：`run(String... args)`
  - **参数**：原始命令行参数数组（`String[]`）
  - **推荐场景**：简单的命令行参数处理

```java
@Component
public class CacheInitializer implements CommandLineRunner {
    @Override
    public void run(String... args) throws Exception {
        // 预热缓存
    }
}
```
1. **@EventListener(ContextRefreshedEvent)**：
  - **事件机制**：监听容器刷新完成事件
  - **执行时机**：在 `finishRefresh()` 时发布，早于 ApplicationRunner/CommandLineRunner
  - **注意**：如果是父子容器（如 Spring Boot + Spring MVC），事件会被触发多次，需判断 `event.getApplicationContext().getParent() == null`

```java
@Component
public class SystemInitializer {
    @EventListener
    public void onContextRefreshed(ContextRefreshedEvent event) {
        if (event.getApplicationContext().getParent() == null) {
            // 只在根容器触发一次
        }
    }
}
```
1. **执行顺序**：`@EventListener(ContextRefreshedEvent)` → `ApplicationRunner/CommandLineRunner`（可通过 `@Order` 指定顺序）
1. **实践建议**：优先使用 `ApplicationRunner`，参数更友好；如果需要监听父子容器事件，用 `@EventListener`。

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
只知道&quot;都能在启动后执行&quot;
</td>
<td>
清楚执行顺序和参数差异
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ContextRefreshedEvent 的父子容器问题
</td>
<td>
解释了事件的多次触发问题和解决方案
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有区分适用场景
</td>
<td>
给出不同场景的选择建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道有这些接口但不深入
</td>
<td>
理解三种机制的设计意图和使用边界
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
BeanFactoryPostProcessor 和 BeanPostProcessor 的区别？
</td>
<td>
容器启动的两个关键扩展点
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@DependsOn 的作用是什么？
</td>
<td>
控制 Bean 的初始化顺序
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
Spring Boot 启动流程（SpringApplication.run()）？
</td>
<td>
Spring Boot 对 refresh() 的封装
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 2.5 Spring 循环依赖

#### 1、基础题：什么是循环依赖？Spring 默认是如何解决的？

**难度级别**：⭐（循环依赖定义、setter注入可解决、构造器注入无法解决）

**Answer**
1. **循环依赖定义**：A 依赖 B，B 又依赖 A（或者 A→B→C→A），形成闭环。
1. **Spring 默认解决策略**：
  - **可以解决**：**setter 注入**（单例 Bean），通过三级缓存机制
  - **无法解决**：**构造器注入**（实例化时就需要依赖对象，无法提前暴露）
  - **无法解决**：**prototype 作用域**（每次都创建新实例，缓存机制失效）
1. **解决原理**：在创建 Bean 时，先将半成品的 Bean（属性未注入）暴露出去，让其他 Bean 可以引用，等所有 Bean 创建完成后再注入属性。

---

#### 2、进阶题：Spring 三级缓存的结构是什么？为什么需要三级而不是两级？

**难度级别**：⭐⭐⭐（三级缓存Map、earlySingletonObjects、singletonFactories、AOP代理时机）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 三级缓存结构（DefaultSingletonBeanRegistry）
- 三级缓存的工作流程（以 A 依赖 B，B 依赖 A 为例）
- 为什么需要三级而不是两级？
- 如果只有两级：在实例化 A 时，如果 A 需要 AOP 代理，必须立即创建代理对象并放入二级缓存。但此时 A 还没初始化，无法确定是否真的需要代理（可能被其他逻辑覆盖）。
- 三级缓存的优势：ObjectFactory 是延迟执行的，只有在其他 Bean 真正引用 A 时，才调用 getObject() 创建代理。这样可以
- 避免不必要的代理创建（如果 A 不被循环引用，就不需要代理）

**2️⃣ Impressive Answer**
1. **三级缓存结构**（`DefaultSingletonBeanRegistry`）：

```java
// 一级缓存：完整的 Bean（已初始化完成）
private final Map<String, Object> singletonObjects = new ConcurrentHashMap<>(256);

// 二级缓存：早期暴露的 Bean（实例化但未初始化，可能被代理）
private final Map<String, Object> earlySingletonObjects = new ConcurrentHashMap<>(16);

// 三级缓存：Bean 工厂（ObjectFactory，用于提前暴露 Bean 或创建 AOP 代理）
private final Map<String, ObjectFactory<?>> singletonFactories = new HashMap<>(16);
```
1. **三级缓存的工作流程**（以 A 依赖 B，B 依赖 A 为例）：

```
① 创建 A：实例化 A，将 A 的 ObjectFactory 放入三级缓存
② 注入 B：发现依赖 B，创建 B
③ 创建 B：实例化 B，注入 A
④ 获取 A：从三级缓存获取 A 的 ObjectFactory，调用 getObject()
⑤ AOP 判断：如果 A 需要 AOP 代理，ObjectFactory 创建代理对象
⑥ 升级缓存：将代理对象从三级移到二级缓存
⑦ B 完成：A 的代理对象注入到 B，B 初始化完成，放入一级缓存
⑧ A 完成：A 注入 B（从一级缓存获取），A 初始化完成，从二级移到一级
```
1. **为什么需要三级而不是两级？**
  - **如果只有两级**：在实例化 A 时，如果 A 需要 AOP 代理，必须立即创建代理对象并放入二级缓存。但此时 A 还没初始化，无法确定是否真的需要代理（可能被其他逻辑覆盖）。
  - **三级缓存的优势**：`ObjectFactory` 是**延迟执行**的，只有在其他 Bean 真正引用 A 时，才调用 `getObject()` 创建代理。这样可以：
    - 避免不必要的代理创建（如果 A 不被循环引用，就不需要代理）
    - 确保 AOP 代理在正确的时机创建（`getEarlyBeanReference` 回调）
1. **AOP 代理的时机**：如果 A 被 `@Async`、`@Transactional` 等注解标注，且发生了循环依赖，A 的代理对象会在 `getEarlyBeanReference` 中提前创建，而不是在 `BeanPostProcessor.postProcessAfterInitialization`。
1. **实践注意**：如果项目中没有 AOP 或循环依赖，三级缓存其实可以简化为两级（Spring 源码注释也提到过）。

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
只知道&quot;三个 Map&quot;
</td>
<td>
清楚每个缓存的用途和 ObjectFactory 的延迟特性
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道为什么需要三级
</td>
<td>
解释了 AOP 代理的延迟创建机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到 AOP 代理的时机
</td>
<td>
理解循环依赖对 AOP 代理时机的影响
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
背过概念但不懂原理
</td>
<td>
理解三级缓存的设计意图和 AOP 的关系
</td>
</tr>
</table>

---

#### 3、场景题：构造器注入为什么无法解决循环依赖？项目中遇到循环依赖应该怎么处理？

**难度级别**：⭐⭐⭐（构造器注入时机、@Lazy、重新设计、设计模式）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 构造器注入无法解决的原因
- 解决方案
- 实践建议
- 实例化时机：构造器注入在实例化阶段就需要依赖对象，而三级缓存是在实例化后才将半成品暴露出去。
- 死锁问题：A 实例化需要 B，B 实例化需要 A，两者都无法实例化，形成死锁。
- 原理：@Lazy 会先注入一个代理对象，真正调用时才从容器获取真实 Bean，打破循环依赖。

**2️⃣ Impressive Answer**
1. **构造器注入无法解决的原因**：
  - **实例化时机**：构造器注入在**实例化阶段**就需要依赖对象，而三级缓存是在**实例化后**才将半成品暴露出去。
  - **死锁问题**：A 实例化需要 B，B 实例化需要 A，两者都无法实例化，形成死锁。
1. **解决方案**：
    **方案 1：使用 @Lazy 注解（推荐）**

```java
@Service
public class ServiceA {
    private final ServiceB serviceB;

    public ServiceA(@Lazy ServiceB serviceB) {  // 延迟注入
        this.serviceB = serviceB;
    }
}
```

```
-   **原理**：`@Lazy` 会先注入一个代理对象，真正调用时才从容器获取真实 Bean，打破循环依赖。
```

```
**方案 2：改为 setter 注入或 @Autowired 字段注入**
```

```java
@Service
public class ServiceA {
    @Autowired
    private ServiceB serviceB;  // 字段注入，可以解决循环依赖
}
```

```
**方案 3：重新设计架构（最佳实践）**
```
- **引入中间层**：A 和 B 都依赖 C，通过 C 通信-   **事件驱动**：A 发布事件，B 监听事件-   **设计模式**：使用观察者模式、中介者模式解耦

```java
// 事件驱动解耦
@Service
public class ServiceA {
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    public void doSomething() {
        eventPublisher.publishEvent(new MyEvent());
    }
}

@Service
public class ServiceB {
    @EventListener
    public void handleEvent(MyEvent event) {
        // 处理事件
    }
}
```
1. **实践建议**：
  - 优先使用构造器注入（保证不可变性），遇到循环依赖时用 `@Lazy`
  - 如果循环依赖频繁出现，说明架构设计有问题，应该重构
  - `@DependsOn` 可以强制指定 Bean 初始化顺序，但治标不治本

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
只知道&quot;构造器不行&quot;
</td>
<td>
解释了实例化时机和死锁原理
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
只提到 @Lazy 和 setter
</td>
<td>
给出事件驱动、中间层等架构级方案
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有强调架构重构
</td>
<td>
指出频繁循环依赖是设计问题
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用注解但不懂原理
</td>
<td>
理解循环依赖的本质和解决思路
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
@DependsOn 的作用是什么？
</td>
<td>
控制 Bean 初始化顺序，可配合解决循环依赖
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
@Async 导致的循环依赖问题？
</td>
<td>
@Async 会提前创建代理，可能引发循环依赖
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：@Async 会提前创建代理，可能引发循环依赖，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring 代理的创建时机？
</td>
<td>
循环依赖时代理提前创建，正常情况在 BeanPostProcessor
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 2.6 Spring 事件机制

#### 1、基础题：Spring 的事件发布/监听机制是什么？如何使用？

**难度级别**：⭐（ApplicationEvent、ApplicationListener、观察者模式、解耦）

**Answer**
1. **核心原理**：Spring 事件机制是**观察者模式**的实现，通过 `ApplicationEventPublisher` 发布事件，`ApplicationListener` 监听事件，实现组件间的解耦。
1. **使用方式**：
    **方式 1：继承 ApplicationListener（传统方式）**

```java
// 定义事件
public class UserRegisteredEvent extends ApplicationEvent {
    private final String username;

    public UserRegisteredEvent(Object source, String username) {
        super(source);
        this.username = username;
    }
}

// 监听事件
@Component
public class EmailNotificationListener implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent event) {
        System.out.println("Send email to " + event.getUsername());
    }
}

// 发布事件
@Service
public class UserService {
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    public void register(String username) {
        // 注册逻辑
        eventPublisher.publishEvent(new UserRegisteredEvent(this, username));
    }
}
```

```
**方式 2：@EventListener 注解（推荐）**
```

```java
@Component
public class NotificationListener {
    @EventListener
    public void handleUserRegistered(UserRegisteredEvent event) {
        System.out.println("Send email to " + event.getUsername());
    }
}
```
1. **核心优势**：解耦业务逻辑，发布者不需要知道有哪些监听者，监听者之间互不影响。

---

#### 2、进阶题：@EventListener 的实现原理是什么？同步事件和异步事件（@Async）有什么区别？

**难度级别**：⭐⭐⭐（EventListenerMethodProcessor、同步vs异步、异常处理、事务传播）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- @EventListener 实现原理
- 同步事件 vs 异步事件
- 事务传播特性
- 异常处理
- 实践注意
- 注册时机：EventListenerMethodProcessor（BeanFactoryPostProcessor）在容器启动时扫描所有带 @EventListener 的方法。

**2️⃣ Impressive Answer**
1. **@EventListener 实现原理**：
  - **注册时机**：`EventListenerMethodProcessor`（`BeanFactoryPostProcessor`）在容器启动时扫描所有带 `@EventListener` 的方法。
  - **包装为 ApplicationListener**：将方法包装成 `ApplicationListenerMethodAdapter`，注册到 `ApplicationEventMulticaster`。
  - **事件匹配**：通过反射检查方法参数类型，匹配到对应事件时调用方法。

```java
@Component
public class MyListener {
    @EventListener(condition = "#event.success")  // 支持 SpEL 条件
    public void handleEvent(MyEvent event) {
        // 处理逻辑
    }
}
```
1. **同步事件 vs 异步事件**：

<table>
<tr>
<td>
特性
</td>
<td>
同步事件（默认）
</td>
<td>
异步事件（@Async）
</td>
</tr>
<tr>
<td>
执行线程
</td>
<td>
发布者线程
</td>
<td>
独立线程池（默认 SimpleAsyncTaskExecutor）
</td>
</tr>
<tr>
<td>
阻塞特性
</td>
<td>
阻塞发布者
</td>
<td>
不阻塞发布者
</td>
</tr>
<tr>
<td>
事务传播
</td>
<td>
共享发布者事务
</td>
<td>
独立事务（无事务）
</td>
</tr>
<tr>
<td>
异常处理
</td>
<td>
监听器异常会向上传播
</td>
<td>
监听器异常不影响发布者
</td>
</tr>
<tr>
<td>
适用场景
</td>
<td>
需要事务一致性、数据同步
</td>
<td>
非核心逻辑、耗时操作
</td>
</tr>
</table>

```java
@Component
public class AsyncListener {
    @Async  // 异步执行
    @EventListener
    public void handleAsyncEvent(MyEvent event) {
        // 在独立线程执行，不影响主流程
    }
}
```
1. **事务传播特性**：
  - **同步事件**：监听器在发布者的事务中执行，如果监听器抛异常，发布者的事务会回滚。
  - **异步事件**：监听器在独立线程执行，**不共享发布者的事务**，即使监听器抛异常也不影响发布者。
1. **异常处理**：
  - 同步事件：监听器异常会中断后续监听器，异常传播到发布者。
  - 异步事件：监听器异常被捕获，不影响其他监听器和发布者（可以通过 `@Async("exceptionHandler")` 指定异常处理器）。
1. **实践注意**：
  - 异步事件如果需要事务，需要在监听器方法上加 `@Transactional`（独立事务）。
  - 同步事件如果不想让监听器异常影响发布者，可以用 `try-catch` 包裹监听器逻辑。

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
只知道&quot;同步阻塞、异步不阻塞&quot;
</td>
<td>
清楚事务传播、异常处理的差异
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 EventListenerMethodProcessor
</td>
<td>
解释了注解扫描和监听器注册机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到事务和异常处理
</td>
<td>
给出不同场景的最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用注解但不理解机制
</td>
<td>
理解事件机制的设计意图和边界
</td>
</tr>
</table>

---

#### 3、场景题：Agent 工具调用完成后需要异步通知多个下游系统，如何用 Spring 事件解耦？

**难度级别**：⭐⭐⭐（异步事件、多监听器、事务传播、异常隔离）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 场景分析
- 实现方案
- 关键设计点
- 实践注意
- Agent 调用工具后，需要通知多个下游系统（日志系统、监控系统、审计系统等）。
- 下游系统的处理不应该影响 Agent 的响应速度，也不应该因为某个下游系统失败而影响主流程。

**2️⃣ Impressive Answer**
1. **场景分析**：
  - Agent 调用工具后，需要通知多个下游系统（日志系统、监控系统、审计系统等）。
  - 下游系统的处理不应该影响 Agent 的响应速度，也不应该因为某个下游系统失败而影响主流程。
1. **实现方案**：
    **步骤 1：定义事件**

```java
public class ToolCallCompletedEvent extends ApplicationEvent {
    private final String toolName;
    private final Object result;
    private final long duration;

    public ToolCallCompletedEvent(Object source, String toolName, Object result, long duration) {
        super(source);
        this.toolName = toolName;
        this.result = result;
        this.duration = duration;
    }

    // getters...
}
```

```
**步骤 2：发布事件（在 Agent 调用完成后）**
```

```java
@Service
public class AgentService {
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    @Async
    public CompletableFuture<Object> callTool(String toolName, Map<String, Object> params) {
        long start = System.currentTimeMillis();
        Object result = toolExecutor.execute(toolName, params);
        long duration = System.currentTimeMillis() - start;

        // 发布事件（异步发布，不阻塞当前线程）
        eventPublisher.publishEvent(new ToolCallCompletedEvent(this, toolName, result, duration));

        return CompletableFuture.completedFuture(result);
    }
}
```

```
**步骤 3：多个监听器异步处理**
```

```java
@Component
public class MonitoringListener {
    @Async("agentEventExecutor")  // 指定线程池
    @EventListener
    public void recordMetrics(ToolCallCompletedEvent event) {
        metricsService.recordToolCall(event.getToolName(), event.getDuration());
    }
}

@Component
public class AuditListener {
    @Async("agentEventExecutor")
    @EventListener
    public void auditToolCall(ToolCallCompletedEvent event) {
        auditService.logToolCall(event.getToolName(), event.getResult());
    }
}

@Component
public class LogListener {
    @Async("agentEventExecutor")
    @EventListener
    public void logToolCall(ToolCallCompletedEvent event) {
        log.info("Tool {} called, duration: {}ms", event.getToolName(), event.getDuration());
    }
}
```

```
**步骤 4：配置线程池**
```

```java
@Configuration
public class AsyncConfig {
    @Bean("agentEventExecutor")
    public Executor agentEventExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("agent-event-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```
1. **关键设计点**：
  - **异步发布**：`callTool` 方法本身就是 `@Async`，事件发布也在异步线程中，不会阻塞用户请求。
  - **异常隔离**：某个监听器失败不会影响其他监听器，也不会影响 Agent 主流程。
  - **独立线程池**：使用专用线程池，避免和业务线程池竞争资源。
  - **事务独立**：监听器在独立事务中执行，即使需要数据库操作也不会影响 Agent 的事务。
1. **实践注意**：
  - 如果监听器需要重试机制，可以用 Spring Retry（`@Retryable`）。
  - 如果监听器执行顺序有要求，可以用 `@Order` 指定顺序（但异步执行时顺序不保证）。

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
只知道&quot;发布事件、异步监听&quot;
</td>
<td>
完整方案，包含事件定义、发布、监听、线程池配置
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
没有提到异常隔离和事务独立
</td>
<td>
解释了异步事件的异常处理和事务特性
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有考虑线程池和资源隔离
</td>
<td>
给出生产级的线程池配置建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用事件机制但不深入
</td>
<td>
理解异步事件的设计边界和最佳实践
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
TransactionalEventListener 的作用？
</td>
<td>
监听事务提交后的事件
</td>
<td>
答：MySQL 题要从数据结构、事务隔离、锁/MVCC、执行计划和慢 SQL 优化展开；最后落到 explain、索引设计和业务一致性。
</td>
</tr>
<tr>
<td>
@Async 的线程池如何配置？
</td>
<td>
异步事件的线程池管理
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：异步事件的线程池管理，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring 事件机制和消息队列的区别？
</td>
<td>
本地事件 vs 分布式事件
</td>
<td>
答：分布式题先明确一致性、可用性和性能目标，再讲协议或方案；落地时补超时、重试、幂等、监控和故障恢复。
</td>
</tr>
</table>

---

### 2.7 Spring Bean 作用域

#### 1、基础题：Spring Bean 有哪些作用域？singleton 和 prototype 的区别？

**难度级别**：⭐（singleton、prototype、request、session、application）

**Answer**
1. **Spring Bean 的作用域**：
  - **singleton**（默认）：单例，整个容器只有一个实例
  - **prototype**：原型，每次 getBean 都创建新实例
  - **request**：每个 HTTP 请求一个实例（仅 Web 环境）
  - **session**：每个 HTTP Session 一个实例（仅 Web 环境）
  - **application**：ServletContext 生命周期一个实例（仅 Web 环境）
1. **singleton vs prototype 区别**：

<table>
<tr>
<td>
特性
</td>
<td>
singleton
</td>
<td>
prototype
</td>
</tr>
<tr>
<td>
实例数量
</td>
<td>
容器中只有一个
</td>
<td>
每次 getBean 都创建新实例
</td>
</tr>
<tr>
<td>
创建时机
</td>
<td>
容器启动时（默认）
</td>
<td>
每次 getBean 时
</td>
</tr>
<tr>
<td>
生命周期管理
</td>
<td>
容器管理（初始化、销毁）
</td>
<td>
容器只创建，不管理销毁
</td>
</tr>
<tr>
<td>
线程安全
</td>
<td>
需要保证线程安全
</td>
<td>
每个线程独立实例，天然线程安全
</td>
</tr>
<tr>
<td>
适用场景
</td>
<td>
无状态对象（Service、DAO）
</td>
<td>
有状态对象（Command、Form）
</td>
</tr>
</table>

---

#### 2、进阶题：singleton Bean 注入 prototype Bean 时，为什么每次拿到的不是新实例？如何解决？

**难度级别**：⭐⭐⭐（依赖注入时机、@Lookup、ObjectFactory、Provider）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 问题根源
- 解决方案
- 方案对比
- 依赖注入时机：singleton Bean 在容器启动时初始化，此时注入的 prototype Bean 只会被创建一次。
- 缓存机制：注入后，prototype Bean 的引用被 singleton Bean 持有，后续调用时复用同一个实例。
- 原理：Spring 通过 CGLIB 动态代理子类，重写 getPrototypeBean() 方法，每次调用时从容器获取新实例。

**2️⃣ Impressive Answer**
1. **问题根源**：
  - **依赖注入时机**：singleton Bean 在容器启动时初始化，此时注入的 prototype Bean 只会被创建一次。
  - **缓存机制**：注入后，prototype Bean 的引用被 singleton Bean 持有，后续调用时复用同一个实例。

```java
@Service
public class SingletonService {
    @Autowired
    private PrototypeBean prototypeBean;  // 只注入一次

    public void doSomething() {
        prototypeBean.execute();  // 每次都是同一个实例
    }
}
```
1. **解决方案**：
    **方案 1：@Lookup 注解（推荐）**

```java
@Service
public abstract class SingletonService {
    public void doSomething() {
        PrototypeBean prototypeBean = getPrototypeBean();  // 每次调用都创建新实例
        prototypeBean.execute();
    }

    @Lookup
    protected abstract PrototypeBean getPrototypeBean();
}
```

```
-   **原理**：Spring 通过 CGLIB 动态代理子类，重写 `getPrototypeBean()` 方法，每次调用时从容器获取新实例。
```

```
**方案 2：ObjectFactory**
```

```java
@Service
public class SingletonService {
    @Autowired
    private ObjectFactory<PrototypeBean> prototypeBeanFactory;

    public void doSomething() {
        PrototypeBean prototypeBean = prototypeBeanFactory.getObject();  // 每次获取新实例
        prototypeBean.execute();
    }
}
```

```
**方案 3：Provider（JSR-330）**
```

```java
@Service
public class SingletonService {
    @Autowired
    private Provider<PrototypeBean> prototypeBeanProvider;

    public void doSomething() {
        PrototypeBean prototypeBean = prototypeBeanProvider.get();  // 每次获取新实例
        prototypeBean.execute();
    }
}
```

```
**方案 4：ApplicationContext 直接获取（不推荐）**
```

```java
@Service
public class SingletonService {
    @Autowired
    private ApplicationContext applicationContext;

    public void doSomething() {
        PrototypeBean prototypeBean = applicationContext.getBean(PrototypeBean.class);
        prototypeBean.execute();
    }
}
```
1. **方案对比**：

<table>
<tr>
<td>
方案
</td>
<td>
优点
</td>
<td>
缺点
</td>
</tr>
<tr>
<td>
@Lookup
</td>
<td>
代码简洁，Spring 原生支持
</td>
<td>
需要抽象类或方法
</td>
</tr>
<tr>
<td>
ObjectFactory
</td>
<td>
灵活，支持延迟加载
</td>
<td>
需要额外接口
</td>
</tr>
<tr>
<td>
Provider
</td>
<td>
JSR-330 标准
</td>
<td>
依赖额外依赖
</td>
</tr>
<tr>
<td>
ApplicationContext
</td>
<td>
简单直接
</td>
<td>
耦合容器，不推荐
</td>
</tr>
</table>
1. **实践建议**：优先使用 `@Lookup`，代码最简洁；如果需要更灵活的控制（如缓存、条件获取），用 `ObjectFactory`。

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
只知道&quot;注入时机问题&quot;
</td>
<td>
解释了依赖注入时机和缓存机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
只提到 @Lookup
</td>
<td>
给出 4 种方案，对比优缺点
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有区分适用场景
</td>
<td>
给出不同场景的选择建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用注解但不理解原理
</td>
<td>
理解依赖注入机制和作用域的边界
</td>
</tr>
</table>

---

#### 3、场景题：Agent 的会话上下文（每个用户会话独立）如何用 Spring Scope 管理？

**难度级别**：⭐⭐⭐（自定义 Scope、ThreadLocal、Session Scope、请求上下文）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 场景分析
- 解决方案
- 方案对比
- 实践建议
- Agent 每次对话需要维护会话上下文（历史消息、用户偏好、工具调用状态等）。
- 不同用户的会话上下文必须隔离，同一用户的多次请求共享上下文。

**2️⃣ Impressive Answer**
1. **场景分析**：
  - Agent 每次对话需要维护会话上下文（历史消息、用户偏好、工具调用状态等）。
  - 不同用户的会话上下文必须隔离，同一用户的多次请求共享上下文。
1. **解决方案**：
    **方案 1：Session Scope（Web 环境）**

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_SESSION, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class AgentSessionContext {
    private List<Message> history = new ArrayList<>();
    private Map<String, Object> preferences = new HashMap<>();

    public void addMessage(Message message) {
        history.add(message);
    }

    // getters...
}

@Service
public class AgentService {
    @Autowired
    private AgentSessionContext sessionContext;  // 每个用户会话一个实例

    public void chat(String message) {
        sessionContext.addMessage(new Message(message));
        // 处理逻辑
    }
}
```

```
-   **注意**：需要在 singleton Bean 中注入 Session Scope Bean 时，使用 `proxyMode = ScopedProxyMode.TARGET_CLASS` 创建代理对象。
```

```
**方案 2：自定义 Scope（非 Web 环境）**
```

```java
// 定义自定义 Scope
public class ConversationScope implements Scope {
    private final ThreadLocal<Map<String, Object>> conversationContext = ThreadLocal.withInitial(HashMap::new);

    @Override
    public Object get(String name, ObjectFactory<?> objectFactory) {
        return conversationContext.get().computeIfAbsent(name, k -> objectFactory.getObject());
    }

    @Override
    public Object remove(String name) {
        return conversationContext.get().remove(name);
    }

    @Override
    public void registerDestructionCallback(String name, Runnable callback) {
        // 销毁回调
    }

    @Override
    public Object resolveContextualObject(String key) {
        return null;
    }

    @Override
    public String getConversationId() {
        return String.valueOf(Thread.currentThread().getId());
    }
}

// 注册自定义 Scope
@Configuration
public class ScopeConfig {
    @Bean
    public static CustomScopeConfigurer customScopeConfigurer() {
        CustomScopeConfigurer configurer = new CustomScopeConfigurer();
        configurer.addScope("conversation", new ConversationScope());
        return configurer;
    }
}

// 使用自定义 Scope
@Component
@Scope("conversation")
public class AgentContext {
    private List<Message> history = new ArrayList<>();
    // ...
}
```

```
**方案 3：ThreadLocal + RequestContextHolder（简单场景）**
```

```java
@Component
public class AgentContextHolder {
    private static final ThreadLocal<AgentContext> CONTEXT = new ThreadLocal<>();

    public static void setContext(AgentContext context) {
        CONTEXT.set(context);
    }

    public static AgentContext getContext() {
        return CONTEXT.get();
    }

    public static void clear() {
        CONTEXT.remove();
    }
}

// 拦截器中设置上下文
@Component
public class AgentInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String conversationId = request.getHeader("X-Conversation-Id");
        AgentContext context = contextRepository.findByConversationId(conversationId);
        AgentContextHolder.setContext(context);
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        AgentContextHolder.clear();
    }
}
```
1. **方案对比**：

<table>
<tr>
<td>
方案
</td>
<td>
适用场景
</td>
<td>
优点
</td>
<td>
缺点
</td>
</tr>
<tr>
<td>
Session Scope
</td>
<td>
Web 环境，每个用户会话
</td>
<td>
Spring 原生支持，简单
</td>
<td>
依赖 Web 容器
</td>
</tr>
<tr>
<td>
自定义 Scope
</td>
<td>
非Web环境，灵活控制
</td>
<td>
可完全自定义生命周期
</td>
<td>
实现复杂
</td>
</tr>
<tr>
<td>
ThreadLocal
</td>
<td>
简单场景，请求级别
</td>
<td>
轻量级，无侵入
</td>
<td>
需要手动管理，内存泄漏风险
</td>
</tr>
</table>
1. **实践建议**：
  - Web 环境优先用 Session Scope
  - 如果需要跨请求共享上下文（如 WebSocket），用自定义 Scope 或 Redis 存储
  - ThreadLocal 适合简单的请求级别上下文，但要注意内存泄漏（及时清理）

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
只知道&quot;Session Scope&quot;
</td>
<td>
给出 3 种方案，覆盖不同场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
没有提到代理模式
</td>
<td>
解释了 ScopedProxyMode 的作用
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有区分 Web 和非 Web 环境
</td>
<td>
给出不同环境的选择建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会用 Session Scope 但不深入
</td>
<td>
理解 Scope 的扩展机制和自定义能力
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
@RefreshScope 的作用是什么？
</td>
<td>
Spring Cloud 的动态刷新 Scope
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
<tr>
<td>
ThreadLocal 的内存泄漏问题？
</td>
<td>
自定义 Scope 需要注意的问题
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：自定义 Scope 需要注意的问题，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring 代理的两种模式？
</td>
<td>
ScopedProxyMode 的 JDK 动态代理 vs CGLIB
</td>
<td>
答：Java/Spring 题要把概念、生命周期、底层机制和项目实践连起来答；重点说清容器管理、代理机制、事务边界和常见坑。
</td>
</tr>
</table>

---

### 2.8 Spring 条件装配与自动配置

#### 1、基础题：@ConditionalOnProperty、@ConditionalOnClass 等条件注解的作用是什么？

**难度级别**：⭐（条件装配、@Conditional系列、自动配置）

**Answer**
1. **条件装配核心**：`@Conditional` 注解可以根据特定条件决定是否注册 Bean，避免不必要的 Bean 创建，提升启动速度和灵活性。
1. **常用条件注解**：
  - `@ConditionalOnProperty`：根据配置属性判断
  - `@ConditionalOnClass`：根据 classpath 中是否存在某个类判断
  - `@ConditionalOnMissingBean`：根据容器中是否缺少某个 Bean 判断
  - `@ConditionalOnBean`：根据容器中是否存在某个 Bean 判断
  - `@ConditionalOnWebApplication`：根据是否是 Web 应用判断
1. **使用示例**：

```java
@Configuration
public class AgentConfiguration {

    @Bean
    @ConditionalOnProperty(name = "agent.enabled", havingValue = "true")
    public AgentService agentService() {
        return new AgentService();
    }

    @Bean
    @ConditionalOnClass(name = "com.alibaba.dubbo.config.ApplicationConfig")
    public DubboAgentService dubboAgentService() {
        return new DubboAgentService();
    }

    @Bean
    @ConditionalOnMissingBean(ToolExecutor.class)
    public DefaultToolExecutor defaultToolExecutor() {
        return new DefaultToolExecutor();
    }
}
```

---

#### 2、进阶题：Spring Boot 自动配置的原理是什么？从 @EnableAutoConfiguration 到 Bean 注册的完整链路？

**难度级别**：⭐⭐⭐（自动配置原理、spring.factories、@EnableAutoConfiguration、条件过滤）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 完整链路
- 关键步骤详解
- 自动配置报告
- 实践注意
- 配置类本身注册为 BeanDefinition- 配置类中的 @Bean 方法解析为 BeanDefinition- 条件过滤后，符合条件的 Bean 被实例化
- 启动参数 --debug 可以查看自动配置报告

**2️⃣ Impressive Answer**
1. **自动配置核心定位**：Spring Boot 通过"约定优于配置"的理念，根据 classpath 中的依赖自动装配 Bean，减少手动配置。
1. **完整链路**：

```
① @SpringBootApplication 启动
② @EnableAutoConfiguration 导入 AutoConfigurationImportSelector
③ AutoConfigurationImportSelector 从 spring.factories 加载配置类
④ 配置类经过条件过滤（@Conditional 系列）
⑤ 符合条件的配置类注册为 BeanDefinition
⑥ 配置类中的 @Bean 方法创建 Bean
```
1. **关键步骤详解**：
    **步骤 1：@EnableAutoConfiguration 导入选择器**

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@AutoConfigurationPackage
@Import(AutoConfigurationImportSelector.class)  // 导入自动配置选择器
public @interface EnableAutoConfiguration {
    String ENABLED_OVERRIDE_PROPERTY = "spring.boot.enableautoconfiguration";
    Class<?>[] exclude() default {};
    String[] excludeName() default {};
}
```

```
**步骤 2：AutoConfigurationImportSelector 加载配置类**
```

```java
public class AutoConfigurationImportSelector implements DeferredImportSelector {
    @Override
    public String[] selectImports(AnnotationMetadata annotationMetadata) {
        // 从 spring.factories 加载所有自动配置类
        List<String> configurations = getCandidateConfigurations(
            annotationMetadata,
            getAttributes()
        );
        // 去重、排序
        configurations = removeDuplicates(configurations);
        configurations = sort(configurations);
        // 条件过滤
        configurations = filter(configurations, getAutoConfigurationMetadata());
        return configurations.toArray(new String[0]);
    }

    protected List<String> getCandidateConfigurations(AnnotationMetadata metadata, Attributes attributes) {
        // 从 spring.factories 加载
        return SpringFactoriesLoader.loadFactoryNames(
            getSpringFactoriesLoaderFactoryClass(),
            getBeanClassLoader()
        );
    }
}
```

```
**步骤 3：spring.factories 定义配置类**
```

```properties
# spring-boot-autoconfigure/META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
org.springframework.boot.autoconfigure.admin.SpringApplicationAdminJmxAutoConfiguration,\
org.springframework.boot.autoconfigure.aop.AopAutoConfiguration,\
org.springframework.boot.autoconfigure.amqp.RabbitAutoConfiguration,\
# ... 更多配置类
```

```
**步骤 4：条件过滤**
```

```java
@Configuration
@ConditionalOnClass(DataSource.class)  // classpath 中有 DataSource 类
@ConditionalOnMissingBean(DataSource.class)  // 容器中没有 DataSource Bean
@EnableConfigurationProperties(DataSourceProperties.class)  // 绑定配置属性
public class DataSourceAutoConfiguration {

    @Bean
    @ConditionalOnProperty(name = "spring.datasource.type")  // 配置了 type 属性
    public DataSource dataSource(DataSourceProperties properties) {
        // 创建 DataSource
    }
}
```

```
**步骤 5：Bean 注册**
```
- 配置类本身注册为 BeanDefinition-   配置类中的 `@Bean` 方法解析为 BeanDefinition-   条件过滤后，符合条件的 Bean 被实例化
1. **自动配置报告**：
  - 启动参数 `--debug` 可以查看自动配置报告
  - 报告显示哪些配置类被匹配，哪些被排除
1. **实践注意**：
  - 如果不需要某个自动配置，可以用 `@EnableAutoConfiguration(exclude = {...})` 排除
  - 自定义 Starter 时，需要在 `spring.factories` 中声明配置类

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
只知道&quot;从 spring.factories 加载&quot;
</td>
<td>
完整链路，从注解到 Bean 注册
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 AutoConfigurationImportSelector
</td>
<td>
解释了选择器的工作机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有提到条件过滤和调试
</td>
<td>
给出自动配置报告和排除配置的方法
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
理解自动配置的设计思路和扩展能力
</td>
</tr>
</table>

---

#### 3、场景题：如何实现一个自定义 Starter，让 Agent 的 LLM 客户端在引入依赖后自动装配？

**难度级别**：⭐⭐⭐（自定义Starter、自动配置、spring.factories、条件装配）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：
- 场景分析
- 实现步骤
- 最佳实践
- 实践注意
- 需要创建一个 agent-llm-starter，让其他项目引入依赖后自动配置 LLM 客户端。
- 支持配置 LLM 的 API Key、模型名称、超时时间等参数。

**2️⃣ Impressive Answer**
1. **场景分析**：
  - 需要创建一个 `agent-llm-starter`，让其他项目引入依赖后自动配置 LLM 客户端。
  - 支持配置 LLM 的 API Key、模型名称、超时时间等参数。
  - 支持多种 LLM 提供商（OpenAI、通义千问等），通过配置切换。
1. **实现步骤**：
    **步骤 1：创建 Starter 项目结构**

```
agent-llm-starter/
├── pom.xml
└── src/main/java/
    └── com/example/agent/llm/
        ├── autoconfigure/
        │   ├── LlmAutoConfiguration.java
        │   └── LlmProperties.java
        ├── client/
        │   ├── LlmClient.java
        │   ├── OpenAiLlmClient.java
        │   └── QwenLlmClient.java
        └── META-INF/
            └── spring.factories
```

```
**步骤 2：定义配置属性**
```

```java
@ConfigurationProperties(prefix = "agent.llm")
public class LlmProperties {
    private String provider = "openai";  // 默认 OpenAI
    private String apiKey;
    private String model = "gpt-3.5-turbo";
    private Integer timeout = 30000;
    private Integer maxRetries = 3;

    // getters and setters...
}
```

```
**步骤 3：实现 LLM 客户端**
```

```java
public interface LlmClient {
    String chat(String prompt);
}

public class OpenAiLlmClient implements LlmClient {
    private final String apiKey;
    private final String model;

    public OpenAiLlmClient(String apiKey, String model) {
        this.apiKey = apiKey;
        this.model = model;
    }

    @Override
    public String chat(String prompt) {
        // 调用 OpenAI API
        return "Response from OpenAI";
    }
}

public class QwenLlmClient implements LlmClient {
    private final String apiKey;
    private final String model;

    public QwenLlmClient(String apiKey, String model) {
        this.apiKey = apiKey;
        this.model = model;
    }

    @Override
    public String chat(String prompt) {
        // 调用通义千问 API
        return "Response from Qwen";
    }
}
```

```
**步骤 4：创建自动配置类**
```

```java
@Configuration
@EnableConfigurationProperties(LlmProperties.class)
@ConditionalOnClass(LlmClient.class)  // classpath 中有 LlmClient 类
@ConditionalOnProperty(prefix = "agent.llm", name = "enabled", havingValue = "true", matchIfMissing = true)
public class LlmAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean(LlmClient.class)  // 容器中没有 LlmClient Bean
    public LlmClient llmClient(LlmProperties properties) {
        switch (properties.getProvider().toLowerCase()) {
            case "openai":
                return new OpenAiLlmClient(properties.getApiKey(), properties.getModel());
            case "qwen":
                return new QwenLlmClient(properties.getApiKey(), properties.getModel());
            default:
                throw new IllegalArgumentException("Unsupported provider: " + properties.getProvider());
        }
    }

    @Bean
    @ConditionalOnProperty(prefix = "agent.llm", name = "async", havingValue = "true")
    public LlmClient asyncLlmClient(LlmClient llmClient) {
        return new AsyncLlmClient(llmClient);
    }
}
```

```
**步骤 5：注册自动配置类**
```

```properties
# META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
com.example.agent.llm.autoconfigure.LlmAutoConfiguration
```

```
**步骤 6：使用 Starter**
```

```xml
<!-- pom.xml -->
<dependency>
    <groupId>com.example</groupId>
    <artifactId>agent-llm-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
# application.yml
agent:
  llm:
    enabled: true
    provider: openai
    api-key: ${LLM_API_KEY}
    model: gpt-4
    timeout: 30000
    async: true
```

```java
@Service
public class AgentService {
    @Autowired
    private LlmClient llmClient;  // 自动注入

    public String chat(String prompt) {
        return llmClient.chat(prompt);
    }
}
```
1. **最佳实践**：
  - **条件装配**：使用 `@ConditionalOnMissingBean` 允许用户自定义 Bean
  - **配置属性**：使用 `@ConfigurationProperties` 绑定配置，支持 IDE 自动提示
  - **文档完善**：提供 README 和配置示例
  - **测试覆盖**：编写自动配置的集成测试
1. **实践注意**：
  - Starter 的命名规范：`{name}-spring-boot-starter`
  - 如果需要条件装配，确保条件逻辑正确（如 `@ConditionalOnClass` 的类存在）
  - 自动配置类不要扫描包（`@ComponentScan`），避免意外的 Bean 注册

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
只知道&quot;创建配置类、写 spring.factories&quot;
</td>
<td>
完整实现，包含配置属性、客户端、条件装配
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
没有提到条件装配和配置绑定
</td>
<td>
解释了 @ConditionalOnMissingBean 的作用
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
没有给出生产级的代码示例
</td>
<td>
给出完整的 Starter 项目结构和最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
会写 Starter 但不规范
</td>
<td>
理解 Starter 的设计规范和生产级实践
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
@ConfigurationProperties 的作用？
</td>
<td>
配置属性绑定，支持自动提示
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：配置属性绑定，支持自动提示，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
@EnableConfigurationProperties 的作用？
</td>
<td>
启用配置属性类
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：启用配置属性类，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
Spring Boot 的 SPI 机制？
</td>
<td>
spring.factories 的加载机制
</td>
<td>
答：SpringFactoriesLoader 加载流程；Boot 3.x 的改进；spring.factories 支持的扩展点类型
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| Spring IoC 容器的工作原理是什么？Bean 的生命周期有哪些阶段？ | IoC 核心原理：IoC（Inversion of Control）是将对象的创建和依赖关系管理从代码中转移到容器。Spring 通过 BeanDefinition 描述 Bean 的元数据（类名、作用域、依赖关系等），容器根据 BeanDefinition 完成 Bean 的创建和装配；实例化阶段：通过构造器或工厂方法创建 Bean 实例；属性赋值阶段：Spring 对 Bean 的属性进行依赖注入（@Autowired、@Value）。 |
| BeanPostProcessor、InitializingBean、@PostConstruct 的执行顺序是什么？各自的应用场景？ | 执行顺序：实例化 → 属性赋值 → BeanPostProcessor.postProcessBeforeInitialization → @PostConstruct → InitializingBean.afterPropertiesSet → init-method → BeanPostProcessor.postProcessAfterInitialization；BeanPostProcessor 应用：在初始化前后对 Bean 进行增强，如 AOP 代理创建、属性校验、日志记录等；InitializingBean 应用：实现接口的 afterPropertiesSet 方法，依赖注入完成后执行必要初始化。 |
| Agent 的 LLM 客户端 Bean 需要在启动时预热连接池，如何利用 Bean 生命周期钩子实现？ | 选择 @PostConstruct：在 LLM 客户端 Bean 中添加 @PostConstruct 注解的方法；预热逻辑：方法中调用客户端发送少量测试请求（如健康检查），建立连接池连接；异常处理：捕获预热异常，记录日志并决定是否阻止 Bean 创建。 |
| 三级缓存与循环依赖 | 一级缓存（singletonObjects）：存放完全初始化好的 Bean；二级缓存（earlySingletonObjects）：存放提前暴露的 Bean（实例化但未初始化）；三级缓存（singletonFactories）：存放 Bean 工厂，用于生成提前暴露的对象（可能包含 AOP 代理）；创建 A，实例化后放入三级缓存；注入 B，发现 B 依赖 A。 |
| 什么是 Spring 的循环依赖？Spring 是如何解决的？ | 一级缓存（singletonObjects）：存放完全初始化好的 Bean；二级缓存（earlySingletonObjects）：存放提前暴露的 Bean（实例化但未初始化）；三级缓存（singletonFactories）：存放 Bean 工厂，用于生成提前暴露的对象（可能包含 AOP 代理）；创建 A，实例化后放入三级缓存；注入 B，发现 B 依赖 A。 |
| Spring 三级缓存（singletonObjects/earlySingletonObjects/singletonFactories）各自的作用是什么？为什么需要三级而不是两级？ | singletonObjects（一级）：Map，存放完全初始化的 Bean，getBean() 默认从这里获取；earlySingletonObjects（二级）：Map，存放实例化但未初始化的 Bean，用于循环依赖注入；singletonFactories（三级）：Map>，存放 Bean 工厂，延迟创建提前暴露对象（支持 AOP 代理）；两级缓存问题：如果只有两级，必须在实例化时就创建 AOP 代理，但此时还没确定是否需要代理（可能后续的 BeanPostProcessor 决定不代理）；三级缓存优势：三级缓存存的是工厂，只有真正发生循环依赖时才调用工厂创建代理，避免不必要的代理创建。 |
| Agent 服务中 ToolRegistry 和 AgentExecutor 互相依赖导致循环依赖，如何设计规避？ | Lazy：简单，但掩盖设计问题；事件驱动：解耦彻底，但增加复杂度；抽取接口：符合依赖倒置原则，推荐。 |
| Spring 中@Lazy 注解的作用是什么？如何解决循环依赖？ | 一级缓存：成品 Bean；二级缓存：早期暴露的 Bean（未填充属性）；三级缓存：ObjectFactory，用于生成 AOP 代理的早期引用。 |
| @Autowired、@Resource、@Inject 三种注入方式的区别？什么时候用构造器注入？ | 不可变性：依赖声明为 final，对象创建后不可修改，线程安全；避免 NPE：构造器注入保证依赖在使用前一定已注入，不会出现字段为 null 的情况；便于单测：不依赖 Spring 容器，直接 new 传入 mock 对象即可测试；暴露设计问题：构造器参数过多时，说明类职责过重，提醒重构。 |
| Spring 的依赖注入有哪几种方式？@Autowired 和 @Resource 有什么区别？ | 构造器注入：通过构造函数注入，依赖对象在 Bean 创建时就必须提供，保证 Bean 不可变且完全初始化；Setter 注入：通过 setter 方法注入，依赖对象可以在 Bean 创建后设置，支持可选依赖和循环依赖；字段注入：直接在字段上加 @Autowired，不推荐使用——无法进行单元测试（无法 mock 依赖）、隐藏依赖关系、违反单一职责原则；来源不同：@Autowired 是 Spring 注解，@Resource 是 JSR-250 标准（JDK 自带）；匹配策略：@Autowired 默认按类型匹配（byType），类型冲突时按 @Qualifier 指定名称 |
| Spring 的依赖注入底层是如何实现的？AutowiredAnnotationBeanPostProcessor 的工作原理？ | 注册阶段：实现了 MergedBeanDefinitionPostProcessor，在 Bean 定义合并后（postProcessMergedBeanDefinition）扫描类中的 @Autowired、@Value、@Inject 注解，构建注入元数据（InjectionMetadata）缓存；注入阶段：实现了 InstantiationAwareBeanPostProcessor，在 Bean 实例化后、属性填充前（postProcessProperties）执行注入逻辑；懒加载支持：@Lazy 注解会生成代理对象，延迟到实际使用时才注入真实 Bean；循环依赖处理：构造器注入无法解决循环依赖（因为 Bean 还没创建），Setter/字段注入通过三级缓存解决；Optional 支持：@Autowired + Optional 允许依赖不存在时注入 Optional.empty()。 |
| Agent 服务中有多个 LLM Provider 实现（OpenAI、Claude、通义千问），如何用 Spring 依赖注入实现策略模式动态切换？ | 多 LLM Provider 用统一接口抽象 chat/embed 等能力，Spring 注入所有实现为 Map，运行时按模型名、租户、成本、健康状态或灰度策略选择 Provider；失败时可自动降级到备用模型并记录路由原因。 |
| Spring Cache 缓存抽象 | Cacheable：先查缓存，命中则直接返回，不命中则执行方法并将结果存入缓存。适用于读多写少的查询方法 |
| Spring Cache 的 @Cacheable、@CachePut、@CacheEvict 分别有什么作用？ | Cacheable：先查缓存，命中则直接返回，不命中则执行方法并将结果存入缓存。适用于读多写少的查询方法 |
| Spring Cache 的底层抽象是什么？如何集成 Redis 作为缓存后端？CacheManager 的工作原理？ | Cache 接口：定义缓存的基本操作（get、put、evict、clear），实现类有 ConcurrentMapCache（本地内存）、RedisCache（Redis）、CaffeineCache（Caffeine）；CacheManager 接口：管理多个 Cache 实例，根据 cacheName 获取对应的 Cache；启动时根据 @Cacheable 的 value/cacheNames 创建对应的 Cache 实例；运行时根据 cacheName 从 CacheManager 获取 Cache，然后执行缓存操作；RedisCache 的 key 生成规则：缓存区名::实际key（如 users::1001）。 |
| @Async 注解如何使用？需要哪些前置配置？ | 在启动类或配置类上加 @EnableAsync 注解；配置线程池（可选，默认使用 SimpleAsyncTaskExecutor，每次创建新线程，不推荐） |
| @Async 的底层实现原理是什么？如何自定义线程池？异步方法的异常如何处理？ | EnableAsync 导入 AsyncConfigurationSelector，注册 ProxyAsyncConfiguration；AsyncAnnotationBeanPostProcessor 扫描 @Async 注解，为 Bean 创建 AOP 代理；代理拦截器 AnnotationAsyncExecutionInterceptor 将方法调用提交到线程池执行；如果 @Async 指定了线程池名称，使用指定的线程池；如果未指定，查找名为 taskExecutor 的 TaskExecutor Bean。 |
| AOP 原理 | 代理机制不同：JDK 动态代理基于接口，运行时通过反射生成代理类，要求目标类必须实现接口；CGLIB 通过 ASM 字节码框架生成目标类的子类，不依赖接口，但 final 类/方法无法代理；Spring 的选择策略：Spring Boot 2.x 起默认优先使用 CGLIB（spring.aop.proxy-target-class=true），减少因没有接口导致代理失败的问题；也可以强制指定；自调用失效是核心陷阱：同一个 Bean 内部方法 A 调用方法 B，B 上的 AOP 不生效，因为调用绕过了代理对象，直接走 this；解决方案是注入自身代理（AopContext.currentProxy()）或拆分到另一个 Bean。 |
| Spring AOP 的两种代理方式（JDK 动态代理 vs CGLIB）有什么区别？ | 代理机制不同：JDK 动态代理基于接口，运行时通过反射生成代理类，要求目标类必须实现接口；CGLIB 通过 ASM 字节码框架生成目标类的子类，不依赖接口，但 final 类/方法无法代理；Spring 的选择策略：Spring Boot 2.x 起默认优先使用 CGLIB（spring.aop.proxy-target-class=true），减少因没有接口导致代理失败的问题；也可以强制指定；自调用失效是核心陷阱：同一个 Bean 内部方法 A 调用方法 B，B 上的 AOP 不生效，因为调用绕过了代理对象，直接走 this；解决方案是注入自身代理（AopContext.currentProxy()）或拆分到另一个 Bean。 |
| Spring AOP 的完整执行链路是什么？ProxyFactory、PointcutAdvisor、MethodInterceptor 各自的角色？ | ProxyFactory：代理工厂，根据 Advisor 创建代理对象（JDK 或 CGLIB）；PointcutAdvisor：切面定义，包含 Pointcut（切点，匹配哪些方法）和 Advice（通知，做什么）；MethodInterceptor：方法拦截器，Advice 的实现，负责拦截方法调用（如 MethodBeforeAdviceInterceptor）；AdvisedSupport：持有所有 Advisor 和配置信息。 |
| 如何用 Spring AOP 实现 Agent 工具调用的统一耗时监控和异常捕获？ | tool.call.duration：工具调用耗时（P50/P95/P99）；tool.call.count：工具调用次数（成功/失败）；配合 Prometheus + Grafana 可视化监控。 |
| Agent 的工具调用需要统一做鉴权和耗时日志，如何用 AOP 实现？ | 定义标记注解：自定义 @ToolAuth(permission="xxx")，标注在需要鉴权的工具方法上，便于精确切入，不污染无关方法 |
| @Transactional 注解有哪些常见的失效场景？ | 方法修饰符问题：@Transactional 只能作用于 public 方法，private、protected、package-private 会失效（Spring AOP 代理限制）；异常类型问题：默认只回滚 RuntimeException 和 Error，检查型异常（如 IOException）不回滚。需指定 rollbackFor = Exception.class；自调用问题：同一个类内部方法调用不经过代理，事务失效。 |
| Spring 事务的 7 种传播机制分别是什么？REQUIRED 和 REQUIRES_NEW 的区别？ | REQUIRED：（默认）：如果当前有事务，加入；否则新建；REQUIRES_NEW：总是新建事务，挂起当前事务；SUPPORTS：如果当前有事务，加入；否则非事务执行；NOT_SUPPORTED：总是非事务执行，挂起当前事务；MANDATORY：必须当前有事务，否则抛异常。 |
| Agent 执行多步骤任务（工具调用→结果存储→状态更新），如何设计事务边界保证数据一致性？ | 单事务：所有操作在同一个数据库，简单场景；独立事务：涉及外部调用，需要部分成功；Saga：长流程、多服务、需要补偿机制。 |
| BeanPostProcessor 和 BeanFactoryPostProcessor 的区别？各自的典型应用场景？ | BeanFactoryPostProcessor 在 Bean 实例化前修改 BeanDefinition，适合改元数据和属性定义；BeanPostProcessor 在 Bean 实例化后、初始化前后增强 Bean 实例，AOP、代理包装、初始化增强通常依赖它。 |
| 如何实现一个自定义注解，让 Agent 的工具方法自动注册到工具列表中？ | 定义工具注解：@AgentTool(name="search", description="搜索工具")，标注在方法上，携带工具名称和描述信息，用于生成 Function Definition 给模型 |
| Spring 事务管理 | 自调用失效（最常见）：同一个 Bean 内部方法 A 调用带@Transactional 的方法 B，B 的事务不生效。原因：AOP 代理对象才是事务载体，自调用走的是 this.B()，绕过了代理。解决：注入自身代理调用，或用 AopContext.currentProxy()；访问权限限制：@Transactional 只能标注在 public 方法上。protected/private 方法即使加上也不会生效，因为 Spring AOP 默认只代理 public 方法；异常类型不匹配：默认只回滚 RuntimeException 和 Error。如果抛的是受检异常（Checked Exception），需要显式指定 @Transactional(rollbackFor = Exception.class)。 |
| @Transactional 注解的作用是什么？Spring 事务的传播机制有哪些？ | REQUIRED：（默认）：当前有事务就加入，没有就新建；REQUIRES\_NEW：不管有没有事务，都新建一个（当前事务会被挂起）；SUPPORTS：有事务就加入，没有就以非事务方式执行；NOT\_SUPPORTED：以非事务方式执行，如果有事务就挂起；MANDATORY：必须有事务，否则抛异常。 |
| @Transactional 在什么情况下会失效？ | 自调用失效（最常见）：同一个 Bean 内部方法 A 调用带@Transactional 的方法 B，B 的事务不生效。原因：AOP 代理对象才是事务载体，自调用走的是 this.B()，绕过了代理。解决：注入自身代理调用，或用 AopContext.currentProxy()；访问权限限制：@Transactional 只能标注在 public 方法上。protected/private 方法即使加上也不会生效，因为 Spring AOP 默认只代理 public 方法；异常类型不匹配：默认只回滚 RuntimeException 和 Error。如果抛的是受检异常（Checked Exception），需要显式指定 @Transactional(rollbackFor = Exception.class)。 |
| Agent 执行多步工具调用，如何保证部分失败时数据一致性？ | 本地事务兜底：单服务内多步操作（如写 DB + 发消息）用 @Transactional 保证原子性；消息发送用事务消息表，本地事务提交后由定时任务异步投递，保证最终一致；跨服务 Saga 模式：Agent 多步工具调用涉及多个微服务时，用 Saga 编排：每个步骤有正向操作和补偿操作，步骤 3 失败则逆向执行步骤 2→1 的补偿。Spring Cloud State Machine 或自研引擎可实现；幂等 + 重试：每个工具调用设计幂等性（唯一键/状态机），失败后安全重试；配合本地消息表 + 事务性轮询，确保补偿操作必然执行。 |
| Spring 事务的底层实现原理？TransactionManager 和 TransactionSynchronizationManager 的作用？ | PlatformTransactionManager 三板斧：getTransaction()（获取/创建事务）、commit()、rollback()。DataSourceTransactionManager 实现中，getTransaction() 从 DataSource 获取 Connection 并设置 autoCommit=false，然后将 Connection 绑定到 ThreadLocal；TransactionSynchronizationManager 的核心作用：通过 ThreadLocal 维护当前线程的事务资源（Connection、Session 等）和同步回调。@Transactional 方法内所有 DAO 操作通过 DataSourceUtils.getConnection() 获取的都是同一个 Connection，这就是事务生效的根本原因；事务同步回调：TransactionSynchronization 接口提供 beforeCommit()、afterCommit()、afterCompletion() 等钩子。典型应用：事务提交后发消息（避免事务未提交就发消息导致消费者查不到数据）。 |
| Agent 执行工具调用时需要"部分提交"，前 3 步成功就保存，第 4 步失败不影响前 3 步，如何设计？ | 部分提交可以把每一步工具调用拆成独立事务，成功步骤立即落库并记录状态，失败步骤只标记失败不回滚前序结果；关键是每步幂等、状态可恢复，并提供补偿任务处理后续失败。 |
| Spring 如何解决循环依赖？三级缓存的作用分别是什么？ | 一级缓存 singletonObjects：存放完全初始化好的 Bean（实例化+属性填充+初始化完成）；二级缓存 earlySingletonObjects：存放提前暴露的半成品 Bean（已实例化但未填充属性），用于解决循环依赖；三级缓存 singletonFactories：存放 ObjectFactory 工厂，用于生成提前暴露的 Bean，关键是可能生成 AOP 代理对象。 |
| 为什么构造器注入无法解决循环依赖？@Lazy 如何解决？ | ObjectProvider：注入 ObjectProvider，调用 getObject() 时才获取 Bean；ApplicationContext.getBean()：在需要时手动从容器获取，但增加了容器耦合 |
| Spring Boot 2.6+ 默认禁止循环依赖，如何优雅地重构消除循环依赖？ | Spring Boot 2.6 的变化：spring.main.allow-circular-references 默认从 true 改为 false，强制要求消除循环依赖，这是为了推动更健康的架构设计 |
| @Configuration 和 @Component 的区别？@Bean 方法的 Full 模式代理机制？ | Configuration 是配置类，Spring 会用 CGLIB 代理，保证 @Bean 方法调用返回同一个实例 |
| Spring 容器 refresh() 的 12 个核心步骤是什么？ | 第 5 步 invokeBeanFactoryPostProcessors 是最关键的，@Configuration、@ComponentScan 都在这里解析；第 11 步 finishBeanFactoryInitialization 完成 Bean 的完整生命周期（包括 AOP 代理）；第 12 步 finishRefresh 后，容器就完全就绪了。 |
| Spring 设计模式与扩展点 | Spring 框架是设计模式的教科书级应用，我从 7 个核心模式来说：；工厂模式：BeanFactory / ApplicationContext 是 Bean 的工厂，根据 BeanDefinition 创建对象。FactoryBean 接口让用户自定义复杂 Bean 的创建逻辑；单例模式：Bean 默认 Singleton 作用域，通过三级缓存（singletonObjects）保证全局唯一。不是传统的私有构造器单例，而是容器级别的单例。 |
| Spring 中用到了哪些设计模式？举例说明 | Spring 框架是设计模式的教科书级应用，我从 7 个核心模式来说：；工厂模式：BeanFactory / ApplicationContext 是 Bean 的工厂，根据 BeanDefinition 创建对象。FactoryBean 接口让用户自定义复杂 Bean 的创建逻辑；单例模式：Bean 默认 Singleton 作用域，通过三级缓存（singletonObjects）保证全局唯一。不是传统的私有构造器单例，而是容器级别的单例。 |
| Spring 事件机制 | 方式一：@EventListener + @Async，需要 @EnableAsync 开启异步支持；方式二：配置 ApplicationEventMulticaster 的 TaskExecutor，全局异步；注意：异步事件的异常不会传播到发布者，需要在监听器内部单独处理。 |
| Spring 的事件机制（ApplicationEvent）如何实现？同步还是异步？ | 方式一：@EventListener + @Async，需要 @EnableAsync 开启异步支持；方式二：配置 ApplicationEventMulticaster 的 TaskExecutor，全局异步；注意：异步事件的异常不会传播到发布者，需要在监听器内部单独处理。 |
| 如何用 Spring 事件机制实现 Agent 工具调用的审计日志？ | 审计日志监听器：@EventListener + @Async，异步写入审计日志表（DB）；实时分析监听器：推送到 Kafka，供实时数据分析平台消费；告警监听器：检测异常调用（如耗时 > 阈值、连续失败），触发告警通知。 |
| ApplicationEvent 和 @EventListener 的基本用法？ | ApplicationEvent 是 Spring 的应用内事件模型，发布方通过 ApplicationEventPublisher 发事件，监听方用 @EventListener 或 ApplicationListener 处理；它适合同进程内解耦，异步执行需配合 @Async 或自定义事件多播器。 |
| 同步事件 vs 异步事件（@Async）的区别？@TransactionalEventListener 的作用？ | 默认行为，发布事件的线程立即执行所有监听器；优点：事务一致性，监听器可以回滚事务；缺点：阻塞主流程，影响性能；优点：解耦、提升性能，适合日志、通知等非核心流程；缺点：监听器无法回滚主事务，需要处理事务一致性。 |
| Agent 工具调用完成后如何用事件机制解耦通知下游（日志、计费、审计）？ | 解耦：工具执行逻辑和日志、计费、审计逻辑完全分离；扩展：新增下游处理只需添加监听器，无需修改工具执行代码；性能：异步处理不阻塞主流程。 |
| @Conditional 系列注解有哪些？各自触发条件？ | ConditionalOnClass：类路径存在指定类 |
| Spring Boot 自动配置的原理（spring.factories / AutoConfiguration.imports）？ | Spring Boot 启动时，通过 @EnableAutoConfiguration 导入 AutoConfigurationImportSelector；AutoConfigurationImportSelector 从 META-INF/spring.factories（Spring Boot 2.7 之前）或 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports（Spring Boot 2.7+）加载自动配置类；自动配置类使用 @Conditional 系列注解，根据类路径、配置、Bean 存在性等条件决定是否生效；启动参数：--debug 或 --logging.level.org.springframework.boot.autoconfigure=DEBUG；查看报告：启动日志会输出哪些自动配置类生效/未生效。 |
| 如何自定义一个 Spring Boot Starter，让 Agent 工具库开箱即用？ | calculator-tool；agent-spring-boot-starter/；│ └── com/example/agent/。 |
| Bean 的 6 种作用域分别是什么？各自适用场景？ | singleton：单例，容器中只有一个实例（默认）；prototype：原型，每次请求创建新实例；request：请求，每个 HTTP 请求一个实例（Web 环境）；session：会话，每个 HTTP Session 一个实例（Web 环境）；application：应用，ServletContext 生命周期内一个实例（Web 环境）。 |
| Singleton Bean 注入 Prototype Bean 的陷阱？@Lookup 和 ObjectProvider 如何解决？ | Singleton Bean 只初始化一次，注入的 Prototype Bean 也只创建一次；后续使用 toolRequest 时，仍然是同一个实例，违背了 Prototype 的设计意图；Spring 会生成 CGLIB 子类，覆盖 getToolRequest() 方法，每次调用都从容器获取新实例；ObjectProvider 是延迟获取 Bean 的工具，每次调用 getObject() 都会从容器获取新实例；Spring 会生成代理对象，每次调用代理对象的方法时，都会从容器获取新的目标对象。 |
| Agent 会话级别的上下文（如对话历史）如何用 Session 作用域 Bean 管理？ | proxyMode = ScopedProxyMode.TARGET_CLASS：Spring 生成 CGLIB 代理，代理对象持有 Session 引用；每次调用代理对象的方法时，代理会从当前 Session 获取对应的真实 Bean |
| @Value、@ConfigurationProperties、Environment 三种配置读取方式的区别？ | Value 适合注入单个配置并支持 SpEL，但不支持松散绑定和类型安全校验，配置错误通常到运行时才暴露 |
| PropertySource 的加载优先级？如何实现配置动态刷新（@RefreshScope）？ | 原理：@RefreshScope 基于 GenericScope，Bean 是代理对象，配置变更时销毁旧 Bean，创建新 Bean；触发：通过 /actuator/refresh 端点或配置中心（如 Nacos、Apollo）推送变更 |
| Agent 的 LLM 配置（模型名、temperature、API Key）如何用配置中心动态热更新？ | LLM 配置热更新通常用配置中心加刷新作用域或监听机制，模型名、temperature、API Key 等配置变更后刷新配置 Bean 或路由表；敏感信息要加密存储，刷新时要保证存量请求不受影响。 |
| @Scheduled 注解如何使用？cron 表达式如何编写？ | 0 0 2 * * ?：每天凌晨 2 点；0 0/5 * * * ?：每 5 分钟；0 0 12 ? * MON-FRI：周一到周五中午 12 点；0 0 12 L * ?：每月最后一天中午 12 点；0 15 10 ? * 6L：每月最后一个周五上午 10:15。 |
| Spring 定时任务的底层实现是什么？TaskScheduler 和 ThreadPoolTaskScheduler 的关系？分布式环境下如何避免重复执行？ | EnableScheduling 导入 SchedulingConfiguration，注册 ScheduledAnnotationBeanPostProcessor；ScheduledAnnotationBeanPostProcessor 扫描 @Scheduled 注解，注册定时任务到 TaskScheduler；TaskScheduler 根据调度策略（fixedRate、fixedDelay、cron）提交任务到线程池执行；TaskScheduler：定时任务调度接口，定义了 schedule()、scheduleAtFixedRate() 等方法；ThreadPoolTaskScheduler：基于 ThreadPoolTaskExecutor 的实现，支持并行执行。 |
| @Async 的线程池隔离如何配置？@Async 和事务的关系？ | 异步方法不会继承调用方的事务，因为不在同一个线程；异步方法需要自己开启事务（@Transactional）；主事务无法感知异步方法的异常；如果需要事务一致性，应该使用同步方法或分布式事务。 |
| @SpringBootTest vs @WebMvcTest vs @DataJpaTest 的区别？ | 完整集成测试，启动整个 Spring 上下文；适合测试完整流程，但启动慢；Web 层切片测试，只加载 Controller 相关的 Bean；适合测试 Controller，启动快；数据访问层切片测试，只加载 Repository 相关的 Bean。 |
| 如何用 @MockBean 和 @SpyBean 隔离外部依赖？两者的区别？ | MockBean 会用 Mockito mock 替换 Spring 容器中的 Bean，适合完全隔离外部依赖；SpyBean 包装真实 Bean，只对部分方法打桩，适合保留真实逻辑但控制少数外部调用。 |
| 如何对 Agent 工具调用链路做集成测试，Mock LLM 响应并验证工具调用顺序？ | Agent 工具调用链路集成测试应 Mock LLM 输出和外部工具响应，用 MockMvc 或测试客户端触发完整请求，再验证工具调用顺序、参数、状态落库、异常分支和最终响应，确保编排逻辑可回归。 |
| @ExceptionHandler 和 @ControllerAdvice 是什么？如何做全局异常处理？ | ExceptionHandler：用于处理 Controller 方法抛出的特定异常，可以返回自定义的响应 |
| Spring MVC 异常处理的优先级链是什么？多个 @ControllerAdvice 的执行顺序如何控制？ | Spring MVC 异常处理优先走当前 Controller 内的 ExceptionHandler，再走 ControllerAdvice，最后由默认异常解析器处理框架内置异常；多个 ControllerAdvice 可用 Order 或 Ordered 控制优先级。 |
| Agent 调用 LLM 超时、工具执行失败、参数校验失败，如何统一封装错误响应格式？ | 错误码国际化：错误消息支持多语言，根据请求头 Accept-Language 返回对应语言；错误详情：开发环境返回详细错误栈，生产环境返回通用错误消息；监控告警：对 LLM 超时、工具失败等异常进行监控和告警。 |
| @Value、@ConfigurationProperties、Environment 三种读取配置的方式有什么区别？ | Value 适合注入单个配置并支持 SpEL，但不支持松散绑定和类型安全校验，配置错误通常到运行时才暴露 |
| Spring 的 PropertySource 优先级链是什么？如何实现配置的动态刷新（@RefreshScope）？ | 后加载的优先级高：后面的 PropertySource 会覆盖前面的同名属性；Profile 优先：激活的 Profile 配置会覆盖默认配置；命令行参数最高：方便运维临时调整配置；原理：@RefreshScope 标注的 Bean 会被代理，配置刷新时，代理会重新创建 Bean 实例，注入新的配置值；刷新触发：调用 /actuator/refresh 端点，Spring Cloud Config 会重新加载配置并刷新 @RefreshScope Bean。 |
| Agent 的 LLM API Key、模型参数需要多环境隔离 + 运行时热更新，如何设计配置方案？ | 手动触发：调用 /api/admin/config/refresh 端点；自动触发：配置中心（如 Nacos、Apollo）推送配置变更，监听变更事件自动刷新；定时刷新：定时任务检查配置变更，自动刷新；敏感配置加密：使用 Jasypt 加密 API Key，配置文件中存储加密值；环境变量注入：生产环境的 API Key 通过环境变量注入，不在配置文件中暴露。 |
| Spring 异步与线程池 | AOP 代理：@Async 是一个 AOP 注解，Spring 会为标注了 @Async 的 Bean 创建代理（JDK 动态代理或 CGLIB）；拦截器：AsyncAnnotationBeanPostProcessor 会注册一个 AnnotationAsyncExecutionInterceptor，拦截 @Async 方法调用；TaskExecutor：拦截器将方法调用包装成 Runnable，提交到 TaskExecutor 线程池执行；返回值处理：如果方法返回 CompletableFuture，拦截器会等待异步执行完成并返回结果；代理机制：Spring AOP 是基于代理的，只有通过代理调用的方法才会被拦截。 |
| @Async 注解的作用是什么？如何配置自定义线程池？ | Async 让方法通过 AOP 代理提交到线程池异步执行，调用方立即返回；自定义线程池要配置核心线程数、队列、拒绝策略和线程名前缀，void 方法异常用 AsyncUncaughtExceptionHandler，Future/CompletableFuture 异常由调用方处理。 |
| @Async 的实现原理是什么（AOP + TaskExecutor）？为什么 @Async 在同类自调用时失效？ | AOP 代理：@Async 是一个 AOP 注解，Spring 会为标注了 @Async 的 Bean 创建代理（JDK 动态代理或 CGLIB）；拦截器：AsyncAnnotationBeanPostProcessor 会注册一个 AnnotationAsyncExecutionInterceptor，拦截 @Async 方法调用；TaskExecutor：拦截器将方法调用包装成 Runnable，提交到 TaskExecutor 线程池执行；返回值处理：如果方法返回 CompletableFuture，拦截器会等待异步执行完成并返回结果；代理机制：Spring AOP 是基于代理的，只有通过代理调用的方法才会被拦截。 |
| Agent 并发调用多个工具（并行 Tool Call），如何用 Spring 异步 + CompletableFuture 实现并发编排，并处理部分失败？ | 熔断降级：使用 Resilience4j 实现熔断，连续失败时快速失败；限流：限制并发工具调用的数量，避免资源耗尽；重试：对失败的工具调用进行重试，提高成功率。 |
| Spring 事务底层原理 | AOP 代理：@Transactional 是一个 AOP 注解，Spring 会为标注了 @Transactional 的 Bean 创建代理；TransactionInterceptor：拦截 @Transactional 方法调用，在方法执行前开启事务，执行后提交或回滚事务；PlatformTransactionManager：事务管理器，负责事务的开启、提交、回滚。常用实现：；DataSourceTransactionManager：JDBC 事务管理器；JpaTransactionManager：JPA 事务管理器。 |
| 编程式事务（TransactionTemplate）和声明式事务（@Transactional）的区别是什么？ | 编程式：灵活但繁琐，适合复杂事务逻辑；声明式：简洁但不够灵活，适合大多数场景；编程式事务（TransactionTemplate）：在代码中显式管理事务，使用 TransactionTemplate.execute() 包裹事务代码；声明式事务（@Transactional）：通过注解声明事务，Spring AOP 自动管理事务，代码更简洁。 |
| Spring 事务的底层实现原理是什么？TransactionInterceptor + PlatformTransactionManager + ThreadLocal 如何协作？ | AOP 代理：@Transactional 是一个 AOP 注解，Spring 会为标注了 @Transactional 的 Bean 创建代理；TransactionInterceptor：拦截 @Transactional 方法调用，在方法执行前开启事务，执行后提交或回滚事务；PlatformTransactionManager：事务管理器，负责事务的开启、提交、回滚。常用实现：；DataSourceTransactionManager：JDBC 事务管理器；JpaTransactionManager：JPA 事务管理器。 |
| Agent 执行完工具调用后需要在事务提交后才发消息（避免消息先到但数据未提交），如何用 TransactionSynchronization 实现？ | 异步发送：事务提交后异步发送消息，避免阻塞事务提交；消息幂等：确保消息幂等，避免重复发送；补偿机制：如果消息发送失败，需要补偿机制（重试或人工介入）。 |
| Spring 容器启动流程 | 步骤⑤：BeanFactoryPostProcessor 可以修改 BeanDefinition（如 @ConfigurationClassPostProcessor 处理 @Configuration）；步骤⑥：BeanPostProcessor 在 Bean 创建前后拦截，AOP 代理在 postProcessAfterInitialization 创建；步骤⑪：真正的 Bean 实例化，包括依赖注入、初始化回调。 |
| ApplicationContext 和 BeanFactory 的区别是什么？ | 国际化支持：MessageSource 接口，支持 i18n；事件发布：ApplicationEventPublisher，支持事件监听机制；资源加载：ResourceLoader，支持从 classpath、URL 等加载资源；环境抽象：Environment，支持 profile、配置属性；预实例化：默认在容器启动时创建所有 singleton Bean（可通过 lazy-init 覆盖）。 |
| Spring 容器的 refresh() 方法做了哪些事？核心步骤是什么？ | 步骤⑤：BeanFactoryPostProcessor 可以修改 BeanDefinition（如 @ConfigurationClassPostProcessor 处理 @Configuration）；步骤⑥：BeanPostProcessor 在 Bean 创建前后拦截，AOP 代理在 postProcessAfterInitialization 创建；步骤⑪：真正的 Bean 实例化，包括依赖注入、初始化回调。 |
| 如何在 Spring 容器完全启动后执行初始化逻辑？ApplicationRunner、CommandLineRunner、@EventListener(ContextRefreshedEvent) 有什么区别？ | ApplicationRunner 和 CommandLineRunner 都在 Spring Boot 启动完成、ApplicationContext 就绪后执行，区别是 ApplicationRunner 接收解析后的 ApplicationArguments，适合读取 option/non-option 参数，CommandLineRunner 接收原始 String[]，适合简单命令行参数处理。 |
| 什么是循环依赖？Spring 默认是如何解决的？ | 可以解决：setter 注入（单例 Bean），通过三级缓存机制；无法解决：构造器注入（实例化时就需要依赖对象，无法提前暴露）；无法解决：prototype 作用域（每次都创建新实例，缓存机制失效）。 |
| Spring 三级缓存的结构是什么？为什么需要三级而不是两级？ | 如果只有两级：在实例化 A 时，如果 A 需要 AOP 代理，必须立即创建代理对象并放入二级缓存。但此时 A 还没初始化，无法确定是否真的需要代理（可能被其他逻辑覆盖）；三级缓存的优势：ObjectFactory 是延迟执行的，只有在其他 Bean 真正引用 A 时，才调用 getObject() 创建代理。这样可以：；避免不必要的代理创建（如果 A 不被循环引用，就不需要代理）；确保 AOP 代理在正确的时机创建（getEarlyBeanReference 回调）。 |
| 构造器注入为什么无法解决循环依赖？项目中遇到循环依赖应该怎么处理？ | 实例化时机：构造器注入在实例化阶段就需要依赖对象，而三级缓存是在实例化后才将半成品暴露出去；死锁问题：A 实例化需要 B，B 实例化需要 A，两者都无法实例化，形成死锁；原理：@Lazy 会先注入一个代理对象，真正调用时才从容器获取真实 Bean，打破循环依赖；引入中间层：A 和 B 都依赖 C，通过 C 通信- 事件驱动：A 发布事件，B 监听事件- 设计模式：使用观察者模式、中介者模式解耦；优先使用构造器注入（保证不可变性），遇到循环依赖时用 @Lazy。 |
| Spring 事件机制 | 注册时机：EventListenerMethodProcessor（BeanFactoryPostProcessor）在容器启动时扫描所有带 @EventListener 的方法；包装为 ApplicationListener：将方法包装成 ApplicationListenerMethodAdapter，注册到 ApplicationEventMulticaster；事件匹配：通过反射检查方法参数类型，匹配到对应事件时调用方法；同步事件：监听器在发布者的事务中执行，如果监听器抛异常，发布者的事务会回滚；异步事件：监听器在独立线程执行，不共享发布者的事务，即使监听器抛异常也不影响发布者。 |
| Spring 的事件发布/监听机制是什么？如何使用？ | 核心原理：Spring 事件机制是观察者模式的实现，通过 ApplicationEventPublisher 发布事件，ApplicationListener 监听事件，实现组件间的解耦；方式 1：继承 ApplicationListener（传统方式）；核心优势：解耦业务逻辑，发布者不需要知道有哪些监听者，监听者之间互不影响。 |
| @EventListener 的实现原理是什么？同步事件和异步事件（@Async）有什么区别？ | 注册时机：EventListenerMethodProcessor（BeanFactoryPostProcessor）在容器启动时扫描所有带 @EventListener 的方法；包装为 ApplicationListener：将方法包装成 ApplicationListenerMethodAdapter，注册到 ApplicationEventMulticaster；事件匹配：通过反射检查方法参数类型，匹配到对应事件时调用方法；同步事件：监听器在发布者的事务中执行，如果监听器抛异常，发布者的事务会回滚；异步事件：监听器在独立线程执行，不共享发布者的事务，即使监听器抛异常也不影响发布者。 |
| Agent 工具调用完成后需要异步通知多个下游系统，如何用 Spring 事件解耦？ | Agent 调用工具后，需要通知多个下游系统（日志系统、监控系统、审计系统等）；下游系统的处理不应该影响 Agent 的响应速度，也不应该因为某个下游系统失败而影响主流程；异步发布：callTool 方法本身就是 @Async，事件发布也在异步线程中，不会阻塞用户请求；异常隔离：某个监听器失败不会影响其他监听器，也不会影响 Agent 主流程；独立线程池：使用专用线程池，避免和业务线程池竞争资源。 |
| Spring Bean 有哪些作用域？singleton 和 prototype 的区别？ | singleton：（默认）：单例，整个容器只有一个实例；prototype：原型，每次 getBean 都创建新实例；request：每个 HTTP 请求一个实例（仅 Web 环境）；session：每个 HTTP Session 一个实例（仅 Web 环境）；application：ServletContext 生命周期一个实例（仅 Web 环境）。 |
| singleton Bean 注入 prototype Bean 时，为什么每次拿到的不是新实例？如何解决？ | 依赖注入时机：singleton Bean 在容器启动时初始化，此时注入的 prototype Bean 只会被创建一次；缓存机制：注入后，prototype Bean 的引用被 singleton Bean 持有，后续调用时复用同一个实例；原理：Spring 通过 CGLIB 动态代理子类，重写 getPrototypeBean() 方法，每次调用时从容器获取新实例。 |
| Agent 的会话上下文（每个用户会话独立）如何用 Spring Scope 管理？ | Agent 每次对话需要维护会话上下文（历史消息、用户偏好、工具调用状态等）；不同用户的会话上下文必须隔离，同一用户的多次请求共享上下文；注意：需要在 singleton Bean 中注入 Session Scope Bean 时，使用 proxyMode = ScopedProxyMode.TARGET_CLASS 创建代理对象；Web 环境优先用 Session Scope；如果需要跨请求共享上下文（如 WebSocket），用自定义 Scope 或 Redis 存储。 |
| @ConditionalOnProperty、@ConditionalOnClass 等条件注解的作用是什么？ | ConditionalOnProperty：根据配置属性判断 |
| Spring Boot 自动配置的原理是什么？从 @EnableAutoConfiguration 到 Bean 注册的完整链路？ | 配置类本身注册为 BeanDefinition- 配置类中的 @Bean 方法解析为 BeanDefinition- 条件过滤后，符合条件的 Bean 被实例化；启动参数 --debug 可以查看自动配置报告；报告显示哪些配置类被匹配，哪些被排除；如果不需要某个自动配置，可以用 @EnableAutoConfiguration(exclude = {}) 排除；自定义 Starter 时，需要在 spring.factories 中声明配置类。 |
| 如何实现一个自定义 Starter，让 Agent 的 LLM 客户端在引入依赖后自动装配？ | 需要创建一个 agent-llm-starter，让其他项目引入依赖后自动配置 LLM 客户端；支持配置 LLM 的 API Key、模型名称、超时时间等参数；支持多种 LLM 提供商（OpenAI、通义千问等），通过配置切换；条件装配：使用 @ConditionalOnMissingBean 允许用户自定义 Bean；配置属性：使用 @ConfigurationProperties 绑定配置，支持 IDE 自动提示。 |
