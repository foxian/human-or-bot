import pytest
from unittest.mock import AsyncMock, patch
from npc.profile import NpcProfile
from game.session import GameSession, ConversationTurn


@pytest.fixture
def sample_profile():
    return NpcProfile(
        name="陈建国", age=34, occupation="建筑设计师", city="成都",
        personality=["内敛"], backstory="测试背景",
        hobbies=["摄影"], speech_style="简洁", quirks=["用「其实」开头"]
    )


@pytest.fixture
def session(sample_profile):
    return GameSession(npc_profile=sample_profile)


def test_initial_state(session):
    """初始状态：10次提问，未结束，无宣判"""
    assert session.questions_left == 10
    assert session.is_over is False
    assert session.verdict is None
    assert session.conversation_history == []


@pytest.mark.asyncio
async def test_ask_decrements_questions(session):
    """每次提问减少 questions_left"""
    with patch("game.session.run_npc_turn", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = ("内心独白", "NPC回复")
        await session.ask("你好")

    assert session.questions_left == 9
    assert len(session.conversation_history) == 1


@pytest.mark.asyncio
async def test_ask_returns_conversation_turn(session):
    """ask() 返回 ConversationTurn 对象"""
    with patch("game.session.run_npc_turn", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = ("这是内心独白", "这是NPC回复")
        turn = await session.ask("你喜欢什么？")

    assert isinstance(turn, ConversationTurn)
    assert turn.turn_number == 1
    assert turn.player_question == "你喜欢什么？"
    assert turn.inner_monologue == "这是内心独白"
    assert turn.npc_response == "这是NPC回复"


@pytest.mark.asyncio
async def test_ask_game_over_when_no_questions(session):
    """提问次数用尽后 is_over 变为 True"""
    session.questions_left = 1
    with patch("game.session.run_npc_turn", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = ("独白", "回复")
        await session.ask("最后一问")

    assert session.questions_left == 0
    assert session.is_over is True


def test_judge_sets_verdict(session):
    """judge() 设置宣判结果并结束游戏"""
    session.judge("ai")
    assert session.verdict == "ai"
    assert session.is_over is True


def test_judge_invalid_verdict(session):
    """judge() 接受非预期值时应引发 ValueError"""
    with pytest.raises(ValueError):
        session.judge("maybe")


def test_get_lc_history_empty(session):
    """初始状态下 get_lc_history() 返回空列表"""
    assert session.get_lc_history() == []


@pytest.mark.asyncio
async def test_get_lc_history_after_turn(session):
    """提问后 get_lc_history() 包含 user 和 assistant 条目"""
    with patch("game.session.run_npc_turn", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = ("内心独白", "NPC回复")
        await session.ask("你好")

    history = session.get_lc_history()
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "你好"}
    assert history[1] == {"role": "assistant", "content": "NPC回复"}
