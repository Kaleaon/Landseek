"""Recursive Language Models for unbounded context processing."""

from .core import RLM, RLMError, MaxIterationsError, MaxDepthError
from .repl import REPLError
from .prompts import build_system_prompt, build_rag_system_prompt

__version__ = "0.1.0"

__all__ = [
    "RLM",
    "RLMError",
    "MaxIterationsError",
    "MaxDepthError",
    "REPLError",
    "build_system_prompt",
    "build_rag_system_prompt",
]
