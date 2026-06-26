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
