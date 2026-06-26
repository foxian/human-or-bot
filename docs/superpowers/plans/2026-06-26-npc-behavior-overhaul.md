# NPC 行为系统改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 NPC 的 profile 数据结构与 think/respond prompt 模板，让 NPC 行为从"演角色"转为"活在当下"。

**Architecture:** 改动严格限制在 `npc/profile.py` 和 `npc/prompts.py` 两个文件。Profile 新增 `defense_style` 和 `sealed_topics` 字段、删除 `quirks`、收紧 `backstory` 生成要求；`to_system_prompt()` 根据 `defense_style` 注入差异化守则。Think prompt 重构为"威胁评估 → 情绪 → 策略 → 信息门控 → 意图"五步，第一行显式输出威胁等级。Respond prompt 读取该等级决定长度，并强制信息克制。`graph.py`、`nodes/think.py`、`nodes/respond.py` 不动。

**Tech Stack:** Python 3.11+，dataclasses，LangChain（ChatOpenAI），LangGraph，pytest + pytest-asyncio（asyncio_mode=auto）。

## Global Constraints

- 只能修改 `npc/profile.py` 和 `npc/prompts.py` 两个生产文件；不得修改 `npc/graph.py`、`npc/nodes/think.py`、`npc/nodes/respond.py`。
- `defense_style` 取值必须从 `["转移反问","轻描带过","微微恼火","自嘲化解"]` 中四选一。
- Think 独白字数上限从 150 字降至 100 字。
- Think 独白第一行必须为 `威胁等级：低/中/高`，第二行起为自然语言独白。
- 删除 `quirks` 字段（合并进 `speech_style` 生成要求）。
- 所有现有测试 fixture 中传给 `NpcProfile(...)` 的 `quirks=` 参数必须替换为 `defense_style=` 和 `sealed_topics=`。
- 不引入新依赖。

---

## File Structure

| 文件 | 责任 | 本计划改动 |
|---|---|---|
| `npc/profile.py` | `NpcProfile` 数据类、`to_system_prompt()`、`GENERATE_PROFILE_PROMPT`、`generate_npc_profile()` | 重构数据类与 prompt |
| `npc/prompts.py` | `THINK_SYSTEM_TEMPLATE`、`RESPOND_SYSTEM_TEMPLATE`、`build_think_prompt()`、`build_respond_prompt()` | 重写两个 system template |
| `tests/npc/test_profile.py` | NpcProfile 字段与 `to_system_prompt()` 测试 | 更新 fixture、新增守则注入测试 |
| `tests/npc/test_prompts.py` | prompt 构建函数测试 | 更新 fixture、新增 think/respond 内容测试 |
| `tests/npc/test_graph.py` | graph 集成测试 fixture | 更新 fixture |
| `tests/game/test_review.py` | review 模式测试 fixture | 更新 fixture |
| `tests/game/test_session.py` | session 测试 fixture | 更新 fixture |

---

### Task 1: Profile 数据结构重构

**Files:**
- Modify: `npc/profile.py`
- Modify: `tests/npc/test_profile.py`
- Modify: `tests/npc/test_prompts.py`
- Modify: `tests/npc/test_graph.py`
- Modify: `tests/game/test_review.py`
- Modify: `tests/game/test_session.py`

**Interfaces:**
- Produces: `NpcProfile` 新增字段 `defense_style: str`、`sealed_topics: list[str]`；删除字段 `quirks`。`NpcProfile(...)` 构造签名变为：
  ```python
  NpcProfile(name, age, occupation, city, personality, backstory, hobbies, speech_style, defense_style, sealed_topics)
  ```
- Produces: `NpcProfile.to_system_prompt()` 返回值包含 `defense_style` 专属守则段、`sealed_topics` 回避行为段；不再包含"小怪癖"段。
- Produces: `GENERATE_PROFILE_PROMPT` 要求 LLM 输出 `defense_style`、`sealed_topics` 字段；`backstory` 含模糊记忆+轻微矛盾、不戏剧性；`speech_style` 合并原 quirks；不再要求输出 `quirks`。
- Produces: `generate_npc_profile()` 从 JSON 解析新字段、不再解析 `quirks`。

- [ ] **Step 1: 更新所有测试 fixture 以匹配新签名**

把 5 个测试文件里所有 `NpcProfile(...)` 构造调用改成新签名。同时把 `tests/npc/test_profile.py` 里检查 `quirks` 的断言改成检查 `defense_style`/`sealed_topics`。

替换 `tests/npc/test_profile.py` 全文为：

```python
import pytest
from npc.profile import NpcProfile, generate_npc_profile


def test_npc_profile_fields():
    """NpcProfile 数据类字段完整性测试（不调用 LLM）"""
    profile = NpcProfile(
        name="测试人",
        age=30,
        occupation="工程师",
        city="北京",
        personality=["内敛", "认真"],
        backstory="这是一段测试背景故事，包含具体的生活细节和情感经历。",
        hobbies=["读书", "跑步"],
        speech_style="简洁直接",
        defense_style="轻描带过",
        sealed_topics=["感情史"],
    )
    assert profile.name == "测试人"
    assert profile.age == 30
    assert len(profile.personality) == 2
    assert len(profile.hobbies) == 2
    assert profile.defense_style == "轻描带过"
    assert profile.sealed_topics == ["感情史"]


def test_npc_profile_to_system_prompt():
    """NpcProfile.to_system_prompt() 输出包含关键字段"""
    profile = NpcProfile(
        name="陈建国",
        age=34,
        occupation="建筑设计师",
        city="成都",
        personality=["内敛", "完美主义"],
        backstory="从小在重庆长大，大学考到成都理工后定居至今。",
        hobbies=["胶片摄影", "徒步"],
        speech_style="话少但有力，偶尔用川渝方言",
        defense_style="转移反问",
        sealed_topics=["父亲的工作"],
    )
    prompt = profile.to_system_prompt()
    assert "陈建国" in prompt
    assert "34" in prompt
    assert "建筑设计师" in prompt
    assert "成都" in prompt


def test_npc_profile_to_system_prompt_includes_defense_style_guard():
    """to_system_prompt() 根据 defense_style 注入对应守则关键词"""
    profile = NpcProfile(
        name="测试人", age=30, occupation="工程师", city="北京",
        personality=["认真"], backstory="测试背景",
        hobbies=["读书"], speech_style="简洁",
        defense_style="微微恼火",
        sealed_topics=[],
    )
    prompt = profile.to_system_prompt()
    # 微微恼火型守则的关键短语
    assert "轻微不舒服" in prompt


def test_npc_profile_to_system_prompt_includes_sealed_topics():
    """to_system_prompt() 包含 sealed_topics 及其回避行为指引"""
    profile = NpcProfile(
        name="测试人", age=30, occupation="工程师", city="北京",
        personality=["认真"], backstory="测试背景",
        hobbies=["读书"], speech_style="简洁",
        defense_style="轻描带过",
        sealed_topics=["父亲的工作", "大学那段日子"],
    )
    prompt = profile.to_system_prompt()
    assert "父亲的工作" in prompt
    assert "大学那段日子" in prompt
    assert "回避" in prompt
```

替换 `tests/npc/test_prompts.py` 顶部的 `sample_profile` fixture：

```python
@pytest.fixture
def sample_profile():
    return NpcProfile(
        name="陈建国", age=34, occupation="建筑设计师", city="成都",
        personality=["内敛", "完美主义"],
        backstory="从小在重庆长大，后来定居成都。",
        hobbies=["胶片摄影", "徒步"],
        speech_style="话少但有力",
        defense_style="转移反问",
        sealed_topics=["父亲的工作"],
    )
```
（保留该文件中其余测试函数不变。）

替换 `tests/npc/test_graph.py` 的 `sample_profile` fixture：

```python
@pytest.fixture
def sample_profile():
    return NpcProfile(
        name="陈建国", age=34, occupation="建筑设计师", city="成都",
        personality=["内敛"], backstory="测试背景",
        hobbies=["摄影"], speech_style="简洁",
        defense_style="转移反问", sealed_topics=["父亲的工作"],
    )
```

替换 `tests/game/test_review.py` 中 `session_with_history` 内的 profile 构造：

```python
    profile = NpcProfile(
        name="测试人", age=30, occupation="工程师", city="北京",
        personality=["认真"], backstory="测试背景",
        hobbies=["读书"], speech_style="简洁",
        defense_style="轻描带过", sealed_topics=[],
    )
```

替换 `tests/game/test_session.py` 的 `sample_profile` fixture：

```python
@pytest.fixture
def sample_profile():
    return NpcProfile(
        name="陈建国", age=34, occupation="建筑设计师", city="成都",
        personality=["内敛"], backstory="测试背景",
        hobbies=["摄影"], speech_style="简洁",
        defense_style="转移反问", sealed_topics=["父亲的工作"],
    )
```

- [ ] **Step 2: 运行测试确认全部失败（字段未实现）**

Run: `pytest tests/npc/test_profile.py tests/npc/test_prompts.py tests/npc/test_graph.py tests/game/test_review.py tests/game/test_session.py -v`

Expected: FAIL，错误形如 `unexpected keyword argument 'defense_style'` 或 `missing required keyword argument 'quirks'`。

- [ ] **Step 3: 重写 `npc/profile.py`**

替换 `npc/profile.py` 全文为：

```python
from __future__ import annotations
import json
import random
from dataclasses import dataclass

OCCUPATIONS = [
    "建筑设计师", "初中语文老师", "快递站长", "自由摄影师", "程序员",
    "儿科护士", "餐厅老板", "律师助理", "健身教练", "广告文案"
]

CITIES = [
    "成都", "武汉", "杭州", "西安", "长沙",
    "重庆", "南京", "哈尔滨", "厦门", "郑州"
]

DEFENSE_STYLES = ["转移反问", "轻描带过", "微微恼火", "自嘲化解"]

_DEFENSE_STYLE_GUARDS: dict[str, str] = {
    "转移反问": (
        "被质疑时，你的第一反应是好奇对方为什么这么问。你不会直接否认，而是把问题反抛回去。"
        "你对\"为什么你要怀疑我\"比\"证明我自己\"更感兴趣。"
    ),
    "轻描带过": (
        "被质疑时，你觉得这种问题无聊，不值得认真回应。一两个字否认，"
        "然后你已经在想别的事了。你的冷淡不是防御，而是真的不在乎。"
    ),
    "微微恼火": (
        "被质疑时，你会有一点情绪上来——不是愤怒，是那种被人不信任的轻微不舒服。"
        "你会简短地表达这个不适，然后不再解释，因为解释显得你很在乎。"
    ),
    "自嘲化解": (
        "被质疑时，你用幽默把尴尬接住。你会拿自己或者这个问题本身开玩笑，"
        "笑着否认比严肃否认更让人放松警惕。"
    ),
}

_SEALED_TOPIC_GUARDS: dict[str, str] = {
    "转移反问": "被问到这类话题时：\"怎么突然问这个？\"然后把话题引开，不正面回答。",
    "轻描带过": "被问到这类话题时：\"没什么好说的。\"然后主动切到别的事。",
    "微微恼火": "被问到这类话题时：\"这个不聊。\"明确切断，语气比平时硬。",
    "自嘲化解": "被问到这类话题时：\"哈哈这个就别提了。\"笑着挡掉。",
}

GENERATE_PROFILE_PROMPT = """请生成一个真实可信的中国人物档案，用于角色扮演。
必须以 JSON 格式返回，字段如下：
- name: 中文姓名（2-3个字）
- age: 整数，范围 25-50
- occupation: "{occupation}"
- city: "{city}"
- personality: 列表，3-5个性格特征词，要有点矛盾感
- backstory: 字符串，200-400字。要求：
  · 至少有一件事记不太清（时间、人名、地点有模糊）
  · 至少有一个轻微的自我矛盾（比如说不在乎钱，但曾为钱妥协过）
  · 不需要戏剧性——普通人的生活大多是平淡的，过于"有情感重量"的细节反而可疑
  · 真实感优先
- hobbies: 列表，2-4个具体爱好（不要泛化，如「摄影」改为「用胶片拍城市边缘地带」）
- speech_style: 字符串，包含说话节奏、口头禅、方言特色、小怪癖（原 quirks 字段已合并进来，不要单独输出 quirks）
- defense_style: 从["转移反问","轻描带过","微微恼火","自嘲化解"]中选一个，基于 personality 选择最匹配的
- sealed_topics: 列表，1-2个这个人不愿意聊的话题

只返回 JSON，不要其他文字。"""


@dataclass
class NpcProfile:
    name: str
    age: int
    occupation: str
    city: str
    personality: list[str]
    backstory: str
    hobbies: list[str]
    speech_style: str
    defense_style: str
    sealed_topics: list[str]

    def to_system_prompt(self) -> str:
        """生成用于 LLM System Prompt 的人物描述文本。"""
        personality_str = "、".join(self.personality)
        hobbies_str = "；".join(self.hobbies)

        defense_guard = _DEFENSE_STYLE_GUARDS.get(self.defense_style, "")
        sealed_guard = _SEALED_TOPIC_GUARDS.get(self.defense_style, "")

        lines = [
            f"你是 {self.name}，{self.occupation}，{self.age}岁，住在{self.city}。",
            f"性格：{personality_str}",
            f"背景：{self.backstory}",
            f"爱好：{hobbies_str}",
            f"说话风格：{self.speech_style}",
            f"防御姿态：{self.defense_style}",
            f"应对质疑的方式：{defense_guard}",
        ]

        if self.sealed_topics:
            topics_str = "、".join(self.sealed_topics)
            lines.append(f"不想聊的话题：{topics_str}")
            lines.append(f"回避方式：{sealed_guard}")

        return "\n".join(lines)

    def introduction(self) -> str:
        """NPC 开场白（基于档案生成，不调用 LLM）。"""
        return f"你好！我是{self.name}。"


async def generate_npc_profile() -> NpcProfile:
    """调用 LLM 生成一个完整的 NPC 档案。"""
    from langchain_openai import ChatOpenAI
    import config

    occupation = random.choice(OCCUPATIONS)
    city = random.choice(CITIES)

    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=config.TEMPERATURE_THINK,
        openai_api_key=config.OPENAI_API_KEY,
        openai_api_base=config.OPENAI_BASE_URL,
    )
    prompt = GENERATE_PROFILE_PROMPT.format(occupation=occupation, city=city)

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    raw = response.content.strip()

    # 去除可能的 markdown 代码块包裹
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)

    defense_style = data.get("defense_style", "轻描带过")
    if defense_style not in DEFENSE_STYLES:
        defense_style = "轻描带过"

    sealed_topics = data.get("sealed_topics", [])
    if not isinstance(sealed_topics, list):
        sealed_topics = []

    return NpcProfile(
        name=data["name"],
        age=int(data["age"]),
        occupation=data["occupation"],
        city=data["city"],
        personality=data["personality"],
        backstory=data["backstory"],
        hobbies=data["hobbies"],
        speech_style=data["speech_style"],
        defense_style=defense_style,
        sealed_topics=sealed_topics,
    )
```

- [ ] **Step 4: 运行所有受影响测试确认通过**

Run: `pytest tests/npc/test_profile.py tests/npc/test_prompts.py tests/npc/test_graph.py tests/game/test_review.py tests/game/test_session.py -v`

Expected: PASS。

- [ ] **Step 5: 跑全量测试确认无回归**

Run: `pytest -v`

Expected: PASS（全绿）。

- [ ] **Step 6: Commit**

```bash
git add npc/profile.py tests/npc/test_profile.py tests/npc/test_prompts.py tests/npc/test_graph.py tests/game/test_review.py tests/game/test_session.py
git commit -m "refactor(profile): add defense_style/sealed_topics, drop quirks, tighten backstory"
```

---

### Task 2: 重写 THINK_SYSTEM_TEMPLATE

**Files:**
- Modify: `npc/prompts.py:4-14`（`THINK_SYSTEM_TEMPLATE`）
- Modify: `tests/npc/test_prompts.py`（新增 think 内容测试）

**Interfaces:**
- Consumes: Task 1 产出的 `NpcProfile`（含 `defense_style`、`sealed_topics`），`profile.to_system_prompt()` 已注入守则。
- Produces: `THINK_SYSTEM_TEMPLATE` 仍接收 `{profile_context}` 和 `{name}` 占位符；`build_think_prompt()` 签名不变。

- [ ] **Step 1: 在 `tests/npc/test_prompts.py` 末尾追加新的 think 测试**

```python
def test_build_think_prompt_requires_threat_level_first_line(sample_profile):
    """Think prompt 要求独白第一行显式输出威胁等级"""
    messages = build_think_prompt(sample_profile, [], "你是真人吗？")
    system_content = messages[0]["content"]
    assert "威胁等级：低/中/高" in system_content
    assert "第一行" in system_content


def test_build_think_prompt_enforces_100_char_limit(sample_profile):
    """Think prompt 字数上限为 100 字（不再 150）"""
    messages = build_think_prompt(sample_profile, [], "你在做什么？")
    system_content = messages[0]["content"]
    assert "100字" in system_content
    assert "150字" not in system_content


def test_build_think_prompt_prohibits_meta_consciousness(sample_profile):
    """Think prompt 禁止元意识（如'我要证明我是真人'）"""
    messages = build_think_prompt(sample_profile, [], "你是 AI 吗？")
    system_content = messages[0]["content"]
    assert "证明我是真人" in system_content
    assert "不得出现" in system_content or "禁止" in system_content


def test_build_think_prompt_has_five_step_structure(sample_profile):
    """Think prompt 包含五步思考结构关键词"""
    messages = build_think_prompt(sample_profile, [], "你好")
    system_content = messages[0]["content"]
    assert "威胁评估" in system_content
    assert "情绪反应" in system_content
    assert "策略选择" in system_content
    assert "信息门控" in system_content
    assert "意图草稿" in system_content


def test_build_think_prompt_references_defense_style(sample_profile):
    """Think prompt 让策略选择匹配 defense_style"""
    messages = build_think_prompt(sample_profile, [], "你是真人吗？")
    system_content = messages[0]["content"]
    assert "defense_style" in system_content or "防御姿态" in system_content
```

- [ ] **Step 2: 运行新测试确认失败**

Run: `pytest tests/npc/test_prompts.py -v -k "threat_level or 100_char or meta_consciousness or five_step or defense_style"`

Expected: FAIL（新断言在旧 prompt 上找不到关键词）。

- [ ] **Step 3: 重写 `npc/prompts.py` 的 `THINK_SYSTEM_TEMPLATE`**

把 `npc/prompts.py` 中的 `THINK_SYSTEM_TEMPLATE`（当前第 4-14 行）替换为：

```python
THINK_SYSTEM_TEMPLATE = """{profile_context}

重要：你现在正在和一个陌生人对话，这个人怀疑你是 AI。
但你的任务不是"证明自己是真人"——你只是在过自己的生活，对方恰好来问东问西。

请用第一人称内心独白的方式思考下面五步（按顺序）：
1. 威胁评估   对方这句话让我几分警觉？（低/中/高）
2. 情绪反应   我此刻的第一反应是什么感受？（不是分析，是感受）
3. 策略选择   根据我的防御姿态（defense_style），我用什么姿态回应？
4. 信息门控   我有哪些背景细节"可以用"？现在有没有自然引出的理由？没有就不用。
5. 意图草稿   我大概想说什么方向？（一句话，不是完整回复）

输出格式（严格遵守）：
- 第一行必须写：威胁等级：低/中/高
- 第二行起才是自然语言内心独白，不超过100字

关键约束：
- 第 4 步是门控：没有自然引出的理由，就不要用那个细节
- 禁止元意识：内心独白里不得出现"我要证明我是真人"这类表达
- 不要在独白里写完整回复，只写意图方向

只输出内心独白，不要其他文字。"""
```

- [ ] **Step 4: 运行 think 相关测试确认通过**

Run: `pytest tests/npc/test_prompts.py -v`

Expected: PASS（包括原有结构测试和 5 个新测试）。

- [ ] **Step 5: 跑全量测试确认无回归**

Run: `pytest -v`

Expected: PASS。

- [ ] **Step 6: Commit**

```bash
git add npc/prompts.py tests/npc/test_prompts.py
git commit -m "refactor(prompts): rewrite THINK template to threat-tagged 5-step monologue"
```

---

### Task 3: 重写 RESPOND_SYSTEM_TEMPLATE

**Files:**
- Modify: `npc/prompts.py`（`RESPOND_SYSTEM_TEMPLATE`）
- Modify: `tests/npc/test_prompts.py`（新增 respond 内容测试）

**Interfaces:**
- Consumes: Task 2 产出的 think 独白格式（第一行为 `威胁等级：低/中/高`）。
- Produces: `RESPOND_SYSTEM_TEMPLATE` 仍接收 `{profile_context}`、`{name}`、`{inner_monologue}` 占位符；`build_respond_prompt()` 签名不变。

- [ ] **Step 1: 在 `tests/npc/test_prompts.py` 末尾追加新的 respond 测试**

```python
def test_build_respond_prompt_reads_threat_level(sample_profile):
    """Respond prompt 要求读取独白第一行的威胁等级"""
    monologue = "威胁等级：中\n有点试探，我用转移反问挡回去。"
    messages = build_respond_prompt(sample_profile, [], "你是真人吗？", monologue)
    system_content = messages[0]["content"]
    assert "威胁等级" in system_content
    assert "第一行" in system_content


def test_build_respond_prompt_has_length_rules_by_threat(sample_profile):
    """Respond prompt 包含按威胁等级分级的长度规则"""
    monologue = "威胁等级：低\n随便聊聊。"
    messages = build_respond_prompt(sample_profile, [], "在干嘛？", monologue)
    system_content = messages[0]["content"]
    assert "低" in system_content
    assert "中" in system_content
    assert "高" in system_content
    assert "1-2句" in system_content or "1-2 句" in system_content


def test_build_respond_prompt_enforces_info_restraint(sample_profile):
    """Respond prompt 强制信息克制：只用 think 决定用的细节"""
    monologue = "威胁等级：低\n就说刚扎完针，别的不提。"
    messages = build_respond_prompt(sample_profile, [], "在干嘛？", monologue)
    system_content = messages[0]["content"]
    assert "内心独白" in system_content
    assert "不要引入" in system_content or "只能用" in system_content


def test_build_respond_prompt_requires_emotion_through_tone(sample_profile):
    """Respond prompt 要求情绪透出来而不是演出来"""
    monologue = "威胁等级：高\n有点不舒服。"
    messages = build_respond_prompt(sample_profile, [], "你是 AI 吧？", monologue)
    system_content = messages[0]["content"]
    assert "透出来" in system_content or "透出" in system_content
    assert "不要说出情绪" in system_content or "不要表演" in system_content


def test_build_respond_prompt_removed_old_rules(sample_profile):
    """Respond prompt 不再包含被删除的两条旧规则"""
    monologue = "威胁等级：低\n随便聊聊。"
    messages = build_respond_prompt(sample_profile, [], "你好", monologue)
    system_content = messages[0]["content"]
    assert "口语瑕疵" not in system_content
    assert "有个人色彩" not in system_content
```

- [ ] **Step 2: 运行新测试确认失败**

Run: `pytest tests/npc/test_prompts.py -v -k "reads_threat_level or length_rules or info_restraint or emotion_through_tone or removed_old_rules"`

Expected: FAIL。

- [ ] **Step 3: 重写 `npc/prompts.py` 的 `RESPOND_SYSTEM_TEMPLATE`**

把 `npc/prompts.py` 中的 `RESPOND_SYSTEM_TEMPLATE` 替换为：

```python
RESPOND_SYSTEM_TEMPLATE = """{profile_context}

你刚才的内心想法是：
{inner_monologue}

基于这个想法，用 {name} 的说话风格回复玩家。

第一步：从内心独白第一行读取"威胁等级：低/中/高"，按下表决定回复长度：
- 低（闲聊）：1-2句，可以随意一点
- 中（试探）：1句核心 + 最多1句转移，不展开
- 高（直接质疑）：越短越有力，1句就够，留白比解释更像真人

第二步：实现内心独白里的那个意图，遵循三个控制维度：

① 长度由威胁等级决定（见上表）

② 情绪"透出来"而不是"演出来"
如果内心独白里有情绪，让它影响语气，但不要说出情绪本身。
- 错误示范："哎呀你啷个问这种问题嘛！"（把情绪表演给对方看）
- 正确示范："问这个干啥。"（情绪在语气里，没有解释）

③ 信息克制：只能用内心独白里"决定用"的细节
如果内心独白里没有提到某个背景细节，不要在回复里引入它。

其他要求：
- 完全不能提到自己是 AI 或机器人
- 只输出对话内容本身，不要输出任何动作描述或括号里的舞台提示（如「（微笑）」「（放下杯子）」等）
- 不要以「某某：」开头，直接输出回复内容"""
```

- [ ] **Step 4: 运行 respond 相关测试确认通过**

Run: `pytest tests/npc/test_prompts.py -v`

Expected: PASS（包括原有测试和 5 个新测试）。

- [ ] **Step 5: 跑全量测试确认无回归**

Run: `pytest -v`

Expected: PASS（全绿）。

- [ ] **Step 6: Commit**

```bash
git add npc/prompts.py tests/npc/test_prompts.py
git commit -m "refactor(prompts): rewrite RESPOND template to threat-driven length and info restraint"
```

---

## Self-Review

**1. Spec coverage:**
- 改动一·新增 `defense_style` 字段 → Task 1 Step 3（dataclass + `DEFENSE_STYLES`）
- 改动一·新增 `sealed_topics` 字段 → Task 1 Step 3
- 改动一·`backstory` 生成要求（模糊+矛盾+不戏剧性）→ Task 1 Step 3（`GENERATE_PROFILE_PROMPT`）
- 改动一·删除 `quirks` 并入 `speech_style` → Task 1 Step 3
- 改动一·`GENERATE_PROFILE_PROMPT` 概要 → Task 1 Step 3
- 改动二·五步思考结构 → Task 2 Step 3
- 改动二·100 字上限 → Task 2 Step 3 + test_build_think_prompt_enforces_100_char_limit
- 改动二·禁止元意识 → Task 2 Step 3 + test_build_think_prompt_prohibits_meta_consciousness
- 改动二·威胁等级显式化（第一行）→ Task 2 Step 3 + test_build_think_prompt_requires_threat_level_first_line
- 改动三·长度由威胁等级决定 → Task 3 Step 3 + test_build_respond_prompt_has_length_rules_by_threat
- 改动三·情绪透出来不演出来 → Task 3 Step 3 + test_build_respond_prompt_requires_emotion_through_tone
- 改动三·信息克制 → Task 3 Step 3 + test_build_respond_prompt_enforces_info_restraint
- 改动三·删除两条旧规则 → Task 3 Step 3 + test_build_respond_prompt_removed_old_rules
- 改动四·`to_system_prompt()` 注入 `defense_style` 守则 → Task 1 Step 3（`_DEFENSE_STYLE_GUARDS`）+ test_npc_profile_to_system_prompt_includes_defense_style_guard
- 改动四·`sealed_topics` 按 `defense_style` 分型回避 → Task 1 Step 3（`_SEALED_TOPIC_GUARDS`）+ test_npc_profile_to_system_prompt_includes_sealed_topics

无遗漏。

**2. Placeholder scan:** 无 TBD/TODO/「类似 Task N」。每个 Step 都有完整代码。

**3. Type consistency:**
- `NpcProfile` 构造签名在 Task 1 定义后，Task 2/3 的 `sample_profile` fixture（已在 Task 1 更新）使用同一签名 ✓
- `build_think_prompt` / `build_respond_prompt` 签名在三个 Task 中均不变 ✓
- `defense_style` 字符串值在 `DEFENSE_STYLES`、`_DEFENSE_STYLE_GUARDS`、`_SEALED_TOPIC_GUARDS` 三处使用同一组 key（`转移反问`/`轻描带过`/`微微恼火`/`自嘲化解`）✓
- `THINK_SYSTEM_TEMPLATE` 和 `RESPOND_SYSTEM_TEMPLATE` 的占位符（`{profile_context}`、`{name}`、`{inner_monologue}`）与 `build_think_prompt`/`build_respond_prompt` 中的 `.format()` 调用一致 ✓
