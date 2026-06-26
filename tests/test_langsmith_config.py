import importlib
import os

import config


def test_langsmith_env_mapping(monkeypatch):
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)

    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    monkeypatch.setenv("LANGSMITH_API_KEY", "test_key")
    monkeypatch.setenv("LANGSMITH_PROJECT", "test_project")

    importlib.reload(config)

    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_ENDPOINT") == "https://api.smith.langchain.com"
    assert os.environ.get("LANGCHAIN_API_KEY") == "test_key"
    assert os.environ.get("LANGCHAIN_PROJECT") == "test_project"
