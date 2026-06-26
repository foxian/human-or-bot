# NPC 机器人 · 反向图灵测试设计规格

**日期**: 2026-06-25  
**状态**: 已批准  
**作者**: Antigravity × 用户

---

## 概述

构建一个命令行「反向图灵测试」游戏：NPC 拥有真实的人类身份设定，并用尽全力伪装成人类，而玩家的目标是通过10次对话问答识破 NPC 是 AI。

游戏的核心张力来自 NPC 的反应质量 —— 它不会刻意暴露，玩家需要从自然对话中找到蛛丝马迹。每局结束后，玩家可以回看任意一轮对话，并查看 NPC 当时的内心独白（思考过程）。

---

## 范围

### 本期（MVP）
- 单人对战模式：一个玩家 vs 一个 NPC
- 命令行界面（CLI）
- NPC 身份随机生成
- 固定10次问答
- 内心独白记录 + 游戏结束后的回顾模式
- 玩家宣判（AI / 人类）

### 后期迭代（不在本期范围）
- 多人公开房间模式（多玩家 + 多 NPC 混在一起）
- Web 界面（Next.js）
- 算分系统与排行榜
- NPC 难度分级
- AI 特征漏出机制的刻意设计

---

## 系统架构

### 技术栈
- **语言**: Python 3.11+
- **框架**: LangGraph（双节点状态图）
- **LLM**: 通过 LangChain 接入（默认 OpenAI GPT-4，可配置）
- **界面**: 命令行 CLI（rich 库美化输出）

### 核心组件

```
NPC Robot
├── npc/
│   ├── profile.py        # NpcProfile 数据类 + 生成逻辑
│   ├── graph.py          # LangGraph 双节点状态图
│   ├── nodes/
│   │   ├── think.py      # ThinkNode：内心独白生成
│   │   └── respond.py    # RespondNode：对外回复生成
│   └── prompts.py        # 所有 Prompt 模板
├── game/
│   ├── session.py        # GameSession：游戏状态管理
│   └── review.py         # ReviewMode：回顾模式
├── cli/
│   └── main.py           # CLI 入口，用户交互
└── config.py             # 配置（LLM 提供商、模型名等）
```

### 架构流程图

```
玩家输入一个问题
        ↓
  GameSession 接收
        ↓
  LangGraph StateGraph
  ┌─────────────────────┐
  │  [ThinkNode]        │  ← 生成内心独白（不显示给玩家）
  │       ↓             │
  │  [RespondNode]      │  ← 基于内心独白生成对外回复
  └─────────────────────┘
        ↓
  回复显示给玩家
  内心独白存入 GameSession.inner_monologue_log
        ↓
  玩家选择：继续提问 / 宣判 / 查看回顾
```

---

## NPC 身份系统

### NpcProfile 数据结构

```python
@dataclass
class NpcProfile:
    name: str                # 中文姓名
    age: int                 # 年龄（25-50）
    occupation: str          # 职业
    city: str                # 所在城市
    personality: list[str]   # 3-5个性格特征词
    backstory: str           # 200-400字的背景故事，含具体生活细节
    hobbies: list[str]       # 2-4个兴趣爱好（具体，非泛化）
    speech_style: str        # 说话风格描述（用于指导回复节点）
    quirks: list[str]        # 2-3个小怪癖/习惯（增加真实感）
```

### 生成策略

- 每局开始时调用 LLM 一次性生成完整档案
- 档案需要包含具体细节（具体地名、具体事件、具体时间），避免泛化描述
- 职业和城市从预定义列表中抽取，保证多样性
- backstory 需要包含至少一段有情感重量的真实经历

### 示例生成结果

```json
{
  "name": "陈建国",
  "age": 34,
  "occupation": "建筑设计师",
  "city": "成都",
  "personality": ["内敛", "完美主义", "有点悲观"],
  "backstory": "从小在重庆渝中区长大，大学考到成都理工后定居至今。30岁时经历一段失败的婚姻，前妻说他把工作看得比什么都重要。离婚后搬去了金牛区的一间一居室，养了一只橘猫叫「丁香」。最近的项目是一个商业综合体改造，他觉得甲方品味太差但不敢说。",
  "hobbies": ["胶片摄影（主要拍城市边缘地带）", "徒步", "做手冲咖啡"],
  "speech_style": "话少但有力，偶尔用川渝方言词汇，不喜欢废话",
  "quirks": ["被问到感情话题时总是用「嗯」开头", "喜欢用「其实」来开始解释"]
}
```

---

## LangGraph 双节点状态图

### 状态定义（GraphState）

```python
class GraphState(TypedDict):
    npc_profile: NpcProfile          # NPC 档案
    conversation_history: list[dict] # 完整对话历史（含内心独白）
    player_input: str                # 当前玩家输入
    inner_monologue: str             # 当前轮次内心独白（ThinkNode 写入）
    npc_response: str                # 当前轮次对外回复（RespondNode 写入）
```

### ThinkNode（思考节点）

**职责**：模拟 NPC 的内心思考，决定回应策略

**Prompt 结构**：
```
System: 你是 {name}，{occupation}，{age}岁，住在{city}。
        你的背景：{backstory}
        你的说话风格：{speech_style}
        
        重要：你现在正在和一个陌生人对话，但这个人怀疑你是 AI。
        你必须尽可能让他/她认为你是真实的人类。
        
        现在请用第一人称内心独白的方式思考：
        - 这个问题危险吗？会让我暴露身份吗？
        - 作为 {name}，我真实的感受和想法是什么？
        - 我打算怎么回答？语气是什么？

User: {conversation_history}
      玩家问：{player_input}
      
      请写出你的内心独白（不超过150字）：
```

**输出**：内心独白字符串，存入 `inner_monologue`

### RespondNode（回复节点）

**职责**：基于内心独白，生成符合 NPC 性格的实际回复

**Prompt 结构**：
```
System: 你是 {name}，{occupation}，{age}岁，住在{city}。
        你的说话风格：{speech_style}
        
        你刚才的内心想法是：{inner_monologue}
        
        基于这个想法，用 {name} 的说话风格回复玩家。
        要求：
        - 完全不能提到自己是 AI
        - 回复要自然、有个人色彩，不能太正式
        - 长度适中（1-4句话），不要废话

User: {conversation_history}
      玩家：{player_input}
      
      {name} 的回复：
```

**输出**：对外回复字符串，存入 `npc_response`

---

## 游戏会话（GameSession）

```python
@dataclass
class GameSession:
    npc_profile: NpcProfile
    questions_left: int = 10
    conversation_history: list[ConversationTurn] = field(default_factory=list)
    is_over: bool = False
    verdict: str | None = None  # "ai" 或 "human"

@dataclass  
class ConversationTurn:
    turn_number: int
    player_question: str
    inner_monologue: str      # 仅游戏结束后可见
    npc_response: str
```

---

## CLI 交互设计

### 游戏界面

```
╔══════════════════════════════════════╗
║    NPC 机器人 · 反向图灵测试          ║
║    你有 10 次机会识破他/她是 AI        ║
╚══════════════════════════════════════╝

「你好！我是陈建国。」

[第 1/10 问] > _

指令：/judge ai · /judge human · /review · /quit
```

### 宣判结果展示

```
══ 宣判：你认为我是 AI ══

✓ 正确！陈建国 确实是 AI。

━━━━━━━━━━━━━━━━━━━━━━━━

输入 /review 回顾对话和内心独白
输入 /quit 退出
```

### 回顾模式

```
══ 回顾模式 ══

输入轮次编号查看（1-7），或 /back 返回

> 3

━━ 第 3 轮 ━━
玩家：你有没有为什么事情哭过？

💭 内心独白：
这是个情感类问题，有点危险。我需要表现出情感，但不能太完美。
陈建国离过婚，那是个真实的伤。我可以用那段经历，但要显得不太
愿意提起……语气要收一下，不要解释太多。

陈建国：有啊……离婚那年吧。不想多说。
```

---

## 配置

```python
# config.py
LLM_PROVIDER = "openai"         # 或 "anthropic", "google"
LLM_MODEL = "gpt-4o"
TEMPERATURE_THINK = 0.7         # 内心独白温度
TEMPERATURE_RESPOND = 0.8       # 对外回复温度
MAX_QUESTIONS = 10
THINK_MAX_TOKENS = 200
RESPOND_MAX_TOKENS = 150
```

---

## 验证计划

### 基础功能验证
1. 运行 `python cli/main.py`，检查 NPC 档案生成是否正常
2. 进行10轮对话，观察 NPC 回复的连贯性和人格一致性
3. 测试 `/judge ai` 和 `/judge human` 指令
4. 测试 `/review` 模式，检查内心独白是否正确记录
5. 测试 `/quit` 退出

### 质量评估（主观）
- NPC 回复是否有个人色彩，还是感觉「像 AI 在回答」
- 内心独白是否真实反映了回应策略
- 不同 NPC 档案之间是否有明显的性格差异

---

## 待决定（后期迭代时处理）

- [ ] 算分系统具体设计
- [ ] AI 特征漏出机制（是否刻意设计，如何平衡难度）
- [ ] 多人房间模式的架构
- [ ] Web 界面迁移时机
