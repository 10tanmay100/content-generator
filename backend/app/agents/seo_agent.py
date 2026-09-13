"""
SEO Optimization Agent: writes a meta description, suggests keywords, and
lightly revises the article for natural keyword usage — using a pre-computed
SEO analysis as input context (see app/tools/seo_tool.py, called directly in
content_crew.py, not through this agent).

This agent has NO tools attached. Small local Ollama models are not reliable
enough at structured function-calling to trust for this: they can emit a
tool-call attempt as plain hallucinated text (including invented parameters)
instead of an actual executed call, corrupting the output. Since the SEO
analysis itself is a deterministic calculation, it's computed once in plain
Python and handed to this agent as text, so the agent only ever has to do
what LLMs are actually good at: write.
"""
from crewai import Agent

from app.services.llm_service import get_writing_llm


def build_seo_agent() -> Agent:
    return Agent(
        role="SEO Specialist",
        goal=(
            "Given a pre-computed SEO analysis and the article, write a compelling meta "
            "description, suggest relevant keywords, and lightly revise the article only "
            "if the analysis suggests genuine keyword-usage improvements."
        ),
        backstory=(
            "You are a technical SEO specialist who balances search-engine optimization "
            "with genuine readability, never sacrificing content quality for keyword stuffing."
        ),
        llm=get_writing_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )