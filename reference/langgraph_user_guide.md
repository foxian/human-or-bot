# LangGraph 使用手册

> 来源: https://docs.langchain.com/  |  整理时间: 2025-06-25

---

## 概述

LangGraph是LangChain的低层编排框架，用于构建、管理和部署长期运行、有状态的AI Agent。

**核心特点:**
- 图结构执行模型
- 支持分支、循环、动态决策
- 显式状态管理
- 强大的checkpointing
- 持久化内存
- 内置可观测性
- 人机交互控制
- 错误处理机制

---

## 核心概念

### Graph API

LangGraph使用声明式图构建API:

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    messages: list

def call_model(state: State):
    # 处理逻辑
    return {"messages": [...]}

graph = StateGraph(State)
graph.add_node("call_model", call_model)
graph.add_edge(START, "call_model")
graph.add_edge("call_model", END)
app = graph.compile()
```

### 状态管理

LangGraph使用显式的reducer驱动状态schemas:

```python
from typing import TypedDict

class AgentState(TypedDict):
    messages: list  # 消息列表
    current_task: str  # 当前任务
    memory: dict  # 持久化数据
```

**状态转换通过TypedDicts和reducer函数确保:**
- 精确的状态转换
- 数据完整性
- 并行执行安全

---

## 安装

```bash
pip install -U langgraph
```

---

## 创建Agent

### 基本Agent

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    messages: list

builder = StateGraph(State)
builder.add_node("model", lambda state: {"messages": ["response"]})
builder.add_edge(START, "model")
builder.add_edge("model", END)
graph = builder.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "Hi"}]})
```

### 带工具的Agent

```python
from langgraph.prebuilt import create_react_agent

def get_weather(city: str) -> str:
    return f"It's always sunny in {city}!"

agent = create_react_agent(
    model="openai:gpt-4",
    tools=[get_weather]
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]
})
```

---

## 持久化 (Persistence)

### Checkpointers (检查点)

用于持久化和检查线程状态:

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

graph = builder.compile(checkpointer=checkpointer)

# 带thread_id调用
result = graph.invoke(
    {"messages": [{"role": "user", "content": "Hi, my name is Bob."}]},
    {"configurable": {"thread_id": "thread-1"}}
)
```

**用途:**
- 对话连续性
- 人机交互
- 时间旅行
- 容错

### Stores (存储)

用于跨线程持久化应用数据:

```python
from langgraph.store.memory import MemoryStore

store = MemoryStore()

graph = builder.compile(store=store)

result = graph.invoke(
    {"messages": [{"role": "user", "content": "Hi"}]},
    {"configurable": {"thread_id": "thread-1"}}
)
```

**用途:**
- 用户偏好
- 事实和共享知识
- 长期数据

### Checkpointer vs Store

| 特性 | Checkpointer | Store |
|------|--------------|-------|
| 持久化内容 | 图状态快照 | 应用定义的键值数据 |
| 范围 | 单个线程 | 跨线程 |
| 内存类型 | 短期，线程作用域 | 长期，跨线程 |
| 使用场景 | 对话连续性、人机交互 | 用户偏好、共享知识 |
| 访问模式 | 通过thread_id传递 | 从节点或应用代码读写 |

---

## 工作流与Agent

### Workflows

使用图构建复杂工作流:

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class WorkflowState(TypedDict):
    messages: list
    next_step: str

def process(state: WorkflowState):
    return {"next_step": "end"}

builder = StateGraph(WorkflowState)
builder.add_node("process", process)
builder.add_edge(START, "process")
builder.add_edge("process", END)
app = builder.compile()
```

### 多Agent模式

**子Agent委托:**
```python
# Personal assistant delegating to sub-agents
```

**状态转换:**
```python
# Customer support workflow with state transitions
```

**路由:**
```python
# Multi-source knowledge base routing queries
```

---

## LangGraph vs LangChain

| 特性 | LangChain | LangGraph |
|------|-----------|-----------|
| 抽象级别 | 高层API | 底层编排 |
| 复杂度 | 简单用例 | 复杂工作流 |
| 状态管理 | 隐式 | 显式(通过reducer) |
| 灵活性 | 受限 | 高度可定制 |
| 适用场景 | 快速原型、标准Agent | 企业级、定制化需求 |

**推荐选择:**
- 简单用例 → LangChain `create_agent`
- 复杂工作流 → LangGraph
- 需要结合两者 → LangChain Agent使用LangGraph原语

---

## 错误处理与调试

### LangSmith集成

LangGraph与LangSmith深度集成:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=your_api_key
```

**功能:**
- 追踪请求
- 调试Agent行为
- 评估输出
- 引擎监控

### Agent Server

Agent Server自动处理持久化，无需手动配置checkpointers或stores。

---

## 相关链接

- 官方文档: https://docs.langchain.com/oss/python/langgraph/overview
- GitHub: https://github.com/langchain-ai/langgraph
- PyPI: https://pypi.org/project/langgraph/

---

## 版本信息

| 版本 | 说明 |
|------|------|
| 1.0 | 正式发布，生产就绪，零Breaking Changes承诺 |
| 0.3.26 | 最后0.x版本 (2025-04-08) |
| 1.2.5 | 持续完善核心API |
