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
RESPOND_MAX_TOKENS = int(os.getenv("RESPOND_MAX_TOKENS", "80"))
