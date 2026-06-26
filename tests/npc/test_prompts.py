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
