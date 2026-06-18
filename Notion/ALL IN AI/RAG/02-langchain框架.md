---
notion-id: 338a95f7-5835-8184-a326-d866d629c7f5
---
## `LangChain`框架
**学习目标:**
1. 熟悉 LangChain核心组件
2. 熟悉 LangChain的使用方式
3. 熟悉 `LangChain`各个开发组件

### 一. 简介
`LangChain` 是⼀个⽤于开发由⼤型语⾔模型（LLMs）驱动的应⽤程序的框架。
官⽅⽂档：[https://reference.langchain.com/python/langchain/](https://reference.langchain.com/python/langchain/)
中文文档: [https://langchain.ichuangpai.com/](https://langchain.ichuangpai.com/)
`LangChain`简化了LLM应用程序生命周期的各个阶段：
开发阶段：使用`LangChain`的开源构建块和组件构建应用程序，利用第三方集成和模板快速启动。
生产化阶段：使用`LangSmith`检查、监控和评估您的链，从而可以自信地持续优化和部署。
部署阶段：使用`LangServe`将任何链转化为API。
### 1. 发展历史
`LangChain` 由 **Harrison Chase** 于 2022 年 10 月创建，他目前担任 `LangChain Inc.`的 CEO。
### 1.1 创建初衷
```plain text
在 2022 年底，Harrison Chase 观察到开发者在构建 LLM 应用时面临一个普遍问题：**大量的重复性工作**。开发者们都在编写类似的“胶水代码”来连接模型与数据源。

为了解决这个问题，他创建了 `LangChain`，核心理念是**“可组合性 (Composability)”**——将模型、提示词、索引和工具抽象为标准组件，让开发者能够通过组合这些组件来快速构建应用。
```
### 1.2 版本演进历史
`LangChain` 的发展经历了从快速验证到架构稳定的完整过程。截至目前，项目已发布至 v1.0 正式版。
- 阶段一：概念验证与功能积累 (v0.0.x)**时间跨度**：2022.10 - 2023.12
- **状态**：项目处于早期快速迭代阶段。
- **特点**：
    - **功能集成**：集成了当时市场上几乎所有的主流模型和工具。
    - **单体架构**：所有功能代码都包含在一个包中。
    - **不稳定性**：API 变动频繁，主要用于原型开发和概念验证。
- 阶段二：架构分层与标准化 (v0.1.0)**发布时间**：2024.01
- **核心变化**：这是 LangChain 的首个架构稳定版本。
- **技术细节**：
    - **架构拆分**：代码库被拆分为 `langchain-core`（核心协议）、`langchain-community`（社区集成）和 `langchain`（编排层）。
    - **LCEL 引入**：正式确立 **LangChain Expression Language (LCEL)** 为标准开发范式，支持流式传输和异步操作。
    - **向后兼容**：官方开始承诺核心 API 的稳定性。
- 阶段三：生态解耦与性能优化 (v0.2.0 - v0.3.0)
**发布时间**：2024.05 (v0.2) / 2024.09 (v0.3)
- **核心变化**：重点在于解决依赖冲突和提升运行效率。
- **技术细节**：
- **生态解耦 (v0.2)**：将 OpenAI、Anthropic 等合作伙伴的集成包独立发布（如 `langchain-openai`），不再绑定在主包中，减轻了安装体积和依赖冲突。
- **底层升级 (v0.3)**：全面适配 **Pydantic v2**，显著提升了数据验证和序列化的性能，增强了类型安全性。
- 阶段四：企业级稳定版 (v1.0.0)**发布时间**：2025.10
- **核心变化**：首个主要版本 (Major Release)，标志着框架进入成熟期。
- **技术细节**：
    - **长期稳定 (LTS)**：核心 API 锁定，不再进行破坏性更新，满足企业级生产环境的稳定性要求。
    - **LangGraph 1.0**：同步发布 LangGraph 1.0 正式版。这确立了**“图 (Graph)”**结构作为复杂智能体（Agent）编排的标准架构，取代了早期的线性链式架构。
    - **文档体系重构**：提供了结构更清晰、以用例为导向的官方文档。

### 2. `Langchain`的核心组件
![[1769758876179-b3ed7956-778b-4479-be69-ea7a577dc735.png]]
- 模型（Models）：包含各大语言模型的LangChain接口和调用细节，以及输出解析机制。
- 嵌入 （Embeddings）：为检索增强生成（RAG）提供基础支持
- 代理（Agents）：另一个`LangChain`中的核心机制，通过“代理”让大模型自主调用外部工具和内部工具，使智能Agent成为可能。
- 工具 (Tools) : 赋予大模型与外部世界交互的能力。工具可以是搜索引擎、计算器、数据库连接，或者是自定义的 API 接口。
- 中间件 (Middleware) : 在 LangChain 的 Agent 体系中，Middleware 是一种**拦截器机制**，允许开发者在 Agent 执行循环的各个关键节点插入自定义逻辑。
- 消息（Messages): 标准化对话数据结构，确保不同模型间的兼容性

### 3. 开源第三方库
![[1769758876253-8ed3c453-0e89-48c7-abec-fc70d1810141.png]]
- `langchain-core` ：基础抽象和LangChain表达式语言
- `langchain-community` ：第三方集成。合作伙伴包（如langchain-openai、langchain-anthropic等），一些集成已经进一步拆分为自己的轻量级包，只依赖于langchain-core
- `langchain` ：构成应用程序认知架构的模型、代理和检索策略
- `langgraph`：通过将步骤建模为图中的边和节点，使用 LLMs 构建健壮且有状态的多参与者应用程序
- `langserve`：将 LangChain 链部署为 REST API
- `LangSmith`：一个开发者平台，可让您调试、测试、评估和监控LLM应用程序，并与LangChain无缝集成

> 注意: `Langchain`开发我们一般说的是他的整个生态

### 3.1 `langchain-core`核心功能
`langchain-core` 是 `LangChain` 框架的基石，它包含了最基础、最稳定且与具体模型供应商无关的核心抽象与接口。

| 功能模块 | 核心功能介绍 |
| --- | --- |
| **基础抽象 (**`Runnable`**)** | 为所有组件（模型、链、工具）提供统一的调用接口（`invoke`/`batch`/`stream`）和声明式组合方式（使用 `｜` 管道符）。 |
| **消息系统 (**`BaseMessage`**)** | 定义了 `HumanMessage`、`AIMessage` 等标准化消息类，是框架与LLM交互的通用数据结构。 |
| **提示模板 (**`BasePromptTemplate`**)** | 作为所有提示模板的基类，负责将用户输入和上下文动态格式化为发送给模型的最终提示文本。 |
| **输出解析 (**`BaseOutputParser`**)** | 提供将模型生成的原始文本或消息，转换为结构化数据（如JSON、Python对象）的标准方法。 |
| **文档处理 (**`Document`**)** | 表示一个带有元数据（如来源）的文本块，是检索与向量数据库操作中的基本数据单元。 |
| **模型抽象 (**`BaseChatModel`**)** | 所有聊天模型的抽象基类，定义了与LLM交互的核心协议，确保不同供应商的模型有一致的调用方式。 |
| **回调处理 (**`BaseCallbackHandler`**)** | 提供回调处理器接口，允许在应用执行的关键节点插入自定义逻辑，用于日志、流式输出或监控。 |
| **结构化输出 (**`with_structured_output`**)** | 核心功能方法。允许直接要求语言模型返回一个符合预定Pydantic模型或JSON Schema的强类型对象。 |
| **缓存接口 (**`BaseCache`**)** | 定义了模型调用缓存的通用接口，支持多种后端，用于提升响应速度并降低重复调用成本。 |

新版本`langchain1.0`架构图
![[1769758876340-c42392dd-7b58-41ab-9306-e2fa036ea41d.png]]
老版本`langchain0.3`架构图
![[1769758876404-8f4253c1-f243-4e9a-a751-8e58099e6547.png]]
### 4. `LangChain`基本使用
- 模块安装

```plain text
# 安装指定版本的LangChain
pip install langchain==1.1.0  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install langchain-openai==1.1.0  -i https://pypi.tuna.tsinghua.edu.cn/simple
```
### 4.1模型调用
- 通过`LangChain`的接口来调用`OpenAI`对话

```plain text
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

load_dotenv()

llm = ChatOpenAI(api_key=os.getenv("api_key"),
                 base_url=os.getenv("base_url"),
                 model_name="qwen-plus")

# 直接提供问题，并调用llm
response = llm.invoke("什么是大模型？")
print(response)
print("=" * 50)
print(response.content)
```
### 4.2 向量存储
- 使用一个简单的本地向量存储 FAISS，首先需要安装它

```plain text
pip install faiss-cpu
pip install langchain_community
pip install dashscope
```
```plain text
import os
from langchain_community.document_loaders import WebBaseLoader
import bs4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化 WebBaseLoader
loader = WebBaseLoader(
    'https://www.gov.cn/zhengce/content/202510/content_7043916.htm',
    bs_kwargs=dict(parse_only=bs4.SoupStrainer(id='UCAP-CONTENT'))
)
docs = loader.load()

# 分割文档
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
)
documents = text_splitter.split_documents(docs)
print(f"总文档数量: {len(documents)}")

# 初始化 DashScope 嵌入模型
embeddings = DashScopeEmbeddings(
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="text-embedding-v4",
)

# 初始化 FAISS 索引（第一次循环）
vector = None
batch_size = 10

# 分批处理文档
for i in range(0, len(documents), batch_size):
    batch_docs = documents[i:i + batch_size]
    print(f'第{i // batch_size + 1}批次 文档数量: {len(batch_docs)}')

    # 第一批：创建新的 FAISS 索引
    if i == 0:
        vector = FAISS.from_documents(batch_docs, embeddings)
    # 后续批次：将新文档添加到现有索引
    else:
        new_vector = FAISS.from_documents(batch_docs, embeddings)
        vector.merge_from(new_vector)  # 合并新索引到现有索引


vector.save_local("faiss_index")
print("FAISS 索引已保存到 faiss_index 文件夹")
```
### 4.3 RAG+Langchain
> 基于外部知识，增强大模型回复

```plain text
import os
# 0.3版本能进行导入 替换导入方式
# from langchain.chains.combine_documents import create_stuff_documents_chain
# langchain_classic 提供向下兼容模块
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from dotenv import load_dotenv

# 加载环境变量（用于 LLM 的 API 密钥）
load_dotenv()

# 创建嵌入模型
embeddings = DashScopeEmbeddings(
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    model='text-embedding-v4'
)
# 加载本地 FAISS 索引
save_path = "faiss_index"

vector_store = FAISS.load_local(
    folder_path=save_path,
    embeddings=embeddings,
    allow_dangerous_deserialization=True  # 允许加载 pickle 文件（仅限可信文件）
)


# 创建提示模板
prompt = ChatPromptTemplate.from_template("""仅根据提供的上下文回答以下问题:

<context>
{context}
</context>

问题: {input}""")

# 创建 LLM 连接（继续使用阿里云 qwen-plus）
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),  # 确保环境变量名为 DASHSCOPE_API_KEY
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)

# 创建文档组合链
# langchain_core\prompts\chat.py可以看到提示词拼接
# format_messages 方法拼接提示词
document_chain = create_stuff_documents_chain(llm, prompt)

# 创建检索器
retriever = vector_store.as_retriever(search_kwargs={"k": 3})  # 限制检索 3 个文档

# 创建检索链
# 在langchain_community\vectorstores\faiss.py 可以查看向量检索的实现
# similarity_search_with_score_by_vector 是检索的方法  return docs[:k]
retrieval_chain = create_retrieval_chain(retriever, document_chain)

# 调用检索链并获取回答
# openai\resources\chat\completions\completions.py
# create方法中 self._post()  调用模型请求的api
response = retrieval_chain.invoke({"input": "密云水库水源保护条例什么时候执行"})

print("\n回答:", response["answer"])
```
### 二. 提示模板
可以把对模型的使用过程拆解成三块: 输入提示(Format)、调用模型(Predict)、输出解析(Parse)
- 1.提示模板: `LangChain-core`的模板允许动态选择输入，根据实际需求调整输入内容，适用于各种特定任务和应用。
- 2.语言模型: `LangChain` 提供通用接口调用不同类型的语言模型，提升了灵活性和使用便利性。
- 3.输出解析: 利用`LangChain-core` 的输出解析功能，精准提取模型输出中所需信息，避免处理冗余数据，同时将非结构化文本转换为可处理的结构化数据，提高信息处理效率。

这三块形成了一个整体，在LangChain中这个过程被统称为Model I/O。针对每块环节，LangChain都提供了模板和工具，可以帮助快捷的调用各种语言模型的接口
![[1769758876473-93d5ab6c-dcff-4f59-a399-15b7e549faef.png]]
> 很多用户可能对大模型使用的不熟练,那么我们给了他模版他只需要填关键字就行

`PromptTemplates` 是`LangChain-core`中的一个概念，通过接收原始用户输入，并返回一个准备好传递给语言模型的信息（即提示词 prompt）
通俗点说，prompt template 是一个模板化的字符串，可以用来生成特定的提示（prompts）。你可以将变量插入到模板中，从而创建出不同的提示。这对于重复生成相似格式的提示非常有用，尤其是在自动化任务中
### 1 `LangChain-core`提示模板
4. 清晰易懂的提示: 提高提示文本的可读性，使其更易于理解，尤其是在处理复杂或涉及多个变量的情况下。
5. 增强可重用性: 使用模板，可以在多个地方重复使用，简化代码，无需重复构建提示字符串。
6. 简化维护: 使用模板后，如果需要更改提示内容，只需修改模板，无需逐个查找所有用到该提示的地方。
7. 智能处理变量: 模板可以自动处理变量的插入，无需手动拼接字符串。
8. 参数化生成: 模板可以根据不同的参数生成不同的提示，有助于个性化文本生成。

### 2. 类型
9. LLM提示模板 `PromptTemplate`：常用的String提示模板
10. 聊天提示模板 `ChatPromptTemplate`： 常用的Chat提示模板，用于组合各种角色的消息模板，传入聊天模型。消息模板包括：`ChatMessagePromptTemplate`、`HumanMessagePromptTemplate`、`AIlMessagePromptTemplate`、`SystemMessagePromptTemplate`等
11. 样本提示模板 `FewShotPromptTemplate`：通过示例来教模型如何回答
12. 部分格式化提示模板：提示模板传入所需值的子集，以创建仅期望剩余值子集的新提示模板。
13. 管道提示模板 PipelinePrompt： 用于把几个提示组合在一起使用。
14. 自定义模板：允许基于其他模板类来定制自己的提示模板。
- 使用的模块

```plain text
# langchain03版本提供的 PromptTemplate导入方式
# from langchain.prompts.prompt import PromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import (
    ChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
```
### 1.3 String提示模板
```plain text
# 导入LangChain中的OpenAI模型接口
from langchain_openai import ChatOpenAI
# 导入LangChain中的提示模板
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

# 创建模型实例
model = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                   base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                   model='qwen-plus')

prompt = PromptTemplate(
    template="您是一位专业的程序员。\n对于信息 {text} 进行简短描述"
)

# 输入提示
input = prompt.format(text="大模型langchain")

# 得到模型的输出
output = model.invoke(input)
# output = model.invoke("您是一位专业的程序员。对于信息 langchain 进行简短描述")

# 打印输出内容
print(output.content)
```
### 1.4 **聊天提示模板**
- PromptTemplate创建字符串提示的模板。默认情况下，使用Python的str.format语法进行模板化。而ChatPromptTemplate是创建聊天消息列表的提示模板。
- 创建一个ChatPromptTemplate提示模板，模板的不同之处是它们有对应的角色。

```plain text
from langchain_core.prompts.chat import ChatPromptTemplate
# 导入LangChain中的ChatOpenAI模型接口
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

template = "你是一个数学家，你可以计算任何算式"
# template = "你是一个翻译专家,擅长将 {input_language} 语言翻译成 {output_language}语言."
human_template = "{text}"

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    ("human", human_template),
])
# print(chat_prompt)


# 创建模型实例
model = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                   base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                   model='qwen-plus')
# 输入提示
messages = chat_prompt.format_messages(text="我今年18岁，我的舅舅今年38岁，我的爷爷今年72岁，我和舅舅一共多少岁了？")
# print(messages)
# messages = chat_prompt.format_messages(input_language="英文", output_language="中文", text="I love Large Language Model.")
print(messages)
# 得到模型的输出
output = model.invoke(messages)
# 打印输出内容
print(output.content)
```
- LangChain提供不同类型的MessagePromptTemplate.最常用的是AIMessagePromptTemplate、 SystemMessagePromptTemplate和HumanMessagePromptTemplate，分别创建人工智能消息、系统消息和人工消息。

```plain text
# 导入聊天消息类模板
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 系统模板的构建
system_template = "你是一个翻译专家,擅长将 {input_language} 语言翻译成 {output_language}语言."
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

# 用户模版的构建
human_template = "{text}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

# 组装成最终模版
prompt_template = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

# 格式化提示消息生成提示
prompt = prompt_template.format_prompt(input_language="英文", output_language="中文",
                                       text="I love Large Language Model.").to_messages()
# 打印模版
print("prompt:", prompt)

# 创建模型实例
model = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                   base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                   model='qwen-plus')
# 得到模型的输出
result = model.invoke(prompt)
# 打印输出内容
print("result:", result.content)
```
### 1.5 少量样板提示
基于LLM模型与聊天模型，可分别使用`FewShotPromptTemplate`或`FewShotChatMessagePromptTemplate`，两者使用基本一致
创建示例集：创建一些提示样本，每个示例都是一个字典，其中键是输入变量，值是输入变量的值
```plain text
# 创建示例
examples = [
    {"input": "2+2", "output": "4", "description": "加法运算"},
    {"input": "5-2", "output": "3", "description": "减法运算"},
]
```
- 创建提示模板

```plain text
# 创建提示模板，配置一个提示模板，将一个示例格式化为字符串
prompt_template = "你是一个数学专家,算式： {input} 值： {output} 使用： {description} "

# 这是一个提示模板，用于设置每个示例的格式
prompt_sample = PromptTemplate.from_template(prompt_template)
```
- 创建FewShotPromptTemplate对象

```plain text
prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=prompt_sample,
    suffix="你是一个数学专家,算式: {input}  值: {output} ",
    input_variables=["input", "output"]
)
print(prompt.format(input="2*5", output="10"))  # 你是一个数学专家,算式: 2*5  值:
```
- 初始化大模型，然后调用

```plain text
# 创建提示模板，配置一个提示模板，将一个示例格式化为字符串
import os

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
import langchain_openai
load_dotenv()
# 创建示例
examples = [
    {"input": "2+2", "output": "4", "description": "加法运算"},
    {"input": "5-2", "output": "3", "description": "减法运算"},
]
prompt_template = "你是一个数学专家,算式： {input} 值： {output} 使用： {description} "

# 这是一个提示模板，用于设置每个示例的格式
prompt_sample = PromptTemplate.from_template(prompt_template)

prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=prompt_sample,
    # 告诉大模型要按照这个格式输出description
    suffix="""你是一个数学专家,请计算： {input} 值： {output} """,
    input_variables=["input", "output"],
)
# print(prompt.format(input="2*5", output="10"))  # 你是一个数学专家,算式: 2*5  值:
#
# print(prompt_sample)
print('-' * 50)

llm = langchain_openai.ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                                  base_url=os.getenv("DASHSCOPE_BASE_URL"),
                                  model_name='qwen-plus')
result = llm.invoke(prompt.format(input="2*5", output="10"))
print(result.content)  # 使用: 乘法运算
```
### 三.`LangChain`的Model
### 2. Model 模型
LangChain支持的模型有三大类
- 1.大语言模型（LLM） ，也叫Text Model，这些模型将文本字符串作为输入，并返回文本字符串作为输出。
- 2.聊天模型（Chat Model），主要代表Open AI的ChatGPT系列模型。这些模型通常由语言模型支持，但它们的API更加结构化。具体来说，这些模型将聊天消息列表作为输入，并返回聊天消息。
- 3.文本嵌入模型（Embedding Model），这些模型将文本作为输入并返回浮点数列表，也就是Embedding。

聊天模型通常由大语言模型支持，但专门调整为对话场景。重要的是，它们的提供商API使用不同于纯文本模型的接口。输入被处理为聊天消息列表，输出为AI生成的消息。
### 2.1 各个库调用模型的区别
`langchain`提供了很多种调用模型的方法,有`langchain`本身的调用方法,`langchain-openai`调用以及模型厂商本身调用库
```plain text
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

# langchain自己封装的模型调用方法
# qwen 目前不支持调用  model_provider="openai"的作用千问提供了OpenAI兼容的API
llm = init_chat_model(
    "deepseek-reasoner",
    # model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0
)
response = llm.invoke("什么是大模型？")
print(response)
print("=" * 50)
print(response.content)


from langchain_openai import ChatOpenAI

# 通过langchain_openai调用千问模型
# 市面模型兼容OpenAI能让开发者无缝切换
llm = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model_name="deepseek-reasoner"
)

# 直接提供问题，并调用llm
response = llm.invoke("什么是大模型？")
print(response)
print("=" * 50)
print(response.content)



# 用模型厂商自己封装的模型调用方法的优势, 调用返回的结果会更加细腻
from langchain_deepseek import ChatDeepSeek
llm = ChatDeepSeek(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model_name="deepseek-reasoner"
)

response = llm.invoke("什么是大模型？")
print(response)
print("=" * 50)
print(response.content)
```
### 2.1 大语言模型LLM
LangChain的核心组件是大型语言模型（LLM），它提供一个标准接口以字符串作为输入并返回字符串的形式与多个不同的LLM进行交互。这一接口旨在为诸如OpenAI、Hugging Face等多家LLM供应商提供标准化的对接方法。
文本补全-千问不支持
```plain text
from langchain_community.llms import Tongyi
from dotenv import load_dotenv
import os

load_dotenv()


# LLM纯文本补全模型
llm = Tongyi(api_key=os.getenv("DASHSCOPE_API_KEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model='qwen-plus')

text = "我的真的好想（帮我补全这个文本）"
res = llm.invoke(text)
print(res)
```
### 2.2 聊天模型
聊天模型是LangChain的核心组件，使用聊天消息作为输入并返回聊天消息作为输出。
LangChain有一些内置的消息类型
- SystemMessage:用于启动 AI 行为，通常作为输入消息序列中的第一个传递。
- HumanMessage:表示来自与聊天模型交互的人的消息。
- AIMessage:表示来自聊天模型的消息。这可以是文本，也可以是调用工具的请求。

```plain text
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

load_dotenv()

human_text = "你好啊"
system_text = "你是一个强大的助手，你的名字叫0713"
# 聊天模型
chat_model = ChatTongyi(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",  # 此处以qwen-plus为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
)

messages = [HumanMessage(content=human_text)]
# 聊天模型支持多个消息作为输入
# messages = [SystemMessage(content=system_text), HumanMessage(content=human_text)]

res = chat_model.invoke(messages)
print(res)
```
### 2.3 文本嵌入模型
Embedding类是一个用于与嵌入进行交互的类。有许多嵌入提供商（OpenAI、Cohere、Hugging Face等)- 这个类旨在为所有这些提供商提供一个标准接口。
```plain text


import os

from langchain_community.embeddings import DashScopeEmbeddings
from dotenv import load_dotenv

load_dotenv()
# 初始化 DashScopeEmbeddings实例
embeddings = DashScopeEmbeddings(dashscope_api_key=os.getenv("api_key"), model='text-embedding-v3')


# 获取文本嵌入向量
text = '大模型'

# 嵌入文档 把文档内容转换为向量 他支持多个文档列表形式
doc_res = embeddings.embed_documents([text])
print(doc_res)

# 嵌入查询  把问题嵌入向量  一般都是一个问题
res = embeddings.embed_query(text)
print(res)
```
- **调用HuggingFaceBgeEmbeddings**
- 国内的镜像地址：[https://hf-mirror.com/](https://hf-mirror.com/)
- 魔塔： [https://www.modelscope.cn/models/maidalun/bce-embedding-base_v1](https://www.modelscope.cn/models/maidalun/bce-embedding-base_v1)

```plain text
# 安装模块
pip install sentence_transformers
```
- 下载modelscope Embedding的模型

```plain text
from modelscope import snapshot_download
# maidalun/bce-embedding-base_v1 模型名字   cache_dir：下载位置
# model_dir = snapshot_download('maidalun/bce-embedding-base_v1', cache_dir="D:\大模型\RAG_Project")
```
```plain text
# langchain_huggingface 加载huggingface模型
from langchain_huggingface import HuggingFaceEmbeddings

# 创建嵌入模型
model_name = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'

# 生成的嵌入向量将被标准化, 有助于向量比较
encode_kwargs = {'normalize_embeddings': True}

embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    encode_kwargs=encode_kwargs
)
text = "大模型"
query_result = embeddings.embed_query(text)
print(query_result[:5])
```
- 通过Hugging Face官方包的加持，开发小伙伴们通过简单的api调用就能在langchain中轻松使用Hugging Face上各类流行的开源大语言模型以及各类AI工具
- 访问：HuggingFace(`https://huggingface.co/settings/tokens`)，在个人设置中心，创建一个API Token

```plain text
import os

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from dotenv import load_dotenv
load_dotenv()

ENDPOINT_URL = "Qwen/Qwen3-8B"
# ENDPOINT_URL = "deepseek-ai/DeepSeek-R1"
HF_TOKEN = os.getenv('HF_TOKEN')

llm = HuggingFaceEndpoint(
    endpoint_url=ENDPOINT_URL,
    # max_new_tokens=30,  限制生成的最大 token 数量为 30 个
    typical_p=0.95,     # 控制输出文本的多样性，避免生成太过常见或太过罕见的 tokens
    temperature=0.01,
    repetition_penalty=1.03,    # 对重复出现的 tokens 施加惩罚，避免生成重复的内容
    huggingfacehub_api_token=HF_TOKEN
)
# 生成key时需要把权限都点上
chat_model = ChatHuggingFace(llm=llm)
resp = chat_model.invoke("解释 prompt 是什么？")
print(resp)
```
### 2.4 输出解析器
输出解析器负责获取 LLM 的输出并将其转换为更合适的格式。借助`LangChain-core`的输出解析器重构程序，使模型能够生成结构化回应，并可以直接解析这些回应
`LangChain-core`有许多不同类型的输出解析器
- CSV解析器:`CommaSeparatedListOutputParser`,模型的输出以逗号分隔，以列表形式返回输出
- JSON解析器:JsonOutputParser,确保输出符合特定JSON对象格式。
- XML解析器:XMLOutputParser,允许以流行的XML格式从LLM获取结果

```plain text
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
# 创建解析器
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser, XMLOutputParser
from langchain_classic.chains import LLMChain  # 新增：导入 LLMChain 用于非 LCEL 链式调用
from dotenv import load_dotenv
import os

load_dotenv()

# 初始化语言模型
model = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
)

# output_parser = StrOutputParser()
# output_parser = JsonOutputParser()
xml_parser = XMLOutputParser()

# 提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的程序员"),
    ("user", "{input}")
])

# 使用 LLMChain 构建链（非 LCEL 方式）
chain = LLMChain(
    llm=model,
    prompt=prompt,
    output_parser=xml_parser  # 指定输出解析器
)

res = chain.invoke({"input": "langchain是什么? 使用xml格式输出"})
# res = chain.invoke({"input": "langchain是什么? 问题用question 回答用ans 返回一个JSON格式"})
# res = chain.invoke({"input": "大模型中的langchain是什么?"})
print(res)
```
### 四. Langchain数据检索
在前面课程中我们已经讲了大模型存在的缺陷：数据不实时，缺少垂直领域数据和私域数据等。解决这些缺陷的主要方法是通过检索增强生成（RAG）。首先检索外部数据，然后在执行生成步骤时将其传递给LLM。
LangChain为RAG应用程序提供了从简单到复杂的所有构建块，本文要学习的数据检索（Retrieval）模块包括与检索步骤相关的所有内容，例如数据的获取、切分、向量化、向量存储、向量检索等模块（见下图）。
![[1769758876556-4dae195a-ccf9-4612-879c-08d8b34b8ef8.png]]
### 1. Document loaders 文档加载模块
LangChain封装了一系列类型的文档加载模块，例如PDF、CSV、HTML、JSON、Markdown、File Directory等。下面以PDF文件夹在为例看一下用法，其它类型的文档加载的用法都类似。
### 1.1 加载本地文件
- LangChain加载PDF文件使用的是pypdf，先安装：

```plain text
python
复制代码
pip install pypdf
```
- 加载代码示例：

```plain text
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader(r"D:\python_project\AI_object\RAG备课\day02\财务管理文档.pdf")
pages = loader.load_and_split()

print(f"第0页：\n{pages[0]}")  ## 也可通过 pages[0].page_content只获取本页内容
```
- `langchain`加载Word文件

```plain text
pip install unstructured
# 官网:https://docs.unstructured.io/welcome
# 下载时需要开科学上网不然会报错File is not a zip file
# 如果报错开科学上网之后
# import nltk
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# 把nltk 重新加载
pip install python-doc
pip install python-docx
```
```python
# from langchain_community.document_loaders import PyPDFLoader
#
# loader = PyPDFLoader(r"D:\python_project\AI_object\RAG备课\day02\财务管理文档.pdf")
# pages = loader.load_and_split()
#
# print(f"第0页：\n{pages[0]}")  ## 也可通过 pages[0].page_content只获取本页内容


from langchain_community.document_loaders import UnstructuredWordDocumentLoader

# 指定要加载的Word文档路径
loader = UnstructuredWordDocumentLoader(r"D:\python_project\AI_object\RAG备课\day02\人事管理流程.docx")
print(loader)

# 加载文档并分割成段落或元素
documents = loader.load()
print(documents)
# 输出加载的内容
for doc in documents:
    print(doc.page_content)

# 需要科学上网需要下载一个包 punkt_tab
```
### 1.2 加载在线PDF文件
- LangChain也能加载在线的PDF文件。
- 在开始之前，你可能需要安装以下的Python包：

```plain text
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple unstructured
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pdf2image
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opencv-python
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple unstructured-inference
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pikepdf
```
- 代码示例：

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("https://arxiv.org/pdf/2302.03803.pdf")
data = loader.load()
print(f"第0页：\n{data[0].page_content}")  # 也可通过 pages[0].page_content只获取本页内容
# 需要注意科学上网
```
### 2. 文档切分模块
- LangChain提供了许多不同类型的文本切分器，具体见下表：

![[1769758876629-22f634b7-2186-4799-8160-d0f8f8b09532.png]]
这里以Recursive为例展示用法。RecursiveCharacterTextSplitter是LangChain对这种文档切分方式的封装，里面的几个重点参数：
- chunk_size：每个切块的token数量
- chunk_overlap：相邻两个切块之间重复的token数量

```plain text
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = PyPDFLoader(r"D:\python_project\vip_LLM\RAG\RAG-02\day04\财务管理文档.pdf")
pages = loader.load_and_split()
# print(f"第0页：\n{pages[0].page_content}")
# print(pages)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=100,
    length_function=len,
)
# [pages[1].page_content]
# print([page.page_content for page in pages if pages])
paragraphs = text_splitter.create_documents([page.page_content.replace('\n', '').replace(' ', '') for page in pages if pages])
print(paragraphs)
for para in paragraphs:
    print(para.page_content)
    print('-------', len(para.page_content))
```
- 以上示例程序将chunk_overlap设置为100，看下运行效果，可以看到上一个chunk和下一个chunk会有一部分的信息重合，**这样做的原因是尽可能地保证两个chunk之间的上下文关系**：这里提供了一个可视化展示文本如何分割的工具，感兴趣的可以看下。
- 工具网址：[http://chunkviz.up.railway.app/](http://chunkviz.up.railway.app/)

### 3. 文本向量化模型封装
- LangChain对一些文本向量化模型的接口做了封装，例如OpenAI, Cohere, Hugging Face等。 向量化模型的封装提供了两种接口，一种针对文档的向量化`embed_documents`，一种针对句子的向量化`embed_query`。
- 示例代码：
- 文档的向量化`embed_documents`，接收的参数是字符串数组

```plain text
from langchain_community.embeddings import DashScopeEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

embeddings_model = DashScopeEmbeddings(dashscope_api_key=os.getenv('api_key'))
embeddings = embeddings_model.embed_documents(
    [
        "Hi there!",
        "Oh, hello!",
        "What's your name?",
        "My friends call me World",
        "Hello World!"
    ]
)
print(len(embeddings), len(embeddings[0]), len(embeddings[1]))
##运行结果 (5, 1536)
```
- 句子的向量化`embed_query`，接收的参数是字符串

```plain text
from langchain_community.embeddings import DashScopeEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

embeddings_model = DashScopeEmbeddings(dashscope_api_key=os.getenv('api_key'))

embedded_query = embeddings_model.embed_query("What was the name mentioned in the conversation?")
print(embedded_query[:5])
```
### 4. 向量存储
- 将文本向量化之后，下一步就是进行向量的存储。 这部分包含两块：一是向量的存储。二是向量的查询。
- 官方提供了三种开源、免费的可用于本地机器的向量数据库示例（chroma、FAISS、 Lance）。因为我在之前RAG的文章中用的chroma数据库，所以这里还是以这个数据库为例。

```plain text
import os

from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()
# 读取文件
loader = PyPDFLoader(r"D:\python_project\vip_LLM\RAG\RAG-02\day04\财务管理文档.pdf")
pages = loader.load_and_split()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=100,
    length_function=len,
    add_start_index=True,
)

# 将数据进行切割成块
paragraphs = text_splitter.create_documents([page.page_content for page in pages if pages])
print(paragraphs)
# 创建嵌入模型
model_name = r'D:\LLM\Local_model\BAAI\bge-large-zh-v1___5'
embeddings = HuggingFaceEmbeddings(model_name=model_name)
# 创建chroma数据库，并将文本数据个向量化的数据存入
# db = Chroma.from_documents(paragraphs, embeddings, persist_directory="chroma_db")  # 一行代码搞定

db = Chroma(persist_directory="chroma_db", embedding_function=embeddings)


# 在数据库中进行搜索
query = "会计核算基础规范"
docs = db.similarity_search(query)  # 一行代码搞定
for doc in docs:
    print(f"{doc}\n-------\n")
```
### 5. Retrievers 检索器
- 检索器是在给定非结构化查询的情况下返回相关文本的接口。它比Vector stores更通用。检索器不需要能够存储文档，只需要返回（或检索）文档即可。Vector stores可以用作检索器的主干，但也有其他类型的检索器。**检索器接受字符串查询作为输入，并返回文档列表作为输出**。
- 检索器（Retrievers） 是一个用于从文档集合中检索最相关文档或信息片段的关键组件。它们通常与向量存储（Vector Stores）结合使用，通过计算查询向量与存储中的文档向量之间的相似度来实现高效的语义搜索。简单来说，检索器帮助你找到与特定查询最相关的文档。
- LangChain检索器提供的检索类型如下：

![[1769758876685-8e08f033-4030-44ce-9745-42899647284b.png]]
```plain text
import os
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建嵌入模型
model_name = r"D:\LLM\Local_model\BAAI\bge-large-zh-v1___5"

embeddings = HuggingFaceEmbeddings(model_name=model_name)


# 加载现有 Chroma 数据库
persist_directory = "./chroma_db"

db = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings
)
print(f"成功加载 Chroma 数据库从 {persist_directory}")

# 实例化检索器
retriever = db.as_retriever(search_kwargs={"k": 4})  # 设置返回文档数量

# 获取问题相关文档
query = "会计核算基础规范"

docs = retriever.invoke(query)
for i, doc in enumerate(docs, 1):
    print(f"结果 {i}:\n{doc.page_content}")
```
### 五. Langchain之Chain链
- 为开发更复杂的应用程序，需要使用Chain来链接LangChain中的各个组件和功能，包括模型之间的链接以及模型与其他组件之间的链接
- 链在内部把一系列的功能进行封装，而链的外部则又可以组合串联。 链其实可以被视为LangChain中的一种基本功能单元。
- API地址：[https://python.langchain.com/api_reference/langchain/chains.html](https://python.langchain.com/api_reference/langchain/chains.html)

### 1. 链的基本使用
- LLMChain是最基础也是最常见的链。LLMChain结合了语言模型推理功能，并添加了PromptTemplate和Output Parser等功能，将模型输入输出整合在一个链中操作。
- 它利用提示模板格式化输入，将格式化后的字符串传递给LLM模型，并返回LLM的输出。这样使得整个处理过程更加高效和便捷。

### 1.1 未使用Chain
```plain text
# 导入LangChain中的提示模板
from langchain_core.prompts import PromptTemplate
# 导入LangChain中的OpenAI模型接口
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
import os

# 原始字符串模板
template = "桌上有{number}个苹果，四个桃子和 3 本书，一共有几个水果?"

# 创建LangChain模板
prompt_temp = PromptTemplate.from_template(template)

# 根据模板创建提示
prompt = prompt_temp.format(number=2)

model = ChatOpenAI(api_key=os.getenv("api_key"),
                   base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                   model='qwen-plus',
                   temperature=0)
# 传入提示，调用模型返回结果
result = model.invoke(prompt)
print(result)
```
### 1.2 **使用Chain**
```plain text
from langchain_classic.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 原始字符串模板
template = "桌上有{number}个苹果，四个桃子和 3 本书，一共有几个水果?"

# 创建模型实例
llm = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model='qwen-max',
                 temperature=0)

# 创建LLMChain
llm_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate.from_template(template)
)

# 调用LLMChain，返回结果
result = llm_chain.invoke({"number": 2})
print(type(result))
print(result['text'])
```
### 1.3 **使用表达式语言 (LCEL)**
- LangChain Expression Language 是一种以声明式方法，轻松地将链或组件组合在一起的机制。通过利用管道操作符，构建的任何链将自动具有完整的同步、异步和流式支持。
- LangChain 表达式语言（LangChain Expression Language，简称 LCEL）是一种专为链组件（Chain）编排设计的声明式语法，其核心价值在于以统一的方式实现从简单到复杂的 AI 应用构建。从设计之初，LCEL 就致力于消除原型开发与生产部署间的鸿沟 —— 无论是基础的 “提示词 + LLM” 单链结构，还是包含 100 + 步骤的复杂工作流，均可通过同一套语法实现，无需修改代码逻辑。
- python实现管道调用

```plain text

from pipe import select

numbers = [1,2,3]
aa = list(numbers | select(lambda x: x*2))
print(aa)
```
```plain text
class Chain():
    def __init__(self, value):
        self.value = value


    def __or__(self, other):
        # 调用 | 运算符  触发的魔法方法
        return other(self.value)

def prompt(text):
    return "请求回答问题:{}".format(text)

aa = Chain('人工智能是什么?')

res = aa | prompt
print(res)
```
- 普通调用

![[1769758876754-570df306-e713-4391-a113-b14451b9287e.png]]
```plain text
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os

load_dotenv()

# 创建提示词
prompt = ChatPromptTemplate.from_template("tell me a short joke about {topic}")

# 创建llm模型
model = ChatOpenAI(api_key=os.getenv("api_key"),
                   base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                   model="qwen-plus")
# 创建输出解释器
output_parser = StrOutputParser()
# 使用chain链在一起
chain = prompt | model | output_parser
print(chain.invoke({"topic": "ice cream"}))
```
- 语言表达式语言(LCEL) 采用声明式[方法](https://en.wikipedia.org/wiki/Declarative_programming)从现有的 Runnable构建新的[Runnable](https://python.langchain.com/docs/concepts/runnables/)。

### 2. Runnable是什么？
- Runnable 接口是 `LangChain 0.2` 版本后推出的核心抽象层，旨在通过函数式编程模型统一各类 AI 组件的交互方式。它将语言模型（LLM）、链（Chain）、工具调用、数据处理等操作抽象为可组合的 “可运行单元”（Runnable），允许开发者以类似流水线（Pipeline）的方式编排复杂逻辑，而无需关注底层实现细节。

### 2.1 核心特性
![[1769758876874-b2872231-432e-4353-8e87-393ad781909f.png]]
### 2.2 主要实现类
- `LangChain` 中几乎所有核心组件都实现了 `Runnable` 接口

![[1769758877012-a58ac31d-6f5d-4dce-b4ac-b814d22bd85b.png]]
- [https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html#langchain_core.runnables.base.Runnable可以在这个网站中查询所有Runnable对应的方法](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html#langchain_core.runnables.base.Runnable%E5%8F%AF%E4%BB%A5%E5%9C%A8%E8%BF%99%E4%B8%AA%E7%BD%91%E7%AB%99%E4%B8%AD%E6%9F%A5%E8%AF%A2%E6%89%80%E6%9C%89Runnable%E5%AF%B9%E5%BA%94%E7%9A%84%E6%96%B9%E6%B3%95)

### 2.3 案例
![[1769758877094-3e52ce37-ad4e-4491-8839-3ce014b4ffc9.png]]
```plain text
from langchain_openai import ChatOpenAI
# from langchain.schema import SystemMessage
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.vectorstores import InMemoryVectorStore
# from langchain.schema.runnable import RunnableMap, RunnableBranch, RunnableLambda
from langchain_core.runnables import RunnableMap, RunnableBranch, RunnableLambda
# from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_tavily import TavilySearch
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()


class TravelQASystem:
    def __init__(self, openai_api_key, serpapi_api_key, embed_path):
        """初始化旅游问答系统核心组件"""

        # 初始化语言模型
        self.llm = ChatOpenAI(api_key=openai_api_key,
                              base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                              model="qwen-plus")

        # 初始化搜索工具
        self.search = TavilySearch(tavily_api_key=serpapi_api_key)

        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(model_name=embed_path)

        # 构建景点知识库
        self.attraction_data = [
            "故宫：北京地标，明清皇宫，开放时间8:30-17:00",
            "颐和园：皇家园林，昆明湖、长廊等景点",
            "八达岭长城：距离市区70公里，建议游览3-4小时"
        ]

        # 使用内存型向量存储类
        self.vector_store = InMemoryVectorStore.from_texts(
            self.attraction_data, self.embeddings, k=1
        )

    def setup_runnable_pipeline(self):
        """定义Runnable流程管道"""
        # 3.1 问题解析模块：识别地点与查询类型
        parse_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="你是旅游助手，需从用户问题中提取地点和查询类型（天气/景点介绍/行程规划）"),
            ("user", """问题：{user_question}请以JSON格式返回：{{"location": "地点", "type": "查询类型"}}""")
        ])
        parse_module = parse_prompt | self.llm | JsonOutputParser()  # Output JSON string

        # 3.2 并行数据获取：天气查询+景点信息检索
        weather_query = RunnableLambda(
            lambda x: self.search.invoke(f"{x['location']} 今日天气")
        )
        attraction_retrieval = (lambda x: x["location"]) | self.vector_store.as_retriever() | (
            lambda x: x[0].page_content)
        # RunnableMap：并行执行天气查询和景点检索
        data_acquisition = RunnableMap({
            "weather": weather_query,
            "attraction": attraction_retrieval,
            "location": (lambda x: x["location"])
        })

        # 3.3 回答生成模块：整合信息并格式化
        generate_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="你是专业旅游顾问，需结合景点信息和天气生成建议"),
            ("user", """地点：{location}
                景点信息：{attraction}
                天气情况：{weather}
                请生成1条行程建议，包含注意事项（如天气相关准备）""")
        ])
        generate_module = generate_prompt | self.llm | (lambda x: x.content.strip())

        """
        RunnableBranch实现
        RunnableBranch(
            (lambda x: 条件1, 执行的代码),
            (lambda x: 条件2, 执行的代码2),
            lambda x: {"location": x["location"], "attraction": attraction_retrieval.invoke(x)}
        )

        """
        # 3.4 全流程串联
        self.travel_qa_pipeline = (
            # 阶段1：解析问题
                parse_module
                | (lambda x: {"location": x["location"], "type": x["type"]})
                # 阶段2：并行获取数据（仅当查询类型为天气或行程时触发）
                # RunnableBranch：根据查询类型选择数据获取路径
                | RunnableBranch(
            (lambda x: "天气" in x["type"], data_acquisition),
            lambda x: {"location": x["location"], "attraction": attraction_retrieval.invoke(x)}
        )
                # 阶段3：生成回答
                | generate_module
        )

    def process_user_question(self, user_question):
        """处理用户提问并返回回答"""
        input_data = {"user_question": user_question}
        # try:
        response = self.travel_qa_pipeline.invoke(input_data)
        return response


# 示例用法
if __name__ == "__main__":
    # 替换为实际API密钥
    OPENAI_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    # https://www.tavily.com/
    SERPAPI_API_KEY = os.getenv("TAVILY_API_KEY")
    embed_path = r"D:\LLM\Local_model\BAAI\bge-large-zh-v1___5"

    # 初始化系统
    travel_qa = TravelQASystem(OPENAI_API_KEY, SERPAPI_API_KEY, embed_path)
    travel_qa.setup_runnable_pipeline()

    # 测试1：查询天气与景点建议
    question1 = "今天故宫的天气怎么样?"
    answer1 = travel_qa.process_user_question(question1)
    print(f"User Question: {question1}\nAI Answer: {answer1}\n")
```
### 3. 链的调用方式
- **通过invoke方法**

```plain text
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# 原始字符串模板
template = "桌上有{number}个苹果，四个桃子和 3 本书，一共有几个水果?"
prompt = PromptTemplate.from_template(template)

# 创建模型实例
llm = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model='qwen-plus',
                 temperature=0)

# 创建Chain
chain = prompt | llm

# 调用Chain，返回结果
result = chain.invoke({"number": "3"})
print(result)
```
- **通过batch方法(原apply方法)**:batch方法允许输入列表运行链，一次处理多个输入。

```plain text

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()


# 创建模型实例
template = PromptTemplate(
    input_variables=["role", "fruit"],
    template="{role}喜欢吃{fruit}?",
)

# 创建LLM
llm = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model='qwen-plus',
                 temperature=0)


llm_chain = template | llm

# 输入列表
input_list = [
    {"role": "猪八戒", "fruit": "人参果"}, {"role": "孙悟空", "fruit": "仙桃"}
]

# 调用LLMChain，返回结果
result = llm_chain.batch(input_list)
print(result[0].content)
print(result[1].content)
```
### 六. Agent代理
在LangChain框架中，Agents是一种利用大型语言模型（Large Language Models，简称LLMs）来执行任务和做出决策的系统
在 LangChain 的世界里，Agent 是一个智能代理，它的任务是听取你的需求（用户输入）和分析当前的情境（应用场景），然后从它的工具箱（一系列可用工具）中选择最合适的工具来执行操作
- 使用工具（Tool）：LangChain中的Agents可以使用一系列的工具（Tools）实现，这些工具可以是API调用、数据库查询、文件处理等，Agents通过这些工具来执行特定的功能。
- 推理引擎（Reasoning Engine）：Agents使用语言模型作为推理引擎，以确定在给定情境下应该采取哪些行动，以及这些行动的执行顺序。
- 可追溯性（Traceability）：LangChain的Agents操作是可追溯的，这意味着可以记录和审查Agents执行的所有步骤，这对于调试和理解代理的行为非常有用。
- 自定义（Customizability）：开发者可以根据需要自定义Agents的行为，包括创建新的工具、定义新的Agents类型或修改现有的Agents。
- 交互式（Interactivity）：Agents可以与用户进行交互，响应用户的查询，并根据用户的输入采取行动。
- 记忆能力（Memory）：LangChain的Agents可以被赋予记忆能力，这意味着它们可以记住先前的交互和状态，从而在后续的决策中使用这些信息。
- 执行器（Agent Executor）：LangChain提供了Agent Executor，这是一个用来运行代理并执行其决策的工具，负责协调代理的决策和实际的工具执行。

Agent代理的核心思想是使用语言模型来选择要采取的一系列动作。在链中，动作序列是硬编码的。
在代理中，语言模型用作推理引擎来确定要采取哪些动作以及按什么顺序进行。
因此，在LangChain中，Agent代理就是使用语言模型作为推理引擎，让模型自主判断、调用工具和决定下一步行动。
Agent代理像是一个多功能接口，能够使用多种工具，并根据用户输入决定调用哪些工具，同时能够将一个工具的输出数据作为另一个工具的输入数据。
`注意:在新版本当中langchain关于agent的创建都集成给了langgraph,目前这个内容作为了解`
### 1. Agent的基本使用
### 1.1 Tavily在线搜索
- 构建一个具有两种工具的代理：一种用于在线查找，另一种用于查找加载到索引中的特定数据。
- 在LangChain中有一个内置的工具，可以方便地使用Tavily搜索引擎作为工具。
- 访问Tavily（用于在线搜索）注册账号并登录，获取API 密钥
- TAVILY_API_KEY申请：[https://tavily.com/](https://tavily.com/)

```plain text
# 加载所需的库
import os
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
load_dotenv()

# 查询 Tavily 搜索 API 并返回 json 的工具
search = TavilySearch(tavily_api_key=os.getenv("TAVILY_API_KEY"))
# 执行查询
res = search.invoke("目前市场上苹果手机16的售价是多少？")
print(res)
```
- **创建检索器**
- 根据上述查询结果中的某个URL中，获取一些数据创建一个检索器。

```plain text
# 加载所需的库
import os

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

# 查询 Tavily 搜索 API 并返回 json 的工具
# search = TavilySearchResults()
# # 执行查询
# res = search.invoke("目前市场上苹果手机16的售价是多少？")
# print(res)


# 创建索引器根据上述查询的结果

# 加载HTML内容为一个文档对象
loader = WebBaseLoader("https://news.qq.com/rain/a/20240920A07Y5Y00")
# 读取文档
docs = loader.load()
# print(docs)

# 分割文档
documents = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)

# 向量化
vector = FAISS.from_documents(documents, DashScopeEmbeddings(dashscope_api_key=os.getenv('DASHSCOPE_API_KEY')))

# 创建检索器
retriever = vector.as_retriever()

# 测试检索结果
print(retriever.invoke("目前市场上苹果手机16的售价是多少？"))
```
- **得到工具列表**

```plain text
from langchain.tools.retriever import create_retriever_tool
# 创建一个工具来检索文档
retriever_tool = create_retriever_tool(
    retriever,
    "iPhone_price_search",
    "搜索有关 iPhone 16 的价格信息。对于iPhone 16的任何问题，您必须使用此工具！",
)

# 创建将在下游使用的工具列表
tools = [search, retriever_tool]
```
- 对接大模型
- 创建Agent,这里使用LangChain中一个叫OpenAI functions的代理，然后得到一个AgentExecutor代理执行器

```plain text
# 加载所需的库
import os

# from langchain import hub
from langsmith import Client

from langchain_tavily import TavilySearch
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools.retriever import create_retriever_tool
load_dotenv()

# 查询 Tavily 搜索 API 并返回 json 的工具
search = TavilySearch(tavily_api_key=os.getenv("tavily_key"))
# # 执行查询
# res = search.invoke("目前市场上苹果手机16的售价是多少？")
# print(res)


# 创建索引器根据上述查询的结果

# 加载HTML内容为一个文档对象
loader = WebBaseLoader("https://news.qq.com/rain/a/20240920A07Y5Y00")
# 读取文档
docs = loader.load()
# print(docs)

# 分割文档
documents = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)

# 向量化
vector = FAISS.from_documents(documents, DashScopeEmbeddings(dashscope_api_key=os.getenv('DASHSCOPE_API_KEY')))

# 创建检索器
retriever = vector.as_retriever()

# 测试检索结果
# print(retriever.invoke("目前市场上苹果手机16的售价是多少？"))


# 创建一个工具来检索文档
retriever_tool = create_retriever_tool(
    retriever,
    "iPhone_price_search",
    "搜索有关 iPhone 16 的价格信息。对于iPhone 16的任何问题，您必须使用此工具！",
)

# 创建将在下游使用的工具列表
tools = [search, retriever_tool]

# 初始化大模型
llm = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model='qwen-plus', temperature=0)



# https://smith.langchain.com/hub
# 获取要使用的提示
hub = Client()
prompt = hub.pull_prompt("hwchase17/openai-functions-agent")
# 打印Prompt
# print(prompt)

# 使用OpenAI functions代理
# from langchain.agents import create_openai_functions_agent
from langchain_classic.agents import create_openai_functions_agent



# 构建OpenAI函数代理：使用 LLM、提示模板和工具来初始化代理
agent = create_openai_functions_agent(llm, tools, prompt)

# from langchain.agents import AgentExecutor
from langchain_classic.agents import AgentExecutor
# 将代理与AgentExecutor工具结合起来
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
# 执行代理 进行对比
# agent_executor.invoke({"input": "目前市场上苹果手机16的各个型号的售价是多少？如果我在此基础上加价5%卖出，应该如何定价?"})
agent_executor.invoke({"input": "美国2024年谁胜出了总统的选举?"})
```
![[1769758877155-3944bf92-bbe8-4acd-ab68-8b53fb93bac0.png]]
### 2. langchain1.0使用agent
- 在`LangChain1.0`中，`create_agent`是一个便捷的函数，代理将语言模型与工具相结合，从而创建出能够对任务进行推理、决定使用何种工具并不断迭代以寻求解决方案的系统。 `create_agent`提供了可投入实际使用的代理程序实现。 一个 LLM 代理会循环运行工具以实现目标。该代理会一直运行，直到满足停止条件——即当模型产生最终输出或者达到迭代次数限制时。

### 2.1 **应用示例**
```plain text
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
import os
from dotenv import load_dotenv

load_dotenv()


# 定义查询订单状态的函数
def query_order_status(order_id):
    if order_id == "1024":
        return "订单 1024 的状态是：已发货，预计送达时间是 3-5 个工作日。"
    else:
        return f"未找到订单 {order_id} 的信息，请检查订单号是否正确。"


# 定义退款政策说明函数
def company_refund_policy(company_name):
    print(company_name)
    if company_name == "tom":
        return "tom公司的退款政策是：在购买后7天内可以申请全额退款，需提供购买凭证。"
    else:
        print('输入有误')


# 查询年龄
def get_age(name):
    if name == "tom":
        print(name)
        return "我的年龄是56岁！"
    else:
        print('输入有误')


# 初始化工具
tools = [
    TavilySearch(max_results=1, tavily_api_key=os.getenv("TAVILY_API_KEY")),
    Tool(
        name="queryOrderStatus",
        func=query_order_status,
        description="根据订单ID查询订单状态",
        args={"order_id": "订单的ID"}
    ),
    Tool(
        name="companyRefundPolicy",
        func=company_refund_policy,
        description="查询某某公司退款政策详细内容",
        args={"company_name": "公司名称"}
    ),
    Tool(
        name="getAge",
        func=get_age,
        description="查询tom年龄大小",
        args={"name": "查询tom年龄大小"}
    ),
]

# 选择将驱动代理的LLM
llm = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model='qwen-plus')

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个客服助手，使用工具回答问题。传递给工具的内容必须是准确的json数据不结尾的括号多加一个,如果是字符串数据必须和输入的保持一致要完整,不是篡改**重要规则**, ",
)
# 定义一些测试询问
queries = [
    "请问订单1024的状态是什么？",
    "请问tom公司退款政策是什么？",
    "2024年谁胜出了美国总统的选举"
]

# 运行代理并输出结果
for input in queries:
    print('客户提问：' + input)
    inputs = {"messages": [{"role": "user", "content": input}]}
    result = agent.invoke(inputs)
    print(result['messages'][-1].content)
```
### 七. `Langchain`之中间件
```plain text
中间件是`LangChain` 1.0引入的重要功能，允许你在LLM调用、工具执行、链式调用等关键环节**插入自定义逻辑**，实现监控、修改、记录等能力
```
- 文档:[https://reference.langchain.com/python/langchain/middleware](https://reference.langchain.com/python/langchain/middleware)

### 1. 常见中间件基础使用

| class | 描述 |
| --- | --- |
| `SummarizationMiddleware` | 接近令牌限制时自动总结对话历史记录 |
| `HumanInTheLoopMiddleware` | 暂停执行，等待人工批准工具调用 |
| `ModelCallLimitMiddleware` | 限制模型调用次数，以防止成本过高。 |
| `ToolCallLimitMiddleware` | 通过限制调用次数来控制工具执行。 |
| `ModelFallbackMiddleware` | 主模型故障时自动回退到备用模型 |
| `PIIMiddleware` | 检测和处理个人身份信息 |
| `TodoListMiddleware` | 为代理人配备任务规划和跟踪功能 |
| `LLMToolSelectorMiddleware` | 在调用主模型之前，使用 LLM 选择相关工具。 |
| `ToolRetryMiddleware` | 使用指数退避算法自动重试失败的工具调用 |
| `LLMToolEmulator` | 使用LLM模拟工具执行以进行测试 |
| `ContextEditingMiddleware` | 通过精简或清除工具使用情况来管理对话上下文 |
| `ShellToolMiddleware` | 向代理公开持久 shell 会话以执行命令 |
| `FilesystemFileSearchMiddleware` | 提供对文件系统文件的 Glob 和 Grep 搜索工具 |
| `AgentMiddleware` | 用于创建自定义中间件的基础中间件类 |

中间件决策方法选择:
- **approve (批准)** :允许智能体**按照原参数执行**被拦截的工具调用。
- **reject (拒绝)** : **禁止**智能体执行此次工具调用
- **edit (编辑)** : 在批准执行前，**修改工具调用的参数**

### 2. 人机交互中间件使用
![[1769758877214-42ba5a5d-149c-47e1-b1e1-583bf196ac4d.png]]
```plain text
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
import os
from dotenv import load_dotenv
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

load_dotenv()


# 定义查询订单状态的函数
def query_order_status(order_id):
    if order_id == "1024":
        return "订单 1024 的状态是：已发货，预计送达时间是 3-5 个工作日。"
    else:
        return f"未找到订单 {order_id} 的信息，请检查订单号是否正确。"


# 定义退款政策说明函数
def company_refund_policy(company_name):
    print(company_name)
    if company_name == "tom":
        return "tom公司的退款政策是：在购买后7天内可以申请全额退款，需提供购买凭证。"
    else:
        print('输入有误')


# 查询年龄
def get_age(name):
    if name == "tom":
        print(name)
        return "我的年龄是56岁！"
    else:
        print('输入有误')


# 初始化工具
tools = [
    TavilySearch(max_results=1, tavily_api_key=os.getenv("TAVILY_API_KEY")),
    Tool(
        name="queryOrderStatus",
        func=query_order_status,
        description="根据订单ID查询订单状态",
        args={"order_id": "订单的ID"}
    ),
    Tool(
        name="companyRefundPolicy",
        func=company_refund_policy,
        description="查询某某公司退款政策详细内容",
        args={"company_name": "公司名称"}
    ),
    Tool(
        name="getAge",
        func=get_age,
        description="查询tom年龄大小",
        args={"name": "查询tom年龄大小"}
    ),
]

# 选择将驱动代理的LLM
llm = ChatOpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model='qwen-plus')

agent = create_agent(
    model=llm,
    tools=tools,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                'tavily_search': {'allowed_decisions': ['approve', 'reject']},
                "queryOrderStatus": {'allowed_decisions': ['approve', 'reject']},
                "companyRefundPolicy": {'allowed_decisions': ['approve', 'reject']},
                "getAge": {'allowed_decisions': ['approve', 'reject']},
            }
        )
    ],
    checkpointer=InMemorySaver(),
    system_prompt="你是一个客服助手，使用工具回答问题。传递给工具的内容必须是准确的json数据不结尾的括号多加一个,如果是字符串数据必须和输入的保持一致要完整,不是篡改**重要规则**, ",
)
# 定义一些测试询问
queries = [
    "请问订单1024的状态是什么？",
    "请问tom公司退款政策是什么？",
    "2024年谁胜出了美国总统的选举"
]
config = {"configurable": {"thread_id": "some_other_id"}}

# 运行代理并输出结果
for que in queries:
    print('客户提问：' + que)
    inputs = {"messages": [{"role": "user", "content": que}]}
    result = agent.invoke(inputs, config=config)
    tool_name = result['__interrupt__'][0].value['action_requests'][0]['name']
    print(tool_name)
    app_or_reject = input("请确认调用{}是否同意(approve or reject)：".format(tool_name))
    res = agent.invoke(
        Command(resume={'decisions': [{'type': app_or_reject}]}),
        config=config
    )
    print(res['messages'][-1].content)
```
> 更多的使用会在agent阶段进行讲解

### 八. `LangChain`之Tools工具
### 1. 工具Tools
工具是代理、链或LLM可以用来与世界互动的接口。它们结合了几个要素
- 工具的名称
- 工具的描述
- 该工具输入的JSON模式
- 要调用的函数
- 是否应将工具结果直接返回给用户

`LangChain`通过提供统一框架集成功能的具体实现。在框架内，每个功能被封装成一个工具，具有自己的输入输出及处理方法。代理接收任务后，通过大模型推理选择适合的工具处理任务。一旦选定，LangChain将任务输入传递给该工具，工具处理输入生成输出。输出经过大模型推理，可用于其他工具的输入或作为最终结果返回给用户。
`Langchain`地址：[https://reference.langchain.com/python/langchain/tools/](https://reference.langchain.com/python/langchain/tools/)
### 1.1 工具的初步认识
```plain text

from langchain_tavily import TavilySearch
from dotenv import load_dotenv
import os

load_dotenv()

# 初始化工具 可以根据需要进行配置
tool = TavilySearch(top_k_results=1, doc_content_chars_max=100)

# 工具默认名称
print("name:", tool.name)
# 工具默认的描述
print("description:", tool.description)
# 输入内容 默认JSON模式
print("args:", tool.args)
# 是否直接返回工具的输出。
print("return_direct:", tool.return_direct)

# 可以用字典输入来调用这个工具
print(tool.run({"query": "langchain"}))
# 使用单个字符串输入来调用该工具。
print(tool.run("langchain"))
# 需要科学上网
```
### 1.2 **自定义工具**
- 在LangChain中，自定义工具有多种方法
- **@tool装饰器**
- @tool装饰器是定义自定义工具的最简单方法。装饰器默认使用函数名称作为工具名称，但可以通过传递字符串作为第一个参数来覆盖此设置。此外，装饰器将使用函数的文档字符串作为工具的描述 - 因此必须提供文档字符串。

```plain text

from langchain.tools import tool

@tool
def add_number(a: int, b: int) -> int:
    """add two numbers."""
    return a + b


print(add_number.name)
print(add_number.description)
print(add_number.args)

res = add_number.run({"a": 10, "b": 20})
print(res)
```
### 九. `LangChain`实现Memory
- 大多数的 LLM 应用程序都会有一个会话接口，允许我们和 LLM 进行多轮的对话，并有一定的上下文记忆能力。但实际上，模型本身是不会记忆任何上下文的，只能依靠用户本身的输入去产生输出。而实现这个记忆功能，就需要额外的模块去保存我们和模型对话的上下文信息，然后在下一次请求时，把所有的历史信息都输入给模型，让模型输出最终结果。

![[1769758877299-28ddfde7-cad6-4460-9fc6-41d9755e7d26.png]]
```plain text
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
load_dotenv()

llm = ChatOpenAI(api_key=os.getenv("api_key"),
                 base_url=os.getenv("base_url"),
                 model_name="qwen-plus")

# 直接提供问题，并调用llm
response = llm.invoke("你好我是柏汌")
# print(response)
# print("=" * 50)
print(response.content)

response = llm.invoke("我是谁?")

print(response.content)
```
- 而在 LangChain 中，提供这个功能的模块就称为 Memory，用于存储用户和模型交互的历史信息。
- 记忆系统需要支持两种基本操作：读取和写入。
- 在接收到初始用户输入之后但在执行核心逻辑之前，链将从其内存系统中读取并增强用户输入。
- 在执行核心逻辑之后但在返回答案之前，链会将当前运行的输入和输出写入内存，以便在将来的运行中引用它们。

![[1769758877361-77033c35-304a-4c18-bcc5-c70f7119eff1.png]]
- 对该图的解释: 1、输入问题: ({“question”: …})2、读取历史消息: 从Memory中READ历史消息（{“past_messages”: […]}）3、构建提示（Prompt): 读取到的历史消息和当前问题会被合并，构建一个新的Prompt4、模型处理: 构建好的提示会被传递给语言模型进行处理。语言模型根据提示生成一个输出。5、解析输出: 输出解析器通过正则表达式 regex(“Answer: (.*)“)来解析,返回一个回答（{”answer”: …}）给用户6、得到回复并写入Memory: 新生成的回答会与当前的问题一起写入Memory，更新对话历史。Memory会存储最新的对话内容，为后续的对话提供上下文支持。

### 1. Chat Messages
- Chat Messages: 最基础的记忆管理方法,是用于管理和存储对话历史的具体实现。它们通常用于构建对话系统，帮助系统保持对话的连续性和上下文。这些消息通常包含了对话的每一轮，包括用户的输入和系统的响应。

```plain text

from langchain_community.chat_message_histories import ChatMessageHistory

history = ChatMessageHistory()
history.add_user_message("hi!")
history.add_user_message("你好")
history.add_ai_message("whats up?")
print(history.messages)
```
### 2. `RunnableWithMessageHistory`
- `RunnableWithMessageHistory` 包装另一个 Runnable 并为其管理聊天消息历史记录；它负责读取和更新聊天消息历史记录。

### 2.1 **本地内存存储**
- 可以将聊天记录进行本地存储

```plain text
import json
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
# from langchain.schema import messages_from_dict, messages_to_dict
from langchain_core.messages import messages_from_dict, messages_to_dict
from dotenv import load_dotenv
import os

# 加载环境变量（需要包含API_KEY）
load_dotenv()

# 初始化大语言模型（通义千问）
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),  # 从环境变量读取API密钥
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云兼容端点
    model="qwen-turbo"  # 使用qwen-turbo模型
)

# 创建对话提示模板
prompt = ChatPromptTemplate.from_messages([
    # 系统角色设定
    ("system", "你是一个友好的助手"),
    # 历史消息占位符（变量名必须与链配置中的history_messages_key一致）
    MessagesPlaceholder(variable_name="history"),
    # 用户输入占位符
    ("user", "{input}")
])

# 构建基础对话链（组合提示模板和语言模型）
base_chain = prompt | llm

# 全局会话存储字典（Key: session_id, Value: ChatMessageHistory实例）
store = {}


def get_session_history(session_id):
    """获取或创建会话历史存储对象
    Args:
        session_id: 会话唯一标识（用于多会话隔离）
    Returns:
        对应会话的聊天历史记录对象
    """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()  # 初始化空历史记录
    return store[session_id]


# 创建支持历史记录的对话链
conversation = RunnableWithMessageHistory(
    base_chain,  # 基础对话链
    get_session_history=get_session_history,  # 历史记录获取方法
    input_messages_key="input",  # 输入文本的键名
    history_messages_key="history"  # 历史记录的键名（需与提示模板中的变量名一致）
)


def save_memory(filepath, session_id):
    """保存指定会话的历史记录到文件
    Args:
        filepath: 文件保存路径（建议使用.json扩展名）
        session_id: 要保存的会话ID（默认"default"）
    """
    history = get_session_history(session_id)
    # 将消息对象列表转换为字典格式
    dicts = messages_to_dict(history.messages)
    # 写入JSON文件（UTF-8编码）
    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(dicts, f, ensure_ascii=False)


def load_memory(filepath, session_id):
    """从文件加载历史记录到指定会话
    Args:
        filepath: 历史记录文件路径
        session_id: 要加载到的会话ID（默认"default"）
    """
    with open(filepath, "r", encoding='utf-8') as f:
        dicts = json.load(f)
    # 将字典转换回消息对象列表
    messages = messages_from_dict(dicts)
    # 更新全局存储中的会话历史
    store[session_id] = ChatMessageHistory(messages=messages)


def legacy_predict(input_text: str, session_id: str = "default") -> str:
    """模拟旧版predict方法的调用接口
    Args:
        input_text: 用户输入文本
        session_id: 会话ID（默认"default"）
    Returns:
        AI生成的回复文本
    """
    return conversation.invoke(
        {"input": input_text},  # 输入参数
        # 配置参数（必须包含session_id来关联历史记录）
        config={"configurable": {"session_id": session_id}}
    ).content


if __name__ == "__main__":
    # 使用默认会话ID
    SESSION_ID = "default"

    # 模拟连续对话（4轮）
    legacy_predict("你好", SESSION_ID)  # 问候
    legacy_predict("你是谁,我是柏汌", SESSION_ID)  # 身份确认
    legacy_predict("你的背后实现原理是什么", SESSION_ID)  # 技术原理询问

    # 查询对话历史（第4轮）
    last_response = legacy_predict('截止到现在我们聊了什么?', SESSION_ID)
    print("最后一次回答:", last_response)

    # 持久化保存对话历史（JSON格式）
    save_memory("./memory_new.json", SESSION_ID)

    # 模拟重新加载历史记录（清空当前会话后重新加载）
    load_memory("./memory_new.json", SESSION_ID)

    # 验证历史恢复效果（第5轮）
    reload_response = legacy_predict("我回来了，我们之前都聊了一些什么?", SESSION_ID)
    print("\n恢复后的回答:", reload_response)
```
### 十. `LangSmith`使用
### 1. 什么是 `LangSmith`？
`LangSmith` 是一个用于构建、调试和监控大型语言模型 (LLM) 应用的平台，由 LangChain 团队开发。它帮助开发者跟踪 LLM 的调用、性能和输出，优化提示词（Prompt）设计，并管理数据集和评估。
**主要功能:**
- **跟踪（Tracing）**：记录 LLM 调用、输入输出和元数据。
- **调试（Debugging）**：分析模型行为，识别问题。
- **数据集管理**：创建和维护测试数据集。
- **评估（Evaluation）**：运行测试用例，评估模型性能。
- **监控（Monitoring）**：实时监控生产环境中的 LLM 应用。

### 2. 配置 API 密钥
15. 注册 `LangSmith` 账号。
- [https://smith.langchain.com/](https://smith.langchain.com/)
16. 在 `LangSmith` 仪表板中获取 API 密钥。

![[1769758877437-439497ef-bae7-4972-a8c5-9b6ad6d06f27.png]]
17. 设置环境变量：

```plain text
LANGSMITH_API_KEY = 'Langsmith-key'
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_PROJECT="在Langsmith存储的名称"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com" # 任务发布站点
```
18. 执行代码不需要有任何的改动,会自动把执行的内容上传到`Langsmith`进行管理,在平台把任务已树结构展示项目的内容,展示项目的耗时,加载的提示词内容等等

![[1769758877526-1eae137b-e690-4c40-83f1-12870250587a.png]]
```plain text
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

import os




# 定义小红书文案提示词
prompt = PromptTemplate.from_template("""
你是一位小红书内容创作者，擅长撰写简洁、吸引人的种草文案。目标是创作100-150字的小红书风格文案，面向18-35岁用户，激发兴趣和互动。

**输入**：
- 产品/主题：{product}
- 核心特点：{features}
- 目标情绪：{emotion}
- 目标行动：{action}

**要求**：
1. 风格：亲切、口语化，带小幽默或生活场景，融入“种草”“安利”等流行词。
2. 结构：吸睛开头（问题/场景），中间突出特点，结尾引导互动（提问/号召）。
3. 使用1-2个emoji，保持自然。
4. 标题：10字以内。

**输出**：
标题:
文案正文:分2-3段，每段2-3句，结尾带互动引导
""")

llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    model='qwen-plus'
)

# 创建 LangChain 链
chain = prompt | llm

# 输入示例
input_data = {
    "product": "无线耳机",
    "features": "音质清晰、佩戴舒适、续航长",
    "emotion": "科技感、轻松",
    "action": "分享体验"
}
response = chain.invoke(input_data)
# 输出生成的小红书文案
print(response.content)
```
### 3. 提示词优化
- `Langsmith` 提供了提示词优化和导出提示词模版,可以用`Langsmith` 优化自己的提示词得到满意的输出,在将提示词导出使用

![[1769758877688-84dc801b-b9da-4002-9cec-7291173f44e6.png]]
- 使用`Langsmith`生成提示词

```plain text
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
from langsmith import Client

import os

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))
prompt = client.pull_prompt("test")

print(prompt)
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    model='qwen-plus'
)

# 创建 LangChain 链
chain = prompt | llm

# 输入示例
input_data = {
    "product": "无线耳机",
    "features": "音质清晰、佩戴舒适、续航长",
    "emotion": "科技感、轻松",
    "action": "分享体验"
}

response = chain.invoke(input_data)

# 输出生成的小红书文案
print(response.content)
```