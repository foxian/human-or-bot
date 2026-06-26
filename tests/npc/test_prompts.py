import pytest
from npc.profile import NpcProfile
from npc.prompts import build_think_prompt, build_respond_prompt


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


def test_build_think_prompt_structure(sample_profile):
    """ThinkNode prompt 包含 system 和 user 两条消息"""
    messages = build_think_prompt(sample_profile, [], "你平时喜欢做什么？")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_build_think_prompt_contains_key_info(sample_profile):
    """ThinkNode system prompt 包含人物核心信息"""
    messages = build_think_prompt(sample_profile, [], "你平时喜欢做什么？")
    system_content = messages[0]["content"]
    assert "陈建国" in system_content
    assert "建筑设计师" in system_content
    assert "成都" in system_content


def test_build_think_prompt_user_contains_question(sample_profile):
    """ThinkNode user prompt 包含玩家问题"""
    messages = build_think_prompt(sample_profile, [], "你有没有哭过？")
    user_content = messages[1]["content"]
    assert "你有没有哭过？" in user_content


def test_build_respond_prompt_contains_monologue(sample_profile):
    """RespondNode prompt 包含内心独白"""
    monologue = "这个问题有点敏感，我要小心回答。"
    messages = build_respond_prompt(sample_profile, [], "你有没有哭过？", monologue)
    system_content = messages[0]["content"]
    assert "这个问题有点敏感，我要小心回答。" in system_content


def test_build_think_prompt_with_history(sample_profile):
    """ThinkNode prompt 包含对话历史"""
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好啊"}
    ]
    messages = build_think_prompt(sample_profile, history, "你在哪工作？")
    user_content = messages[1]["content"]
    assert "你好" in user_content
