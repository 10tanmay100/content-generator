"""Custom CrewAI tool: lightweight keyword-density / SEO heuristic scorer."""
import re
from collections import Counter

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "in", "on",
    "at", "to", "for", "of", "with", "as", "by", "it", "this", "that", "be", "your",
    "you", "we", "our", "from", "will", "can", "how", "what",
}


class SEOAnalysisInput(BaseModel):
    text: str = Field(..., description="The full body content to analyze")
    target_keywords: str = Field(
    default="",
    description="Comma-separated target keywords. Always pass this explicitly (use an empty string if none).",
    json_schema_extra=lambda schema: schema.pop("default", None),
)


class SEOAnalysisTool(BaseTool):
    name: str = "seo_analyzer"
    description: str = (
        "Analyzes content for SEO: keyword density, readability signals, heading/word "
        "counts, and gives a 0-100 heuristic SEO score plus suggestions."
    )
    args_schema: type[BaseModel] = SEOAnalysisInput

    def _run(self, text: str, target_keywords: str = "") -> str:
        words = re.findall(r"[a-zA-Z']+", text.lower())
        word_count = len(words)
        keywords = [k.strip().lower() for k in target_keywords.split(",") if k.strip()]

        keyword_hits = {kw: text.lower().count(kw) for kw in keywords}
        keyword_density = {
            kw: round((count / word_count) * 100, 2) if word_count else 0
            for kw, count in keyword_hits.items()
        }

        top_terms = Counter(w for w in words if w not in STOPWORDS and len(w) > 3).most_common(10)
        headings = len(re.findall(r"^#{1,3}\s", text, flags=re.MULTILINE))
        avg_sentence_len = word_count / max(text.count(".") + text.count("!") + text.count("?"), 1)

        score = 60
        if 600 <= word_count <= 2000:
            score += 15
        if headings >= 3:
            score += 10
        if keywords and all(0.5 <= keyword_density.get(k, 0) <= 3.0 for k in keywords):
            score += 15
        score = min(score, 100)

        suggestions = []
        if word_count < 600:
            suggestions.append("Consider expanding content to 600+ words for stronger topical depth.")
        if headings < 3:
            suggestions.append("Add more H2/H3 subheadings to improve scannability.")
        for kw, density in keyword_density.items():
            if density < 0.5:
                suggestions.append(f"Keyword '{kw}' is underused ({density}% density) — use it a few more times naturally.")
            elif density > 3.0:
                suggestions.append(f"Keyword '{kw}' may be overused ({density}% density) — risk of keyword stuffing.")

        return (
            f"SEO Score: {score}/100\n"
            f"Word count: {word_count}\n"
            f"Headings found: {headings}\n"
            f"Avg sentence length: {round(avg_sentence_len, 1)} words\n"
            f"Keyword density: {keyword_density}\n"
            f"Top recurring terms: {top_terms}\n"
            f"Suggestions: {'; '.join(suggestions) if suggestions else 'Looks solid.'}"
        )
