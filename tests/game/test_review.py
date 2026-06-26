import pytest
from npc.profile import NpcProfile
from game.session import GameSession, ConversationTurn
from game.review import ReviewMode


@pytest.fixture
def session_with_history():
    profile = NpcProfile(
        name="测试人", age=30, occupation="工程师", city="北京",
        personality=["认真"], backstory="测试背景",
        hobbies=["读书"], speech_style="简洁",
        defense_style="轻描带过", sealed_topics=[],
    )
    session = GameSession(npc_profile=profile)
    session.conversation_history = [
        ConversationTurn(1, "你好", "想了想怎么回答", "你好啊"),
        ConversationTurn(2, "你在哪工作？", "这个安全", "在成都一家设计公司"),
    ]
    session.is_over = True
    return session


def test_review_mode_total_turns(session_with_history):
    """total_turns() 返回正确的对话轮数"""
    review = ReviewMode(session_with_history)
    assert review.total_turns() == 2


def test_review_mode_get_turn(session_with_history):
    """get_turn(1) 返回第一轮的 ConversationTurn"""
    review = ReviewMode(session_with_history)
    turn = review.get_turn(1)
    assert turn.player_question == "你好"
    assert turn.inner_monologue == "想了想怎么回答"
    assert turn.npc_response == "你好啊"


def test_review_mode_get_turn_out_of_range(session_with_history):
    """get_turn() 越界时引发 IndexError"""
    review = ReviewMode(session_with_history)
    with pytest.raises(IndexError):
        review.get_turn(0)
    with pytest.raises(IndexError):
        review.get_turn(3)
