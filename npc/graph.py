from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END
from npc.profile import NpcProfile
from npc.nodes.think import think_node
from npc.nodes.respond import respond_node


class GraphState(TypedDict):
    npc_profile: NpcProfile
    conversation_history: list[dict]
    player_input: str
    inner_monologue: str
    npc_response: str


def _build_graph() -> StateGraph:
    """构建 LangGraph 双节点状态图。"""
    builder = StateGraph(GraphState)
    builder.add_node("think", think_node)
    builder.add_node("respond", respond_node)
    builder.set_entry_point("think")
    builder.add_edge("think", "respond")
    builder.add_edge("respond", END)
    return builder.compile()


_graph = _build_graph()


async def run_npc_turn(
    profile: NpcProfile,
    conversation_history: list[dict],
    player_input: str,
) -> tuple[str, str]:
    """
    执行一轮 NPC 对话（ThinkNode -> RespondNode）。

    Returns:
        (inner_monologue, npc_response)
    """
    initial_state: GraphState = {
        "npc_profile": profile,
        "conversation_history": conversation_history,
        "player_input": player_input,
        "inner_monologue": "",
        "npc_response": "",
    }
    result = await _graph.ainvoke(initial_state)
    return result["inner_monologue"], result["npc_response"]
