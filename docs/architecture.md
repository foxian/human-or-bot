# 概要设计

## 1. 技术选型

| 类别 | 技术 | 版本 |
|------|------|------|
| 编程语言 | Python | 3.11+ |
| 状态图框架 | LangGraph | 最新 |
| LLM 框架 | LangChain | 最新 |
| LLM 接口 | OpenAI 兼容（DeepSeek） | - |
| CLI 美化 | Rich | 最新 |
| 测试框架 | pytest | 最新 |

## 2. 系统架构

### 2.1 当前架构（单体 CLI）

```
┌─────────────────────────────────────────────────────────┐
│                    CLI 入口层                            │
│                  (cli/main.py)                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  游戏逻辑层                              │
│         ┌─────────────────┬─────────────────┐           │
│         │  GameSession    │  ReviewMode    │           │
│         │ (game/session)  │ (game/review)  │           │
│         └─────────────────┴─────────────────┘           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  NPC 核心层                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │         LangGraph 双节点状态图                    │  │
│  │  ┌──────────────┐    ┌──────────────────┐       │  │
│  │  │  ThinkNode   │ →  │ RespondNode      │       │  │
│  │  │  (内心独白)  │    │  (对外回复)      │       │  │
│  │  └──────────────┘    └──────────────────┘       │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────────┐       │
│  │  NpcProfile      │  │  prompts.py          │       │
│  │  (npc/profile)   │  │  (Prompt 模板)       │       │
│  └──────────────────┘  └──────────────────────┘       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   配置层                                 │
│                 (config.py)                             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 未来架构（前后端分离）

见 `docs/superpowers/specs/2026-06-26-frontend-backend-separation-design.md`

## 3. 核心模块设计

### 3.1 npc/profile.py - NPC 档案模块

| 组件 | 类型 | 描述 |
|------|------|------|
| `NpcProfile` | dataclass | NPC 身份档案数据类 |
| `generate_npc_profile()` | async function | 调用 LLM 生成完整 NPC 档案 |

**NpcProfile 字段：**
- `name: str` - 中文姓名
- `age: int` - 年龄
- `occupation: str` - 职业
- `city: str` - 所在城市
- `personality: list[str]` - 性格特征列表
- `backstory: str` - 背景故事
- `hobbies: list[str]` - 爱好列表
- `speech_style: str` - 说话风格描述
- `quirks: list[str]` - 小怪癖列表

### 3.2 npc/prompts.py - Prompt 模板模块

| 函数 | 描述 |
|------|------|
| `build_think_prompt()` | 构建 ThinkNode 使用的消息列表 |
| `build_respond_prompt()` | 构建 RespondNode 使用的消息列表 |

### 3.3 npc/graph.py - LangGraph 状态图

| 组件 | 类型 | 描述 |
|------|------|------|
| `GraphState` | TypedDict | 状态图状态定义 |
| `think_node()` | async function | 内心独白节点 |
| `respond_node()` | async function | 对外回复节点 |
| `run_npc_turn()` | async function | 执行一轮 NPC 对话 |

**GraphState 字段：**
- `npc_profile: NpcProfile` - NPC 档案
- `conversation_history: list[dict]` - 对话历史
- `player_input: str` - 当前玩家输入
- `inner_monologue: str` - 当前轮次内心独白
- `npc_response: str` - 当前轮次对外回复

### 3.4 game/session.py - 游戏会话模块

| 组件 | 类型 | 描述 |
|------|------|------|
| `ConversationTurn` | dataclass | 单轮对话记录 |
| `GameSession` | dataclass | 游戏会话管理 |

**ConversationTurn 字段：**
- `turn_number: int` - 轮次编号
- `player_question: str` - 玩家问题
- `inner_monologue: str` - 内心独白
- `npc_response: str` - NPC 回复

**GameSession 主要方法：**
- `ask(player_input: str)` - 玩家提问一轮
- `judge(verdict: str)` - 玩家宣判
- `get_lc_history()` - 获取 LangChain 格式对话历史

### 3.5 game/review.py - 回顾模式模块

| 组件 | 类型 | 描述 |
|------|------|------|
| `ReviewMode` | class | 游戏结束后的回顾模式 |

**ReviewMode 主要方法：**
- `total_turns()` - 返回总对话轮数
- `get_turn(turn_number)` - 获取指定轮次的对话记录

### 3.6 cli/main.py - CLI 入口

负责用户交互、命令路由、格式化显示。

## 4. 配置设计

### 4.1 config.py

| 配置项 | 环境变量 | 默认值 | 描述 |
|--------|----------|--------|------|
| `OPENAI_API_KEY` | `OPENAI_API_KEY` | - | API Key |
| `OPENAI_BASE_URL` | `OPENAI_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `LLM_MODEL` | `OPENAI_MODEL` | `deepseek-v4-flash` | 模型名称 |
| `TEMPERATURE_THINK` | `TEMPERATURE_THINK` | `0.7` | 内心独白温度 |
| `TEMPERATURE_RESPOND` | `TEMPERATURE_RESPOND` | `0.8` | 对外回复温度 |
| `MAX_QUESTIONS` | `MAX_QUESTIONS` | `10` | 最大提问次数 |
| `THINK_MAX_TOKENS` | `THINK_MAX_TOKENS` | `200` | 内心独白最大 Token |
| `RESPOND_MAX_TOKENS` | `RESPOND_MAX_TOKENS` | `150` | 对外回复最大 Token |

### 4.2 LangSmith 配置（可选）

| 用户配置 | 映射为 | 描述 |
|----------|--------|------|
| `LANGSMITH_TRACING` | `LANGCHAIN_TRACING_V2` | 开启追踪 |
| `LANGSMITH_ENDPOINT` | `LANGCHAIN_ENDPOINT` | LangSmith 地址 |
| `LANGSMITH_API_KEY` | `LANGCHAIN_API_KEY` | LangSmith API Key |
| `LANGSMITH_PROJECT` | `LANGCHAIN_PROJECT` | 项目名称 |

## 5. 数据流向

### 5.1 一轮对话的数据流

```
1. 玩家输入问题
   ↓
2. GameSession.ask() 接收
   ↓
3. 调用 run_npc_turn(profile, history, player_input)
   ↓
4. LangGraph 执行：
   ├─ ThinkNode → 生成 inner_monologue
   └─ RespondNode → 基于 inner_monologue 生成 npc_response
   ↓
5. 返回 (inner_monologue, npc_response)
   ↓
6. 保存 ConversationTurn 到 GameSession
   ↓
7. 显示 npc_response 给玩家（inner_monologue 暂存）
```

## 6. 目录结构

```
npc/
├── npc/
│   ├── __init__.py
│   ├── profile.py          # NpcProfile 数据类 + 生成逻辑
│   ├── graph.py            # LangGraph 双节点状态图
│   ├── prompts.py          # Prompt 模板
│   └── nodes/
│       ├── __init__.py
│       ├── think.py        # 内心独白节点
│       └── respond.py      # 对外回复节点
├── game/
│   ├── __init__.py
│   ├── session.py          # 游戏会话管理
│   └── review.py           # 回顾模式
├── cli/
│   ├── __init__.py
│   └── main.py             # CLI 入口
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── npc/
│   │   ├── test_profile.py
│   │   ├── test_prompts.py
│   │   └── test_graph.py
│   └── game/
│       ├── test_session.py
│       └── test_review.py
├── docs/
│   ├── requirements.md     # 需求文档（本文档）
│   ├── architecture.md     # 概要设计文档
│   └── superpowers/        # 详细设计规格和计划
├── config.py               # 配置
├── requirements.txt
├── pyproject.toml
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```
