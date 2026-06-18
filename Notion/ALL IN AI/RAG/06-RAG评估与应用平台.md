---
notion-id: 338a95f7-5835-811f-bc9e-c0e8dac54989
---
## RAG评估和应用平台
**学习目标:**
1. 熟悉 RAG评估方式
2. 熟悉 RAG评估工具
3. 熟悉 RAG应用平台

### 一. RAG评估
- RAG评估是对基于检索增强生成模型（RAG）的性能进行评估和全面分析的过程。也就是去判断RAG他的能力怎么样。RAG有检索和生成的两种能力，用于对话系统和问答等任务中。
- RAG评估的的目标是看检索相关文档和生成准确、连贯回答这方面的表现。
- 任何RAG系统的有效性和性能都严重依赖于这两个核心组件：**检索器和生成器**。检索器必须高效地识别和检索最相关的文档，而生成器应该使用检索到的信息生成连贯、相关和准确的响应。在部署之前，对这些组件进行严格评估对于确保RAG模型的最佳性能和可靠性至关重要。

### 1. 评估指标
- RAG评估的方式有很多种:
- 检索评估(检索到的内容)
- 响应评估(模型响应的内容)
- 系统性能评估(执行的效率)
- 鲁棒性评估(纠错机制)
- ……
- 主要使用的是两种类型的评估
- 检索评估
    - 精确度
    - 召回率
- 响应评估
    - 忠诚度
    - 答案相关性

### 2. 检索评估
- 检索评估的主要目标是评估上下文相关性，即检索到的文档与用户查询的匹配程度。它确保提供给生成组件的上下文是相关和准确的。

### 2.1 精确度
- 精确度衡量了检索到的文档的准确性。它是检索到的相关文档数量与检索到的文档总数之比。定义如下：
$$
精确度=\frac{检索到的相关文档数量}{检索到的文档总数}
$$
- 这意味着精确度评估了系统检索到的文档中有多少实际与用户查询相关。例如，如果检索器检索到了10个文档，其中7个是相关的，那么精确度将是0.7或70%。

> 精确度评估的是“系统检索到的所有文档中，有多少实际上是相关的？

- 在可能导致负面后果的情况下，精确度尤为重要。例如，在医学信息检索系统中，高精确度至关重要，因为提供不相关的医学文档可能导致错误信息和潜在的有害结果。

### 2.2 召回率
- 召回率衡量了检索到的文档的覆盖率。它是检索到的相关文档数量与数据库中相关文档的总数之比。定义如下：
$$
召回率=\frac{检索到的相关文档数量}{数据库中相关文档的总数}
$$

> 假设：
> - 知识库中有 10 篇与问题相关的文档。
> - 模型检索到了 7 篇相关文档。
> - Recall=7/10=0.7

- 这意味着召回率评估了数据库中存在的相关文档有多少被系统成功检索到。
- 召回率评估的是“数据库中存在的所有相关文档中，系统成功检索到了多少”
- 在可能错过相关信息会产生成本的情况下，召回率至关重要。例如，在法律信息检索系统中，高召回率至关重要，因为未能检索到相关的法律文件可能导致不完整的案例研究，并可能影响法律诉讼的结果。

### 2.3 F1分数
- F1分数用来平衡精确度和召回率，目标是找到适合特定应用需求的最佳平衡。F1分数是精确度和召回率的调和平均值：
```plain text
                                 $$ F1分数=2\frac{准确率 \times 召回率}{准确率 + 召回率} $$
```

![[1769758888140-1ca27026-7072-4e95-82d8-41091b4af957.png]]
- 合理区间

| **F1 范围** | **性能评价** | **适用阶段** | **典型场景** |
| --- | --- | --- | --- |
| <0.5 | 需重大优化 | 模型原型/POC 阶段 | 初步实验、基线测试 |
| 0.5-0.7 | 基本可用 | 内部测试/非关键场景 | 内部工具、非核心功能 |
| 0.7-0.85 | 良好性能 | 准生产环境 | 电商推荐、客服问答 |
| 0.85-0.93 | 优秀性能 | 生产环境关键系统 | 金融风控、医疗辅助诊断 |
| >0.93 | 接近理论上限 | 高精度要求场景 | 工业质检、法律条款匹配 |

> F1 分数的合适值**没有绝对标准**，完全取决于**业务场景需求**、**数据特性**和**错误容忍度**。

### 3. 响应评估
- 响应评估适用于系统的生成组件。这些评估衡量系统根据检索到的文档提供的上下文有效地生成响应的能力。我们将响应评估分为两种类型：

![[1769758888214-46e52f28-d869-43f5-9aca-df93b2a89250.png]]
![[1769758888279-f3a2d29e-185f-4000-8d88-147549c483ba.png]]
- 忠实度
- 答案相关性

### 二. 评估方法
### 1. 人工评估
- 人工评估是RAG评估的基础方法，通过邀请专家或人工评估员对RAG生成的结果进行质量评估。评估标准通常包括准确性、连贯性、相关性等。尽管人工评估能够提供高质量的反馈，但这种方法耗时费力，且受限于评估员的主观性和经验差异。

### 2. 自动化评估
- 自动化评估是当前RAG评估的主流和发展方向。通过利用大型语言模型和相关算法，自动化评估工具能够实现对RAG生成文本的质量评分，从而快速评估模型性能。这种方法不仅提高了评估效率，还降低了人力成本。

### 三. 常用的评估工具介绍
- 目前开源社区已经出现了专业的工具，用户可以使用它们来方便快速进行定量评估。下面我们介绍目前比较常见好用的 RAG 评估工具，以及它们的一些特点。

### 1. Ragas
### 1. 简介
- RAGAs是一个用于评测检索增强生成（RAG）应用的评测框架，它的核心目标是提供一套综合性的评测指标和方法，以量化地评测RAG管道(RAG Pipeline)在不同组件层面上的性能。RAGAs特别适用于那些结合了检索（Retrieval）和生成（Generation）两个主要组件的RAG系统，支持Langchain 和 Llama-Index。
- 开源链接：[https://github.com/explodinggradients/ragas](https://github.com/explodinggradients/ragas)
- 论文: [https://arxiv.org/pdf/2309.15217](https://arxiv.org/pdf/2309.15217)
- 为了评估 RAG 系统，RAGAs 需要以下信息:

> question：用户输入的问题。
> answer：从 RAG 系统生成的答案(由LLM给出)。
> contexts：根据用户的问题从外部知识源检索的上下文即与问题相关的文档。
> ground_truths： 人类提供的基于问题的真实(正确)答案。 这是唯一的需要人类提供的信息。

![[1769758888346-fd82cdef-1bee-4bed-804b-613ed3eabfe7.png]]
### 2. 评估指标
- **四个评估指标** :
- 评估检索质量：
    - context_precision（上下文相关性, 问题和检索内容的相关性）
    - context_recall（召回性，越高表示检索出来的内容与正确答案越相关）
- 评估生成质量：
    - faithfulness（忠实性，越高表示答案的生成使用了越多的参考文档（检索出来的内容））
    - answer_relevancy（答案的相关性）

![[1769758888415-8daaaad1-9d88-4d1a-a001-a26dc759d103.png]]
### 2.1 faithfulness
![[1769758888489-4ced51bf-3393-46d0-891d-2d4f95b77c73.png]]
- 计算方式
$$
\text{Faithfulness} = \frac{\text{被上下文支持的声明数}}{\text{答案中的总声明数}}
$$
- 举例

![[1769758888638-4ff23076-9e3e-4a82-867f-aee6bd68d3d1.png]]
- 实际效果
- 把答案「拆成一条条小句子」→ 逐条去检索结果（contexts）里找 → 看每条是不是“原样出现”或“语义支持” → 统计比例
- Faithfulness = 检查大模型有没有「瞎编」不在检索结果里的内容
- 优化方式:
- 优化提示词对模型输出的内容进行约束
- 提高检索top_k值

### 2.2 answer_relevancy
![[1769758888708-a7ef64c8-a8f9-4c36-94ba-e864d2e6f6cf.png]]
- 计算方式

![[1769758888849-9597a244-5fa7-4f1c-9dbc-a556fa3045ed.png]]
- 举例:

![[1769758888942-72155e8f-42bc-4011-b92f-dbeb9537d269.png]]
- 实际效果:
- Answer Relevancy = 答案越能「反问」出原问题 → 分数越高
- 优化方式:
- 预索引(问题拓展)

### 2.3 context_precision
![[1769758889017-a678685a-1143-4ccc-b3ad-b062f31a28ba.png]]
- 举例

![[1769758889083-a9ba1d5d-be66-4af9-b0e1-cd2e25b70490.png]]
- 实际效果
- 评估对象：检索到的context与**问题(Question)**的相关性
- 判断标准：LLM判断每个context能否帮助回答问题
- 计算目标：衡量检索器是否把能回答问题的context排在前面
- 分数含义： 分数高 = 相关内容排序靠前 ✅ 分数低 = 相关内容排序靠后 ❌
- 优化方向:
- 使用重排模型进行重新排序
- 混合检索
- Query 改写与扩展
- 优化 Embedding 模型

### 2.4 context_recall
![[1769758889174-f80b80e9-94bc-4ccb-b767-231be7d315c6.png]]
- 举例

![[1769758889253-d6d38b75-d525-4dee-a19f-460e14899405.png]]
- 实际效果
- 需要 Ground Truth: Context Recall 必须有参考答案才能计算
- 评估召回能力: 衡量检索系统是否找到了所有必要信息 LLM
- 作为判断器: 使用 LLM 判断陈述是否被支持
- 原子化分解: Ground Truth 需要分解为独立的事实陈述
- 取值范围: 0-1，越接近 1 表示召回越完整
- 优化方向
- 增加 Top-K + Reranker
- 混合检索
- Query 改写与分解
- Parent Document Retriever

### 2. Trulens
- TruLens是一款旨在评估和改进 LLM 应用的软件工具，它相对独立，可以集成 LangChain 或 LlamaIndex 等 LLM 开发框架。它使用反馈功能来客观地衡量 LLM 应用的质量和效果。这包括分析相关性、适用性和有害性等方面。TruLens 提供程序化反馈，支持 LLM 应用的快速迭代，这比人工反馈更快速、更可扩展。
- 开源链接：[https://github.com/truera/trulens](https://github.com/truera/trulens)

![[1769758889356-b13acb25-f785-4bdf-ad2d-6f3746e1feab.png]]
使用的步骤：
（1）创建LLM应用
（2）将LLM应用与TruLens连接，记录日志并上传
（3）添加 feedback functions到日志中，并评估LLM应用的质量
（4）在TruLens的看板中可视化查看日志、评估结果等
（5）迭代和优化LLM应用，选择最优的版本
**三个评估指标**
- 上下文相关性（context relevance）：衡量用户提问与查询到的参考上下文之间的相关性
- 忠实性（groundedness ）：衡量大模型生成的回复有多少是来自于参考上下文中的内容
- 答案相关性（answer relevance）：衡量用户提问与大模型回复之间的相关性

![[1769758889430-f47f3a6d-bd9d-4666-8d3a-ef266011d011.png]]
### 四. 评估案例
- 需要在RAGS网址注册token
- 网址: [https://app.ragas.io](https://app.ragas.io/)

### 4.1 模块安装
```plain text
pip install ragas==0.3
```
### 4.2 完整代码
```plain text
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_core.stores import InMemoryStore
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()

# 创建BAAI的embedding
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
bge_embeddings = HuggingFaceEmbeddings(model_name=embedding_model_path)
urls = "https://baike.baidu.com/item/%E6%81%90%E9%BE%99/139019"
loader = WebBaseLoader(
    urls,
    header_template={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'cookie': 'zhishiTopicRequestTime=1761745354412; PSTM=1760964266; BAIDUID=CDADB0D59AC42CF2E480DD38F8F0A8A2:FG=1; BIDUPSID=BB3C8281FAB5D9BF613466F32412F0C4; BAIDUID_BFESS=CDADB0D59AC42CF2E480DD38F8F0A8A2:FG=1; ZFY=3vUqyGhXIfCOJU5wvX2ZZ7CU88lGG8DmvmQS:A9cdcKw:C; H_PS_PSSID=63148_64982_65247_65311_65361_65539_65618_65723_65759_65776_65803_65838_65858_65915_65921_65925_65940_65941_65962_65966_65989; H_WISE_SIDS=63148_64982_65247_65311_65361_65539_65618_65723_65759_65776_65803_65838_65858_65915_65921_65925_65940_65941_65962_65966_65989; ab_sr=1.0.1_NzlhZTU5ZDA3YjdiN2RkMzMwN2I2NjVjNTNjNzJkNjk4NDA5NWY3ZGZlN2I3NjhhZjUyZTFhOTdjYTZmZjRkYWE2NDhmNzBkZjA1OGU4ZWVjOGU3ODVlMjRjZWM0OWM5ZGZhMGRmODg3ZTMzZWM3N2M1NTcyZDcwYzQ2OWFkMjkwMzgyMjI4NTIxMjEzNWU3Nzc1MWE5YzIxNjAyOTJiOA==; baikeVisitId=13bee4af-f600-4bc9-a6c5-87d5720cee4a'
    }
)
docs = loader.load()

# 创建主文档分割器
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)

# 创建子文档分割器
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

# 创建向量数据库对象
vectorstore = Chroma(
    collection_name="split_parents", embedding_function=bge_embeddings
)
# 创建内存存储对象
store = InMemoryStore()
# 创建父文档检索器
retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
    verbose=True,
    search_kwargs={"k": 2}
)

# 添加文档集
retriever.add_documents(docs)

chat = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# 创建prompt模板
template = """你是负责回答问题的助手。使用以下检索到的上下文片段来回答问题。
如果你不知道答案，就说你不知道。最多用两句话，回答要简明扼要。
Question: {question}
Context: {context}
Answer:
"""

# 由模板生成prompt
prompt = ChatPromptTemplate.from_template(template)

# 创建chain
chain = RunnableMap({
    "context": lambda x: retriever.invoke(x["question"]),
    "question": lambda x: x["question"]
}) | prompt | chat | StrOutputParser()

from datasets import Dataset

# 问题
questions = ["恐龙是怎么被命名的？",
             "恐龙怎么分类的？",
             "体型最大的是哪种恐龙?",
             "体型最长的是哪种恐龙？它在哪里被发现？",
             "恐龙采样什么样的方式繁殖？",
             "恐龙是冷血动物吗？",
             "陨石撞击是导致恐龙灭绝的原因吗？",
             "恐龙是在什么时候灭绝的？",
             "鳄鱼是恐龙的近亲吗？",
             "恐龙在英语中叫什么？"
             ]
# 真实答案
ground_truths = [
    "1841年，英国科学家理查德·欧文在研究几块样子像蜥蜴骨头化石时，认为它们是某种史前动物留下来的，并命名为恐龙，意思是“恐怖的蜥蜴”。",
    "恐龙可分为鸟类和非鸟恐龙。",
    "恐龙整体而言的体型很大。以恐龙作为标准来看，蜥脚下目是其中的巨无霸。",
    "最长的恐龙是27米长的梁龙，是在1907年发现于美国怀俄明州。",
    "恐龙采样产卵、孵蛋的方式繁殖。",
    "恐龙是介于冷血和温血之间的动物",
    "科学家最新研究显示，0.65亿年前小行星碰撞地球时间或早或晚都可能不会导致恐龙灭绝，真实灭绝原因是当时恐龙处于较脆弱的生态系统中，环境剧变易导致灭绝。",
    "恐龙灭绝的时间是在距今约6500万年前，地质年代为中生代白垩纪末或新生代第三纪初。",
    "鳄鱼是另一群恐龙的现代近亲，但两者关系较非鸟恐龙与鸟类远。",
    "1842年，英国古生物学家理查德·欧文创建了“dinosaur”这一名词。英文的dinosaur来自希腊文deinos（恐怖的）Saurosc（蜥蜴或爬行动物）。"

]
# 模型回答
answers = []
# 文档内容
contexts = []

# 把检索到的内容和回答的问题进行存储
for query in questions:
    answers.append(chain.invoke({"question": query}))
    contexts.append([docs.page_content for docs in retriever.invoke(query)])
print("question", questions)
print("answer", answers)
print("contexts", contexts)
print("ground_truth", ground_truths)
# 转换成字典
data_samples = {
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths
}

# 字典转换为Dataset对象，便于高效处理数据并适配模型训练、评估等任务。
dataset = Dataset.from_dict(data_samples)

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,

)

# 进行评估
result = evaluate(
    dataset,
    metrics=[
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    ],
    llm=chat,
    embeddings=bge_embeddings
)
df = result.to_pandas()
print(df)
df.to_csv('ragas_reval.csv', index=True)
```
### 
### 五. 优化方式

| 评估维度 | 定义 | 优化目标 | 关键技术方案 |
| --- | --- | --- | --- |
| **精确度** (Context Precision) | 检索结果与问题的相关比例 | 提升TOP-K结果的精准性 | 1. 混合检索策略（向量+关键词+图） 2. 嵌入模型微调（领域适配） 3. 重排序模型 |
| **召回率** (Context Recall) | 关键信息是否被完整检索 | 覆盖核心证据文档 | 1. 多粒度分块（父子索引） 2. 多条检索 |
| **忠诚度** (Faithfulness) | 生成答案与检索内容一致性 | 消除幻觉/矛盾 | 1. 尽量避免噪声数据 2. 模型调试 3. 提示词合理 |
| **答案相关性** (Answer Relevance) | 回答与问题匹配度 | 提升语义匹配完整性 | 1. 指令微调 2. 拒绝回答机制 3. 偏好优化 |

### 六. RAG应用平台
- 工作流平台的核心作用是**通过自动化、标准化和可视化手段，简化复杂任务的编排与管理**，从而提升效率、降低协作成本，并确保流程的可控性,对比四个知名平台：Dify、FastGPT、RagFlow和QAnything，以帮助用户理解它们的功能、优势和适用场景。
- 优缺点:

| **维度** | **RAG开发** | **RAG工作流平台** |
| --- | --- | --- |
| 开发速度 | ❌ 慢（需全链路实现） | ✅ 快（开箱即用） |
| 定制化能力 | ✅ 高（完全自主控制） | ❌ 低（受限于平台功能） |
| 工程复杂度 | ❌ 高（需处理部署、监控等） | ✅ 低（平台自动化管理） |
| 维护成本 | ❌ 高（需持续优化底层） | ✅ 低（平台负责升级） |
| **性能调优能力** | ✅ 强（可针对硬件/场景深度优化） | ❌ 弱（受限于平台默认配置） |
| **数据隐私控制** | ✅ 完全自主（本地化部署，无数据外流） | ❌ 受限（依赖平台数据托管策略） |
| 适用场景 | 超大规模、高定制化需求（如企业级知识库） | 中小规模、快速验证需求（如MVP或PoC） |

### 1. QAnything
- QAnything(Question 和 Answer based on Anything）是网易一个开源的本地知识库RAG问答系统，支持用户上传多种格式的文档，以构建知识库，并采用**两阶段检索**机制及**混合检索**技术，提升检索效率和准确性。

![[1769758889500-03489345-15f2-465a-b6f5-e0690077a438.png]]
- 与常规的 RAG 流程图相比，明显更加突出了 `Rerank` 环节，将 `Rerank` 作为 `2nd Retrieval` 进行强调，看起来这是有道对 RAG 的独到理解。
- 另外 [QAnything 官方文档](https://github.com/netease-youdao/QAnything/tree/master?tab=readme-ov-file#rag-evaluations-in-llamaindexembedding-and-rerank) 中也强调，QAnything 使用的向量检索模型 `bce-embedding-base_v1` 向量排序模型 `bce-reranker-base_v1` 组合才是 SOTA。同样也印证了架构图， `Rerank` 是 QAnything 是相当重要的模块。
- 源码地址：[https://github.com/netease-youdao/QAnything/](https://github.com/netease-youdao/QAnything/)
- 官方网址：[https://qanything.ai/](https://qanything.ai/)

### 2. RagFlow
- RAGFlow 是一个基于对文档的深入理解的开源 RAG（检索增强生成）引擎。当与大语言模型集成时，它能凭借引用知识库中各种复杂格式的数据为后盾，为用户提供真实可信，少幻觉的答案。RAGFlow的技术原理涵盖了文档理解、检索增强、生成模型、注意力机制等，特别强调了深度文档理解技术，能够从复杂格式的非结构化数据中提取关键信息。

![[1769758889569-c1918b7d-ab13-417c-ae0c-6226bd1b2dd3.png]]
- 可以看到右侧知识库被明显放大，同时最右侧详细介绍了文件解析的各种手段，比如 OCR， Document Layout Analyze 等，这些在常规的 RAG 中可能会作为一个不起眼的 Unstructured Loader 包含进去，可以猜到 RagFlow 的一个核心能力在于文件的解析环节。
- 在 [官方文档](https://github.com/infiniflow/ragflow?tab=readme-ov-file#-key-features) 中也反复强调 Quality in, quality out, 反映出 RAGFlow 的独到之处在于细粒度文档解析。
- 另外 [介绍文章](https://www.aigcopen.com/content/corporate_news/23689.html) 中提到其没有使用任何 RAG 中间件，而是完全重新研发了一套智能文档理解系统，并以此为依托构建 RAG 任务编排体系，也可以理解文档的解析是其 RagFlow 的核心亮点。
- 源码地址：[https://github.com/infiniflow/ragflow](https://github.com/infiniflow/ragflow)
- 官方网址：[https://ragflow.io/](https://ragflow.io/)

### 3. FastGPT
- FastGPT是一款基于LLM（Large Language Model）大语言模型的知识库问答系统。它提供了数据处理、模型调用、RAG（Retriever-Augmented Generation）检索、可视化AI工作流编排等能力，使用户能够轻松构建复杂的AI应用。FastGPT不仅支持多轮对话，还能处理实时信息和企业内部资料，极大地提高了AI应用的实用性和效率。
- 与常规的 RAG 相比增加了额外工作流编排的能力，这部分类似 Dify。但是相对 Dify 而言可调用的第三方应用更少一些。按照习惯先查看项目的架构图：

![[1769758889658-347e5b58-6d6a-44c5-a87c-b7cc0bf30600.png]]
对于常规的 RAG 架构图，这张图可以明显看到大模型模块被放大，而且文件入库的流程都会先调用大模型。从大模型的输出来看，存在 QA 拆分，文本分段和手动输入三种情况：
- 文本分段是常规的 RAG 的处理方案
- QA 拆分看起来是基于原始文本生成问答对，这部分猜测应该是根据大模型生成问答对，之前 Dify 也有类似的功能，被称为 Q&A 模式
- 手动输入则是直接输入问答对，这部分应该是手工输入数据进行补充

预计文件入库环节的大模型调用主要作用于 QA 拆分。
源码地址：[https://github.com/labring/FastGPT](https://github.com/labring/FastGPT)
官方网址：[https://tryfastgpt.ai/](https://tryfastgpt.ai/)
### 七.Dify使用
### 1. 简介
- Dify是一个流行的开源大模型应用开发平台，内置了构建 LLM 应用所需的关键技术栈，包括对数百个模型的支持、直观的 Prompt 编排界面、高质量的 RAG 引擎、稳健的 Agent 框架、灵活的流程编排，并同时提供了一套易用的界面和 API。这为开发者节省了许多重复造轮子的时间，使其可以专注在创新和业务需求上。
- 基于 Dify 可以在不需要太多开发的情况下，快速搭建一个大模型应用。应用中可以调用 Dify 中内置的大量基础能力，比如知识库检索 RAG，大模型调用。通过可插拔式的组合构建大模型应用。一个典型的应用如下所示：

![[1769758889740-30ccc499-70ec-4c74-810d-147fbb20ae55.png]]
- Dify源码地址：[https://github.com/langgenius/dify](https://link.zhihu.com/?target=https%3A%2F%2Fgithub.com%2Flanggenius%2Fdify)
- 中文文档：[https://docs.dify.ai/v/zh-hans](https://link.zhihu.com/?target=https%3A%2F%2Fdocs.dify.ai%2Fv%2Fzh-hans)
- 官方地址: [https://cloud.dify.ai/apps](https://cloud.dify.ai/apps)

### 2. 界面介绍
- 探索界面: dify提供的模版大家可以参考使用

![[1769758889807-4428f974-ae2c-4c51-9b64-ab8e567e6405.png]]
- 工作室: 我们自己创建的任务就在工作室当中

![[1769758889871-b2678844-017d-44db-b068-873fd30f9b47.png]]
- 知识库: dify处理自己文档的地方

![[1769758889969-99bef38a-3cd2-4031-80f0-ae88b36cc012.png]]
- 工具: 提供agent工具,可以自定义也可以市场下载

![[1769758890030-c87adf9c-8c7d-4f08-bb5b-10ff6272ce3e.png]]
### 3. 新手适用
### 1. 模型设置
- 安装好对应的模型供应商,配置对应的`apikey`

![[1769758890104-9200cfef-046d-4377-94be-a10f7d40274f.png]]
- 配置好之后点击工作室,点击创建空白应用

### 2. 聊天助手
- 聊天助手主要是让你快速创建一个可以和用户进行智能自然语言对话的机器人应用，支持多轮对话、上下文理解、知识接入、发布为服务等功能

![[1769758890170-90d34a64-89b1-4a98-8353-f75be9babf37.png]]
- 页面功能介绍

![[1769758890280-59043838-3ce2-4a3c-9ec7-68aceaeb55bb.png]]
- 单次日志输出

![[1769758890376-57bd1905-96be-4ac5-91ce-b26c54908501.png]]
- 翻译提示词

```plain text
你是一个专业的翻译助手，根据用户输入的内容进行翻译
用户输入的语言的类型: {{source_language}}
需要翻译的目标语言: {{target_language}}
```
### 3. 文本生成
- Dify 的文本生成，本质就是把 AI 变成一个“稳定、可复用、自动化的写作能力模块”。
- 可以被反复执行很多次，但每一次都是“全新的一次”，没有记忆。

![[1769758890493-afd228b0-3062-4a69-917e-0364870147a0.png]]
- 运行之后的日志内容会有区别之前是系统提示词,现在是用户提示词
- 提示词

```plain text
提供多种代码语言转换能力，将用户输入的代码转换成他们需要的代码语言。
请将以下代码片段转为{{Target_code}}:
当用户输入的信息是非代码片段时，提示：请正确输入代码片段。
只需要转换之后的代码不需过多的解释
{{default_input}}
```
- 如果你使用的是中文的显示名称会有编码冲突的问题可以自己用代码做批量,不使用平台提供的模版

```plain text
import csv

with open('input.csv', 'a', encoding='utf-8', newline='') as f:
    aa = csv.writer(f)
    aa.writerow(['目标语言', '翻译的代码'])
    aa.writerow(['java', 'print("hello world")'])
    aa.writerow(['JavaScript', 'print("hello world")'])
```
### 4. agent
- 本地工具使用

![[1769758890554-e43a58fe-79ea-4166-94d4-e5bf8fed9f57.png]]
- 通过工具直接调用
- 工具下载

![[1769758890680-d6d5790a-a805-4e4b-ab9c-119936f29b7d.png]]
![[1769758890753-61935fb4-d70e-4fa8-8854-8fcdc124a733.png]]
### 5. 知识库使用
- 创建空白知识库

![[1769758890819-314ac066-fc0d-4dc1-9ae2-7de15bf73a7e.png]]
- 可以自己选检索方式,切片规则

![[1769758890914-b0f75d1d-0601-41e7-b8fa-868f37d453ce.png]]
### 4. 工作流
- 用户只需要输入,按照固定的流程进行输出,有点类似与售货机(投币 → 按按钮 → 出货 )
- 高阶的使用页面可以进行自主编排
- 工作流触发方式有两种,一种是用户自己触发,一个是按照规则触发

![[1769758891041-1f748229-0d9b-46a4-a4c8-8c2a42d8a58f.png]]
### 1. AI热点收集案例
- 流程分析
- 网址: [AI最新资讯_人工智能新闻头条_AI行业动态 | AIBase](https://news.aibase.com/zh/news)
- 获取网址内容,让大模型提取”最新AI日报” 当中的链接地址和标题返回列表数据
- 通过迭代进行循环,在对详情页面发送请求,通过大模型获取需要的内容
- 输出内容

![[1769758891151-8b715d90-997a-4f64-9088-bd7a9b5128d5.png]]
- 发送http请求可以直接抓包复制curl

![[1769758891210-e23cac44-071e-463c-92d3-4c630854ec9a.png]]
- 大模型提取内容

![[1769758891293-f7d1e697-fc5e-406f-8964-d40af2328672.png]]
- 提示词内容
- 结构化输出内容

```plain text
# 系统提示词
你是专业的提取数据专家
用户会传递给你html内容,解析出正确的内容

# 用户提示词
从{{#1767515008721.body#}}中提取最新的AI日报信息，以JSON格式返回。

提取要求：
1. 仅提取AI日报相关内容
2. 最多返回10篇最新的日报
3. 如果内容中包含发布日期，请一并提取

返回格式：
{
  "ai_reports": [
    {
      "title": "日报标题",
      "url": "详情页面完整URL",
      "date": "发布日期(如有)"
    },
    ...
  ]
}

处理说明：
- 确保URL是完整的，如缺少域名请补全
- 按发布时间从新到旧排序
- 如果原始数据格式有问题，请尝试修复后再提取
```
- 迭代节点

![[1769758891437-9ef0d65c-7e16-4870-9fa9-ec3672f870e2.png]]
- 对详情页面发送请求

![[1769758891578-c60de207-9590-45dc-817c-32b8e6e1fe6b.png]]
- 通过大模型提取数据内容

```plain text
# 系统提示词
作为文档提取与总结专家，请分析用户提供的HTML内容并执行以下任务：

1. 提取关键数据：
   - 标题、作者、发布日期
   - 主要段落内容
   - 列表项和表格数据
   - 嵌入的媒体链接

2. 结构化总结（500-800字）：
   - 核心主题和要点（3-5点）
   - 主要论点和支持证据
   - 数据和统计信息的解释
   - 文档的目的和目标受众

3. 数据可视化建议：
   - 指出哪些数据适合图表展示
   - 建议合适的可视化类型

输出格式：
- 使用清晰的标题和分节符号
- 对关键术语和概念进行加粗标记
- 如有表格数据，使用markdown表格格式呈现
- 在总结末尾提供3-5个关键词标签

如果HTML内容存在特定领域术语或专业知识，请一并解释这些术语。

请确保提取的信息准确反映原始内容，不添加未在文档中出现的信息，并保持原文的核心观点和立场。



# 用户提示词
作为文档提取与总结专家，请执行以下任务：

1. 从提供的HTML数据{{#1767515579213.body#}}中的文章内容。

2. 原文内容不需要标签内容只需要纯文本

3. 对提取的内容生成一个结构化总结（400-600字），包括：
   - 文章的主要主题和目的
   - 3-5个核心观点或要点
   - 重要数据或发现（如适用）
   - 结论或建议（如适用）

4. 如果文章包含专业术语或技术概念，请在总结后提供简短解释。

输出格式：
标题:
{{#1767515529032.title#}}
提取的原文内容
[此处呈现提取的原始内容]

内容总结
[此处呈现您的总结]

关键词
[3-5个代表文章核心内容的关键词]
```
### 5. 各个节点使用
### 1. llm节点
- 节点文档查询
- 选择模型
- 检索上下文内容
- 提示词

![[1773842871048-6318f5d0-8e64-4d94-83cb-21adcf70213f.png]]
### 2. 知识检索
- 检索关键字
- 检索知识库

![[1773842890340-4821e56a-376e-4aac-ae8c-fe3d43c47f24.png]]
### 3. agent
- agent策略: agent调用方法
- 模型: 使用的大模型
- 工具:提供给agent使用的工具
- 指令:系统提示词
- 查询:用户提示词

![[1773843040945-1b18bbec-ad30-40a3-b1c8-f4a3fb73313f.png]]
### 4. 问题分类器
- 根据用户输入的问题/意图，自动判断它属于哪一类，然后把流程引导到不同的分支去处理
- 分类:你在节点里定义几个类别，每个类别写一段描述/示例

```plain text
描述：用户在询问公司产品、功能、使用方法、价格、规则、文档内容、帮助中心相关问题。典型词：怎么用、是什么、价格多少、有没有、支持不支持、教程、手册

描述：用户打招呼、聊天、开玩笑、表达情绪、闲扯、不涉及任何具体业务或知识的问题。典型词：你好、哈哈、好无聊、今天天气、你真可爱
```
![[1773843061216-eb4de760-91fa-4230-bf9f-bc731771d406.png]]
### 5. 条件分支
- 它让工作流从“一条直线”变成“多条可选路径”，根据实时变量的值自动决定走哪条路

![[1773843071377-fc6b336c-ccc2-4856-a2d4-822408d7dfe2.png]]
### 6. 人工介入
- 是 Dify 在 v1.13.0正式引入的一个的节点
- 提交方式:当前需要人工选择的提交地址
- webapp: WebApp 界面
- 邮件:发一封邮件，里面带链接
- 表单内容:
- 显示给人工看的信息
- 让人工手动输入的字段
    - ctrl + /
- 用户操作:给出按钮让用户选择,每个选择走不同的逻辑

![[1773843088845-614f23f3-15bc-4fe2-ba7f-ce317aacb6a9.png]]
### 7. 循环节点&变量赋值
- 迭代节点：针对按元素个数执行，核心是 “挨个处理”
- 循环节点：针对「条件判断」，按条件是否满足执行，核心是 “重复直到达标”；
- 输入节点

![[1773843101808-457bc46f-d5d7-47cd-8908-f3766508c070.png]]
- 循环节点

![[1773843120585-c26c312a-1b30-4445-81fb-3a0d574e5155.png]]
- 代码节点

![[1773843130335-d2a64ab6-061c-4a7c-b3c3-046061832b18.png]]
- 变量赋值节点
- 把参数进行赋值

![[1773843148895-c839c367-dcd8-4907-af7e-4d1b40e5f9e7.png]]
### 8. 模版转换
- 用 Jinja2 模板引擎，把上游传过来的各种数据（字符串、列表、JSON 对象、知识检索结果等）按照你定义的格式，灵活地转换成一个新的文本
- 和我们自己写的提示词有点像

![[1773843162444-dab487fa-1186-4f5e-a838-6d0e9b53925f.png]]
### 9. 变量聚合器
- 把多个互斥分支（或并行但最终只走一条路的分支）产生的“同类变量”合并/统一成一个变量
- 没使用集合器
- 每个内容都需要单独回复

![[1773843174536-a243531e-f5dd-4382-80aa-d141516a7382.png]]
- 使用了聚合器

![[1773843185532-8ee657a4-6f69-447c-acaf-f44798015a9d.png]]
### 10. 参数提取器
- 用 LLM 的理解和结构化输出能力，从一段非结构化的文本（用户输入、LLM 回复、邮件内容等）中，按照你定义的字段规则，智能提取出结构化的参数（JSON 格式），直接供下游工具、HTTP 请求、迭代节点等使用

![[1773843204390-67d0c1a2-742e-4cf9-91ca-b19339958e41.png]]
### 6. ChatFlow
- 和工作流相对提供了多轮对话功能,实现记忆功能类似柜台客服(接受用户的问题->给出回答->用户在根据问题提问)
- 使用方法和工作流一模一样