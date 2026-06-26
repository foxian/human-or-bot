# 前后端分离架构设计方案

**日期:** 2026-06-26
**状态:** 设计中
**作者:** Claude Code

---

## 1. 概述

本项目是一款基于 LangGraph 构建的"NPC 机器人反向图灵测试"命令行游戏。为了实现更好的架构解耦、支持多种前端（CLI 和未来的 Web）以及方便未来扩展，本方案将项目重构为**前后端分离架构**：

- **后端:** Python + FastAPI 提供 REST API
- **前端 1:** CLI 客户端（通过 HTTP 调用 API）
- **前端 2:** Web 前端（预留，后期实现）

---

## 2. 架构设计

### 2.1 新的目录结构

```
npc/
├── core/                    # 核心业务逻辑（纯 Python，无框架依赖）
│   ├── npc/
│   │   ├── profile.py       # NpcProfile（保持原样）
│   │   ├── graph.py         # LangGraph（保持原样）
│   │   ├── nodes/
│   │   │   ├── think.py
│   │   │   └── respond.py
│   │   └── prompts.py
│   └── game/
│       ├── session.py       # GameSession 重构，移除 CLI 相关
│       └── review.py        # ReviewMode
│
├── storage/                 # 会话存储抽象
│   ├── base.py              # 存储接口定义
│   ├── memory.py            # 内存实现（前期用）
│   └── redis.py             # Redis 实现（后期加）
│
├── api/                     # FastAPI 后端
│   ├── main.py              # FastAPI 应用入口
│   ├── dependencies.py      # 依赖注入（存储、配置等）
│   ├── schemas.py           # Pydantic 模型（请求/响应 DTO）
│   └── routes/
│       ├── sessions.py      # 会话相关 API
│       └── health.py        # 健康检查
│
├── cli/                     # CLI 客户端（重构版）
│   ├── main.py
│   └── api_client.py        # 封装 API 调用
│
├── web/                     # Web 前端（预留，后期加）
│
├── tests/                   # 测试
│   ├── core/
│   ├── storage/
│   └── api/
│
└── config.py                # 配置（保持原样）
```

### 2.2 架构原则

1. **核心逻辑纯粹化** - `core/` 下的代码不依赖 FastAPI 或任何 Web 框架
2. **存储抽象化** - 通过统一接口访问会话存储，内存/Redis 可互换
3. **API 薄化** - `api/` 只负责 HTTP 层，业务逻辑委托给 `core/`
4. **客户端独立** - CLI 通过 HTTP 调用 API，不直接依赖 `core/`

---

## 3. REST API 设计

### 3.1 端点概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions` | 创建新游戏会话 |
| GET | `/api/sessions/{session_id}` | 获取会话状态 |
| POST | `/api/sessions/{session_id}/turns` | 玩家提问一轮 |
| POST | `/api/sessions/{session_id}/judge` | 玩家宣判（AI/human）|
| GET | `/api/sessions/{session_id}/turns/{turn_number}` | 获取单轮详情（含内心独白）|
| GET | `/health` | 健康检查 |

### 3.2 详细接口定义

#### 3.2.1 创建会话 `POST /api/sessions`

**请求体:** 空

**响应 (201):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "npc": {
    "name": "陈建国",
    "age": 34,
    "occupation": "建筑设计师",
    "city": "成都",
    "introduction": "你好！我是陈建国。"
  },
  "questions_left": 10,
  "is_over": false
}
```

#### 3.2.2 获取会话 `GET /api/sessions/{session_id}`

**响应 (200):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "npc": {
    "name": "陈建国",
    "age": 34,
    "occupation": "建筑设计师",
    "city": "成都"
  },
  "questions_left": 8,
  "is_over": false,
  "verdict": null,
  "turns": [
    {
      "turn_number": 1,
      "player_question": "你好",
      "npc_response": "你好啊！"
    }
  ]
}
```

**注意:** `turns` 列表中**不包含** `inner_monologue`，需要通过单独的端点获取。

#### 3.2.3 提问 `POST /api/sessions/{session_id}/turns`

**请求体:**
```json
{
  "question": "你平时喜欢做什么？"
}
```

**响应 (200):**
```json
{
  "turn_number": 2,
  "player_question": "你平时喜欢做什么？",
  "npc_response": "我喜欢用胶片拍城市边缘地带，周末偶尔去徒步。",
  "questions_left": 7,
  "is_over": false
}
```

**错误响应 (404):**
```json
{
  "detail": "Session not found"
}
```

**错误响应 (409):**
```json
{
  "detail": "Game is already over"
}
```

#### 3.2.4 宣判 `POST /api/sessions/{session_id}/judge`

**请求体:**
```json
{
  "verdict": "ai"
}
```

**响应 (200):**
```json
{
  "verdict": "ai",
  "correct": true,
  "is_over": true
}
```

**错误响应 (400):**
```json
{
  "detail": "Invalid verdict: must be 'ai' or 'human'"
}
```

#### 3.2.5 获取单轮详情（含内心独白）`GET /api/sessions/{session_id}/turns/{turn_number}`

**响应 (200):**
```json
{
  "turn_number": 1,
  "player_question": "你好",
  "inner_monologue": "这是第一个问题，我要表现得自然一点，不要太正式...",
  "npc_response": "你好啊！"
}
```

#### 3.2.6 健康检查 `GET /health`

**响应 (200):**
```json
{
  "status": "healthy"
}
```

---

## 4. 存储抽象层设计

### 4.1 接口定义 (`storage/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Optional
from core.game.session import GameSession

class SessionStorage(ABC):
    """会话存储抽象接口"""

    @abstractmethod
    def save(self, session: GameSession) -> str:
        """保存会话，返回 session_id"""
        pass

    @abstractmethod
    def get(self, session_id: str) -> Optional[GameSession]:
        """获取会话，不存在返回 None"""
        pass

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        pass

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """删除会话"""
        pass
```

### 4.2 内存实现 (`storage/memory.py`)

```python
import uuid
from typing import Optional, Dict
from core.game.session import GameSession
from .base import SessionStorage

class MemorySessionStorage(SessionStorage):
    """内存存储实现（前期用）"""

    def __init__(self):
        self._sessions: Dict[str, GameSession] = {}

    def save(self, session: GameSession) -> str:
        session_id = str(uuid.uuid4())
        session.session_id = session_id
        self._sessions[session_id] = session
        return session_id

    def get(self, session_id: str) -> Optional[GameSession]:
        return self._sessions.get(session_id)

    def exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    def delete(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]
```

### 4.3 Redis 实现（预留，`storage/redis.py`）

```python
import json
import uuid
from typing import Optional
import redis
from core.game.session import GameSession
from .base import SessionStorage

class RedisSessionStorage(SessionStorage):
    """Redis 存储实现（后期加）"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl: int = 3600):
        self._redis = redis.from_url(redis_url)
        self._ttl = ttl  # 会话过期时间，单位秒

    def save(self, session: GameSession) -> str:
        # GameSession 需要实现 to_dict() 和 from_dict()
        session_id = session.session_id or str(uuid.uuid4())
        session.session_id = session_id
        data = session.to_dict()
        self._redis.setex(f"session:{session_id}", self._ttl, json.dumps(data))
        return session_id

    def get(self, session_id: str) -> Optional[GameSession]:
        data = self._redis.get(f"session:{session_id}")
        if not data:
            return None
        return GameSession.from_dict(json.loads(data))

    def exists(self, session_id: str) -> bool:
        return self._redis.exists(f"session:{session_id}") > 0

    def delete(self, session_id: str) -> None:
        self._redis.delete(f"session:{session_id}")
```

---

## 5. 核心模型修改

### 5.1 GameSession 重构 (`core/game/session.py`)

**新增字段:**
```python
@dataclass
class GameSession:
    session_id: Optional[str] = None  # 新增
    # ... 其他现有字段
```

**新增序列化方法:**
```python
@dataclass
class GameSession:
    # ... 现有字段

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "npc_profile": self.npc_profile.to_dict(),
            "questions_left": self.questions_left,
            "conversation_history": [turn.to_dict() for turn in self.conversation_history],
            "is_over": self.is_over,
            "verdict": self.verdict
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameSession":
        """从字典反序列化"""
        return cls(
            session_id=data.get("session_id"),
            npc_profile=NpcProfile.from_dict(data["npc_profile"]),
            questions_left=data["questions_left"],
            conversation_history=[ConversationTurn.from_dict(t) for t in data["conversation_history"]],
            is_over=data["is_over"],
            verdict=data["verdict"]
        )
```

### 5.2 NpcProfile 添加序列化方法

```python
@dataclass
class NpcProfile:
    # ... 现有字段

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age": self.age,
            "occupation": self.occupation,
            "city": self.city,
            "personality": self.personality,
            "backstory": self.backstory,
            "hobbies": self.hobbies,
            "speech_style": self.speech_style,
            "quirks": self.quirks
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NpcProfile":
        return cls(**data)
```

### 5.3 ConversationTurn 添加序列化方法

```python
@dataclass
class ConversationTurn:
    # ... 现有字段

    def to_dict(self) -> dict:
        return {
            "turn_number": self.turn_number,
            "player_question": self.player_question,
            "inner_monologue": self.inner_monologue,
            "npc_response": self.npc_response
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationTurn":
        return cls(**data)
```

---

## 6. API 层实现

### 6.1 Pydantic Schemas (`api/schemas.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional

# NPC 相关
class NpcProfileBase(BaseModel):
    name: str
    age: int
    occupation: str
    city: str

class NpcProfileCreate(NpcProfileBase):
    pass

class NpcProfileResponse(NpcProfileBase):
    introduction: str

# 会话回合
class ConversationTurnBase(BaseModel):
    turn_number: int
    player_question: str
    npc_response: str

class ConversationTurnResponse(ConversationTurnBase):
    pass

class ConversationTurnDetailResponse(ConversationTurnBase):
    inner_monologue: str

# 会话相关
class SessionCreate(BaseModel):
    pass

class SessionResponse(BaseModel):
    session_id: str
    npc: NpcProfileResponse
    questions_left: int
    is_over: bool
    verdict: Optional[str] = None
    turns: List[ConversationTurnResponse] = Field(default_factory=list)

# 提问
class AskQuestionRequest(BaseModel):
    question: str

class AskQuestionResponse(BaseModel):
    turn_number: int
    player_question: str
    npc_response: str
    questions_left: int
    is_over: bool

# 宣判
class JudgeRequest(BaseModel):
    verdict: str

class JudgeResponse(BaseModel):
    verdict: str
    correct: bool
    is_over: bool

# 健康检查
class HealthResponse(BaseModel):
    status: str
```

### 6.2 依赖注入 (`api/dependencies.py`)

```python
from typing import Annotated
from fastapi import Depends
import config
from storage.base import SessionStorage
from storage.memory import MemorySessionStorage

# 可以根据配置切换存储实现
def get_storage() -> SessionStorage:
    if config.STORAGE_TYPE == "redis":
        # 后期实现 Redis 存储
        raise NotImplementedError("Redis storage not implemented yet")
    return MemorySessionStorage()

StorageDep = Annotated[SessionStorage, Depends(get_storage)]
```

### 6.3 会话路由 (`api/routes/sessions.py`)

```python
from fastapi import APIRouter, HTTPException, status
from api.schemas import (
    SessionCreate, SessionResponse,
    AskQuestionRequest, AskQuestionResponse,
    JudgeRequest, JudgeResponse,
    ConversationTurnDetailResponse
)
from api.dependencies import StorageDep
from core.npc.profile import generate_npc_profile
from core.game.session import GameSession

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
async def create_session(storage: StorageDep):
    """创建新游戏会话"""
    profile = await generate_npc_profile()
    session = GameSession(npc_profile=profile)
    session_id = storage.save(session)

    return SessionResponse(
        session_id=session_id,
        npc={
            "name": profile.name,
            "age": profile.age,
            "occupation": profile.occupation,
            "city": profile.city,
            "introduction": profile.introduction()
        },
        questions_left=session.questions_left,
        is_over=session.is_over
    )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, storage: StorageDep):
    """获取会话状态"""
    session = storage.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session_id,
        npc={
            "name": session.npc_profile.name,
            "age": session.npc_profile.age,
            "occupation": session.npc_profile.occupation,
            "city": session.npc_profile.city,
            "introduction": session.npc_profile.introduction()
        },
        questions_left=session.questions_left,
        is_over=session.is_over,
        verdict=session.verdict,
        turns=[
            {
                "turn_number": t.turn_number,
                "player_question": t.player_question,
                "npc_response": t.npc_response
            }
            for t in session.conversation_history
        ]
    )

@router.post("/{session_id}/turns", response_model=AskQuestionResponse)
async def ask_question(session_id: str, request: AskQuestionRequest, storage: StorageDep):
    """玩家提问一轮"""
    session = storage.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.is_over:
        raise HTTPException(status_code=409, detail="Game is already over")

    turn = await session.ask(request.question)
    storage.save(session)  # 更新存储

    return AskQuestionResponse(
        turn_number=turn.turn_number,
        player_question=turn.player_question,
        npc_response=turn.npc_response,
        questions_left=session.questions_left,
        is_over=session.is_over
    )

@router.post("/{session_id}/judge", response_model=JudgeResponse)
async def judge(session_id: str, request: JudgeRequest, storage: StorageDep):
    """玩家宣判"""
    session = storage.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.is_over and session.verdict:
        raise HTTPException(status_code=409, detail="Game is already over")

    try:
        session.judge(request.verdict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    storage.save(session)
    return JudgeResponse(
        verdict=session.verdict,
        correct=session.verdict == "ai",
        is_over=session.is_over
    )

@router.get("/{session_id}/turns/{turn_number}", response_model=ConversationTurnDetailResponse)
async def get_turn(session_id: str, turn_number: int, storage: StorageDep):
    """获取单轮详情（含内心独白）"""
    session = storage.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if turn_number < 1 or turn_number > len(session.conversation_history):
        raise HTTPException(status_code=404, detail="Turn not found")

    turn = session.conversation_history[turn_number - 1]
    return ConversationTurnDetailResponse(
        turn_number=turn.turn_number,
        player_question=turn.player_question,
        inner_monologue=turn.inner_monologue,
        npc_response=turn.npc_response
    )
```

### 6.4 FastAPI 应用入口 (`api/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import sessions, health
import config

app = FastAPI(title="NPC Robot API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions.router)
app.include_router(health.router)

@app.get("/")
async def root():
    return {"message": "NPC Robot API", "version": "1.0.0"}
```

---

## 7. CLI 客户端重构

### 7.1 API 客户端封装 (`cli/api_client.py`)

```python
import httpx
from typing import Optional, List, Dict, Any

class NpcApiClient:
    """NPC API 客户端封装"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    async def create_session(self) -> Dict[str, Any]:
        """创建新会话"""
        response = await self._client.post(f"{self.base_url}/api/sessions")
        response.raise_for_status()
        return response.json()

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取会话"""
        response = await self._client.get(f"{self.base_url}/api/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    async def ask_question(self, session_id: str, question: str) -> Dict[str, Any]:
        """提问"""
        response = await self._client.post(
            f"{self.base_url}/api/sessions/{session_id}/turns",
            json={"question": question}
        )
        response.raise_for_status()
        return response.json()

    async def judge(self, session_id: str, verdict: str) -> Dict[str, Any]:
        """宣判"""
        response = await self._client.post(
            f"{self.base_url}/api/sessions/{session_id}/judge",
            json={"verdict": verdict}
        )
        response.raise_for_status()
        return response.json()

    async def get_turn(self, session_id: str, turn_number: int) -> Dict[str, Any]:
        """获取单轮详情"""
        response = await self._client.get(
            f"{self.base_url}/api/sessions/{session_id}/turns/{turn_number}"
        )
        response.raise_for_status()
        return response.json()
```

### 7.2 CLI 主程序 (`cli/main.py`)

基本流程保持不变，但把所有直接调用 `core/` 的地方改成调用 `NpcApiClient`。

---

## 8. 配置变更

### 8.1 config.py 添加内容

```python
# API 配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# 存储配置
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "memory")  # "memory" 或 "redis"
# Redis 相关（预留）
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

### 8.2 .env.example 添加内容

```env
# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 存储配置
STORAGE_TYPE=memory
# REDIS_URL=redis://localhost:6379/0
```

---

## 9. 依赖变更

### 新增依赖（requirements.txt 或 pyproject.toml）

```toml
# 后端
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0

# CLI 客户端
httpx>=0.24.0
```

---

## 10. 启动方式

### 10.1 启动后端

```bash
uvicorn api.main:app --reload
```

### 10.2 启动 CLI 客户端

```bash
python cli/main.py --api-url http://localhost:8000
```

### 10.3 启动脚本更新

更新 `run.bat` 和 `run.sh`，让它们可以：
- 同时启动后端和 CLI（开发模式）
- 或者只启动后端（生产模式）

---

## 11. 测试策略

### 11.1 单元测试
- `tests/core/` - 测试核心业务逻辑
- `tests/storage/` - 测试存储实现
- `tests/api/` - 使用 TestClient 测试 API

### 11.2 集成测试
- 测试完整的游戏流程从 CLI 到 API 再到存储

---

## 12. 迁移计划

### 阶段 1: 重组目录结构
- 创建新目录结构
- 移动现有文件到 `core/`
- 调整 import 路径

### 阶段 2: 添加序列化方法
- 修改 GameSession、NpcProfile、ConversationTurn
- 添加 to_dict/from_dict

### 阶段 3: 实现存储层
- 定义接口
- 实现内存存储

### 阶段 4: 实现 API 层
- 添加 schemas
- 实现路由
- 实现 FastAPI 应用

### 阶段 5: 重构 CLI
- 创建 api_client.py
- 修改 cli/main.py 使用 API

### 阶段 6: 测试和文档
- 编写测试
- 更新 README
- 更新启动脚本

---

## 13. 未来扩展点

1. **Redis 存储** - 替换内存存储，支持多实例和持久化
2. **数据库存储** - 把会话历史存入数据库（PostgreSQL/SQLite）
3. **用户认证** - 添加用户登录/注册，关联会话到用户
4. **Web 前端** - 使用 React/Vue 构建 Web 界面
5. **多房间/多人模式** - 支持多个玩家同时进行游戏
6. **排行榜** - 记录玩家成绩
