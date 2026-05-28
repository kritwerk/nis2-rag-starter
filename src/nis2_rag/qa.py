"""Question answering with mandatory source citations."""
from __future__ import annotations

from dataclasses import dataclass

import structlog

from nis2_rag.config import Settings
from nis2_rag.store import Hit

log = structlog.get_logger(__name__)


SYSTEM_PROMPT = (
    "Du bist ein präziser Assistent für deutsche NIS2- und KRITIS-Compliance-Fragen. "
    "Antworte ausschließlich auf Basis der bereitgestellten Quellen-Auszüge. "
    "Wenn die Auszüge die Frage nicht beantworten, sage das offen. "
    "Erfinde keine Paragrafen, Fristen oder Pflichten. "
    "Antworte knapp in 3–6 Sätzen, danach liste die genutzten Quellen als "
    "[Datei, Seite X] auf."
)


@dataclass(frozen=True)
class Answer:
    text: str
    citations: list[Hit]


def build_prompt(question: str, hits: list[Hit]) -> str:
    """Build a deterministic user prompt with numbered source blocks."""
    if not hits:
        return f"Frage: {question}\n\nKeine relevanten Auszüge gefunden."
    blocks = []
    for i, h in enumerate(hits, start=1):
        blocks.append(f"[{i}] Quelle: {h.source}, Seite {h.page}\n{h.text}")
    sources = "\n\n".join(blocks)
    return (
        f"Frage: {question}\n\n"
        f"Quellen-Auszüge:\n{sources}\n\n"
        f"Beantworte die Frage ausschließlich aus diesen Auszügen."
    )


def format_citations(hits: list[Hit]) -> str:
    seen: set[tuple[str, int]] = set()
    parts: list[str] = []
    for h in hits:
        key = (h.source, h.page)
        if key in seen:
            continue
        seen.add(key)
        parts.append(f"[{h.source}, Seite {h.page}]")
    return " ".join(parts)


def call_llm(prompt: str, settings: Settings) -> str:
    """Call the configured LLM. Falls back to a deterministic echo for tests."""
    provider = settings.llm_provider.lower()

    if provider == "echo":
        # Deterministic, no network — used in unit tests and offline demos.
        return (
            "Demo-Antwort ohne LLM-Backend: die untenstehenden Quellen-Auszüge "
            "enthalten die relevanten Informationen zur Frage."
        )

    if provider in {"openai", "ollama"}:
        from openai import OpenAI

        base_url = settings.llm_base_url
        if provider == "ollama" and not base_url:
            base_url = "http://localhost:11434/v1"

        client = OpenAI(api_key=settings.llm_api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""

    raise ValueError(f"Unknown llm_provider: {settings.llm_provider}")


def answer_question(
    question: str,
    hits: list[Hit],
    settings: Settings,
) -> Answer:
    prompt = build_prompt(question, hits)
    log.info("qa.call_llm", provider=settings.llm_provider, model=settings.llm_model)
    text = call_llm(prompt, settings).strip()
    if hits and "[" not in text:
        # Defensive: ensure citations are present even if the model forgets.
        text = f"{text}\n\nQuellen: {format_citations(hits)}"
    return Answer(text=text, citations=hits)
