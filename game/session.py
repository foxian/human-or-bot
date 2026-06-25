from __future__ import annotations
from dataclasses import dataclass, field
from npc.profile import NpcProfile
from npc.graph import run_npc_turn
import config


@dataclass
class ConversationTurn:
    turn_number: int
    player_question: str
    inner_monologue: str
    npc_response: str


@dataclass
class GameSession:
    npc_profile: NpcProfile
    questions_left: int = field(default_factory=lambda: config.MAX_QUESTIONS)
    conversation_history: list[ConversationTurn] = field(default_factory=list)
    is_over: bool = False
    verdict: str | None = None

    async def ask(self, player_input: str) -> ConversationTurn:
        """玩家提问一轮，调用 LangGraph，记录结果。"""
        if self.is_over:
            raise RuntimeError("游戏已结束，无法继续提问。")

        lc_history = self.get_lc_history()
        inner_monologue, npc_response = await run_npc_turn(
            self.npc_profile, lc_history, player_input
        )

        turn = ConversationTurn(
            turn_number=len(self.conversation_history) + 1,
            player_question=player_input,
            inner_monologue=inner_monologue,
            npc_response=npc_response,
        )
        self.conversation_history.append(turn)
        self.questions_left -= 1

        if self.questions_left <= 0:
            self.is_over = True

        return turn

    def judge(self, verdict: str) -> None:
        """玩家宣判：verdict 必须是 'ai' 或 'human'。"""
        if verdict not in ("ai", "human"):
            raise ValueError(f"无效宣判值：{verdict!r}，必须是 'ai' 或 'human'")
        self.verdict = verdict
        self.is_over = True

    def get_lc_history(self) -> list[dict]:
        """将对话历史转换为 LangChain 格式的消息列表。"""
        messages = []
        for turn in self.conversation_history:
            messages.append({"role": "user", "content": turn.player_question})
            messages.append({"role": "assistant", "content": turn.npc_response})
        return messages
