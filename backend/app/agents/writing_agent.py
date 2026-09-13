"""Content Writing Agent: long-form drafting, tone adaptation, structure."""
from crewai import Agent

from app.services.llm_service import get_writing_llm


def build_writing_agent() -> Agent:
    return Agent(
        role="Senior Content Writer",
        goal=(
            "Write a well-structured, engaging, factually grounded article based on the "
            "research provided, matching the requested tone, audience, and target word count."
        ),
        backstory=(
            "You are an award-winning content writer who has ghostwritten for major tech "
            "and business blogs. You write in clear, active prose, use varied sentence "
            "structure, and always organize content with clear headings."
        ),
        llm=get_writing_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=6,
    )