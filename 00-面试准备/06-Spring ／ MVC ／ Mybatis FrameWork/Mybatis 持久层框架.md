## 动态 SQL 与缓存机制

### 1、基础题：MyBatis 的一级缓存和二级缓存有什么区别？

**难度级别**：⭐⭐（SqlSession 级别 vs Mapper 级别、缓存失效条件、多表查询脏读风险）

**1️⃣ Common Answer**

一级缓存是 SqlSession 级别的，默认开启，同一个 SqlSession 里查询相同数据会走缓存。二级缓存是 Mapper 级别的，需要配置开启，多个 SqlSession 可以共享缓存。一级缓存会在增删改操作后失效，二级缓存也是一样。

**2️⃣ Impressive Answer**

1. **一级缓存（SqlSession 级别）**：基于 `PerpetualCache` 实现，默认开启，缓存 key 是 Statement ID + 参数 + SQL。在同一个 SqlSession 内，相同查询直接返回缓存结果，避免重复查库。**失效条件**：执行 insert/update/delete、调用 `sqlSession.clearCache()`、SqlSession 关闭。

2. **二级缓存（Mapper 级别）**：基于 Mapper 的 namespace，需要在 XML 中配置 `<cache/>` 开启，多个 SqlSession 共享同一 Mapper 的缓存。**核心区别**：一级缓存只在 SqlSession 内有效，二级缓存跨 SqlSession 共享；二级缓存需要实体类实现 `Serializable`（缓存需要序列化对象）。

3. **多表查询脏读风险**：二级缓存是 namespace 级别的，多表关联查询时，A 表更新不会自动清除 B 表 Mapper 的缓存，导致脏读。**最佳实践**：多表关联查询时关闭二级缓存，或在关联的 Mapper 中配置 `<cache-ref namespace="..."/>` 共享缓存，保证一致性。

4. **Spring 整合后的行为**：Spring 整合 MyBatis 后，SqlSession 由 `SqlSessionTemplate` 管理，无事务时每次操作创建新 SqlSession，一级缓存形同虚设；**开启事务后**，整个事务共享同一 SqlSession，一级缓存才真正生效。二级缓存独立于事务，适合读多写少的场景。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了级别区别 | 级别→实现→失效条件→脏读风险→Spring 行为 |
| 技术深度 | 没提 PerpetualCache 和序列化 | 有底层实现类和配置细节 |
| 实践经验 | 没考虑多表查询脏读 | 有脏读风险和最佳实践 |
| 面试官印象 | 知道概念但肤浅 | 理解原理和工程实践 |

---

### 2、进阶题：MyBatis 的插件（Interceptor）机制是如何实现的？

**难度级别**：⭐⭐⭐（四大对象拦截、Plugin.wrap 动态代理、Invocation、实现分页插件原理）

**1️⃣ Common Answer**

MyBatis 插件就是实现 Interceptor 接口，然后用 @Intercepts 注解标注要拦截哪些方法。在 intercept 方法里可以做一些额外逻辑，然后调用 invocation.proceed() 继续执行。PageHelper 就是这么实现的。

**2️⃣ Impressive Answer**

1. **四大对象拦截点**：MyBatis 只允许拦截 `Executor`（执行）、`StatementHandler`（SQL 组装）、`ParameterHandler`（参数处理）、`ResultSetHandler`（结果映射）四类对象的特定方法，通过 `@Intercepts + @Signature` 精确声明拦截目标。

2. **Plugin.wrap 的代理机制**：`Plugin.wrap(target, interceptor)` 判断目标对象是否命中签名，是则用 JDK 动态代理包装，拦截对应方法；执行时进入 `intercept(Invocation)` 方法，调用 `invocation.proceed()` 放行原始逻辑。

3. **分页插件原理**：PageHelper 拦截 `StatementHandler.prepare()`，在 SQL 执行前改写 SQL，追加 `LIMIT ? OFFSET ?`，并拦截 `Executor.query()` 额外执行 COUNT SQL 获取总数。

4. **多插件执行顺序**：多个插件形成责任链，执行顺序与注册顺序相反（类似栈）；设计插件要注意幂等性，避免 SQL 被重复改写。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了接口实现步骤，没有原理 | 四大对象→代理机制→分页原理→顺序问题 |
| 技术深度 | 不知道 Plugin.wrap 内部逻辑 | 清楚动态代理包装和签名匹配的原理 |
| 实践经验 | 只知道 PageHelper 能用，不知道原理 | 能解释 PageHelper 改写 SQL 的具体机制 |
| 面试官印象 | 用过插件但不理解扩展点设计 | 理解 MyBatis 插件链设计，能自己写插件 |

---

### 3、场景题：Agent 需要根据运行时条件动态拼接查询 SQL，MyBatis 如何安全实现？

**难度级别**：⭐⭐⭐（\<if\>/\<foreach\>、\#\{\} vs \$\{\}、SQL 注入防护、参数类型映射）

**1️⃣ Common Answer**

可以用 MyBatis 的动态 SQL，比如 `<if test="xxx != null">` 来判断条件，然后拼接不同的 SQL 片段。如果有列表就用 `<foreach>`。注意不要直接拼字符串，会有 SQL 注入风险。

**2️⃣ Impressive Answer**

1. **#{} vs ${} 是安全红线**：`#{}` 是预编译参数占位符，MyBatis 会转成 PreparedStatement 的 `?`，完全防注入；`${}` 是字符串替换，直接拼入 SQL，**只能用于表名/列名等结构性参数**，绝不能用于用户输入值。

2. **动态标签安全构建**：用 `<if>`、`<choose>`、`<where>`、`<set>`、`<foreach>` 组合动态条件；`<where>` 自动去掉多余的 AND/OR，`<set>` 自动去掉末尾逗号，比手动拼 SQL 更安全稳健。

3. **Agent 场景特殊处理**：Agent 可能传入动态字段名（如按哪个字段排序），字段名必须走白名单校验后再用 `${}`，绝不能直接透传 LLM 生成的字段名；参数值统一走 `#{}` 预编译。

4. **类型处理器兜底**：用 `@Param` 明确参数名，避免多参数时 MyBatis 找不到映射；复杂对象用 `typeHandler` 处理 JSON 字段存储。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 知道有动态 SQL 标签，但说不清楚 | #{} 安全边界→动态标签→Agent 白名单→类型处理 |
| 技术深度 | 不清楚 #{} 和 ${} 的底层差异 | 能说出预编译 vs 字符串替换的本质区别 |
| 实践经验 | 没有考虑 Agent 传入字段名的风险 | 明确提出白名单校验 LLM 生成的字段名 |
| 面试官印象 | 会用但有安全盲区 | 有安全意识，能识别 Agent 场景下的特殊风险 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 的 TypeHandler 如何自定义？ | 处理 Agent 场景下 JSON 字段、枚举等特殊类型映射的能力 |
| MyBatis 一级缓存和事务的关系是什么？ | 动态 SQL 执行后缓存失效策略，考察对缓存生命周期的理解 |
| MyBatis-Plus 的条件构造器和手写 XML 动态 SQL 怎么选型？ | 工程实践中两种动态 SQL 方案的取舍，考察框架使用经验 |

---

### 5、进阶题：MyBatis 的 Mapper 接口没有实现类，为什么能直接调用？底层原理是什么？

**难度级别**：⭐⭐⭐（MapperProxy 动态代理、MapperRegistry、SqlSession 绑定）

**1️⃣ Common Answer**

MyBatis 用了动态代理，Mapper 接口在运行时会生成代理对象。调用接口方法时，代理对象会根据方法名找到对应的 XML 里的 SQL 去执行。Spring 整合后通过 @MapperScan 扫描接口自动注册。

**2️⃣ Impressive Answer**

1. **MapperProxy 动态代理**：MyBatis 启动时，`MapperRegistry` 为每个 Mapper 接口创建 `MapperProxyFactory`；获取 Mapper 时，工厂用 JDK 动态代理生成 `MapperProxy` 实例，所有方法调用都被 `MapperProxy.invoke()` 拦截。

2. **方法到 SQL 的映射**：`invoke()` 内部根据接口全限定名 + 方法名（如 `com.example.UserMapper.selectById`）从 `Configuration` 中查找对应的 `MappedStatement`，获取 SQL、参数映射、结果映射等元数据。

3. **SqlSession 执行**：最终委托给 `SqlSession.selectOne/selectList/insert/update/delete` 执行，SqlSession 再通过 `Executor → StatementHandler → JDBC` 完成数据库操作。

4. **Spring 整合关键**：`@MapperScan` 通过 `MapperScannerConfigurer`（一个 BeanDefinitionRegistryPostProcessor）扫描接口，将每个 Mapper 注册为 `MapperFactoryBean` 类型的 BeanDefinition；`MapperFactoryBean.getObject()` 调用 `sqlSession.getMapper()` 返回代理对象。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了"动态代理" | MapperProxy→MappedStatement→SqlSession→Spring 整合，全链路 |
| 技术深度 | 不知道 MapperProxy 的具体实现 | 能说出 invoke() 如何定位到 MappedStatement |
| 实践经验 | 不清楚 Spring 整合的原理 | 知道 MapperScannerConfigurer 和 MapperFactoryBean 的角色 |
| 面试官印象 | 知道用了代理 | 理解 MyBatis 和 Spring 整合的完整机制 |

---

### 6、场景题：Agent 的对话记录需要存储到 MySQL，消息体是变长 JSON，如何用 MyBatis 优雅处理？

**难度级别**：⭐⭐⭐（TypeHandler 自定义、JSON 字段映射、大字段存储策略）

**1️⃣ Common Answer**

可以把 JSON 存成 TEXT 或 LONGTEXT 类型的字段，然后在 Java 里用 String 接收，需要的时候用 Jackson 手动序列化和反序列化。或者用 MyBatis-Plus 的 @TableField(typeHandler = JacksonTypeHandler.class) 注解。

**2️⃣ Impressive Answer**

1. 自定义 TypeHandler：

```java
@MappedTypes(ChatMessage.class)
@MappedJdbcTypes(JdbcType.VARCHAR)
public class ChatMessageTypeHandler extends BaseTypeHandler<ChatMessage> {
  private static final ObjectMapper MAPPER = new ObjectMapper();
  
  @Override
  public void setNonNullParameter(PreparedStatement ps, int i,ChatMessage param, JdbcType jdbcType) throws SQLException {
    ps.setString(i, MAPPER.writeValueAsString(param));
  }
  
  @Override
  public ChatMessage getNullableResult(ResultSet rs, String col) throws SQLException {
      String json = rs.getString(col);
      return json == null ? null : MAPPER.readValue(json, ChatMessage.class);
  }
}
```

1. **XML 中声明使用**：`<result column="message_body" property="messageBody" typeHandler="com.xxx.ChatMessageTypeHandler"/>`，读写自动转换，业务代码无感知。

2. **大字段存储策略**：消息体小于 4KB 用 `VARCHAR`，大于 4KB 用 `TEXT`/`MEDIUMTEXT`；超大对话记录（如带图片 base64）考虑存 OSS，DB 只存引用 URL，避免单行过大影响查询性能。

3. **Agent 场景优化**：对话记录按 `session_id` 分表，避免单表过大；历史消息用**归档策略**（30 天前的移到冷存储），保持热表轻量。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 String 存储 | TypeHandler→XML 声明→存储策略→分表归档 |
| 技术深度 | 不知道自定义 TypeHandler | 有完整的 TypeHandler 实现代码 |
| 实践经验 | 没考虑大字段性能问题 | 有分级存储策略和 OSS 方案 |
| 面试官印象 | 能存但不优雅 | 有工程化思维，考虑性能和可维护性 |

---

## 一级缓存与二级缓存

### 1、基础题：MyBatis 的一级缓存和二级缓存有什么区别？

**难度级别**：⭐⭐（缓存级别、失效条件、脏读风险）

**1️⃣ Common Answer**
一级缓存是 SqlSession 级别的，默认开启，同一个 SqlSession 里查询相同数据会走缓存。二级缓存是 Mapper 级别的，需要配置开启，多个 SqlSession 可以共享缓存。一级缓存会在增删改操作后失效，二级缓存也是一样。

**2️⃣ Impressive Answer**

1. **一级缓存（SqlSession 级别）**：基于 PerpetualCache 实现，默认开启，缓存 key 是 Statement ID + 参数 + SQL。在同一个 SqlSession 内，相同查询直接返回缓存结果，避免重复查询数据库。**失效条件**：执行 insert/update/delete、调用 sqlSession.clearCache()、SqlSession 关闭。

2. **二级缓存（Mapper 级别）**：基于 Mapper 的 namespace，需要配置 `<cache/>` 开启，多个 SqlSession 共享同一 Mapper 的缓存。**核心区别**：一级缓存只在 SqlSession 内有效，二级缓存跨 SqlSession 共享；二级缓存需要序列化对象（要求实体类实现 Serializable）。

3. **多表查询脏读风险**：一级缓存可能脏读（多表关联时，只查询主表可能返回缓存的旧数据），二级缓存通过 `flushCache` 配置避免。**最佳实践**：多表关联查询时关闭二级缓存或设置 `flushCache="true"`，避免脏数据。

4. **Spring 整合后的行为**：Spring 整合 MyBatis 后，SqlSession 由 Spring 管理，一级缓存在事务内有效，事务提交后 SqlSession 关闭，一级缓存清空。二级缓存独立于事务，适合读多写少的场景。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了级别区别 | 级别→实现→失效条件→脏读风险→Spring 行为 |
| 技术深度 | 没提 PerpetualCache 和序列化 | 有底层实现类和配置细节 |
| 实践经验 | 没考虑多表查询脏读 | 有脏读风险和最佳实践 |
| 面试官印象 | 知道概念但肤浅 | 理解原理和工程实践 |

---

### 2、进阶题：MyBatis 一级缓存在 Spring 事务中的行为是什么？为什么开启事务后缓存命中率更高？

**难度级别**：⭐⭐⭐（事务管理、缓存共享、命中机制）

**1️⃣ Common Answer**
Spring 事务中，SqlSession 是共享的，所以一级缓存在事务内有效。开启事务后，多次查询会走缓存，命中率更高。事务提交后 SqlSession 关闭，缓存清空。

**2️⃣ Impressive Answer**

1. **Spring 整合后的 SqlSession 管理**：Spring 使用 `SqlSessionTemplate` 代理 SqlSession，默认每次操作创建新 SqlSession。但在**事务内**，Spring 通过 `SqlSessionHolder` 绑定当前 SqlSession 到 ThreadLocal，整个事务共享同一个 SqlSession，一级缓存生效。

2. **缓存命中率提升的原因**：无事务时，每次数据库操作都创建新 SqlSession，一级缓存无法跨操作共享；开启事务后，同一事务内的多次查询共享 SqlSession，相同查询直接命中一级缓存，避免重复查库。**性能提升**：高频查询场景（如 Agent 对话记录查询），事务内缓存命中率可达 90%+。

3. **事务提交后的缓存清理**：事务提交时，Spring 会调用 `SqlSessionUtils.closeSqlSession()` 清理 SqlSession，一级缓存自动清空，避免脏读。二级缓存独立于事务，事务提交后二级缓存仍然有效。

4. **Agent 场景实践**：Agent 查询对话记录时，在 `@Transactional` 方法内多次查询相同 Session，一级缓存生效，减少 DB 压力。但**注意**：事务内避免大对象查询（如加载全量历史消息），防止一级缓存占用过多内存。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了共享 SqlSession | SqlSessionTemplate→ThreadLocal→命中率→清理机制 |
| 技术深度 | 没提 SqlSessionHolder 和 ThreadLocal | 有 Spring 底层实现细节 |
| 实践经验 | 没考虑内存占用 | 有性能优化和内存管理建议 |
| 面试官印象 | 知道现象但不懂原理 | 理解 Spring 事务与缓存的协同机制 |

---

### 3、场景题：Agent 的知识库查询接口 QPS 很高，如何合理利用 MyBatis 缓存减少数据库压力？

**难度级别**：⭐⭐⭐（缓存策略、性能优化、Agent 场景）

**1️⃣ Common Answer**
开启 MyBatis 的二级缓存，知识库查询走缓存，减少数据库压力。设置缓存过期时间，避免数据过期。用 Redis 做缓存，提高性能。

**2️⃣ Impressive Answer**

1. **二级缓存配置**：在知识库 Mapper XML 中配置 `<cache eviction="LRU" flushInterval="60000" size="1024"/>`，使用 LRU 淘汰策略，60 秒刷新，缓存 1024 个对象。**注意**：实体类实现 `Serializable`，二级缓存需要序列化。

2. **一级缓存 + 事务优化**：在高频查询接口（如 Agent 知识库检索）使用 `@Transactional(readOnly = true)`，同一事务内多次查询共享一级缓存，避免重复查库。**性能提升**：单次请求内多次查询相同知识库条目，一级缓存命中率可达 100%。

3. **缓存失效策略**：知识库更新时，调用 `sqlSession.clearCache()` 清空一级缓存；二级缓存通过 `flushCache="true"` 在 update/delete 时自动失效。**Agent 场景**：知识库更新频率低，二级缓存命中率高，QPS 1000+ 时 DB 压力可降低 80%。

4. **混合缓存方案**：热点知识库条目（如 FAQ）用二级缓存，冷数据用 Redis 分布式缓存；大对象（如向量数据）不缓存，避免内存溢出。**监控指标**：缓存命中率、缓存大小、DB QPS，通过 MyBatis 插件统计缓存效果。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了开启缓存 | 二级缓存配置→一级缓存+事务→失效策略→混合方案 |
| 技术深度 | 没提序列化和淘汰策略 | 有完整的缓存配置和监控方案 |
| 实践经验 | 没考虑 Agent 高 QPS 场景 | 有具体的性能优化和监控指标 |
| 面试官印象 | 知道缓存但不会用 | 有工程化缓存策略和性能优化经验 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 插件原理 | 插件可以拦截 Executor，用于统计缓存命中率 |
| Redis 分布式缓存 | 二级缓存是本地缓存，Redis 是分布式缓存，两者结合使用 |
| Spring 事务传播 | 事务传播行为影响一级缓存的共享范围 |
| 缓存一致性 | 多数据源场景下，缓存一致性如何保证 |

---

## SQL 执行全链路

### 1、基础题：MyBatis 中 SqlSession 的作用是什么？它和 SqlSessionFactory 的关系？

**难度级别**：⭐⭐（SqlSession 作用、工厂模式、生命周期）

**1️⃣ Common Answer**
SqlSession 是 MyBatis 的核心接口，用于执行 SQL、获取 Mapper、管理事务。SqlSessionFactory 是工厂，用来创建 SqlSession。SqlSessionFactory 是单例的，SqlSession 每次用完要关闭。

**2️⃣ Impressive Answer**

1. **SqlSession 的作用**：SqlSession 相当于 JDBC 的 Connection，封装了 Executor、StatementHandler、Transaction 等组件，提供 `selectList()`、`insert()`、`update()`、`delete()` 等方法执行 SQL，以及 `getMapper()` 获取 Mapper 代理对象，`commit()`/`rollback()` 管理事务。

2. **SqlSessionFactory 的职责**：SqlSessionFactory 是重量级对象，创建时加载配置文件（mybatis-config.xml）、Mapper XML，构建 Configuration 对象，内部维护 Executor、StatementHandler 等组件的工厂方法。**生命周期**：应用级别，全局单例，线程安全。

3. **关系与生命周期**：SqlSessionFactory 创建 SqlSession，SqlSession 是轻量级对象，非线程安全，每次请求创建新实例，用完必须关闭（`finally` 块中调用 `close()`）。**Spring 整合**：Spring 管理 SqlSessionFactory（单例），SqlSession 由 SqlSessionTemplate 代理，自动管理生命周期。

4. **底层实现**：SqlSession 默认实现是 `DefaultSqlSession`，内部持有 `Configuration`、`Executor`、`Transaction`；SqlSessionFactory 默认实现是 `DefaultSqlSessionFactory`，通过 `openSession()` 创建 SqlSession，可指定 Executor 类型（SIMPLE、REUSE、BATCH）。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了作用和关系 | 作用→工厂模式→生命周期→底层实现类 |
| 技术深度 | 没提 Executor 和事务管理 | 有完整的组件封装和 Spring 整合细节 |
| 实践经验 | 没考虑线程安全和资源管理 | 有生命周期管理和最佳实践 |
| 面试官印象 | 知道概念但肤浅 | 理解设计模式和工程实践 |

---

### 2、进阶题：MyBatis 的 SQL 执行流程是什么？从 sqlSession.selectList() 到 JDBC 的完整链路？

**难度级别**：⭐⭐⭐（执行链路、组件协作、JDBC 封装）

**1️⃣ Common Answer**
SqlSession 调用 selectList，然后 Executor 执行 SQL，StatementHandler 处理 JDBC，最后返回结果。中间还有 ParameterHandler 和 ResultSetHandler 处理参数和结果。

**2️⃣ Impressive Answer**

1. **SqlSession.selectList()**：调用 `Configuration.getMappedStatement()` 获取 MappedStatement（包含 SQL、参数映射、结果映射），然后调用 `executor.query()`。

2. **Executor.query()**：BaseExecutor 先查一级缓存（`localCache`），命中直接返回；未命中则调用 `doQuery()`。**二级缓存**：CachingExecutor 先查二级缓存，未命中再查一级缓存，最后查数据库。

3. **StatementHandler.prepare()**：创建 JDBC Statement（PreparedStatement），调用 `ParameterHandler.setParameters()` 设置参数（处理 `#{}` 占位符），然后 `StatementHandler.query()` 执行 SQL。

4. **ResultSetHandler.handleResultSets()**：处理 JDBC ResultSet，根据 ResultMap 映射结果对象，支持嵌套结果、延迟加载。**返回结果**：List<Object>，SqlSession 返回给调用方。

5. **完整链路**：SqlSession → Executor → StatementHandler → ParameterHandler → JDBC Statement → ResultSet → ResultSetHandler → Result Object。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了大致流程 | 完整链路：SqlSession→Executor→StatementHandler→JDBC→ResultSetHandler |
| 技术深度 | 没提缓存和参数处理 | 有一级缓存、二级缓存、参数映射、结果映射的完整流程 |
| 实践经验 | 没考虑性能和优化 | 有缓存机制和组件协作的底层理解 |
| 面试官印象 | 知道流程但不够深入 | 理解 MyBatis 执行链路的完整机制 |

---

### 3、场景题：Agent 服务出现慢 SQL，如何利用 MyBatis 执行链路快速定位问题？

**难度级别**：⭐⭐⭐（性能排查、插件拦截、Agent 场景）

**1️⃣ Common Answer**
开启 MyBatis 日志，看 SQL 执行时间。用数据库慢查询日志定位问题。优化 SQL，加索引。

**2️⃣ Impressive Answer**

1. **MyBatis 插件拦截**：实现 `Interceptor` 接口，拦截 `Executor.update()` 和 `Executor.query()`，记录 SQL 执行时间、参数、结果行数。**关键代码**：

```java
@Intercepts({@Signature(type = Executor.class, method = "query", args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class})})
public class SlowSqlInterceptor implements Interceptor {
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = invocation.proceed();
        long cost = System.currentTimeMillis() - start;
        if (cost > 1000) log.warn("Slow SQL: {}, cost: {}ms", invocation.getArgs()[0], cost);
        return result;
    }
}
```

1. **执行链路分析**：慢 SQL 可能出现在以下环节：

  - **Executor**：缓存未命中，重复查库 → 优化缓存策略

  - **StatementHandler**：参数设置慢（如大对象序列化）→ 优化参数传递

  - **JDBC**：SQL 本身慢（如全表扫描）→ 优化 SQL，加索引

  - **ResultSetHandler**：结果映射慢（如大量数据）→ 分页查询，减少数据量

2. **Agent 场景优化**：Agent 对话记录查询慢，通过插件定位到 `ResultSetHandler` 处理大量历史消息耗时，改用分页查询（`RowBounds` 或 `PageHelper`），单页 20 条，性能提升 80%。

3. **监控与告警**：集成 Prometheus，采集 SQL 执行时间、QPS、缓存命中率，设置慢 SQL 告警（>1s）。**最佳实践**：开发环境开启 SQL 日志（`logging.level.org.mybatis=DEBUG`），生产环境用插件监控。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了日志和索引 | 插件拦截→执行链路分析→Agent 场景优化→监控告警 |
| 技术深度 | 没提插件和执行链路 | 有完整的插件实现和性能排查方案 |
| 实践经验 | 没考虑 Agent 场景 | 有具体的优化案例和监控方案 |
| 面试官印象 | 知道慢 SQL 但不会排查 | 有系统化的性能排查和优化经验 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 插件原理 | 插件拦截执行链路，用于监控和优化 |
| JDBC 基础 | MyBatis 底层依赖 JDBC，理解 JDBC 有助于理解执行链路 |
| 慢 SQL 优化 | 执行链路分析是慢 SQL 优化的基础 |
| Spring 事务 | 事务管理影响 Executor 的行为和缓存策略 |

---

## 懒加载与 N+1 问题

### 1、基础题：什么是 MyBatis 的懒加载？如何开启？

**难度级别**：⭐⭐（懒加载概念、配置方式、延迟查询）

**1️⃣ Common Answer**
懒加载就是用到的时候才查询关联数据，不用的时候不查。在 mybatis-config.xml 里配置 lazyLoadingEnabled=true 开启。关联查询用 association 或 collection。

**2️⃣ Impressive Answer**

1. **懒加载概念**：懒加载（延迟加载）指在查询主对象时，不立即查询关联对象，而是在访问关联对象属性时才触发查询。**好处**：避免一次性加载大量数据，减少内存占用和数据库压力。

2. **配置方式**：在 `mybatis-config.xml` 中配置：

```xml
<settings>
    <setting name="lazyLoadingEnabled" value="true"/>
    <setting name="aggressiveLazyLoading" value="false"/>
</settings>
```

`lazyLoadingEnabled=true` 开启懒加载，`aggressiveLazyLoading=false` 关闭激进懒加载（只加载被调用的属性，而非所有属性）。

1. **关联查询配置**：在 Mapper XML 中使用 `association` 或 `collection`，设置 `fetchType="lazy"`：

```xml
<resultMap id="sessionResultMap" type="Session">
    <id property="id" column="id"/>
    <collection property="messages" ofType="Message" fetchType="lazy">
        <id property="id" column="msg_id"/>
    </collection>
</resultMap>
```

1. **底层实现**：懒加载通过 CGLIB 代理实现，代理对象拦截 `getMessages()` 方法，触发 SQL 查询。**注意**：懒加载要求 SqlSession 未关闭，否则报错；Spring 整合后需在事务内访问懒加载属性。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了概念和配置 | 概念→配置→关联查询→底层实现→注意事项 |
| 技术深度 | 没提 CGLIB 代理和 SqlSession 生命周期 | 有完整的代理实现和 Spring 整合细节 |
| 实践经验 | 没考虑懒加载的限制 | 有 SqlSession 生命周期和最佳实践 |
| 面试官印象 | 知道懒加载但不深入 | 理解原理和工程实践 |

---

### 2、进阶题：MyBatis 懒加载的底层实现原理是什么？

**难度级别**：⭐⭐⭐（CGLIB 代理、代理拦截、aggressiveLazyLoading）

**1️⃣ Common Answer**
懒加载用 CGLIB 生成代理对象，访问属性时触发查询。aggressiveLazyLoading 控制是否加载所有属性。

**2️⃣ Impressive Answer**

1. **CGLIB 代理生成**：MyBatis 使用 `ProxyFactory` 创建代理对象，默认用 CGLIB（`proxyFactory` 可配置为 JAVASSIST）。代理对象继承目标类，拦截 `getter` 方法，触发延迟查询。

2. **代理拦截逻辑**：代理对象内部持有 `ResultLoader`，拦截 `getMessages()` 方法时，调用 `ResultLoader.loadResult()` 执行 SQL 查询，填充属性值。**关键代码**：

```java
public class CglibProxyFactory implements ProxyFactory {
    @Override
    public Object createProxy(Object target, ResultLoaderMap lazyLoader) {
        Enhancer enhancer = new Enhancer();
        enhancer.setSuperclass(target.getClass());
        enhancer.setCallback(new LazyLoaderInterceptor(lazyLoader));
        return enhancer.create();
    }
}
```

1. **aggressiveLazyLoading 配置**：

  - `aggressiveLazyLoading=true`（默认）：调用任意 `getter` 方法时，加载所有懒加载属性（性能差，不推荐）。

  - `aggressiveLazyLoading=false`：只加载被调用的属性，其他懒加载属性保持未加载状态（推荐，性能好）。

2. **SqlSession 生命周期限制**：懒加载依赖 SqlSession，如果 SqlSession 已关闭，访问懒加载属性会报 `SqlSessionException`。**Spring 整合**：在 `@Transactional` 方法内访问懒加载属性，确保 SqlSession 未关闭；或在事务外使用 `fetchType="eager"` 预加载。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 CGLIB 代理 | CGLIB 代理→拦截逻辑→aggressiveLazyLoading→SqlSession 限制 |
| 技术深度 | 没提 ResultLoader 和拦截器 | 有完整的代理实现和配置细节 |
| 实践经验 | 没考虑 SqlSession 生命周期 | 有 Spring 整合和最佳实践 |
| 面试官印象 | 知道代理但不懂原理 | 理解懒加载的底层机制和工程实践 |

---

### 3、场景题：Agent 多轮对话中，每次查询 Session 都要关联查询所有 Message，出现了 N+1 问题，如何优化？

**难度级别**：⭐⭐⭐（N+1 问题、懒加载、批量查询、Agent 场景）

**1️⃣ Common Answer**
用懒加载，访问 Message 时再查。或者用 JOIN 查询，一次性查出所有数据。用 MyBatis 的 batch 查询。

**2️⃣ Impressive Answer**

1. **N+1 问题分析**：查询 10 个 Session，每个 Session 关联查询 100 条 Message，共执行 1 + 10 × 100 = 1001 次 SQL（1 次查 Session，1000 次查 Message），性能极差。**根本原因**：循环中逐个查询关联数据。

2. **优化方案 1：懒加载 + 批量查询**：

  - 开启懒加载（`lazyLoadingEnabled=true`），查询 Session 时不立即查询 Message。

  - 使用 `MyBatis-Plus` 的 `in` 查询批量加载 Message：

```java
List<Long> sessionIds = sessions.stream().map(Session::getId).collect(Collectors.toList());
List<Message> messages = messageMapper.selectList(new LambdaQueryWrapper<Message>().in(Message::getSessionId, sessionIds));
```

- 手动组装 Session 和 Message 的关联关系，减少 SQL 次数到 2 次（1 次查 Session，1 次批量查 Message）。

1. **优化方案 2：JOIN 查询**：

  - 在 Mapper XML 中使用 `collection` 嵌套查询，配置 `fetchType="eager"`：

```xml
<resultMap id="sessionWithMessagesMap" type="Session">
    <id property="id" column="id"/>
    <collection property="messages" ofType="Message" fetchType="eager">
        <id property="id" column="msg_id"/>
    </collection>
</resultMap>
<select id="selectSessionWithMessages" resultMap="sessionWithMessagesMap">
    SELECT s.*, m.id as msg_id FROM session s LEFT JOIN message m ON s.id = m.session_id WHERE s.id = #{id}
</select>
```

- 一次 SQL 查询出 Session 和所有 Message，避免 N+1 问题。

1. **Agent 场景最佳实践**：

  - **多轮对话查询**：用懒加载 + 批量查询，避免加载全量历史消息，只加载最近 20 条（分页）。

  - **知识库关联查询**：用 JOIN 查询，一次性加载知识库条目和关联标签。

  - **监控与优化**：通过 MyBatis 插件统计 SQL 次数，设置告警（单次请求 SQL > 10 次），持续优化。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了懒加载和 JOIN | N+1 分析→懒加载+批量查询→JOIN 查询→Agent 最佳实践 |
| 技术深度 | 没提批量查询和分页 | 有完整的优化方案和代码示例 |
| 实践经验 | 没考虑 Agent 场景 | 有具体的优化案例和监控方案 |
| 面试官印象 | 知道 N+1 但不会优化 | 有系统化的优化思路和工程实践 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 缓存 | 懒加载和缓存配合使用，减少数据库压力 |
| MyBatis-Plus 批量查询 | MyBatis-Plus 提供批量查询 API，优化 N+1 问题 |
| JOIN 查询优化 | JOIN 查询是 N+1 问题的另一种解决方案 |
| 分页查询 | 分页查询减少数据量，缓解 N+1 问题 |

---

## 多数据源与事务协同

### 1、基础题：MyBatis 如何配置多数据源？

**难度级别**：⭐⭐（多数据源配置、SqlSessionFactory 分离、Mapper 扫描）

**1️⃣ Common Answer**
配置多个 DataSource，每个 DataSource 对应一个 SqlSessionFactory。用 @Qualifier 指定使用哪个数据源。Mapper 分开扫描。

**2️⃣ Impressive Answer**

1. **多数据源配置**：在 Spring Boot 中配置多个 `DataSource`，分别创建 `SqlSessionFactory` 和 `SqlSessionTemplate`：

```java
@Configuration
public class DataSourceConfig {
    @Bean(name = "primaryDataSource")
    @Primary
    public DataSource primaryDataSource() {
        return DataSourceBuilder.create().url("jdbc:mysql://primary-db").build();
    }
       
    @Bean(name = "secondaryDataSource")
    public DataSource secondaryDataSource() {
        return DataSourceBuilder.create().url("jdbc:mysql://secondary-db").build();
    }
       
    @Bean(name = "primarySqlSessionFactory")
    @Primary
    public SqlSessionFactory primarySqlSessionFactory(@Qualifier("primaryDataSource") DataSource dataSource) throws Exception {
        SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
        factory.setDataSource(dataSource);
        factory.setMapperLocations(new PathMatchingResourcePatternResolver().getResources("classpath:mapper/primary/*.xml"));
        return factory.getObject();
    }
       
    @Bean(name = "secondarySqlSessionFactory")
    public SqlSessionFactory secondarySqlSessionFactory(@Qualifier("secondaryDataSource") DataSource dataSource) throws Exception {
        SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
        factory.setDataSource(dataSource);
        factory.setMapperLocations(new PathMatchingResourcePatternResolver().getResources("classpath:mapper/secondary/*.xml"));
        return factory.getObject();
    }
}
```

1. **Mapper 扫描分离**：使用 `@MapperScan` 分别扫描不同数据源的 Mapper：

```java
@MapperScan(basePackages = "com.example.primary.mapper", sqlSessionFactoryRef = "primarySqlSessionFactory")
public class PrimaryMapperConfig {}
   
@MapperScan(basePackages = "com.example.secondary.mapper", sqlSessionFactoryRef = "secondarySqlSessionFactory")
public class SecondaryMapperConfig {}
```

1. **使用方式**：在 Service 中注入对应的 Mapper，自动使用对应的数据源：

```java
@Service
public class AgentService {
    @Autowired
    private PrimaryUserMapper primaryUserMapper;
    @Autowired
    private SecondaryVectorMapper secondaryVectorMapper;
}
```

1. **动态数据源**：使用 `AbstractRoutingDataSource` 实现动态切换数据源（进阶题详细讲解）。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了配置多数据源 | 多数据源配置→SqlSessionFactory 分离→Mapper 扫描→动态数据源 |
| 技术深度 | 没提 Mapper 扫描和动态切换 | 有完整的配置方案和代码示例 |
| 实践经验 | 没考虑 Agent 场景 | 有具体的配置实践和最佳实践 |
| 面试官印象 | 知道多数据源但不会配置 | 有系统化的配置方案和工程实践 |

---

### 2、进阶题：AbstractRoutingDataSource 的原理是什么？如何与 Spring 事务协同工作？

**难度级别**：⭐⭐⭐（动态数据源、ThreadLocal、事务传播）

**1️⃣ Common Answer**
AbstractRoutingDataSource 是动态数据源，根据 key 切换数据源。用 ThreadLocal 存数据源 key。事务内不能切换数据源。

**2️⃣ Impressive Answer**

1. **AbstractRoutingDataSource 原理**：继承 `AbstractRoutingDataSource`，实现 `determineCurrentLookupKey()` 方法，返回数据源 key。内部维护 `Map<Object, Object> targetDataSources`，存储多个数据源。`getConnection()` 时，根据 `determineCurrentLookupKey()` 返回的 key 从 `targetDataSources` 获取对应数据源。

2. **ThreadLocal 存储数据源 key**：

```java
public class DynamicDataSource extends AbstractRoutingDataSource {
    private static final ThreadLocal<String> contextHolder = new ThreadLocal<>();
       
    public static void setDataSourceKey(String key) {
        contextHolder.set(key);
    }
       
    @Override
    protected Object determineCurrentLookupKey() {
        return contextHolder.get();
    }
}
```

使用时：`DynamicDataSource.setDataSourceKey("secondary")`，后续 SQL 操作使用 secondary 数据源。

1. **与 Spring 事务协同**：

  - **事务内切换数据源**：事务开始前切换数据源，事务内所有操作使用同一数据源。**注意**：事务内不能切换数据源，否则报错（事务绑定的是初始数据源的 Connection）。

  - **事务传播行为**：`REQUIRED` 传播行为下，子事务继承父事务的数据源；`REQUIRES_NEW` 传播行为下，子事务可以切换数据源。

  - **最佳实践**：在 `@Transactional` 方法外切换数据源，事务内不切换；或使用 `@Transactional(propagation = Propagation.REQUIRES_NEW)` 开启新事务切换数据源。

2. **Agent 场景实践**：Agent 工具调用需要读写业务库和向量库，使用动态数据源切换：

```java
@Service
public class AgentToolService {
    @Transactional
    public void executeTool(ToolRequest request) {
        DynamicDataSource.setDataSourceKey("primary");
        businessMapper.insert(request);
        DynamicDataSource.setDataSourceKey("secondary");
        vectorMapper.insert(request.getVector());
    }
}
```

**注意**：上述代码会报错，因为事务内切换数据源无效。正确做法：拆分成两个事务方法，或使用 `REQUIRES_NEW`。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了动态切换 | AbstractRoutingDataSource 原理→ThreadLocal→事务协同→Agent 场景 |
| 技术深度 | 没提事务传播和 Connection 绑定 | 有完整的底层机制和事务协同细节 |
| 实践经验 | 没考虑事务内切换的限制 | 有具体的代码示例和最佳实践 |
| 面试官印象 | 知道动态数据源但不懂原理 | 理解底层机制和工程实践 |

---

### 3、场景题：Agent 工具调用需要同时读写业务库和向量库，如何保证跨库操作的数据一致性？

**难度级别**：⭐⭐⭐（分布式事务、两阶段提交、Agent 场景）

**1️⃣ Common Answer**
用分布式事务，如 Seata。或者用消息队列，最终一致性。先写业务库，再写向量库，失败回滚。

**2️⃣ Impressive Answer**

1. **场景分析**：Agent 工具调用需要同时写入业务库（订单、用户）和向量库（向量数据），两个数据库独立部署，无法使用本地事务保证一致性。**挑战**：网络分区、数据库宕机、部分提交导致数据不一致。

2. **方案 1：本地事务 + 补偿机制（推荐）**：

  - 主流程：先写业务库（本地事务），成功后写向量库（远程调用）。

  - 补偿机制：向量库写入失败时，记录失败日志，通过定时任务重试；或发送消息到 MQ，消费者重试。

  - **代码示例**：

```java
@Transactional
public void executeTool(ToolRequest request) {
    businessMapper.insert(request);
    try {
        vectorService.insertVector(request.getVector());
    } catch (Exception e) {
        log.error("向量库写入失败，记录重试日志", e);
        retryLogMapper.insert(new RetryLog(request));
    }
}
```

1. **方案 2：Seata 分布式事务**：

  - 使用 Seata AT 模式，业务库和向量库都接入 Seata，通过 `@GlobalTransactional` 保证分布式事务一致性。

  - **缺点**：性能开销大（锁机制、日志记录），不适合高并发场景。

  - **适用场景**：强一致性要求高、并发量低的场景（如金融系统）。

2. **Agent 场景最佳实践**：

  - **弱一致性**：工具调用允许短暂不一致，用本地事务 + 补偿机制，性能好。

  - **强一致性**：关键操作（如支付）用 Seata，保证数据一致。

  - **监控与告警**：监控跨库操作的成功率、失败重试次数，设置告警（失败率 > 1%）。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了分布式事务 | 本地事务+补偿→Seata→Agent 最佳实践→监控告警 |
| 技术深度 | 没提补偿机制和性能开销 | 有完整的方案对比和代码示例 |
| 实践经验 | 没考虑 Agent 场景 | 有具体的优化案例和监控方案 |
| 面试官印象 | 知道分布式事务但不会选型 | 有系统化的方案设计和工程实践 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| Spring 事务传播 | 事务传播行为影响跨库操作的一致性 |
| 分布式事务 | 多数据源场景下，分布式事务保证一致性 |
| MyBatis 插件 | 插件可以拦截 SQL，用于监控跨库操作 |
| 消息队列 | 消息队列实现最终一致性，补偿机制 |

---

## MyBatis-Plus 选型与实践

### 1、基础题：MyBatis-Plus 的条件构造器（LambdaQueryWrapper）和手写 XML 动态 SQL 各有什么优缺点？

**难度级别**：⭐⭐（条件构造器、动态 SQL、代码可读性）

**1️⃣ Common Answer**
LambdaQueryWrapper 用 Java 代码写查询，方便，不用写 XML。XML 动态 SQL 灵活，复杂查询用 XML。LambdaQueryWrapper 类型安全，XML 容易写错。

**2️⃣ Impressive Answer**

1. **LambdaQueryWrapper 优点**：

  - **类型安全**：编译期检查字段名，避免 SQL 拼写错误。

  - **代码可读性**：Java 代码直观，IDE 支持重构和跳转。

  - **动态条件**：支持 `if` 条件判断，动态构建查询：

```java
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(User::getStatus, "ACTIVE")
       .like(StringUtils.isNotBlank(name), User::getName, name)
       .ge(User::getCreateTime, startTime);
```

- **链式调用**：API 设计优雅，代码简洁。

1. **LambdaQueryWrapper 缺点**：

  - **复杂查询限制**：多表关联、子查询、复杂聚合查询不如 XML 灵活。

  - **性能问题**：动态拼接 SQL，可能生成低效 SQL（如 `OR` 条件过多）。

  - **学习成本**：需要熟悉 MyBatis-Plus API。

2. **XML 动态 SQL 优点**：

  - **灵活性高**：支持复杂 SQL（多表关联、子查询、存储过程调用）。

  - **SQL 优化**：可以手动优化 SQL，避免低效查询。

  - **可维护性**：SQL 与代码分离，DBA 可以直接优化 SQL。

3. **XML 动态 SQL 缺点**：

  - **类型不安全**：字段名是字符串，容易拼写错误。

  - **代码冗余**：需要编写 XML 文件，增加维护成本。

  - **重构困难**：修改字段名需要同步修改 XML。

4. **选型建议**：

  - **简单查询**：用 `LambdaQueryWrapper`，提高开发效率。

  - **复杂查询**：用 XML 动态 SQL，保证 SQL 性能和灵活性。

  - **混合使用**：简单条件用 `LambdaQueryWrapper`，复杂逻辑用 XML。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了优缺点 | 优点→缺点→选型建议→代码示例 |
| 技术深度 | 没提性能问题和 SQL 优化 | 有完整的优缺点对比和选型策略 |
| 实践经验 | 没考虑 Agent 场景 | 有具体的选型建议和最佳实践 |
| 面试官印象 | 知道区别但不会选型 | 有系统化的选型思路和工程实践 |

---

### 2、进阶题：MyBatis-Plus 的自动填充（MetaObjectHandler）和逻辑删除是如何实现的？

**难度级别**：⭐⭐⭐（自动填充、逻辑删除、拦截器、Agent 场景）

**1️⃣ Common Answer**
自动填充用 MetaObjectHandler，在插入和更新时自动填充字段。逻辑删除用 @TableLogic，删除时改标记字段，不是真删除。

**2️⃣ Impressive Answer**

1. **自动填充实现**：

  - 实现 `MetaObjectHandler` 接口，重写 `insertFill()` 和 `updateFill()` 方法：

```java
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "createBy", String.class, getCurrentUserId());
    }
         
    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
        this.strictUpdateFill(metaObject, "updateBy", String.class, getCurrentUserId());
    }
}
```

- 实体类字段添加 `@TableField(fill = FieldFill.INSERT)` 或 `@TableField(fill = FieldFill.INSERT_UPDATE)`，触发自动填充。

1. **自动填充原理**：

  - MyBatis-Plus 通过 `MybatisPlusInterceptor` 拦截 SQL 执行，在插入和更新前调用 `MetaObjectHandler` 填充字段。

  - `strictInsertFill()` 严格填充（字段存在且非空才填充），`fillStrategy()` 策略填充（覆盖已有值）。

2. **逻辑删除实现**：

  - 实体类字段添加 `@TableLogic`：

```java
@TableLogic
private Integer deleted;
```

- 配置逻辑删除值和未删除值：

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted
      logic-delete-value: 1
      logic-not-delete-value: 0
```

- 删除操作自动转为 `UPDATE`：`UPDATE user SET deleted = 1 WHERE id = ?`；查询自动添加条件：`WHERE deleted = 0`。

1. **Agent 场景实践**：

  - **自动填充**：Agent 对话记录自动填充 `createTime`、`createBy`（Agent ID），避免手动设置，减少代码冗余。

  - **逻辑删除**：Agent 工具调用记录逻辑删除，保留历史数据用于审计和分析，查询时自动过滤已删除记录。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了概念和配置 | 自动填充实现→原理→逻辑删除实现→Agent 场景 |
| 技术深度 | 没提拦截器和填充策略 | 有完整的底层实现和代码示例 |
| 实践经验 | 没考虑 Agent 场景 | 有具体的优化案例和最佳实践 |
| 面试官印象 | 知道功能但不懂原理 | 理解底层机制和工程实践 |

---

### 3、场景题：Agent 需要根据 LLM 返回的结构化条件动态构建查询，MyBatis-Plus 和 XML 动态 SQL 如何选型？

**难度级别**：⭐⭐⭐（动态查询、LLM 场景、选型策略）

**1️⃣ Common Answer**
用 MyBatis-Plus 的条件构造器，动态拼接条件。LLM 返回什么条件就加什么条件。或者用 XML 动态 SQL，灵活。

**2️⃣ Impressive Answer**

1. **场景分析**：LLM 返回结构化条件（如 `{"name": "张三", "age": ">18", "status": "ACTIVE"}`），需要动态构建 SQL 查询。**挑战**：条件数量不固定、操作符多样（`=`、`>`、`LIKE`）、字段类型多样。

2. **方案 1：MyBatis-Plus 条件构造器（推荐）**：

  - 解析 LLM 返回的 JSON，动态构建 `LambdaQueryWrapper`：

```java
public List<User> queryByLLMCondition(String conditionJson) {
    Map<String, Object> condition = JSON.parseObject(conditionJson, new TypeReference<Map<String, Object>>() {});
    LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
    condition.forEach((key, value) -> {
        if (value instanceof String) {
            wrapper.like(User::getName, value);
        } else if (value instanceof Number) {
            wrapper.eq(User::getAge, value);
        } else if (value instanceof Map) {
            Map<String, String> opMap = (Map<String, String>) value;
            if (opMap.containsKey("$gt")) {
                wrapper.gt(User::getAge, opMap.get("$gt"));
            }
        }
    });
    return userMapper.selectList(wrapper);
}
```

- **优点**：类型安全、代码简洁、支持动态条件。

- **缺点**：复杂操作符（如 `IN`、`BETWEEN`）需要手动处理。

1. **方案 2：XML 动态 SQL**：

  - 在 Mapper XML 中使用 `<if>`、`<choose>`、`<foreach>` 动态构建 SQL：

```xml
<select id="queryByLLMCondition" resultType="User">
    SELECT * FROM user
    <where>
        <if test="name != null">AND name LIKE CONCAT('%', #{name}, '%')</if>
        <if test="age != null">AND age = #{age}</if>
        <if test="ageMin != null">AND age > #{ageMin}</if>
        <if test="status != null">AND status = #{status}</if>
    </where>
</select>
```

- **优点**：SQL 灵活、支持复杂操作符。

- **缺点**：字段名是字符串，容易拼写错误。

1. **选型建议**：

  - **简单动态查询**：用 MyBatis-Plus 条件构造器，提高开发效率。

  - **复杂动态查询**：用 XML 动态 SQL，保证 SQL 灵活性。

  - **混合使用**：基础条件用 `LambdaQueryWrapper`，复杂逻辑用 XML。

2. **Agent 场景最佳实践**：

  - **LLM 返回简单条件**（如 `name=张三`、`age>18`）：用 `LambdaQueryWrapper`，代码简洁。

  - **LLM 返回复杂条件**（如 `IN (1,2,3)`、`BETWEEN 10 AND 20`）：用 XML 动态 SQL，保证 SQL 性能。

  - **监控与优化**：通过 MyBatis 插件统计 SQL 执行时间，优化慢查询。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了选型 | 场景分析→MyBatis-Plus 方案→XML 方案→选型建议→Agent 最佳实践 |
| 技术深度 | 没提复杂操作符和性能优化 | 有完整的方案对比和代码示例 |
| 实践经验 | 没考虑 LLM 场景 | 有具体的选型策略和优化案例 |
| 面试官印象 | 知道选型但不会设计 | 有系统化的方案设计和工程实践 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 动态 SQL | MyBatis-Plus 条件构造器是动态 SQL 的 Java 实现 |
| LLM 应用 | LLM 返回结构化条件，动态构建 SQL 查询 |
| MyBatis 插件 | 插件可以拦截 SQL，用于监控动态查询性能 |
| SQL 注入防护 | 动态拼接 SQL 需要注意 SQL 注入防护 |

---

## ResultMap 高级映射

### 1、基础题：MyBatis 的 ResultMap 和 resultType 有什么区别？什么时候必须用 ResultMap？

**难度级别**：⭐⭐（自动映射 vs 手动映射、字段名不一致、复杂映射场景）

**1️⃣ Common Answer**
resultType 是自动映射，数据库字段名和 Java 属性名一样就能直接映射。ResultMap 是手动映射，需要自己配置字段对应关系。如果字段名不一样或者需要关联查询，就用 ResultMap。

**2️⃣ Impressive Answer**

1. **resultType 自动映射**：`resultType="com.example.User"` 基于 Java Bean 规范，通过反射自动映射，要求数据库列名和 Java 属性名完全一致（或遵循驼峰命名转换）。**适用场景**：简单查询、单表映射、字段名规范。

2. **ResultMap 手动映射**：`<resultMap id="userMap" type="User">` 精确控制字段映射关系，通过 `<result column="db_name" property="javaName"/>` 指定映射。**必须用 ResultMap 的场景**：字段名不一致、多表关联、复杂类型映射、需要延迟加载。

3. **高级映射能力**：ResultMap 支持 `association`（一对一）、`collection`（一对多）、`discriminator`（鉴别器）等高级映射，能解决复杂对象关系映射问题。resultType 无法处理这些场景。

4. **性能差异**：resultType 性能略优（直接反射），ResultMap 需要解析配置；但 ResultMap 的可维护性更好，字段变更只需修改配置，不改 Java 代码。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了自动 vs 手动 | resultType 原理→ResultMap 能力→必须场景→性能对比 |
| 技术深度 | 不知道 association/collection | 有高级映射的完整说明 |
| 实践经验 | 没提字段名不一致问题 | 有具体的必用场景和可维护性分析 |
| 面试官印象 | 知道区别但不会用 | 理解映射机制，能根据场景选型 |

---

### 2、进阶题：ResultMap 的 association（一对一）和 collection（一对多）如何配置？嵌套查询和嵌套结果的区别？

**难度级别**：⭐⭐⭐（嵌套查询 vs 嵌套结果、N+1 问题、延迟加载）

**1️⃣ Common Answer**
association 用在一对一，collection 用在一对多。嵌套查询是再查一次数据库，嵌套结果是一次查询把数据都查出来。嵌套查询可能会有 N+1 问题，所以一般用嵌套结果。

**2️⃣ Impressive Answer**

1. **association 一对一配置**：`<association property="tool" javaType="Tool" column="tool_id" select="selectToolById"/>` 嵌套查询方式，或 `<association property="tool" resultMap="toolMap"/>` 嵌套结果方式，通过 `resultMap` 复用映射规则。

2. **collection 一对多配置**：`<collection property="params" ofType="ToolParam" column="tool_id" select="selectParamsByToolId"/>` 嵌套查询，或 `<collection property="params" resultMap="paramMap"/>` 嵌套结果，一对多返回 List。

3. **嵌套查询 vs 嵌套结果**：嵌套查询执行多条 SQL（主查询 + N 条子查询），**N+1 问题**：查 100 条工具调用记录，会执行 101 条 SQL；嵌套结果执行一条 SQL，通过 JOIN 查询，性能更好，但 SQL 复杂度增加。

4. **延迟加载优化**：嵌套查询配合 `lazyLoadingEnabled="true"`，只有在访问关联对象时才执行子查询，减少不必要的查询。**Agent 场景**：工具调用记录列表只显示基本信息，点击详情才加载工具详情和参数，延迟加载避免性能浪费。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了配置方式 | 配置示例→嵌套对比→N+1 问题→延迟加载 |
| 技术深度 | 不知道 N+1 问题原理 | 能说出 N+1 问题和 JOIN 查询的权衡 |
| 实践经验 | 没考虑延迟加载 | 有 Agent 场景的延迟加载实践 |
| 面试官印象 | 会配置但不懂性能问题 | 理解性能优化策略，能设计高效映射 |

---

### 3、场景题：Agent 的工具调用记录需要关联查询工具详情和参数列表（一对多），如何用 ResultMap 优雅映射？

**难度级别**：⭐⭐⭐（复杂映射、性能优化、Agent 场景）

**1️⃣ Common Answer**
可以写一个 ResultMap，用 association 关联工具详情，用 collection 关联参数列表。查询的时候用 JOIN 把表连起来，一次查询把数据都查出来。

**2️⃣ Impressive Answer**

1. **ResultMap 配置**：

```xml
<resultMap id="toolCallMap" type="ToolCall">
  <id property="id" column="call_id"/>
  <result property="toolName" column="tool_name"/>
  <association property="tool" javaType="Tool" column="tool_id" select="selectToolById"/>
  <collection property="params" ofType="ToolParam" column="call_id" select="selectParamsByCallId"/>
</resultMap>
```

1. **嵌套结果优化**：为避免 N+1 问题，使用嵌套结果方式，一条 SQL 查询所有数据：

```sql
SELECT c.id as call_id, c.tool_name, t.*, p.*
FROM tool_call c
LEFT JOIN tool t ON c.tool_id = t.id
LEFT JOIN tool_param p ON c.id = p.call_id
WHERE c.session_id = #{sessionId}
```

1. **Agent 场景性能优化**：工具调用记录查询频率高，参数列表只在详情页展示，使用**延迟加载**：`<collection fetchType="lazy" .../>`，列表页不加载参数，减少数据传输量。**缓存策略**：工具详情用二级缓存，避免重复查询。

2. **分页处理**：一对多关联查询时，主记录分页需要特殊处理（如使用 `DISTINCT` 或子查询），避免分页数据不准确。**Agent 最佳实践**：工具调用列表只返回主记录，参数列表通过独立接口按需加载。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 JOIN 查询 | ResultMap 配置→嵌套结果→延迟加载→分页处理 |
| 技术深度 | 没考虑 N+1 和延迟加载 | 有完整的性能优化方案 |
| 实践经验 | 没考虑 Agent 场景的查询特点 | 有分页和按需加载的具体策略 |
| 面试官印象 | 会写映射但不懂优化 | 有工程化思维，能设计高性能方案 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 一级缓存 | 嵌套查询时，一级缓存如何避免重复查询 |
| MyBatis 插件 | 插件可以拦截 ResultSetHandler，用于统计关联查询性能 |
| 数据库连接池 | 复杂关联查询占用连接时间长，影响连接池效率 |
| MyBatis-Plus | MyBatis-Plus 的 @TableField 注解 vs ResultMap 手动映射 |

---

## MyBatis 批量操作优化

### 1、基础题：MyBatis 如何实现批量插入？foreach 标签和 ExecutorType.BATCH 有什么区别？

**难度级别**：⭐⭐（批量插入方式、性能对比、SQL 长度限制）

**1️⃣ Common Answer**
批量插入可以用 foreach 标签，把多条数据拼成一条 INSERT 语句。或者用 ExecutorType.BATCH，循环调用 insert 方法，MyBatis 会自动批量执行。foreach 性能好一些。

**2️⃣ Impressive Answer**

1. **foreach 标签批量插入**：`INSERT INTO table (col1, col2) VALUES <foreach item="item" collection="list" separator=",">(#{item.col1}, #{item.col2})</foreach>`，生成一条长 SQL，性能最优（一次网络交互），但有 SQL 长度限制（MySQL 默认 4MB）。

2. **ExecutorType.BATCH 批量**：`sqlSessionFactory.openSession(ExecutorType.BATCH)` 开启批处理，循环调用 `mapper.insert()`，MyBatis 缓存 SQL 和参数，最后 `session.flushStatements()` 一次性提交。**优点**：无 SQL 长度限制，适合大批量数据；**缺点**：性能略低于 foreach。

3. **性能对比**：foreach 一次网络交互，性能最佳（1000 条数据约 50ms）；BATCH 多次网络交互但批量提交，性能次之（1000 条约 100ms）；普通循环插入性能最差（1000 条约 2000ms）。

4. **Agent 场景选择**：批量保存 100+ 条消息记录，优先用 foreach（性能最佳）；批量保存 10000+ 条历史归档数据，用 BATCH（避免 SQL 过长）。**注意**：BATCH 模式下，`insert()` 返回值不准确（可能返回 -1 或 0），需用 `session.flushStatements()` 获取实际影响行数。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了两种方式 | foreach 示例→BATCH 原理→性能对比→场景选择 |
| 技术深度 | 不知道 SQL 长度限制和返回值问题 | 有完整的性能分析和注意事项 |
| 实践经验 | 没考虑 Agent 场景的数据量差异 | 有具体的选择策略和性能数据 |
| 面试官印象 | 会用批量但不懂原理 | 理解批量机制，能根据场景优化 |

---

### 2、进阶题：MyBatis 的 BatchExecutor 和 ReuseExecutor 的工作原理是什么？如何选择合适的 Executor 类型？

**难度级别**：⭐⭐⭐（Executor 类型、批处理原理、Statement 复用）

**1️⃣ Common Answer**
BatchExecutor 是批量执行，ReuseExecutor 是复用 Statement。BatchExecutor 适合批量插入，ReuseExecutor 适合重复执行相同的 SQL。一般用默认的 SimpleExecutor 就行。

**2️⃣ Impressive Answer**

1. **SimpleExecutor（默认）**：每次执行 SQL 都创建新的 `PreparedStatement`，执行完立即关闭。**适用场景**：普通 CRUD 操作，SQL 不重复，简单直接。

2. **ReuseExecutor**：内部维护 `Map<String, Statement>`，相同 SQL 复用同一个 `PreparedStatement`，只重新设置参数。**原理**：`StatementId = SQL + 数据库` 作为 key，执行时先从缓存获取，不存在则创建。**适用场景**：循环执行相同 SQL（如批量更新不同记录），减少 PreparedStatement 创建开销。

3. **BatchExecutor**：批量执行 SQL，内部维护 `List<BatchResult>`，每次 `update/insert` 将 SQL 和参数加入批处理队列，`flushStatements()` 时一次性提交。**原理**：JDBC 的 `addBatch()` + `executeBatch()`，减少网络交互。**适用场景**：大批量插入/更新（如 Agent 消息记录归档）。

4. **选择策略**：普通操作用 SimpleExecutor；循环执行相同 SQL 用 ReuseExecutor；大批量操作用 BatchExecutor。**Spring 配置**：`<bean id="sqlSessionFactory" class="org.mybatis.spring.SqlSessionFactoryBean"><property name="configuration"><bean class="org.apache.ibatis.session.Configuration"><property name="defaultExecutorType" value="BATCH"/></bean></property></bean>`。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了简单描述 | 三种 Executor 原理→适用场景→Spring 配置 |
| 技术深度 | 不知道 Statement 复用机制 | 有底层实现和缓存机制说明 |
| 实践经验 | 没有具体的选择策略 | 有清晰的选型决策树 |
| 面试官印象 | 知道有不同类型 | 理解 Executor 设计，能优化性能 |

---

### 3、场景题：Agent 每次对话结束需要批量保存 100+ 条消息记录，如何用 MyBatis 实现高性能批量写入？

**难度级别**：⭐⭐⭐（批量优化、性能调优、Agent 场景）

**1️⃣ Common Answer**
可以用 foreach 标签，把 100 条消息拼成一条 INSERT 语句，一次性插入数据库。或者用 ExecutorType.BATCH，循环调用 insert 方法，然后 flushStatements。

**2️⃣ Impressive Answer**

1. **foreach 批量插入**：

```xml
<insert id="batchInsertMessages">
  INSERT INTO agent_message (session_id, role, content, create_time)
  VALUES
  <foreach collection="messages" item="msg" separator=",">
    (#{msg.sessionId}, #{msg.role}, #{msg.content}, #{msg.createTime})
  </foreach>
</insert>
```

**性能**：100 条数据约 50ms，一次网络交互，最优方案。

1. **BATCH 模式兜底**：如果消息量超过 1000 条（SQL 长度超限），切换到 BATCH 模式：

```java
SqlSession batchSession = sqlSessionFactory.openSession(ExecutorType.BATCH);
try {
  AgentMessageMapper mapper = batchSession.getMapper(AgentMessageMapper.class);
  for (AgentMessage msg : messages) {
    mapper.insert(msg);
  }
  batchSession.flushStatements();
  batchSession.commit();
} finally {
  batchSession.close();
}
```

1. **Agent 场景优化**：消息记录按 `session_id` 分表，避免单表过大；批量插入前**去重校验**，避免重复插入相同消息；**异步化处理**：对话结束后异步批量保存，不阻塞用户响应。

2. **性能监控**：通过 MyBatis 插件统计批量操作耗时，设置超时告警（如 100 条消息超过 100ms 告警）；**连接池调优**：批量操作占用连接时间长，适当增加连接池最大连接数（如从 10 增加到 20）。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了两种方式 | foreach 示例→BATCH 兜底→分表异步→监控调优 |
| 技术深度 | 没考虑 SQL 长度和异步化 | 有完整的性能优化和容错方案 |
| 实践经验 | 没考虑 Agent 场景的特点 | 有分表、异步、监控的具体实践 |
| 面试官印象 | 会用批量但不懂优化 | 有工程化思维，能设计高性能方案 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 连接池 | 批量操作占用连接时间长，影响连接池效率 |
| 数据库事务 | 批量操作的事务管理，失败回滚策略 |
| MySQL 批量插入限制 | max*allowed*packet 参数，SQL 长度限制 |
| MyBatis 插件 | 插件可以拦截 Executor，用于监控批量操作性能 |

---

## MyBatis 与 Spring 事务集成

### 1、基础题：MyBatis 的 SqlSession 和 Spring 的事务管理器是如何集成的？

**难度级别**：⭐⭐（事务管理器、SqlSessionTemplate、事务传播）

**1️⃣ Common Answer**
Spring 提供了 SqlSessionTemplate，它封装了 SqlSession，可以在 Spring 事务中使用。配置 DataSourceTransactionManager 事务管理器，用 @Transactional 注解开启事务。

**2️⃣ Impressive Answer**

1. **SqlSessionTemplate 的作用**：`SqlSessionTemplate` 是线程安全的 SqlSession 封装，内部代理了 `DefaultSqlSession`，确保每次操作在事务内共享同一个 SqlSession，非事务时创建新 SqlSession。**核心方法**：`getMapper()`、`selectList()`、`insert()` 等，自动处理事务边界。

2. **事务管理器集成**：`DataSourceTransactionManager` 管理事务，通过 `@Transactional` 注解开启事务；事务开始时，`SqlSessionUtils` 创建 SqlSession 并绑定到 ThreadLocal；事务提交/回滚时，自动关闭 SqlSession。

3. **事务传播行为**：`@Transactional(propagation = Propagation.REQUIRED)` 默认行为，加入已有事务或创建新事务；`REQUIRES_NEW` 挂起当前事务，创建新事务；`SUPPORTS` 有事务则加入，无事务则非事务执行。**Agent 场景**：工具调用链中，多个 Mapper 操作默认 REQUIRED，确保原子性。

4. **配置示例**：

```xml
<bean id="transactionManager" class="org.springframework.jdbc.datasource.DataSourceTransactionManager">
  <property name="dataSource" ref="dataSource"/>
</bean>
<tx:annotation-driven transaction-manager="transactionManager"/>
```

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了基本配置 | SqlSessionTemplate 原理→事务管理器→传播行为→配置示例 |
| 技术深度 | 不知道 ThreadLocal 绑定机制 | 有底层实现和事务传播说明 |
| 实践经验 | 没考虑 Agent 场景的事务需求 | 有具体的事务传播策略 |
| 面试官印象 | 会配置但不懂原理 | 理解集成机制，能设计事务方案 |

---

### 2、进阶题：SqlSessionTemplate 和 DefaultSqlSession 的区别是什么？Spring 如何保证同一事务内使用同一个 SqlSession？

**难度级别**：⭐⭐⭐（SqlSession 管理、ThreadLocal、事务同步）

**1️⃣ Common Answer**
SqlSessionTemplate 是 Spring 提供的，DefaultSqlSession 是 MyBatis 原生的。SqlSessionTemplate 是线程安全的，DefaultSqlSession 不是。Spring 用 ThreadLocal 保证同一事务内用同一个 SqlSession。

**2️⃣ Impressive Answer**

1. **DefaultSqlSession**：MyBatis 原生实现，非线程安全，每次操作创建新实例，用完必须关闭。**生命周期**：方法级别，不能跨方法共享。

2. **SqlSessionTemplate**：Spring 封装，线程安全，内部通过动态代理代理 `DefaultSqlSession`，每次操作前检查 ThreadLocal 是否有 SqlSession，有则复用，无则创建。**核心机制**：`SqlSessionInterceptor` 拦截方法调用，委托给 `SqlSessionUtils.getSession()` 获取 SqlSession。

3. **ThreadLocal 绑定机制**：`SqlSessionUtils.getSession()` 内部调用 `TransactionSynchronizationManager.getResource(dataSource)`，从 ThreadLocal 获取当前事务绑定的 SqlSession；事务开始时，`SqlSessionUtils.registerSession()` 将 SqlSession 绑定到 ThreadLocal；事务结束时，`SqlSessionUtils.closeSqlSession()` 清理 ThreadLocal。

4. **事务同步管理**：`TransactionSynchronizationManager` 维护事务同步资源（DataSource → SqlSession），确保同一事务内所有 Mapper 操作共享同一个 SqlSession，一级缓存生效；事务提交后，自动关闭 SqlSession，清理资源。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了线程安全 | DefaultSqlSession→SqlSessionTemplate→ThreadLocal→事务同步 |
| 技术深度 | 不知道代理和绑定机制 | 有完整的底层实现说明 |
| 实践经验 | 没考虑一级缓存共享 | 理解事务内缓存共享机制 |
| 面试官印象 | 知道区别但不懂原理 | 理解 Spring 事务与 SqlSession 的协同机制 |

---

### 3、场景题：Agent 工具调用链中，多个 Mapper 操作需要在同一个事务内完成，如何确保事务一致性？

**难度级别**：⭐⭐⭐（事务一致性、异常处理、Agent 场景）

**1️⃣ Common Answer**
用 @Transactional 注解开启事务，多个 Mapper 操作在同一个方法里调用，如果有异常就回滚。事务传播用默认的 REQUIRED 就行。

**2️⃣ Impressive Answer**

1. **事务配置**：

```java
@Transactional(rollbackFor = Exception.class)
public ToolCallResult executeToolChain(ToolChainRequest request) {
  // 1. 保存工具调用记录
  toolCallMapper.insert(toolCall);
  // 2. 执行工具调用
  ToolResult result = toolExecutor.execute(toolCall);
  // 3. 更新调用结果
  toolCallMapper.updateStatus(toolCall.getId(), "SUCCESS", result);
  // 4. 保存工具参数
  toolParamMapper.batchInsert(params);
  return result;
}
```

**关键点**：`rollbackFor = Exception.class` 确保所有异常回滚，默认只回滚 RuntimeException。

1. **事务传播策略**：工具调用链涉及多个 Service 方法，使用 `@Transactional(propagation = Propagation.REQUIRED)` 确保加入同一事务；如果需要独立事务（如日志记录），用 `REQUIRES_NEW` 挂起当前事务。

2. **异常处理**：工具调用失败时抛出 `ToolExecutionException`，触发事务回滚；**注意**：`try-catch` 捕获异常后不会回滚，需手动调用 `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`。

3. **Agent 场景优化**：工具调用链可能耗时较长（如 LLM 生成），设置事务超时 `@Transactional(timeout = 30)`，避免长时间占用数据库连接；**异步化处理**：非核心操作（如日志记录）异步执行，减少事务时间。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 @Transactional | 代码示例→传播策略→异常处理→超时异步 |
| 技术深度 | 不知道 rollbackFor 和超时配置 | 有完整的事务配置和异常处理 |
| 实践经验 | 没考虑 Agent 场景的长事务问题 | 有超时和异步的具体优化 |
| 面试官印象 | 会用事务但不懂细节 | 理解事务机制，能设计一致性方案 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 一级缓存 | 事务内共享 SqlSession，一级缓存生效 |
| Spring 事务传播 | 不同传播行为对事务边界的影响 |
| 数据库隔离级别 | Spring 事务隔离级别与数据库隔离级别的关系 |
| 分布式事务 | 跨多个数据库的事务一致性解决方案 |

---

## MyBatis 配置优化与调优

### 1、基础题：MyBatis 的 settings 配置有哪些常用项？cacheEnabled、lazyLoadingEnabled 分别控制什么？

**难度级别**：⭐⭐（settings 配置、缓存控制、延迟加载）

**1️⃣ Common Answer**
settings 是 MyBatis 的配置项，可以配置缓存、延迟加载等。cacheEnabled 控制二级缓存是否开启，lazyLoadingEnabled 控制是否延迟加载关联对象。

**2️⃣ Impressive Answer**

1. **常用 settings 配置**：

  - `cacheEnabled="true"`：全局开启二级缓存（默认 true），可被 Mapper 级别覆盖

  - `lazyLoadingEnabled="true"`：全局开启延迟加载（默认 false），按需加载关联对象

  - `aggressiveLazyLoading="false"`：按需加载（默认 true，加载任一属性则加载所有）

  - `multipleResultSetsEnabled="true"`：允许单条语句返回多个结果集（默认 true）

  - `useColumnLabel="true"`：使用列标签代替列名（默认 true）

  - `defaultExecutorType="SIMPLE"`：默认执行器类型（SIMPLE/REUSE/BATCH）

2. **cacheEnabled 控制二级缓存**：`cacheEnabled="true"` 时，Mapper XML 中配置 `<cache/>` 生效，多个 SqlSession 共享缓存；`cacheEnabled="false"` 时，即使配置 `<cache/>` 也不生效。**Agent 场景**：知识库查询开启二级缓存，减少 DB 压力。

3. **lazyLoadingEnabled 控制延迟加载**：`lazyLoadingEnabled="true"` 时，ResultMap 中的 `association` 和 `collection` 按需加载，访问关联对象时才执行子查询；`lazyLoadingEnabled="false"` 时，立即加载所有关联对象。**性能优化**：工具调用记录列表页，参数列表延迟加载，减少数据传输。

4. **配置示例**：

```xml
<settings>
  <setting name="cacheEnabled" value="true"/>
  <setting name="lazyLoadingEnabled" value="true"/>
  <setting name="aggressiveLazyLoading" value="false"/>
  <setting name="defaultExecutorType" value="REUSE"/>
</settings>
```

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了两个配置项 | 常用配置列表→缓存原理→延迟加载→配置示例 |
| 技术深度 | 不知道 aggressiveLazyLoading | 有完整的配置项说明和原理 |
| 实践经验 | 没考虑 Agent 场景的优化 | 有具体的应用场景和性能优化 |
| 面试官印象 | 知道配置但不懂原理 | 理解配置项的作用，能优化性能 |

---

### 2、进阶题：MyBatis 的连接池（PooledDataSource）工作原理是什么？如何调优连接池参数？

**难度级别**：⭐⭐⭐（连接池原理、参数调优、性能优化）

**1️⃣ Common Answer**
MyBatis 自带了连接池，可以复用数据库连接，避免频繁创建和销毁连接。可以配置最大连接数、初始连接数等参数。

**2️⃣ Impressive Answer**

1. **PooledDataSource 工作原理**：内部维护 `idleConnections`（空闲连接池）和 `activeConnections`（活跃连接池），请求连接时先从空闲池获取，无空闲则创建新连接（不超过最大连接数）；连接释放时归还到空闲池，超过最大空闲数则关闭。

2. **核心参数**：

  - `poolMaximumActiveConnections`：最大活跃连接数（默认 10），超过则等待

  - `poolMaximumIdleConnections`：最大空闲连接数（默认 10），超过则关闭

  - `poolMaximumCheckoutTime`：最大等待时间（默认 20000ms），超时抛异常

  - `poolTimeToWait`：等待重试间隔（默认 20000ms）

  - `poolPingQuery`：连接检测 SQL（默认 "SELECT 1"），检测连接有效性

  - `poolPingEnabled`：是否开启连接检测（默认 false）

3. **调优策略**：

  - **高峰期调优**：Agent 服务 QPS 1000+，设置 `poolMaximumActiveConnections=50`，避免连接耗尽

  - **空闲连接优化**：低峰期设置 `poolMaximumIdleConnections=5`，减少资源占用

  - **连接检测**：`poolPingEnabled=true`，`poolPingQuery="SELECT 1"`，避免使用失效连接

  - **等待时间**：`poolMaximumCheckoutTime=5000ms`，快速失败，避免长时间阻塞

4. **Agent 场景优化**：工具调用链耗时较长，适当增加 `poolMaximumCheckoutTime` 到 10000ms；知识库查询频率高，增加 `poolMaximumActiveConnections` 到 30；监控连接池指标（活跃连接数、等待队列长度），动态调整参数。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了连接复用 | 连接池原理→核心参数→调优策略→Agent 场景 |
| 技术深度 | 不知道参数的具体含义 | 有完整的参数说明和调优方案 |
| 实践经验 | 没考虑 QPS 和监控 | 有具体的调优数值和监控指标 |
| 面试官印象 | 知道连接池但不会调优 | 理解连接池机制，能优化性能 |

---

### 3、场景题：Agent 服务高峰期数据库连接耗尽，如何通过 MyBatis 和连接池配置优化解决？

**难度级别**：⭐⭐⭐（连接耗尽问题、配置优化、监控告警）

**1️⃣ Common Answer**
增加连接池的最大连接数，减少连接等待时间。优化 SQL 查询，减少查询时间。用连接池监控工具，看连接使用情况。

**2️⃣ Impressive Answer**

1. **连接池配置优化**：

```xml
<dataSource type="POOLED">
  <property name="driver" value="com.mysql.cj.jdbc.Driver"/>
  <property name="url" value="jdbc:mysql://localhost:3306/agent_db"/>
  <property name="username" value="root"/>
  <property name="password" value="password"/>
  <property name="poolMaximumActiveConnections" value="50"/>
  <property name="poolMaximumIdleConnections" value="10"/>
  <property name="poolMaximumCheckoutTime" value="10000"/>
  <property name="poolPingEnabled" value="true"/>
  <property name="poolPingQuery" value="SELECT 1"/>
</dataSource>
```

**关键点**：增加最大连接数到 50，等待时间 10 秒，开启连接检测。

1. **MyBatis 配置优化**：

  - **二级缓存**：知识库查询开启二级缓存，减少 DB 连接占用

  - **延迟加载**：工具调用记录参数列表延迟加载，减少长事务

  - **Executor 类型**：批量操作用 `BATCH`，减少连接占用时间

  - **超时设置**：`defaultStatementTimeout=5000ms`，避免慢查询占用连接

2. **SQL 优化**：

  - **索引优化**：为 `session_id`、`tool_id` 等高频查询字段添加索引

  - **分页优化**：大数据量查询使用分页，避免全表扫描

  - **批量操作**：消息记录批量插入，减少连接次数

3. **监控告警**：

  - **连接池监控**：通过 JMX 或 Prometheus 监控活跃连接数、等待队列长度

  - **慢查询告警**：设置慢查询阈值（5 秒），超过则告警

  - **连接泄露检测**：定期检查活跃连接数，发现异常增长告警

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了增加连接数 | 连接池配置→MyBatis 优化→SQL 优化→监控告警 |
| 技术深度 | 不知道具体参数和优化点 | 有完整的优化方案和配置示例 |
| 实践经验 | 没有监控和告警机制 | 有具体的监控指标和告警策略 |
| 面试官印象 | 会调连接数但不懂系统优化 | 有系统化思维，能解决生产问题 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis 批量操作 | 批量操作占用连接时间长，影响连接池效率 |
| 数据库连接池 | Druid/HikariCP vs MyBatis 自带连接池的对比 |
| 数据库索引 | 索引优化减少查询时间，释放连接池压力 |
| MyBatis 插件 | 插件可以拦截 SQL，用于监控连接池使用情况 |

---

## MyBatis Generator 与代码生成

### 1、基础题：MyBatis Generator（MBG）能生成哪些文件？如何配置？

**难度级别**：⭐⭐（代码生成、配置文件、生成内容）

**1️⃣ Common Answer**
MBG 可以生成 Mapper 接口、Mapper XML、实体类。配置一个 generatorConfig.xml 文件，指定数据库连接、要生成的表，然后运行 MBG 就能生成代码。

**2️⃣ Impressive Answer**

1. **MBG 生成内容**：

  - **实体类**：`User.java`，包含所有字段，支持 `@Generated` 注解

  - **Mapper 接口**：`UserMapper.java`，包含 `insert`、`updateByPrimaryKey`、`selectByPrimaryKey`、`deleteByPrimaryKey` 等基础方法

  - **Mapper XML**：`UserMapper.xml`，包含 SQL 映射配置

  - **Example 类**：`UserExample.java`，用于动态构建查询条件（如 `WHERE id = ? AND name LIKE ?`）

2. **配置文件 generatorConfig.xml**：

```xml
<generatorConfiguration>
  <context id="mysql" targetRuntime="MyBatis3">
    <jdbcConnection driverClass="com.mysql.cj.jdbc.Driver"
                    connectionURL="jdbc:mysql://localhost:3306/agent_db"
                    userId="root" password="password"/>
    <javaModelGenerator targetPackage="com.example.model" targetProject="src/main/java"/>
    <sqlMapGenerator targetPackage="mapper" targetProject="src/main/resources"/>
    <javaClientGenerator type="XMLMAPPER" targetPackage="com.example.mapper" targetProject="src/main/java"/>
    <table tableName="tool_call" domainObjectName="ToolCall"/>
  </context>
</generatorConfiguration>
```

1. **运行方式**：

  - **命令行**：`java -jar mybatis-generator-core-x.x.x.jar -configfile generatorConfig.xml`

  - **Maven 插件**：`mvn mybatis-generator:generate`

  - **Java 代码**：`GeneratorGenerator.generate(null, config, null, null, null, true)`

2. **生成策略**：`<table schema="agent_db" tableName="tool_call" domainObjectName="ToolCall" enableCountByExample="false" enableUpdateByExample="false" enableDeleteByExample="false" enableSelectByExample="false" selectByExampleQueryId="false"/>` 禁用 Example 类，只生成基础 CRUD。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了生成内容 | 生成内容→配置示例→运行方式→生成策略 |
| 技术深度 | 不知道 Example 类和生成策略 | 有完整的配置和运行说明 |
| 实践经验 | 没有具体的配置示例 | 有详细的配置文件和参数说明 |
| 面试官印象 | 知道 MBG 但不会配置 | 理解代码生成机制，能快速搭建项目 |

---

### 2、进阶题：MBG 生成的 Example 类是什么？如何自定义 MBG 插件扩展生成逻辑？

**难度级别**：⭐⭐⭐（Example 类、插件机制、自定义扩展）

**1️⃣ Common Answer**
Example 类是用来构建查询条件的，可以动态拼接 WHERE 条件。MBG 支持插件，可以自定义生成逻辑，比如生成注释、自定义方法等。

**2️⃣ Impressive Answer**

1. **Example 类的作用**：`UserExample example = new UserExample();` `example.createCriteria().andIdEqualTo(1).andNameLike("%test%");` 动态构建查询条件，避免手写 XML SQL。**核心类**：`Criteria`（内部类，构建 AND 条件）、`Criterion`（条件对象，封装字段、操作符、值）。

2. **Example 使用场景**：

  - **动态查询**：Agent 查询工具调用记录，按 `session_id`、`tool_name`、`status` 等条件组合查询

  - **复杂条件**：`example.or().andCreateTimeBetween(startTime, endTime);` 支持 OR 条件

  - **排序分页**：`example.setOrderByClause("create_time DESC");` 排序，配合 PageHelper 分页

3. **自定义 MBG 插件**：

```java
public class CommentPlugin extends PluginAdapter {
  @Override
  public boolean modelFieldGenerated(Field field, IntrospectedTable introspectedTable, IntrospectedColumn introspectedColumn, PluginModel.PluginModelClass pluginModelClass, PluginModel.PluginModelField pluginModelField) {
    field.addJavaDocLine("/** " + introspectedColumn.getRemarks() + " */");
    return true;
  }
}
```

**配置插件**：`<plugin type="com.example.CommentPlugin"/>`，为生成的字段添加数据库注释。

1. **扩展生成逻辑**：

  - **自定义方法**：继承 `IntrospectedTableMyBatis3Impl`，重写 `generateBaseRecordClass()`，添加自定义方法

  - **自定义模板**：修改 `mapperGenerator.ftl` 模板，生成自定义 Mapper 方法

  - **MyBatis-Plus 代码生成器**：`AutoGenerator generator = new AutoGenerator();` `generator.setStrategy(new StrategyConfig().setInclude("tool_call"));` 支持生成 Service、Controller 等更多文件。

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了 Example 和插件 | Example 原理→使用场景→自定义插件→扩展方式 |
| 技术深度 | 不知道 Criteria 和 Criterion | 有完整的 Example 类结构说明 |
| 实践经验 | 没有具体的插件代码 | 有详细的插件实现和配置 |
| 面试官印象 | 知道 Example 但不会用 | 理解代码生成机制，能自定义扩展 |

---

### 3、场景题：Agent 项目需要快速接入新的数据表，如何用 MBG 或 MyBatis-Plus 代码生成器提升开发效率？

**难度级别**：⭐⭐⭐（代码生成、开发效率、Agent 场景）

**1️⃣ Common Answer**
用 MBG 生成 Mapper 接口和实体类，然后手写业务逻辑。或者用 MyBatis-Plus 的代码生成器，生成 Service 和 Controller，直接用。

**2️⃣ Impressive Answer**

1. **MyBatis-Plus 代码生成器**：

```java
AutoGenerator generator = new AutoGenerator();
generator.setDataSource(new DataSourceConfig.Builder("jdbc:mysql://localhost:3306/agent_db", "root", "password").build());
generator.setGlobalConfig(new GlobalConfig.Builder().outputDir("src/main/java").author("agent").build());
generator.setPackageInfo(new PackageConfig.Builder().parent("com.example.agent").moduleName("tool").build());
generator.setStrategy(new StrategyConfig.Builder().addInclude("tool_call", "tool_param").entityBuilder().enableLombok().build());
generator.execute();
```

**生成内容**：Entity、Mapper、Mapper XML、Service、ServiceImpl、Controller，完整 CRUD 代码。

1. **Agent 场景快速接入**：

  - **新表接入**：Agent 新增 `agent_log` 表，运行代码生成器，5 分钟内生成完整 CRUD 代码

  - **自定义模板**：修改 `controller.java.ftl`，添加 Agent 特有的方法（如 `@PostMapping("/execute")` 工具执行接口）

  - **批量生成**：一次生成多个表（`addInclude("tool_call", "tool_param", "agent_log")`），统一代码风格

2. **开发效率提升**：

  - **减少重复代码**：自动生成基础 CRUD，专注业务逻辑开发

  - **统一代码规范**：通过模板统一代码风格，降低维护成本

  - **快速迭代**：Agent 功能快速扩展，新增数据表即时生成代码

3. **最佳实践**：

  - **版本控制**：生成代码纳入 Git，避免重复生成覆盖修改

  - **增量生成**：只生成新表，已生成的表手动维护

  - **自定义扩展**：在生成代码基础上添加业务逻辑，不修改生成模板

**3️⃣ Key Differences**

| 维度 | Common Answer | Impressive Answer |
| --- | --- | --- |
| 结构性 | 只说了生成代码 | MyBatis-Plus 示例→Agent 场景→效率提升→最佳实践 |
| 技术深度 | 不知道模板和批量生成 | 有完整的生成器配置和策略 |
| 实践经验 | 没有具体的开发流程 | 有清晰的快速接入流程 |
| 面试官印象 | 会用生成器但不懂优化 | 理解代码生成机制，能提升开发效率 |

---

### 4、容易一起考的题

| 关联题 | 和本题的关系 |
| --- | --- |
| MyBatis-Plus 条件构造器 | MyBatis-Plus 的 Wrapper 比 Example 更强大 |
| Lombok | 代码生成器结合 Lombok，减少样板代码 |
| 数据库设计 | 良好的数据库设计能生成更规范的代码 |
| 代码重构 | 生成代码后如何重构和优化 |
