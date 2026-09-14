"""
SEO Optimization Agent: writes a meta description, suggests keywords, and
lightly revises the article for natural keyword usage — using a pre-computed
SEO analysis as input context (see app/tools/seo_tool.py, called directly in
content_crew.py, not through this agent).

This agent has NO tools attached — the SEO analysis is a deterministic
calculation, computed once in plain Python and handed to this agent as
text, so the agent only ever has to do what LLMs are actually good at:
write.
"""
from crewai import Agent

from app.services.llm_service import get_llm


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
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )