# Prompt 设计

### Prompt Template 与上下文管理

##### 基础题：Prompt Template 的作用是什么？常见的变量替换方式有哪些？

**难度**：⭐（Prompt 工程、模板引擎、上下文管理）

**Answer**：

Prompt Template 的核心作用是**结构化 Prompt 生成**，实现内容与逻辑分离。

常见变量替换方式：

1. **占位符替换**（最基础）

```java
// SpringAI 风格
String prompt = "你是一个{role}助手，擅长{skill}";
String filled = prompt.replace("{role}", "编程")
                     .replace("{skill}", "Java 开发");
```

1. **Mustache 模板**（推荐）

```java
// 支持条件判断和循环
"""
{{#system}}
你是{{role}}专家
{{/system}}
{{#messages}}
用户：{{content}}
{{/messages}}
"""
```

1. **表达式引擎**（最强大）支持函数调用、算术运算等复杂逻辑，如 Spring Expression Language。

实际项目中建议用**成熟的模板引擎**（Mustache/FreeMarker），避免手写正则替换的边界问题。

---

##### 进阶题：Few-shot Prompt 的示例选择策略有哪些？如何动态选择最相关的示例？

**难度**：⭐⭐⭐（静态示例 vs 动态检索、Embedding 相似度选择、示例多样性、示例数量与效果的关系）

1️⃣ **Common Answer**：

重点总结（便于面试记忆）：

- 静态 vs 动态选择
- 动态选择策略
- 静态：人工精选固定示例，适合任务类型单一的场景（如固定格式的 SQL 生成）
- 动态：根据用户输入实时检索最相关的示例，适合多样化任务

2️⃣ **Impressive Answer**：

1. **静态 vs 动态选择**：

  - **静态**：人工精选固定示例，适合任务类型单一的场景（如固定格式的 SQL 生成）

  - **动态**：根据用户输入实时检索最相关的示例，适合多样化任务

1. **动态选择策略**：

```java
public class DynamicFewShotSelector {
    private final VectorStore exampleStore;

    public List<Example> selectExamples(String userQuery, int topK) {
        // Step1: Embedding 相似度检索
        List<Example> candidates = exampleStore.similaritySearch(userQuery, topK * 2);

        // Step2: 多样性过滤（MMR 算法）
        // 避免选出的示例过于相似，增加覆盖面
        List<Example> diverseExamples = maximalMarginalRelevance(
            candidates, userQuery, topK, diversityWeight: 0.3);

        // Step3: 按难度排序（简单→复杂）
        diverseExamples.sort(Comparator.comparing(Example::getDifficulty));
        return diverseExamples;
    }
}
```

1. **示例数量的权衡**：示例越多效果越好，但占用 Token 越多。经验值：简单任务 2-3 个，复杂任务 5-8 个；超过 8 个通常边际收益递减。

1. **示例质量 > 数量**：一个高质量的示例（覆盖边界情况）胜过五个普通示例。示例应覆盖**正常路径 + 边界情况 + 错误处理**。

3️⃣ **Key Differences**

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
选择策略
</td>
<td>
只说了相似度
</td>
<td>
相似度→MMR 多样性→难度排序
</td>
</tr>
<tr>
<td>
代码深度
</td>
<td>
无
</td>
<td>
有完整的动态选择器实现
</td>
</tr>
<tr>
<td>
核心洞察
</td>
<td>
3-5 个
</td>
<td>
&quot;质量 &gt; 数量&quot;，覆盖边界情况
</td>
</tr>
<tr>
<td>
实践经验
</td>
<td>
概念层面
</td>
<td>
有 MMR 算法和经验数据
</td>
</tr>
</table>

---

##### 场景题：Agent 需要处理多语言用户输入，Prompt Template 如何设计才能兼顾多语言？

**难度**：⭐⭐⭐（语言检测、模板国际化、System Prompt 语言策略、翻译 vs 原生多语言模型）

1️⃣ **Common Answer**：

重点总结（便于面试记忆）：

- 三种策略对比
- 推荐方案：语言感知 + 动态模板
- 关键原则
- Agent 场景特殊处理

2️⃣ **Impressive Answer**：

1. **三种策略对比**：

<table>
<tr>
<td>
策略
</td>
<td>
优点
</td>
<td>
缺点
</td>
<td>
适用场景
</td>
</tr>
<tr>
<td>
模型原生多语言
</td>
<td>
简单，无额外延迟
</td>
<td>
小语种效果差
</td>
<td>
GPT-4 等强多语言模型
</td>
</tr>
<tr>
<td>
翻译中转
</td>
<td>
效果稳定
</td>
<td>
增加延迟和成本
</td>
<td>
本地模型 + 翻译 API
</td>
</tr>
<tr>
<td>
多语言模板
</td>
<td>
精确控制
</td>
<td>
维护成本高
</td>
<td>
高质量要求的固定场景
</td>
</tr>
</table>

1. **推荐方案：语言感知 + 动态模板**：

```java
public class MultiLangPromptBuilder {
    public Prompt build(String userInput) {
        String detectedLang = languageDetector.detect(userInput);

        // System Prompt 始终用英文（模型理解最好）
        String systemPrompt = loadTemplate("system_prompt_en.mustache");

        // 输出指令动态切换语言
        String langInstruction = String.format(
            "You MUST respond in %s. Match the user's language exactly.",
            detectedLang);

        // Few-shot 示例选择对应语言的版本
        List<Example> examples = exampleSelector.select(userInput, detectedLang);

        return Prompt.builder()
            .system(systemPrompt + "\n" + langInstruction)
            .examples(examples)
            .user(userInput)
            .build();
    }
}
```

1. **关键原则**：System Prompt 用英文（模型理解力最强），输出语言跟随用户；Few-shot 示例尽量用目标语言（减少语言切换的认知负担）。

1. **Agent 场景特殊处理**：工具调用的参数始终用英文（API 兼容性），只有最终回复跟随用户语言。

3️⃣ **Key Differences**

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
方案对比
</td>
<td>
列举但没有选型
</td>
<td>
三种策略对比表格 + 推荐方案
</td>
</tr>
<tr>
<td>
代码深度
</td>
<td>
无
</td>
<td>
有完整的多语言 Prompt 构建器
</td>
</tr>
<tr>
<td>
核心原则
</td>
<td>
没有总结
</td>
<td>
&quot;System 用英文，输出跟用户&quot;
</td>
</tr>
<tr>
<td>
Agent 适配
</td>
<td>
未考虑
</td>
<td>
工具参数英文，回复跟用户语言
</td>
</tr>
</table>
---

## 知识点一句话总结

| 知识点 | 一句话总结（来自 Impressive Answer） |
| --- | --- |
| Prompt Template 的作用是什么？常见的变量替换方式有哪些？ | Prompt Template 的核心作用是结构化 Prompt 生成，实现内容与逻辑分离；表达式引擎：（最强大）支持函数调用、算术运算等复杂逻辑，如 Spring Expression Language；实际项目中建议用成熟的模板引擎（Mustache/FreeMarker），避免手写正则替换的边界问题。 |
| Few-shot Prompt 的示例选择策略有哪些？如何动态选择最相关的示例？ | 静态：人工精选固定示例，适合任务类型单一的场景（如固定格式的 SQL 生成）；动态：根据用户输入实时检索最相关的示例，适合多样化任务 |
| Agent 需要处理多语言用户输入，Prompt Template 如何设计才能兼顾多语言？ | 模型原生多语言上，优点是简单，无额外延迟，缺点是小语种效果差；翻译中转上，优点是效果稳定，缺点是增加延迟和成本；多语言模板上，优点是精确控制，缺点是维护成本高。 |
