from __future__ import annotations
from typing import TYPE_CHECKING
from langchain_openai import ChatOpenAI
from npc.prompts import build_think_prompt
import config

if TYPE_CHECKING:
    from npc.graph import GraphState


async def think_node(state: "GraphState") -> dict:
    """ThinkNode：生成 NPC 的内心独白（不显示给玩家）。"""
    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=config.TEMPERATURE_THINK,
        max_tokens=config.THINK_MAX_TOKENS,
        openai_api_key=config.OPENAI_API_KEY,
        openai_api_base=config.OPENAI_BASE_URL,
    )
    messages = build_think_prompt(
        profile=state["npc_profile"],
        conversation_history=state["conversation_history"],
        player_input=state["player_input"],
    )
    response = await llm.ainvoke(messages)
    return {"inner_monologue": response.content.strip()}
