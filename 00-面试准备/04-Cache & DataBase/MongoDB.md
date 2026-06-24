## MongoDB 文档存储与聚合管道

#### 1、基础题：MongoDB 的文档模型和关系型数据库有什么区别？适合什么场景？

**难度级别**：⭐⭐（BSON 格式、Schema-Free、嵌套结构、横向扩展）

---

#### 2、进阶题：MongoDB 的聚合管道（Aggregation Pipeline）怎么用？有哪些常用阶段？

**难度级别**：⭐⭐⭐（group/project/$unwind、管道优化、索引利用）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 常用阶段与用途
- 性能优化要点
- Agent 场景应用
- $match：过滤文档，类似 WHERE，应尽早使用减少后续处理量
- avg/$push 等累加器
- $lookup：左外连接，关联其他集合（类似 LEFT JOIN）

**2️⃣ Impressive Answer**

聚合管道是 MongoDB 的**数据处理核心**，类似 Unix 管道，数据流经多个阶段处理：

1. **常用阶段与用途**

  - $match：过滤文档，类似 WHERE，应尽早使用减少后续处理量

  - avg/$push 等累加器

  - $lookup：左外连接，关联其他集合（类似 LEFT JOIN）

  - $project：投影字段，控制输出结构，可计算衍生字段

  - $unwind：拆解数组字段，一对多展开

  - skip/$limit：分页排序，注意内存限制（128MB）

1. **性能优化要点**

  - 管道顺序：$match 尽早过滤 → $sort 利用索引 → $group 聚合 → $limit 截断

  - 索引利用：group 无法利用

  - 使用 $explain() 分析执行计划，关注 totalDocsExamined 指标

1. **Agent 场景应用**

  - 会话分析：按用户分组统计对话轮次、Token 消耗

  - 知识库检索：match 过滤权限

  - 用户行为漏斗：$match 筛选事件 → $sort 按时间 → $group 统计转化率

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
简单列举阶段名，无使用逻辑
</td>
<td>
分用途、优化、场景三层，有管道顺序意识
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道索引利用和执行计划
</td>
<td>
明确 $explain() 和内存限制
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
结合 Agent 会话分析、知识库检索给出实例
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
用过但没思考过优化
</td>
<td>
有性能意识和实战经验
</td>
</tr>
</table>

---

#### 3、基础题：MongoDB 的 CRUD 操作有哪些？`updateOne` 和 `findAndModify` 有什么区别？

**难度级别**：⭐⭐（原子操作、push/$inc、upsert、findAndModify 的原子性、写关注 WriteConcern）

MongoDB 的 CRUD 操作分为四类，核心区别在于**原子性**：

1. **基础 CRUD**：`insertOne/insertMany`、`findOne/find`、`updateOne/updateMany`、`deleteOne/deleteMany`

1. **更新操作符**：

  - `$set`：设置字段值（不存在则创建）

  - `$unset`：删除字段

  - `$inc`：数值自增/自减（原子操作，适合计数器）

  - `$push/$pull`：数组追加/删除元素

  - `$addToSet`：数组去重追加

1. **upsert**：`updateOne({filter}, {$set: {...}}, {upsert: true})`，不存在则插入，存在则更新，原子操作

1. **updateOne vs findAndModify**：

  - `updateOne`：只执行更新，返回更新结果（匹配数、修改数），不返回文档内容

  - `findAndModify`（即 `findOneAndUpdate`）：原子地查找并更新，**返回更新前或更新后的文档**，适合需要获取更新后值的场景（如分布式 ID 生成、乐观锁）

1. **WriteConcern**：控制写入确认级别，`w:1`（主节点确认）、`w:majority`（多数副本确认，更安全）、`w:0`（不确认，最快）。**Agent 场景**：会话写入用 `w:1`，计费数据用 `w:majority`

---

#### 4、进阶题：MongoDB 的事务支持（4.0+）是怎样的？和 MySQL 事务有什么区别？

**难度级别**：⭐⭐⭐（多文档事务、ACID、WiredTiger 存储引擎、隔离级别、分布式事务）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- MongoDB 事务演进
- 与 MySQL 事务对比
- 最佳实践
- Agent 场景实践
- 0：支持副本集内的多文档事务（单分片）
- 2：支持分片集群的分布式事务（跨分片）

**2️⃣ Impressive Answer**

MongoDB 事务是**文档数据库向关系型数据库能力靠拢**的重要演进，需要从实现机制、与 MySQL 对比、使用场景三个层面理解：

1. **MongoDB 事务演进**

  - **4.0**：支持副本集内的多文档事务（单分片）

  - **4.2**：支持分片集群的分布式事务（跨分片）

  - **底层机制**：基于 WiredTiger 的 MVCC（多版本并发控制），通过快照隔离实现事务

1. **与 MySQL 事务对比**
    | 维度 | MongoDB | MySQL || --- | --- | --- || 隔离级别 | 快照隔离（Snapshot Isolation） | RC/RR/Serializable 可配置 || 锁机制 | 文档级乐观锁（MVCC） | 行锁 + 间隙锁（Next-Key Lock） || 性能开销 | 事务性能较差，建议单文档原子操作替代 | 事务性能成熟，优化完善 || 适用场景 | 文档内嵌套数据天然原子，跨集合事务少用 | 关系型数据，事务是核心能力 || 超时控制 | `maxTimeMS` 控制事务超时 | `innodb_lock_wait_timeout` |

1. **最佳实践**

  - **优先使用单文档原子操作**：MongoDB 的文档嵌套设计使得大多数操作无需跨文档事务

  - **必要时才用多文档事务**：如转账（扣款 + 入账跨集合），性能代价约 3-5 倍

  - **事务超时**：设置合理的 `maxTimeMS`（建议 5 秒），避免长事务锁资源

1. **Agent 场景实践**

  - **会话 + 消息原子写入**：会话表和消息表分开存储时，用事务保证会话更新和消息插入的原子性

  - **知识库文档 + 向量同步**：文档元数据和向量 ID 跨集合写入时，用事务保证一致性

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
简单说支持 ACID，性能差
</td>
<td>
系统对比隔离级别、锁机制、适用场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道版本演进和 MVCC 机制
</td>
<td>
深入 4.0/4.2 演进、快照隔离、最佳实践
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体使用场景
</td>
<td>
结合 Agent 会话、知识库场景给出实践
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
掌握核心机制，有数据库选型能力
</td>
</tr>
</table>

---

#### 5、进阶题：MongoDB 的副本集（Replica Set）机制是怎样的？如何实现高可用？

**难度级别**：⭐⭐⭐（Primary/Secondary/Arbiter、Oplog、选举机制、读写偏好、故障转移）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 节点角色
- Oplog（操作日志）同步机制
- 选举机制
- 读写偏好（Read Preference）
- Agent 场景实践
- Primary：唯一接受写入的主节点，处理所有写操作，将变更写入 Oplog

**2️⃣ Impressive Answer**

副本集是 MongoDB **高可用的核心机制**，需要从节点角色、数据同步、选举机制三个层面理解：

1. **节点角色**

  - **Primary**：唯一接受写入的主节点，处理所有写操作，将变更写入 Oplog

  - **Secondary**：从主节点异步复制 Oplog，保持数据同步，可配置为只读节点

  - **Arbiter**：仲裁节点，不存储数据，只参与选举投票，用于凑足奇数节点避免平票

1. **Oplog（操作日志）同步机制**

  - Oplog 是一个固定大小的 Capped Collection，记录所有写操作（幂等格式）

  - Secondary 持续拉取 Primary 的 Oplog 并重放，实现异步复制

  - **复制延迟**：可通过 `rs.printReplicationInfo()` 查看 Oplog 窗口和复制延迟

1. **选举机制**

  - **触发条件**：Primary 故障或网络分区时触发选举

  - **选举算法**：基于 Raft 协议，获得多数票（超过半数节点）的 Secondary 成为新 Primary

  - **选举时间**：通常 10-30 秒，期间写入不可用（需应用层重试）

  - **Priority 配置**：可设置节点优先级（`priority: 0` 表示不参与选举，适合跨机房备份节点）

1. **读写偏好（Read Preference）**

  - `primary`：只读主节点（强一致，默认）

  - `primaryPreferred`：优先主节点，主不可用时读从节点

  - `secondary`：只读从节点（可能读到旧数据）

  - `nearest`：读延迟最低的节点（适合地理分布场景）

1. **Agent 场景实践**

  - **会话数据**：写入用 `w:majority` 确保多数副本写入，读取用 `primaryPreferred` 保证一致性

  - **知识库查询**：只读统计分析用 `secondary` 读偏好，减轻主节点压力

  - **跨机房部署**：主机房 2 个节点 + 备机房 1 个节点 + Arbiter，Priority 配置确保主机房优先选举

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
简单描述主从同步
</td>
<td>
系统阐述节点角色、Oplog 机制、选举算法
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Oplog 和 Raft 选举
</td>
<td>
深入 Oplog 幂等格式、Priority 配置、读写偏好
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体配置方案
</td>
<td>
结合 Agent 会话、跨机房部署给出实践
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
掌握核心机制，有高可用架构设计能力
</td>
</tr>
</table>

---

## MongoDB 索引与性能优化

#### 6、进阶题：MongoDB 的索引类型有哪些？如何设计高效索引？

**难度级别**：⭐⭐⭐（单字段索引、复合索引、多键索引、地理空间索引、文本索引、索引选择规则）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 核心索引类型
- 索引设计原则
- Agent 场景实践
- 单字段索引：最基础的索引，支持升序/降序，默认 _id 字段自动创建
- 复合索引：多个字段组合，遵循最左前缀原则，查询时必须包含索引的前缀字段才能命中
- 多键索引：针对数组字段，为数组中每个元素创建索引项

**2️⃣ Impressive Answer**

MongoDB 的索引体系设计借鉴了 B-Tree，支持多种索引类型以适应不同场景：

1. **核心索引类型**

  - **单字段索引**：最基础的索引，支持升序/降序，默认 `_id` 字段自动创建

  - **复合索引**：多个字段组合，遵循**最左前缀原则**，查询时必须包含索引的前缀字段才能命中

  - **多键索引**：针对数组字段，为数组中每个元素创建索引项

  - **地理空间索引**：2dsphere（球面）、2d（平面），支持地理位置查询和范围查询

  - **文本索引**：支持全文搜索，支持多语言，注意每个集合只能有一个文本索引

  - **哈希索引**：基于哈希值，支持等值查询，不支持范围查询

1. **索引设计原则**

  - **ESR 规则**：Equality（等值）→ Sort（排序）→ Range（范围），按此顺序建索引效率最高

  - **选择性原则**：在高选择性字段（基数大）上建索引，如 `userId` 比 `gender` 更适合

  - **覆盖索引**：索引包含查询所需的所有字段，避免回表查询，提升性能

  - **TTL 索引**：自动过期数据，适合日志、会话等临时数据

1. **Agent 场景实践**

  - **会话查询**：复合索引 `{userId: 1, createdAt: -1}` 支持按用户查询并按时间倒序

  - **向量检索**：使用 2dsphere 索引存储向量坐标，配合 `$near` 实现相似度搜索

  - **知识库检索**：文本索引支持全文搜索，多键索引处理标签数组

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
简单列举类型名，无使用逻辑
</td>
<td>
分类型、设计原则、场景三层，有 ESR 规则意识
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道最左前缀和覆盖索引
</td>
<td>
明确索引选择规则和性能优化策略
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
结合 Agent 会话、向量检索给出实例
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
用过但没思考过设计
</td>
<td>
有架构设计和性能优化能力
</td>
</tr>
</table>

---

#### 7、进阶题：MongoDB 的分片集群是如何工作的？如何选择分片键？

**难度级别**：⭐⭐⭐⭐（分片架构、数据分布、分片键选择、均衡策略）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 集群架构
- 数据分布策略
- 分片键选择原则
- Agent 场景实践
- Shard Server：存储数据的分片节点，每个分片是一个副本集（高可用）
- Config Server：存储集群元数据（分片信息、配置），必须是副本集

**2️⃣ Impressive Answer**

MongoDB 分片集群是**水平扩展**的核心方案，由三个组件组成：

1. **集群架构**

  - **Shard Server**：存储数据的分片节点，每个分片是一个副本集（高可用）

  - **Config Server**：存储集群元数据（分片信息、配置），必须是副本集

  - **Mongos**：查询路由器，接收应用请求，根据分片键路由到对应分片

1. **数据分布策略**

  - **范围分片（Range Sharding）**：按分片键值范围分配，适合范围查询，但可能导致数据倾斜

  - **哈希分片（Hash Sharding）**：对分片键哈希后分配，数据均匀分布，不适合范围查询

  - **基数分片（Ranged + Tag）**：结合范围和标签，支持按业务规则分配数据

1. **分片键选择原则**

  - **基数足够大**：避免热点，如 `userId` 比 `status` 更适合

  - **数据分布均匀**：避免某个分片成为热点，不要用递增字段（如时间戳）单独做分片键

  - **查询模式匹配**：分片键应包含常用查询条件，避免 Scatter-Gather 查询（全分片扫描）

  - **避免频繁变更**：分片键一旦选定很难修改，不要用易变字段

1. **Agent 场景实践**

  - **用户数据分片**：`{tenantId: 1, userId: 1}` 复合键，按租户隔离，支持租户内用户查询

  - **日志数据分片**：哈希分片 `{logId: "hashed"}` 均匀分布，配合 TTL 索引自动清理

  - **向量数据分片**：按 `collectionId` 范围分片，支持按知识库查询，避免跨分片聚合

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
简单描述架构，无深入机制
</td>
<td>
分架构、分布策略、选择原则、场景四层
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Scatter-Gather 和数据倾斜
</td>
<td>
明确分片策略优缺点和均衡机制
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
结合 Agent 多租户、日志、向量数据给出实例
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本概念
</td>
<td>
有大规模系统设计和扩展能力
</td>
</tr>
</table>

---

#### 8、进阶题：MongoDB 和 Elasticsearch 在搜索场景如何选型？各自适合什么场景？

**难度级别**：⭐⭐⭐（全文检索能力对比、写入性能、事务支持、Agent 知识库选型、混合使用场景）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 核心能力对比
- 适用场景
- Agent 场景实践
- 选 MongoDB：主数据存储（会话、用户、文档元数据）、需要事务、写多读少、数据结构复杂嵌套
- 选 ES：全文搜索、日志分析、实时聚合看板、混合检索（BM25 + 向量）
- 两者结合：MongoDB 作为主存储（Source of Truth），ES 作为搜索索引（Search Layer），Canal 同步

**2️⃣ Impressive Answer**

MongoDB 和 ES 的选型需要从**核心能力差异、适用场景、混合架构**三个层面系统分析：

1. **核心能力对比**
    | 维度 | MongoDB | Elasticsearch || --- | --- | --- || 数据模型 | 文档存储（BSON），支持嵌套、数组 | 文档存储（JSON），扁平化更优 || 全文检索 | 基础文本索引，不支持中文分词 | 强大的倒排索引，支持 ik 中文分词 || 聚合分析 | 聚合管道功能完整，但性能一般 | 聚合性能强，适合实时分析 || 事务支持 | 4.0+ 支持多文档事务 | 不支持事务 || 写入性能 | 写入性能好，支持高并发写 | 写入有延迟（refresh 1 秒），批量写更优 || 数据一致性 | 强一致（副本集 w:majority） | 近实时（NRT，1 秒延迟） || 向量检索 | 支持（Atlas Vector Search） | 支持（dense_vector + kNN） |

1. **适用场景**

  - **选 MongoDB**：主数据存储（会话、用户、文档元数据）、需要事务、写多读少、数据结构复杂嵌套

  - **选 ES**：全文搜索、日志分析、实时聚合看板、混合检索（BM25 + 向量）

  - **两者结合**：MongoDB 作为主存储（Source of Truth），ES 作为搜索索引（Search Layer），Canal 同步

1. **Agent 场景实践**

  - **知识库架构**：MongoDB 存储文档原文、元数据、权限；ES 存储分块文本 + 向量，负责检索

  - **会话管理**：MongoDB 存储会话历史（需要事务保证原子性）；ES 不适合（无事务、NRT 延迟）

  - **日志分析**：ES 天然适合日志聚合分析（date_histogram + terms 聚合）

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
简单说 ES 搜索强 MongoDB 存储好
</td>
<td>
用表格系统对比七个维度，给出选型决策树
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道具体能力差异
</td>
<td>
深入事务支持、NRT 延迟、向量检索能力对比
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体架构方案
</td>
<td>
结合 Agent 知识库、会话、日志给出混合架构
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基础定位，缺乏深度
</td>
<td>
掌握核心差异，有技术选型和架构设计能力
</td>
</tr>
</table>

---

#### 9、进阶题：MongoDB 的 Change Stream 是什么？在 Agent 场景如何应用？

**难度级别**：⭐⭐⭐⭐（实时监听数据变更、Oplog 原理、会话状态同步、知识库更新推送、断点续传）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Change Stream 原理
- 使用方式
- Agent 场景实践
- 底层依赖 Oplog：Change Stream 本质是对 Oplog 的高级封装，将底层的 Oplog 事件转换为结构化的变更事件
- 事件类型：insert、update、replace、delete、invalidate（集合删除/重命名）
- 监听粒度：可监听单个集合、整个数据库、整个集群（需副本集或分片集群）

**2️⃣ Impressive Answer**

Change Stream 是 MongoDB **实时数据流处理的核心能力**，需要从原理、使用方式、Agent 场景三个层面理解：

1. **Change Stream 原理**

  - **底层依赖 Oplog**：Change Stream 本质是对 Oplog 的高级封装，将底层的 Oplog 事件转换为结构化的变更事件

  - **事件类型**：`insert`、`update`、`replace`、`delete`、`invalidate`（集合删除/重命名）

  - **监听粒度**：可监听单个集合、整个数据库、整个集群（需副本集或分片集群）

  - **断点续传**：每个事件包含 `_id`（Resume Token），应用重启后可从上次位置继续消费

1. **使用方式**
    `\``// 监听集合变更const changeStream = db.collection('documents').watch([{ $match: { 'operationType': { $in: ['insert', 'update'] } } }]);changeStream.on('change', (event) => {console.log(event.fullDocument); // 变更后的完整文档});
    `\``

  - **Pipeline 过滤**：支持聚合管道过滤，只监听特定条件的变更（如特定租户的文档）

  - **fullDocument**：设置 `fullDocument: 'updateLookup'` 可在 update 事件中获取完整文档

1. **Agent 场景实践**

  - **知识库实时同步**：监听文档集合变更，触发 ES 索引更新（替代 Canal 方案，无需额外组件）

  - **会话状态推送**：监听会话集合，当 Agent 写入新消息时，通过 WebSocket 实时推送给前端

  - **向量索引更新**：文档更新时，Change Stream 触发 Embedding 重新计算并更新向量数据库

  - **多租户隔离**：使用 Pipeline 过滤 `tenantId`，不同租户的变更事件独立处理

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
简单说监听变更，类似 Binlog
</td>
<td>
系统阐述 Oplog 原理、断点续传、Pipeline 过滤
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Resume Token 和 fullDocument
</td>
<td>
深入底层原理、监听粒度、事件类型
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体应用场景
</td>
<td>
结合知识库同步、会话推送、向量更新给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解概念，缺乏工程能力
</td>
<td>
掌握核心机制，有实时数据流处理能力
</td>
</tr>
</table>

---

#### 10、进阶题：MongoDB 的性能如何优化？如何分析慢查询？

**难度级别**：⭐⭐⭐⭐（explain/profiler、索引优化、连接池、读写分离、内存管理、慢查询分析）

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 慢查询定位
- 索引优化
- 架构优化
- Agent 场景实践
- Profiler：db.setProfilingLevel(1, {slowms: 100}) 记录超过 100ms 的慢查询，结果存入 system.profile 集合
- explain() 分析：db.collection.find({...}).explain('executionStats')，关键指标

**2️⃣ Impressive Answer**

MongoDB 性能优化需要从**慢查询定位、索引优化、架构优化**三个层面系统掌握：

1. **慢查询定位**

  - **Profiler**：`db.setProfilingLevel(1, {slowms: 100})` 记录超过 100ms 的慢查询，结果存入 `system.profile` 集合

  - **explain() 分析**：`db.collection.find({...}).explain('executionStats')`，关键指标：

    - `COLLSCAN`：全集合扫描（最差，需加索引）

    - `IXSCAN`：索引扫描（理想）

    - `totalDocsExamined`：扫描文档数，越接近 `nReturned` 越好

    - `executionTimeMillis`：执行时间

  - **currentOp**：`db.currentOp({active: true, secs_running: {$gt: 5}})` 查看当前执行超过 5 秒的操作

1. **索引优化**

  - **ESR 规则**：Equality → Sort → Range，按此顺序建复合索引效率最高

  - **覆盖索引**：查询字段全在索引中，避免回表（`projection` 只返回索引字段）

  - **索引选择性**：在高基数字段建索引（如 `userId`），低基数字段（如 `status`）放复合索引后面

  - **TTL 索引**：自动清理过期数据，避免手动删除影响性能

1. **架构优化**

  - **读写分离**：读偏好设置为 `secondary`，将统计分析查询路由到从节点

  - **连接池**：合理配置 `maxPoolSize`（默认 100），避免连接数超过 MongoDB 的 `maxIncomingConnections`

  - **文档设计**：避免超大文档（16MB 限制），嵌套 vs 引用根据查询模式选择

  - **WiredTiger 缓存**：默认使用 50% 内存作为缓存，确保热数据在内存中，减少磁盘 IO

1. **Agent 场景实践**

  - **会话查询优化**：`{userId: 1, createdAt: -1}` 复合索引 + `projection` 只返回需要字段，避免全文档加载

  - **知识库检索**：文本索引 + 复合索引组合，`explain()` 验证索引命中，`totalDocsExamined` 控制在合理范围

  - **批量写入优化**：使用 `insertMany` + `ordered: false`（无序插入，失败不中断），提升批量写入吞吐量

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
简单列举加索引、读写分离
</td>
<td>
系统阐述定位→索引→架构三层优化体系
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 explain 关键指标和 ESR 规则
</td>
<td>
深入 COLLSCAN/IXSCAN、覆盖索引、WiredTiger 缓存
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体优化方案
</td>
<td>
结合 Agent 会话、知识库、批量写入给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本手段，缺乏方法论
</td>
<td>
有完整的性能优化方法论和实战经验
</td>
</tr>
</table>

---

#### 11、容易一起考的题

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
MongoDB 文档模型与关系型数据库的区别
</td>
<td>
理解 MongoDB 设计哲学的基础
</td>
<td>
答：MongoDB 文档模型强调聚合数据放在一个文档中，适合结构灵活、读多写少的聚合查询；关系型数据库强调表结构和 Join，适合强约束、多表事务和复杂关系。
</td>
</tr>
<tr>
<td>
MongoDB 聚合管道（group/$lookup）
</td>
<td>
数据分析核心能力，与索引优化配合
</td>
<td>
答：MongoDB 聚合管道是把数据按 stage 流式处理，常见有 $match、$group、$lookup、$project。优化时把 $match 前置、让过滤字段命中索引，避免大集合上无限制 $lookup。
</td>
</tr>
<tr>
<td>
MongoDB 副本集选举机制（Raft 协议）
</td>
<td>
高可用基础，与分片集群配合
</td>
<td>
答：MongoDB 副本集通过心跳和选举保证高可用，Primary 负责写入，Secondary 复制 Oplog；Primary 故障后多数派选出新 Primary，写关注可控制确认级别。
</td>
</tr>
<tr>
<td>
MongoDB 事务（4.0+）与 MySQL 事务对比
</td>
<td>
数据一致性保障，考察数据库选型能力
</td>
<td>
答：MySQL 事务是关系型数据库的基础能力，适合强一致多表操作；MongoDB 4.0+ 支持多文档事务，但更推荐通过合理文档建模把相关数据聚合在一个文档内，减少跨文档事务。
</td>
</tr>
<tr>
<td>
ES 与 MongoDB 在搜索场景的技术选型
</td>
<td>
两者定位不同，考察架构设计能力
</td>
<td>
答：MongoDB 适合业务数据存储和按文档模型查询，Elasticsearch 适合全文检索、复杂搜索和相关性排序。常见架构是 MongoDB 做主存储，ES 做搜索索引，通过 Change Stream/CDC 同步。
</td>
</tr>
<tr>
<td>
Change Stream 与 Canal + Binlog 的对比
</td>
<td>
实时数据同步方案选型
</td>
<td>
答：Change Stream 是 MongoDB 原生变更订阅，适合同步 MongoDB 数据变化；Canal + Binlog 面向 MySQL 生态。比较时看数据源、可靠性、延迟、断点续传和运维复杂度。
</td>
</tr>
<tr>
<td>
MongoDB Atlas Vector Search 与 pgvector 对比
</td>
<td>
向量检索方案选型，Agent 知识库核心
</td>
<td>
答：Atlas Vector Search 适合已经使用 MongoDB Atlas、希望文档和向量一体化的场景；pgvector 适合 PostgreSQL 体系内的小中规模向量检索。大规模高性能检索再考虑专用向量库。
</td>
</tr>
</table>

---

## MongoDB 存储引擎与底层原理

#### 12、WiredTiger 存储引擎原理

**难度级别**：⭐⭐~⭐⭐⭐⭐（B-Tree、MVCC、Checkpoint、压缩）

##### 基础题：MongoDB 默认存储引擎是什么？有什么特点？

MongoDB 3.2+ 默认存储引擎是 **WiredTiger**，替代了 MMAPv1。主要特点：

1. **文档级锁**：支持并发读写，比 MMAPv1 的全局锁性能大幅提升

1. **压缩算法**：默认使用 Snappy 压缩，数据压缩率约 50%，节省磁盘空间

1. **Checkpoint 机制**：定期将内存脏页刷盘，保证数据持久化

1. **Journaling**：WAL 日志保证数据安全，崩溃恢复

##### 进阶题：WiredTiger 的 B-Tree 存储结构、MVCC 实现、Checkpoint 机制、压缩算法分别是怎样的？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- B-Tree 存储结构
- MVCC 实现（多版本并发控制）
- Checkpoint 机制
- 压缩算法
- Agent 场景应用
- 索引和数据都存储在 B-Tree 中，每个节点 8KB

**2️⃣ Impressive Answer**

WiredTiger 是 MongoDB 的**核心存储引擎**，底层机制包括：

1. **B-Tree 存储结构**

  - 索引和数据都存储在 B-Tree 中，每个节点 8KB

  - B-Tree 节点在内存中是 Page，磁盘上是 Block

  - 内部节点存储键值和子节点指针，叶子节点存储完整文档

1. **MVCC 实现（多版本并发控制）**

  - **快照隔离**：每个事务开始时获取快照，读取历史版本数据

  - **写时复制**：修改文档时创建新版本，旧版本保留在内存中

  - **版本链**：通过事务 ID 追踪文档版本，读取时选择可见版本

  - **并发读写**：读操作不阻塞写，写操作不阻塞读

1. **Checkpoint 机制**

  - **触发条件**：每 60 秒或 Journal 大小达到 2GB

  - **刷盘流程**：将内存脏页写入数据文件 → 清空 Journal → 更新 Checkpoint 记录

  - **崩溃恢复**：从最近 Checkpoint + Journal 重放 WAL 日志

1. **压缩算法**

  - **Snappy**：默认压缩算法，压缩比约 50%，CPU 开销低

  - **Zlib**：可选，压缩比约 70%，但 CPU 开销高

  - **压缩粒度**：Page 级别压缩，减少磁盘 I/O

1. **Agent 场景应用**

  - 会话数据高频写入：文档级锁 + MVCC 保证并发性能

  - 知识库文档存储：压缩算法节省存储成本

  - 崩溃恢复保障：Journal + Checkpoint 保证数据不丢失

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
简单罗列特性
</td>
<td>
系统阐述 B-Tree→MVCC→Checkpoint→压缩完整机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 MVCC 实现细节
</td>
<td>
深入快照隔离、写时复制、版本链机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无场景应用
</td>
<td>
结合 Agent 会话、知识库、崩溃恢复给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本概念
</td>
<td>
深入理解存储引擎原理，具备底层优化能力
</td>
</tr>
</table>

##### 场景题：为什么 MongoDB 写入性能好？内存配置如何影响性能？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 写入性能好的原因
- 内存配置影响
- Agent 场景优化
- 文档级锁：WiredTiger 支持文档级并发写入，锁粒度细
- Journal 异步刷盘：默认 journalCommitIntervalMs=100，批量刷盘减少 I/O
- 内存缓冲：写入先到内存，Checkpoint 定期刷盘，减少磁盘随机写

**2️⃣ Impressive Answer**

MongoDB 写入性能好的**核心原因**和内存配置策略：

1. **写入性能好的原因**

  - **文档级锁**：WiredTiger 支持文档级并发写入，锁粒度细

  - **Journal 异步刷盘**：默认 `journalCommitIntervalMs=100`，批量刷盘减少 I/O

  - **内存缓冲**：写入先到内存，Checkpoint 定期刷盘，减少磁盘随机写

  - **压缩算法**：减少磁盘 I/O 量，提升吞吐量

1. **内存配置影响**

  - **WiredTiger 缓存**：默认占用 50% 内存，建议 `cacheSizeGB` 设置为物理内存的 40-60%

  - **热数据驻留**：确保工作集（Working Set）在内存中，避免磁盘抖动

  - **内存不足表现**：Page Fault 频繁 → 查询延迟飙升 → CPU 等待 I/O

  - **监控指标**：`wiredTiger.cache.pages read into cache`（读入页数）和 `pages evicted`（驱逐页数）

1. **Agent 场景优化**

  - 会话写入：`w:1` + `journal:true` 平衡性能和安全

  - 知识库检索：确保索引和热数据在内存中，`cacheSizeGB` 配置充足

  - 监控告警：Page Fault 率超过阈值时扩容内存

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
简单说&quot;锁粒度细&quot;
</td>
<td>
系统阐述文档锁→异步刷盘→内存缓冲→压缩四层原因
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道内存配置细节
</td>
<td>
深入 Working Set、Page Fault、监控指标
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体优化方案
</td>
<td>
结合 Agent 会话、知识库给出配置策略
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道 MongoDB 写入快
</td>
<td>
深入理解性能瓶颈和优化方法
</td>
</tr>
</table>

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
MongoDB 文档模型与关系型数据库的区别
</td>
<td>
理解 MongoDB 设计哲学的基础
</td>
<td>
答：MongoDB 文档模型强调聚合数据放在一个文档中，适合结构灵活、读多写少的聚合查询；关系型数据库强调表结构和 Join，适合强约束、多表事务和复杂关系。
</td>
</tr>
<tr>
<td>
MongoDB 聚合管道（group/$lookup）
</td>
<td>
数据分析核心能力，与索引优化配合
</td>
<td>
答：MongoDB 聚合管道是把数据按 stage 流式处理，常见有 $match、$group、$lookup、$project。优化时把 $match 前置、让过滤字段命中索引，避免大集合上无限制 $lookup。
</td>
</tr>
<tr>
<td>
MongoDB 副本集选举机制（Raft 协议）
</td>
<td>
高可用基础，与分片集群配合
</td>
<td>
答：MongoDB 副本集通过心跳和选举保证高可用，Primary 负责写入，Secondary 复制 Oplog；Primary 故障后多数派选出新 Primary，写关注可控制确认级别。
</td>
</tr>
<tr>
<td>
MongoDB 事务（4.0+）与 MySQL 事务对比
</td>
<td>
数据一致性保障，考察数据库选型能力
</td>
<td>
答：MySQL 事务是关系型数据库的基础能力，适合强一致多表操作；MongoDB 4.0+ 支持多文档事务，但更推荐通过合理文档建模把相关数据聚合在一个文档内，减少跨文档事务。
</td>
</tr>
<tr>
<td>
ES 与 MongoDB 在搜索场景的技术选型
</td>
<td>
两者定位不同，考察架构设计能力
</td>
<td>
答：MongoDB 适合业务数据存储和按文档模型查询，Elasticsearch 适合全文检索、复杂搜索和相关性排序。常见架构是 MongoDB 做主存储，ES 做搜索索引，通过 Change Stream/CDC 同步。
</td>
</tr>
<tr>
<td>
Change Stream 与 Canal + Binlog 的对比
</td>
<td>
实时数据同步方案选型
</td>
<td>
答：Change Stream 是 MongoDB 原生变更订阅，适合同步 MongoDB 数据变化；Canal + Binlog 面向 MySQL 生态。比较时看数据源、可靠性、延迟、断点续传和运维复杂度。
</td>
</tr>
<tr>
<td>
MongoDB Atlas Vector Search 与 pgvector 对比
</td>
<td>
向量检索方案选型，Agent 知识库核心
</td>
<td>
答：Atlas Vector Search 适合已经使用 MongoDB Atlas、希望文档和向量一体化的场景；pgvector 适合 PostgreSQL 体系内的小中规模向量检索。大规模高性能检索再考虑专用向量库。
</td>
</tr>
</table>

---

#### 13、Oplog 机制深挖

**难度级别**：⭐⭐~⭐⭐⭐⭐（幂等性、固定集合、复制延迟）

##### 基础题：Oplog 是什么？存在哪里？有什么特点？

Oplog（Operations Log）是 MongoDB 副本集的**操作日志**，用于数据复制：

1. **存储位置**：`local` 数据库的 `oplog.rs` 集合（固定集合，Capped Collection）

1. **特点**：

  - 记录所有写操作（增删改）

  - 按时间顺序追加写入

  - 固定大小，循环覆盖旧数据

  - 从节点拉取 Oplog 并重放

##### 进阶题：Oplog 的幂等性设计是怎样的？固定集合大小如何影响复制？Oplog 窗口与复制延迟有什么关系？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 幂等性设计
- 固定集合大小
- Oplog 窗口与复制延迟
- Agent 场景实践
- 操作类型幂等：insert、update、delete 都包含完整操作信息
- 重放安全：从节点重放 Oplog 时，重复执行不会产生副作用

**2️⃣ Impressive Answer**

Oplog 是 MongoDB 副本集复制的**核心机制**，设计要点包括：

1. **幂等性设计**

  - **操作类型幂等**：`insert`、`update`、`delete` 都包含完整操作信息

  - **重放安全**：从节点重放 Oplog 时，重复执行不会产生副作用

  - **$inc 操作符**：使用 `$inc: {count: 1}` 而非 `count++`，保证重放一致性

  - **Upsert 操作**：`update` 带 `upsert: true`，避免重复插入

1. **固定集合大小**

  - **默认大小**：Windows 1GB，Linux/macOS 5% 可用磁盘空间（最小 1GB）

  - **影响范围**：决定 Oplog 窗口时间（能保留多长时间的操作历史）

  - **配置建议**：高写入场景手动调大，避免 Oplog 覆盖过快

  - **查看大小**：`rs.printReplicationInfo()` 查看 Oplog 大小和窗口时间

1. **Oplog 窗口与复制延迟**

  - **Oplog 窗口**：Oplog 能保留的时间范围，窗口 = Oplog 大小 / 写入速率

  - **复制延迟**：从节点落后主节点的时间，`rs.printSlaveReplicationInfo()` 查看

  - **脱离同步**：复制延迟 > Oplog 窗口时，从节点无法找到起始点，需要全量同步

  - **风险场景**：批量导入、长时间维护后重启、从节点宕机过久

1. **Agent 场景实践**

  - 会话数据高写入：监控复制延迟，Oplog 大小配置充足

  - 批量导入操作：先暂停从节点，导入后再恢复，避免脱离同步

  - 告警配置：复制延迟超过阈值时告警

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
简单描述 Oplog 功能
</td>
<td>
系统阐述幂等性→固定集合→复制延迟三层机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道幂等性设计原理
</td>
<td>
深入 $inc、Upsert、Oplog 窗口计算
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体配置方案
</td>
<td>
结合 Agent 会话、批量导入给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本复制机制
</td>
<td>
深入理解 Oplog 设计和复制延迟风险
</td>
</tr>
</table>

##### 场景题：Oplog 窗口过小导致从节点脱离同步时如何排查和处理？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 排查步骤
- 处理方案
- 预防措施
- Agent 场景应用
- 查看复制延迟：rs.printSlaveReplicationInfo()，检查从节点落后时间
- 查看 Oplog 窗口：rs.printReplicationInfo()，检查 Oplog 大小和窗口时间

**2️⃣ Impressive Answer**

Oplog 窗口过小导致从节点脱离同步的**排查和处理流程**：

1. **排查步骤**

  - **查看复制延迟**：`rs.printSlaveReplicationInfo()`，检查从节点落后时间

  - **查看 Oplog 窗口**：`rs.printReplicationInfo()`，检查 Oplog 大小和窗口时间

  - **检查从节点状态**：`rs.status()`，查看从节点 `stateStr` 是否为 `RECOVERING`

  - **查看日志**：`mongod.log` 搜索 "replSet" 关键字，确认脱离同步原因

1. **处理方案**

  - **方案一：全量同步（Initial Sync）**

    - 从节点清空数据 → 从主节点拉取完整数据 → 重放 Oplog

    - 缺点：耗时长、影响主节点性能、从节点不可用

  - **方案二：调整 Oplog 大小**

    - 停止主节点 → 以 `--oplogSize` 参数重启 → 从节点自动同步

    - 推荐大小：写入量 × 最大容忍延迟时间（如 10GB 可保留 24 小时）

  - **方案三：从节点快照恢复**

    - 对主节点做快照 → 从节点恢复快照 → 重放 Oplog

    - 优点：比全量同步快，适合大集群

1. **预防措施**

  - **监控告警**：复制延迟超过 Oplog 窗口的 50% 时告警

  - **定期检查**：`rs.printReplicationInfo()` 定期查看 Oplog 使用率

  - **容量规划**：根据业务写入量增长，提前规划 Oplog 大小

1. **Agent 场景应用**

  - 会话数据高写入：Oplog 大小配置 20GB+，避免批量导入导致脱离同步

  - 从节点维护：维护时间不超过 Oplog 窗口，避免全量同步

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
简单说&quot;全量同步&quot;
</td>
<td>
系统阐述排查→处理→预防完整流程
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 Oplog 窗口计算
</td>
<td>
深入复制延迟监控、Oplog 大小调整
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体排查命令
</td>
<td>
结合 Agent 场景给出预防和处理方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
知道从节点会脱离同步
</td>
<td>
具备故障排查和容量规划能力
</td>
</tr>
</table>

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
MongoDB 副本集选举机制（Raft 协议）
</td>
<td>
高可用基础，与 Oplog 复制配合
</td>
<td>
答：MongoDB 副本集通过心跳和选举保证高可用，Primary 负责写入，Secondary 复制 Oplog；Primary 故障后多数派选出新 Primary，写关注可控制确认级别。
</td>
</tr>
<tr>
<td>
MongoDB 事务（4.0+）与 MySQL 事务对比
</td>
<td>
数据一致性保障，考察数据库选型能力
</td>
<td>
答：MySQL 事务是关系型数据库的基础能力，适合强一致多表操作；MongoDB 4.0+ 支持多文档事务，但更推荐通过合理文档建模把相关数据聚合在一个文档内，减少跨文档事务。
</td>
</tr>
<tr>
<td>
MongoDB 写关注（WriteConcern）与读关注（ReadConcern）
</td>
<td>
一致性级别配置，与 Oplog 复制配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
<tr>
<td>
MongoDB 监控与可观测性
</td>
<td>
复制延迟监控，告警体系搭建
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
MongoDB 分片集群架构
</td>
<td>
水平扩展方案，与副本集配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
</table>

---

#### 14、文档设计模式：嵌套 vs 引用

**难度级别**：⭐⭐~⭐⭐⭐⭐（Subset、Bucket、Computed、Outlier、Extended Reference、Schema Versioning）

##### 基础题：什么时候用嵌套文档，什么时候用引用？各有什么优缺点？

**嵌套文档**：适合一对多关系、数据一起读取、子文档较少（<100 个）
**优点**：查询快（一次读取）、原子性更新
**缺点**：文档大小限制 16MB、嵌套过深查询复杂

**引用**：适合多对多关系、数据独立读取、子文档较多
**优点**：避免 16MB 限制、灵活查询
**缺点**：需要多次查询（$lookup 连表）

##### 进阶题：MongoDB 有哪些经典文档设计模式？（Subset、Bucket、Computed、Outlier、Extended Reference、Schema Versioning）各自解决什么问题？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Subset Pattern（子集模式）
- Bucket Pattern（分桶模式）
- Computed Pattern（计算模式）
- Outlier Pattern（异常值模式）
- Extended Reference Pattern（扩展引用模式）
- Schema Versioning Pattern（模式版本模式）

**2️⃣ Impressive Answer**

MongoDB 有**六大经典文档设计模式**，解决不同场景问题：

1. **Subset Pattern（子集模式）**

  - **问题**：大文档嵌套太多子数据，超过 16MB 限制

  - **方案**：只嵌入常用子集，其他数据引用存储

  - **场景**：商品详情只嵌入前 10 条评论，其他评论单独存储

1. **Bucket Pattern（分桶模式）**

  - **问题**：小文档过多，查询和索引开销大

  - **方案**：按时间/类别分桶，将多个小文档合并为一个大文档

  - **场景**：Agent 会话消息按日期分桶，每天一个文档，包含当天所有消息

  - **优势**：减少文档数量、提升查询性能、方便时间范围查询

1. **Computed Pattern（计算模式）**

  - **问题**：频繁聚合计算（如求和、计数）性能差

  - **方案**：预计算结果并存储，查询时直接读取

  - **场景**：会话统计预存消息数、Token 消耗，避免实时聚合

1. **Outlier Pattern（异常值模式）**

  - **问题**：大部分数据相似，少数异常值导致文档过大

  - **方案**：正常值嵌入，异常值单独存储

  - **场景**：用户大部分配置项少，少数用户配置项多，异常配置单独存

1. **Extended Reference Pattern（扩展引用模式）**

  - **问题**：引用需要频繁 $lookup，性能差

  - **方案**：引用时嵌入常用字段，减少连表

  - **场景**：订单引用用户时，嵌入用户名和头像，避免每次查询用户表

1. **Schema Versioning Pattern（模式版本模式）**

  - **问题**：文档结构频繁变更，兼容性差

  - **方案**：每个文档添加 `schema_version` 字段，根据版本处理

  - **场景**：Agent 会话结构升级，旧版本数据保留 `schema_version: 1`，新版本 `schema_version: 2`

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
只知道嵌套和引用
</td>
<td>
系统阐述六大设计模式及其应用场景
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道分桶、计算等模式
</td>
<td>
深入 Subset、Bucket、Computed 等模式原理
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体应用方案
</td>
<td>
结合 Agent 会话、订单、用户配置给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本文档设计
</td>
<td>
深入理解设计模式，具备架构设计能力
</td>
</tr>
</table>

##### 场景题：Agent 会话消息如何用 Bucket Pattern 分桶存储？设计方案是什么？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 文档结构设计
- 分桶策略
- 查询优化
- 写入优化
- 优势总结
- 按日期分桶：每个会话每天一个 Bucket，避免单文档过大

**2️⃣ Impressive Answer**

Agent 会话消息用 Bucket Pattern 分桶存储的**设计方案**：

1. **文档结构设计**
    `\``json{"_id": ObjectId("..."),"userId": "user123","sessionId": "session456","bucketDate": "2024-01-15","messages": [{"role": "user", "content": "你好", "timestamp": ISODate("2024-01-15T10:00:00Z")},{"role": "assistant", "content": "你好！", "timestamp": ISODate("2024-01-15T10:00:01Z")}],"messageCount": 2,"createdAt": ISODate("2024-01-15T00:00:00Z")}

````
```
````

1. **分桶策略**

  - **按日期分桶**：每个会话每天一个 Bucket，避免单文档过大

  - **消息数量限制**：单个 Bucket 消息数不超过 1000 条，超过则分多个 Bucket

  - **索引设计**：`{userId: 1, sessionId: 1, bucketDate: -1}` 复合索引

1. **查询优化**

  - **时间范围查询**：直接按 `bucketDate` 查询，避免扫描多个 Bucket

  - **分页查询**：先查 Bucket 列表，再查具体消息

  - **投影优化**：`projection` 只返回需要的消息字段

1. **写入优化**

  - **追加写入**：新消息追加到 `messages` 数组末尾

  - **批量更新**：使用 `$push` 批量插入消息

  - **文档锁**：同一会话同一天的消息写入同一文档，减少锁竞争

1. **优势总结**

  - **减少文档数量**：假设每天 100 万条消息，分桶后只需 1000 个文档

  - **提升查询性能**：时间范围查询只需扫描少量文档

  - **方便归档**：按日期归档历史数据

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
简单说&quot;按天存&quot;
</td>
<td>
系统阐述文档结构→分桶策略→查询优化→写入优化
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道索引设计和查询优化
</td>
<td>
深入复合索引、投影优化、批量更新
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体设计方案
</td>
<td>
给出完整的文档结构和查询方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解分桶概念
</td>
<td>
具备架构设计和性能优化能力
</td>
</tr>
</table>

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
MongoDB 文档模型与关系型数据库的区别
</td>
<td>
理解 MongoDB 设计哲学的基础
</td>
<td>
答：MongoDB 文档模型强调聚合数据放在一个文档中，适合结构灵活、读多写少的聚合查询；关系型数据库强调表结构和 Join，适合强约束、多表事务和复杂关系。
</td>
</tr>
<tr>
<td>
MongoDB 聚合管道（group/$lookup）
</td>
<td>
数据分析核心能力，与文档设计配合
</td>
<td>
答：MongoDB 聚合管道是把数据按 stage 流式处理，常见有 $match、$group、$lookup、$project。优化时把 $match 前置、让过滤字段命中索引，避免大集合上无限制 $lookup。
</td>
</tr>
<tr>
<td>
MongoDB 索引设计与优化
</td>
<td>
查询性能基础，与文档设计配合
</td>
<td>
答：数据库索引题要讲数据结构、匹配规则、回表成本、选择性和慢 SQL 验证，最后落到 explain。
</td>
</tr>
<tr>
<td>
MongoDB 16MB 文档限制与优化
</td>
<td>
文档大小限制，与嵌套设计相关
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
<tr>
<td>
MongoDB 时序数据存储（Time Series Collection）
</td>
<td>
时序数据存储，与分桶模式配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
</table>

---

## MongoDB 一致性与并发

#### 15、写关注（WriteConcern）与读关注（ReadConcern）

**难度级别**：⭐⭐~⭐⭐⭐⭐（w:1/w:majority、local/majority/linearizable/snapshot）

##### 基础题：WriteConcern w:1 和 w:majority 有什么区别？

**w:1**：写入主节点成功即返回，性能好但可能丢数据（主节点崩溃未复制到从节点）
**w:majority**：写入大多数节点成功才返回，性能差但数据安全（至少一个从节点写入成功）

##### 进阶题：ReadConcern 的 local/majority/linearizable/snapshot 四种级别分别是什么含义？与隔离性有什么关系？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- local（默认）
- majority
- linearizable
- snapshot
- Agent 场景应用
- 含义：从主节点或从节点读取最新数据，不保证已复制到大多数节点

**2️⃣ Impressive Answer**

ReadConcern 定义了**读操作的隔离级别**，与数据库事务隔离性类似：

1. **local（默认）**

  - **含义**：从主节点或从节点读取最新数据，不保证已复制到大多数节点

  - **隔离性**：读未提交（Read Uncommitted）级别

  - **场景**：对一致性要求不高的场景，如日志、监控数据

1. **majority**

  - **含义**：只读已复制到大多数节点的数据，保证数据不回滚

  - **隔离性**：读已提交（Read Committed）级别

  - **场景**：需要数据一致性的场景，如计费、订单

1. **linearizable**

  - **含义**：读取最新写入的数据，保证线性一致性（类似串行化）

  - **隔离性**：可串行化（Serializable）级别

  - **场景**：需要强一致性的场景，如库存扣减、余额查询

  - **代价**：只能从主节点读，性能差

1. **snapshot**

  - **含义**：读取事务开始时的快照数据，保证可重复读

  - **隔离性**：可重复读（Repeatable Read）级别

  - **场景**：多文档事务，需要读取一致的数据集

1. **Agent 场景应用**

  - 会话数据：`writeConcern: w:1` + `readConcern: local`，性能优先

  - 计费数据：`writeConcern: w:majority` + `readConcern: majority`，一致性优先

  - 余额查询：`readConcern: linearizable`，保证读到最新数据

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
简单描述级别含义
</td>
<td>
系统阐述四种级别及对应隔离性
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道隔离性关系
</td>
<td>
深入 Read Uncommitted→Read Committed→Serializable
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无场景应用
</td>
<td>
结合 Agent 会话、计费、余额给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本级别
</td>
<td>
深入理解隔离性和一致性权衡
</td>
</tr>
</table>

##### 场景题：Agent 计费数据如何配置强一致读写？会话数据如何配置？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 计费数据（强一致）
- 会话数据（最终一致）
- 用户余额（线性一致）
- 配置示例（Spring Boot）
- 性能对比
- WriteConcern：{w: "majority", j: true}，确保写入大多数节点且落盘

**2️⃣ Impressive Answer**

Agent 不同业务场景的**一致性配置策略**：

1. **计费数据（强一致）**

  - **WriteConcern**：`{w: "majority", j: true}`，确保写入大多数节点且落盘

  - **ReadConcern**：`majority`，确保读取已提交数据

  - **ReadPreference**：`primary`，只从主节点读

  - **理由**：计费数据不能丢，不能读脏数据，性能可以牺牲

1. **会话数据（最终一致）**

  - **WriteConcern**：`{w: 1, j: false}`，写入主节点即返回

  - **ReadConcern**：`local`，读取最新数据

  - **ReadPreference**：`secondaryPreferred`，优先从从节点读

  - **理由**：会话数据量大，性能优先，短暂不一致可接受

1. **用户余额（线性一致）**

  - **WriteConcern**：`{w: "majority", j: true}`

  - **ReadConcern**：`linearizable`，保证读到最新余额

  - **ReadPreference**：`primary`，只能从主节点读

  - **理由**：余额查询需要强一致性，避免超卖

1. **配置示例（Spring Boot）**
    `\``yamlspring:data:mongodb:uri: mongodb://localhost:27017/agent_dbwrite-concern: MAJORITYread-concern: MAJORITYread-preference: PRIMARY
    `\``

1. **性能对比**

  - 强一致配置：TPS 约 1000，延迟 10-50ms

  - 最终一致配置：TPS 约 5000，延迟 1-5ms

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
简单说&quot;w:majority&quot;
</td>
<td>
系统阐述计费→会话→余额三种配置策略
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ReadPreference 配置
</td>
<td>
深入 WriteConcern+ReadConcern+ReadPreference 组合
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体配置示例
</td>
<td>
给出 Spring Boot 配置和性能对比
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本配置
</td>
<td>
具备一致性权衡和配置优化能力
</td>
</tr>
</table>

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
MongoDB 事务（4.0+）与 MySQL 事务对比
</td>
<td>
数据一致性保障，考察数据库选型能力
</td>
<td>
答：MySQL 事务是关系型数据库的基础能力，适合强一致多表操作；MongoDB 4.0+ 支持多文档事务，但更推荐通过合理文档建模把相关数据聚合在一个文档内，减少跨文档事务。
</td>
</tr>
<tr>
<td>
MongoDB 副本集选举机制（Raft 协议）
</td>
<td>
高可用基础，与一致性配置配合
</td>
<td>
答：MongoDB 副本集通过心跳和选举保证高可用，Primary 负责写入，Secondary 复制 Oplog；Primary 故障后多数派选出新 Primary，写关注可控制确认级别。
</td>
</tr>
<tr>
<td>
MongoDB 因果一致性（Causal Consistency）
</td>
<td>
一致性级别，与 ReadConcern 配合
</td>
<td>
答：这类题要先说明一致性目标，再讲本地事务、消息事务、Outbox、幂等消费和补偿机制的取舍。
</td>
</tr>
<tr>
<td>
MongoDB 锁机制：从全局锁到文档级锁的演进
</td>
<td>
并发控制基础，与一致性配合
</td>
<td>
答：MySQL 题要从数据结构、事务隔离、锁/MVCC、执行计划和慢 SQL 优化展开；最后落到 explain、索引设计和业务一致性。
</td>
</tr>
<tr>
<td>
MongoDB 监控与可观测性
</td>
<td>
写入延迟监控，告警体系搭建
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
</table>

---

#### 16、锁机制：从全局锁到文档级锁的演进

**难度级别**：⭐⭐~⭐⭐⭐⭐（意向锁、乐观并发控制、db.currentOp）

##### 基础题：MongoDB 的锁粒度是什么级别？

MongoDB 3.0+ 使用 WiredTiger 存储引擎，锁粒度为**文档级锁**（Document-Level Locking）。

- 3.0 之前：全局锁（Global Lock），整个数据库被锁定

- 3.0-3.2：数据库级锁（Database-Level Locking）

- 3.2+：文档级锁，支持并发读写

##### 进阶题：意向锁（IS/IX）的作用是什么？WiredTiger 的乐观并发控制如何工作？如何用 db.currentOp() 排查锁等待？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 意向锁（IS/IX）
- WiredTiger 乐观并发控制
- db.currentOp() 排查锁等待
- Agent 场景应用
- IS（意向共享锁）：事务打算读取文档，允许其他事务读取
- IX（意向排他锁）：事务打算修改文档，允许其他事务读取但不允许修改

**2️⃣ Impressive Answer**

MongoDB 锁机制从全局锁演进到文档级锁，**核心机制**包括：

1. **意向锁（IS/IX）**

  - **IS（意向共享锁）**：事务打算读取文档，允许其他事务读取

  - **IX（意向排他锁）**：事务打算修改文档，允许其他事务读取但不允许修改

  - **作用**：避免锁冲突，提高并发效率

  - **兼容性**：IS 兼容 IS/IX，IX 兼容 IS，IX 不兼容 IX

1. **WiredTiger 乐观并发控制**

  - **无锁读取**：读操作不加锁，通过快照读取历史版本

  - **写时复制**：修改文档时创建新版本，旧版本保留

  - **冲突检测**：提交时检查是否有其他事务修改了相同文档

  - **重试机制**：冲突时自动重试（最多 10 次）

1. **db.currentOp() 排查锁等待**

  - **查看当前操作**：`db.currentOp({active: true, secs_running: {$gt: 5}})`

  - **关键字段**：

    - `op`：操作类型（insert/update/query）

    - `secs_running`：运行时间（秒）

    - `lock`：锁类型（r/w/R/W）

    - `waitingForLock`：是否等待锁

    - `microsecs_running`：运行时间（微秒）

  - **终止操作**：`db.killOp(opId)`，谨慎使用

1. **Agent 场景应用**

  - 会话高并发写入：文档级锁保证并发性能

  - 慢查询排查：`db.currentOp()` 定位长时间运行的操作

  - 锁竞争优化：避免长时间事务，减少锁持有时间

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
简单描述锁粒度
</td>
<td>
系统阐述意向锁→乐观并发→锁排查完整机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道意向锁作用
</td>
<td>
深入 IS/IX 兼容性、冲突检测、重试机制
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体排查命令
</td>
<td>
结合 Agent 场景给出排查和优化方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本锁机制
</td>
<td>
深入理解并发控制和故障排查
</td>
</tr>
</table>

##### 场景题：高并发写入时出现锁竞争如何分析和优化？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 问题分析
- 优化方案
- Agent 场景优化
- 监控指标：wiredTiger.cache.pages read into cache（读入页数）和 pages evicted（驱逐页数）
- 查看锁等待：db.currentOp({waitingForLock: true}) 查看等待锁的操作
- 查看慢查询：db.setProfilingLevel(1, {slowms: 100}) 记录慢查询

**2️⃣ Impressive Answer**

高并发写入锁竞争的**分析和优化流程**：

1. **问题分析**

  - **监控指标**：`wiredTiger.cache.pages read into cache`（读入页数）和 `pages evicted`（驱逐页数）

  - **查看锁等待**：`db.currentOp({waitingForLock: true})` 查看等待锁的操作

  - **查看慢查询**：`db.setProfilingLevel(1, {slowms: 100})` 记录慢查询

1. **优化方案**

  - **方案一：优化文档设计**

    - 避免大文档：拆分嵌套文档，减少单文档大小

    - 分散写入：按用户 ID 分片，避免热点文档

  - **方案二：优化索引**

    - 复合索引：ESR 规则（Equality → Sort → Range）

    - 覆盖索引：查询字段全在索引中，避免回表

  - **方案三：优化写入策略**

    - 批量写入：`insertMany` + `ordered: false`

    - 异步写入：`writeConcern: w:1`，不等待从节点确认

  - **方案四：架构优化**

    - 读写分离：读请求路由到从节点

    - 分片集群：水平扩展，分散写入压力

1. **Agent 场景优化**

  - 会话写入：按用户 ID 分片，避免同一会话高并发写入

  - 批量导入：使用 `insertMany` + `ordered: false`，失败不中断

  - 监控告警：锁等待时间超过阈值时告警

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
简单说&quot;加索引&quot;
</td>
<td>
系统阐述分析→优化方案→架构优化完整流程
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道监控指标
</td>
<td>
深入 wiredTiger cache、锁等待、慢查询监控
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体优化方案
</td>
<td>
结合 Agent 场景给出文档设计、索引、写入策略优化
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本优化
</td>
<td>
具备性能分析和架构优化能力
</td>
</tr>
</table>

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
MongoDB 存储引擎与底层原理
</td>
<td>
WiredTiger 存储引擎基础，与锁机制配合
</td>
<td>
答：MySQL 题要从数据结构、事务隔离、锁/MVCC、执行计划和慢 SQL 优化展开；最后落到 explain、索引设计和业务一致性。
</td>
</tr>
<tr>
<td>
MongoDB 写关注（WriteConcern）与读关注（ReadConcern）
</td>
<td>
一致性级别配置，与并发控制配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
<tr>
<td>
MongoDB 监控与可观测性
</td>
<td>
锁等待监控，告警体系搭建
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
MongoDB 索引设计与优化
</td>
<td>
查询性能基础，与锁竞争优化配合
</td>
<td>
答：数据库索引题要讲数据结构、匹配规则、回表成本、选择性和慢 SQL 验证，最后落到 explain。
</td>
</tr>
<tr>
<td>
MongoDB 分片集群架构
</td>
<td>
水平扩展方案，分散写入压力
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
</table>

---

#### 17、因果一致性（Causal Consistency）

**难度级别**：⭐⭐~⭐⭐⭐⭐（ClientSession、afterClusterTime、线性一致性）

##### 基础题：什么是因果一致性？为什么副本集读写会有一致性问题？

**因果一致性**：保证有因果关系的操作按顺序执行，如果操作 A 影响 B，则任何看到 B 的节点必须先看到 A。

**副本集一致性问题**：主节点写入后立即从从节点读取，可能读不到刚写入的数据（复制延迟导致）。

##### 进阶题：ClientSession + afterClusterTime 如何实现因果一致性？与线性一致性有什么区别？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- ClientSession（客户端会话）
- afterClusterTime（集群时间）
- 因果一致性实现
- 与线性一致性的区别
- Agent 场景应用
- 定义：客户端与 MongoDB 之间的逻辑会话，包含操作序列

**2️⃣ Impressive Answer**

因果一致性是 MongoDB 副本集的**重要一致性保证**，实现机制包括：

1. **ClientSession（客户端会话）**

  - **定义**：客户端与 MongoDB 之间的逻辑会话，包含操作序列

  - **作用**：跟踪会话内的所有操作，保证因果顺序

  - **创建方式**：`client.startSession()` 或驱动自动创建

1. **afterClusterTime（集群时间）**

  - **定义**：MongoDB 全局递增的时间戳（包含时间 + 计数器）

  - **作用**：标记操作发生的时刻，用于因果排序

  - **使用方式**：`find().readConcern("majority").afterClusterTime(clusterTime)`

1. **因果一致性实现**

  - **写操作**：记录当前 `clusterTime`

  - **读操作**：使用 `afterClusterTime`，只读时间戳之后的数据

  - **保证**：如果写操作发生在读操作之前，读操作一定能读到写操作的结果

1. **与线性一致性的区别**

  - **因果一致性**：只保证有因果关系的操作顺序，无因果关系的操作可以乱序

  - **线性一致性**：所有操作按全局顺序执行，保证强一致

  - **性能对比**：因果一致性好于线性一致性，线性一致性只能从主节点读

  - **适用场景**：因果一致性适合大多数业务，线性一致性适合库存扣减等强一致场景

1. **Agent 场景应用**

  - 会话写入后立即读取：使用 `ClientSession` + `afterClusterTime` 保证读到最新数据

  - 多步骤操作：在同一个 `ClientSession` 中执行，保证因果顺序

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
简单描述因果一致性
</td>
<td>
系统阐述 ClientSession→afterClusterTime→实现机制
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 afterClusterTime 作用
</td>
<td>
深入集群时间、因果排序、与线性一致性区别
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无场景应用
</td>
<td>
结合 Agent 会话给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本概念
</td>
<td>
深入理解一致性和权衡
</td>
</tr>
</table>

##### 场景题：Agent 写入会话后立即读取，如何保证读到最新数据？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 方案一：强一致配置
- 方案二：因果一致性（推荐）
- 方案三：读后写缓存
- Agent 场景最佳实践
- WriteConcern：{w: "majority", j: true}
- ReadConcern：majority

**2️⃣ Impressive Answer**

Agent 写入会话后立即读取的**一致性保证方案**：

1. **方案一：强一致配置**

  - **WriteConcern**：`{w: "majority", j: true}`

  - **ReadConcern**：`majority`

  - **ReadPreference**：`primary`

  - **缺点**：性能差，只能从主节点读

1. **方案二：因果一致性（推荐）**

  - **使用 ClientSession**：
      `\``javascriptconst session = client.startSession();try {session.startTransaction();// 写入会话await db.sessions.insertOne({userId: "user123", content: "你好"}, {session});// 立即读取const result = await db.sessions.findOne({userId: "user123"}, {session,readConcern: {level: "majority"},readPreference: "primary"});await session.commitTransaction();} finally {session.endSession();}

````
    ```

*   **优势**：性能好，保证因果顺序
````

1. **方案三：读后写缓存**

  - **写入后缓存**：写入成功后，将数据缓存到 Redis

  - **读取时先查缓存**：优先从缓存读取，缓存未命中再查数据库

  - **缺点**：引入缓存复杂度，缓存一致性需要处理

1. **Agent 场景最佳实践**

  - 会话写入后立即读取：使用 `ClientSession` + `afterClusterTime`

  - 性能要求高：使用读后写缓存

  - 数据一致性要求高：使用强一致配置

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
简单说&quot;从主节点读&quot;
</td>
<td>
系统阐述三种方案及优劣
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 ClientSession 实现
</td>
<td>
深入事务、afterClusterTime、缓存方案
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体代码示例
</td>
<td>
给出完整代码实现和最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本配置
</td>
<td>
具备一致性方案设计和实现能力
</td>
</tr>
</table>

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
MongoDB 写关注（WriteConcern）与读关注（ReadConcern）
</td>
<td>
一致性级别配置，与因果一致性配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
<tr>
<td>
MongoDB 事务（4.0+）与 MySQL 事务对比
</td>
<td>
数据一致性保障，考察数据库选型能力
</td>
<td>
答：MySQL 事务是关系型数据库的基础能力，适合强一致多表操作；MongoDB 4.0+ 支持多文档事务，但更推荐通过合理文档建模把相关数据聚合在一个文档内，减少跨文档事务。
</td>
</tr>
<tr>
<td>
MongoDB 副本集选举机制（Raft 协议）
</td>
<td>
高可用基础，与一致性配合
</td>
<td>
答：MongoDB 副本集通过心跳和选举保证高可用，Primary 负责写入，Secondary 复制 Oplog；Primary 故障后多数派选出新 Primary，写关注可控制确认级别。
</td>
</tr>
<tr>
<td>
MongoDB 锁机制：从全局锁到文档级锁的演进
</td>
<td>
并发控制基础，与一致性配合
</td>
<td>
答：MySQL 题要从数据结构、事务隔离、锁/MVCC、执行计划和慢 SQL 优化展开；最后落到 explain、索引设计和业务一致性。
</td>
</tr>
</table>

---

## MongoDB 运维与架构

#### 18、连接池与驱动配置优化

**难度级别**：⭐⭐~⭐⭐⭐⭐（maxPoolSize、minPoolSize、waitQueueTimeoutMS、serverSelectionTimeoutMS）

##### 基础题：MongoDB 驱动的连接池是怎么工作的？

MongoDB 驱动使用**连接池**管理数据库连接：

1. 应用启动时创建一定数量的连接

1. 执行操作时从连接池获取连接

1. 操作完成后将连接归还连接池

1. 连接池自动维护连接健康状态

##### 进阶题：maxPoolSize/minPoolSize/waitQueueTimeoutMS/serverSelectionTimeoutMS 各参数的含义是什么？连接泄漏如何排查？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 核心参数
- 连接泄漏排查
- 连接池配置建议
- Agent 场景优化
- maxPoolSize：（默认 100）：最大连接数，超过则等待
- minPoolSize：（默认 0）：最小连接数，保持连接池中有这么多连接

**2️⃣ Impressive Answer**

MongoDB 驱动连接池的**核心参数**和连接泄漏排查：

1. **核心参数**

  - **maxPoolSize**（默认 100）：最大连接数，超过则等待

  - **minPoolSize**（默认 0）：最小连接数，保持连接池中有这么多连接

  - **waitQueueTimeoutMS**（默认 0）：等待连接超时时间（毫秒），0 表示无限等待

  - **serverSelectionTimeoutMS**（默认 30000）：选择服务器超时时间（毫秒）

  - **maxIdleTimeMS**（默认 0）：连接最大空闲时间（毫秒），超过则关闭

  - **connectTimeoutMS**（默认 10000）：连接超时时间（毫秒）

1. **连接泄漏排查**

  - **监控指标**：`db.serverStatus().connections` 查看当前连接数

  - **查看连接来源**：`db.currentOp()` 查看当前操作和客户端信息

  - **连接数告警**：当前连接数超过 `maxPoolSize * 0.8` 时告警

  - **代码审查**：检查是否正确关闭连接（如使用 try-finally）

1. **连接池配置建议**

  - **maxPoolSize**：根据应用并发量设置，一般 50-200

  - **minPoolSize**：设置为 `maxPoolSize * 0.5`，避免冷启动

  - **waitQueueTimeoutMS**：设置为 5000，避免无限等待

  - **maxIdleTimeMS**：设置为 60000，关闭空闲连接

1. **Agent 场景优化**

  - 会话高并发：`maxPoolSize: 200`，`minPoolSize: 100`

  - 监控告警：连接数超过 160 时告警

  - 连接泄漏排查：定期检查 `db.serverStatus().connections`

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
简单描述参数含义
</td>
<td>
系统阐述核心参数→连接泄漏排查→配置建议
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道连接泄漏排查方法
</td>
<td>
深入连接监控、告警、代码审查
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体配置建议
</td>
<td>
结合 Agent 场景给出配置和监控方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本参数
</td>
<td>
具备连接池优化和故障排查能力
</td>
</tr>
</table>

##### 场景题：Spring Boot 集成 MongoDB 的连接池最佳配置是什么？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- application.yml 配置
- 配置说明
- 监控配置
- Agent 场景最佳实践
- max-connections-per-host：每个主机最大连接数，根据应用并发量设置
- min-connections-per-host：每个主机最小连接数，避免冷启动

**2️⃣ Impressive Answer**

Spring Boot 集成 MongoDB 的**连接池最佳配置**：

1. **application.yml 配置**
    `\``yamlspring:data:mongodb:uri: mongodb://localhost:27017/agent_dbauto-index-creation: true# 连接池配置min-connections-per-host: 50max-connections-per-host: 200max-connection-idle-time: 60000max-connection-life-time: 120000connection-timeout: 10000socket-timeout: 30000# 服务器选择超时server-selection-timeout: 30000# 等待队列超时wait-queue-timeout: 5000# 心跳频率heartbeat-frequency: 10000# 心跳连接超时heartbeat-connect-timeout: 10000# 心跳 socket 超时heartbeat-socket-timeout: 30000

````
```
````

1. **配置说明**

  - **max-connections-per-host**：每个主机最大连接数，根据应用并发量设置

  - **min-connections-per-host**：每个主机最小连接数，避免冷启动

  - **max-connection-idle-time**：连接最大空闲时间，关闭空闲连接

  - **max-connection-life-time**：连接最大生命周期，定期重建连接

  - **connection-timeout**：连接超时时间，避免长时间等待

  - **socket-timeout**：Socket 超时时间，避免长时间阻塞

1. **监控配置**

  - **Actuator 监控**：启用 `spring-boot-starter-actuator`，查看 `/actuator/metrics/mongo.driver.pool.size`

  - **日志配置**：设置 `logging.level.org.mongodb.driver.cluster: DEBUG`，查看连接池日志

  - **告警配置**：连接数超过阈值时告警

1. **Agent 场景最佳实践**

  - 会话高并发：`max-connections-per-host: 200`

  - 监控告警：连接数超过 160 时告警

  - 日志调试：开发环境开启 DEBUG 日志，生产环境关闭

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
简单说&quot;配置连接池&quot;
</td>
<td>
系统阐述配置文件→参数说明→监控配置
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道参数含义和监控方法
</td>
<td>
深入连接池参数、Actuator 监控、日志配置
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体配置示例
</td>
<td>
给出完整配置文件和最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本配置
</td>
<td>
具备连接池优化和监控能力
</td>
</tr>
</table>

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
MongoDB 监控与可观测性
</td>
<td>
连接数监控，告警体系搭建
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
MongoDB 副本集选举机制（Raft 协议）
</td>
<td>
高可用基础，与连接池配合
</td>
<td>
答：MongoDB 副本集通过心跳和选举保证高可用，Primary 负责写入，Secondary 复制 Oplog；Primary 故障后多数派选出新 Primary，写关注可控制确认级别。
</td>
</tr>
<tr>
<td>
MongoDB 写关注（WriteConcern）与读关注（ReadConcern）
</td>
<td>
一致性级别配置，与连接池配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
<tr>
<td>
MongoDB 锁机制：从全局锁到文档级锁的演进
</td>
<td>
并发控制基础，与连接池配合
</td>
<td>
答：MySQL 题要从数据结构、事务隔离、锁/MVCC、执行计划和慢 SQL 优化展开；最后落到 explain、索引设计和业务一致性。
</td>
</tr>
</table>

---

#### 19、时序数据存储（Time Series Collection）

**难度级别**：⭐⭐~⭐⭐⭐⭐（列式压缩、granularity、性能对比）

##### 基础题：MongoDB 5.0+ 的 Time Series Collection 是什么？和普通集合有什么区别？

**Time Series Collection**：MongoDB 5.0+ 引入的时序数据集合，专门优化时序数据存储和查询。

**与普通集合的区别**：

1. 自动按时间分桶存储

1. 内部列式压缩，节省存储空间

1. 自动优化时序查询性能

1. 支持时间范围聚合查询

##### 进阶题：时序集合的内部存储优化（列式压缩）是怎样的？granularity 如何配置？与普通集合的性能对比如何？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 内部存储优化
- granularity 配置
- 性能对比
- Agent 场景应用
- 自动分桶：按时间范围将数据分桶存储，默认桶大小 1 小时
- 列式压缩：同一列的数据连续存储，压缩比高（如时间戳压缩比 90%）

**2️⃣ Impressive Answer**

Time Series Collection 是 MongoDB 时序数据的**专用存储引擎**，优化机制包括：

1. **内部存储优化**

  - **自动分桶**：按时间范围将数据分桶存储，默认桶大小 1 小时

  - **列式压缩**：同一列的数据连续存储，压缩比高（如时间戳压缩比 90%）

  - **数据优化**：自动删除重复数据，减少存储空间

  - **索引优化**：自动创建时间索引，加速时间范围查询

1. **granularity 配置**

  - **定义**：时间粒度，决定分桶大小

  - **可选值**：

    - `seconds`：秒级粒度，适合高频数据

    - `minutes`：分钟级粒度，适合分钟级数据

    - `hours`：小时级粒度，适合小时级数据

  - **配置方式**：`createCollection({timeseries: {timeField: "timestamp", granularity: "minutes"}})`

  - **选择建议**：根据数据频率选择，数据频率越高，粒度越小

1. **性能对比**

  - **存储空间**：时序集合比普通集合节省 50-70% 空间

  - **写入性能**：时序集合比普通集合快 2-3 倍

  - **查询性能**：时间范围查询比普通集合快 5-10 倍

  - **聚合性能**：时间聚合查询比普通集合快 3-5 倍

1. **Agent 场景应用**

  - 调用链路指标：使用时序集合存储，granularity 设置为 `seconds`

  - 用户行为埋点：使用时序集合存储，granularity 设置为 `minutes`

  - 系统监控数据：使用时序集合存储，granularity 设置为 `hours`

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
简单描述时序集合
</td>
<td>
系统阐述存储优化→granularity 配置→性能对比
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道列式压缩原理
</td>
<td>
深入自动分桶、列式压缩、索引优化
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体应用场景
</td>
<td>
结合 Agent 调用链路、埋点、监控给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本概念
</td>
<td>
深入理解时序存储优化和应用
</td>
</tr>
</table>

##### 场景题：Agent 调用链路的指标数据如何用时序集合存储？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 集合创建
- 文档结构设计
- 索引设计
- 查询优化
- 优势总结
- 时间索引：自动创建，加速时间范围查询

**2️⃣ Impressive Answer**

Agent 调用链路指标数据用时序集合存储的**设计方案**：

1. **集合创建**
    `\``javascriptdb.createCollection("agent_metrics", {timeseries: {timeField: "timestamp",metaField: "metadata",granularity: "seconds"}})

````
```
````

1. **文档结构设计**
    `\``json{"timestamp": ISODate("2024-01-15T10:00:00Z"),"metadata": {"agentId": "agent123","sessionId": "session456","userId": "user789"},"metrics": {"latency": 123,"tokenCount": 456,"requestCount": 1,"errorCount": 0}}

````
```
````

1. **索引设计**

  - **时间索引**：自动创建，加速时间范围查询

  - **元数据索引**：手动创建，加速元数据查询

`\``javascriptdb.agent_metrics.createIndex({"metadata.agentId": 1, "metadata.sessionId": 1})

`\``

1. **查询优化**

  - **时间范围查询**：
      `\``javascriptdb.agent_metrics.find({"metadata.agentId": "agent123","timestamp": {$gte: ISODate("2024-01-15T00:00:00Z"),$lte: ISODate("2024-01-15T23:59:59Z")}})

````
    ```

*   **聚合查询**：

    ```javascript
    db.agent_metrics.aggregate([
      {
        $match: {
          "metadata.agentId": "agent123",
          "timestamp": {
            $gte: ISODate("2024-01-15T00:00:00Z"),
            $lte: ISODate("2024-01-15T23:59:59Z")
          }
        }
      },
      {
        $group: {
          _id: {
            $dateToString: {format: "%Y-%m-%d %H:%M", date: "$timestamp"}
          },
          avgLatency: {$avg: "$metrics.latency"},
          totalTokenCount: {$sum: "$metrics.tokenCount"}
        }
      }
    ])
````

````
    ```
````

1. **优势总结**

  - **存储优化**：列式压缩节省 60% 存储空间

  - **查询优化**：时间范围查询快 8 倍

  - **聚合优化**：时间聚合查询快 4 倍

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
简单说&quot;创建时序集合&quot;
</td>
<td>
系统阐述集合创建→文档结构→索引设计→查询优化
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道文档结构设计
</td>
<td>
深入 metaField、时间索引、聚合查询
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体设计方案
</td>
<td>
给出完整的集合创建、文档结构、查询示例
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本概念
</td>
<td>
具备时序数据设计和优化能力
</td>
</tr>
</table>

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
MongoDB 文档设计模式：嵌套 vs 引用
</td>
<td>
文档设计基础，与时序集合配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
<tr>
<td>
MongoDB 聚合管道（group/$lookup）
</td>
<td>
数据分析核心能力，与时序查询配合
</td>
<td>
答：MongoDB 聚合管道是把数据按 stage 流式处理，常见有 $match、$group、$lookup、$project。优化时把 $match 前置、让过滤字段命中索引，避免大集合上无限制 $lookup。
</td>
</tr>
<tr>
<td>
MongoDB 索引设计与优化
</td>
<td>
查询性能基础，与时序集合配合
</td>
<td>
答：数据库索引题要讲数据结构、匹配规则、回表成本、选择性和慢 SQL 验证，最后落到 explain。
</td>
</tr>
<tr>
<td>
MongoDB 监控与可观测性
</td>
<td>
时序数据监控，告警体系搭建
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
</table>

---

#### 20、Atlas Vector Search 与 pgvector 对比

**难度级别**：⭐⭐~⭐⭐⭐⭐（HNSW、ANN 近似最近邻、精度/性能/生态对比）

##### 基础题：MongoDB Atlas 支持向量检索吗？用什么索引？

MongoDB Atlas 支持**向量检索**，使用 **HNSW（Hierarchical Navigable Small World）** 索引。

- 支持向量相似度搜索（欧氏距离、余弦相似度、点积）

- 与 MongoDB 文档存储集成，无需额外向量数据库

- 支持 $vectorSearch 聚合阶段进行向量检索

##### 进阶题：HNSW 索引的原理是什么？ANN 近似最近邻算法如何工作？Atlas Vector Search 与 pgvector 在精度/性能/生态上有什么差异？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- HNSW 索引原理
- ANN 近似最近邻算法
- Atlas Vector Search vs pgvector
- Agent 场景应用
- 分层图结构：多层图，上层稀疏，下层密集
- 搜索过程：从顶层开始，逐层向下搜索，快速定位到最近邻

**2️⃣ Impressive Answer**

Atlas Vector Search 和 pgvector 是**两种主流向量检索方案**，对比分析：

1. **HNSW 索引原理**

  - **分层图结构**：多层图，上层稀疏，下层密集

  - **搜索过程**：从顶层开始，逐层向下搜索，快速定位到最近邻

  - **优势**：查询速度快，索引构建快，内存占用低

1. **ANN 近似最近邻算法**

  - **定义**：近似最近邻搜索，不保证找到绝对最近邻，但速度极快

  - **精度权衡**：通过调整 `ef` 参数（搜索宽度）平衡精度和性能

  - **适用场景**：大规模向量检索（百万级以上），需要毫秒级响应

1. **Atlas Vector Search vs pgvector**

  - **精度对比**：

    - Atlas Vector Search：精度 95-98%，可调整 `ef` 参数

    - pgvector：精度 90-95%，可调整 `lists` 参数

  - **性能对比**：

    - Atlas Vector Search：查询速度 10-50ms，适合实时检索

    - pgvector：查询速度 50-200ms，适合离线检索

  - **生态对比**：

    - Atlas Vector Search：MongoDB 原生支持，无需额外组件，与文档存储集成

    - pgvector：PostgreSQL 扩展，需要单独安装，与关系型数据库集成

  - **成本对比**：

    - Atlas Vector Search：MongoDB Atlas 云服务，按使用量付费

    - pgvector：开源免费，自建成本低

1. **Agent 场景应用**

  - 知识库向量检索：使用 Atlas Vector Search，实时检索要求高

  - 用户行为分析：使用 pgvector，离线分析要求高

  - 混合方案：热数据用 Atlas，冷数据用 pgvector

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
简单描述两种方案
</td>
<td>
系统阐述 HNSW 原理→ANN 算法→多维度对比
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道 HNSW 分层结构
</td>
<td>
深入分层图、搜索过程、精度权衡
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无场景应用
</td>
<td>
结合 Agent 知识库、用户行为给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本概念
</td>
<td>
具备向量检索方案选型和优化能力
</td>
</tr>
</table>

##### 场景题：Agent 知识库向量检索方案如何在 Atlas、pgvector、Milvus 之间选型？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- Atlas Vector Search
- pgvector
- Milvus
- 选型建议
- 适用场景：实时检索、与文档存储集成、中小规模（百万级）
- MongoDB 原生支持，无需额外组件

**2️⃣ Impressive Answer**

Agent 知识库向量检索方案的**选型决策**：

1. **Atlas Vector Search**

  - **适用场景**：实时检索、与文档存储集成、中小规模（百万级）

  - **优势**：

    - MongoDB 原生支持，无需额外组件

    - 与文档存储集成，方便管理

    - 查询速度快（10-50ms）

  - **劣势**：

    - 仅支持 MongoDB Atlas 云服务

    - 成本较高（按使用量付费）

  - **Agent 场景**：适合实时知识库检索，与 Agent 会话数据集成

1. **pgvector**

  - **适用场景**：离线分析、与关系型数据库集成、中小规模（百万级）

  - **优势**：

    - PostgreSQL 扩展，开源免费

    - 与关系型数据库集成，方便管理

    - 支持复杂查询（SQL）

  - **劣势**：

    - 查询速度慢（50-200ms）

    - 需要单独安装和配置

  - **Agent 场景**：适合离线知识库分析，与用户行为数据集成

1. **Milvus**

  - **适用场景**：大规模检索（千万级以上）、高性能要求、独立向量数据库

  - **优势**：

    - 查询速度快（1-10ms）

    - 支持大规模向量（十亿级）

    - 开源免费

  - **劣势**：

    - 需要单独部署和管理

    - 与文档存储分离，需要额外同步

  - **Agent 场景**：适合大规模知识库检索，独立向量数据库

1. **选型建议**

  - **实时检索 + 文档集成**：选择 Atlas Vector Search

  - **离线分析 + 关系型数据库**：选择 pgvector

  - **大规模检索 + 高性能**：选择 Milvus

  - **混合方案**：热数据用 Atlas，冷数据用 Milvus

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
简单说&quot;用 Atlas&quot;
</td>
<td>
系统阐述三种方案及选型建议
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道各方案优劣
</td>
<td>
深入性能、成本、场景对比
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体选型建议
</td>
<td>
给出完整的选型决策和混合方案
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本方案
</td>
<td>
具备向量检索方案选型能力
</td>
</tr>
</table>

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
ES 与 MongoDB 在搜索场景的技术选型
</td>
<td>
搜索方案选型，与向量检索配合
</td>
<td>
答：MongoDB 适合业务数据存储和按文档模型查询，Elasticsearch 适合全文检索、复杂搜索和相关性排序。常见架构是 MongoDB 做主存储，ES 做搜索索引，通过 Change Stream/CDC 同步。
</td>
</tr>
<tr>
<td>
MongoDB 聚合管道（group/$lookup）
</td>
<td>
数据分析核心能力，与向量检索配合
</td>
<td>
答：MongoDB 聚合管道是把数据按 stage 流式处理，常见有 $match、$group、$lookup、$project。优化时把 $match 前置、让过滤字段命中索引，避免大集合上无限制 $lookup。
</td>
</tr>
<tr>
<td>
MongoDB 索引设计与优化
</td>
<td>
查询性能基础，与向量检索配合
</td>
<td>
答：数据库索引题要讲数据结构、匹配规则、回表成本、选择性和慢 SQL 验证，最后落到 explain。
</td>
</tr>
<tr>
<td>
MongoDB 文档设计模式：嵌套 vs 引用
</td>
<td>
文档设计基础，与知识库存储配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
</table>

---

#### 21、多租户数据隔离方案

**难度级别**：⭐⭐~⭐⭐⭐⭐（独立数据库、共享集合+tenantId、分片键隔离）

##### 基础题：多租户数据隔离有哪几种方式？

**多租户数据隔离**三种方式：

1. **独立数据库**：每个租户一个数据库，隔离性最好

1. **共享集合+tenantId**：所有租户共享集合，通过 tenantId 字段隔离

1. **分片键隔离**：使用 tenantId 作为分片键，数据分散到不同分片

##### 进阶题：独立数据库 vs 共享集合+tenantId vs 分片键隔离，各自的安全性、成本、查询性能如何对比？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 安全性对比
- 成本对比
- 查询性能对比
- Agent 场景应用
- 独立数据库
- 隔离性：最高，租户之间完全隔离

**2️⃣ Impressive Answer**

多租户数据隔离方案是**SaaS 架构的核心决策**，多维度对比：

1. **安全性对比**

  - **独立数据库**：

    - 隔离性：最高，租户之间完全隔离

    - 数据泄露风险：最低，租户无法访问其他租户数据

  - **共享集合+tenantId**：

    - 隔离性：中等，通过 tenantId 字段隔离

    - 数据泄露风险：中等，需要应用层保证查询带 tenantId

  - **分片键隔离**：

    - 隔离性：中等，租户数据分散到不同分片

    - 数据泄露风险：中等，需要应用层保证查询带 tenantId

1. **成本对比**

  - **独立数据库**：

    - 存储成本：高，每个租户独立数据库，存储空间浪费

    - 运维成本：高，需要管理大量数据库

  - **共享集合+tenantId**：

    - 存储成本：低，所有租户共享集合，存储空间利用率高

    - 运维成本：低，只需要管理少量集合

  - **分片键隔离**：

    - 存储成本：中等，租户数据分散，存储空间利用率中等

    - 运维成本：中等，需要管理分片集群

1. **查询性能对比**

  - **独立数据库**：

    - 查询性能：高，每个租户独立数据库，索引小，查询快

    - 扩展性：差，每个租户独立数据库，无法水平扩展

  - **共享集合+tenantId**：

    - 查询性能：低，所有租户共享集合，索引大，查询慢

    - 扩展性：好，可以水平扩展

  - **分片键隔离**：

    - 查询性能：中等，租户数据分散，索引中等，查询速度中等

    - 扩展性：好，可以水平扩展

1. **Agent 场景应用**

  - 大客户（独立数据库）：安全要求高，查询性能要求高

  - 中小客户（共享集合+tenantId）：成本敏感，查询性能要求低

  - 混合方案：大客户独立数据库，中小客户共享集合

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
简单描述三种方案
</td>
<td>
系统阐述安全性→成本→查询性能多维度对比
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道查询性能差异
</td>
<td>
深入索引大小、扩展性、查询速度对比
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体应用场景
</td>
<td>
结合 Agent 大客户、中小客户给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本方案
</td>
<td>
具备多租户架构设计能力
</td>
</tr>
</table>

##### 场景题：SaaS 型 Agent 平台的多租户 MongoDB 架构如何设计？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 架构设计
- 索引设计
- 查询优化
- 数据迁移
- 监控告警
- Agent 场景最佳实践

**2️⃣ Impressive Answer**

SaaS 型 Agent 平台多租户 MongoDB 架构的**设计方案**：

1. **架构设计**

  - **租户分类**：

    - 大客户（VIP）：独立数据库，安全要求高

    - 中小客户（SMB）：共享集合+tenantId，成本敏感

  - **数据库设计**：

    - 大客户：每个租户一个数据库，如 `tenant_001_db`、`tenant_002_db`

    - 中小客户：共享数据库，如 `smb_db`，集合中包含 `tenantId` 字段

1. **索引设计**

  - **大客户**：

    - 每个租户独立索引，索引小，查询快

    - 索引示例：`{userId: 1, createdAt: -1}`

  - **中小客户**：

    - 共享索引，索引大，查询慢

    - 索引示例：`{tenantId: 1, userId: 1, createdAt: -1}`

1. **查询优化**

  - **大客户**：

    - 查询时指定数据库，如 `db.tenant_001_db.sessions.find({...})`

    - 查询性能高，延迟 1-5ms

  - **中小客户**：

    - 查询时必须带 `tenantId`，如 `db.smb_db.sessions.find({tenantId: "tenant123", ...})`

    - 查询性能中等，延迟 5-20ms

1. **数据迁移**

  - **中小客户升级为大客户**：

    - 导出中小客户数据 → 创建独立数据库 → 导入数据 → 删除原数据

  - **大客户降级为中小客户**：

    - 导出大客户数据 → 删除独立数据库 → 导入共享数据库

1. **监控告警**

  - **大客户**：监控每个租户的数据库性能，独立告警

  - **中小客户**：监控共享数据库性能，统一告警

1. **Agent 场景最佳实践**

  - 大客户：独立数据库，查询性能高，安全要求高

  - 中小客户：共享集合+tenantId，成本低，查询性能中等

  - 混合方案：根据租户规模动态调整

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
简单说&quot;共享集合&quot;
</td>
<td>
系统阐述架构设计→索引设计→查询优化→数据迁移
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道索引设计和数据迁移
</td>
<td>
深入独立索引、共享索引、迁移流程
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体设计方案
</td>
<td>
给出完整的架构设计和最佳实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本方案
</td>
<td>
具备多租户架构设计和优化能力
</td>
</tr>
</table>

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
MongoDB 分片集群架构
</td>
<td>
水平扩展方案，与分片键隔离配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
<tr>
<td>
MongoDB 索引设计与优化
</td>
<td>
查询性能基础，与多租户隔离配合
</td>
<td>
答：数据库索引题要讲数据结构、匹配规则、回表成本、选择性和慢 SQL 验证，最后落到 explain。
</td>
</tr>
<tr>
<td>
MongoDB 监控与可观测性
</td>
<td>
租户性能监控，告警体系搭建
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
MongoDB 写关注（WriteConcern）与读关注（ReadConcern）
</td>
<td>
一致性级别配置，与多租户隔离配合
</td>
<td>
答：MongoDB 题要抓文档模型、副本集高可用、分片扩展、索引和写关注；设计时重点权衡嵌入/引用、一致性和查询模式。
</td>
</tr>
</table>

---

#### 22、MongoDB 监控与可观测性

**难度级别**：⭐⭐~⭐⭐⭐⭐（mongostat、mongotop、opcounters、connections、wiredTiger cache、慢查询 Profiler）

##### 基础题：如何监控 MongoDB 的健康状态？有哪些常用工具？

**MongoDB 监控工具**：

1. **mongostat**：实时监控 MongoDB 状态（QPS、连接数、内存使用等）

1. **mongotop**：监控集合读写时间，定位热点集合

1. **db.serverStatus()**：查看服务器状态（内存、连接、锁等）

1. **db.currentOp()**：查看当前运行的操作

1. **MongoDB Atlas**：云服务自带监控仪表板

##### 进阶题：mongostat/mongotop 的核心指标是什么？opcounters、connections、wiredTiger cache 分别代表什么？慢查询 Profiler 如何配置？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- mongostat 核心指标
- mongotop 核心指标
- db.serverStatus() 核心指标
- 慢查询 Profiler 配置
- Agent 场景监控
- insert/query/update/delete：每秒操作数（QPS）

**2️⃣ Impressive Answer**

MongoDB 监控的**核心指标**和配置方法：

1. **mongostat 核心指标**

  - **insert/query/update/delete**：每秒操作数（QPS）

  - **command**：每秒命令数

  - **vsize**：虚拟内存使用量

  - **res**：物理内存使用量

  - **faults**：每秒 Page Fault 数（内存不足时增加）

  - **qr|qw**：读写队列长度（队列过长表示性能瓶颈）

  - **ar|aw**：活跃读写连接数

  - **netIn/netOut**：网络流入/流出量

1. **mongotop 核心指标**

  - **total**：集合总读写时间

  - **read**：集合读时间

  - **write**：集合写时间

  - **作用**：定位热点集合，优化索引

1. **db.serverStatus() 核心指标**

  - **opcounters**：操作计数器（insert/query/update/delete 总数）

  - **connections**：连接数（current/available）

  - **wiredTiger.cache**：缓存指标

    - `pages read into cache`：读入页数（内存不足时增加）

    - `pages evicted`：驱逐页数（内存不足时增加）

    - `percentage dirty`：脏页比例（过高时 Checkpoint 频繁）

1. **慢查询 Profiler 配置**

  - **级别设置**：

    - 0：关闭

    - 1：记录慢查询（默认超过 100ms）

    - 2：记录所有查询（仅用于调试）

  - **配置方式**：
      `\``javascriptdb.setProfilingLevel(1, {slowms: 100})
      `\``

  - **查看慢查询**：
      `\``javascriptdb.system.profile.find().sort({ts: -1}).limit(10)
      `\``

1. **Agent 场景监控**

  - 会话 QPS 监控：`mongostat` 监控 insert/query QPS

  - 热点集合监控：`mongotop` 定位热点集合，优化索引

  - 内存监控：`db.serverStatus()` 监控 wiredTiger cache，避免内存不足

  - 慢查询监控：`Profiler` 记录慢查询，优化查询

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
简单描述监控工具
</td>
<td>
系统阐述 mongostat→mongotop→serverStatus→Profiler
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道核心指标含义
</td>
<td>
深入 QPS、Page Fault、脏页比例、慢查询配置
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体监控方案
</td>
<td>
结合 Agent 会话、热点集合、内存、慢查询给出实践
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本监控工具
</td>
<td>
具备监控指标分析和优化能力
</td>
</tr>
</table>

##### 场景题：Agent 平台的 MongoDB 监控告警体系如何搭建？

**1️⃣ Common Answer**

重点总结（便于面试记忆）：

- 监控架构
- 监控指标
- 告警规则
- Grafana 仪表板
- Agent 场景最佳实践
- 数据采集：MongoDB Exporter 采集指标

**2️⃣ Impressive Answer**

Agent 平台 MongoDB 监控告警体系的**搭建方案**：

1. **监控架构**

  - **数据采集**：MongoDB Exporter 采集指标

  - **数据存储**：Prometheus 存储时序数据

  - **数据展示**：Grafana 可视化展示

  - **告警通知**：Alertmanager 发送告警

1. **监控指标**

  - **基础指标**：

    - QPS：`mongod_op_counters_total`（insert/query/update/delete）

    - 连接数：`mongod_connections_current` / `mongod_connections_available`

    - 内存：`mongod_wiredtiger_cache_bytes`（缓存大小）

  - **性能指标**：

    - 延迟：`mongod_latency_histogram`（操作延迟）

    - Page Fault：`mongod_wiredtiger_cache_pages_evicted_total`（驱逐页数）

    - 队列长度：`mongod_global_lock_current_queue`（锁队列长度）

  - **业务指标**：

    - 会话 QPS：按 agentId 分组统计

    - 慢查询数：按集合分组统计

1. **告警规则**

  - **QPS 告警**：QPS 超过阈值时告警
      `\``yaml

    - alert: HighQPSexpr: rate(mongod*op*counters_total[5m]) > 1000for: 5mlabels:severity: warningannotations:summary: "MongoDB QPS 过高"

`\``

  - **连接数告警**：连接数超过阈值时告警
      `\``yaml

    - alert: HighConnectionsexpr: mongod*connections*current / mongod*connections*available > 0.8for: 5mlabels:severity: warningannotations:summary: "MongoDB 连接数过高"

`\``

  - **内存告警**：内存使用率超过阈值时告警
      `\``yaml

    - alert: HighMemoryexpr: mongod*wiredtiger*cache*bytes / node*memory*MemTotal*bytes > 0.8for: 5mlabels:severity: warningannotations:summary: "MongoDB 内存使用率过高"

`\``

  - **慢查询告警**：慢查询数超过阈值时告警
      `\``yaml

    - alert: HighSlowQueryexpr: rate(mongod*slow*queries_total[5m]) > 10for: 5mlabels:severity: warningannotations:summary: "MongoDB 慢查询过多"

`\``

1. **Grafana 仪表板**

  - **基础仪表板**：QPS、连接数、内存、延迟

  - **业务仪表板**：会话 QPS、慢查询数、热点集合

  - **告警仪表板**：告警历史、告警趋势

1. **Agent 场景最佳实践**

  - 会话 QPS 监控：按 agentId 分组，定位热点 Agent

  - 慢查询监控：按集合分组，优化慢查询

  - 内存监控：监控 wiredTiger cache，避免内存不足

  - 告警通知：钉钉、邮件、短信多渠道通知

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
简单说&quot;Prometheus + Grafana&quot;
</td>
<td>
系统阐述监控架构→监控指标→告警规则→仪表板
</td>
</tr>
<tr>
<td>
技术深度
</td>
<td>
不知道告警规则配置
</td>
<td>
深入 QPS、连接数、内存、慢查询告警
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
无具体搭建方案
</td>
<td>
给出完整的监控架构和告警规则配置
</td>
</tr>
<tr>
<td>
面试官印象
</td>
<td>
了解基本监控工具
</td>
<td>
具备监控告警体系搭建能力
</td>
</tr>
</table>

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
MongoDB 索引设计与优化
</td>
<td>
查询性能基础，与慢查询监控配合
</td>
<td>
答：数据库索引题要讲数据结构、匹配规则、回表成本、选择性和慢 SQL 验证，最后落到 explain。
</td>
</tr>
<tr>
<td>
MongoDB 写关注（WriteConcern）与读关注（ReadConcern）
</td>
<td>
一致性级别配置，与延迟监控配合
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
MongoDB 锁机制：从全局锁到文档级锁的演进
</td>
<td>
并发控制基础，与锁队列监控配合
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
MongoDB 存储引擎与底层原理
</td>
<td>
WiredTiger 存储引擎基础，与缓存监控配合
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
<tr>
<td>
MongoDB 连接池与驱动配置优化
</td>
<td>
连接池配置，与连接数监控配合
</td>
<td>
答：可观测性要覆盖输入、Prompt、模型输出、工具调用、耗时、Token、错误和最终结果；用 Trace 串起一次 Agent 执行链路。
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| MongoDB 的文档模型和关系型数据库有什么区别？适合什么场景？ | MongoDB 用 BSON 文档存储聚合数据，适合结构灵活、字段变化快、读写围绕单个业务对象展开的场景；关系型数据库用表和 Join 表达关系，适合强约束、多表事务、复杂查询和高度规范化的数据模型。 |
| MongoDB 的聚合管道（Aggregation Pipeline）怎么用？有哪些常用阶段？ | $match：过滤文档，类似 WHERE，应尽早使用减少后续处理量；avg/$push 等累加器；$lookup：左外连接，关联其他集合（类似 LEFT JOIN）；$project：投影字段，控制输出结构，可计算衍生字段；$unwind：拆解数组字段，一对多展开。 |
| MongoDB 的 CRUD 操作有哪些？updateOne 和 findAndModify 有什么区别？ | $set：设置字段值（不存在则创建）；$inc：数值自增/自减（原子操作，适合计数器）；$push/$pull：数组追加/删除元素；$addToSet：数组去重追加；updateOne：只执行更新，返回更新结果（匹配数、修改数），不返回文档内容。 |
| MongoDB 的事务支持（4.0+）是怎样的？和 MySQL 事务有什么区别？ | 0：支持副本集内的多文档事务（单分片）；2：支持分片集群的分布式事务（跨分片）；底层机制：基于 WiredTiger 的 MVCC（多版本并发控制），通过快照隔离实现事务；优先使用单文档原子操作：MongoDB 的文档嵌套设计使得大多数操作无需跨文档事务；必要时才用多文档事务：如转账（扣款 + 入账跨集合），性能代价约 3-5 倍。 |
| MongoDB 的副本集（Replica Set）机制是怎样的？如何实现高可用？ | Primary：唯一接受写入的主节点，处理所有写操作，将变更写入 Oplog；Secondary：从主节点异步复制 Oplog，保持数据同步，可配置为只读节点；Arbiter：仲裁节点，不存储数据，只参与选举投票，用于凑足奇数节点避免平票；Oplog 是一个固定大小的 Capped Collection，记录所有写操作（幂等格式）；Secondary 持续拉取 Primary 的 Oplog 并重放，实现异步复制。 |
| MongoDB 的索引类型有哪些？如何设计高效索引？ | 单字段索引：最基础的索引，支持升序/降序，默认 _id 字段自动创建；复合索引：多个字段组合，遵循最左前缀原则，查询时必须包含索引的前缀字段才能命中；多键索引：针对数组字段，为数组中每个元素创建索引项；地理空间索引：2dsphere（球面）、2d（平面），支持地理位置查询和范围查询；文本索引：支持全文搜索，支持多语言，注意每个集合只能有一个文本索引。 |
| MongoDB 的分片集群是如何工作的？如何选择分片键？ | Shard Server：存储数据的分片节点，每个分片是一个副本集（高可用）；Config Server：存储集群元数据（分片信息、配置），必须是副本集；Mongos：查询路由器，接收应用请求，根据分片键路由到对应分片；范围分片（Range Sharding）：按分片键值范围分配，适合范围查询，但可能导致数据倾斜；哈希分片（Hash Sharding）：对分片键哈希后分配，数据均匀分布，不适合范围查询。 |
| MongoDB 和 Elasticsearch 在搜索场景如何选型？各自适合什么场景？ | 选 MongoDB：主数据存储（会话、用户、文档元数据）、需要事务、写多读少、数据结构复杂嵌套；选 ES：全文搜索、日志分析、实时聚合看板、混合检索（BM25 + 向量）；两者结合：MongoDB 作为主存储（Source of Truth），ES 作为搜索索引（Search Layer），Canal 同步；知识库架构：MongoDB 存储文档原文、元数据、权限；ES 存储分块文本 + 向量，负责检索；会话管理：MongoDB 存储会话历史（需要事务保证原子性）；ES 不适合（无事务、NRT 延迟）。 |
| MongoDB 的 Change Stream 是什么？在 Agent 场景如何应用？ | 底层依赖 Oplog：Change Stream 本质是对 Oplog 的高级封装，将底层的 Oplog 事件转换为结构化的变更事件；事件类型：insert、update、replace、delete、invalidate（集合删除/重命名）；监听粒度：可监听单个集合、整个数据库、整个集群（需副本集或分片集群）；断点续传：每个事件包含 _id（Resume Token），应用重启后可从上次位置继续消费；Pipeline 过滤：支持聚合管道过滤，只监听特定条件的变更（如特定租户的文档）。 |
| MongoDB 的性能如何优化？如何分析慢查询？ | Profiler：db.setProfilingLevel(1, {slowms: 100}) 记录超过 100ms 的慢查询，结果存入 system.profile 集合；explain() 分析：db.collection.find({}).explain('executionStats')，关键指标：；COLLSCAN：全集合扫描（最差，需加索引）；IXSCAN：索引扫描（理想）；totalDocsExamined：扫描文档数，越接近 nReturned 越好。 |
| WiredTiger 存储引擎原理 | 索引和数据都存储在 B-Tree 中，每个节点 8KB；B-Tree 节点在内存中是 Page，磁盘上是 Block；内部节点存储键值和子节点指针，叶子节点存储完整文档；快照隔离：每个事务开始时获取快照，读取历史版本数据；写时复制：修改文档时创建新版本，旧版本保留在内存中。 |
| MongoDB 默认存储引擎是什么？有什么特点？ | MongoDB 3.2+ 默认存储引擎是 WiredTiger，替代了 MMAPv1。主要特点：；文档级锁：支持并发读写，比 MMAPv1 的全局锁性能大幅提升；压缩算法：默认使用 Snappy 压缩，数据压缩率约 50%，节省磁盘空间。 |
| WiredTiger 的 B-Tree 存储结构、MVCC 实现、Checkpoint 机制、压缩算法分别是怎样的？ | 索引和数据都存储在 B-Tree 中，每个节点 8KB；B-Tree 节点在内存中是 Page，磁盘上是 Block；内部节点存储键值和子节点指针，叶子节点存储完整文档；快照隔离：每个事务开始时获取快照，读取历史版本数据；写时复制：修改文档时创建新版本，旧版本保留在内存中。 |
| 为什么 MongoDB 写入性能好？内存配置如何影响性能？ | 文档级锁：WiredTiger 支持文档级并发写入，锁粒度细；Journal 异步刷盘：默认 journalCommitIntervalMs=100，批量刷盘减少 I/O；内存缓冲：写入先到内存，Checkpoint 定期刷盘，减少磁盘随机写；压缩算法：减少磁盘 I/O 量，提升吞吐量；WiredTiger 缓存：默认占用 50% 内存，建议 cacheSizeGB 设置为物理内存的 40-60%。 |
| Oplog 机制深挖 | 操作类型幂等：insert、update、delete 都包含完整操作信息；重放安全：从节点重放 Oplog 时，重复执行不会产生副作用；$inc 操作符：使用 $inc: {count: 1} 而非 count++，保证重放一致性；Upsert 操作：update 带 upsert: true，避免重复插入；默认大小：Windows 1GB，Linux/macOS 5% 可用磁盘空间（最小 1GB）。 |
| Oplog 是什么？存在哪里？有什么特点？ | 记录所有写操作（增删改）；固定大小，循环覆盖旧数据；从节点拉取 Oplog 并重放。 |
| Oplog 的幂等性设计是怎样的？固定集合大小如何影响复制？Oplog 窗口与复制延迟有什么关系？ | 操作类型幂等：insert、update、delete 都包含完整操作信息；重放安全：从节点重放 Oplog 时，重复执行不会产生副作用；$inc 操作符：使用 $inc: {count: 1} 而非 count++，保证重放一致性；Upsert 操作：update 带 upsert: true，避免重复插入；默认大小：Windows 1GB，Linux/macOS 5% 可用磁盘空间（最小 1GB）。 |
| Oplog 窗口过小导致从节点脱离同步时如何排查和处理？ | 查看复制延迟：rs.printSlaveReplicationInfo()，检查从节点落后时间；查看 Oplog 窗口：rs.printReplicationInfo()，检查 Oplog 大小和窗口时间；检查从节点状态：rs.status()，查看从节点 stateStr 是否为 RECOVERING；查看日志：mongod.log 搜索 "replSet" 关键字，确认脱离同步原因；从节点清空数据 → 从主节点拉取完整数据 → 重放 Oplog。 |
| 文档设计模式：嵌套 vs 引用 | 问题：大文档嵌套太多子数据，超过 16MB 限制；方案：只嵌入常用子集，其他数据引用存储；场景：商品详情只嵌入前 10 条评论，其他评论单独存储；问题：小文档过多，查询和索引开销大；方案：按时间/类别分桶，将多个小文档合并为一个大文档。 |
| 什么时候用嵌套文档，什么时候用引用？各有什么优缺点？ | 嵌套文档：适合一对多关系、数据一起读取、子文档较少（<100 个）；缺点：文档大小限制 16MB、嵌套过深查询复杂；引用：适合多对多关系、数据独立读取、子文档较多。 |
| MongoDB 有哪些经典文档设计模式？（Subset、Bucket、Computed、Outlier、Extended Reference、Schema Versioning）各自解决什么问题？ | 问题：大文档嵌套太多子数据，超过 16MB 限制；方案：只嵌入常用子集，其他数据引用存储；场景：商品详情只嵌入前 10 条评论，其他评论单独存储；问题：小文档过多，查询和索引开销大；方案：按时间/类别分桶，将多个小文档合并为一个大文档。 |
| Agent 会话消息如何用 Bucket Pattern 分桶存储？设计方案是什么？ | 按日期分桶：每个会话每天一个 Bucket，避免单文档过大；消息数量限制：单个 Bucket 消息数不超过 1000 条，超过则分多个 Bucket；：{userId: 1, sessionId: 1, bucketDate: -1} 复合索引；时间范围查询：直接按 bucketDate 查询，避免扫描多个 Bucket；分页查询：先查 Bucket 列表，再查具体消息。 |
| 连接池与驱动配置优化 | maxPoolSize：（默认 100）：最大连接数，超过则等待；minPoolSize：（默认 0）：最小连接数，保持连接池中有这么多连接；waitQueueTimeoutMS：（默认 0）：等待连接超时时间（毫秒），0 表示无限等待；serverSelectionTimeoutMS：（默认 30000）：选择服务器超时时间（毫秒）；maxIdleTimeMS：（默认 0）：连接最大空闲时间（毫秒），超过则关闭。 |
| maxPoolSize/minPoolSize/waitQueueTimeoutMS/serverSelectionTimeoutMS 各参数的含义是什么？连接泄漏如何排查？ | maxPoolSize：（默认 100）：最大连接数，超过则等待；minPoolSize：（默认 0）：最小连接数，保持连接池中有这么多连接；waitQueueTimeoutMS：（默认 0）：等待连接超时时间（毫秒），0 表示无限等待；serverSelectionTimeoutMS：（默认 30000）：选择服务器超时时间（毫秒）；maxIdleTimeMS：（默认 0）：连接最大空闲时间（毫秒），超过则关闭。 |
| Spring Boot 集成 MongoDB 的连接池最佳配置是什么？ | max-connections-per-host：每个主机最大连接数，根据应用并发量设置；min-connections-per-host：每个主机最小连接数，避免冷启动；max-connection-idle-time：连接最大空闲时间，关闭空闲连接；max-connection-life-time：连接最大生命周期，定期重建连接；connection-timeout：连接超时时间，避免长时间等待。 |
| Atlas Vector Search 与 pgvector 对比 | 分层图结构：多层图，上层稀疏，下层密集；搜索过程：从顶层开始，逐层向下搜索，快速定位到最近邻；优势：查询速度快，索引构建快，内存占用低；定义：近似最近邻搜索，不保证找到绝对最近邻，但速度极快；精度权衡：通过调整 ef 参数（搜索宽度）平衡精度和性能。 |
| MongoDB Atlas 支持向量检索吗？用什么索引？ | 支持向量相似度搜索（欧氏距离、余弦相似度、点积）；与 MongoDB 文档存储集成，无需额外向量数据库；支持 $vectorSearch 聚合阶段进行向量检索。 |
| HNSW 索引的原理是什么？ANN 近似最近邻算法如何工作？Atlas Vector Search 与 pgvector 在精度/性能/生态上有什么差异？ | 分层图结构：多层图，上层稀疏，下层密集；搜索过程：从顶层开始，逐层向下搜索，快速定位到最近邻；优势：查询速度快，索引构建快，内存占用低；定义：近似最近邻搜索，不保证找到绝对最近邻，但速度极快；精度权衡：通过调整 ef 参数（搜索宽度）平衡精度和性能。 |
| Agent 知识库向量检索方案如何在 Atlas、pgvector、Milvus 之间选型？ |：实时检索、与文档存储集成、中小规模（百万级）；MongoDB 原生支持，无需额外组件；与文档存储集成，方便管理；查询速度快（10-50ms）；仅支持 MongoDB Atlas 云服务。 |
| 多租户数据隔离方案 | 隔离性：最高，租户之间完全隔离；数据泄露风险：最低，租户无法访问其他租户数据；隔离性：中等，通过 tenantId 字段隔离；数据泄露风险：中等，需要应用层保证查询带 tenantId；隔离性：中等，租户数据分散到不同分片。 |
| 多租户数据隔离有哪几种方式？ | 独立数据库：每个租户一个数据库，隔离性最好；共享集合+tenantId：所有租户共享集合，通过 tenantId 字段隔离；分片键隔离：使用 tenantId 作为分片键，数据分散到不同分片。 |
| 独立数据库 vs 共享集合+tenantId vs 分片键隔离，各自的安全性、成本、查询性能如何对比？ | 隔离性：最高，租户之间完全隔离；数据泄露风险：最低，租户无法访问其他租户数据；隔离性：中等，通过 tenantId 字段隔离；数据泄露风险：中等，需要应用层保证查询带 tenantId；隔离性：中等，租户数据分散到不同分片。 |
| SaaS 型 Agent 平台的多租户 MongoDB 架构如何设计？ | 大客户（VIP）：独立数据库，安全要求高；中小客户（SMB）：共享集合+tenantId，成本敏感；大客户：每个租户一个数据库，如 tenant_001_db、tenant_002_db；中小客户：共享数据库，如 smb_db，集合中包含 tenantId 字段；每个租户独立索引，索引小，查询快。 |
| MongoDB 监控与可观测性 | insert/query/update/delete：每秒操作数（QPS）；command：每秒命令数；vsize：虚拟内存使用量；faults：每秒 Page Fault 数（内存不足时增加）；qr\|qw：读写队列长度（队列过长表示性能瓶颈）。 |
| 如何监控 MongoDB 的健康状态？有哪些常用工具？ | mongostat：实时监控 MongoDB 状态（QPS、连接数、内存使用等）；mongotop：监控集合读写时间，定位热点集合；db.serverStatus()：查看服务器状态（内存、连接、锁等）。 |
| mongostat/mongotop 的核心指标是什么？opcounters、connections、wiredTiger cache 分别代表什么？慢查询 Profiler 如何配置？ | insert/query/update/delete：每秒操作数（QPS）；command：每秒命令数；vsize：虚拟内存使用量；faults：每秒 Page Fault 数（内存不足时增加）；qr\|qw：读写队列长度（队列过长表示性能瓶颈）。 |
| Agent 平台的 MongoDB 监控告警体系如何搭建？ | 数据采集：MongoDB Exporter 采集指标；数据存储：Prometheus 存储时序数据；数据展示：Grafana 可视化展示；告警通知：Alertmanager 发送告警；QPS：mongod_op_counters_total（insert/query/update/delete）。 |
