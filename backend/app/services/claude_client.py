"""Claude Vertex AI client for ontology extraction."""
from __future__ import annotations

import asyncio
import json
import logging
import re

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt (Korean) — mirrors spike/prompt_template.py
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """당신은 게임 회사의 이벤트 운영 문서에서 온톨로지 구성 요소를 추출하는 전문가입니다.
다음 카테고리를 한국어로 추출하세요:
- Objects: 행위 주체(actor), 이벤트 도메인 개체(domain), 트랜잭션(tx), CS 처리(cs), 기록(record)
- Links: 두 Object 간 관계 (label, cardinality, 파생 여부)
- Actions: 행위 주체가 수행하는 동작 (입력/출력/전제조건)

출력 형식: 아래 JSON 스키마를 반드시 준수하고, JSON만 출력하세요 (마크다운 코드 블록 없이).

{
  "objects": [
    {"name": "string", "category": "actor|domain|tx|cs|record", "properties": ["string"], "confidence": 0.0, "evidence_quote": "string"}
  ],
  "links": [
    {"from_name": "string", "to_name": "string", "label": "string", "cardinality": "1:1|1:N|N:1|N:M", "is_derived": false, "confidence": 0.0, "evidence_quote": "string"}
  ],
  "actions": [
    {"name": "string", "actor_name": "string", "reads": ["string"], "creates": ["string"], "updates": ["string"], "preconditions": "string", "outcomes": "string", "trigger": "manual_ui|scheduled|notion_webhook", "confidence": 0.0, "evidence_quote": "string"}
  ]
}"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client() -> anthropic.AnthropicVertex:
    return anthropic.AnthropicVertex(
        project_id=settings.GCP_PROJECT_ID,
        region=settings.VERTEX_LOCATION,
    )


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"```$", "", text.strip())
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def extract_ontology_from_text(document_text: str) -> dict:
    """Call Claude Vertex AI and return parsed ontology dict.

    Returns a dict with keys: objects, links, actions.

    If GCP_PROJECT_ID is not configured, logs a warning and returns an empty
    result without calling the API.

    Raises:
        ValueError: Claude returned non-JSON output.
        RuntimeError: Unexpected API error.
    """
    if not settings.GCP_PROJECT_ID:
        logger.warning(
            "GCP_PROJECT_ID is not configured — skipping Claude call and returning empty result"
        )
        return {"objects": [], "links": [], "actions": []}

    client = _get_client()

    # AnthropicVertex is synchronous — run in a thread pool to avoid blocking
    def _call() -> anthropic.types.Message:
        return client.messages.create(
            model=settings.VERTEX_MODEL_ID,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "다음 게임 회사 이벤트 운영 문서에서 온톨로지 구성 요소를 추출하세요.\n\n"
                        "=== 문서 내용 ===\n"
                        f"{document_text}\n"
                        "=================\n\n"
                        "위 문서에서 Objects, Links, Actions를 추출하여 JSON 형식으로만 출력하세요."
                    ),
                }
            ],
        )

    response = await asyncio.get_event_loop().run_in_executor(None, _call)
    raw = _strip_fences(response.content[0].text)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON: {e}\nRaw: {raw[:200]}")
