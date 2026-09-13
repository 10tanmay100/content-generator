"""Unit tests for individual agent builders and tools (no live LLM calls)."""
from unittest.mock import patch

from app.tools.seo_tool import SEOAnalysisTool
from app.tools.image_tool import ImagePromptTool


def test_seo_tool_scores_reasonable_content():
    tool = SEOAnalysisTool()
    text = "# Great Article\n\n" + ("This is a well written sentence about solar energy. " * 60)
    result = tool._run(text=text, target_keywords="solar energy")
    assert "SEO Score" in result
    assert "Word count" in result


def test_image_prompt_tool_returns_prompt_and_alt_text(tmp_path, monkeypatch):
    import app.tools.image_tool as image_tool_module

    monkeypatch.setattr(image_tool_module, "STORAGE_DIR", tmp_path)

    class FakeResponse:
        content = b"fake-image-bytes"

        def raise_for_status(self):
            pass

    with patch("app.tools.image_tool.requests.get", return_value=FakeResponse()) as mock_get:
        tool = ImagePromptTool()
        result = tool._run(topic="renewable energy", tone="professional")

    mock_get.assert_called_once()
    assert "IMAGE_PROMPT" in result
    assert "ALT_TEXT" in result
    assert "IMAGE_URL" in result
    assert list(tmp_path.iterdir()), "expected an image file to be saved"


@patch("app.agents.research_agent.get_tool_llm")
def test_research_agent_builds_with_mocked_llm(mock_llm):
    from app.agents.research_agent import build_research_agent

    mock_llm.return_value = "ollama_chat/llama3.2:latest"
    agent = build_research_agent()
    assert agent.role == "Senior Content Research Analyst"
    assert len(agent.tools) == 1