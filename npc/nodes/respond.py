from __future__ import annotations
from typing import TYPE_CHECKING
from langchain_openai import ChatOpenAI
from npc.prompts import build_respond_prompt
import config

if TYPE_CHECKING:
    from npc.graph import GraphState


async def respond_node(state: "GraphState") -> dict:
    """RespondNode：基于内心独白生成对外回复。"""
    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=config.TEMPERATURE_RESPOND,
        max_tokens=config.RESPOND_MAX_TOKENS,
        openai_api_key=config.OPENAI_API_KEY,
        openai_api_base=config.OPENAI_BASE_URL,
    )
    messages = build_respond_prompt(
        profile=state["npc_profile"],
        conversation_history=state["conversation_history"],
        player_input=state["player_input"],
        inner_monologue=state["inner_monologue"],
    )
    response = await llm.ainvoke(messages)
    return {"npc_response": response.content.strip()}
