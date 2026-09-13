"""Custom CrewAI tool: web search via DuckDuckGo (no API key required)."""
from crewai.tools import BaseTool
from duckduckgo_search import DDGS
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query to look up on the web")
    max_results: int = Field(
    default=5,
    description="Maximum number of results to return. Always pass this explicitly, e.g. 5.",
    json_schema_extra=lambda schema: schema.pop("default", None),
)


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Searches the public web for current information on a topic. "
        "Use this to research facts, trends, competitor content, and statistics "
        "before writing. Input should be a focused search query."
    )
    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return f"No results found for query: {query}"

            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(
                    f"{i}. {r.get('title', 'N/A')}\n   URL: {r.get('href', 'N/A')}\n   {r.get('body', '')[:280]}"
                )
            return "\n\n".join(formatted)
        except Exception as exc:  # pragma: no cover
            return f"Web search failed: {exc}"
