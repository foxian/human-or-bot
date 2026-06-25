from __future__ import annotations
from game.session import GameSession, ConversationTurn


class ReviewMode:
    """游戏结束后的回顾模式，允许玩家查看任意轮次的对话和内心独白。"""

    def __init__(self, session: GameSession) -> None:
        self._session = session

    def total_turns(self) -> int:
        """返回本局游戏的总对话轮数。"""
        return len(self._session.conversation_history)

    def get_turn(self, turn_number: int) -> ConversationTurn:
        """
        获取指定轮次的对话记录（含内心独白）。

        Args:
            turn_number: 轮次编号，从 1 开始。

        Raises:
            IndexError: 如果 turn_number 超出范围。
        """
        if turn_number < 1 or turn_number > self.total_turns():
            raise IndexError(
                f"轮次 {turn_number} 不存在，有效范围：1-{self.total_turns()}"
            )
        return self._session.conversation_history[turn_number - 1]
