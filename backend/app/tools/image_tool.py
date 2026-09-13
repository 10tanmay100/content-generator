"""
Custom CrewAI tool: generates an actual hero image (not just a prompt) via
Pollinations.ai — free, no API key required — saves it to local disk, and
returns a URL served by this backend's own /generated-images static mount.

Uses a deterministic seed (hash of topic+tone) so repeat requests for the
same article return the same cached image instead of a new random one each
time a job is re-viewed.
"""
import hashlib
import urllib.parse
from pathlib import Path

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

STORAGE_DIR = Path(settings.image_storage_dir)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

STYLE_MAP = {
    "professional": "clean minimalist editorial illustration, soft gradients, corporate blue palette",
    "casual": "friendly flat-design illustration, warm colors, approachable",
    "witty": "playful modern vector illustration, bold colors, subtle humor",
    "authoritative": "high-contrast editorial photo-style, dramatic lighting, premium feel",
}


class ImagePromptInput(BaseModel):
    topic: str = Field(..., description="Article topic / title")
    tone: str = Field(
        default="professional",
        description="Visual tone/style. Always pass this explicitly, e.g. 'professional'.",
        json_schema_extra=lambda schema: schema.pop("default", None),
    )


class ImagePromptTool(BaseTool):
    name: str = "image_prompt_builder"
    description: str = (
        "Generates an actual hero image (not just a text prompt) for a given article "
        "topic and tone using a free text-to-image model, saves it, and returns its "
        "URL plus matching alt text."
    )
    args_schema: type[BaseModel] = ImagePromptInput

    def _build_prompt(self, topic: str, tone: str) -> str:
        style = STYLE_MAP.get(tone.lower(), STYLE_MAP["professional"])
        return (
            f"A {style} representing the concept of '{topic}', no text or logos, "
            f"16:9 blog header composition, high detail, web-optimized."
        )

    def _run(self, topic: str, tone: str = "professional") -> str:
        prompt = self._build_prompt(topic, tone)
        alt_text = f"Illustration representing {topic}"

        cache_key = hashlib.sha256(f"{topic}:{tone}".encode()).hexdigest()
        seed = int(cache_key, 16) % (2**31)
        filename = f"{cache_key[:16]}.jpg"
        filepath = STORAGE_DIR / filename

        encoded_prompt = urllib.parse.quote(prompt)
        api_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={settings.image_width}&height={settings.image_height}"
            f"&seed={seed}&nologo=true"
        )

        try:
            if not filepath.exists():
                response = requests.get(api_url, timeout=60)
                response.raise_for_status()
                filepath.write_bytes(response.content)
                logger.info("image_generated", topic=topic, filename=filename)
            else:
                logger.info("image_cache_hit", topic=topic, filename=filename)

            image_url = f"{settings.public_base_url.rstrip('/')}/generated-images/{filename}"
            return f"IMAGE_PROMPT: {prompt}\nALT_TEXT: {alt_text}\nIMAGE_URL: {image_url}"

        except Exception as exc:
            logger.error("image_generation_failed", topic=topic, error=str(exc))
            return (
                f"IMAGE_PROMPT: {prompt}\nALT_TEXT: {alt_text}\nIMAGE_URL: \n"
                f"NOTE: Image generation failed ({exc}); use the prompt above "
                f"manually with any text-to-image tool."
            )