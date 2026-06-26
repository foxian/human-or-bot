# LangSmith 追踪功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现通过环境变量无侵入地自动启用 LangSmith 追踪，完整监控游戏对话中 Think 和 Respond 节点的执行状况。

**Architecture:** 在 `config.py` 中读取 `LANGSMITH_*` 系列环境变量，在初始化时自动将其映射为 LangChain 官方标准的 `LANGCHAIN_*` 环境变量，从而使全局 LangGraph 无侵入开启追踪。

**Tech Stack:** Python, LangChain, LangGraph, pytest

## Global Constraints

- 环境变量映射名称必须与设计方案完全一致。
- 必须包含单元测试，确保环境变量在加载 config 时被正确注入。
- 修改 `.env` 和 `.env.example` 时，必须保留原有配置。

---

### Task 1: 环境变量模板与本地配置追加

**Files:**
- Modify: `.env`
- Modify: `.env.example`

**Interfaces:**
- Produces: `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` 环境变量。

- [ ] **Step 1: 修改 `.env.example` 追加模板**

在 `D:\DevProjects\npc\.env.example` 文件末尾追加：
```ini
# LangSmith 追踪配置
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT="npc"
```

- [ ] **Step 2: 修改 `.env` 追加真实配置**

在 `D:\DevProjects\npc\.env` 文件末尾追加您提供的具体配置：
```ini
# LangSmith 追踪配置
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT="npc"
```

- [ ] **Step 3: 验证文件追加完成**

确保文件内容追加成功，且原有的 API KEY 和其他配置保持不变。

- [ ] **Step 4: Commit**

```bash
git add .env.example
git commit -m "config: add LangSmith environment variable templates"
```

---

### Task 2: 在 `config.py` 中实现环境变量映射与自动注入

**Files:**
- Modify: `config.py`

**Interfaces:**
- Consumes: `.env` 中的 `LANGSMITH_*` 环境变量。
- Produces: 自动在 `os.environ` 中注入官方标准的 `LANGCHAIN_*` 环境变量。

- [ ] **Step 1: 修改 `config.py`，实现映射逻辑**

在 `D:\DevProjects\npc\config.py` 的末尾追加以下逻辑：
```python
# 读取 LangSmith 相关配置并自动映射为 LangChain 标准变量以实现自动追踪
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false")
if LANGSMITH_TRACING.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if env_endpoint := os.getenv("LANGSMITH_ENDPOINT"):
        os.environ["LANGCHAIN_ENDPOINT"] = env_endpoint
    if env_api_key := os.getenv("LANGSMITH_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = env_api_key
    if env_project := os.getenv("LANGSMITH_PROJECT"):
        os.environ["LANGCHAIN_PROJECT"] = env_project
```

- [ ] **Step 2: 验证语法无误**

运行 Python 解释器导入 `config` 模块，确保没有语法错误。
运行：`python -c "import config"`
Expected: 运行成功，无任何错误输出。

- [ ] **Step 3: Commit**

```bash
git add config.py
git commit -m "feat: implement automatic LangSmith to LangChain environment variable mapping"
```

---

### Task 3: 编写并运行单元测试验证映射逻辑

**Files:**
- Create: `tests/test_langsmith_config.py`

**Interfaces:**
- Consumes: `config` 模块和映射机制。

- [ ] **Step 1: 创建测试文件编写测试**

创建 `tests/test_langsmith_config.py`，内容如下：
```python
import os
import importlib
import config

def test_langsmith_env_mapping(monkeypatch):
    # 清理已有的环境变量
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    
    # 模拟设置 LANGSMITH_TRACING = true
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    monkeypatch.setenv("LANGSMITH_API_KEY", "test_key")
    monkeypatch.setenv("LANGSMITH_PROJECT", "test_project")
    
    # 重新加载 config 模块以触发映射
    importlib.reload(config)
    
    # 验证官方标准变量是否被正确注入
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_ENDPOINT") == "https://api.smith.langchain.com"
    assert os.environ.get("LANGCHAIN_API_KEY") == "test_key"
    assert os.environ.get("LANGCHAIN_PROJECT") == "test_project"
```

- [ ] **Step 2: 运行测试并验证它通过**

运行：`pytest tests/test_langsmith_config.py -v`
Expected: 1 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_langsmith_config.py
git commit -m "test: add unit test for LangSmith environment variable mapping"
```

---

### Task 4: 运行游戏并进行集成验证

**Files:**
- None (运行游戏)

- [ ] **Step 1: 启动游戏会话**

运行游戏命令行入口，确保项目可以正常启动且不报错：
运行：`python cli/main.py`
预期：游戏成功启动，显示欢迎界面或输入提示。

- [ ] **Step 2: 进行一次对话**

在游戏中输入任意测试消息，发送给 NPC。
确认 NPC 能够正常思考（显示独白）并进行回复，无任何异常抛出。

- [ ] **Step 3: 检查终端输出或退出**

输入 `/quit` 退出游戏。

- [ ] **Step 4: 登录 LangSmith 确认 Trace**

登录您的 LangSmith 平台（`https://smith.langchain.com`），进入 `npc` 项目，确认生成了最新的 `run_npc_turn` (或对应 graph 运行) 的 Trace 记录。
