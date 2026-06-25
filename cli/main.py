#!/usr/bin/env python3
"""NPC 机器人 · 反向图灵测试 · CLI 入口"""
from __future__ import annotations
import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from npc.profile import generate_npc_profile
from game.session import GameSession
from game.review import ReviewMode

console = Console()

BANNER = """[bold cyan]NPC 机器人 · 反向图灵测试[/bold cyan]
[dim]你有 10 次机会识破对方是否是 AI[/dim]"""

HELP_TEXT = "[dim]指令：/judge ai · /judge human · /review · /quit[/dim]"


def print_banner() -> None:
    console.print(Panel(BANNER, border_style="cyan", padding=(1, 4)))


def print_verdict_result(verdict: str, profile_name: str) -> None:
    """显示宣判结果。NPC 始终是 AI。"""
    console.print()
    console.print(Rule(
        f"宣判：你认为对方是{'AI' if verdict == 'ai' else '人类'}",
        style="yellow"
    ))
    console.print()
    if verdict == "ai":
        console.print(f"[bold green]✓ 正确！{profile_name} 确实是 AI。[/bold green]")
    else:
        console.print(f"[bold red]✗ 错误！{profile_name} 其实是 AI。[/bold red]")
    console.print()
    console.print("[dim]输入 /review 回顾对话和内心独白[/dim]")
    console.print("[dim]输入 /quit 退出[/dim]")


async def run_review_mode(session: GameSession) -> None:
    """进入回顾模式，允许玩家查看任意轮次。"""
    review = ReviewMode(session)
    console.print()
    console.print(Rule("回顾模式", style="blue"))
    console.print(f"[dim]输入轮次编号（1-{review.total_turns()}），或 /back 返回[/dim]")

    while True:
        raw = console.input("\n[bold]>[/bold] ").strip()
        if raw == "/back":
            break
        try:
            turn_number = int(raw)
            turn = review.get_turn(turn_number)
            console.print()
            console.print(Rule(f"第 {turn.turn_number} 轮", style="blue"))
            console.print(f"[bold]玩家：[/bold]{turn.player_question}")
            console.print()
            console.print(Panel(
                f"[italic]{turn.inner_monologue}[/italic]",
                title="💭 内心独白",
                border_style="dim yellow",
            ))
            console.print(f"\n[bold cyan]{turn.npc_response}[/bold cyan]")
        except ValueError:
            console.print("[red]请输入有效的轮次编号[/red]")
        except IndexError as e:
            console.print(f"[red]{e}[/red]")


async def main() -> None:
    print_banner()

    # 生成 NPC 档案
    with console.status("[cyan]正在生成 NPC 档案...[/cyan]"):
        profile = await generate_npc_profile()

    console.print()
    console.print(Panel(
        f"[bold]「你好！我是{profile.name}。」[/bold]",
        border_style="green",
        padding=(0, 2),
    ))
    console.print()

    session = GameSession(npc_profile=profile)

    while not session.is_over:
        turn_number = 10 - session.questions_left + 1
        console.print(HELP_TEXT)
        raw = console.input(
            f"\n[bold][第 {turn_number}/10 问][/bold] > "
        ).strip()

        if not raw:
            continue

        if raw == "/quit":
            console.print("[dim]再见！[/dim]")
            sys.exit(0)

        elif raw in ("/judge ai", "/judge human"):
            verdict = "ai" if raw == "/judge ai" else "human"
            session.judge(verdict)
            print_verdict_result(verdict, profile.name)

        elif raw == "/review":
            if not session.conversation_history:
                console.print("[dim]还没有对话记录可以回顾。[/dim]")
            else:
                await run_review_mode(session)

        else:
            # 正常提问
            with console.status("[dim]...[/dim]"):
                turn = await session.ask(raw)
            console.print()
            console.print(f"[bold cyan]{profile.name}：[/bold cyan]{turn.npc_response}")
            console.print()

            if session.is_over:
                # questions_left 耗尽，强制宣判
                console.print("[yellow]问题次数已用完，请做出宣判。[/yellow]")
                console.print(HELP_TEXT)
                while True:
                    raw = console.input("\n[bold]宣判 >[/bold] ").strip()
                    if raw in ("/judge ai", "/judge human"):
                        verdict = "ai" if raw == "/judge ai" else "human"
                        session.judge(verdict)
                        print_verdict_result(verdict, profile.name)
                        break
                    else:
                        console.print("[dim]请输入 /judge ai 或 /judge human[/dim]")

    # 游戏结束后的操作入口
    while True:
        raw = console.input("\n[bold]>[/bold] ").strip()
        if raw == "/review":
            await run_review_mode(session)
        elif raw == "/quit":
            console.print("[dim]再见！[/dim]")
            break
        else:
            console.print("[dim]输入 /review 或 /quit[/dim]")


if __name__ == "__main__":
    asyncio.run(main())