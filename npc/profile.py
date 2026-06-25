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

GENERATE_PROFILE_PROMPT = """请生成一个真实可信的中国人物档案，用于角色扮演。
必须以 JSON 格式返回，字段如下：
- name: 中文姓名（2-3个字）
- age: 整数，范围 25-50
- occupation: "{occupation}"
- city: "{city}"
- personality: 列表，3-5个性格特征词，要有点矛盾感
- backstory: 字符串，200-400字，包含具体地名、具体事件、有情感重量的经历
- hobbies: 列表，2-4个具体爱好（不要泛化，如「摄影」改为「用胶片拍城市边缘地带」）
- speech_style: 字符串，描述说话风格（语气、口头禅、方言特色等）
- quirks: 列表，2-3个小怪癖或习惯

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
    quirks: list[str]

    def to_system_prompt(self) -> str:
        """生成用于 LLM System Prompt 的人物描述文本。"""
        personality_str = "、".join(self.personality)
        hobbies_str = "；".join(self.hobbies)
        quirks_str = "；".join(self.quirks)
        return (
            f"你是 {self.name}，{self.occupation}，{self.age}岁，住在{self.city}。\n"
            f"性格：{personality_str}\n"
            f"背景：{self.backstory}\n"
            f"爱好：{hobbies_str}\n"
            f"说话风格：{self.speech_style}\n"
            f"小怪癖：{quirks_str}"
        )

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
    return NpcProfile(
        name=data["name"],
        age=int(data["age"]),
        occupation=data["occupation"],
        city=data["city"],
        personality=data["personality"],
        backstory=data["backstory"],
        hobbies=data["hobbies"],
        speech_style=data["speech_style"],
        quirks=data["quirks"],
    )
