# SDD Progress Ledger — NPC Behavior Overhaul

Plan: `docs/superpowers/plans/2026-06-26-npc-behavior-overhaul.md`
Branch: main
Pre-flight commit: e8c56c4 (chore: shorten respond length and add speech imperfections tuning)

## Tasks

- [x] Task 1: Profile 数据结构重构
- [x] Task 2: 重写 THINK_SYSTEM_TEMPLATE
- [x] Task 3: 重写 RESPOND_SYSTEM_TEMPLATE
- [x] Fix: add missing tests from final review

## Completion Log

(pre-flight e8c56c4 committed before Task 1)
Task 1: complete (commits e8c56c4..c55bba9, review clean on diff — spec ✅; report file was stale LangSmith content, controller rewrote it and cleaned stale SDD scratch files)
Task 2: complete (commits c55bba9..72bad5a, review clean — spec ✅, Approved)
Task 3: complete (commits 72bad5a..13e72b7, review clean — spec ✅, Approved)
Fix 4: complete (commits 13e72b7..3458efc) — added 2 tests for sealed_topics=[] omission and defense_style validation fallback; final whole-branch review's remaining Important (threat-level parsing robustness) is a plan-mandated trade-off (approach C, prompt-only) flagged to user, not auto-fixed
Final suite: 34 passed, 0 warnings (run via .venv/Scripts/python.exe -m pytest)
