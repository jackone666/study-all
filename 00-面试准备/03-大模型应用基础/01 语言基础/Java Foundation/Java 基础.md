## 1.1 String 与 StringBuilder/StringBuffer

### 不可变字符串与可变字符串的选择与优化

#### 1、基础题：String 为什么要设计成不可变的？

**难度**：⭐（不可变性、安全性、线程安全、缓存优化）

**Answer**：

String 设计成不可变主要有这几个好处：

1. **字符串常量池的需要**：JVM 中有字符串常量池，同一个字符串字面量只存一份。如果 String 可变，修改一个引用会影响所有指向它的变量，造成混乱。

2. **安全性**：String 广泛用于文件路径、URL、数据库连接等敏感场景。如果可变，传递后可能被篡改，带来安全隐患。

3. **线程安全**：不可变对象天然是线程安全的，多线程共享时无需同步，提升了性能和安全性。

4. **缓存 Hash 值**：String 的 hashCode 会被缓存，第一次调用后就不再计算。如果可变，hash 值会失效，影响 HashMap 等集合的使用。

---

#### 2、进阶题：StringBuilder 和 StringBuffer 有什么区别？各自适用什么场景？

**难度**：⭐⭐（线程安全、性能对比、场景选择）

1️⃣ **Common Answer**：

StringBuilder 和 StringBuffer 都是可变的字符串类。StringBuffer 是线程安全的，有 synchronized 关键字。StringBuilder 不是线程安全的，但性能更好。单线程用 StringBuilder，多线程用 StringBuffer。

2️⃣ **Impressive Answer**：

我会从这几个角度分析：

1. **线程安全机制**：StringBuffer 的关键方法（append、insert、delete）都加了 synchronized 锁，保证线程安全。而 StringBuilder 没有加锁，所以单线程下性能更高，大概快 10%-15%。

2. **底层实现**：两者都继承自 AbstractStringBuilder，底层都是 char 数组（JDK8）或 byte 数组（JDK9+ 的 Compact Strings）。区别只在于是否同步。

3. **场景选择**：

  - 单线程/方法内部：优先用 StringBuilder，比如循环拼接字符串

  - 多线程共享：用 StringBuffer，但更推荐用 ThreadLocal 或锁外控

  - 实际项目中，90% 的场景用 StringBuilder，因为大多数拼接都是方法内局部操作

4. **性能对比**：在 JMH 基准测试下，10000 次循环拼接，StringBuilder 耗时约 2ms，StringBuffer 约 2.5ms，String 则超过 50ms。

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 只知道加锁区别 | 理解底层实现和性能差异 |
| 实践体现 | 简单场景分类 | 给出具体性能数据和最佳实践 |
| 思考维度 | 单一维度 | 线程安全、性能、场景三维分析 |
| 表达方式 | 机械背诵 | 有数据、有分析、有观点 |

---

## 1.2 Java 反射机制

### 动态获取类信息与运行时操作

#### 3、基础题：什么是反射？反射能做什么？

**难度**：⭐（反射定义、动态代理、框架原理）

**Answer**：

反射是 Java 在运行时动态获取类信息、操作类成员的能力。核心 API 包括：

- `Class.forName()`：获取 Class 对象

- `getDeclaredFields/Methods()`：获取字段/方法

- `setAccessible(true)`：绕过访问检查

- `newInstance()` / `Constructor.newInstance()`：创建对象

**应用场景**：

1. **框架底层**：Spring 的 IOC 容器、MyBatis 的 Mapper 映射都依赖反射

2. **动态代理**：JDK 动态代理通过反射调用目标方法

3. **通用工具**：如 BeanUtils、JSON 序列化等需要动态操作对象

4. **SPI 机制**：JDBC、Logger 等通过反射加载实现类

反射的缺点是性能开销较大，因为需要动态解析，但现代 JVM 优化后差距已缩小。

---

#### 4、进阶题：反射调用方法比普通调用慢多少？如何优化反射性能？

**难度**：⭐⭐⭐（性能基准、优化策略、生产实践）

1️⃣ **Common Answer**：

反射调用确实比普通调用慢，因为要动态解析。可以通过 setAccessible(true) 来优化，关闭访问检查会快一些。还可以用 MethodHandle 或者缓存 Method 对象来优化。

2️⃣ **Impressive Answer**：

我会从这几个角度分析：

1. **性能差距量化**：

  - 普通方法调用：约 5-10 纳秒

  - 反射调用（未优化）：约 100-200 纳秒，慢 10-20 倍

  - setAccessible(true) 后：约 30-50 纳秒，慢 3-5 倍

  - MethodHandle：约 15-25 纳秒，接近普通调用

2. **优化策略**：

  - **缓存反射对象**：Method、Field、Constructor 对象可以缓存，避免重复查找。Spring 的 ReflectUtils 就做了这层缓存。

  - **关闭访问检查**：setAccessible(true) 跳过权限验证，性能提升 2-3 倍。

  - **使用 MethodHandle**：JDK7 引入的 MethodHandle 性能更好，因为它可以被 JIT 内联优化。

  - **避免频繁反射**：在循环外获取 Method，循环内只调用 invoke。

3. **生产实践**：

  - Spring 的 CachedIntrospectionResults 缓存 BeanInfo

  - MyBatis 的 MetaObject 缓存类元信息

  - 框架初始化时预加载反射元数据，运行时只用缓存

4. **极端场景**：如果需要高频反射调用（如 RPC 框架），可以考虑字节码生成（CGLIB、ByteBuddy）或 MethodHandle。

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道优化方向 | 量化性能差距，理解 JVM 优化原理 |
| 实践体现 | 泛泛而谈 | 引用 Spring/MyBatis 源码实践 |
| 思考维度 | 单一优化点 | 缓存、访问检查、替代方案多维分析 |
| 表达方式 | 缺乏数据 | 有基准数据、有源码引用、有方案对比 |

---

## 1.3 泛型与类型擦除

### 泛型的本质与类型擦除的影响

#### 5、基础题：Java 泛型是类型擦除的，这意味着什么？

**难度**：⭐⭐（类型擦除、运行时限制、桥接方法）

**Answer**：

类型擦除指泛型信息只在编译期存在，运行时会被擦除。具体表现：

1. **擦除规则**：

  - `List<String>` 运行时变成 `List`，泛型参数被擦除

  - 无界泛型 `<T>` 擦除为 `Object`

  - 有界泛型 `<T extends Comparable>` 擦除为第一个边界 `Comparable`

2. **限制**：

  - 不能 `new T()` 或 `new T[]`，因为运行时不知道 T 是什么

  - 不能 `instanceof List<String>`，只能 `instanceof List`

  - 不能有 `method(List<String>)` 和 `method(List<Integer>)` 的重载

3. **桥接方法**：为保持多态，编译器会生成桥接方法。如子类 `class StringList extends ArrayList<String>` 重写 `get(int)` 时，编译器会保留原方法并生成桥接方法返回 String。

4. **获取泛型信息**：通过 `ParameterizedType` 可以在反射中获取部分泛型信息，如字段声明类型、方法参数类型。

---

## 1.4 枚举与注解

### 枚举的高级用法与注解的实际应用

#### 6、进阶题：枚举除了表示固定集合，还有什么高级用法？

**难度**：⭐⭐⭐（策略模式、单例、枚举常量类）

1️⃣ **Common Answer**：

枚举可以实现接口、有构造方法、可以有抽象方法。还可以用枚举实现单例模式，因为枚举单例天然防反射和序列化攻击。

2️⃣ **Impressive Answer**：

我会从这几个角度分析：

1. **策略模式实现**：

```java
enum Operator {
    ADD {
        public int execute(int a, int b) { return a + b; }
    },
    SUB {
        public int execute(int a, int b) { return a - b; }
    };
    public abstract int execute(int a, int b);
}
```

每个枚举常量可以有不同的实现，相当于一个轻量级的策略模式。

1. **单例模式**：

```java
enum Singleton { INSTANCE; }
```

枚举单例由 JVM 保证唯一性，天然防反射攻击和序列化破坏，是《Effective Java》推荐的单例写法。

1. **枚举 Set/Map**：

  - `EnumSet` 底层是位向量，性能远超 `HashSet`，内存占用极小

  - `EnumMap` 底层是数组，按枚举 ordinal 索引，查询 O(1)

  - 适合做状态机、权限标记等场景

2. **常量类模式**：

```java
enum Day {
    MONDAY("工作日", true),
    SATURDAY("周末", false);
    private final String desc;
    private final boolean isWeekend;
}
```

可以为枚举常量附加属性和行为，比纯常量更灵活。

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道基本用法 | 理解策略模式、单例、性能优化 |
| 实践体现 | 简单举例 | 给出代码示例和具体场景 |
| 思考维度 | 单一用法 | 策略、单例、集合、常量多维分析 |
| 表达方式 | 缺乏代码 | 有代码、有场景、有最佳实践引用 |

---

#### 7、基础题：注解的三种 RetentionPolicy 有什么区别？

**难度**：⭐（保留策略、运行时注解、编译时处理）

**Answer**：

RetentionPolicy 决定注解的生命周期：

1. **SOURCE**：只存在于源码，编译后丢弃。如 `@Override`，编译器用完后不需要保留。

2. **CLASS**：存在于 class 文件，但运行时不可见。用于字节码处理工具（如 ASM、ByteBuddy）。

3. **RUNTIME**：存在于 class 文件且运行时可见，可通过反射获取。Spring 的 `@Autowired`、`@Component` 都是 RUNTIME。

**选择建议**：

- 编译期检查：用 SOURCE

- 字节码增强/插桩：用 CLASS

- 运行时依赖（如 IOC 容器扫描）：必须用 RUNTIME

---

## 1.5 Java 模块化

### 模块化系统的理解与实践

#### 8、进阶题：Java 9 引入的模块化解决了什么问题？实际项目中如何使用？

**难度**：⭐⭐⭐（模块化优势、exports/uses 指令、迁移实践）

1️⃣ **Common Answer**：

Java 9 引入了模块系统，可以用 module-info.java 声明模块依赖。主要是为了解决类路径问题，实现更好的封装。可以用 exports 导出包，requires 声明依赖。但实际项目中用得不多，因为迁移成本高。

2️⃣ **Impressive Answer**：

我会从这几个角度分析：

1. **解决的核心问题**：

  - **类路径地狱**：传统 classpath 下，依赖冲突无法在编译期发现，模块系统可以在编译期检查依赖完整性。

  - **封装性不足**：public 类对所有类可见，模块系统可以用 exports 精确控制哪些包对外暴露。

  - **启动优化**：模块系统支持惰性加载，只加载需要的模块，减少启动时间（虽然效果有限）。

2. **核心指令**：

  - `exports com.example.api`：只导出 api 包，其他包对外不可见

  - `requires java.sql`：声明对 java.sql 模块的依赖

  - `opens com.example.impl`：开放包供反射使用（如 Spring 的依赖注入）

  - `uses com.example.Service` / `provides ... with`：SPI 服务发现机制

3. **实践挑战**：

  - **反射冲突**：框架依赖反射，但模块默认禁止跨模块反射。需要 opens 或--illegal-access。

  - **依赖迁移成本**：大型项目迁移需要大量适配，很多第三方库没有模块化。

  - **Maven/Gradle 支持**：构建工具对模块化的支持仍在完善中。

4. **实际建议**：

  - 新项目可以考虑模块化，特别是需要强封装的场景

  - 老项目可以先用自动模块名过渡，逐步迁移

  - Spring 6 开始支持模块化，但实际使用中大多仍用 classpath

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道基本概念 | 理解设计动机和核心问题 |
| 实践体现 | 简单指令介绍 | 分析反射冲突、迁移成本等实际问题 |
| 思考维度 | 单一功能描述 | 问题、方案、挑战、建议四维分析 |
| 表达方式 | 缺乏场景 | 有场景分析、有最佳实践建议 |

---

## 1.6 Record 类与密封类

### 现代 Java 的数据建模与类型约束

#### 9、基础题：Record 类是什么？它解决了什么问题？

**难度**：⭐（数据载体、不可变性、样板代码消除）

**Answer**：

Record 是 JDK 16 正式引入的一种特殊类，专门用于承载不可变数据，解决了 Java 中 POJO/DTO 样板代码过多的问题。

1. **核心特性**：

  - 自动生成 `equals()`、`hashCode()`、`toString()`、全参构造器和 getter

  - 字段默认 `private final`，天然不可变

  - 不能继承其他类（隐式继承 `java.lang.Record`），但可以实现接口

2. **语法示例**：

```java
record Point(int x, int y) {}
// 等价于一个有 x、y 字段的不可变类，自带所有样板方法
```

1. **适用场景**：

  - DTO/VO 数据传输对象

  - 方法多返回值封装

  - Map 的复合 Key

  - 与 Pattern Matching 配合做数据解构

2. **限制**：

  - 不能声明实例字段（只能用组件声明）

  - 不能是 abstract 的

  - 可以自定义紧凑构造器做参数校验

---

#### 10、进阶题：Sealed Classes 密封类解决了什么问题？和 final、abstract 有什么区别？

**难度**：⭐⭐（类型层次约束、模式匹配、代数数据类型）

1️⃣ **Common Answer**：

密封类是 JDK 17 引入的，用 sealed 关键字修饰，可以限制哪些类能继承它。子类必须用 final、sealed 或 non-sealed 修饰。和 final 的区别是 final 完全不能继承，sealed 可以指定谁能继承。

2️⃣ **Impressive Answer**：

我会从设计动机和实际价值两个角度分析：

1. **解决的核心问题**：在 sealed 之前，Java 的类型层次要么完全开放（abstract），要么完全封闭（final），没有中间态。密封类提供了**受控继承**——明确声明"只有这几个子类"。

2. **语法机制**：

```java
sealed interface Shape permits Circle, Rectangle, Triangle {}
record Circle(double radius) implements Shape {}
record Rectangle(double w, double h) implements Shape {}
final class Triangle implements Shape { /*...*/ }
```

- `permits` 子句显式列出允许的子类

- 子类必须是 `final`、`sealed` 或 `non-sealed`

1. **与 final/abstract 的对比**：

| 修饰符 | 继承策略 | 适用场景 |
| --- | --- | --- |
| abstract | 完全开放，任何人可继承 | 框架扩展点、SPI |
| final | 完全封闭，禁止继承 | 工具类、不可变类 |
| sealed | 受控开放，白名单继承 | 领域模型、状态机、AST 节点 |

1. **核心价值——与 Pattern Matching 联动**：密封类的真正威力在于编译器知道所有子类，因此 switch 表达式可以做**穷举检查**，不需要 default 分支：

```java
double area(Shape shape) {
    return switch (shape) {
        case Circle c    -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.w() * r.h();
        case Triangle t  -> calculateTriangleArea(t);
    }; // 编译器确认已穷举，无需 default
}
```

1. **实际应用**：JDK 自身已大量使用，如 `java.lang.constant.ConstantDesc` 就是密封接口。在业务中适合建模有限状态（订单状态、审批流节点）和 AST 节点。

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 只知道语法限制 | 理解代数数据类型和穷举检查 |
| 实践体现 | 缺乏应用场景 | 给出领域建模和 JDK 源码实例 |
| 思考维度 | 单一语法对比 | 设计动机、语法、联动、应用四维分析 |
| 表达方式 | 机械背诵 | 有代码、有对比表、有工程判断 |

---

## 1.7 Pattern Matching 模式匹配

### 从 instanceof 到 switch 的类型安全革命

#### 11、基础题：Pattern Matching for instanceof 是什么？比传统写法好在哪？

**难度**：⭐（类型检查、变量绑定、代码简化）

**Answer**：

Pattern Matching for instanceof（JDK 16 正式）让类型检查和类型转换合并为一步，消除了冗余的强制转换。

1. **传统写法 vs 新写法**：

```java
// 传统：检查 + 强转，重复且易错
if (obj instanceof String) {
    String s = (String) obj;
    System.out.println(s.length());
}

// Pattern Matching：一步到位
if (obj instanceof String s) {
    System.out.println(s.length());
}
```

1. **作用域规则**：模式变量的作用域由编译器的流分析决定，只在"确定匹配"的分支内可用：

```java
// 可以在 && 后使用，因为短路保证了匹配
if (obj instanceof String s && s.length() > 5) { ... }
// 不能在 || 后使用，因为不保证匹配
// if (obj instanceof String s || s.length() > 5) { } // 编译错误
```

1. **优势**：减少样板代码、消除手动强转的 ClassCastException 风险、提升可读性。

---

#### 12、进阶题：JDK 21 的 Pattern Matching for switch 有哪些能力？为什么说它是 Java 类型系统的重大升级？

**难度**：⭐⭐⭐（switch 模式匹配、守卫模式、穷举检查、解构模式）

1️⃣ **Common Answer**：

JDK 21 的 switch 支持模式匹配了，可以在 case 里直接写类型判断，不用一堆 if-else。还支持 null 的处理，比以前方便。

2️⃣ **Impressive Answer**：

我会从能力演进和实际价值两个角度分析：

1. **核心能力矩阵**：JDK 21 的 switch 模式匹配是多个 JEP 的集大成：

| 能力 | 示例 | 价值 |
| --- | --- | --- |
| 类型模式 | `case Integer i` | 替代 instanceof 链 |
| 守卫模式 | `case String s when s.length() > 5` | 条件细化，替代 if 嵌套 |
| null 处理 | `case null` | 不再需要前置 null 检查 |
| 记录解构 | `case Point(int x, int y)` | 直接提取 Record 组件 |
| 穷举检查 | sealed 类无需 default | 编译期保证完整性 |

1. **记录解构模式**（Record Pattern）——这是最强大的能力：

```java
sealed interface Expr permits Num, Add {}
record Num(int value) implements Expr {}
record Add(Expr left, Expr right) implements Expr {}

int eval(Expr expr) {
    return switch (expr) {
        case Num(int v)           -> v;
        case Add(Expr l, Expr r)  -> eval(l) + eval(r);
    };
}
```

支持嵌套解构，编译器自动穷举检查，写出来就像函数式语言的模式匹配。

1. **守卫模式（Guarded Pattern）**：

```java
String classify(Object obj) {
    return switch (obj) {
        case Integer i when i > 0  -> "正整数";
        case Integer i when i == 0 -> "零";
        case Integer i             -> "负整数";
        case String s              -> "字符串: " + s;
        case null                  -> "空值";
        default                    -> "其他类型";
    };
}
```

`when` 关键字替代了之前预览版的 `&&`，语义更清晰。

1. **为什么是重大升级**：

  - **类型安全**：编译器穷举检查，新增子类时强制处理，不会遗漏

  - **表达力**：Java 终于有了接近 Scala/Kotlin 的模式匹配能力

  - **与 Sealed + Record 形成铁三角**：Sealed 约束类型层次、Record 提供数据解构、Pattern Matching 提供分支逻辑，三者组合实现了 Java 版的代数数据类型（ADT）

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 只知道 switch 能匹配类型 | 理解解构模式、穷举检查、ADT 体系 |
| 实践体现 | 缺乏代码示例 | 给出 AST 求值器等实际建模案例 |
| 思考维度 | 语法糖层面 | 类型系统演进、与 Sealed/Record 联动 |
| 表达方式 | 一句话概括 | 能力矩阵 + 代码 + 设计哲学 |

---

## 1.8 Virtual Threads 虚拟线程

### Java 并发编程的范式转移

#### 13、基础题：什么是虚拟线程？它和平台线程有什么区别？

**难度**：⭐⭐（用户态线程、轻量级、调度模型）

1️⃣ **Common Answer**：

虚拟线程是 JDK 21 引入的轻量级线程，不需要和操作系统线程一一对应，可以创建很多个。比平台线程更轻量，适合高并发场景。

2️⃣ **Impressive Answer**：

我会从底层原理和工程价值两个角度分析：

1. **核心区别**：

| 维度 | 平台线程 | 虚拟线程 |
| --- | --- | --- |
| 映射关系 | 1:1 映射 OS 线程 | M:N 映射（多个虚拟线程共享少量载体线程） |
| 内存开销 | 约 1MB 栈空间 | 初始仅几百字节，按需增长 |
| 创建上限 | 通常数千个 | 轻松百万级 |
| 调度方式 | OS 内核调度 | JVM 用户态调度（ForkJoinPool） |
| 阻塞代价 | 阻塞 OS 线程，资源浪费 | 阻塞时自动 unmount，释放载体线程 |

1. **工作原理**：虚拟线程运行在**载体线程**（Carrier Thread）上。当虚拟线程执行阻塞操作（如 I/O、sleep、锁等待）时，JVM 会自动将其从载体线程上 **unmount**，载体线程去执行其他虚拟线程。阻塞结束后再 **mount** 回来继续执行。这就是 **continuation** 机制。

2. **创建方式**：

```java
// 方式一：直接创建
Thread.startVirtualThread(() -> {
    System.out.println("Hello from virtual thread");
});

// 方式二：使用 ExecutorService（推荐）
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 100_000).forEach(i ->
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1));
            return i;
        })
    );
}
```

1. **适用场景**：

  - **I/O 密集型**：HTTP 请求、数据库查询、文件读写——虚拟线程的主战场

  - **不适合 CPU 密集型**：计算密集任务不会阻塞，虚拟线程没有优势

  - **不适合持有重量级资源**：如数据库连接池，虚拟线程数远超连接数时需要信号量控制

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 只知道"轻量" | 理解 mount/unmount、continuation 机制 |
| 实践体现 | 缺乏量化对比 | 内存、数量、调度方式全维度对比 |
| 思考维度 | 单一优势描述 | 原理、创建方式、适用/不适用场景 |
| 表达方式 | 概念模糊 | 有对比表、有代码、有工程判断 |

---

#### 14、进阶题：虚拟线程有哪些陷阱？在生产中使用需要注意什么？

**难度**：⭐⭐⭐（Pinning 问题、ThreadLocal、连接池、最佳实践）

1️⃣ **Common Answer**：

虚拟线程虽然轻量，但也有一些问题。比如 synchronized 会导致线程固定，ThreadLocal 可能有内存问题。生产中要注意这些坑。

2️⃣ **Impressive Answer**：

我会从四个关键陷阱逐一分析：

1. **Pinning（线程固定）问题**：

  - 当虚拟线程执行 `synchronized` 代码块或 JNI 调用时，会被 **pin** 在载体线程上，阻塞时无法 unmount

  - 后果：载体线程被占用，其他虚拟线程无法调度，退化为平台线程模型

  - 解决方案：将 `synchronized` 替换为 `ReentrantLock`，因为 Lock API 支持虚拟线程的 unmount

```java
// 有 Pinning 风险
synchronized (lock) { blockingCall(); }

// 推荐写法
reentrantLock.lock();
try { blockingCall(); }
finally { reentrantLock.unlock(); }
```

1. **ThreadLocal 内存膨胀**：

  - 平台线程数有限，ThreadLocal 内存可控

  - 虚拟线程可达百万级，每个都持有 ThreadLocal 副本会导致内存爆炸

  - 解决方案：使用 JDK 21 的 **Scoped Values**（预览）替代 ThreadLocal，它是不可变的、生命周期受限的

2. **连接池饥饿**：

  - 虚拟线程数远超数据库连接池大小（如 100 万虚拟线程 vs 50 个连接）

  - 大量虚拟线程等待连接，可能导致超时雪崩

  - 解决方案：用 `Semaphore` 限制并发访问数，与连接池大小匹配

```java
Semaphore semaphore = new Semaphore(50);
semaphore.acquire();
try { dataSource.getConnection(); }
finally { semaphore.release(); }
```

1. **不要池化虚拟线程**：

  - 虚拟线程极其廉价，应该 **一个任务一个线程**（thread-per-task）

  - 不要用 `Executors.newFixedThreadPool()` 管理虚拟线程，这违背了设计初衷

  - 正确做法：`Executors.newVirtualThreadPerTaskExecutor()`

2. **生产检查清单**：

  - 用 `-Djdk.tracePinnedThreads=short` 检测 Pinning

  - 审计所有 `synchronized` 使用，评估是否需要迁移到 ReentrantLock

  - 审计 ThreadLocal 使用，评估迁移到 Scoped Values

  - 为共享资源（连接池、限流器）添加 Semaphore 保护

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道有坑但说不清 | 逐一分析 Pinning、ThreadLocal、连接池 |
| 实践体现 | 泛泛而谈 | 给出代码级解决方案和检测手段 |
| 思考维度 | 罗列问题 | 问题 + 原因 + 解决方案 + 检查清单 |
| 表达方式 | 缺乏深度 | 有代码、有 JVM 参数、有工程规范 |

---

## 1.9 Sequenced Collections 与其他新特性

### JDK 21 的集合增强与实用新特性

#### 15、基础题：Sequenced Collections 是什么？解决了什么痛点？

**难度**：⭐（有序集合接口、统一 API、首尾元素访问）

**Answer**：

Sequenced Collections（JDK 21）引入了三个新接口，解决了 Java 集合框架中**有序集合缺乏统一操作接口**的历史痛点。

1. **痛点回顾**：在 JDK 21 之前，获取不同有序集合的首尾元素方式五花八门：

| 集合类型 | 获取第一个元素 | 获取最后一个元素 |
| --- | --- | --- |
| List | `list.get(0)` | `list.get(list.size()-1)` |
| Deque | `deque.getFirst()` | `deque.getLast()` |
| SortedSet | `set.first()` | `set.last()` |
| LinkedHashSet | 只能迭代器... | 无直接方法 |

1. **新接口体系**：

  - `SequencedCollection`：有序集合，提供 `getFirst()`、`getLast()`、`addFirst()`、`addLast()`、`reversed()`

  - `SequencedSet`：有序去重集合

  - `SequencedMap`：有序映射，提供 `firstEntry()`、`lastEntry()`、`pollFirstEntry()`

2. **统一操作**：

```java
// 现在所有有序集合都可以这样操作
SequencedCollection<String> col = new ArrayList<>();
col.addFirst("first");
col.addLast("last");
String first = col.getFirst();
String last = col.getLast();
SequencedCollection<String> reversed = col.reversed(); // 反转视图
```

1. **reversed() 的妙用**：返回的是原集合的**反转视图**（不是拷贝），对视图的修改会反映到原集合，非常适合反向遍历。

---

#### 16、进阶题：JDK 21 到 JDK 23 还有哪些值得关注的语言层面新特性？

**难度**：⭐⭐（String Templates、Unnamed Patterns、Scoped Values、Structured Concurrency）

1️⃣ **Common Answer**：

JDK 21 之后还有一些新特性，比如字符串模板、未命名变量之类的。不过很多还是预览特性，生产中用得不多。

2️⃣ **Impressive Answer**：

我会按"已稳定"和"值得关注的预览"两个维度梳理：

1. **已稳定的特性**：

  - **Unnamed Patterns and Variables（JDK 22）**：用 `_` 表示不关心的变量，减少噪音：

```java
// 解构时忽略不需要的组件
if (obj instanceof Point(int x, _)) { use(x); }
// catch 中忽略异常变量
try { ... } catch (Exception _) { log("failed"); }
// 增强 for 中忽略元素
for (var _ : collection) { count++; }
```

- **Statements before super()（JDK 22）**：构造器中可以在 `super()` 之前执行语句，终于可以做参数校验了：

```java
class PositivePoint extends Point {
    PositivePoint(int x, int y) {
        if (x < 0 || y < 0) throw new IllegalArgumentException();
        super(x, y); // 之前这行必须是第一条语句
    }
}
```

1. **值得关注的预览/孵化特性**：

  - **Scoped Values**：替代 ThreadLocal 的新方案，不可变、生命周期受限、对虚拟线程友好：

```java
static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();
ScopedValue.runWhere(CURRENT_USER, user, () -> {
    // 在此作用域内可以读取 CURRENT_USER
    handleRequest();
});
```

- **Structured Concurrency**：结构化并发，将并发任务视为一个整体，子任务的生命周期不超过父任务：

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<String> user  = scope.fork(() -> fetchUser());
    Subtask<Integer> order = scope.fork(() -> fetchOrder());
    scope.join().throwIfFailed();
    return new Response(user.get(), order.get());
}
```

```plaintext
 任何子任务失败，自动取消其他子任务，避免线程泄漏。
```

- **String Templates（已移除，重新设计中）**：原本计划用 `STR."Hello \{name}"` 做字符串插值，但 JDK 23 中已撤回重新设计。目前仍需用 `String.format()` 或 `MessageFormat`。

1. **面试建议**：重点掌握 Virtual Threads、Record + Sealed + Pattern Matching 这个"铁三角"，这些是 JDK 21 LTS 的核心卖点。Scoped Values 和 Structured Concurrency 了解设计思想即可，它们代表了 Java 并发的未来方向。

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 只知道有新特性 | 区分稳定/预览，理解设计动机 |
| 实践体现 | 缺乏代码示例 | 每个特性都有代码和场景说明 |
| 思考维度 | 简单罗列 | 按稳定性分类 + 面试重点建议 |
| 表达方式 | 一句话带过 | 有代码、有对比、有学习路径建议 |

---

## 1.10 关联问题详解

### String 常量池与 intern 优化

#### 17、基础题：String 的 intern() 方法有什么用？

**难度**：⭐⭐（常量池、内存优化、引用比较）

**Answer**：

`intern()` 方法将字符串放入常量池并返回池中的引用，使得相同内容的字符串共享同一个对象。

1. **工作机制**：

  - 调用 `intern()` 时，JVM 检查常量池中是否已有 `equals()` 相等的字符串

  - 如果有，直接返回池中引用；如果没有，将当前字符串加入池中并返回

  - 字面量字符串（如 `"hello"`）编译时自动进入常量池

2. **典型场景**：

```java
String s1 = new String("hello");  // 堆上新对象
String s2 = s1.intern();          // 返回常量池引用
String s3 = "hello";              // 常量池引用
System.out.println(s2 == s3);     // true，同一个常量池对象
System.out.println(s1 == s3);     // false，s1 在堆上
```

1. **适用场景**：

  - 大量重复字符串的去重（如 XML 解析、日志字段）

  - 需要用 `==` 替代 `equals()` 提升比较性能的场景

2. **注意事项**：

  - JDK 7+ 常量池从永久代移到堆中，`intern()` 不再容易导致 PermGen OOM

  - 但大量 `intern()` 仍会增加 GC 压力，常量池底层是 `StringTable`（哈希表），可通过 `-XX:StringTableSize` 调整桶数

  - 现代项目中更推荐用 `Map` 手动去重，控制力更强

---

### 泛型的运行时类型获取

#### 18、进阶题：泛型如何绕过类型擦除获取实际类型？

**难度**：⭐⭐⭐（TypeReference、ParameterizedType、超类型令牌）

1️⃣ **Common Answer**：

可以通过反射获取泛型信息，比如用 `getGenericSuperclass()` 获取父类的泛型参数。Jackson 的 `TypeReference` 就是这么做的，创建一个匿名子类来保留泛型信息。

2️⃣ **Impressive Answer**：

我会从三个角度分析：

1. **为什么能获取**：虽然运行时泛型参数被擦除，但**类定义上的泛型信息**会保留在 Class 文件的 `Signature` 属性中。具体来说，以下位置的泛型信息不会被擦除：

  - 类/接口声明的泛型参数（`class Foo extends Bar<String>`）

  - 字段声明的泛型类型（`List<String> names`）

  - 方法签名的泛型参数和返回值

2. **超类型令牌（Super Type Token）模式**：

```java
// 核心原理：匿名子类会保留父类的泛型参数
abstract class TypeReference<T> {
    Type getType() {
        // 获取当前类的带泛型的父类信息
        ParameterizedType superClass = (ParameterizedType)
            getClass().getGenericSuperclass();
        return superClass.getActualTypeArguments()[0];
    }
}

// 使用：创建匿名子类，泛型信息被编译到 class 文件中
TypeReference<List<String>> ref = new TypeReference<List<String>>() {};
Type type = ref.getType(); // java.util.List<java.lang.String>
```

1. **框架中的实际应用**：

  - **Jackson**：`new TypeReference<Map<String, List<User>>>() {}` 反序列化复杂泛型

  - **Gson**：`new TypeToken<List<User>>() {}.getType()` 同样原理

  - **Spring**：`ParameterizedTypeReference` 用于 RestTemplate 的泛型响应解析

  - **MyBatis**：`TypeHandler` 通过反射获取泛型参数确定类型映射

2. **局限性**：

  - 只能获取**编译期确定**的泛型信息，运行时动态创建的泛型无法获取

  - `new ArrayList<String>()` 的泛型信息无法获取，因为没有子类化

  - 必须通过子类化（匿名类）来"固化"泛型参数到 class 文件中

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道 TypeReference 用法 | 理解 Signature 属性和擦除边界 |
| 实践体现 | 只提 Jackson | 横跨 Jackson/Gson/Spring/MyBatis |
| 思考维度 | 单一方案 | 原理、实现、应用、局限四维分析 |
| 表达方式 | 缺乏原理解释 | 有源码级实现和框架引用 |

---

### 注解处理器的编译期魔法

#### 19、进阶题：注解处理器（APT）如何使用？

**难度**：⭐⭐⭐（编译期处理、代码生成、AbstractProcessor）

1️⃣ **Common Answer**：

APT 是注解处理工具，可以在编译期扫描注解并生成代码。需要继承 `AbstractProcessor`，重写 `process` 方法。Lombok 就是用 APT 实现的，在编译期生成 getter/setter。

2️⃣ **Impressive Answer**：

我会从三个角度分析：

1. **核心机制**：APT（Annotation Processing Tool）在 **javac 编译期**运行，分多轮处理：

  - 编译器扫描源码中的注解

  - 调用对应的 `Processor.process()` 方法

  - 如果处理器生成了新的源文件，触发新一轮处理

  - 直到没有新文件生成为止

2. **实现步骤**：

```java
@SupportedAnnotationTypes("com.example.AutoValue")
@SupportedSourceVersion(SourceVersion.RELEASE_17)
public class AutoValueProcessor extends AbstractProcessor {

    @Override
    public boolean process(Set<? extends TypeElement> annotations,
                           RoundEnvironment roundEnv) {
        for (Element element : roundEnv.getElementsAnnotatedWith(AutoValue.class)) {
            TypeElement typeElement = (TypeElement) element;
            // 使用 JavaPoet 或 Filer 生成新的 Java 源文件
            generateValueClass(typeElement);
        }
        return true; // true 表示该注解已被处理，不传递给后续处理器
    }

    private void generateValueClass(TypeElement element) {
        // 通过 processingEnv.getFiler().createSourceFile() 生成代码
    }
}
```

还需要在 `META-INF/services/javax.annotation.processing.Processor` 中注册处理器。

1. **两种流派**：

  - **标准 APT（代码生成）**：只能生成新文件，不能修改已有源码。如 Google AutoValue、Dagger、MapStruct

  - **Lombok 流派（AST 修改）**：通过 `javac` 内部 API 直接修改抽象语法树（AST），属于 hack 行为，不是标准用法，但效果强大

2. **实际应用**：

  - **MapStruct**：编译期生成对象映射代码，零反射开销

  - **Dagger**：编译期生成依赖注入代码，替代运行时反射

  - **AutoValue/Immutables**：生成不可变值对象

  - **JMH**：生成基准测试的 harness 代码

3. **与运行时注解的对比**：

| 维度 | 编译期 APT | 运行时反射 |
| --- | --- | --- |
| 执行时机 | 编译期 | 运行时 |
| 性能影响 | 零运行时开销 | 反射有性能损耗 |
| 错误发现 | 编译期报错 | 运行时才暴露 |
| 灵活性 | 只能生成代码 | 可以动态操作 |

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道继承 AbstractProcessor | 理解多轮处理机制和两种流派 |
| 实践体现 | 只提 Lombok | 横跨 MapStruct/Dagger/AutoValue |
| 思考维度 | 单一实现描述 | 机制、实现、流派、对比多维分析 |
| 表达方式 | 缺乏代码 | 有完整代码骨架和对比表 |

---

### 反射替代方案的性能对比

#### 20、进阶题：反射和 MethodHandle 性能差距多大？

**难度**：⭐⭐⭐（调用点优化、JIT 内联、LambdaMetafactory）

1️⃣ **Common Answer**：

MethodHandle 比反射快，因为它可以被 JIT 优化。反射每次调用都要做安全检查，MethodHandle 在查找时就做了检查，调用时更快。

2️⃣ **Impressive Answer**：

我会从三个角度分析：

1. **性能基准对比**（JMH 测试，JDK 17，单方法调用）：

| 调用方式 | 耗时（ns/op） | 相对倍数 |
| --- | --- | --- |
| 直接调用 | ~5 | 1x |
| MethodHandle（常量） | ~5-8 | ~1x |
| MethodHandle（非常量） | ~15-25 | ~3-5x |
| 反射（setAccessible） | ~30-50 | ~6-10x |
| 反射（未优化） | ~100-200 | ~20-40x |

1. **为什么 MethodHandle 更快**：

  - **JIT 内联**：当 MethodHandle 是 `static final` 常量时，JIT 可以将其内联，性能接近直接调用

  - **无运行时安全检查**：权限检查在 `lookup()` 阶段完成，`invoke()` 时不再检查

  - **多态内联缓存**：MethodHandle 的调用点可以被 JVM 的 `invokedynamic` 指令优化

2. **更进一步——LambdaMetafactory**：

```java
// 最快的反射替代方案：编译期生成函数式接口实现
MethodHandles.Lookup lookup = MethodHandles.lookup();
MethodHandle handle = lookup.findVirtual(String.class, "length",
    MethodType.methodType(int.class));

// 通过 LambdaMetafactory 生成 ToIntFunction<String> 实现
CallSite site = LambdaMetafactory.metafactory(lookup,
    "applyAsInt",
    MethodType.methodType(ToIntFunction.class),
    MethodType.methodType(int.class, Object.class),
    handle,
    MethodType.methodType(int.class, String.class));

ToIntFunction<String> lengthFunc = (ToIntFunction<String>) site.getTarget().invokeExact();
lengthFunc.applyAsInt("hello"); // 性能等同直接调用
```

Spring 6 的 `ReflectionUtils` 内部已经用这种方式优化了高频反射调用。

1. **选型建议**：

  - **一次性反射**（如框架初始化）：普通反射即可，差距可忽略

  - **高频调用**（如 RPC 序列化）：MethodHandle 或 LambdaMetafactory

  - **极致性能**（如 JSON 库）：字节码生成（CGLIB、ByteBuddy）

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道 MethodHandle 更快 | 量化性能差距，理解 JIT 内联原理 |
| 实践体现 | 缺乏数据 | JMH 基准数据 + Spring 6 源码引用 |
| 思考维度 | 单一对比 | 反射、MethodHandle、LambdaMetafactory 三级方案 |
| 表达方式 | 概念模糊 | 有数据、有代码、有选型建议 |

---

### 枚举序列化的隐藏陷阱

#### 21、基础题：枚举 ordinal() 有什么坑？

**难度**：⭐⭐（序列化风险、持久化、ordinal 依赖）

**Answer**：

`ordinal()` 返回枚举常量的声明顺序（从 0 开始），但它**不应该被用于持久化或序列化**，因为顺序会随代码变更而改变。

1. **核心风险**：

```java
enum Status { PENDING, APPROVED, REJECTED }
// ordinal: PENDING=0, APPROVED=1, REJECTED=2

// 如果后来在中间插入一个新状态：
enum Status { PENDING, REVIEWING, APPROVED, REJECTED }
// ordinal 全变了：REVIEWING=1, APPROVED=2, REJECTED=3
// 数据库里存的 1 原来是 APPROVED，现在变成了 REVIEWING！
```

1. **受影响的场景**：

  - 数据库存储枚举值（用 ordinal 做字段值）

  - 网络传输/序列化（用 ordinal 编码）

  - switch 语句中依赖 ordinal 的隐式行为

  - `EnumSet` 和 `EnumMap` 内部依赖 ordinal，但这是内部实现，不影响使用

2. **正确做法**：

  - **数据库存储**：使用 `name()` 或自定义的 code 字段，不要用 ordinal

  - **序列化**：JSON 序列化用字符串名称，Protobuf 用显式编号

  - **自定义编码**：为枚举添加显式的 code 属性

```java
enum Status {
    PENDING(1), APPROVED(2), REJECTED(3);
    private final int code;
    Status(int code) { this.code = code; }
    public int getCode() { return code; }
}
```

1. **《Effective Java》建议**：Item 37 明确指出"永远不要根据枚举的 ordinal 值派生与它关联的值"，应该用实例字段替代。

---

### Record 与 Lombok 的取舍

#### 22、进阶题：Record 能替代 Lombok 的 @Data 吗？

**难度**：⭐⭐⭐（不可变 vs 可变、框架兼容性、适用边界）

1️⃣ **Common Answer**：

Record 和 Lombok 的 @Data 都能减少样板代码，但 Record 是不可变的，@Data 是可变的。如果需要 setter 就用 @Data，不需要就用 Record。

2️⃣ **Impressive Answer**：

我会从四个角度分析：

1. **核心差异对比**：

| 维度 | Record | Lombok @Data |
| --- | --- | --- |
| 可变性 | 不可变（final 字段） | 可变（有 setter） |
| 继承 | 不能继承其他类 | 可以继承 |
| 自定义字段 | 只能有组件字段 | 任意字段 |
| 构建方式 | 全参构造器 + 紧凑构造器 | @Builder、@NoArgsConstructor 等 |
| 依赖 | JDK 原生，零依赖 | 需要 Lombok 依赖和 IDE 插件 |
| 框架支持 | JPA 实体不支持（需要无参构造器和 setter） | JPA 完全兼容 |

1. **Record 适合的场景**：

  - DTO/VO 数据传输：接口返回值、方法间传递数据

  - 不可变值对象：金额、坐标、配置项

  - Map 的复合 Key：天然实现了 equals/hashCode

  - 与 Pattern Matching 配合做数据解构

2. **Lombok @Data 仍然必要的场景**：

  - JPA/Hibernate 实体：需要无参构造器、setter、代理继承

  - 需要 Builder 模式的复杂对象

  - 需要继承层次的领域模型

  - 需要部分字段可变的场景

3. **工程建议**：

  - 新项目中，DTO/VO 优先用 Record，减少对 Lombok 的依赖

  - 持久层实体继续用 Lombok 或手写

  - 不要混用——同一层的数据类保持一致的风格

  - Record + Lombok @Builder 可以组合使用，但会增加复杂度，不推荐

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 只知道可变性区别 | 理解框架兼容性和继承限制 |
| 实践体现 | 简单二选一 | 按场景给出具体选型建议 |
| 思考维度 | 单一维度对比 | 特性、场景、兼容性、工程规范四维分析 |
| 表达方式 | 缺乏细节 | 有对比表、有场景分类、有工程建议 |

---

### 虚拟线程与响应式编程的并发模型之争

#### 23、进阶题：虚拟线程能替代 WebFlux 响应式编程吗？

**难度**：⭐⭐⭐⭐（同步阻塞 vs 异步非阻塞、编程模型、适用边界）

1️⃣ **Common Answer**：

虚拟线程和 WebFlux 都是解决高并发的方案。虚拟线程用同步写法，WebFlux 用响应式写法。虚拟线程更简单，以后可能会替代 WebFlux。

2️⃣ **Impressive Answer**：

我会从四个角度分析：

1. **编程模型对比**：

| 维度 | 虚拟线程 | WebFlux（响应式） |
| --- | --- | --- |
| 编程风格 | 同步阻塞（命令式） | 异步非阻塞（声明式） |
| 代码可读性 | 和传统代码一样直观 | Mono/Flux 链式调用，学习曲线陡峭 |
| 调试体验 | 正常的堆栈跟踪 | 堆栈信息碎片化，调试困难 |
| 背压支持 | 无原生背压 | Reactive Streams 原生背压 |
| 生态成熟度 | 新兴，部分库未适配 | 成熟，R2DBC、WebClient 等完善 |

1. **性能对比**：

  - **I/O 密集型**：两者吞吐量接近，虚拟线程略有优势（无 Reactor 调度开销）

  - **极端高并发**（百万连接）：WebFlux 的事件循环模型内存更可控，虚拟线程需要注意 Pinning 和资源管理

  - **CPU 密集型**：两者都不适合，应该用平台线程池

2. **虚拟线程不能完全替代的场景**：

  - **背压需求**：流式数据处理（如 Kafka 消费、SSE 推送）需要背压控制，虚拟线程没有原生支持

  - **复杂异步编排**：多个异步流的合并、转换、错误恢复，Reactor 的操作符更强大

  - **已有响应式生态**：如果项目已深度使用 R2DBC、Reactive Redis，迁移成本高

3. **工程建议**：

  - **新项目**：优先考虑虚拟线程 + Spring MVC，代码简单、团队上手快

  - **已有 WebFlux 项目**：不必迁移，继续维护

  - **流式处理场景**：WebFlux 仍是更好的选择

  - **混合使用**：Spring 6 支持在同一项目中混用 MVC（虚拟线程）和 WebFlux

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 只知道写法不同 | 理解背压、事件循环、调度模型差异 |
| 实践体现 | 简单判断"会替代" | 分场景分析，给出不能替代的边界 |
| 思考维度 | 单一对比 | 编程模型、性能、场景、工程建议四维分析 |
| 表达方式 | 缺乏深度 | 有对比表、有性能分析、有迁移建议 |

---

### 模式匹配对设计模式的冲击

#### 25、进阶题：Pattern Matching 和 Visitor 模式的关系？

**难度**：⭐⭐⭐（表达式问题、开放/封闭维度、替代边界）

1️⃣ **Common Answer**：

Pattern Matching 可以替代 Visitor 模式，因为 switch 模式匹配可以根据类型分发逻辑，不需要 accept/visit 那套双重分派了。

2️⃣ **Impressive Answer**：

我会从三个角度分析：

1. **Visitor 模式的本质**：Visitor 解决的是**在不修改类层次的前提下，添加新操作**的问题。它通过双重分派（accept + visit）实现类型安全的分发：

```java
// 传统 Visitor
interface ShapeVisitor<R> {
    R visitCircle(Circle c);
    R visitRectangle(Rectangle r);
}
interface Shape { <R> R accept(ShapeVisitor<R> visitor); }
```

1. **Pattern Matching 如何替代**：

```java
// Sealed + Record + Pattern Matching
sealed interface Shape permits Circle, Rectangle {}
record Circle(double radius) implements Shape {}
record Rectangle(double w, double h) implements Shape {}

// 直接用 switch 替代 Visitor
double area(Shape shape) {
    return switch (shape) {
        case Circle(var r)      -> Math.PI * r * r;
        case Rectangle(var w, var h) -> w * h;
    };
}
```

代码量减少 60%+，无需 accept/visit 样板代码，编译器穷举检查保证类型安全。

1. **经典的"表达式问题"（Expression Problem）**：

| 扩展维度 | Visitor 模式 | Pattern Matching |
| --- | --- | --- |
| 添加新操作 | ✅ 新增 Visitor 实现 | ✅ 新增 switch 方法 |
| 添加新类型 | ❌ 需修改所有 Visitor | ✅ sealed 穷举检查，编译器提醒 |
| 类型安全 | ✅ 编译期保证 | ✅ 编译期穷举检查 |
| 代码简洁度 | ❌ 大量样板代码 | ✅ 极其简洁 |

Pattern Matching + Sealed Classes 在**两个维度都有优势**，这是 Visitor 做不到的。

1. **仍需 Visitor 的场景**：

  - 类型层次不是 sealed 的（开放继承），无法穷举

  - 需要在不同编译单元独立扩展操作（如插件系统）

  - 遍历复杂树结构时，Visitor 的递归遍历逻辑更清晰

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道可以替代 | 理解表达式问题和双重分派原理 |
| 实践体现 | 缺乏对比 | 给出代码对比和扩展维度分析 |
| 思考维度 | 简单替代关系 | 替代边界 + 仍需 Visitor 的场景 |
| 表达方式 | 一句话概括 | 有代码、有表格、有设计哲学 |

---

### 结构化并发与 CompletableFuture 的范式差异

#### 26、进阶题：Structured Concurrency 和 CompletableFuture 的区别？

**难度**：⭐⭐⭐⭐（生命周期管理、错误传播、资源泄漏、并发范式）

1️⃣ **Common Answer**：

Structured Concurrency 是 JDK 21 的预览特性，把并发任务组织成一个整体，子任务的生命周期不超过父任务。CompletableFuture 是非结构化的，任务之间没有父子关系。

2️⃣ **Impressive Answer**：

我会从四个角度分析：

1. **核心理念差异**：

| 维度 | CompletableFuture | Structured Concurrency |
| --- | --- | --- |
| 并发模型 | 非结构化：任务独立，手动管理 | 结构化：子任务生命周期 ≤ 父任务 |
| 错误传播 | 需要手动 exceptionally/handle | 自动传播，任一失败可取消全部 |
| 资源泄漏 | 容易忘记取消未完成的 Future | 作用域结束自动清理 |
| 取消机制 | cancel() 不保证生效 | 自动级联取消 |
| 可观测性 | 线程转储看不到任务关系 | 线程转储可见父子层级 |

1. **代码对比——并发获取用户和订单**：

```java
// CompletableFuture：非结构化
CompletableFuture<User> userFuture = CompletableFuture.supplyAsync(() -> fetchUser());
CompletableFuture<Order> orderFuture = CompletableFuture.supplyAsync(() -> fetchOrder());
// 问题：如果 userFuture 异常，orderFuture 仍在运行，资源浪费
// 需要手动处理：userFuture.exceptionally(...) + orderFuture.cancel(true)

// Structured Concurrency：结构化
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> user = scope.fork(() -> fetchUser());
    Subtask<Order> order = scope.fork(() -> fetchOrder());
    scope.join().throwIfFailed();
    // 任一子任务失败 → 自动取消另一个 → 异常自动传播
    return new Response(user.get(), order.get());
}
// 离开 try-with-resources → 所有子任务保证结束
```

1. **Structured Concurrency 的三种策略**：

  - **ShutdownOnFailure**：任一子任务失败，取消其余所有（最常用）

  - **ShutdownOnSuccess**：任一子任务成功，取消其余所有（竞速模式）

  - **自定义 Policy**：继承 StructuredTaskScope 实现自定义策略

2. **为什么是范式升级**：

  - **类比**：就像 `try-with-resources` 解决了资源泄漏，Structured Concurrency 解决了**线程泄漏**

  - **可观测性**：JFR（Java Flight Recorder）和线程转储可以看到任务的父子层级关系，排查问题更容易

  - **与虚拟线程配合**：虚拟线程 + 结构化并发是 Java 并发的未来方向，用同步写法获得异步性能，用结构化管理获得安全保障

3. **现阶段建议**：

  - Structured Concurrency 仍是预览特性，生产慎用

  - 新项目可以先用虚拟线程 + CompletableFuture 过渡

  - 关注 JDK 后续版本的稳定化进展

3️⃣ **Key Differences**：

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 技术深度 | 知道生命周期区别 | 理解错误传播、资源泄漏、可观测性 |
| 实践体现 | 缺乏代码对比 | 给出完整的代码对比和三种策略 |
| 思考维度 | 单一概念对比 | 模型、代码、策略、范式、建议五维分析 |
| 表达方式 | 概念模糊 | 有代码、有类比、有演进路径 |
