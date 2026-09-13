"""Social Media Agent: platform-specific repurposing, hashtags, scheduling suggestions."""
from crewai import Agent

from app.services.llm_service import get_tool_llm


def build_social_agent() -> Agent:
    return Agent(
        role="Social Media Strategist",
        goal=(
            "Repurpose the final article into platform-specific variants (Twitter/X thread, "
            "LinkedIn post, Instagram caption) with relevant hashtags and a suggested posting "
            "time, each adapted to that platform's tone and length constraints."
        ),
        backstory=(
            "You are a social media strategist who has grown multiple brand accounts to "
            "six figures in followers, expert at platform-native tone and hook writing."
        ),
        # Uses the faster llama3.2:latest model — Social doesn't call tools,
        # but stays on this tier (rather than the reasoning model) since
        # platform-native repurposing doesn't need deep reasoning and
        # benefits more from speed.
        llm=get_tool_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=4,
    )