import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from npc.profile import NpcProfile
from npc.graph import GraphState, run_npc_turn


@pytest.fixture
def sample_profile():
    return NpcProfile(
        name="陈建国", age=34, occupation="建筑设计师", city="成都",
        personality=["内敛"], backstory="测试背景",
        hobbies=["摄影"], speech_style="简洁", quirks=["用「其实」开头"]
    )


def test_graph_state_typing(sample_profile):
    """GraphState 可以用字典形式构造（TypedDict 验证）"""
    state: GraphState = {
        "npc_profile": sample_profile,
        "conversation_history": [],
        "player_input": "你好",
        "inner_monologue": "",
        "npc_response": "",
    }
    assert state["npc_profile"].name == "陈建国"
    assert state["player_input"] == "你好"


@pytest.mark.asyncio
async def test_run_npc_turn_returns_tuple(sample_profile):
    """run_npc_turn 返回 (inner_monologue, npc_response) 元组"""
    with patch("npc.nodes.think.ChatOpenAI") as MockThinkLLM, \
         patch("npc.nodes.respond.ChatOpenAI") as MockRespondLLM:

        mock_think_instance = AsyncMock()
        mock_think_instance.ainvoke.return_value = MagicMock(content="内心独白")
        MockThinkLLM.return_value = mock_think_instance

        mock_respond_instance = AsyncMock()
        mock_respond_instance.ainvoke.return_value = MagicMock(content="对外回复")
        MockRespondLLM.return_value = mock_respond_instance

        monologue, response = await run_npc_turn(sample_profile, [], "你好")

    assert isinstance(monologue, str)
    assert isinstance(response, str)
    assert monologue == "内心独白"
    assert response == "对外回复"
