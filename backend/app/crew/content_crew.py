"""
ContentCrew: orchestrates the content creation pipeline in phases:
  1. Research -> Write -> Edit          (LLM crew, Research uses web_search)
  2. SEO analysis                        (deterministic Python, no LLM)
  3. SEO writing pass                    (LLM, given the analysis as context)
  4. Image generation                    (deterministic Python, no LLM)
  5. Social repurposing (optional)       (LLM, no tools)

# CrewAI + LLM (Anthropic / Claude)
# Note: crewai-tools is intentionally NOT included — this project uses its own
# lightweight custom tools (app/tools/*) built on crewai.tools.BaseTool.
# crewai.LLM(model="anthropic/<model>") uses CrewAI's native Anthropic
# provider, which requires the `anthropic` SDK directly (not just litellm).
crewai==1.15.21
litellm>=1.44.22
anthropic>=0.40.0
"""
import re
import time
from typing import Any

from crewai import Crew, Process, Task

from app.agents.editing_agent import build_editing_agent
from app.agents.research_agent import build_research_agent
from app.agents.seo_agent import build_seo_agent
from app.agents.social_agent import build_social_agent
from app.agents.writing_agent import build_writing_agent
from app.core.logging import get_logger
from app.crew.tasks import build_content_tasks, build_seo_task, build_social_task
from app.models.schemas import ContentGenerationRequest, ContentResult
from app.tools.image_tool import ImagePromptTool
from app.tools.seo_tool import SEOAnalysisTool

logger = get_logger(__name__)


def _extract_section(text: str, marker: str, stop_markers: list[str]) -> str:
    """Pull a labeled section (e.g. 'META_DESCRIPTION:') out of raw text."""
    pattern = rf"{marker}\s*:?\s*(.*?)(?=(?:{'|'.join(stop_markers)})|\Z)"
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _task_output(task: Task) -> str:
    output = getattr(task, "output", None)
    if output and hasattr(output, "raw"):
        return output.raw
    return str(output) if output else ""


def _extract_sources(research_raw: str) -> list[str]:
    match = re.search(r"SOURCES:\s*(.*)", research_raw, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    return [line.strip("- ").strip() for line in match.group(1).splitlines() if line.strip()]


class ContentCrew:
    """Builds and runs the full content-creation pipeline for a single request."""

    def __init__(self, request: ContentGenerationRequest):
        self.request = request

    def run(self) -> dict[str, Any]:
        req = self.request
        start = time.time()

        # --- Phase 1: Research -> Write -> Edit (LLM crew) -----------------
        research_agent = build_research_agent()
        writing_agent = build_writing_agent()
        editing_agent = build_editing_agent()

        content_tasks = build_content_tasks(
            research_agent=research_agent,
            writing_agent=writing_agent,
            editing_agent=editing_agent,
            topic=req.topic,
            content_format=req.content_format.value,
            tone=req.tone,
            target_audience=req.target_audience,
            word_count=req.word_count,
        )
        research_task, writing_task, editing_task = content_tasks

        logger.info("crew_phase_started", phase="research_write_edit", topic=req.topic)
        Crew(
            agents=[research_agent, writing_agent, editing_agent],
            tasks=content_tasks,
            process=Process.sequential,
            verbose=True,
        ).kickoff()

        edited_article = _task_output(editing_task) or _task_output(writing_task)
        sources = _extract_sources(_task_output(research_task))

        # --- Phase 2: Deterministic SEO analysis (no LLM) -------------------
        keywords_str = ", ".join(req.target_keywords)
        seo_analysis = SEOAnalysisTool()._run(text=edited_article, target_keywords=keywords_str)
        score_match = re.search(r"SEO Score:\s*(\d+)", seo_analysis)
        seo_score = int(score_match.group(1)) if score_match else None

        # --- Phase 3: SEO writing pass (LLM, no tools) ----------------------
        seo_agent = build_seo_agent()
        seo_task = build_seo_task(
            seo_agent=seo_agent,
            edited_article=edited_article,
            seo_analysis=seo_analysis,
            target_keywords=keywords_str,
        )
        logger.info("crew_phase_started", phase="seo_writing", topic=req.topic)
        Crew(agents=[seo_agent], tasks=[seo_task], process=Process.sequential, verbose=True).kickoff()
        seo_raw = _task_output(seo_task)

        final_article = _extract_section(seo_raw, "FINAL_ARTICLE", ["META_DESCRIPTION", "SUGGESTED_KEYWORDS"])
        if not final_article:
            final_article = edited_article  # never lose the article if the LLM output is malformed
        meta_description = _extract_section(seo_raw, "META_DESCRIPTION", ["SUGGESTED_KEYWORDS", "FINAL_ARTICLE"])
        keywords_raw = _extract_section(seo_raw, "SUGGESTED_KEYWORDS", ["FINAL_ARTICLE", "META_DESCRIPTION"])
        seo_keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

        title_match = re.search(r"^#\s+(.+)$", final_article, flags=re.MULTILINE)
        title = title_match.group(1).strip() if title_match else req.topic

        # --- Phase 4: Deterministic image generation (no LLM) ---------------
        image_prompt = alt_text = image_url = None
        if req.generate_image:
            logger.info("crew_phase_started", phase="image_generation", topic=req.topic)
            image_output = ImagePromptTool()._run(topic=req.topic, tone=req.tone)
            image_prompt = _extract_section(image_output, "IMAGE_PROMPT", ["ALT_TEXT", "IMAGE_URL", "NOTE"]) or None
            alt_text = _extract_section(image_output, "ALT_TEXT", ["IMAGE_URL", "NOTE"]) or None
            image_url = _extract_section(image_output, "IMAGE_URL", ["NOTE"]) or None

        # --- Phase 5: Social repurposing (LLM, no tools, optional) ----------
        social_variants: dict[str, str] = {}
        hashtags: list[str] = []
        if req.generate_social_variants:
            social_agent = build_social_agent()
            social_task = build_social_task(social_agent=social_agent, final_article=final_article)
            logger.info("crew_phase_started", phase="social", topic=req.topic)
            Crew(agents=[social_agent], tasks=[social_task], process=Process.sequential, verbose=True).kickoff()
            social_raw = _task_output(social_task)
            for label in ["TWITTER_THREAD", "LINKEDIN_POST", "INSTAGRAM_CAPTION"]:
                others = [l for l in ["TWITTER_THREAD", "LINKEDIN_POST", "INSTAGRAM_CAPTION", "HASHTAGS"] if l != label]
                section = _extract_section(social_raw, label, others)
                if section:
                    social_variants[label.lower()] = section
            hashtags_raw = _extract_section(social_raw, "HASHTAGS", [])
            hashtags = [h.strip() for h in re.split(r"[,\s]+", hashtags_raw) if h.strip().startswith("#")]

        logger.info("crew_run_completed", topic=req.topic, duration_seconds=round(time.time() - start, 2))

        result = ContentResult(
            title=title,
            body_markdown=final_article,
            meta_description=meta_description or None,
            seo_keywords=seo_keywords,
            seo_score=seo_score,
            image_prompt=image_prompt,
            alt_text=alt_text,
            image_url=image_url,
            social_variants=social_variants,
            hashtags=hashtags,
            sources=sources[:10],
        )
        return result.model_dump()