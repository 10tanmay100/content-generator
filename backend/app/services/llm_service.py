"""
LLM provider wiring: Claude Sonnet via CrewAI's built-in LLM class (litellm
under the hood, provider-prefixed as "anthropic/<model>").

A single model is used for every agent — unlike the earlier local-Ollama
setup, which needed a tool-calling-capable model split from a separate
writing/reasoning model because small local models weren't reliably good at
both. Claude Sonnet handles tool-calling and long-form writing well enough
that one model for everything is simpler and doesn't trade off quality.

Note: earlier versions of this file patched around a CrewAI bug where a
`cache_breakpoint` marker (meant for Anthropic prompt caching) leaked into
requests for non-Anthropic providers. That patch is intentionally removed
now — Anthropic is the one provider CrewAI handles that marker correctly
for, so leaving it in place lets real Anthropic prompt caching work as
intended instead of disabling it.
"""
from functools import lru_cache

from crewai import LLM

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Workaround for a real CrewAI/Anthropic incompatibility: when an agent
# exceeds its max_iter limit, CrewAI's handle_max_iterations_exceeded()
# forces a final answer by appending an assistant-role message to the
# conversation and sending that as the LAST message in the request — a
# technique called "prefill". Claude 4.6+ (including Sonnet 5) explicitly
# rejects this with a 400 "This model does not support assistant message
# prefill" error, since Anthropic requires every conversation to end on a
# user turn for these models. The fix mirrors Anthropic's own documented
# workaround: append a short trailing user message after the assistant one,
# so the conversation always ends correctly regardless of which model is
# configured.
#
# handle_max_iterations_exceeded is imported by name (not looked up lazily)
# into three separate modules, so each of those bound copies needs patching
# individually — patching only the original in agent_utils would silently
# do nothing, since the other modules already hold their own reference.
# ---------------------------------------------------------------------------
def _install_max_iterations_patch() -> None:
    import crewai.utilities.agent_utils as agent_utils

    I18N_DEFAULT = agent_utils.I18N_DEFAULT
    format_message_for_llm = agent_utils.format_message_for_llm
    format_answer = agent_utils.format_answer
    AgentFinish = agent_utils.AgentFinish

    def patched_handle_max_iterations_exceeded(
        formatted_answer, printer, messages, llm, callbacks, verbose: bool = True
    ):
        if verbose:
            printer.print(
                content="Maximum iterations reached. Requesting final answer.",
                color="yellow",
            )

        if formatted_answer and hasattr(formatted_answer, "text"):
            assistant_message = (
                formatted_answer.text + f"\n{I18N_DEFAULT.errors('force_final_answer')}"
            )
        else:
            assistant_message = I18N_DEFAULT.errors("force_final_answer")

        messages.append(format_message_for_llm(assistant_message, role="assistant"))
        # The fix: keep the conversation ending on a user turn.
        messages.append(
            format_message_for_llm("Please continue with your final answer now.", role="user")
        )

        answer = llm.call(messages, callbacks=callbacks)

        if answer is None or answer == "":
            if verbose:
                printer.print(
                    content="Received None or empty response from LLM call.",
                    color="red",
                )
            raise ValueError("Invalid response from LLM call - None or empty.")

        formatted = format_answer(answer=answer)

        if isinstance(formatted, AgentFinish):
            return formatted
        return AgentFinish(
            thought=formatted.thought,
            output=formatted.text,
            text=formatted.text,
        )

    agent_utils.handle_max_iterations_exceeded = patched_handle_max_iterations_exceeded

    import crewai.agents.crew_agent_executor as crew_agent_executor
    import crewai.experimental.agent_executor as experimental_agent_executor
    import crewai.lite_agent as lite_agent

    crew_agent_executor.handle_max_iterations_exceeded = patched_handle_max_iterations_exceeded
    experimental_agent_executor.handle_max_iterations_exceeded = patched_handle_max_iterations_exceeded
    lite_agent.handle_max_iterations_exceeded = patched_handle_max_iterations_exceeded


_install_max_iterations_patch()
logger.info("crewai_max_iterations_prefill_patch_applied")


@lru_cache
def get_llm() -> LLM:
    """The model used by every agent (research, writing, editing, SEO, social)."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    return LLM(
        model=f"anthropic/{settings.anthropic_model}",
        api_key=settings.anthropic_api_key
    )