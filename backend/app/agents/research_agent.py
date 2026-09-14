"""Content Research Agent: web search, competitor scan, keyword & source gathering."""
from crewai import Agent

from app.services.llm_service import get_llm
from app.tools.web_search_tool import WebSearchTool


def build_research_agent() -> Agent:
    return Agent(
        role="Senior Content Research Analyst",
        goal=(
            "Research the given topic thoroughly: gather current facts, statistics, "
            "trending angles, competitor coverage, and credible sources that the Writer "
            "can use to produce an authoritative, well-grounded article."
        ),
        backstory=(
            "You are a meticulous research analyst with 10 years of experience in digital "
            "content strategy. You know how to separate credible sources from noise, spot "
            "trending angles, and summarize findings concisely for writers."
        ),
        tools=[WebSearchTool()],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=8,
    )