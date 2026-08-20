"""
Prompt template for ontology extraction from Korean game company event operation documents.

Extracts three ontology categories:
  - Objects: actor / domain / tx / cs / record
  - Links:   directional relationship between two Objects
  - Actions: behaviour performed by an actor
"""

import json

# ---------------------------------------------------------------------------
# System prompt (Korean) — must not be modified without re-running the spike
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """당신은 게임 회사의 이벤트 운영 문서에서 온톨로지 구성 요소를 추출하는 전문가입니다.
다음 카테고리를 한국어로 추출하세요:
- Objects: 행위 주체(actor), 이벤트 도메인 개체(domain), 트랜잭션(tx), CS 처리(cs), 기록(record)
- Links: 두 Object 간 관계 (label, cardinality, 파생 여부)
- Actions: 행위 주체가 수행하는 동작 (입력/출력/전제조건)

출력 형식: 아래 JSON 스키마를 반드시 준수하세요.

{
  "objects": [
    {
      "name": "string (Korean)",
      "category": "actor|domain|tx|cs|record",
      "properties": ["string"],
      "confidence": 0.0,
      "evidence_quote": "string (exact quote from document)"
    }
  ],
  "links": [
    {
      "from_name": "string",
      "to_name": "string",
      "label": "string (Korean)",
      "cardinality": "1:1|1:N|N:1|N:M",
      "is_derived": false,
      "confidence": 0.0,
      "evidence_quote": "string"
    }
  ],
  "actions": [
    {
      "name": "string (Korean)",
      "actor_name": "string",
      "reads": ["string"],
      "creates": ["string"],
      "updates": ["string"],
      "preconditions": "string",
      "outcomes": "string",
      "trigger": "manual_ui|scheduled|notion_webhook",
      "confidence": 0.0,
      "evidence_quote": "string"
    }
  ]
}

반드시 유효한 JSON만 출력하세요. 마크다운 코드 블록, 추가 설명, 주석을 포함하지 마세요."""

# ---------------------------------------------------------------------------
# Output schema reference (Python dict, mirrors the JSON schema above)
# ---------------------------------------------------------------------------

OUTPUT_JSON_SCHEMA = {
    "objects": [
        {
            "name": "string (Korean)",
            "category": "actor|domain|tx|cs|record",
            "properties": ["string"],
            "confidence": 0.0,
            "evidence_quote": "string (exact quote from document)",
        }
    ],
    "links": [
        {
            "from_name": "string",
            "to_name": "string",
            "label": "string (Korean)",
            "cardinality": "1:1|1:N|N:1|N:M",
            "is_derived": False,
            "confidence": 0.0,
            "evidence_quote": "string",
        }
    ],
    "actions": [
        {
            "name": "string (Korean)",
            "actor_name": "string",
            "reads": ["string"],
            "creates": ["string"],
            "updates": ["string"],
            "preconditions": "string",
            "outcomes": "string",
            "trigger": "manual_ui|scheduled|notion_webhook",
            "confidence": 0.0,
            "evidence_quote": "string",
        }
    ],
}


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_user_prompt(document_text: str) -> str:
    """
    Wrap the document text in a user turn that asks Claude to extract
    ontology elements and return them as JSON.

    Args:
        document_text: Full text content of the Korean event operation document.

    Returns:
        Formatted user prompt string.
    """
    return (
        "다음 게임 회사 이벤트 운영 문서에서 온톨로지 구성 요소를 추출하세요.\n\n"
        "=== 문서 내용 ===\n"
        f"{document_text}\n"
        "=================\n\n"
        "위 문서에서 Objects, Links, Actions를 추출하여 JSON 형식으로만 출력하세요."
    )
