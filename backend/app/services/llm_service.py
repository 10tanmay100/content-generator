"""
LLM provider wiring: local Ollama models via CrewAI's built-in LLM class
(litellm under the hood, provider-prefixed as "ollama_chat/<model>" — the
"_chat" variant hits Ollama's /api/chat endpoint and preserves system/user/
assistant roles properly, unlike the legacy "ollama/" provider which
flattens everything into a single prompt string).

Two models are used:
  - get_tool_llm(): llama3.2:latest — assigned to every agent that calls a
    tool (Research, SEO, Image), since Ollama's tool-calling support is more
    consistent on Llama-family models.
  - get_writing_llm(): deepseek-r1:8b — a reasoning-tuned model, assigned to
    agents that do pure text generation with no tools (Writing, Editing,
    Social), where its stronger reasoning/structuring tends to help.

Requires Ollama running locally (or reachable at OLLAMA_BASE_URL) with both
models pulled:
    ollama pull llama3.2:latest
    ollama pull deepseek-r1:14b
"""
from functools import lru_cache

from crewai import LLM

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Workaround for crewAI bug: crew_agent_executor.py unconditionally calls
# mark_cache_breakpoint() on messages to support Anthropic prompt caching,
# but non-Anthropic providers routed through litellm never get that marker
# stripped back out, so some providers reject the raw `cache_breakpoint`
# key (see crewAIInc/crewAI#5886). Ollama has not been confirmed to reject
# it, but this patch is a harmless no-op if the provider already ignores
# unknown keys, so it's kept here as a safety net when swapping providers.
# ---------------------------------------------------------------------------
import crewai.llms.cache as _crewai_cache


def _noop_mark_cache_breakpoint(message: dict) -> dict:
    return message


if _crewai_cache.mark_cache_breakpoint is not _noop_mark_cache_breakpoint:
    _crewai_cache.mark_cache_breakpoint = _noop_mark_cache_breakpoint
    logger.info("crewai_cache_breakpoint_patch_applied")


@lru_cache
def get_tool_llm() -> LLM:
    """Tool-calling model (Research, SEO, Image agents) — llama3.2:latest."""
    return LLM(
        model=f"ollama_chat/{settings.ollama_model}",
        base_url=settings.ollama_base_url,
        temperature=settings.ollama_temperature,
    )


@lru_cache
def get_writing_llm() -> LLM:
    """Pure-text reasoning model (Writing, Editing, Social agents) — deepseek-r1:8b."""
    return LLM(
        model=f"ollama_chat/{settings.ollama_model_reasoning}",
        base_url=settings.ollama_base_url,
        temperature=settings.ollama_temperature,
    )       