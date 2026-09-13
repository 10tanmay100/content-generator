"""
Task definitions wiring agents to concrete CrewAI tasks.

Split into three phases so content_crew.py can inject deterministic,
Python-computed results (SEO analysis, generated image) as plain-text
context between LLM phases, instead of asking a local model to call tools
mid-task (see app/agents/seo_agent.py for why).
"""
from crewai import Agent, Task


def build_content_tasks(
    *,
    research_agent: Agent,
    writing_agent: Agent,
    editing_agent: Agent,
    topic: str,
    content_format: str,
    tone: str,
    target_audience: str,
    word_count: int,
) -> list[Task]:
    """Phase 1: Research -> Write -> Edit."""
    research_task = Task(
        description=(
            f"Research the topic: '{topic}'.\n"
            f"Target audience: {target_audience}.\n"
            "Find current facts, statistics, notable trends, and at least 3-5 credible source "
            "URLs. Summarize findings in bullet points, grouped by subtopic, and list all "
            "source URLs at the end under 'SOURCES:'."
        ),
        expected_output="A structured research brief with bullet-point findings and a SOURCES list.",
        agent=research_agent,
    )

    writing_task = Task(
        description=(
            f"Using the research brief, write a {content_format} article on '{topic}'.\n"
            f"Tone: {tone}. Target audience: {target_audience}. Target length: ~{word_count} words.\n"
            "Structure: a compelling title (H1), an engaging intro, 3-6 H2 sections, and a "
            "conclusion with a clear takeaway. Output valid Markdown."
        ),
        expected_output="A complete Markdown draft with title, headings, and body copy.",
        agent=writing_agent,
        context=[research_task],
    )

    editing_task = Task(
        description=(
            "Edit the draft for grammar, clarity, tone consistency, and factual alignment "
            "with the research brief. Fix awkward phrasing and tighten prose. Preserve the "
            "Markdown structure. Return ONLY the final, polished Markdown article — no "
            "preamble, no commentary, no explanations of what you changed."
        ),
        expected_output="A publish-ready, polished Markdown article, and nothing else.",
        agent=editing_agent,
        context=[research_task, writing_task],
    )

    return [research_task, writing_task, editing_task]


def build_seo_task(*, seo_agent: Agent, edited_article: str, seo_analysis: str, target_keywords: str) -> Task:
    """Phase 2: SEO writing pass, given a pre-computed analysis (no tool calls)."""
    keywords_str = target_keywords or "(none specified — infer relevant ones from the article)"
    return Task(
        description=(
            "You are given the final edited article and an automated SEO analysis of it "
            "below. Do not attempt to call any tools — just use the analysis as-is.\n\n"
            f"TARGET KEYWORDS: {keywords_str}\n\n"
            f"SEO ANALYSIS:\n{seo_analysis}\n\n"
            f"ARTICLE:\n{edited_article}\n\n"
            "Produce exactly these three sections, in this order, with these exact headers:\n"
            "1) META_DESCRIPTION: a compelling meta description under 160 characters.\n"
            "2) SUGGESTED_KEYWORDS: 5-8 relevant keywords (comma-separated).\n"
            "3) FINAL_ARTICLE: the article above, lightly revised only if the analysis "
            "suggests a genuine keyword-usage improvement — otherwise return it unchanged."
        ),
        expected_output="META_DESCRIPTION, SUGGESTED_KEYWORDS, and FINAL_ARTICLE sections.",
        agent=seo_agent,
    )


def build_social_task(*, social_agent: Agent, final_article: str) -> Task:
    """Phase 3 (optional): repurpose the final article for social platforms."""
    return Task(
        description=(
            "Using the final article below, create platform-specific repurposed content:\n"
            "1) TWITTER_THREAD: a 4-6 tweet thread (each tweet <=280 chars).\n"
            "2) LINKEDIN_POST: a professional LinkedIn post (150-300 words).\n"
            "3) INSTAGRAM_CAPTION: a short, engaging caption with line breaks.\n"
            "4) HASHTAGS: 8-12 relevant hashtags (comma-separated, no spaces).\n"
            "Label each section clearly with the headers above.\n\n"
            f"ARTICLE:\n{final_article}"
        ),
        expected_output="TWITTER_THREAD, LINKEDIN_POST, INSTAGRAM_CAPTION, and HASHTAGS sections.",
        agent=social_agent,
    )