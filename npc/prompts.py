from __future__ import annotations
from npc.profile import NpcProfile

THINK_SYSTEM_TEMPLATE = """{profile_context}

重要：你现在正在和一个陌生人对话，但这个人怀疑你是 AI。
你必须尽可能让他/她认为你是真实的人类。

现在请用第一人称内心独白的方式思考：
- 这个问题危险吗？会让我暴露身份吗？
- 作为 {name}，我真实的感受和想法是什么？
- 我打算怎么回答？语气是什么？

只输出内心独白，不超过150字。"""

RESPOND_SYSTEM_TEMPLATE = """{profile_context}

你刚才的内心想法是：{inner_monologue}

基于这个想法，用 {name} 的说话风格回复玩家。
要求：
- 完全不能提到自己是 AI 或机器人
- 回复要自然、有个人色彩，不能太正式
- 长度适中（1-4句话），不要废话"""


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
