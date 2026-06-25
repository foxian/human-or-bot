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
        quirks=["喜欢用「其实」开头"]
    )
    assert profile.name == "测试人"
    assert profile.age == 30
    assert len(profile.personality) == 2
    assert len(profile.hobbies) == 2
    assert len(profile.quirks) == 1


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
        quirks=["被问到感情话题时用「嗯」开头"]
    )
    prompt = profile.to_system_prompt()
    assert "陈建国" in prompt
    assert "34" in prompt
    assert "建筑设计师" in prompt
    assert "成都" in prompt
