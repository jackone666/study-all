# 12 SolutionCompare方案对比工具与CompatCheck版本兼容工具

> 面试口径：HarmonyDev 是服务 HarmonyOS / OpenHarmony 开发的 AI 开发助手；系统实现主体是 Python Agent 后端 + LocalAgent Gateway + Web/DevEco 面板，不要求运行在鸿蒙设备上。鸿蒙相关内容是被服务的开发对象，包括 ArkTS、ArkUI、Ability、Stage 模型、构建日志和官方文档。


**模块目标：**

- 接住第 11 章 4 路候选合流后的下一段：修复方案对比 + 版本兼容估算。

- 理解为什么 SolutionCompare 和 CompatCheck 在 HarmonyDev 里**不需要 fork**——它们是典型的"主 loop 自己处理就够了"场景。

- 掌握“改动范围归一 / API Level 分级 / 兼容性风险分档”这些鸿蒙开发场景特有的工程细节。

- 看清两个工具的协作模式：SolutionCompare 输出结构化对比，CompatCheck 把"落地成本"算清楚。

**阅读重点：** 这一章是 9 个工具里**最容易被低估、也最容易出错**的两个。建议把每段代码读到具体公式——很多 bug 不是工具用错了，而是API Level、废弃状态、设备能力矩阵、兼容性分档这种业务细节没对。

---

## 1、本章导读

### 1.1 上一章结束在哪里

上一章 4 路同质子 AgentLoop 各自跑完 DocSearch，主 loop 拿到一个合流后的候选集：

```
[
  DocHit(doc_id=A1, source=harmony_docs,    impl_cost=1.2, api_level=12, ...),
  DocHit(doc_id=A2, source=harmony_docs,    impl_cost=2.5, api_level=11, ...),
  ...
  DocHit(doc_id=S1, source=openharmony_docs,    impl_cost=3.0, api_level=10, ...),
  ...
  DocHit(doc_id=X1, source=sample_code, impl_cost=2.4, risk_score=0.35, ...),
  ...
  DocHit(doc_id=E1, source=migration_notes,      impl_cost=1.8, migration_risk=0.2, ...),
  ...
]   # 大约 4 × 20 = 80 条
```

接下来主 loop 在 Think 阶段会问自己一个非常具体的问题：**"加上兼容性风险 / 版本约束之后，哪条修复路径最稳？"**

这正是 SolutionCompare + CompatCheck 要回答的。

### 1.2 本章先做什么，不做什么

要做的：

1. 设计 SolutionCompare 的工具签名和"方案复杂度归一"算法。

1. 设计 CompatCheck 的工具签名和"版本分级 / 兼容性分档"算法。

1. 讲清这两个工具为什么属于"主 loop 直接调"——不满足 fork 三件事。

1. 给出主 loop 怎么"先 SolutionCompare 拿到 Top-N，再让 CompatCheck 只算 Top-N"的协作模式。

不做的：

- PatchPicker 的二次筛选、DevSummary 的最终修复建议留给第 14 章。

- 真实 HarmonyOS / OpenHarmony 版本差异、设备能力矩阵和系统 API 兼容细节超出当前实现范围，本章给出可演示的简化模型。

---

## 2、为什么这两个工具不 fork

### 2.1 用三件事判断对一遍

| 条件 | SolutionCompare 场景 | CompatCheck 场景 |
| --- | --- | --- |
| 能并行 | ❌ 只是一次性算一个排序 | ❌ 一次输入只对应一次输出 |
| 上下文要隔离 | ❌ 输入是 80 条 DocHit 摘要 | ❌ 输入是 Top-N 已经被 SolutionCompare 筛过 |
| 调用链 ≥ 3 | ❌ 内部就是个加法 + 排序 | ❌ 内部就是查兼容矩阵 + 查兼容性风险表 |

三个条件一个都不满足。fork 反而会平白多一次主 / 子 LLM 调用，浪费延迟和 token。

### 2.2 这件事说明什么

不是所有"工具调用"都该 fork。**fork 的成本不低**——多一次 LLM 推理 + checkpoint + AGUI 事件路由。值不值得 fork，永远要回到"能并行 / 上下文隔离 / 链深"三件事。

SolutionCompare 和 CompatCheck 是"主 loop 自己处理就够了"的典型样本，刚好和上一章的 DocSearch 形成对比。

---

## 3、SolutionCompare 工具

### 3.1 它要解决的问题

修复方案对比不是"按实现成本排序"那么简单：

| 难点 | 例子 |
| --- | --- |
| 评分口径不一样 | harmony_docs 给改动步数 / openharmony_docs 给 API level / sample_code 给 risk_score |
| 粒度不一样 | 单 API / 组合方案（3 个 API + 1 个配置文件） |
| API Level / 废弃状态 | 候选方案改动小但若 API 已废弃，则兼容性风险高于复杂度收益 |
| 可信度和采纳次数也要权衡 | 实现成本低 5%，但来源可信度低、采纳次数少，到底选谁 |

SolutionCompare 的设计目标：**输出一个多源、方案复杂度归一、可解释的排序，并保留足够字段让模型在 Reflect 阶段做判断。**

### 3.2 工具签名

```python
# app/tools/solution_compare.py
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from app.tools.doc_search import DocHit

class SolutionPoint(BaseModel):
    doc_id: str
    source: str
    title: str
    impl_cost_raw: float
    score_unit: str
    compat_score: float                    # 归一后的实现复杂度（仅方案本体，不含兼容性风险）
    confidence: float | None = None
    adoption_count: int | None = None
    note: str | None = None                # 例如 "组合方案含 3 个 API + 1 个配置文件"

class SolutionCompareOutput(BaseModel):
    target_unit: str = "impl_cost"
    ranked: list[SolutionPoint]
    best_per_source: dict[str, str]  # {"harmony_docs": "A1", "openharmony_docs": "S2", ...}

@tool
async def solution_compare(
    candidates: list[DocHit],
    target_unit: str = "impl_cost",
    top_n: int = 12,
) -> SolutionCompareOutput:
    """候选方案API/代码片段方案对比，输出方案复杂度归一后的排序。

    Args:
        candidates: 来自 DocSearch 合流后的候选集（最多接受 100 条）。
        target_unit: 归一目标单位，默认 impl_cost。
        top_n: 仅返回排序后的前 N 条，默认 12，最大 30。

    Returns:
        ranked: 按 compat_score 升序的 SolutionPoint 列表。
        best_per_source: 每个资料源的最稳妥 doc_id，便于 CompatCheck 复用。
    """
    ...
```

关键设计：

- **入参直接传 **`list[DocHit]`：和 DocSearch 的出参 schema 对接，模型不用做格式转换。

- `top_n=12`：让后续 CompatCheck 只算 12 条，不要给 80 条全做兼容性检查——这是工具协作里的"剪枝"。

- `note`** 字段**：留给"组合方案含多个 API / 配置文件"这类特殊场景的人类可读说明。

### 3.3 方案复杂度归一

```python
# app/recall/cost_normalizer.py（方案复杂度归一服务，简化为静态表）
from typing import Final

# 实际项目应接规则表并加缓存
COST_FACTORS: Final[dict[str, float]] = {
    "impl_cost": 1.0,
    "api_level_gap": 0.8,
    "migration_risk": 1.5,
    "sample_complexity": 1.2,
}

def normalize_cost(value: float, unit: str, base: str = "impl_cost") -> float:
    if unit not in COST_FACTORS or base not in COST_FACTORS:
        raise ValueError(f"未知复杂度单位: {unit} 或 {base}")
    return value * COST_FACTORS[unit] / COST_FACTORS[base]
```

### 3.4 主体实现

```python
# app/tools/solution_compare.py（续）
import time
from app.api.monitor import monitor
from app.recall.cost_normalizer import normalize_cost

@tool
async def solution_compare(
    candidates: list[DocHit],
    target_unit: str = "impl_cost",
    top_n: int = 12,
) -> SolutionCompareOutput:
    """候选方案API/代码片段方案对比。"""
    top_n = min(top_n, 30)
    candidates = candidates[:100]
    await monitor.report_tool_start("solution_compare", {
        "candidates_count": len(candidates),
        "target_unit": target_unit,
    })
    t0 = time.time()

    points: list[SolutionPoint] = [ ]

    for c in candidates:
        try:
            normalized_cost = normalize_cost(c.impl_cost, c.score_unit, target_unit)
        except ValueError:
            continue
        points.append(SolutionPoint(
            doc_id=c.doc_id,
            source=c.source,
            title=c.title,
            impl_cost_raw=c.impl_cost,
            score_unit=c.score_unit,
            compat_score=round(normalized_cost, 2),
            confidence=c.confidence,
            adoption_count=c.adoption_count,
            note=_combo_note(c),
        ))

    points.sort(key=lambda p: p.compat_score)
    ranked = points[:top_n]

    best: dict[str, str] = {}
    for p in points:
        if p.source not in best:
            best[p.source] = p.doc_id

    await monitor.report_tool_end("solution_compare", int((time.time() - t0) * 1000))
    return SolutionCompareOutput(
        target_unit=target_unit,
        ranked=ranked,
        best_per_source=best,
    )

def _combo_note(c: DocHit) -> str | None:
    """从 attributes 中识别组合方案信息。"""
    api_count = c.attributes.get("api_count")
    file_count = c.attributes.get("file_count")
    if api_count or file_count:
        return f"组合方案：{api_count or 0} 个 API，{file_count or 0} 个文件"
    return None
```

### 3.5 排序里没有的两件事

**不在 SolutionCompare 里做的事**：

1. **不直接用可信度 / 采纳次数给API/代码片段打综合分**——那是 PatchPicker 的职责。

1. **不做兼容性检查和版本约束**——那是 CompatCheck 的职责。

让一个工具只做一件事，主 loop 才能有意义地调用它们的组合。

---

## 4、CompatCheck 工具

### 4.1 它要解决的问题

落地成本 ≠ 实现成本。一个看起来只改 2 行的 API/代码片段，如果目标版本不支持、涉及废弃 API 或需要跨 Ability 重构，真实落地风险会明显高于表面复杂度。如果用户不知道这个差额，"最稳妥方案"会看走眼。

CompatCheck 要算的是 **实现成本 + API 兼容风险 + 版本迁移风险**，并统一折成 `resolved_score`。

### 4.2 工具签名

```python
# app/tools/compat_check.py
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Literal
from app.tools.solution_compare import SolutionPoint

class CompatResult(BaseModel):
    doc_id: str
    source: str
    compat_score: float
    migration_cost: float
    api_risk_score: float
    resolved_score: float                # 落地成本 = 实现复杂度 + 兼容风险 + 迁移风险
    verify_minutes: int                    # 验证耗时预估
    risk_tier: Literal["低风险", "标准", "高风险"]

class CompatCheckOutput(BaseModel):
    target_version: str
    items: list[CompatResult]

@tool
async def compat_check(
    points: list[SolutionPoint],
    target_version: str = "HarmonyOS 5.0",
) -> CompatCheckOutput:
    """为已方案对比的候选估算落地成本（含 API 兼容风险 + 版本迁移风险）。

    Args:
        points: 来自 SolutionCompare.ranked 的子集（建议直接传 ranked，不超过 30 条）。
        target_version: 目标 HarmonyOS / OpenHarmony 版本。

    Returns:
        items: 每条候选的 CompatResult，按 resolved_score 升序。
    """
    ...
```

注意 CompatCheck **不接受原始 DocHit**，只接受 SolutionCompare 算过方案复杂度归一的 SolutionPoint。这是工具链路里的"约定"——上游已经做过的事下游不重做。

### 4.3 版本与兼容性的简化模型

```python
# app/recall/api_risk.py
from typing import Literal

# 极简的"通用兼容矩阵"，实际应按 API level / targetSdk / 废弃状态查
API_RISK_TABLE: dict[str, tuple[float, Literal["低风险", "标准", "高风险"]]] = {
    "harmony_docs":     (0.13, "标准"),
    "openharmony_docs":     (0.06, "低风险"),  # 走OpenHarmony 文档路径默认低风险
    "sample_code": (0.13, "标准"),
    "migration_notes":       (0.20, "高风险"),  # 迁移说明通常代表版本差异更大
}

def estimate_api_risk(compat_score: float, source: str) -> tuple[float, str]:
    rate, tier = API_RISK_TABLE.get(source, (0.13, "标准"))
    return round(compat_score * rate, 2), tier
```

```python
# app/recall/migration_cost.py
# 按改动复杂度 + 资料源的简化迁移成本表
MIGRATION_COST_TABLE: dict[str, list[tuple[float, float, int]]] = {
    # source: [(min_complexity, migration_cost, verify_minutes), ...]
    "harmony_docs":     [(0, 0.5, 12), (2.0, 1.0, 20), (4.0, 2.0, 35)],
    "openharmony_docs": [(0, 0.4, 15), (2.0, 1.2, 25), (4.0, 2.5, 45)],
    "sample_code":      [(0, 0.8, 25), (2.0, 1.6, 40), (4.0, 3.0, 60)],
    "migration_notes":  [(0, 1.0, 20), (2.0, 2.0, 40), (4.0, 3.5, 75)],
}

def estimate_migration_cost(complexity: float, source: str) -> tuple[float, int]:
    table = MIGRATION_COST_TABLE.get(source, MIGRATION_COST_TABLE["harmony_docs"])
    cost, minutes = table[0][1], table[0][2]
    for min_complexity, c, m in table:
        if complexity >= min_complexity:
            cost, minutes = c, m
    return cost, minutes
```

### 4.4 主体实现

```python
# app/tools/compat_check.py（续）
import time
from app.api.monitor import monitor
from app.recall.api_risk import estimate_api_risk
from app.recall.migration_cost import estimate_migration_cost

@tool
async def compat_check(
    points: list[SolutionPoint],
    target_version: str = "HarmonyOS 5.0",
) -> CompatCheckOutput:
    """为已方案对比的候选估算落地成本。"""
    await monitor.report_tool_start("compat_check", {
        "items_count": len(points), "target_version": target_version,
    })
    t0 = time.time()

    compat: list[CompatResult] = [ ]

    for p in points:
        complexity = _guess_complexity_level(p)
        migration_cost, eta = estimate_migration_cost(complexity, p.source)
        api_risk_score, risk_tier = estimate_api_risk(p.compat_score, p.source)
        total = round(p.compat_score + migration_cost + api_risk_score, 2)
        compat.append(CompatResult(
            doc_id=p.doc_id,
            source=p.source,
            compat_score=p.compat_score,
            migration_cost=migration_cost,
            api_risk_score=api_risk_score,
            resolved_score=total,
            verify_minutes=eta,
            risk_tier=risk_tier,
        ))

    compat.sort(key=lambda x: x.resolved_score)

    await monitor.report_tool_end("compat_check", int((time.time() - t0) * 1000))
    return CompatCheckOutput(target_version=target_version, items=compat)

def _guess_complexity_level(p: SolutionPoint) -> float:
    """从 SolutionPoint 反推出大致改动复杂度。真实项目应来自 DocHit.attributes。"""
    # 这里给一个占位值；第 13 章 APIInsight 会把 Kit 能力域典型复杂度补回来
    return p.compat_score
```

### 4.5 边界情况

| 情况 | 处理 |
| --- | --- |
| 改动复杂度未知 | 退到 Kit 能力域默认值（第 13 章会补） |
| API 未在兼容矩阵 | 标记为中风险并要求人工确认 |
| 兼容性风险表全部超出（极复杂 API/代码片段） | 走最高档 + 加日志，下次调权 |

不要为了完美而阻塞链路——鸿蒙开发场景里"大致对的落地成本"比"不返回"对用户体验更友好。

---

## 5、主 loop 的协作模式

### 5.1 Think 阶段的话术

主 loop 的 LLM 在 Think 阶段会产出这样的内部独白（这是 system prompt 引导的结果）：

```
我已经拿到 4 类资料源合流后的 80 条候选。
下一步要选最稳妥的。直接按方案复杂度排会被兼容性风险坑，所以：
  1. 先 solution_compare 拿方案复杂度归一后的 Top-12
  2. 再 compat_check 算这 12 条的落地成本
  3. 把 resolved_score 最低的几条交给 patch_picker 二次筛选
```

### 5.2 工具调用顺序

```python
# 主 loop 的等价 Python 视角（实际由 LLM 决定）
pc_out = await solution_compare(candidates=合流候选, top_n=12)
sc_out = await compat_check(points=pc_out.ranked, target_version="HarmonyOS 5.0")
# sc_out.items 已经按 resolved_score 升序，直接喂给 PatchPicker
```

注意 CompatCheck 只算 12 条，不算 80 条。这是"上游剪枝下游计算"的工程意识。

### 5.3 AGUI 事件流前端怎么显示

```
[tool_start] solution_compare 正在方案对比...
[tool_end]   solution_compare 完成（126 ms）
[tool_start] compat_check 正在做兼容性检查 / 版本约束...
[tool_end]   compat_check 完成（38 ms）
```

注意没有 `fork` 事件——这两个工具确实没 fork。前端面板可以渲染成"主 loop 直接调"的样子，让用户看清楚"什么时候 HarmonyDev 自己干、什么时候它叫了多个子 Agent"。

---

## 6、容易踩的两个坑

### 6.1 不要在 SolutionCompare 里偷偷做兼容性检查

很多新手会想"反正都要算落地成本，不如一步到位"。这样做有三个问题：

| 坏处 | 后果 |
| --- | --- |
| 工具职责模糊 | 模型不知道单调 SolutionCompare 是不是已经做兼容性检查 |
| 主 loop 没法做 Top-N 剪枝 | 每次都要算 80 条兼容性风险，浪费 |
| AGUI 事件粒度变粗 | 前端不知道哪一步在方案对比、哪一步在做兼容性检查 |

让一个工具只做一件事，会比"少调一次工具"重要得多。

### 6.2 不要让 CompatCheck 去查 DocSearch

也有人会想"兼容性风险需要改动复杂度，复杂度在 DocHit 里，让 CompatCheck 自己反查 DocSearch 拿到 attributes"。

这违反了**工具单向数据流**：上游产出的字段，下游应该要么用要么忽略，不能反向去叫上游。如果复杂度信息丢了，要么在 SolutionCompare 把 complexity_level 透传到 SolutionPoint，要么用 Kit 能力域默认值兜底——绝不让下游工具反过来"找"上游。

---

**本章小结：**

到这里，4 路候选合流之后的两步处理已经做完。现在你应该清楚：

- SolutionCompare 和 CompatCheck 都不需要 fork——它们都不满足"能并行 / 上下文隔离 / 链深 ≥ 3"任一条件，主 loop 直接调最稳妥；

- SolutionCompare 只做"方案复杂度归一 + 排序"，CompatCheck 只做"落地成本"，互不重叠；

- 工具间通过 Pydantic schema（DocHit → SolutionPoint → CompatResult）做单向数据流，上游剪枝、下游消费；

- 简化的版本分级 / 兼容性分档可以让 demo 跑起来，真实项目按 HarmonyOS API Level、targetSdkVersion、废弃状态和设备能力矩阵接规则服务即可；

- AGUI 事件流里这两步是直链，没有 fork——这正是"什么时候 HarmonyDev 自己干、什么时候叫子 Agent"的最直观对比。

下一章「[APIInsight Kit 能力洞察工具与 RAG 鸿蒙知识库](<18-13 APIInsight能力洞察工具与RAG鸿蒙知识库.md>)」会做Kit 能力洞察——把"这个 Kit 能力下当前常用什么、典型约束怎么分布"接进来，作为 PatchPicker 二次筛选的判断依据。
