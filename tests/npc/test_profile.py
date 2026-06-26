import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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


def test_npc_profile_to_system_prompt_omits_sealed_topics_when_empty():
    """sealed_topics 为空时，to_system_prompt() 不输出 sealed_topics 相关段落"""
    profile = NpcProfile(
        name="测试人", age=30, occupation="工程师", city="北京",
        personality=["认真"], backstory="测试背景",
        hobbies=["读书"], speech_style="简洁",
        defense_style="轻描带过",
        sealed_topics=[],
    )
    prompt = profile.to_system_prompt()
    assert "不想聊的话题" not in prompt
    assert "回避方式" not in prompt


@pytest.mark.asyncio
async def test_generate_npc_profile_falls_back_on_invalid_defense_style():
    """generate_npc_profile() 对无效 defense_style 回退到 '轻描带过'"""
    fake_raw_json = (
        '{"name":"测试人","age":30,"occupation":"工程师","city":"北京",'
        '"personality":["认真"],"backstory":"测试背景",'
        '"hobbies":["读书"],"speech_style":"简洁",'
        '"defense_style":"不存在的姿态","sealed_topics":["x"]}'
    )
    mock_response = MagicMock()
    mock_response.content = fake_raw_json
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("langchain_openai.ChatOpenAI", return_value=mock_llm):
        profile = await generate_npc_profile()

    assert profile.defense_style == "轻描带过"
    assert profile.sealed_topics == ["x"]
    assert profile.name == "测试人"
