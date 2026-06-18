## 16. Harness：AI 交付工程体系

### 16.1 为什么 RAG 系统需要 Harness

传统后端上线关注：
- ✅ 单元测试通过
- ✅ 接口可用
- ✅ 镜像构建成功

RAG 系统上线还必须关注：
- ❓ RAG 检索是否命中（hit@k）
- ❓ Prompt 是否退化（citation rate）
- ❓ 答案是否有引用（groundedness）
- ❓ Verifier 是否误放幻觉答案（false_pass_rate）
- ❓ Tool Calling 是否稳定（tool_success_rate）
- ❓ fallback_rate 是否升高
- ❓ thumbs_down_rate 是否升高
- ❓ human_fallback_rate 是否异常

因此本项目引入了 **Harness-based AI Delivery Pipeline**，把 AI 评估指标作为发布门禁。

### 16.2 目录结构

```
harness/
├── README.md                     # Harness 总览
├── pipeline/
│   ├── ci.yaml                   # CI: install → test → lint → build
│   ├── cd.yaml                   # CD: dev → smoke → gate → staging → canary → prod
│   ├── eval_gate.yaml            # System Eval Gate (3 维度质量门)
│   ├── prompt_eval_gate.yaml     # Prompt Eval Gate (变更专项验证)
│   ├── security_gate.yaml        # Security Gate (密钥/依赖/注入/泄漏检测)
│   └── rollback.yaml             # 7 维度独立回滚
├── feature_flags/
│   ├── flags.md                  # 20+ Feature Flag 定义
│   └── flag_strategy.md          # Flag 生命周期管理策略
├── quality_gates/
│   ├── metric_thresholds.md      # 每个指标的含义/阈值/处理方案
│   └── quality_gate_policy.md    # 阻断策略 + Override 规则
├── environments/
│   ├── dev.md                    # Mock LLM + 快速迭代
│   ├── staging.md                # 真实 Docker + Eval Gate + Canary
│   └── production.md             # Stable only + 审批 + 监控
├── release/
│   ├── release_checklist.md      # 上线前 Checklist
│   ├── canary_strategy.md        # 灰度策略: 5%→20%→50%→100%
│   └── production_readiness_review.md
├── runbooks/
│   ├── deploy_runbook.md         # 部署操作手册
│   ├── rollback_runbook.md       # 回滚操作手册
│   ├── eval_gate_runbook.md      # Eval Gate 诊断手册
│   ├── feature_flag_runbook.md   # Feature Flag 操作手册
│   └── incident_runbook.md       # 故障应急手册
└── templates/
    ├── incident_report_template.md
    ├── rollback_plan_template.md
    ├── environment_variables.md
    └── pipeline_variables.md
```

### 16.3 CI Pipeline

```
install → backend_test → frontend_build → lint → docker_build
   │           │               │            │          │
   └───────────┴───────────────┴────────────┴──────────┘
                        任意失败 → 阻断
```

### 16.4 CD Pipeline

```
dev → smoke_test → eval_gate → staging → canary → production
                      │                      │
                 3 维度质量门          5%→20%→50%→100%
                 (RAG/Answer/System)    自动指标监控
                      │                      │
                 任一不达标 → 阻断     异常 → 自动回滚
```

### 16.5 Eval Gate（3 维度质量门）

| 维度 | 指标 | 阈值 | 阻断策略 |
|------|------|------|----------|
| **RAG** | hit@5 | ≥ 0.80 | 硬阻断 |
| **RAG** | recall@5 | ≥ 0.85 | 硬阻断 |
| **RAG** | MRR | ≥ 0.70 | 软阻断 |
| **Answer** | citation_rate | ≥ 0.75 | 硬阻断 |
| **Answer** | groundedness | ≥ 0.80 | 硬阻断 |
| **Answer** | relevance | ≥ 0.75 | 硬阻断 |
| **System** | intent_accuracy | ≥ 0.85 | 硬阻断 |
| **System** | tool_success_rate | ≥ 0.90 | 软阻断 |
| **System** | fallback_rate | ≤ 0.15 | 硬阻断 |
| **System** | thumbs_down_rate | ≤ 0.10 | 硬阻断 |

### 16.6 Canary 灰度策略

```
Phase 1 (5%):  部署 canary 实例，观察 5 分钟
  │ 指标异常？
  ├─ 是 → 自动回滚
  └─ 否 ↓
Phase 2 (20%): 扩展流量，观察 10 分钟
  │ 指标异常？
  ├─ 是 → 自动回滚
  └─ 否 ↓
Phase 3 (50%): 半数流量，观察 15 分钟
  │ 指标异常？
  ├─ 是 → 自动回滚
  └─ 否 ↓
Phase 4 (100%): 全量，继续监控 30 分钟
```

**监控指标：**
- 错误率 > baseline × 2 → 回滚
- P95 延迟 > baseline × 3 → 回滚
- fallback_rate > 0.25 → 回滚
- thumbs_down_rate > 0.15 → 回滚

### 16.7 7 维度独立回滚

| 维度 | 回滚内容 | 预计时间 |
|------|----------|----------|
| **Code** | Git revert → 重新部署 | 3-5 分钟 |
| **Prompt** | 还原 prompt_builder.py 到上一版本 | 1-2 分钟 |
| **Workflow** | 还原 workflow.py 图结构 | 1-2 分钟 |
| **Retriever** | 切换检索策略 (Milvus→Memory/BGE→Random) | 1-2 分钟 |
| **LLM** | 切换 LLM Provider (openai→mock) | 即时（环境变量） |
| **Tool** | 禁用/替换特定工具 | 即时（Feature Flag） |
| **Verifier** | 降低校验严格度 / 切换到纯规则模式 | 即时（Feature Flag） |

### 16.8 Feature Flags（20+ 开关）

| Flag | 默认值 | 说明 | 切换方式 |
|------|--------|------|----------|
| `USE_REAL_LLM` | false | 使用真实 LLM vs Mock | 环境变量 |
| `USE_MILVUS` | false | 使用 Milvus vs MemoryStore | 环境变量 |
| `USE_REDIS` | false | 使用 Redis vs 内存 | 环境变量 |
| `USE_POSTGRES` | false | 使用 PostgreSQL vs 内存 | 环境变量 |
| `ENABLE_TOOLS` | true | 启用工具调用 | 环境变量 |
| `ENABLE_VERIFICATION` | true | 启用答案校验 | 环境变量 |
| `ENABLE_CANARY` | false | 启用灰度发布 | 环境变量 |
| `STRICT_VERIFICATION` | false | 严格校验模式 | 环境变量 |
| `ENABLE_RERANKING` | false | 启用重排序 | 环境变量 |
| `ENABLE_HYBRID_RETRIEVAL` | false | 启用混合检索 | 环境变量 |

---

## 17. 基础设施与部署

### 17.1 Docker Compose 服务拓扑

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Docker Compose (9 服务)                           │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │PostgreSQL│  │  Redis   │  │  Milvus  │  │  MinIO   │            │
│  │   16     │  │    7     │  │  v2.4.0  │  │  latest  │            │
│  │  :5432   │  │  :6379   │  │  :19530  │  │  :9000   │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │             │             │             │                   │
│  ┌────┴─────┐  ┌────┴─────────────┴──────────────────┐             │
│  │ Neo4j 5  │  │        Elasticsearch 8.17           │             │
│  │  :7474   │  │        + IK Analyzer                │             │
│  │  :7687   │  │        :9200                        │             │
│  └────┬─────┘  └────┬────────────────────────────────┘             │
│       │             │                                              │
│  ┌────┴─────────────┴─────────────┐                                │
│  │    OpenTelemetry Collector     │                                │
│  │    :4317 (gRPC) :4318 (HTTP)  │                                │
│  └───────────────┬───────────────┘                                │
│                  │                                                 │
│     ┌────────────┴────────────┐                                    │
│     ▼                         ▼                                    │
│  ┌──────────┐           ┌──────────┐                              │
│  │Prometheus│           │ Grafana  │                              │
│  │  :9090   │──────────▶│  :3000   │                              │
│  └──────────┘           └──────────┘                              │
└──────────────────────────────────────────────────────────────────────┘

存储卷 (Docker Volumes):
┌──────────┬──────────┬───────────┬──────────┬──────────┬──────────┬──────────┬───────────┐
│ pgdata   │ redisdata│ milvusdata│ miniodata│ esdata   │ promdata │grafanadata│neo4j_data│
└──────────┴──────────┴───────────┴──────────┴──────────┴──────────┴──────────┴───────────┘
```

### 17.2 服务职责矩阵

| 服务 | 端口 | 数据持久化 | 用途 | 降级行为 |
|------|------|-----------|------|----------|
| **PostgreSQL 16** | 5432 | ✅ Volume | 用户、会话、消息、反馈、审计、评估 | → 内存 mock |
| **Redis 7** | 6379 | ✅ Volume | 会话缓存、工具状态、速率限制、Checkpoint | → 内存 dict |
| **Milvus 2.4** | 19530 | ✅ Volume | 向量存储与检索（HNSW 索引） | → MemoryVectorStore / Jaccard |
| **Elasticsearch 8** | 9200 | ✅ Volume | 全文关键词检索（BM25 + IK 分词） | → Jaccard 内存关键词匹配 |
| **Neo4j 5** | 7474/7687 | ✅ Volume | 知识图谱存储与检索 | → 自动退回 hybrid_only 模式 |
| **MinIO** | 9000/9001 | ✅ Volume | 原始文档存储 | → 本地文件系统 |
| **OTel Collector** | 4317/4318 | ❌ | Trace/Metric/Log 管线 | → JSONL 文件 |
| **Prometheus** | 9090 | ✅ Volume | 指标采集与存储 | → 内存 MetricsCollector |
| **Grafana** | 3000 | ✅ Volume | 指标可视化面板 | 不可用时无面板 |

### 17.3 数据库设计

**8 张 init 表（`scripts/init_db.py` 初始化）：**

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `users` | 用户信息 | user_id, name, role, department, permissions, preferred_language |
| `sessions` | 会话记录 | session_id, user_id, summary, created_at, updated_at |
| `messages` | 对话消息 | session_id, role, content, intent, metadata |
| `qa_logs` | QA 完整记录 | trace_id, query, answer, intent, citations, verified, need_human, fallback_reason, latency_ms |
| `tool_audit_logs` | 工具审计日志 | trace_id, tool_name, input_summary, output_summary, success, latency_ms |
| `feedback` | 用户反馈 | trace_id, session_id, thumbs_up, feedback_text |
| `eval_cases` | 评估案例 | query, expected_intent, expected_sources, difficulty, prompt_version |
| `failed_cases` | 失败案例 | trace_id, query, reason, source, payload |

**4 张运行时事件表（SQLAlchemy ORM 自动创建）：**

| 表名 | 用途 |
|------|------|
| `node_events` | LangGraph 节点事件记录 |
| `retrieval_events` | 检索事件记录 |
| `verification_events` | 校验事件记录 |
| `llm_events` | LLM 调用事件记录 |

### 17.4 管理脚本

| 脚本 | 功能 |
|------|------|
| `scripts/start_dev.sh` | 创建 .env + docker compose up + 健康检查 |
| `scripts/stop_dev.sh` | 停止所有服务（保留数据） |
| `scripts/reset_dev.sh` | 完全重置（删除数据卷 + 重新初始化） |
| `scripts/healthcheck.sh` | 检查 9 个服务是否正常 |
| `scripts/init_db.py` | 初始化 PostgreSQL（建表 + 插入 demo 用户） |
| `scripts/ingest_docs.py` | 文档导入流水线（向量 + 关键词 + MinIO） |
| `scripts/ingest_graph.py` | 知识图谱构建（实体抽取 + 关系抽取 + Neo4j 写入） |
| `scripts/build_graph_indexes.py` | 初始化 Neo4j 约束和索引 |
| `scripts/schedule_ingest.py` | 定时增量入库调度 |
| `scripts/run_graph_rag.py` | 运行 Graph-Augmented RAG 完整 trace |
| `scripts/export_failed_cases.py` | 从 PostgreSQL 导出失败案例为 JSONL |
| `scripts/import_eval_cases.py` | 从 JSONL 导入评估案例到 PostgreSQL |
| `scripts/migrate_local_to_middleware.py` | 本地数据迁移到中间件 |

---

## 18. 测试策略

### 18.1 测试金字塔

```
           ┌────────┐
           │  E2E   │  test_workflow.py      完整 LangGraph 工作流测试
           │ 工作流  │
           ├────────┤
           │  集成   │  test_memory.py, test_context.py, test_observability.py,
           │  测试   │  test_graph_orchestrator.py, test_graph_fusion.py, test_graph_context.py
           ├────────┤
           │  单元   │  test_rag.py, test_tools.py, test_recovery.py, test_evals.py,
           │  测试   │  test_router.py, test_qdrant_rag.py, test_graph_router.py,
           │        │  test_graph_retriever.py, test_es_keyword.py
           └────────┘
           总计: 17 个测试文件，~5,000+ 行测试代码
```

### 18.2 测试覆盖矩阵

| 测试文件 | 覆盖模块 | 测试要点 |
|----------|----------|----------|
| `test_workflow.py` | LangGraph 工作流 | 完整 14 节点编排、条件路由、重试循环、human fallback |
| `test_router.py` | Router Module | 意图分类（LLM+关键词）、边界 case、未知意图 |
| `test_rag.py` | RAG 基础 | 文档加载、分块、关键词检索（Jaccard 兜底） |
| `test_qdrant_rag.py` | RAG 完整 | 嵌入提供者、混合检索、MinIO、Milvus、文档导入流水线 |
| `test_es_keyword.py` | ES 关键词检索 | BM25 检索、IK 分词、ES 连接与索引管理 |
| `test_graph_router.py` | 动态检索路由 | 5 种路由模式选择、权重分配、降级路径 |
| `test_graph_retriever.py` | 知识图谱检索 | Cypher 查询、实体检索、1-2 跳遍历 |
| `test_graph_orchestrator.py` | 图谱编排器 | Graph RAG 完整流程、三路融合、降级链 |
| `test_graph_fusion.py` | 三路融合 | Weighted RRF、权重分配、融合排序 |
| `test_graph_context.py` | 图谱上下文 | graph_paths 格式化、上下文注入 |
| `test_tools.py` | 工具系统 | 工具注册、安全策略、执行、审计 |
| `test_memory.py` | 记忆系统 | 短期/摘要/用户记忆、Checkpoint |
| `test_context.py` | 上下文管理 | Token 预算、引用管理、Prompt 构建 |
| `test_recovery.py` | 故障恢复 | Fallback 策略、重试策略、恢复管理器 |
| `test_observability.py` | 可观测性 | Trace/Event/Logger/Metrics |
| `test_evals.py` | 评估体系 | RAG 评估、答案评估、回归评估、Data Flywheel |
| `test_tools.py` | 工具系统 | 注册、策略、执行器、各工具、权限检查、确认流程 |
| `test_memory.py` | 记忆系统 | 短期记忆、摘要生成、用户档案、检查点、统一管理器 |
| `test_context.py` | 上下文管理 | Token 预算分配、引用生成、Prompt 组装、上下文管理器 |
| `test_recovery.py` | 恢复系统 | 兜底类型、恢复动作、策略、重试、恢复管理器 |
| `test_observability.py` | 可观测性 | 事件 Schema、日志器、指标收集器、追踪器、节点包装 |
| `test_evals.py` | 评估系统 | 数据集、RAG 评估、答案评估、反馈处理、E2E 反馈流 |
| `test_workflow.py` | 工作流 | 图编译、完整流水线、多路径测试 |

### 18.3 测试设计模式

**1. 优雅降级测试：**
```python
def test_token_budget_fallback_on_huge_input():
    """极端大的输入不会崩溃"""
    huge_query = "A" * 100000
    budget = TokenBudget(max_tokens=4096)
    alloc = budget.allocate(query=huge_query)
    assert alloc.query > 0  # 永远不会是 0
```

**2. 空输入/边界测试：**
```python
def test_empty_docs_verification():
    verified, reason = verify_answer("some answer", [], [])
    assert not verified
    assert "缺乏依据" in reason
```

**3. 故障注入测试：**
```python
def test_logger_failure_does_not_crash():
    logger = EventLogger(log_path="/dev/null/nonexistent/path")
    event = NodeEvent(...)
    logger.log_event(event)  # 不应抛出异常
```

**4. 恢复路径测试：**
```python
def test_retrieve_exhausted_leads_to_human_fallback():
    state = {"retrieved_docs": [], "retry_count": {"retrieve": 1}}
    route = _after_retrieve(state)
    assert route == "human_fallback"
```

---

