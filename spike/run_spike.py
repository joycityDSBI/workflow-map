"""
run_spike.py — Accuracy spike runner for JoyCity Ontology Builder.

Reads Korean event operation documents (.md), calls Claude via Vertex AI to
extract ontology entities (Objects, Links, Actions), and saves results as JSON.

Usage:
    python run_spike.py [--docs-dir PATH] [--max-docs N]

Examples:
    # Quick test with 3 bundled sample documents
    python run_spike.py --docs-dir sample_docs

    # Full spike against exported Notion docs
    python run_spike.py --docs-dir /path/to/notion-export --max-docs 50

Environment (Vertex AI — no API key needed, uses GCP ADC):
    GCP_PROJECT_ID   — GCP 프로젝트 ID (필수)
    VERTEX_LOCATION  — Vertex AI 리전 (기본값: us-east5)
    VERTEX_MODEL_ID  — Vertex AI 모델 ID (기본값: claude-sonnet-5@20251001)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from prompt_template import SYSTEM_PROMPT, build_user_prompt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_TOKENS = 4096
MAX_RETRIES = 3
RESULTS_DIR = Path("results")

# ---------------------------------------------------------------------------
# Claude API call with exponential backoff
# ---------------------------------------------------------------------------


def extract_ontology(client: anthropic.AnthropicVertex, document_text: str, model: str) -> dict:
    """
    Call the Claude API to extract ontology elements from a document.
    Retries up to MAX_RETRIES times with exponential backoff on rate-limit
    or transient server errors.

    Args:
        client:        Initialised Anthropic client.
        document_text: Full text of the Korean event operation document.

    Returns:
        Parsed JSON dict with keys: objects, links, actions.

    Raises:
        RuntimeError: If all retries are exhausted or the response cannot be parsed.
    """
    user_prompt = build_user_prompt(document_text)

    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = response.content[0].text.strip()

            # Strip markdown fences if the model wrapped the JSON anyway
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                # Drop opening fence (e.g. ```json) and closing fence
                inner = []
                in_block = False
                for line in lines:
                    if line.startswith("```") and not in_block:
                        in_block = True
                        continue
                    if line.startswith("```") and in_block:
                        break
                    if in_block:
                        inner.append(line)
                raw_text = "\n".join(inner)

            return json.loads(raw_text)

        except anthropic.RateLimitError as exc:
            last_exception = exc
            wait = 2 ** attempt  # 1 s, 2 s, 4 s
            print(
                f"  [rate limit] Waiting {wait}s before retry "
                f"{attempt + 1}/{MAX_RETRIES}…"
            )
            time.sleep(wait)

        except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            last_exception = exc
            wait = 2 ** attempt
            print(
                f"  [API error] {exc}. Waiting {wait}s before retry "
                f"{attempt + 1}/{MAX_RETRIES}…"
            )
            time.sleep(wait)

        except json.JSONDecodeError as exc:
            # The model returned something that isn't valid JSON — not retryable
            raise RuntimeError(
                f"Claude returned non-JSON output: {exc}\nRaw text: {raw_text!r}"
            ) from exc

    raise RuntimeError(
        f"All {MAX_RETRIES} retries exhausted. Last error: {last_exception}"
    )


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run(docs_dir: Path, max_docs: int | None) -> None:
    """
    Process all .md documents in docs_dir, extract ontology elements via
    Claude, and write results to the results/ directory.
    """
    # Discover documents
    md_files = sorted(docs_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {docs_dir}. Exiting.")
        sys.exit(1)

    if max_docs is not None:
        md_files = md_files[:max_docs]

    total = len(md_files)
    print(f"Found {total} document(s) in '{docs_dir}'.\n")

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Vertex AI 클라이언트 초기화 ────────────────────────────────────────────
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        print(
            "Error: GCP_PROJECT_ID is not set.\n"
            "Set it with:  export GCP_PROJECT_ID=your-gcp-project-id\n"
            "Or add GCP_PROJECT_ID=... to a .env file",
            file=sys.stderr,
        )
        sys.exit(1)

    location = os.environ.get("VERTEX_LOCATION", "us-east5")
    model = os.environ.get("VERTEX_MODEL_ID", "claude-sonnet-5@20251001")

    print(f"Vertex AI — project: {project_id}, region: {location}, model: {model}\n")

    # 인증: GCP ADC 자동 처리 (VM 서비스 계정 또는 gcloud auth application-default login)
    client = anthropic.AnthropicVertex(project_id=project_id, region=location)

    succeeded = 0
    failed = 0

    for idx, md_path in enumerate(md_files, start=1):
        doc_name = md_path.stem  # e.g. "event_001"
        print(f"Processing doc {idx}/{total}: {md_path.name}…", end=" ", flush=True)

        document_text = md_path.read_text(encoding="utf-8")

        try:
            result = extract_ontology(client, document_text, model)
        except RuntimeError as exc:
            print(f"FAILED\n  {exc}")
            failed += 1
            continue

        # Annotate result with source metadata
        result["_meta"] = {
            "source_file": str(md_path),
            "model": model,
            "vertex_project": project_id,
            "vertex_location": location,
        }

        out_path = RESULTS_DIR / f"{doc_name}.json"
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"OK → {out_path}")
        succeeded += 1

    print(f"\nDone. {succeeded} succeeded, {failed} failed.")
    if succeeded == 0:
        print("No results were saved. Check errors above.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the JoyCity Ontology Builder accuracy spike."
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing .md documents to process. "
            "Defaults to 'docs/' if it exists, otherwise 'sample_docs/'."
        ),
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of documents to process (default: all).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    load_dotenv()  # load .env if present

    args = parse_args()

    # Resolve docs directory
    if args.docs_dir is not None:
        docs_dir = args.docs_dir
    elif Path("docs").is_dir():
        docs_dir = Path("docs")
    else:
        docs_dir = Path("sample_docs")

    if not docs_dir.is_dir():
        print(
            f"Error: docs directory '{docs_dir}' does not exist.\n"
            "Pass --docs-dir to specify a valid path.",
            file=sys.stderr,
        )
        sys.exit(1)

    run(docs_dir, args.max_docs)
