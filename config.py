# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# LLM 配置（DeepSeek，兼容 OpenAI 接口）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")
TEMPERATURE_THINK = float(os.getenv("TEMPERATURE_THINK", "0.7"))
TEMPERATURE_RESPOND = float(os.getenv("TEMPERATURE_RESPOND", "0.8"))

# 游戏配置
MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", "10"))
THINK_MAX_TOKENS = int(os.getenv("THINK_MAX_TOKENS", "200"))
RESPOND_MAX_TOKENS = int(os.getenv("RESPOND_MAX_TOKENS", "150"))

# 读取 LangSmith 相关配置并自动映射为 LangChain 标准变量以实现自动追踪
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false")
if LANGSMITH_TRACING.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if env_endpoint := os.getenv("LANGSMITH_ENDPOINT"):
        os.environ["LANGCHAIN_ENDPOINT"] = env_endpoint
    if env_api_key := os.getenv("LANGSMITH_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = env_api_key
    if env_project := os.getenv("LANGSMITH_PROJECT"):
        os.environ["LANGCHAIN_PROJECT"] = env_project
