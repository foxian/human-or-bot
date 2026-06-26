from __future__ import annotations
from npc.profile import NpcProfile

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


def _format_history(conversation_history: list[dict]) -> str:
    """将对话历史格式化为文本，供 prompt 使用。"""
    if not conversation_history:
        return ""
    lines = ["之前的对话："]
    for msg in conversation_history:
        role = "玩家" if msg["role"] == "user" else "你"
        lines.append(f"{role}：{msg['content']}")
    return "\n".join(lines) + "\n\n"


def build_think_prompt(
    profile: NpcProfile,
    conversation_history: list[dict],
    player_input: str,
) -> list[dict]:
    """构建 ThinkNode 使用的消息列表。"""
    system_content = THINK_SYSTEM_TEMPLATE.format(
        profile_context=profile.to_system_prompt(),
        name=profile.name,
    )
    history_text = _format_history(conversation_history)
    user_content = f"{history_text}玩家问：{player_input}\n\n请写出你的内心独白："
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_respond_prompt(
    profile: NpcProfile,
    conversation_history: list[dict],
    player_input: str,
    inner_monologue: str,
) -> list[dict]:
    """构建 RespondNode 使用的消息列表。"""
    system_content = RESPOND_SYSTEM_TEMPLATE.format(
        profile_context=profile.to_system_prompt(),
        name=profile.name,
        inner_monologue=inner_monologue,
    )
    history_text = _format_history(conversation_history)
    user_content = f"{history_text}玩家：{player_input}\n\n{profile.name} 的回复："
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
