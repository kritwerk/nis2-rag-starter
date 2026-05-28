from nis2_rag.config import Settings
from nis2_rag.qa import answer_question, build_prompt, format_citations
from nis2_rag.store import Hit


def _hits() -> list[Hit]:
    return [
        Hit(text="Meldung innerhalb 24h.", source="policy.md", page=2, score=0.91),
        Hit(text="Folgemeldung 72h.", source="policy.md", page=2, score=0.88),
        Hit(text="Anderer Auszug.", source="other.pdf", page=5, score=0.71),
    ]


def test_build_prompt_includes_all_sources() -> None:
    prompt = build_prompt("Frist?", _hits())
    assert "policy.md" in prompt
    assert "other.pdf" in prompt
    assert "Seite 2" in prompt and "Seite 5" in prompt


def test_format_citations_deduplicates() -> None:
    out = format_citations(_hits())
    assert out.count("policy.md, Seite 2") == 1
    assert "other.pdf, Seite 5" in out


def test_answer_question_with_echo_provider_adds_citations() -> None:
    settings = Settings(llm_provider="echo")
    answer = answer_question("Frist?", _hits(), settings)
    # Echo provider does not emit "[" — answer logic must append citations.
    assert "policy.md, Seite 2" in answer.text
    assert answer.citations == _hits()
