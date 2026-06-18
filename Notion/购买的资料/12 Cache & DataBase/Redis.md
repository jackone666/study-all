# Redis

## Redis 核心基础与持久化

#### 1、基础题：Redis 为什么快？单线程模型为什么能支撑高并发？

**难度级别**：⭐⭐（内存存储、IO多路复用、单线程避免锁竞争、epoll）

---

#### 2、进阶题：RDB 和 AOF 持久化有什么区别？混合持久化怎么工作？

**难度级别**：⭐⭐⭐（快照 vs 日志追加、fork子进程、AOF重写、混合持久化 4.0+、数据安全 vs 性能）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- RDB：快照持久化
- AOF：追加日志持久化
- 混合持久化（Redis 4.0+）
- Agent 场景选型建议
- 核心机制：fork 子进程 + COW（写时复制），主进程继续处理请求
- 触发条件：save/bgsave 手动触发、满足 save 规则自动触发、shutdown 时触发

**2️⃣ Impressive Answer**

Redis 持久化是**数据安全与性能的权衡艺术**，在 Agent 场景中会话状态持久化选型尤为关键：

1. **RDB：快照持久化**

  - 核心机制：fork 子进程 + COW（写时复制），主进程继续处理请求

  - 触发条件：save/bgsave 手动触发、满足 save 规则自动触发、shutdown 时触发

  - 优点：恢复速度快、文件紧凑、适合备份

  - 缺点：fork 时内存翻倍、可能丢失最后一次快照后数据

1. **AOF：追加日志持久化**

  - 核心机制：记录每个写命令到 AOF 缓冲区，根据策略 fsync 到磁盘

  - 三种 fsync 策略：

    - always：每个写都 fsync，数据最安全但性能最差

    - everysec：每秒 fsync（默认），平衡数据安全与性能

    - no：由操作系统决定，性能最好但可能丢失较多数据

  - AOF 重写：fork 子进程压缩 AOF 文件，去除冗余命令

1. **混合持久化（Redis 4.0+）**

  - 工作原理：AOF 重写时，先以 RDB 格式写入基础数据，再追加增量 AOF 日志

  - 优势：兼顾 RDB 的恢复速度和 AOF 的数据安全

  - 文件结构：RDB 头部

1. **Agent 场景选型建议**

  - 会话状态：优先混合持久化，兼顾恢复速度和数据安全

  - 配置信息：RDB 足够，重启恢复快

  - 关键业务数据：AOF + everysec 策略，确保数据不丢失

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
简单列举 RDB 和 AOF
</td>
<td>
系统性对比机制、策略、适用场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
未涉及 fork/COW/AOF 重写原理
</td>
<td>
深入底层机制（COW、fsync 策略、混合持久化）
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无场景化选型建议
</td>
<td>
结合 Agent 场景提供会话、配置、业务数据选型
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
基础概念掌握，但缺乏深度
</td>
<td>
架构级理解，能结合场景做技术决策
</td>
</tr>
</table>

---

#### 3、进阶题：Redis 内存淘汰策略有哪些？在 Agent 场景如何选择？

**难度级别**：⭐⭐⭐（8种淘汰策略、LRU vs LFU、maxmemory配置、volatile vs allkeys）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 淘汰范围：volatile vs allkeys
- 淘汰算法：LRU vs LFU
- Agent 场景选型
- volatile 系列：只淘汰设置了 TTL 的 key
- volatile-lru：从过期 key 中淘汰最少使用的
- volatile-lfu：从过期 key 中淘汰访问频率最低的

**2️⃣ Impressive Answer**

内存淘汰是 Redis 的**保命机制**，当内存达到 maxmemory 限制时触发，选型要从**淘汰范围和淘汰算法**两个维度考虑：

1. **淘汰范围：volatile vs allkeys**

  - **volatile 系列**：只淘汰设置了 TTL 的 key

    - volatile-lru：从过期 key 中淘汰最少使用的

    - volatile-lfu：从过期 key 中淘汰访问频率最低的

    - volatile-ttl：淘汰即将过期的 key（TTL 最小的）

    - volatile-random：随机淘汰过期 key

  - **allkeys 系列**：淘汰所有 key（包括未设置 TTL 的）

    - allkeys-lru：淘汰所有 key 中最少使用的

    - allkeys-lfu：淘汰所有 key 中访问频率最低的

    - allkeys-random：随机淘汰 key

  - **noeviction**：不淘汰，内存满时直接返回错误

1. **淘汰算法：LRU vs LFU**

  - **LRU（Least Recently Used）**：基于最近访问时间，适合热点数据

    - Redis 使用近似 LRU（随机采样），不是精确 LRU

    - 优点：实现简单，适合大部分场景

    - 缺点：无法区分访问频率（一次访问和频繁访问权重相同）

  - **LFU（Least Frequently Used）**：基于访问频率，适合长期热点

    - Redis 4.0+ 支持，使用计数器 + 衰减机制

    - 优点：能识别真正热点，避免缓存污染

    - 缺点：需要维护计数器，内存开销略大

1. **Agent 场景选型**

  - **会话缓存（短 TTL、高并发）**：`allkeys-lru` 或 `allkeys-lfu`

    - 原因：会话数据都有 TTL，但内存压力大时需要淘汰

    - LFU 更适合识别活跃用户，LRU 适合一般场景

  - **模型配置缓存（长 TTL、读多写少）**：`volatile-lru`

    - 原因：配置数据不会设置 TTL（永久缓存），用 allkeys 可能误删

    - 配合主动失效机制，只在内存压力时淘汰过期 key

  - **知识库文档缓存（中等 TTL、访问不均）**：`allkeys-lfu`

    - 原因：文档访问频率差异大，LFU 能识别真正热点

    - 避免冷数据频繁加载影响性能

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
简单列举策略名，无分类逻辑
</td>
<td>
从淘汰范围→淘汰算法→场景选型三层
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 volatile vs allkeys 区别、LRU vs LFU 差异
</td>
<td>
明确近似 LRU、LFU 衰减机制、maxmemory 配置
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体场景分析
</td>
<td>
结合 Agent 会话、配置、知识库给出差异化建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道名字但不会选
</td>
<td>
有决策框架，能根据业务特性做技术选型
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
RDB 和 AOF 持久化
</td>
<td>
持久化失败时内存压力如何缓解
</td>
<td>
答：RDB：快照持久化；AOF：追加日志持久化；混合持久化（Redis 4.0+）；Agent 场景选型建议
</td>
</tr>
<tr>
<td>
Redis 6.0 多线程模型
</td>
<td>
单线程变为多线程后持久化机制是否变化
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
主从复制中的持久化角色
</td>
<td>
主从持久化策略如何配合
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：主从持久化策略如何配合，最后补一个风险点或优化手段。
</td>
</tr>
<tr>
<td>
缓存穿透、击穿、雪崩
</td>
<td>
内存淘汰与缓存问题的联动防护
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
</table>

---

## 缓存穿透、击穿与雪崩

#### 1、基础题：什么是缓存穿透、击穿、雪崩？

**难度级别**：⭐⭐（三者定义和区别）

---

#### 2、进阶题：在 Agent 高并发场景下，如何系统性防护缓存穿透、击穿和雪崩？

**难度级别**：⭐⭐⭐⭐（布隆过滤器、互斥锁、随机TTL、热点Key探测、多级缓存、降级策略）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 穿透防护：防止无效请求打到数据库
- 击穿防护：防止热点 key 失效瞬间大量请求打到数据库
- 雪崩防护：防止大量 key 同时失效
- Agent 场景实战
- 布隆过滤器：基于位数组 + 多个哈希函数，快速判断 key 是否可能存在（0.81% 误判率）
- 优点：内存占用小（12KB 固定内存）、查询速度快

**2️⃣ Impressive Answer**

缓存三高问题是**高并发系统的必考题**，在 Agent 场景中知识库缓存、模型配置缓存都需要系统性防护：

1. **穿透防护：防止无效请求打到数据库**

  - 布隆过滤器：基于位数组 + 多个哈希函数，快速判断 key 是否可能存在（0.81% 误判率）

    - 优点：内存占用小（12KB 固定内存）、查询速度快

    - 缺点：不支持删除、存在误判

  - 空值缓存：对不存在的 key 缓存 null 值，设置较短的 TTL（如 30 秒）

  - 参数校验前置：在 Agent 请求入口层做参数合法性校验，拦截明显无效请求

1. **击穿防护：防止热点 key 失效瞬间大量请求打到数据库**

  - 互斥锁：使用 Redis 的 setnx 或分布式锁，只允许一个线程回源

    - 实现：`set key value NX PX 30000`，其他线程等待或快速失败

  - 逻辑过期：缓存不设置 TTL，在 value 中包含过期时间，异步刷新

  - 热点 Key 预加载：Agent 启动时预加载热门模型配置、知识库热点内容

1. **雪崩防护：防止大量 key 同时失效**

  - 随机 TTL 打散：在基础 TTL 上增加随机值（如 TTL ± 20%）

  - 多级缓存 L1/L2：本地缓存（Caffeine/Guava）+ 分布式缓存（Redis）

    - L1：响应快，但容量小、一致性弱

    - L2：容量大、一致性好，但网络延迟

  - 熔断降级：当缓存命中率低于阈值时，触发降级策略（返回默认值或限流）

  - 集群高可用：Redis Sentinel + Cluster，避免单点故障

1. **Agent 场景实战**

  - 知识库缓存穿透防护：布隆过滤器 + 参数校验，防止恶意查询不存在的文档 ID

  - 热门 Agent 模型配置击穿防护：互斥锁 + 预加载，确保高并发下配置更新不阻塞

  - 大促场景雪崩预案：多级缓存 + 随机 TTL + 降级开关，确保服务可用性

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
简单列举三个问题和基本方案
</td>
<td>
系统性分析穿透、击穿、雪崩的根因和防护体系
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
未涉及布隆过滤器原理、多级缓存架构
</td>
<td>
深入布隆过滤器误判率、分布式锁实现、L1/L2 缓存一致性
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无场景化防护策略
</td>
<td>
结合 Agent 知识库、模型配置、大促场景提供实战方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
基础概念掌握，但缺乏系统性
</td>
<td>
具备高并发架构设计能力，能结合场景做系统性防护
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
布隆过滤器的误判率和不支持删除
</td>
<td>
穿透防护中布隆过滤器的原理和局限性
</td>
<td>
答：缓存异常要先定义现象，再讲治理：穿透用布隆过滤器/空值缓存，击穿用互斥锁/逻辑过期，雪崩用随机 TTL 和限流降级。
</td>
</tr>
<tr>
<td>
Redis 集群高可用
</td>
<td>
雪崩防护中集群架构如何提升可用性
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
缓存预热策略
</td>
<td>
击穿防护中热点 Key 如何提前加载
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
</table>

---

## Redis 高级数据结构

#### 1、基础题：Redis 除了基础数据结构，还有哪些高级数据结构？

**难度级别**：⭐⭐（HyperLogLog、Bitmap、GEO、Stream、Bloom Filter）

---

#### 2、进阶题：HyperLogLog 和 Bitmap 分别适合什么场景？精度和内存占用如何？

**难度级别**：⭐⭐⭐（基数统计、位图操作、误差率 0.81%、12KB 固定内存）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- HyperLogLog：基数统计（去重计数）
- Bitmap：位图操作（布尔状态）
- Agent 场景实践
- 核心算法：基于概率的 Cardinality 估算，误差率约 0.81%
- 内存占用：固定 12KB（与数据量无关）
- API：PFADD 添加、PFCOUNT 计数、PFMERGE 合并

**2️⃣ Impressive Answer**

两者定位完全不同，选型要从**数据特性和精度要求**判断：

1. **HyperLogLog：基数统计（去重计数）**

  - 核心算法：基于概率的 Cardinality 估算，误差率约 0.81%

  - 内存占用：固定 12KB（与数据量无关）

  - API：`PFADD` 添加、`PFCOUNT` 计数、`PFMERGE` 合并

  - 适用场景：UV 统计、Agent 日活用户数、去重 Token 计数

  - 不适用：需要精确值、需要知道具体有哪些元素

1. **Bitmap：位图操作（布尔状态）**

  - 核心特性：用 bit 表示状态（0/1），支持 AND/OR/XOR/NOT 等位运算

  - 内存占用：N 个元素需要 N bits（如 100 万用户 = 125KB）

  - API：`SETBIT`/`GETBIT`、`BITCOUNT`、`BITOP`

  - 适用场景：用户签到、在线状态、权限标记、Agent 功能开关

  - 不适用：稀疏数据（元素 ID 跨度大，浪费空间）

1. **Agent 场景实践**

  - HyperLogLog：统计每个 Agent 的日活（DAU），合并多租户数据用 `PFMERGE`

  - Bitmap：用户连续签到（`BITCOUNT` 统计天数）、功能灰度开关（bit 位表示用户群）

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
简单对比，无具体数据
</td>
<td>
从算法、内存、API、场景四层展开
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道误差率和固定内存
</td>
<td>
明确 0.81% 误差和 12KB 固定占用
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
结合 DAU 统计、签到、灰度给出实例
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道名字但不会用
</td>
<td>
有数据支撑，能直接落地
</td>
</tr>
</table>

---

#### 3、进阶题：Redis Stream 如何实现消息队列？和 Kafka 有什么区别？

**难度级别**：⭐⭐⭐（XADD/XREAD/XREADGROUP、消费者组、ACK机制、持久化、与Kafka对比）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 核心 API 与机制
- Agent 场景选型
- XADD：向 Stream 添加消息，返回唯一的消息 ID（时间戳 + 序列号）
- XADD mystream * field1 value1 field2 value2
- 自动生成 ID 或手动指定（必须大于上一个 ID）
- XREAD/XREADGROUP：读取消息

**2️⃣ Impressive Answer**

Redis Stream 是 Redis 的**轻量级消息队列**，适合中小规模场景，选型要从**架构复杂度和功能完整性**两个维度考虑：

1. **核心 API 与机制**

  - **XADD**：向 Stream 添加消息，返回唯一的消息 ID（时间戳 + 序列号）

    - `XADD mystream * field1 value1 field2 value2`

    - 自动生成 ID 或手动指定（必须大于上一个 ID）

  - **XREAD/XREADGROUP**：读取消息

    - XREAD：独立消费者，从指定 ID 开始读取

    - XREADGROUP：消费者组模式，支持负载均衡和 ACK 机制

  - **消费者组（Consumer Group）**：

    - 一个 Stream 可创建多个消费者组

    - 组内消费者竞争消费，每个消息只能被组内一个消费者处理

    - 支持pending list（未确认消息）和消息重试

  - **ACK 机制**：`XACK` 确认消息已处理，否则消息会保留在 pending list

  - **持久化**：Stream 数据写入 RDB/AOF，重启后不丢失

1. **Redis Stream vs Kafka 对比** | 维度 | Redis Stream | Kafka || --- | --- | --- || 架构复杂度 | ✅ 简单，依赖 Redis | ❌ 复杂，需独立集群（Broker/Zookeeper/KRaft） || 性能 | 中等（单线程） | 高（多线程 + 零拷贝） || 吞吐量 | 10万级/秒 | 百万级/秒 || 消息持久化 | RDB/AOF，重启恢复 | 专用日志文件，多副本 || 消息回溯 | ✅ 支持读取历史消息 | ✅ 支持重置 offset || 消费者组 | ✅ 支持 | ✅ 支持 || 消息顺序 | ✅ 单 Stream 内有序 | ✅ 单 Partition 内有序 || 生态集成 | Redis 客户端 | Kafka Connect + 多语言客户端 || 适用场景 | 中小规模、简单队列 | 大规模、高吞吐、流处理 |

1. **Agent 场景选型**

  - **Agent 任务队列（异步执行）**：Redis Stream

    - 原因：已有 Redis 基础设施，无需额外组件

    - 示例：文档解析、向量索引、异步推理任务

  - **日志收集与流处理（高吞吐）**：Kafka

    - 原因：日志量大，需要高吞吐和流处理能力

    - 示例：Agent 请求日志、用户行为埋点

  - **实时对话消息推送**：Redis Stream 或 Pub/Sub

    - 原因：低延迟、简单场景

    - 示例：多 Agent 协作消息传递

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
简单列举 API，无机制说明
</td>
<td>
从核心 API→消费者组→Kafka 对比→场景选型四层
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ACK 机制、消费者组原理
</td>
<td>
明确 pending list、消息重试、持久化机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体场景分析
</td>
<td>
用表格对比 Kafka，结合 Agent 任务队列、日志给出选型
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道名字但不会用
</td>
<td>
有技术选型框架，能根据业务特性做决策
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
Redis Bloom Filter 原理和使用场景？
</td>
<td>
同属高级数据结构，用于存在性判断
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
Redis GEO 底层用什么数据结构？如何实现附近的人？
</td>
<td>
GEO 是另一高级结构，考察地理位置场景
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
Kafka 的消息顺序和幂等性如何保证？
</td>
<td>
消息队列的进阶问题，考察分布式消息系统理解
</td>
<td>
答：幂等性指同一操作重复执行多次结果一致，Agent 场景下可用 requestId、幂等键或状态机防止重试导致重复写入。
</td>
</tr>
</table>

---

## Redis 集群与高可用

#### 1、基础题：Redis 主从复制、哨兵、Cluster 三种模式有什么区别？

**难度级别**：⭐⭐（主从同步、故障转移、数据分片）

Redis 主从复制、哨兵和 Cluster 是三种不同级别的可用性解决方案：

- **主从复制**：数据复制方案，主节点负责写，从节点负责读。主从之间异步复制，提供读写分离和数据冗余，但主节点故障需要手动切换。

- **哨兵**：高可用监控方案，在主从复制基础上增加 Sentinel 节点监控主从状态。主节点故障时自动选举新的主节点，实现故障自动转移，但仍存在单点写入瓶颈。

- **Cluster**：分布式集群方案，通过数据分片将数据分散到多个主节点，每个主节点可配置从节点。提供数据分片、故障转移、自动水平扩展能力，适合大规模数据场景。

---

#### 2、进阶题：Redis Cluster 的数据分片和故障转移机制是怎样的？

**难度级别**：⭐⭐⭐（16384槽位、一致性哈希、Gossip协议、故障检测、脑裂问题）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 数据分片机制
- 故障检测与转移
- 脑裂防护
- Agent 场景应用
- 16384 槽位：Cluster 将整个键空间划分为 16384 个 slot，每个主节点负责一部分槽位
- 槽位计算：CRC16(key) % 16384 确定键对应的 slot，保证相同 key 路由到同一节点

**2️⃣ Impressive Answer**

Redis Cluster 通过**槽位机制**实现数据分片和故障转移，核心机制包括：

1. **数据分片机制**

  - **16384 槽位**：Cluster 将整个键空间划分为 16384 个 slot，每个主节点负责一部分槽位

  - **槽位计算**：`CRC16(key) % 16384` 确定键对应的 slot，保证相同 key 路由到同一节点

  - **槽位迁移**：支持在线迁移槽位，使用 `ASKING/MOVED` 重定向机制处理迁移期间的数据访问

  - **Hash Tag**：使用 `{}` 包裹部分 key（如 `user:{1001}:profile`）强制相关数据落到同一节点，支持多 key 操作

1. **故障检测与转移**

  - **Gossip 协议**：节点间定期交换 PING/PONG 消息，维护集群拓扑状态

  - **故障检测**：节点超时未响应标记为 PFAIL（可能故障），半数以上主节点确认后升级为 FAIL（确认故障）

  - **从节点选举**：故障主节点的从节点发起选举，通过 epoch 机制保证选举唯一性，复制偏移量最大的从节点优先

  - **故障转移**：选举出的新主节点广播新配置，其他节点更新槽位映射

1. **脑裂防护**

  - **min-slaves-to-write**：主节点至少需要 N 个从节点连接才接受写操作

  - **min-slaves-max-lag**：从节点复制延迟超过指定秒数时拒绝写操作

  - 防止网络分区时旧主节点继续写入导致数据不一致

1. **Agent 场景应用**

  - **多租户 Agent 平台**：按租户 ID 使用 Hash Tag 将同一租户的会话数据路由到同一节点，避免跨节点事务

  - **会话数据优化**：热点 Agent 的会话数据可通过槽位迁移均衡负载

  - **高可用保障**：关键 Agent 状态数据配置主从热备，故障转移时间控制在秒级

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
简单描述分片和故障转移概念
</td>
<td>
系统阐述槽位机制、Gossip 协议、选举流程的完整架构
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
停留在&quot;分片+自动切换&quot;表层
</td>
<td>
深入 CRC16 算法、epoch 机制、ASK/MOVED 重定向细节
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无实际场景
</td>
<td>
结合 Agent 平台的多租户、会话管理、负载均衡实战
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基础概念，缺乏深度
</td>
<td>
掌握核心原理，有架构设计能力，能解决复杂问题
</td>
</tr>
</table>

---

#### 3、进阶题：Redis 主从复制的全量同步和增量同步机制是怎样的？

**难度级别**：⭐⭐⭐（runid、offset、repl\_backlog、PSYNC、全量RDB传输、增量命令传播）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 全量同步（首次连接或复制偏移量过大）
- 增量同步（短时间断开重连）
- 命令传播（持续同步）
- Agent 场景应用
- 触发条件：从节点首次连接主节点，或复制偏移量差距超过 repl\_backlog 大小
- 同步流程

**2️⃣ Impressive Answer**

Redis 主从复制通过**PSYNC 命令**实现，核心机制包括 runid、offset、repl\_backlog 三个关键要素：

1. **全量同步（首次连接或复制偏移量过大）**

  - **触发条件**：从节点首次连接主节点，或复制偏移量差距超过 repl\_backlog 大小

  - **同步流程**：

    1. 从节点发送 `PSYNC ? -1` 请求全量同步

    1. 主节点执行 `BGSAVE` 生成 RDB 文件（fork 子进程）

    1. 主节点将 RDB 文件发送给从节点

    1. RDB 传输期间，主节点将新写命令缓存到 replication buffer

    1. RDB 传输完成后，主节点将缓存命令发送给从节点

    1. 从节点加载 RDB 并执行缓存命令，完成数据同步

  - **缺点**：fork 子进程导致主节点内存翻倍，RDB 传输占用网络带宽

1. **增量同步（短时间断开重连）**

  - **触发条件**：从节点断开后短时间内重连，且复制偏移量在 repl\_backlog 范围内

  - **核心机制**：

    - **runid**：主节点唯一标识，从节点记录上次同步的主节点 runid

    - **offset**：复制偏移量，记录从节点同步到主节点的哪个位置

    - **repl\_backlog**：主节点的复制积压缓冲区（默认 1MB），环形队列存储最近写命令

  - **同步流程**：

    1. 从节点发送 `PSYNC <runid> <offset>` 请求增量同步

    1. 主节点检查 runid 是否匹配（不匹配则触发全量同步）

    1. 主节点检查 offset 是否在 repl\_backlog 范围内

    1. 如果在范围内，从 repl\_backlog 获取 offset 之后的所有命令发送给从节点

    1. 从节点执行命令完成增量同步

1. **命令传播（持续同步）**

  - 全量/增量同步完成后，主节点持续将写命令发送给从节点

  - 从节点执行命令并更新 offset

  - 使用心跳机制（PING/PONG）检测连接状态

1. **Agent 场景应用**

  - **会话数据同步**：主节点处理 Agent 会话写操作，从节点处理读操作，实现读写分离

  - **repl\_backlog 优化**：根据 Agent 写入频率调整 repl\_backlog 大小，避免频繁全量同步

  - **故障恢复**：从节点重启后优先尝试增量同步，减少恢复时间

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
简单描述全量/增量同步概念
</td>
<td>
系统阐述 runid、offset、repl\_backlog 三要素和完整流程
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 repl\_backlog 机制和 offset 作用
</td>
<td>
明确环形队列、复制偏移量、runid 校验细节
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无实际场景
</td>
<td>
结合 Agent 会话同步、故障恢复给出优化建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基础概念，缺乏深度
</td>
<td>
掌握核心原理，有实战优化能力
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
Redis Sentinel 的选举算法
</td>
<td>
Sentinel 和 Cluster 都涉及故障选举，对比两者选举机制差异
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
客户端如何感知集群拓扑变化
</td>
<td>
Cluster 的槽位迁移和故障转移需要客户端配合，考察客户端适配能力
</td>
<td>
答：多模态输入要先做解析和标准化，把图片、语音、文档等转成可推理的文本、结构化字段或 embedding，再交给规划模块。
</td>
</tr>
<tr>
<td>
主从切换时数据丢失如何避免？
</td>
<td>
复制延迟导致的丢失问题，考察 min-slaves 配置
</td>
<td>
答：消息可靠性要分三段讲：生产端用同步发送、确认机制和重试；Broker 端用持久化、副本和 ISR；消费端用手动提交 offset、幂等消费和失败重试，最后用监控补漏。
</td>
</tr>
</table>

---

## Redis 分布式锁

#### 1、基础题：Redis 分布式锁怎么实现？

**难度级别**：⭐⭐（SETNX + EXPIRE、原子性、超时释放）

Redis 分布式锁的基本实现是使用 `SETNX` 命令加锁，同时设置过期时间防止死锁。现代 Redis 使用 `SET key value NX EX seconds` 原子命令保证加锁和设置过期时间的原子性。释放锁时需要先判断锁是否属于自己，避免误删其他客户端的锁，通常使用 Lua 脚本保证"检查+删除"的原子性。

---

#### 2、进阶题：Redisson 看门狗机制和 RedLock 算法的原理与争议？

**难度级别**：⭐⭐⭐⭐（看门狗续期、RedLock多节点、Martin Kleppmann争议、Lua脚本原子性）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 基础实现与陷阱
- Redisson 看门狗机制
- RedLock 算法与争议
- Agent 场景应用
- 原子加锁：SET lock_key unique_value NX EX 30，unique_value 通常是 UUID + 线程 ID，用于识别锁持有者
- 非原子释放风险：先 GET 再 DEL 存在竞态条件，可能误删其他客户端的锁

**2️⃣ Impressive Answer**

Redis 分布式锁的核心是**原子性保证**和**容错机制**，Redisson 看门狗和 RedLock 是两个重要演进：

1. **基础实现与陷阱**

  - **原子加锁**：`SET lock_key unique_value NX EX 30`，`unique_value` 通常是 UUID + 线程 ID，用于识别锁持有者

  - **非原子释放风险**：先 `GET` 再 `DEL` 存在竞态条件，可能误删其他客户端的锁

  - **Lua 脚本释放**：`if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end` 保证"检查+删除"原子性

  - **超时困境**：过期时间设置过短导致业务未完成锁过期，设置过长导致故障后无法快速恢复

1. **Redisson 看门狗机制**

  - **租约模式**：默认 30 秒锁租约，看门狗线程每 10 秒检测并续期

  - **自动续期**：业务执行期间自动续期，业务完成或客户端宕机后锁自动释放

  - **续期条件**：只有锁持有者才能续期，基于 `unique_value` 校验

  - **适用场景**：执行时间不确定但可控的任务，如 Agent 工具调用、知识库索引构建

1. **RedLock 算法与争议**

  - **算法原理**：在 N 个独立 Redis 实例上同时加锁，获取到 N/2+1 个锁才算成功，释放时向所有节点解锁

  - **时钟漂移问题**：不同 Redis 节点时钟不同步可能导致锁过期时间计算偏差

  - **Martin Kleppmann 批评**：

    - RedLock 在网络分区时可能违反安全性，多个客户端同时持有锁

    - 提出使用 fencing token（递增令牌）保证操作顺序，依赖存储系统检查令牌

  - **Antirez 回应**：RedLock 的目标是"尽力而为"的可用性，适用于性能要求高于强一致性的场景

  - **实际选择**：强一致性场景选 Zookeeper/Etcd，高性能场景选 Redis 单节点锁，极端高可用场景选 RedLock

1. **Agent 场景应用**

  - **工具调用幂等控制**：Agent 调用外部 API 时使用分布式锁保证同一请求不重复执行

  - **并发任务互斥**：多 Agent 实例处理同一任务时加锁，避免重复消费消息队列

  - **知识库索引构建锁**：向量数据库索引构建期间加锁，防止并发写入导致索引损坏

  - **锁粒度设计**：租户级锁 vs 全局锁，根据业务隔离需求选择合适粒度

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
简单罗列 SETNX、看门狗、RedLock
</td>
<td>
系统阐述原子性保证、续期机制、多节点算法的完整方案
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
停留在&quot;用 SETNX 加锁&quot;表层
</td>
<td>
深入 Lua 脚本、租约续期、fencing token 争议等核心细节
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无实际场景
</td>
<td>
结合 Agent 的工具调用、并发控制、索引构建等实战经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本用法，缺乏思考
</td>
<td>
掌握原理和争议，能根据场景选择合适方案，有架构视野
</td>
</tr>
</table>

---

#### 3、进阶题：Redisson 可重入锁的实现原理？锁粒度如何设计？

**难度级别**：⭐⭐⭐（Hash结构+计数器、Lua脚本、粗粒度vs细粒度、锁竞争优化）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 可重入锁实现原理
- 锁粒度设计原则
- Agent 场景锁粒度设计
- 数据结构：使用 Redis Hash 存储锁信息\HSET lock:resource ``
- lock:resource：锁名称
- ``：线程唯一标识（UUID + 线程 ID）

**2️⃣ Impressive Answer**

Redisson 可重入锁的核心是**Hash 结构 + 计数器 + Lua 脚本**，锁粒度设计需要平衡并发控制和性能：

1. **可重入锁实现原理**

  - **数据结构**：使用 Redis Hash 存储锁信息`\`HSET lock:resource <threadId> <count>``

    - `lock:resource`：锁名称

    - `<threadId>`：线程唯一标识（UUID + 线程 ID）

    - `<count>`：重入次数计数器

  - **加锁流程（Lua 脚本保证原子性）**：`\`luaif redis.call('exists', KEYS\[1\]) ==0 or redis.call('hexists', KEYS\[1\], ARGV\[2\])== 1 thenredis.call('hincrby', KEYS\[1\], ARGV\[2\], 1)redis.call('pexpire', KEYS\[1\], ARGV\[1\])return 1elsereturn 0end``

    - 如果锁不存在或当前线程已持有锁，计数器 +1 并续期

    - 否则加锁失败

  - **解锁流程（Lua 脚本保证原子性）**：`\`luaif redis.call('hexists', KEYS\[1\], ARGV\[2\]) == 1 thenlocal count = redis.call('hincrby', KEYS\[1\], ARGV\[2\], -1)if count == 0 thenredis.call('del', KEYS\[1\])endreturn 1elsereturn 0end``

    - 计数器 -1，减到 0 时删除锁

1. **锁粒度设计原则**

  - **粗粒度锁**：锁的范围大，如用户级锁、订单级锁

    - 优点：实现简单，锁竞争少

    - 缺点：并发度低，容易阻塞

    - 适用场景：低并发、业务逻辑简单的场景

  - **细粒度锁**：锁的范围小，如订单项锁、库存 SKU 锁

    - 优点：并发度高，性能好

    - 缺点：实现复杂，容易死锁，锁竞争多

    - 适用场景：高并发、需要精细控制的场景

  - **锁粒度选择矩阵**： | 维度 | 粗粒度锁 | 细粒度锁 || --- | --- | --- || 并发度 | 低 | 高 || 实现复杂度 | 简单 | 复杂 || 死锁风险 | 低 | 高 || 适用场景 | 低并发、简单业务 | 高并发、复杂业务 |

1. **Agent 场景锁粒度设计**

  - **用户会话锁（粗粒度）**：`lock:session:<userId>`，同一用户的会话操作串行化

    - 原因：用户操作频率低，粗粒度锁足够

  - **知识库文档锁（中粒度）**：`lock:doc:<docId>`，同一文档的索引/更新操作互斥

    - 原因：文档操作中等频率，需要避免并发冲突

  - **工具调用锁（细粒度）**：`lock:tool:<toolName>:<userId>`，同一用户调用同一工具时互斥

    - 原因：工具调用高频，细粒度锁提升并发度

  - **库存扣减锁（超细粒度）**：`lock:stock:<skuId>`，SKU 级别锁，避免超卖

    - 原因：电商场景高并发，必须精细控制

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
简单描述 Hash + 计数器
</td>
<td>
系统阐述数据结构、Lua 脚本、锁粒度设计原则
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Lua 脚本原子性保证
</td>
<td>
明确加锁/解锁流程、计数器机制、死锁风险
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体场景
</td>
<td>
用锁粒度矩阵对比，结合 Agent 场景给出设计建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道可重入锁概念
</td>
<td>
掌握实现原理，有锁粒度设计能力，能平衡并发与性能
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
Zookeeper 分布式锁 vs Redis 分布式锁
</td>
<td>
对比两种实现的 CP/AP 特性，考察一致性 vs 性能的权衡
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
分布式锁的可重入性实现
</td>
<td>
Redisson 的可重入锁通过 Hash 结构 + 计数器实现，考察锁的进阶特性
</td>
<td>
答：缓存题围绕命中率、一致性、过期策略和故障保护来答；高频风险是穿透、击穿、雪崩、热 key 和大 key。
</td>
</tr>
<tr>
<td>
锁粒度设计
</td>
<td>
粗粒度锁 vs 细粒度锁，考察并发控制和性能优化的平衡
</td>
<td>
答：成本优化先拆 Token、模型、工具和重试四类开销，再用缓存、小模型路由、Prompt 压缩、批处理和限流降级优化。
</td>
</tr>
</table>

---

## X.X Redis 基础数据结构底层实现

#### 1、基础题：Redis 的 5 种基础数据类型底层编码分别是什么？

难度：⭐⭐（String/List/Hash/Set/ZSet的底层编码，ziplist/listpack/skiplist/hashtable/intset）
直接给答案：

- String：int（整数）、embstr（≤44字节）、raw（>44字节）

- List：listpack（元素少且小）、quicklist（元素多，双向链表+listpack节点）

- Hash：listpack（元素≤128且值≤64字节）、hashtable（超出阈值）

- Set：intset（全整数且≤512）、listpack（元素≤128且值≤64字节）、hashtable（超出阈值）

- ZSet：listpack（元素≤128且值≤64字节）、skiplist+hashtable（超出阈值）

#### 2、进阶题：ZSet 为什么同时用 ziplist/listpack 和 skiplist？跳表的查询复杂度如何保证？

难度：⭐⭐⭐⭐（ziplist省内存、skiplist支持范围查询、hashtable O(1)查分、跳表层级概率）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- ZSet双结构设计原因
- 跳表复杂度保证
- skiplist：支持按score范围查询（ZRANGEBYSCORE），O(logN)复杂度
- hashtable：支持按member查score（ZSCORE），O(1)复杂度
- 两者共享member对象（指针引用），内存开销可控
- 层级随机生成：每个节点以50%概率晋升到上一层，期望层数O(logN)

**2️⃣ Impressive Answer**

1. ZSet双结构设计原因：

  - skiplist：支持按score范围查询（ZRANGEBYSCORE），O(logN)复杂度

  - hashtable：支持按member查score（ZSCORE），O(1)复杂度

  - 两者共享member对象（指针引用），内存开销可控

1. 小数据量用listpack（ziplist）：元素少时，listpack连续内存布局，CPU缓存友好，内存占用远小于skiplist

1. 跳表复杂度保证：

  - 层级随机生成：每个节点以50%概率晋升到上一层，期望层数O(logN)

  - 查询路径：从最高层开始，逐层向右向下，期望比较次数O(logN)

  - 最大层数：Redis默认32层，支持2^32个元素

1. 跳表 vs 红黑树：跳表实现简单、支持范围查询（红黑树需要中序遍历）、并发友好（锁粒度更细）

1. Agent场景：模型调用排行榜用ZSet，ZADD O(logN)更新分数，ZREVRANGE O(logN+M)获取Top N

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
只知道用跳表
</td>
<td>
明确skiplist+hashtable双结构设计，理解共享对象机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道复杂度保证原理
</td>
<td>
掌握跳表层级概率分布、查询路径优化、最大层数限制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体场景
</td>
<td>
结合Agent排行榜场景，给出ZADD/ZREVRANGE性能优化方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基础数据结构
</td>
<td>
深入理解底层实现，能分析复杂度，有工程实践能力
</td>
</tr>
</table>

---

#### 3、场景题：Agent 排行榜（模型调用次数 Top N）如何用 ZSet 高效实现？

难度：⭐⭐⭐（ZADD/ZINCRBY/ZREVRANGE、分页、实时更新）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 数据结构设计
- 核心操作
- 性能优化
- Key：model:call:rank:daily:{date}（按天分榜）
- Member：model_id
- Score：调用次数

**2️⃣ Impressive Answer**

1. 数据结构设计：

  - Key：model:call:rank:daily:{date}（按天分榜）

  - Member：model_id

  - Score：调用次数

1. 核心操作：

  - 调用时：ZINCRBY model:call:rank:daily:20240101 1 gpt-4（原子自增）

  - 查Top N：ZREVRANGEBYSCORE model:call:rank:daily:20240101 +inf -inf WITHSCORES LIMIT 0 10

  - 查某模型排名：ZREVRANK model:call:rank:daily:20240101 gpt-4

1. 性能优化：

  - 写入：批量调用用Pipeline，减少网络RTT

  - 过期：设置TTL自动清理历史榜单（EXPIRE key 86400）

  - 分页：ZREVRANGE key start stop WITHSCORES，游标分页

1. 多维度排行：按天/周/月分别维护ZSet，定时任务汇总周榜月榜

1. 防刷：结合Lua脚本实现调用频率限制，防止单个用户刷高排名

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
简单使用ZADD/ZREVRANGE
</td>
<td>
系统设计Key命名规范、数据结构、核心操作流程
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道分页、过期策略
</td>
<td>
掌握Pipeline批量操作、TTL自动清理、游标分页技术
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无性能优化方案
</td>
<td>
给出多维度排行、防刷、性能优化完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道ZSet基本用法
</td>
<td>
能设计完整排行榜系统，考虑性能、扩展性、防刷
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
listpack vs ziplist的区别（Redis 7.0后listpack替代ziplist）
</td>
<td>
考察Redis数据结构的演进和内存优化策略
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
跳表与B+树的对比
</td>
<td>
考察范围查询数据结构的选择，跳表适合内存，B+树适合磁盘
</td>
<td>
答：MySQL 题要从数据结构、事务隔离、锁/MVCC、执行计划和慢 SQL 优化展开；最后落到 explain、索引设计和业务一致性。
</td>
</tr>
</table>

---

## X.X Redis 过期策略与内存管理

#### 1、基础题：Redis 的 key 过期删除策略有哪些？

难度：⭐⭐（惰性删除、定期删除、主动扫描）
直接给答案：

- 惰性删除：访问key时检查是否过期，过期则删除。CPU友好但内存不友好（过期key不访问就不删）

- 定期删除：每隔100ms随机抽取部分设置了过期时间的key检查删除。平衡CPU和内存

- Redis同时使用两种策略：定期删除兜底，惰性删除精确清理

#### 2、进阶题：大量 key 同时过期会有什么问题？如何避免过期扫描阻塞主线程？

难度：⭐⭐⭐（过期扫描时间限制、随机过期时间、lazy-free异步删除）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 问题分析
- 解决方案
- 定期删除每次最多扫描25%的过期key，如果过期key比例超过25%，会持续扫描直到比例降低
- 大量key同时过期时，定期删除占用大量CPU时间，导致其他命令延迟升高
- 大key过期时，同步删除耗时长（如删除一个有10万元素的Hash），阻塞主线程
- 随机过期时间：TTL = base_ttl + random(0, jitter)，分散过期时间，避免集中过期

**2️⃣ Impressive Answer**

1. 问题分析：

  - 定期删除每次最多扫描25%的过期key，如果过期key比例超过25%，会持续扫描直到比例降低

  - 大量key同时过期时，定期删除占用大量CPU时间，导致其他命令延迟升高

  - 大key过期时，同步删除耗时长（如删除一个有10万元素的Hash），阻塞主线程

1. 解决方案：

  - 随机过期时间：TTL = base_ttl + random(0, jitter)，分散过期时间，避免集中过期

  - lazy-free异步删除：配置lazyfree-lazy-expire yes，过期key异步删除，不阻塞主线程

  - 大key拆分：将大key拆分为多个小key，单个key删除耗时可控

  - 主动扫描限速：hz参数控制定期删除频率（默认10次/秒），避免过度占用CPU

1. 监控：通过INFO stats的expired_keys指标监控过期删除速率，异常时告警

1. Agent场景：Agent会话TTL统一设置为1小时，但加±5分钟随机抖动，避免整点大量会话同时过期

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
知道要加随机数
</td>
<td>
系统分析过期策略原理、阻塞原因、多维度解决方案
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道lazy-free机制
</td>
<td>
掌握定期删除25%阈值、异步删除、大key拆分技术
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无监控方案
</td>
<td>
结合Agent会话场景，给出TTL抖动、监控告警完整方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本问题
</td>
<td>
深入理解Redis内存管理，能设计过期策略，有生产经验
</td>
</tr>
</table>

---

#### 3、场景题：Agent 会话 TTL 管理中，如何设计过期策略避免内存突增？

难度：⭐⭐⭐（TTL设计、内存预算、过期通知）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- TTL分层设计
- 内存预算控制
- 活跃会话：TTL=2小时，每次交互时EXPIRE续期（滑动过期）
- 非活跃会话：TTL=24小时，超过24小时无交互自动清理
- 历史会话摘要：TTL=7天，保留最近会话的摘要信息
- 预估单会话内存：消息列表（平均10条×500字节）+ 元数据 ≈ 10KB

**2️⃣ Impressive Answer**

1. TTL分层设计：

  - 活跃会话：TTL=2小时，每次交互时EXPIRE续期（滑动过期）

  - 非活跃会话：TTL=24小时，超过24小时无交互自动清理

  - 历史会话摘要：TTL=7天，保留最近会话的摘要信息

1. 内存预算控制：

  - 预估单会话内存：消息列表（平均10条×500字节）+ 元数据 ≈ 10KB

  - 设置maxmemory和maxmemory-policy（allkeys-lru），超出内存上限时淘汰最久未使用的会话

1. 过期通知：开启notify-keyspace-events Ex，监听会话过期事件，触发会话数据归档到MySQL

1. 随机抖动：TTL = 7200 + random(-300, 300)，避免大量会话同时过期

1. 内存监控：定期执行MEMORY USAGE key检查大会话，超过阈值告警并触发压缩

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
简单设置TTL
</td>
<td>
设计TTL分层策略、内存预算、过期通知完整体系
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道内存淘汰策略
</td>
<td>
掌握maxmemory-policy、MEMORY USAGE、过期通知技术
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体场景
</td>
<td>
结合Agent会话管理，给出分层TTL、监控、归档方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道基本TTL用法
</td>
<td>
能设计完整会话生命周期管理，考虑内存、性能、可观测性
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
Redis内存淘汰策略（LRU/LFU/TTL）
</td>
<td>
考察内存不足时的淘汰策略，与过期策略配合使用
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
keyspace notification的使用场景
</td>
<td>
考察过期事件通知机制，用于触发异步业务逻辑
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：考察过期事件通知机制，用于触发异步业务逻辑，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

## X.X Redis 6.0 多线程模型

#### 1、基础题：Redis 6.0 引入多线程解决了什么问题？哪些操作是多线程的？

难度：⭐⭐（网络IO瓶颈、多线程IO、命令执行仍单线程）
直接给答案：

- 解决的问题：Redis单线程在高并发下，网络IO（读取请求、发送响应）成为瓶颈，CPU利用率低

- 多线程的操作：网络数据读取（read）、请求解析、响应数据写入（write）

- 仍是单线程的：命令执行（保证原子性和数据一致性）

#### 2、进阶题：Redis 多线程 IO 模型和单线程命令执行如何协作？为什么命令执行仍是单线程？

难度：⭐⭐⭐⭐（IO线程池、主线程协调、无锁设计、原子性保证）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 多线程IO协作流程
- 为什么命令执行仍是单线程
- 主线程accept新连接，分配给IO线程
- IO线程并发读取socket数据，解析请求
- 主线程统一执行所有命令（单线程，保证原子性）
- IO线程并发将响应数据写回socket

**2️⃣ Impressive Answer**

1. 多线程IO协作流程：

  - 主线程accept新连接，分配给IO线程

  - IO线程并发读取socket数据，解析请求

  - 主线程统一执行所有命令（单线程，保证原子性）

  - IO线程并发将响应数据写回socket

1. 为什么命令执行仍是单线程：

  - 避免锁竞争：多线程访问共享数据结构需要加锁，锁竞争开销可能超过多线程收益

  - 原子性保证：单线程天然保证命令原子执行，无需额外同步机制

  - 简化实现：Redis的数据结构（dict、skiplist等）均非线程安全，改造成本极高

  - 瓶颈不在CPU：Redis的性能瓶颈主要在网络IO，而非命令执行的CPU计算

1. 性能提升：多线程IO在高并发小包场景下，吞吐量可提升2-3倍

1. 配置：io-threads 4（IO线程数，建议=CPU核数/2），io-threads-do-reads yes

1. Agent场景：Agent平台高并发查询Redis时，多线程IO显著降低网络延迟，提升整体吞吐量

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
知道多线程IO
</td>
<td>
系统阐述IO线程池、主线程协调、无锁设计协作流程
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道为什么命令执行单线程
</td>
<td>
深入分析锁竞争、原子性、实现复杂度、瓶颈定位
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无配置建议
</td>
<td>
给出io-threads配置建议，结合Agent场景评估性能提升
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解多线程IO概念
</td>
<td>
掌握Redis多线程模型原理，能分析性能瓶颈，有配置经验
</td>
</tr>
</table>

---

#### 3、场景题：Agent 高并发场景下，Redis 6.0 多线程能带来多少性能提升？如何评估？

难度：⭐⭐⭐（benchmark测试、吞吐量对比、适用场景判断）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 性能提升场景
- 评估方法
- Agent场景评估
- 高并发小包（<1KB）：多线程IO收益最大，吞吐量提升2-3倍
- 大包或复杂命令：命令执行是瓶颈，多线程IO收益有限
- 网络带宽受限：多线程IO无法突破带宽上限

**2️⃣ Impressive Answer**

1. 性能提升场景：

  - 高并发小包（<1KB）：多线程IO收益最大，吞吐量提升2-3倍

  - 大包或复杂命令：命令执行是瓶颈，多线程IO收益有限

  - 网络带宽受限：多线程IO无法突破带宽上限

1. 评估方法：

  - 基准测试：redis-benchmark -t get,set -n 1000000 -c 200 --threads 4

  - 对比指标：QPS（每秒请求数）、P99延迟、CPU利用率

  - 监控：INFO stats的instantaneous*ops*per*sec、INFO clients的connected*clients

1. Agent场景评估：

  - Agent会话查询（GET/HGETALL）：高频小包，多线程IO收益显著

  - 知识库向量检索（大数据量返回）：网络IO是瓶颈，多线程IO有帮助

  - Lua脚本执行（Token扣减）：命令执行是瓶颈，多线程IO收益有限

1. 配置建议：io-threads设置为CPU核数的一半（如8核CPU设置4个IO线程），避免线程切换开销

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
简单认为多线程快
</td>
<td>
分析性能提升场景、评估方法、适用条件
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道benchmark方法
</td>
<td>
掌握redis-benchmark、QPS/P99指标、INFO监控命令
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无配置建议
</td>
<td>
结合Agent场景评估，给出io-threads配置建议
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解多线程概念
</td>
<td>
能评估性能提升，掌握benchmark方法，有配置经验
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
Redis单线程为什么这么快（内存操作、IO多路复用）
</td>
<td>
考察Redis单线程的性能优势，与多线程模型形成对比
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
Redis 7.0的多线程改进
</td>
<td>
考察Redis多线程模型的演进，了解最新版本优化
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
</table>

---

## X.X Redis Pipeline 与事务

#### 1、基础题：Redis Pipeline 和普通命令有什么区别？MULTI/EXEC 事务是什么？

难度：⭐⭐（批量发送、RTT优化、MULTI/EXEC原子性）
直接给答案：

- Pipeline：将多个命令批量打包发送，一次网络往返执行多个命令，减少RTT（网络往返时间）。注意：Pipeline不保证原子性，命令之间可能被其他客户端命令插入

- MULTI/EXEC事务：MULTI开启事务，命令入队，EXEC统一执行。保证命令顺序执行，执行期间不会被其他命令插入，但不支持回滚

#### 2、进阶题：Redis 事务和 Lua 脚本的区别？为什么 Redis 事务不支持回滚？

难度：⭐⭐⭐⭐（MULTI/EXEC原子性局限、WATCH乐观锁、Lua原子性、错误处理）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Redis事务（MULTI/EXEC）特点
- 为什么不支持回滚
- Lua脚本优势
- 命令入队阶段：语法错误会导致整个事务取消
- 执行阶段：运行时错误（如对String执行LPUSH）不会回滚，其他命令继续执行
- WATCH：乐观锁，监听key变化，如果EXEC前key被修改，事务取消（返回nil）

**2️⃣ Impressive Answer**

1. Redis事务（MULTI/EXEC）特点：

  - 命令入队阶段：语法错误会导致整个事务取消

  - 执行阶段：运行时错误（如对String执行LPUSH）不会回滚，其他命令继续执行

  - WATCH：乐观锁，监听key变化，如果EXEC前key被修改，事务取消（返回nil）

1. 为什么不支持回滚：

  - Redis认为运行时错误是编程错误（类型操作错误），不应该在生产环境发生

  - 支持回滚需要记录undo log，增加复杂度和内存开销，违背Redis简单高效的设计哲学

1. Lua脚本优势：

  - 原子性更强：Lua脚本在执行期间不会被其他命令插入（类似单个命令）

  - 支持条件逻辑：可以在脚本中做if/else判断，实现复杂的原子操作

  - 减少网络往返：多个操作在服务端一次完成

1. 选型建议：简单批量操作→Pipeline；需要原子性的复杂逻辑→Lua脚本；简单原子操作→MULTI/EXEC+WATCH

1. Agent场景：Token扣减（先查余额再扣减）必须用Lua脚本保证原子性，避免并发超扣

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
简单对比事务和Lua
</td>
<td>
系统分析MULTI/EXEC特点、WATCH机制、Lua脚本优势
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道为什么不支持回滚
</td>
<td>
深入理解Redis设计哲学、undo log开销、错误处理策略
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
给出Pipeline/Lua/事务选型建议，结合Agent Token扣减场景
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解事务和Lua
</td>
<td>
掌握Redis原子性机制，能设计并发安全方案，有选型能力
</td>
</tr>
</table>

---

#### 3、场景题：Agent Token 计费场景，如何用 Lua 脚本保证扣减原子性？

难度：⭐⭐⭐（Lua脚本原子性、余额不足处理、并发安全）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Lua脚本设计
- `lua -- KEYS[1]: token:balance:{user_id} -- ARGV[1]: 扣减数量 local balance = tonumber(redis...
- 调用方式：EVALSHA script_sha 1 token:balance:user123 100
- 脚本预加载：使用SCRIPT LOAD预加载脚本，获取SHA，后续用EVALSHA调用，避免每次传输脚本
- 错误处理：返回-1（key不存在，需初始化）、-2（余额不足，拒绝请求）、正数（扣减后余额）
- 幂等性：结合请求ID（request_id）做幂等，同一请求重复调用不重复扣减

**2️⃣ Impressive Answer**

1. Lua脚本设计：

```lua
-- KEYS[1]: token:balance:{user_id}
-- ARGV[1]: 扣减数量
local balance = tonumber(redis.call('GET', KEYS[1]))
if balance == nil then
    return -1  -- key不存在
end
if balance < tonumber(ARGV[1]) then
    return -2  -- 余额不足
end
redis.call('DECRBY', KEYS[1], ARGV[1])
return redis.call('GET', KEYS[1])  -- 返回扣减后余额
```

1. 调用方式：EVALSHA script_sha 1 token:balance:user123 100

1. 脚本预加载：使用SCRIPT LOAD预加载脚本，获取SHA，后续用EVALSHA调用，避免每次传输脚本

1. 错误处理：返回-1（key不存在，需初始化）、-2（余额不足，拒绝请求）、正数（扣减后余额）

1. 幂等性：结合请求ID（request_id）做幂等，同一请求重复调用不重复扣减

1. 降级方案：Redis不可用时，降级到MySQL事务扣减（SELECT FOR UPDATE），保证数据一致性

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
简单使用Lua脚本
</td>
<td>
完整设计Lua脚本逻辑、调用方式、错误处理、幂等性
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道EVALSHA优化
</td>
<td>
掌握脚本预加载、SHA调用、降级方案、并发安全机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体场景
</td>
<td>
结合Agent Token计费，给出完整扣减方案，考虑边界情况
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解Lua脚本
</td>
<td>
能设计原子性计费方案，掌握Lua脚本最佳实践，有生产经验
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
Redis WATCH与乐观锁的实现
</td>
<td>
考察乐观锁机制，与Lua脚本原子性形成对比
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
Lua脚本的超时处理（lua-time-limit）
</td>
<td>
考察Lua脚本的异常处理，避免长时间运行阻塞
</td>
<td>
答：这题可以按“定义 → 核心机制 → 工程落地”三步答；结合本题重点强调：考察Lua脚本的异常处理，避免长时间运行阻塞，最后补一个风险点或优化手段。
</td>
</tr>
</table>

---

## X.X Redis 热 Key 与大 Key 问题

#### 1、基础题：什么是热 Key 和大 Key？会带来什么问题？

难度：⭐⭐（定义、问题影响、单点瓶颈）
直接给答案：

- 热Key：某个key被极高频率访问（如QPS>10万），导致该key所在的Redis节点CPU/网络成为瓶颈，其他key的访问也受影响

- 大Key：key对应的value体积很大（String>10KB，集合类型元素>10000），导致：读写耗时长、网络传输慢、内存分配/释放时阻塞主线程、集群迁移困难

#### 2、进阶题：热 Key 的发现方式有哪些？大 Key 如何拆分和迁移？

难度：⭐⭐⭐⭐（monitor命令、hotkeys参数、大key扫描、渐进式迁移）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 热Key发现方式
- 热Key解决方案
- 大Key发现
- 大Key拆分
- redis-cli --hotkeys：基于LFU策略统计访问频率（需要maxmemory-policy设置为LFU类型）
- MONITOR命令：实时监控所有命令，统计key访问频率（生产慎用，性能影响大）

**2️⃣ Impressive Answer**

1. 热Key发现方式：

  - redis-cli --hotkeys：基于LFU策略统计访问频率（需要maxmemory-policy设置为LFU类型）

  - MONITOR命令：实时监控所有命令，统计key访问频率（生产慎用，性能影响大）

  - 客户端统计：在应用层统计key访问频率，超过阈值上报告警

  - 代理层统计：Twemproxy/Codis等代理层统计热Key

1. 热Key解决方案：

  - 本地缓存：在应用层（JVM堆内存）缓存热Key，减少Redis访问（Caffeine/Guava Cache）

  - 读写分离：热Key读请求分散到多个从节点

  - Key分片：将热Key复制为多个副本（model:config:gpt4:0 ~ model:config:gpt4:9），读取时随机选择

1. 大Key发现：

  - redis-cli --bigkeys：扫描所有key，统计各类型最大的key

  - MEMORY USAGE key：查看单个key的内存占用

  - SCAN + TYPE + STRLEN/LLEN/HLEN：批量扫描统计

1. 大Key拆分：

  - Hash大Key：按field范围拆分为多个Hash（user:profile:1:{field_group}）

  - List大Key：按时间或数量分页拆分

  - 渐进式迁移：新数据写新Key，老数据逐步迁移，双读兼容

1. Agent场景：模型配置（大JSON）是典型大Key，拆分为基础配置+参数配置+提示词配置三个Hash

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
简单知道monitor命令
</td>
<td>
系统阐述热Key发现方式、解决方案、大Key发现和拆分方法
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道--hotkeys、--bigkeys
</td>
<td>
掌握LFU统计、本地缓存、Key分片、渐进式迁移技术
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体场景
</td>
<td>
结合Agent模型配置场景，给出大Key拆分方案，有生产经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解热Key和大Key概念
</td>
<td>
掌握热Key和大Key的发现、诊断、解决完整方案，有实战能力
</td>
</tr>
</table>

---

#### 3、场景题：Agent 平台某个热门模型配置成为热 Key，如何做多级缓存分散压力？

难度：⭐⭐⭐（多级缓存架构、本地缓存+Redis、缓存一致性）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 多级缓存架构
- 缓存一致性
- L1：JVM本地缓存（Caffeine），TTL=30秒，容量=100个模型配置
- L2：Redis集群，TTL=5分钟，全量模型配置
- L3：MySQL，持久化存储
- 更新时：先更新MySQL，再删除Redis（Cache Aside），本地缓存等TTL自然过期

**2️⃣ Impressive Answer**

1. 多级缓存架构：

  - L1：JVM本地缓存（Caffeine），TTL=30秒，容量=100个模型配置

  - L2：Redis集群，TTL=5分钟，全量模型配置

  - L3：MySQL，持久化存储

1. 读取流程：L1命中→直接返回；L1未命中→查L2→回填L1；L2未命中→查L3→回填L2和L1

1. 缓存一致性：

  - 更新时：先更新MySQL，再删除Redis（Cache Aside），本地缓存等TTL自然过期

  - 强一致场景：更新后主动推送失效通知（Redis Pub/Sub或MQ），各实例清除本地缓存

1. 热Key分片：Redis层将模型配置复制为10个副本（model:config:gpt4:{0-9}），读取时按请求ID取模路由

1. 降级保护：Redis不可用时，本地缓存兜底；本地缓存也过期时，直接读MySQL并延长本地缓存TTL

1. 监控：统计各级缓存命中率，L1命中率<90%时告警，说明热Key访问模式异常

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
简单加本地缓存
</td>
<td>
设计完整多级缓存架构、读取流程、一致性保证方案
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道缓存一致性策略
</td>
<td>
掌握Cache Aside、Pub/Sub失效通知、热Key分片技术
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无降级和监控
</td>
<td>
给出降级保护、缓存命中率监控、告警方案，有生产经验
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解本地缓存
</td>
<td>
能设计多级缓存架构，考虑一致性、降级、监控，有架构能力
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
缓存击穿与热Key的关系
</td>
<td>
考察缓存击穿场景，热Key失效会导致大量请求穿透到数据库
</td>
<td>
答：缓存题要围绕命中率、一致性、过期策略、击穿/穿透/雪崩和监控告警来答。
</td>
</tr>
<tr>
<td>
本地缓存与Redis的一致性保证方案
</td>
<td>
考察多级缓存的一致性挑战，与热Key场景紧密相关
</td>
<td>
答：为什么需要多级缓存；架构设计；读流程；一致性问题
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| Redis 为什么快？单线程模型为什么能支撑高并发？ | Redis 快主要因为数据在内存中、核心命令是高效数据结构操作、单线程事件循环避免锁竞争和上下文切换，并通过 I/O 多路复用处理大量连接；瓶颈通常出在大 key、慢命令、网络和持久化。 |
| RDB 和 AOF 持久化有什么区别？混合持久化怎么工作？ | 核心机制：fork 子进程 + COW（写时复制），主进程继续处理请求；触发条件：save/bgsave 手动触发、满足 save 规则自动触发、shutdown 时触发；优点：恢复速度快、文件紧凑、适合备份；缺点：fork 时内存翻倍、可能丢失最后一次快照后数据；核心机制：记录每个写命令到 AOF 缓冲区，根据策略 fsync 到磁盘。 |
| Redis 内存淘汰策略有哪些？在 Agent 场景如何选择？ | volatile 系列：只淘汰设置了 TTL 的 key；volatile-lru：从过期 key 中淘汰最少使用的；volatile-lfu：从过期 key 中淘汰访问频率最低的；volatile-ttl：淘汰即将过期的 key（TTL 最小的）；volatile-random：随机淘汰过期 key。 |
| 什么是缓存穿透、击穿、雪崩？ | 缓存穿透是查询不存在的数据绕过缓存打到数据库，可用布隆过滤器和空值缓存；缓存击穿是热点 key 过期瞬间大量请求打库，可用互斥锁、逻辑过期和热点预热；缓存雪崩是大量 key 同时失效或缓存集群故障，可用随机 TTL、限流降级和多级缓存。 |
| 在 Agent 高并发场景下，如何系统性防护缓存穿透、击穿和雪崩？ | 布隆过滤器：基于位数组 + 多个哈希函数，快速判断 key 是否可能存在（0.81% 误判率）；优点：内存占用小（12KB 固定内存）、查询速度快；缺点：不支持删除、存在误判；空值缓存：对不存在的 key 缓存 null 值，设置较短的 TTL（如 30 秒）；参数校验前置：在 Agent 请求入口层做参数合法性校验，拦截明显无效请求。 |
| Redis 除了基础数据结构，还有哪些高级数据结构？ | Redis 高级数据结构包括 HyperLogLog 做 UV 估算，Bitmap 做签到和布尔状态统计，Geo 做地理位置查询，Stream 做消息流，Bloom/Cuckoo Filter 做去重和防穿透，TopK/Count-Min Sketch 做热点统计。 |
| HyperLogLog 和 Bitmap 分别适合什么场景？精度和内存占用如何？ | 核心算法：基于概率的 Cardinality 估算，误差率约 0.81%；内存占用：固定 12KB（与数据量无关）；API：PFADD 添加、PFCOUNT 计数、PFMERGE 合并；适用场景：UV 统计、Agent 日活用户数、去重 Token 计数；不适用：需要精确值、需要知道具体有哪些元素。 |
| Redis Stream 如何实现消息队列？和 Kafka 有什么区别？ | XADD：向 Stream 添加消息，返回唯一的消息 ID（时间戳 + 序列号）；XADD mystream * field1 value1 field2 value2；自动生成 ID 或手动指定（必须大于上一个 ID）；XREAD/XREADGROUP：读取消息；XREAD：独立消费者，从指定 ID 开始读取。 |
| Redis 主从复制、哨兵、Cluster 三种模式有什么区别？ | 主从复制：数据复制方案，主节点负责写，从节点负责读。主从之间异步复制，提供读写分离和数据冗余，但主节点故障需要手动切换；哨兵：高可用监控方案，在主从复制基础上增加 Sentinel 节点监控主从状态。主节点故障时自动选举新的主节点，实现故障自动转移，但仍存在单点写入瓶颈；Cluster：分布式集群方案，通过数据分片将数据分散到多个主节点，每个主节点可配置从节点。提供数据分片、故障转移、自动水平扩展能力，适合大规模数据场景。 |
| Redis Cluster 的数据分片和故障转移机制是怎样的？ | 16384 槽位：Cluster 将整个键空间划分为 16384 个 slot，每个主节点负责一部分槽位；槽位计算：CRC16(key) % 16384 确定键对应的 slot，保证相同 key 路由到同一节点；槽位迁移：支持在线迁移槽位，使用 ASKING/MOVED 重定向机制处理迁移期间的数据访问；Hash Tag：使用 {} 包裹部分 key（如 user:{1001}:profile）强制相关数据落到同一节点，支持多 key 操作；Gossip 协议：节点间定期交换 PING/PONG 消息，维护集群拓扑状态。 |
| Redis 主从复制的全量同步和增量同步机制是怎样的？ | 触发条件：从节点首次连接主节点，或复制偏移量差距超过 repl\_backlog 大小；缺点：fork 子进程导致主节点内存翻倍，RDB 传输占用网络带宽；触发条件：从节点断开后短时间内重连，且复制偏移量在 repl\_backlog 范围内；runid：主节点唯一标识，从节点记录上次同步的主节点 runid；offset：复制偏移量，记录从节点同步到主节点的哪个位置。 |
| Redis 分布式锁怎么实现？ | Redis 分布式锁通常用 SET key value NX PX 原子加锁，并用 Lua 脚本校验 value 后释放锁；SETNX 后再 EXPIRE 不是原子操作，可能死锁，还要考虑锁过期导致并发进入、业务超时续期、主从切换和 RedLock 争议。 |
| Redisson 看门狗机制和 RedLock 算法的原理与争议？ | 原子加锁：SET lock_key unique_value NX EX 30，unique_value 通常是 UUID + 线程 ID，用于识别锁持有者；非原子释放风险：先 GET 再 DEL 存在竞态条件，可能误删其他客户端的锁；Lua 脚本释放：if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end 保证"检查+删除"原子性；超时困境：过期时间设置过短导致业务未完成锁过期，设置过长导致故障后无法快速恢复；租约模式：默认 30 秒锁租约，看门狗线程每 10 秒检测并续期。 |
| Redisson 可重入锁的实现原理？锁粒度如何设计？ | 数据结构：使用 Redis Hash 存储锁信息\HSET lock:resource ``；lock:resource：锁名称；``：线程唯一标识（UUID + 线程 ID）；加锁流程（Lua 脚本保证原子性）：\luaif redis.call('exists', KEYS\[1\]) ==0 or redis.call('hexists', KEYS\[1\], ARGV\[2\])== 1 thenredis.call('hincrby', KEYS\[1\], ARGV\[2\], 1)redis.call('pexpire', KEYS\[1\], ARGV\[1\])return 1elsereturn 0end``；如果锁不存在或当前线程已持有锁，计数器 +1 并续期。 |
| Redis 的 5 种基础数据类型底层编码分别是什么？ | String：int（整数）、embstr（≤44字节）、raw（>44字节）；List：listpack（元素少且小）、quicklist（元素多，双向链表+listpack节点）；Hash：listpack（元素≤128且值≤64字节）、hashtable（超出阈值）；Set：intset（全整数且≤512）、listpack（元素≤128且值≤64字节）、hashtable（超出阈值）；ZSet：listpack（元素≤128且值≤64字节）、skiplist+hashtable（超出阈值）。 |
| ZSet 为什么同时用 ziplist/listpack 和 skiplist？跳表的查询复杂度如何保证？ | skiplist：支持按score范围查询（ZRANGEBYSCORE），O(logN)复杂度；hashtable：支持按member查score（ZSCORE），O(1)复杂度；两者共享member对象（指针引用），内存开销可控；层级随机生成：每个节点以50%概率晋升到上一层，期望层数O(logN)；查询路径：从最高层开始，逐层向右向下，期望比较次数O(logN)。 |
| Agent 排行榜（模型调用次数 Top N）如何用 ZSet 高效实现？ | Key：model:call:rank:daily:{date}（按天分榜）；Member：model_id；调用时：ZINCRBY model:call:rank:daily:20240101 1 gpt-4（原子自增）；查Top N：ZREVRANGEBYSCORE model:call:rank:daily:20240101 +inf -inf WITHSCORES LIMIT 0 10；查某模型排名：ZREVRANK model:call:rank:daily:20240101 gpt-4。 |
| Redis 的 key 过期删除策略有哪些？ | 惰性删除：访问key时检查是否过期，过期则删除。CPU友好但内存不友好（过期key不访问就不删）；定期删除：每隔100ms随机抽取部分设置了过期时间的key检查删除。平衡CPU和内存；Redis同时使用两种策略：定期删除兜底，惰性删除精确清理。 |
| 大量 key 同时过期会有什么问题？如何避免过期扫描阻塞主线程？ | 定期删除每次最多扫描25%的过期key，如果过期key比例超过25%，会持续扫描直到比例降低；大量key同时过期时，定期删除占用大量CPU时间，导致其他命令延迟升高；大key过期时，同步删除耗时长（如删除一个有10万元素的Hash），阻塞主线程；随机过期时间：TTL = base_ttl + random(0, jitter)，分散过期时间，避免集中过期；lazy-free异步删除：配置lazyfree-lazy-expire yes，过期key异步删除，不阻塞主线程。 |
| Agent 会话 TTL 管理中，如何设计过期策略避免内存突增？ | 活跃会话：TTL=2小时，每次交互时EXPIRE续期（滑动过期）；非活跃会话：TTL=24小时，超过24小时无交互自动清理；历史会话摘要：TTL=7天，保留最近会话的摘要信息；预估单会话内存：消息列表（平均10条×500字节）+ 元数据 ≈ 10KB；设置maxmemory和maxmemory-policy（allkeys-lru），超出内存上限时淘汰最久未使用的会话。 |
| Redis 6.0 引入多线程解决了什么问题？哪些操作是多线程的？ | 解决的问题：Redis单线程在高并发下，网络IO（读取请求、发送响应）成为瓶颈，CPU利用率低；多线程的操作：网络数据读取（read）、请求解析、响应数据写入（write）；仍是单线程的：命令执行（保证原子性和数据一致性）。 |
| Redis 多线程 IO 模型和单线程命令执行如何协作？为什么命令执行仍是单线程？ | 主线程accept新连接，分配给IO线程；IO线程并发读取socket数据，解析请求；主线程统一执行所有命令（单线程，保证原子性）；IO线程并发将响应数据写回socket；避免锁竞争：多线程访问共享数据结构需要加锁，锁竞争开销可能超过多线程收益。 |
| Agent 高并发场景下，Redis 6.0 多线程能带来多少性能提升？如何评估？ | 高并发小包（<1KB）：多线程IO收益最大，吞吐量提升2-3倍；大包或复杂命令：命令执行是瓶颈，多线程IO收益有限；网络带宽受限：多线程IO无法突破带宽上限；基准测试：redis-benchmark -t get,set -n 1000000 -c 200 --threads 4；对比指标：QPS（每秒请求数）、P99延迟、CPU利用率。 |
| Redis Pipeline 和普通命令有什么区别？MULTI/EXEC 事务是什么？ | Pipeline：将多个命令批量打包发送，一次网络往返执行多个命令，减少RTT（网络往返时间）。注意：Pipeline不保证原子性，命令之间可能被其他客户端命令插入；MULTI/EXEC事务：MULTI开启事务，命令入队，EXEC统一执行。保证命令顺序执行，执行期间不会被其他命令插入，但不支持回滚。 |
| Redis 事务和 Lua 脚本的区别？为什么 Redis 事务不支持回滚？ | 命令入队阶段：语法错误会导致整个事务取消；执行阶段：运行时错误（如对String执行LPUSH）不会回滚，其他命令继续执行；WATCH：乐观锁，监听key变化，如果EXEC前key被修改，事务取消（返回nil）；Redis认为运行时错误是编程错误（类型操作错误），不应该在生产环境发生；支持回滚需要记录undo log，增加复杂度和内存开销，违背Redis简单高效的设计哲学。 |
| Agent Token 计费场景，如何用 Lua 脚本保证扣减原子性？ | KEYS[1]: token:balance:{user_id}；local balance = tonumber(redis.call('GET', KEYS[1]))；if balance == nil then。 |
| 什么是热 Key 和大 Key？会带来什么问题？ | 热Key：某个key被极高频率访问（如QPS>10万），导致该key所在的Redis节点CPU/网络成为瓶颈，其他key的访问也受影响；大Key：key对应的value体积很大（String>10KB，集合类型元素>10000），导致：读写耗时长、网络传输慢、内存分配/释放时阻塞主线程、集群迁移困难。 |
| 热 Key 的发现方式有哪些？大 Key 如何拆分和迁移？ | redis-cli --hotkeys：基于LFU策略统计访问频率（需要maxmemory-policy设置为LFU类型）；MONITOR命令：实时监控所有命令，统计key访问频率（生产慎用，性能影响大）；客户端统计：在应用层统计key访问频率，超过阈值上报告警；代理层统计：Twemproxy/Codis等代理层统计热Key；本地缓存：在应用层（JVM堆内存）缓存热Key，减少Redis访问（Caffeine/Guava Cache）。 |
| Agent 平台某个热门模型配置成为热 Key，如何做多级缓存分散压力？ | L1：JVM本地缓存（Caffeine），TTL=30秒，容量=100个模型配置；L2：Redis集群，TTL=5分钟，全量模型配置；L3：MySQL，持久化存储；更新时：先更新MySQL，再删除Redis（Cache Aside），本地缓存等TTL自然过期；强一致场景：更新后主动推送失效通知（Redis Pub/Sub或MQ），各实例清除本地缓存。 |
