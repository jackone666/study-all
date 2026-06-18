---
notion-id: 338a95f7-5835-8109-a469-cd0d014a87e7
---
## Advanced RAG

### 一. Advanced RAG概述
Advanced RAG重点聚焦在检索增强，即优化Retrieval阶段。增加了Pre-Retrieval预检索和Post-Retrieval后检索阶段。
![[1769758882379-830e8ec1-4cf5-4ddd-81c9-fd05318aef6a.png]]
基于朴素RAG，高级RAG主要通过预检索策略和后检索策略来提升检索质量。
**预检索过程**
高级RAG着重优化了索引结构和查询的方式。优化索引旨在提高被索引内容的质量，包括增强数据颗粒度、优化索引结构、添加元数据、对齐优化和混合检索等策略。查询优化的目标则是明确用户的原始问题，使其更适合检索任务，使用了**查询重写、查询转换、查询扩展**等技术。
**后检索过程**
对于由问题检索得到的一系列上下文，后检索策略关注如何优化它们与查询问题的集成。这一过程主要包括**重新排序和压缩上下文**。重新排列检索到的信息，将最相关的内容予以定位标记，这种策略已经在LlamaIndex2、LangChain等框架中得以实施。直接将所有相关文档输入到大型语言模型（LLMs）可能导致信息过载，为了缓解这一点，后检索工作集中选择必要的信息，强调关键部分，并限制了了相应的上下文长度。
### 二. Pre-Retrieval预检索-优化索引
### 1. 摘要索引
### 1.1 痛点分析
在处理大量文档时，如何快速准确地找到所需信息是一个常见挑战。摘要索引可以用来处理半结构化数据，比如许多文档包含多种内容类型，包括文本和表格。这种半结构化数据对于传统 RAG 来说可能具有挑战性，文本拆分可能会分解表，从而损坏检索中的数据；嵌入表可能会给语义相似性搜索带来挑战。
![[1769758882473-b0ab3455-a2b5-4d41-ae7a-b0b1cd7b7539.png]]
### 1.2 **解决思路:**
- 让LLM为每个块生成summary，并作为embedding存到summary database中
- 在检索时，通过summary database找到最相关的summary，再回溯到原始文档中去
- 将原始文本块作为上下文发送给LLM以获取答案

### 1.3 **整体代码**
```python
from langchain_core.stores import InMemoryByteStore
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from langchain_classic.retrievers import MultiVectorRetriever
import uuid
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# 本地embedding模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'

url = "https://news.pku.edu.cn/mtbdnew/15ac0b3e79244efa88b03a570cbcbcaa.htm"
# 初始化文档加载器列表（加载多个文本文件）
loaders = [
    UnstructuredWordDocumentLoader("人事管理流程.docx"),
    WebBaseLoader(url)
]

# 加载并合并所有文档
docs = []
for loader in loaders:
    docs.extend(loader.load())
# print(docs)
# 初始化递归文本分割器（设置块大小和重叠）
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
docs = text_splitter.split_documents(docs)
# print(docs)

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# 创建摘要生成链
chain = (
        {"doc": lambda x: x.page_content}
        | ChatPromptTemplate.from_template("总结下面的文档:\n\n{doc}")
        | llm
        | StrOutputParser()
)

# 批量生成文档摘要（最大并发数5）
summaries = chain.batch(docs, {"max_concurrency": 5})
# print(summaries)

# 初始化嵌入模型（用于文本向量化）
embeddings_model = HuggingFaceEmbeddings(
    model_name=embedding_model_path
)
# 初始化Chroma实例（用于存储摘要向量）
vectorstore = Chroma(
    collection_name="summaries",
    embedding_function=embeddings_model
)

# 初始化内存字节存储（用于存储原始文档）
store = InMemoryByteStore()


# 初始化多向量检索器（结合向量存储和文档存储）
id_key = "doc_id"
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    byte_store=store,
    id_key=id_key,
)

# 为每个文档生成唯一ID
doc_ids = [str(uuid.uuid4()) for _ in docs]

# 创建摘要文档列表（包含元数据） metadata可以用来关联原始文档和摘要文档会自动找到匹配关系
summary_docs = [
    Document(page_content=s, metadata={id_key: doc_ids[i]}) for i, s in enumerate(summaries)
]

# 将摘要添加到向量数据库
retriever.vectorstore.add_documents(summary_docs)

# 将原始文档存储到字节存储（使用ID关联）
retriever.docstore.mset(list(zip(doc_ids, docs)))


# 执行相似性搜索测试
sub_docs = retriever.vectorstore.similarity_search("病假的请假流程?")
print("-------------匹配的摘要内容--------------")
print(sub_docs[0])

# 获取第一个匹配摘要的ID
matched_id = sub_docs[0].metadata[id_key]

# 通过ID获取原始文档
original_doc = retriever.docstore.mget([matched_id])
print("-------------对应的原始文档--------------")
print(original_doc)


prompt = ChatPromptTemplate.from_template("根据下面的文档回答问题:\n\n{doc}\n\n问题: {question}")
# 生成问题回答链
chain = RunnableMap({
    "doc": lambda x: retriever.invoke(x["question"]),
    "question": lambda x: x["question"]
}) | prompt | llm | StrOutputParser()

# 生成问题回答
query = "病假的请假流程?"
answer = chain.invoke({"question": query})
print("-------------回答--------------")
print(answer)

retrieved_docs = retriever.invoke(query)
print("-------------检索到的文档--------------")
print(retrieved_docs)
```
### 2. 父子索引
### 2.1 痛点分析
我们在利用大模型进行文档检索的时候，常常会有相互矛盾的需求，比如：
1. 你可能希望得到较小的文档块，以便它们Embedding以后能够最准确地反映出文档的含义，如果文档块太大，Embedding就失去了意义。
2. 你可能希望得到较大的文档块以保留较多的内容，然后将它们发送给LLM以便得到全面且正确的答案。

![[1769758882539-cdf17b74-2138-42ef-a0df-df39845c1f86.png]]
### 2.2 **解决思路:**
父文档检索重点解决这种问题，基本思路：
- 文档被分割成一个层级化的块结构，随后用最小的叶子块进行索引
- 在检索过程中检索出top k个叶子块
- 如果存在n个叶子块都指向同一个更大的父块，那么我们就用这个父块来替换这些子块，并将其送入大模型用于生成答案。

### 2.3 完整代码
```plain text
from langchain_community.document_loaders import WebBaseLoader
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.retrievers import ParentDocumentRetriever
from langchain_core.stores import BaseStore, InMemoryByteStore
from langchain_core.documents import Document
import pymysql
import json
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# 自定义 MySQL Store
class MySQLStore(BaseStore):
    def __init__(self, host, user, password, database):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        self._create_table()

    def _create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id VARCHAR(255) PRIMARY KEY,
                    page_content TEXT,
                    metadata JSON
                )
            """)
            self.connection.commit()

    def mset(self, key_value_pairs):
        with self.connection.cursor() as cursor:
            for key, doc in key_value_pairs:
                metadata = json.dumps(doc.metadata) if doc.metadata else "{}"
                cursor.execute("""
                    INSERT INTO documents (doc_id, page_content, metadata)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE page_content=%s, metadata=%s
                """, (key, doc.page_content, metadata, doc.page_content, metadata))
            self.connection.commit()

    def mget(self, keys):
        with self.connection.cursor() as cursor:
            if not keys:
                return []
            placeholders = ", ".join(["%s"] * len(keys))
            cursor.execute(f"SELECT doc_id, page_content, metadata FROM documents WHERE doc_id IN ({placeholders})", keys)
            results = cursor.fetchall()
            return [Document(page_content=row["page_content"], metadata=json.loads(row["metadata"]) if row["metadata"] else {}) for row in results]

    def mdelete(self, keys):
        with self.connection.cursor() as cursor:
            if not keys:
                return
            placeholders = ", ".join(["%s"] * len(keys))
            cursor.execute(f"DELETE FROM documents WHERE doc_id IN ({placeholders})", keys)
            self.connection.commit()

    def yield_keys(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT doc_id FROM documents")
            for row in cursor.fetchall():
                yield row["doc_id"]

    def close(self):
        self.connection.close()

# 本地 embedding 模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'

# 目标 URL
url = "https://news.pku.edu.cn/mtbdnew/15ac0b3e79244efa88b03a570cbcbcaa.htm"

# 加载网页
loader = WebBaseLoader(url)
docs = loader.load()

# 创建主文档分割器
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)

# 创建子文档分割器
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

# 初始化嵌入模型
embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_path)

# 创建向量数据库对象
vectorstore = Chroma(collection_name="split_parents", embedding_function=embeddings_model)

# 创建 MySQL 存储对象
store = MySQLStore(host="localhost", user="root", password="root", database="langchain_db")

# 初始化内存字节存储（用于存储原始文档）
# store = InMemoryByteStore()

# 创建父文档检索器
retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
    search_kwargs={"k": 1}
)

# 添加文档集
retriever.add_documents(docs)

print(f"存储的父文档数量: {len(list(store.yield_keys()))}")

print("------------similarity_search------------------------")
# 在向量数据库中搜索子文档
sub_docs = vectorstore.similarity_search("天才AI少女是谁？")
print(sub_docs)

print("------------get_relevant_documents------------------------")
# 过程 retriever.invoke 先检索子文档，根据子文档的元数据找到父文档
retrieved_docs = retriever.invoke("天才AI少女是谁？")
print(retrieved_docs[0].page_content)

# 创建模型
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# 创建 prompt 模板
template = """请根据下面给出的上下文来回答问题:
{context}
问题: {question}
"""

# 由模板生成 prompt
prompt = ChatPromptTemplate.from_template(template)

# 创建 chain
chain = RunnableMap({
    "context": lambda x: retriever.invoke(x["question"]),
    "question": lambda x: x["question"]
}) | prompt | llm | StrOutputParser()

print("------------模型回复------------------------")

response = chain.invoke({"question": "天才AI少女是谁？"})
print(response)

# 关闭 MySQL 连接
store.close()
```
### 3. 假设性问题索引
### 3.1 问题解决
假设性问题是一种提问方式，它基于一个或多个假设的情况或前提来提出问题。在对知识库中文档内容进行切片时，是可以以该切片为假设条件，利用LLM预先设置几个候选的相关性问题的，也就是说，这几个候选的相关性问题是和切片的内容强相关的。 (先把文档对应的问题和答案预设好,问题存向量,答案存文档)
### 3.2 **解决思路:**
- 让LLM为每个块生成3个假设性问题，并将这些问题以向量形式嵌入
- 在运行时，针对这个问题向量的索引进行查询搜索（用问题向量替换文档的块向量）
- 检索后将原始文本块作为上下文发送给LLM以获取答案

### 3.3 完整代码
```plain text
from typing import List
from langchain_core.stores import InMemoryByteStore
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from langchain_classic.retrievers import MultiVectorRetriever
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field
import uuid
import os
from dotenv import load_dotenv

load_dotenv()


# 本地embedding模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
# 初始化嵌入模型（用于文本向量化）
embeddings_model = HuggingFaceEmbeddings(
    model_name=embedding_model_path
)

# 初始化文档加载器列表
loader = TextLoader("deepseek介绍.txt", encoding="utf-8")
docs = loader.load()

# 初始化递归文本分割器（设置块大小和重叠）
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
docs = text_splitter.split_documents(docs)

# 初始化llm
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)


class HypotheticalQuestions(BaseModel):
    """生成假设性问题"""
    # Field  ... 必传字段  问题必须是列表  对接受的数据进行效验限制
    questions: List[str] = Field(..., description="List of questions")


prompt = ChatPromptTemplate.from_template(
    """请基于以下文档生成3个假设性问题（必须使用JSON格式）:
    {doc}

    要求：
1. 输出必须为合法JSON格式，包含questions字段
2. questions字段的值是包含3个问题的数组
3. 使用中文提问
    示例格式：
    {{
    "questions": ["问题1", "问题2", "问题3"]
    }}"""
)

# 创建假设性问题链
chain = (
        {"doc": lambda x: x.page_content}
        | prompt
        # 将LLM输出构建为字符串列表
        | llm.with_structured_output(HypotheticalQuestions)
        # 提取问题列表
        | (lambda x: x.questions)
)
# 在单个文档上调用链输出问题列表：
# print(chain.invoke(docs[0]))


# 批量处理所有文档生成假设性问题（最大并行数5）
hypothetical_questions = chain.batch(docs, {"max_concurrency": 5})
print(hypothetical_questions)

# 初始化Chroma向量数据库（存储生成的问题向量）
vectorstore = Chroma(
    collection_name="hypo-questions", embedding_function=embeddings_model
)
# 初始化内存存储（存储原始文档）
store = InMemoryByteStore()

id_key = "doc_id"  # 文档标识键名

# 配置多向量检索器
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    byte_store=store,
    id_key=id_key,
)

# 为每个原始文档生成唯一ID
doc_ids = [str(uuid.uuid4()) for _ in docs]

# 将生成的问题转换为带元数据的文档对象
question_docs = []
for (i, question_list) in enumerate(hypothetical_questions):
    question_docs.extend(
        [Document(page_content=s, metadata={id_key: doc_ids[i]}) for s in question_list]
    )

retriever.vectorstore.add_documents(question_docs)  # 将问题文档存入向量数据库
retriever.docstore.mset(list(zip(doc_ids, docs)))  # 将原始文档存入字节存储（通过ID关联）

# 执行相似性搜索测试
query = "deepseek受到哪些攻击？"
sub_docs = retriever.vectorstore.similarity_search(query)
print(sub_docs)


prompt1 = ChatPromptTemplate.from_template("根据下面的文档回答问题:\n\n{doc}\n\n问题: {question}")

# 生成问题回答链
chain = RunnableMap({
    "doc": lambda x: retriever.invoke(x["question"]),
    "question": lambda x: x["question"]
}) | prompt1 | llm | StrOutputParser()

# 生成问题回答
answer = chain.invoke({"question": query})
print("-------------回答--------------")
print(answer)
```
### 4. 元数据索引
### 4.1 痛点分析
对于大量的文档仅仅依赖语义相似性有时是不够的。想象一下，你想在一个医学文献数据库中查找关于“糖尿病足”的资料，但数据库中也充斥着大量关于其他糖尿病并发症的信息。仅仅依靠向量相似性，可能会检索出许多与你的目标并不完全相关的文档。
![[1769758882618-8194418f-a4b5-4aea-8bdc-40b849cb72a2.png]]
![[1769758882695-ddc2511a-e61e-4251-a116-a2a5d9d3eafa.png]]
### 4.2 **解决思路:**
- 存入数据之前先给数据打上标签(作者,时间等一些标签), 有点类似摘要区别在于摘要是总结,元数据是存字段
- 元数据是对文档的一种属性描述，假设我们使用一个存储了大量科技博客文章的向量数据库。每篇文章都关联了以下标签：

```plain text
  topic: 人工智能, 区块链, 云计算, 大数据
  author: 作者A, 作者B, 作者C
  year: 2022, 2023, 2024
```
- 我们就可以通过标签先对文档进行过滤，然后再进行相似性检索

⚠️ 经测试英文的元数据要比中文检测的结果要准确
- 在 langchain 中使用`SelfQueryRetriever`自查询检索器实现，具体思路：
- 给定任何自然语言查询，检索器使用查询构造LLM链编写结构化查询，然后将该结构化查询应用于其底层[向量存储](https://python.langchain.com/docs/concepts/vectorstores/)。这允许检索器不仅使用用户输入查询与存储文档的内容进行语义相似性比较，还可以从用户对存储文档元数据的查询中提取过滤器并执行这些过滤器。

### 4.3 完整代码
```plain text
from langchain_chroma import Chroma
from 元数据文档 import docs, metadata_field_info
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()


# 本地embedding模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
# 初始化嵌入模型（用于文本向量化）
embeddings_model = HuggingFaceEmbeddings(
    model_name=embedding_model_path
)

# 文档内容描述（指导LLM理解文档内容）
document_content_description = "Brief description of technical articles"

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)
# 创建向量数据库
vectorstore = Chroma.from_documents(docs, embeddings_model)

# 创建自查询检索器（核心组件）
"""
SelfQueryRetriever.from_llm解析步骤:
1. 用户的问题("2023年评分超过8分的机器学习论文")
    LLM 任务(会由底层源码自己实现)：
    识别用户意图中的显式条件（如“2023年”对应 year=2023）。
    提取隐式语义关键词（如“机器学习论文”作为向量搜索关键词）。
    将模糊表述转换为结构化操作符（如“超过8分” → {"$gt": 8}）。
    {
        "query": "机器学习论文",
        "filter": {"year": 2023, "rating": {"$gt": 8}}
    }

2. 元数据过滤
    根据 filter 对向量数据库中的文档元数据进行筛选。(筛选出 year=2023 且 rating>8 的所有文档。)

3. 语义搜索
    在元数据过滤后的文档子集中，用 query 进行向量相似性搜索。

4. 结果合并与排序
    综合元数据匹配度（如完全匹配 year=2023）和语义相关性（向量得分），返回排序后的文档列表

"""
retriever = SelfQueryRetriever.from_llm(
    llm,
    vectorstore,
    document_content_description,
    metadata_field_info,
    # enable_limit 启用限制查询数量
    enable_limit=True
)


# print(retriever.invoke("作者B在2024年发布的文章"))
# 限定查询的数量需要设置enable_limit=True
print(retriever.invoke("我想了解一篇评分在9分以上的文章"))
```
- 元数据文档

```plain text
from langchain_core.documents import Document
from langchain_classic.chains.query_constructor.schema import AttributeInfo

docs = [
    Document(
        page_content="作者A团队开发出基于深度学习的图像识别系统，在复杂场景下的识别准确率提升250%",
        metadata={"year": 2025, "rating": 9.3, "genre": "AI", "author": "A"},
    ),
    Document(
        page_content="物联网技术成功应用于智能农业监控，作者B主导的项目实现农作物产量提升20%",
        metadata={"year": 2024, "rating": 9.5, "genre": "IoT", "author": "B"},
    ),
    Document(
        page_content="边缘计算平台实现实时数据处理突破，作者C构建的新型架构支持千万级并发计算",
        metadata={"year": 2023, "rating": 8.8, "genre": "Edge Computing", "author": "C"},
    ),
    Document(
        page_content="机器学习模型预测2025年股市趋势，作者A团队构建的模型准确率超95%",
        metadata={"year": 2024, "rating": 9.0, "genre": "Machine Learning", "author": "A"},
    ),
    Document(
        page_content="基于人工智能的心脏病诊断系统在临床应用中达到顶级专家水平，作者B获医疗科技创新奖",
        metadata={"year": 2025, "rating": 7.2, "genre": "AI", "author": "B"},
    ),
    Document(
        page_content="区块链技术在供应链管理中取得突破，作者C设计的新型协议提升供应链透明度30%",
        metadata={"year": 2024, "rating": 8.9, "genre": "Blockchain", "author": "C"},
    ),
    Document(
        page_content="云计算平台实现能效优化，作者A研发的智能调度系统使数据中心能耗降低50%",
        metadata={"year": 2024, "rating": 8.6, "genre": "Cloud", "author": "A"},
    ),
    Document(
        page_content="大数据分析助力环保监测，作者B团队实现污染源识别准确率提升30%",
        metadata={"year": 2025, "rating": 7.5, "genre": "Big Data", "author": "B"},
    )
]

# 元数据字段定义（指导LLM如何解析查询条件）
metadata_field_info = [
    AttributeInfo(
        name="genre",
        description="Technical domain of the article, options: ['AI', 'Blockchain', 'Cloud', 'Big Data']",
        type="string",
    ),
    AttributeInfo(
        name="year",
        description="Publication year of the article",
        type="integer",
    ),
    AttributeInfo(
        name="author",
        description="Author's name who signed the article",
        type="string",
    ),
    AttributeInfo(
        name="rating",
        description="Technical value assessment score (1-10 scale)",
        type="float"
    )
]
```
### 5. 混合检索
### 5.1 痛点分析
- 当用户的查询写的不准确，模棱两可时，比如接下来我们要演示的示例中，用户想问“关于deepseek的相关评价”，但是用户只输入“相关评价”，这个时候向量相似性检索可能检索不到相关的文档

### 5.2 **解决思路**:
- 将传统搜索算法（Best Matching 25, BM25）与向量相似性检索相结合，然后将检索结果融合，实现混合搜索，下面我们通过 langchain 实现混合检索的过程。
- 权重计算方式

![[1769758882789-4ba90dfa-dcf4-45f9-9c27-5ba741f8636f.png]]
### 5.3 完整代码
```plain text
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
# pip install rank_bm25
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings


import os
from dotenv import load_dotenv

load_dotenv()


# 本地embedding模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
# 初始化嵌入模型（用于文本向量化）
embeddings_model = HuggingFaceEmbeddings(
    model_name=embedding_model_path
)

# 加载文档
loader = TextLoader("deepseek介绍.txt", encoding="utf-8")
docs = loader.load()

# 分割文档
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
)
split_docs = text_splitter.split_documents(docs)

vectorstore = Chroma.from_documents(
    documents=split_docs, embedding=embeddings_model
)
question = "社会影响"

# 向量检索
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
vector_retriever_doc = vector_retriever.invoke(question)
print("-------------------向量检索-------------------------")
print(vector_retriever_doc)

# 关键词检索 BM25Retriever是一种经典的文本检索算法，广泛应用于搜索引擎和文档匹配任务,核心是通过统计词项频率和文档结构特征，计算查询与文档的相关性得分
BM25_retriever = BM25Retriever.from_documents(split_docs, k=3)
BM25Retriever_doc = BM25_retriever.invoke(question)
print("-------------------BM25检索-------------------------")
print(BM25Retriever_doc)


# 混合检索
retriever = EnsembleRetriever(retrievers=[BM25_retriever, vector_retriever], weights=[0.5, 0.5])
retriever_doc = retriever.invoke(question)
print("-------------------混合检索-------------------------")
print(retriever_doc)

# 创建llm
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# 创建prompt模板
template = """请根据下面给出的上下文来回答问题:
{context}
问题: {question}
"""

# 由模板生成prompt
prompt = ChatPromptTemplate.from_template(template)

# 创建chain
chain1 = RunnableMap({
    "context": lambda x: retriever.invoke(x["question"]),
    "question": lambda x: x["question"]
}) | prompt | llm | StrOutputParser()
chain2 = RunnableMap({
    "context": lambda x: vector_retriever.invoke(x["question"]),
    "question": lambda x: x["question"]
}) | prompt | llm | StrOutputParser()

print("------------模型回复------------------------")
print("------------向量检索+BM25[0.5, 0.5]------------------------")
print(chain1.invoke({"question": question}))
print("------------向量检索------------------------")
print(chain2.invoke({"question": question}))
```
### 三. 查询优化- 查询扩展
### 1. **痛点分析**
当用户没有正确书写查询语句，或者LLM不能够正确理解用户查询语句的含义时，此时LLM生成的答案可能就不够完整和全面。
### 2. 解决思路
Multi Query的基本思想是当用户输入查询语句(自然语言)时，我们让大模型(LLM)基于用户的问题再生成多个查询语句，这些生成的查询语句是对用户查询语句的补充，它们是从不同的视角来补充用户的查询语句，然后每条查询语句都会从向量数据库中检索到一批相关文档，最后所有的相关文档都会被喂给LLM，这样LLM就会生成比较完整和全面的答案。这样就可以避免因为查询语句的差异而导致结果不正确。
- 利用 LLM 生成 N 个与原始查询相关的问题
- 将所有问题（加上原始查询）发送给检索系统。
- 通过这种方法，可以从向量库中检索到更多文档。

> 注意: 和假设性索引很像,但是一个是提问,一个是查询

### 3. 完整代码
```plain text
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableMap
from langchain_classic.retrievers import MultiQueryRetriever
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# 本地embedding模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
# 初始化嵌入模型（用于文本向量化）
embeddings_model = HuggingFaceEmbeddings(
    model_name=embedding_model_path
)

# 目标 URL
url = "https://news.pku.edu.cn/mtbdnew/15ac0b3e79244efa88b03a570cbcbcaa.htm"

# 加载网页
loader = WebBaseLoader(url)
docs = loader.load()
# 创建文档分割器，并分割文档
text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
splits = text_splitter.split_documents(docs)

# 创建向量数据库
vectorstore = Chroma.from_documents(documents=splits,
                                    embedding=embeddings_model)
# 创建检索器
retriever = vectorstore.as_retriever()

# relevant_docs = retriever.invoke('天才AI少女是谁')
# print(relevant_docs)

# print(len(relevant_docs))

# 创建llm
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# 创建prompt模板
template = """请根据下面给出的上下文来回答问题:
{context}
问题: {question}
"""

# 由模板生成prompt
prompt = ChatPromptTemplate.from_template(template)

chain = RunnableMap({
    "context": lambda x: retriever.invoke(x["question"]),
    "question": lambda x: x["question"]
}) | prompt | llm | StrOutputParser()

print("--------------优化前-------------------")
response = chain.invoke({"question": "天才AI少女是谁"})
print(response)



print("--------------生成问题加载文档-------------------")
# 使用MultiQueryRetriever
import logging
# 打开日志
# 将日志级别设置为 INFO（显示所有日志）langchain的默认日志级别是WARNING  可以把日志等级改为INFO 就会显示生成的问题
logging.basicConfig(level=logging.INFO)

# 在MultiQueryRetriever.from_llm好对象之后 方法会用默认的提示词模板生成问题 'DEFAULT_QUERY_PROMPT'
retrieval_from_llm = MultiQueryRetriever.from_llm(
    retriever=retriever,
    llm=llm,
)

unique_docs = retrieval_from_llm.invoke(input="天才AI少女是谁")
print(unique_docs)
print(len(unique_docs))



print("--------------优化后-------------------")
chain1 = RunnableMap({
    "context": lambda x: retrieval_from_llm.invoke(input=x["question"]),
    "question": lambda x: x["question"]
}) | prompt | llm | StrOutputParser()

res = chain1.invoke({"question": "天才AI少女是谁"})
print(res)
```
### 四. Post-Retrieval后检索
重点是有效的融合检索到的相关内容和query。
### 1. RAG-Fusion
### 1.1 痛点分析
- 在多个查询检索后，会检索到大量的上下文，但并非所有上下文都与问题相关，有的不相关文档可能出现在文档前面，影响答案生成的准确性

### 1.2 解决思路
- RAG-Fusion 是一种搜索方法，旨在弥合传统搜索范式与人类查询多维度之间的差距。受检索增强生成（RAG）能力的启发，该项目更进一步，通过使用多重查询生成和互惠排名融合（Reciprocal Rank Fusion）对搜索结果进行重新排序。
- 其主要思想就是在Multi Query的基础上，对其检索结果进行重新排序(即reranking)后输出Top K个最相关文档，最后将这top k个文档喂给LLM并生成最终的答案

### 1.3 完整代码
```plain text
import os
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_classic import hub
from langchain_core.load import dumps, loads
from dotenv import load_dotenv

load_dotenv()

texts = [
    "人工智能在医疗诊断中的应用。",
    "人工智能如何提升供应链效率。",
    "NBA季后赛最新赛况分析。",
    "传统法式烘焙的五大技巧。",
    "红楼梦人物关系图谱分析。",
    "人工智能在金融风险管理中的应用。",
    "人工智能如何影响未来就业市场。",
    "人工智能在制造业的应用。",
    "今天天气怎么样",
    "人工智能伦理：公平性与透明度。"
]

# 本地embedding模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
# 初始化嵌入模型（用于文本向量化）
embeddings_model = HuggingFaceEmbeddings(
    model_name=embedding_model_path
)
# 创建向量数据库对象
vectorstore = Chroma.from_texts(
    texts=texts, embedding=embeddings_model
)

retriever = vectorstore.as_retriever()

# https://smith.langchain.com/hub/search?q=langchain-ai%2Frag-fusion-query-generation
prompt = hub.pull("langchain-ai/rag-fusion-query-generation")
# print(prompt)

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)
# 创建多重查询chain
generate_queries = (
        prompt | llm | StrOutputParser() | (lambda x: x.split("\n"))
)

original_query = "人工智能的应用"
queries = generate_queries.invoke({"original_query": original_query})

print('--------------问题检索到的内容-------------')
print(queries)
# 我们检索到的内容的位置是不一样的, 需要给查询到的数据进行融合重排
for i in queries:
    print(retriever.invoke(i))


def reciprocal_rank_fusion(results: list[list], k=60):
    """互逆排序融合算法，用于合并多个排序文档列表
    Args:
        results: 包含多个排序文档列表的二维列表
        k: 融合公式中的平滑参数（默认60），值越小排名影响越大
    Returns:
        按融合分数降序排列的文档列表，每个元素为(文档对象, 分数)元组
    """

    # 初始化融合分数字典（key=序列化文档，value=累计分数）
    fused_scores = {}

    # 遍历每个检索结果列表（每个查询对应的结果）
    for docs in results:
        # 对当前结果列表中的文档进行遍历（rank从0开始计算）
        for rank, doc in enumerate(docs):
            # 序列化文档对象为字符串（用于唯一标识）
            doc_str = dumps(doc)
            # 初始化文档得分（如果是首次出现）
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0
            # 计算并累加RRF分数：1 / (当前排名 + k)
            # 排名越靠前（rank值小）的文档获得的分数越高
            fused_scores[doc_str] += 1 / (rank + k)

    # 按融合分数降序排序（分数越高排名越前）
    sorted_Data = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    # print(sorted_Data)
    reranked_results = [
        (loads(doc), score)  for doc, score in sorted_Data
    ]

    return reranked_results

print('--------------问题融合后的内容-------------')
original_query = "人工智能的应用"
chain = generate_queries | retriever.map() | reciprocal_rank_fusion

# 输入结果列表
result_list = chain.invoke({"original_query": original_query})
print(result_list)
# 提取文档内容和对应分数
for i in result_list:
    print(i[0].page_content, i[1])
```
### 1.4 融合排序
- 把我们检索到的内容进行融合和排序
- 多个查询可能检索到不同的相关文档，有的排名高，有的排名低。`RRF` 通过公式 `1 / (rank + k)` 对所有查询结果重新评分，保证更全面的相关性。
- 其中`generate_queries`会生成4个多角度的query, `retriever.map()`的作用是根据`generate_queries`的结果映射出4个retriever(可以理解为同时复制出4个retriever)与`generate_queries`会生成4个query对应，并为每个query检索出来的一组相关文档集(默认为4个相关文档)，那么4个query总共可以生成16个相关文档。最后会经过RRF算法重新排序后输出最相关的文档

### 1.5 计算逻辑
```plain text
Question Rankings
Question A: Doc1 Doc4 Doc3 Doc2
Question B: Doc3 Doc1 Doc2 Doc4
Question C: Doc4 Doc3 Doc1 Doc2
Question D: Doc2 Doc1 Doc4 Doc3
Rank Positions
Doc1:
Question A rank: 0
Question B rank: 1
Question C rank: 2
Question D rank: 1
Doc2:
Question A rank: 3
Question B rank: 2
Question C rank: 3
Question D rank: 0
Doc3:
Question A rank: 2
Question B rank: 0
Question C rank: 1
Question D rank: 3
Doc4:
Question A rank: 1
Question B rank: 3
Question C rank: 0
Question D rank: 2
Reciprocal Rank Fusion Calculation
Using k = 60:
Doc1
Reciprocal Rank (Question A): 1 / (60 + 0) = 1 / 60
Reciprocal Rank (Question B): 1 / (60 + 1) = 1 / 61
Reciprocal Rank (Question C): 1 / (60 + 2) = 1 / 62
Reciprocal Rank (Question D): 1 / (60 + 1) = 1 / 61
RRF(Doc1): 1 / 60 + 1 / 61 + 1 / 62 + 1 / 61 ≈ 0.0656
Doc2
Reciprocal Rank (Question A): 1 / (60 + 3) = 1 / 63
Reciprocal Rank (Question B): 1 / (60 + 2) = 1 / 62
Reciprocal Rank (Question C): 1 / (60 + 3) = 1 / 63
Reciprocal Rank (Question D): 1 / (60 + 0) = 1 / 60
RRF(Doc2): 1 / 63 + 1 / 62 + 1 / 63 + 1 / 60 ≈ 0.0645
Doc3
Reciprocal Rank (Question A): 1 / (60 + 2) = 1 / 62
Reciprocal Rank (Question B): 1 / (60 + 0) = 1 / 60
Reciprocal Rank (Question C): 1 / (60 + 1) = 1 / 61
Reciprocal Rank (Question D): 1 / (60 + 3) = 1 / 63
RRF(Doc3): 1 / 62 + 1 / 60 + 1 / 61 + 1 / 63 ≈ 0.0651
Doc4
Reciprocal Rank (Question A): 1 / (60 + 1) = 1 / 61
Reciprocal Rank (Question B): 1 / (60 + 3) = 1 / 63
Reciprocal Rank (Question C): 1 / (60 + 0) = 1 / 60
Reciprocal Rank (Question D): 1 / (60 + 2) = 1 / 62
RRF(Doc4): 1 / 61 + 1 / 63 + 1 / 60 + 1 / 62 ≈ 0.0651
```
### 2. **上下文压缩**
### 2.1 痛点分析
- 我们划分文档块的时候，通常不知道用户的查询，这意味着，与查询最相关的信息可能隐藏在一个包含大量不相关文本的文档中，这样输入给LLM，可能会导致更昂贵的LLM调用和较差的响应。

### 2.2 解决思路
- 上下文压缩旨在解决这个问题：我们可以使用给定查询的上下文来压缩它们，以便只返回相关信息，而不是立即按原样返回检索到的文档。
- 这里的“压缩”既指压缩单个文档的内容，也指批量过滤文档。

**基本思路：**
3. 使用某种基本的检索器来检索[不同的](https://so.csdn.net/so/search?q=%E4%B8%8D%E5%90%8C%E7%9A%84&spm=1001.2101.3001.7020)信息；
4. 然后将检索到的信息添加到文档压缩器中；
5. 压缩器对这些信息进行过滤和处理，只提取对回答问题有用的信息。

因此，要[使用上下文](https://so.csdn.net/so/search?q=%E4%BD%BF%E7%94%A8%E4%B8%8A%E4%B8%8B%E6%96%87&spm=1001.2101.3001.7020)压缩检索器，我们需要：
- 基础检索器
- 文档压缩器

### 2.3 完整代码
```plain text
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor, EmbeddingsFilter, LLMChainFilter
from langchain_classic.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_text_splitters import CharacterTextSplitter
import os
from dotenv import load_dotenv

load_dotenv()


# 格式化输出内容
def pretty_print_docs(docs):
    print(
        f"\n{'-' * 100}\n".join(
            [f"Document {i + 1}:\n\n" + d.page_content for i, d in enumerate(docs)]
        )
    )


# documents = TextLoader("deepseek介绍.txt", encoding="utf-8").load()
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1024,
#     chunk_overlap=100
# )
# texts = text_splitter.split_documents(documents)
# 本地embedding模型地址
embedding_model_path = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
# 初始化嵌入模型（用于文本向量化）
embeddings_model = HuggingFaceEmbeddings(
    model_name=embedding_model_path
)
persist_directory="./chroma_db"
# chroma = Chroma.from_documents(texts, embeddings_model, persist_directory=persist_directory)
chroma = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings_model
)
retriever = chroma.as_retriever()

print("-------------------压缩前--------------------------")
docs = retriever.invoke("deepseek的发展历程")
pretty_print_docs(docs)

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)


# # LLMChainExtractor 具体执行文档内容精炼的压缩器, 通过 LLM 对文档进行精炼
# compressor = LLMChainExtractor.from_llm(llm)
# # ContextualCompressionRetriever 将基础检索器和 压缩器结合
# compression_retriever = ContextualCompressionRetriever(
#     base_compressor=compressor, base_retriever=retriever
# )
# print("-------------------LLMChainExtractor压缩后--------------------------")
# compressed_docs = compression_retriever.invoke("deepseek的发展历程")
# pretty_print_docs(compressed_docs)



# # LLMChainFilter 具体执行文档内容过滤的压缩器, 通过 LLM 对文档进行过滤
# _filter = LLMChainFilter.from_llm(llm)
# compression_retriever = ContextualCompressionRetriever(
#     base_compressor=_filter, base_retriever=retriever
# )
# print("-------------------LLMChainFilter压缩后--------------------------")
# compressed_docs = compression_retriever.invoke("deepseek的发展历程")
# pretty_print_docs(compressed_docs)


# # EmbeddingsFilter 具体执行文档内容过滤的压缩器, 通过检索到的文档相识度进行过滤
# embeddings_filter = EmbeddingsFilter(embeddings=embeddings_model, similarity_threshold=0.66)
# compression_retriever = ContextualCompressionRetriever(
#     base_compressor=embeddings_filter, base_retriever=retriever
# )
# compressed_docs = compression_retriever.invoke("deepseek的发展历程")
# print("-------------------EmbeddingsFilter压缩后--------------------------")
# pretty_print_docs(compressed_docs)






# EmbeddingsRedundantFilter是文档和文档之间进行过滤的压缩器
redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings_model)
# EmbeddingsFilter是查询问题和文档的相似度进行过滤
relevant_filter = EmbeddingsFilter(embeddings=embeddings_model, similarity_threshold=0.66)
# DocumentCompressorPipeline 是一个用于串联多个文档处理步骤的组件，其核心作用是通过组合不同的文档转换/过滤工具，构建一个多阶段的文档压缩流水线
pipeline_compressor = DocumentCompressorPipeline(
    transformers=[redundant_filter, relevant_filter]
)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=pipeline_compressor, base_retriever=retriever
)
print("-------------------DocumentCompressorPipeline压缩后--------------------------")
compressed_docs = compression_retriever.invoke("deepseek的发展历程")
pretty_print_docs(compressed_docs)
```
### 2.4 构建检索器
- 下面的txt文档是百度百科上关于deepseek的介绍，首先使用基础检索器
- 总共输出的四个相关文档，可以发现Document 3和4是没那么相关的内容

```plain text
documents = TextLoader("deepseek介绍.txt", encoding="utf-8").load()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,
    chunk_overlap=100
)
texts = text_splitter.split_documents(documents)
embeddings_model = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key=os.getenv("api_key"),
)
retriever = Chroma.from_documents(texts, embeddings_model).as_retriever()
print("-------------------压缩前--------------------------")
docs = retriever.invoke("deepseek的发展历程")
pretty_print_docs(docs)
```
### 2.5 创建上下文压缩检索器

| **特性** | **LLMChainExtractor** | **LLMChainFilter** | **EmbeddingsFilter** |
| --- | --- | --- | --- |
| **工作原理** | 使用LLM重写文档内容 | 使用LLM判断文档相关性 | 使用嵌入向量计算相似度 |
| **输出结果** | 修改后的精炼文档 | 是/否的文档保留决策 | 文档相关性分数 |
| **是否修改内容** | ✅ 修改文档内容 | ❌ 只做过滤 | ❌ 只做过滤 |
| **计算开销** | 高 (调用LLM次数多) | 中 (每文档调用LLM) | 低 (向量计算) |
| **主要用途** | 提取关键信息 | 过滤不相关文档 | 相似度过滤 |
| **精度依赖** | LLM的理解能力 | LLM的判断能力 | 嵌入模型质量 |

### 五. MinerU 处理 PDF
**问题描述:**
之前我们讲过我们半结构化数据对于传统 RAG 来说可能具有挑战性，文本拆分可能会分解表，从而损坏检索中的数据；嵌入表可能会给语义相似性搜索带来挑战。对于这个问题可以通过构建摘要索引解决这个问题：分别为每个文本和表格数据创建摘要或者转换成其他处理方便的格式(html, md, json)
### 1. MinerU 是什么？
MinerU 是**上海人工智能实验室 OpenDataLab** 开源的一站式文档智能解析工具
主要目标：
- 把**复杂排版 PDF结构清晰、可直接喂大模型**
（公式 + 表格 + 多栏 + 图表 + 脚注 + 页眉页脚） → 转为
的 Markdown / JSON

核心亮点（目前开源 PDF 解析工具中最强之一）：
- 公式 → LaTeX（极高准确率）
- 表格 → Markdown 表格 / HTML
- 图片 → 提取 + 可配图描述 - 支持**扫描件 / 生图 PDF**
（自动 OCR，109 种语言）
- 自动去除页眉、页脚、页码、重复脚注 - 保留阅读顺序（单栏/双栏/复杂混排都比较聪明）
- 支持中英文混排、科技文献效果显著优于大部分商业工具

适用场景：
- 学术文献批量清洗 → RAG / 知识库
- 财报 / 招股书 / 法律文件结构化提取
- LLM 预训练 / SFT 高质量语料准备
- 个人文献管理、阅读增强

项目地址：[https://github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)
在线体验（限速/限量）：[https://mineru.net/](https://mineru.net/)
### 2. 三种使用方式对比

| **使用方式** | **难度** | **速度** | **表格识别** | **公式 LaTeX** | **批量处理** | **适合人群** |
| --- | --- | --- | --- | --- | --- | --- |
| 在线网页版 | ★☆☆ | 较慢 | 部分 | 部分 | 不方便 | 临时体验、少量文件 |
| 一键桌面客户端 | ★★☆ | 快 | 优秀 | 优秀 | 支持 | 大多数普通用户 |
| 本地命令行/Python | ★★★ | 最快 | 完全可控 | 完全可控 | 极强 | 开发者 / 批量需求 |

### 1. 方式一
6. 打开 [https://mineru.net/](https://mineru.net/)
7. 拖入或上传 pdf 文件（≤200MB 左右）
8. 等待解析完成 → 下载 .md 文件

**注意事项**：
- 图片是网络链接（在线版不下载图片实体）
- 复杂表格可能仍以图片形式存在
- 免费额度有限，高峰期要排队

### 2. 方式二
官方已推出跨平台客户端（Win / Mac / Linux）
下载地址：[https://mineru.net/](https://mineru.net/) → 客户端下载区
操作步骤：
9. 安装后打开 MinerU 客户端
10. 选择「PDF 解析」模块
11. 拖入文件或文件夹（支持批量）
12. 重要参数设置（建议）：
- 公式识别：开启 - 表格识别：开启（推荐 table-transform: markdown）
- 输出格式：Markdown（推荐） / JSON（结构化需求）
13. 点击「开始解析」→ 得到输出文件夹

![[1772802266010-6275986b-2c97-4852-b3d7-7af78c3e4dd2.png]]
### 3. 方式三
- 模块下载

```plain text
pip install -U "mineru[all]"
pip install hf_xet
```
- 首次模型下载

```plain text
from modelscope import snapshot_download

snapshot_download('OpenDataLab/PDF-Extract-Kit-1.0', local_dir=r'D:\LLM\Local_model\PDF-Extract-Kit-1.0')
```
- 添加环境变量

MINERU_MODEL_DIR = D:_model-Extract-Kit-1.0
- 替换代码

```plain text
import os
from mineru.cli.common import do_parse
from mineru.data.data_reader_writer import FileBasedDataWriter

# ===== 1️⃣ 输入 PDF =====
pdf_path = "2020-03-17__厦门灿坤实业股份有限公司__200512__闽灿坤__2019年__年度报告.pdf"

with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

# ===== 2️⃣ 输出目录 =====
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# ===== 3️⃣ MinerU 要求：必须是「列表」 =====
pdf_file_names = [os.path.basename(pdf_path)]
pdf_bytes_list = [pdf_bytes]
p_lang_list = [""]   # 自动语言识别

# ===== 4️⃣ 图片 writer =====
img_writer = FileBasedDataWriter(
    os.path.join(output_dir, "images")
)

# ===== 5️⃣ 核心解析 =====
do_parse(
    pdf_file_names=pdf_file_names,
    pdf_bytes_list=pdf_bytes_list,
    p_lang_list=p_lang_list,
    output_dir=output_dir,
    img_writer=img_writer,
    parse_method="auto"
)
```
### 五. Advanced RAG实战-金融助手
### 1. **项目背景**
- 在金融领域，开发一个能够仿效专家解读上市公司年报的智能对话系统，一直是人工智能技术进步的关键目标。尽管目前的人工智能系统在文本对话领域已展现出显著的进展，但在更为精细、更具挑战性的金融领域交互方面，其性能尚需进一步提升。因此，我们致力于在现有大型模型的基础上，通过精细化调整、大型与小型模型的协同工作以及利用向量数据库等尖端技术，旨在进一步增强人工智能模型的性能。
- 项目架构图

### 
![[1772720670159-f71355b8-32d6-4148-a011-ed31e5e8392a.png]]
### 2. 完整代码
```plain text
import os
from typing import List
import re

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableMap
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever  # 注意：这个包名可能需要确认是否为 langchain_experimental 或其他 fork
from langchain_chroma import Chroma

from base_llm import llm, embeddings_model


class TableExtractor:
    """只负责从文本中抽取 <table>...</table> 标签，并用占位符替换，保留原始表格内容"""

    @staticmethod
    def extract_tables_and_text(
            text: str,
            start_table_id: int = 0
    ) -> tuple[List[tuple[str, str]], str]:
        """
        从文本中提取所有 <table> 标签内容，并用 tbl_0__、tbl_1__ ... 这样的占位符替换
        返回：(表格列表, 替换后的纯文本)
        """
        table_pattern = r'(<table>.*?</table>)'
        # re.DOTALL 匹配多行
        # re.IGNORECASE 忽略大小写
        tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
        # 判断是否有表格
        if not tables:
            return [], text
        # 存储表格列表
        table_items = []
        cleaned = text
        # 给起始文档id编号
        current_id = start_table_id

        for tbl in tables:
            table_id = f"tbl_{current_id}__"
            cleaned = cleaned.replace(tbl, table_id, 1)  # 只替换第一次出现
            table_items.append((table_id, tbl))
            current_id += 1

        return table_items, cleaned


class TableConverter:
    """（目前未在主流程中使用）将 HTML 表格转为 key:value 紧凑文本格式"""

    @staticmethod
    def get_table_kv_chain():
        """定义一个把表格转成 键:值, 键:值 格式的 LLM Chain（示例，未实际调用）"""
        prompt = ChatPromptTemplate.from_template(
            """你是一个数据格式转换助手。
                任务：把下面提供的表格形式数据（通常是两列：键 + 值），转换成紧凑的单行 KV 文本格式。

                转换规则：
                1. 每一行数据输出成一行文本
                2. 格式严格为：键1:值1, 键2:值2, 键3:值3, ... （注意逗号后有一个空格）
                3. 键和值之间用英文冒号 : 连接，不要加空格
                4. 如果一行有多个字段，按表格的列顺序依次写成 key:value 形式，用逗号 + 空格分隔
                5. 第一行如果是表头，则每一行数据都使用这些相同的字段名作为 key
                6. 值中如果本来包含逗号、冒号等特殊字符，保留原样，不要转义
                7. 第一行对表格生成一个20字左右的简介,并介绍字段

                示例输入：
                姓名 年龄 城市
                张三 18 北京
                李四 25 上海

                示例输出：
                人员信息（字段：姓名, 年龄, 城市）
                姓名:张三, 年龄:18, 城市:北京
                姓名:李四, 年龄:25, 城市:上海

                现在请严格按照以上规则转换以下数据：
                {table_content}
                """
        )
        return prompt | llm | StrOutputParser()


class MarkdownTableAwareSplitter:
    """智能切分 Markdown，支持识别并特殊处理 <table> 标签"""

    def __init__(self):
        self.table_extractor = TableExtractor()

    @staticmethod
    def should_merge(prev_len: int, new_len: int, max_len: int) -> bool:
        """判断前后两段是否应该合并（留2个字符给换行）"""
        return (prev_len + new_len + 2) <= max_len

    def split(
            self,
            documents: List[Document],
            max_text_length: int = 1200,
            min_text_length_to_merge: int = 400,
            min_nonempty_text_len: int = 40,
    ) -> List[Document]:
        """
        核心功能：对已经按标题初步切分好的文档列表进行二次智能切分。
        主要目标：
        1. 将普通文本合并成接近 max_text_length 大小的 chunk（尽量减少碎片）
        2. 将 <table>...</table> 完整抽取出来，作为独立的 Document（category="Table"）
        3. 在普通文本中用占位符（如 tbl_0__）暂时替换表格，保持文本连贯性
        4. 最后过滤掉过短、无意义的文本块（但保留所有表格）

        参数说明：
            documents             : List[Document]          已经按一级标题（Header 1）切分好的文档列表
            max_text_length       : int = 1200             单个文本 chunk 的最大字符长度（目标长度）
            min_text_length_to_merge : int = 400           当前 pending_text 与新 chunk 合并的最小长度阈值（避免太碎）
            min_nonempty_text_len : int = 40               最终保留的文本块最小有效长度（低于此值且无字母数字则丢弃）

        返回：
            List[Document]  处理后的文档列表，包含：
                - 普通文本 chunk（已合并、去空行、清理行尾空格）
                - 独立的表格 Document（category="Table"，保留原始 HTML）
        """
        final_docs: List[Document] = []  # 最终输出的所有 Document 列表
        pending_text: str = ""  # 当前正在累积的、尚未提交的文本内容（用于合并）
        pending_meta: dict = {}  # pending_text 对应的元数据（在提交时使用）
        global_table_counter = 0  # 全局表格计数器，用于生成唯一的 table_id（如 tbl_0__、tbl_1__）

        # 遍历每一个初步切分后的文档（通常是一个标题下的内容）
        for doc in documents:
            content = doc.page_content.strip()  # 去除首尾空白，防止空文档干扰
            if not content:  # 如果内容完全为空，直接跳过
                continue

            # 获取当前文档的元数据，并提取章节标题（用于表格的元数据）
            metadata = doc.metadata.copy()  # 复制一份，避免修改原始对象
            section_title = metadata.get("Header 1", "未知章节")

            # 步骤1：从当前 content 中抽取所有 <table>...</table>，替换为占位符
            # 返回：table_items = [(table_id, 原始表格HTML), ...]
            #       text_only  = 替换占位符后的纯文本
            table_items, text_only = self.table_extractor.extract_tables_and_text(
                content, global_table_counter
            )

            # 步骤2：对纯文本进行行级清理
            # - splitlines()：按行拆分
            # - if line.strip()：过滤完全空白行（包括只有空格/Tab的行）
            # - line.rstrip()：只去除每行右边的空白（保留左侧缩进，如 Markdown 列表、代码块）
            lines = [line.rstrip() for line in text_only.splitlines() if line.strip()]

            current_chunk = ""  # 当前正在构建的文本块（在本段落内合并）

            # 步骤3：逐行尝试合并成较大的文本块
            for line in lines:
                # 尝试把当前行拼接到 current_chunk 后面（中间加换行）
                tentative = (current_chunk + "\n" + line).strip() if current_chunk else line

                # 如果拼接后长度还在限制内 → 继续累积
                if len(tentative) <= max_text_length:
                    current_chunk = tentative
                else:
                    # 当前块已经太大，需要决定是提交还是合并到 pending_text
                    if pending_text and self.should_merge(len(pending_text), len(current_chunk), max_text_length):
                        # 可以合并到前面的 pending_text（跨段落合并）
                        pending_text = (pending_text + "\n\n" + current_chunk).strip()
                    else:
                        # 无法合并 → 把 pending_text 提交为一个 Document
                        if pending_text:
                            final_docs.append(Document(
                                page_content=pending_text,
                                metadata=pending_meta
                            ))
                        # 开始新的 pending_text
                        pending_text = current_chunk
                        pending_meta = metadata.copy()  # 使用当前段落的元数据

                    # 当前行作为新块的起点
                    current_chunk = line

            # 处理循环结束后剩余的 current_chunk（最后一小段）
            if current_chunk:
                if pending_text and self.should_merge(len(pending_text), len(current_chunk), max_text_length):
                    pending_text = (pending_text + "\n\n" + current_chunk).strip()
                else:
                    if pending_text:
                        final_docs.append(Document(page_content=pending_text, metadata=pending_meta))
                    pending_text = current_chunk
                    pending_meta = metadata.copy()

            # 步骤4：把本段落中抽取的所有表格，逐个转为独立的 Document
            for table_id, table_content in table_items:
                # 如果前面还有未提交的文本，先提交掉（保证文本和表格的相对顺序）
                if pending_text:
                    final_docs.append(Document(page_content=pending_text, metadata=pending_meta))
                    pending_text = ""
                    pending_meta = {}

                # 为表格准备专属元数据
                table_meta = metadata.copy()
                table_meta.update({
                    "category": "Table",  # 标记为表格，便于后续过滤/单独召回
                    "table_id": table_id,  # 如 "tbl_3__"，用于占位符替换
                    "table_section": section_title,  # 所属章节标题，便于理解上下文
                })

                # 创建表格 Document（目前使用原始 HTML）
                final_docs.append(Document(
                    page_content=table_content,  # 原始 <table>...</table> 内容
                    # 如果未来想转为更易读的 KV 格式，可在此处调用 LLM 转换：
                    # page_content=TableConverter.get_table_kv_chain().invoke({"table_content": table_content}),
                    metadata=table_meta
                ))

                global_table_counter += 1  # 计数器递增，保证 table_id 全局唯一

        # 步骤5：循环结束后，如果还有剩余的 pending_text，提交它
        if pending_text and len(pending_text.strip()) >= min_nonempty_text_len:
            final_docs.append(Document(page_content=pending_text, metadata=pending_meta))

        # 步骤6：最终过滤 - 去除过短且无实际内容的文本块（表格不受影响）
        filtered = []
        for d in final_docs:
            text = d.page_content.strip()

            if d.metadata.get("category") == "Table":
                # 所有表格都保留（无论长短）
                filtered.append(d)
                continue

            # 普通文本：长度太短 且 不包含任何字母/数字/汉字 等有意义字符 → 丢弃
            if len(text) < min_nonempty_text_len and not re.search(r'\w', text):
                continue

            filtered.append(d)

        return filtered


class XiamenDocRAG:
    """厦门文档专用的 RAG 封装：加载 → 智能切分 → 向量化 → 混合检索 → 回答"""

    def __init__(
            self,
            filepath="./厦门.md",
            persist_directory="./chroma_db",
            collection_name="my_collection",
            max_chunk_length=800,
            batch_size=10,
    ):
        self.filepath = filepath
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.max_chunk_length = max_chunk_length
        self.batch_size = batch_size

        self.vector_db = None
        self.retriever = None
        self.chain = None
        self.documents = None  # 保存原始切分后的 documents，便于 BM25 使用

        # 处理文档
        self._load_and_process()
        self._build_retrievers_and_chain()

    def _load_and_process(self):
        """加载 Markdown → 按标题切分 → 自定义切分（考虑表格）→ 向量化存储"""
        loader = TextLoader(self.filepath, encoding="utf-8")
        docs = loader.load()

        # 按一级标题切分
        headers_to_split_on = [("#", "Header 1")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        split_docs = markdown_splitter.split_text(docs[0].page_content)

        # 自定义切分：保护表格、合理合并文本段落
        splitter = MarkdownTableAwareSplitter()
        self.documents = splitter.split(
            documents=split_docs,
            max_text_length=self.max_chunk_length,
        )

        # 创建/连接 Chroma 向量库
        self.vector_db = Chroma(
            collection_name=self.collection_name,
            embedding_function=embeddings_model,
            persist_directory=self.persist_directory
        )
        if not len(os.listdir(self.persist_directory)) > 1:
            # 分批添加文档（防止内存爆炸）
            for i in range(0, len(self.documents), self.batch_size):
                batch = self.documents[i:i + self.batch_size]
                print(f'第 {i // self.batch_size + 1} 批次 文件数: {len(batch)}')
                self.vector_db.add_documents(batch)

    def _build_retrievers_and_chain(self):
        """构建混合检索器 + 后处理（把占位符替换回真实表格内容） + Chain"""
        vector_retriever = self.vector_db.as_retriever(search_kwargs={"k": 6})
        bm25_retriever = BM25Retriever.from_documents(self.documents, k=4)

        # Ensemble 融合：BM25 0.3 + 向量 0.7
        self.retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.3, 0.7]
        )

        def replace_table_placeholders(docs):
            """把检索到的文档中的 tbl_0__ 等占位符替换回真正的表格 HTML 内容"""
            # 从向量库中获取所有表格（category=Table）
            table_docs = self.vector_db.get(where={"category": "Table"})
            table_map = {}
            for meta, content in zip(table_docs["metadatas"], table_docs["documents"]):
                tid = meta.get("table_id")
                if tid:
                    table_map[tid] = content

            context_parts = []
            for doc in docs:
                text = doc.page_content

                def repl(match):
                    tbl_id = f"tbl_{match.group(1)}__"
                    return table_map.get(tbl_id, f"【表格 {tbl_id} 内容缺失】")

                new_text = re.sub(r'tbl_(\d+)__', repl, text)
                context_parts.append(new_text)

            return "\n\n".join(context_parts)

        replace_step = RunnableLambda(lambda x: {
            "context": replace_table_placeholders(x["retrieved_docs"]),
            "question": x["question"]
        })

        template = """请根据下面给出的上下文或者表格来回答问题:
        {context}

        问题: {question}

        回答要尽量准确、完整，使用 markdown 格式排版。
        如果涉及表格，请保留关键数据，不要省略。
        """
        prompt = ChatPromptTemplate.from_template(template)

        self.chain = (
                RunnableMap({
                    "retrieved_docs": lambda x: self.retriever.invoke(x["question"]),
                    "question": lambda x: x["question"]
                })
                | replace_step
                | prompt
                | llm
                | StrOutputParser()
        )

    def query(self, question: str) -> str:
        """执行 RAG 查询"""
        if self.chain is None:
            raise RuntimeError("RAG 未初始化完成")
        return self.chain.invoke({"question": question})


# 使用示例
if __name__ == "__main__":
    rag = XiamenDocRAG(
        filepath="./厦门.md",
        persist_directory="./chroma_db",
        max_chunk_length=800,
    )
    answer = rag.query("我们公司是叫什么")
    print(answer)
    answer = rag.query("公司简介和主要财务指标内容")
    print(answer)
    answer = rag.query("营业收入构有哪些?可以往哪里发展?")
    print(answer)
```

# summary

---
## 一、 核心架构：从“朴素”到“高级”
高级 RAG 在传统的“检索-生成”基础上，增加了**预检索（Pre-Retrieval）**和**后检索（Post-Retrieval）**两个关键阶段。

| **阶段** | **核心任务** | **解决的问题** |
| --- | --- | --- |
| **预检索** | 优化索引结构与查询表达 | 解决“搜不到”、“搜不准”的问题。 |
| **检索后** | 融合、排序与压缩上下文 | 解决“信息过载”、“干扰项多”的问题。 |

---
## 二、 预检索：索引与查询的深度优化
### 1. 索引结构优化（让数据更“好找”）
当遇到复杂文档（如带表格的 PDF）时，单一的切片策略往往会失效。
- **摘要索引 (Summary Index)**：
    - **痛点**：大文档切片后，单个切片可能丢失全文语义。
    - **方案**：为每个块生成 **Summary** 存入向量库，检索时先匹配摘要，再回溯原始块。
- **父子索引 (Parent-Document Retrieval)**：
    - **方案**：将文档切分为“子块”（用于精准匹配）和“父块”（用于提供上下文）。
    - **效果**：平衡了检索的“准确性”与生成的“完整性”。
- **元数据索引 (Metadata Filtering)**：
    - **方案**：在向量检索前，先通过标签（如作者、年份、评分）进行**硬过滤**。
    - **工具**：LangChain 中的 `SelfQueryRetriever`。

### 2. 查询优化（让问题更“清晰”）
- **假设性问题索引**：利用 LLM 为文档块预设 3 个假设性问题并向量化，实现“问题搜问题”而非“问题搜文档”。
- **查询扩展 (Multi-Query)**：将用户的一个模糊问题扩展为多个维度的查询语句，提高召回率。
- **混合检索 (Hybrid Search)**：结合 **BM25 (关键词)** 与 **Vector (语义)**，解决专有名词检索难的问题。

---
## 三、 后检索：上下文的“精加工”
检索回来的 Top-K 文档往往包含大量噪音，需要进一步处理。
### 1. RAG-Fusion & 排序 (Reranking)
- **原理**：通过多重查询检索出多组文档，使用 **RRF (互惠排名融合)** 算法重新计算得分。
- **公式**：$score = \sum_{d \in D} \frac{1}{k + rank(d)}$。
- **意义**：让在多个搜索结果中都排名靠前的文档获得更高权重。

### 2. 上下文压缩 (Context Compression)
- **LLMChainExtractor**：让 LLM 提取文档中仅与问题相关的片段。
- **EmbeddingsFilter**：基于相似度阈值剔除低相关性的文档。

---
## 四、 实战：复杂 PDF 处理 (MinerU & 金融助手)
### 1. MinerU：攻克 PDF 解析难题
传统的 PDF 解析容易损坏表格和公式。**MinerU** 能将复杂排版（多栏、图文混排）转换为高质量的 **Markdown/LaTeX**。
### 2. 金融助手实战逻辑
在处理年报等金融文档时，建议采用以下流程：
14. **解析**：使用 MinerU 将 PDF 转为 Markdown。
15. **提取**：识别并提取 `<table>` 标签，用占位符（如 `tbl_0__`）保护表格不被切断。
16. **切分**：按标题层级切分，并确保表格作为独立 Document 存储。
17. **召回**：混合检索 + 占位符还原，确保 LLM 最终能看到完整的表格 HTML。

---
## 五、 技术方案对比总结

| **优化技术** | **适用场景** | **复杂度** |
| --- | --- | --- |
| **摘要索引** | 半结构化数据、多表格文档 | 中 |
| **混合检索** | 包含大量专有名词、缩写的场景 | 低 |
| **RAG-Fusion** | 用户提问模糊、需要多维度检索时 | 高 |
| **上下文压缩** | 节省 Token 消耗、避免 LLM “迷失” | 中 |

你目前在实施哪一个阶段的优化？如果有具体的代码实现问题，我们可以针对某个组件深入探讨。