# NPC 机器人 · 反向图灵测试

命令行「反向图灵测试」游戏：NPC 拥有真实的人类身份设定，尽力伪装成人类，你有 10 次机会识破它是 AI。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY

# 3. 运行游戏
python cli/main.py
```

## 游戏指令

| 指令 | 说明 |
|------|------|
| `/judge ai` | 宣判：我认为对方是 AI |
| `/judge human` | 宣判：我认为对方是人类 |
| `/review` | 游戏结束后回顾对话与内心独白 |
| `/quit` | 退出游戏 |

## 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
NPC/
├── npc/
│   ├── profile.py      # NpcProfile 数据类 + 生成逻辑
│   ├── graph.py        # LangGraph 双节点状态图
│   ├── nodes/
│   │   ├── think.py    # 内心独白节点
│   │   └── respond.py  # 对外回复节点
│   └── prompts.py      # Prompt 模板
├── game/
│   ├── session.py      # 游戏会话管理
│   └── review.py       # 回顾模式
├── cli/
│   └── main.py         # CLI 入口
├── tests/
├── config.py           # 配置
└── requirements.txt
```
