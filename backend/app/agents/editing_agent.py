"""Content Editing Agent: grammar, clarity, consistency, fact-check pass."""
from crewai import Agent

from app.services.llm_service import get_writing_llm


def build_editing_agent() -> Agent:
    return Agent(
        role="Senior Copy Editor",
        goal=(
            "Review the draft for grammar, clarity, factual consistency with the research, "
            "tone consistency, and overall readability. Return a polished, publish-ready version."
        ),
        backstory=(
            "You are a detail-obsessed copy editor who has worked at major publications. "
            "You catch inconsistencies, awkward phrasing, and unsupported claims, and you "
            "tighten prose without losing the author's voice."
        ),
        llm=get_writing_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )