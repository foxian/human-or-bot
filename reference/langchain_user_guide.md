# LangChain 使用手册

> 来源: https://docs.langchain.com/  |  整理时间: 2025-06-25

---

## 核心概念

### Agent = Model + Harness

LangChain的核心理念是将AI Agent简化为两个组件:

- **Model (模型)**: LLM (如 OpenAI, Anthropic, Google 等)
- **Harness (工具架)**: 围绕模型的封装，包括 prompt、tools、middleware

```
Agent = Model + Tools + Prompt + Middleware
```

### create_agent 函数

LangChain提供 `create_agent` 函数作为最小化、高度可配置的Agent工具架。

---

## 安装

```bash
pip install -U langchain
# Requires Python 3.10+
```

### 安装集成包

```bash
# OpenAI 集成
pip install -U langchain-openai

# Anthropic 集成
pip install -U langchain-anthropic
```

---

## 快速开始

### 创建简单Agent

```python
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="openai:gpt-5.5",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)
print(result["messages"][-1].content_blocks)
```

---

## 核心组件

### 1. Models (模型)

LangChain提供统一接口用于:
- Chat Models (聊天模型)
- Embeddings (嵌入模型)
- 其他LLM功能

**特性:**
- 标准模型接口
- 支持跨提供商切换
- 最小化代码变更

### 2. Tools (工具)

Tools允许Agent与外部世界交互:

```python
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def get_stock_price(symbol: str) -> str:
    """Get stock price for a given symbol."""
    return f"The stock price of {symbol} is $100."
```

### 3. Middleware (中间件)

Middleware提供可组合的能力扩展:

```python
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Choose model based on conversation complexity."""
    message_count = len(request.state["messages"])
    if message_count > 10:
        model = advanced_model
    else:
        model = basic_model
    return handler(request.override(model=model))

agent = create_agent(
    model=basic_model,
    tools=tools,
    middleware=[dynamic_model_selection]
)
```

**内置Middleware:**
- Guardrails (护栏)
- Retries (重试)
- Routing (路由)
- Custom tool policies (自定义工具策略)

### 4. Structured Output (结构化输出)

使用 `bind_tools` 实现结构化输出:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4",
    tools=[],
    system_prompt="Extract structured information."
)
```

> 注意: 使用结构化输出时不支持预绑定模型(pre-bound models)。

---

## Agent类型选择指南

| 场景 | 推荐 |
|------|------|
| 快速原型开发 | Deep Agents (开箱即用) |
| 高度定制化需求 | LangChain `create_agent` |
| 高级编排需求 | LangGraph (底层框架) |

### Deep Agents

适合需要以下功能的场景:
- 自动上下文压缩
- 虚拟文件系统
- 子Agent生成

### LangChain Agents

适合:
- 简单用例快速上手
- 中等定制化需求
- 标准Agent功能

### LangGraph

适合:
- 高级需求
- 结合确定性和Agentic工作流
- 多Agent编排

---

## LangSmith 集成

LangSmith用于追踪、调试和评估Agent:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=your_api_key
```

**功能:**
- 请求追踪
- Agent行为调试
- 输出评估
- 引擎监控(检测问题并提出修复)

---

## 教程资源

### LangChain 教程

1. **Semantic Search** - 构建PDF语义搜索引擎
2. **RAG Agent** - 创建检索增强生成Agent
3. **SQL Agent** - 构建与数据库交互的SQL Agent
4. **Voice Agent** - 构建可语音交互的Agent

### 多Agent模式

1. **Subagents: Personal assistant** - 构建委托给子Agent的个人助理
2. **Handoffs: Customer support** - 构建可在不同状态间转换的客户支持工作流
3. **Router: Knowledge base** - 构建多源知识库，路由查询到专业Agent
4. **Skills: SQL assistant** - 构建渐进式加载专业技能的Agent

---

## 相关链接

- 官方文档: https://docs.langchain.com/
- GitHub: https://github.com/langchain-ai/langchain
- PyPI: https://pypi.org/project/langchain/
- LangSmith: https://smith.langchain.com/
