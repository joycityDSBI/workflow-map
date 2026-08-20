"""
evaluate.py — Precision scoring for the JoyCity Ontology Builder accuracy spike.

Compares Claude extraction results (results/) against human ground truth
(ground_truth/) and reports per-category precision with a pass/fail verdict.

Usage:
    python evaluate.py [--results-dir PATH] [--ground-truth-dir PATH]

Pass criteria: overall precision >= 70%
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Matching thresholds
# ---------------------------------------------------------------------------

OBJECT_NAME_THRESHOLD = 0.80   # fuzzy name similarity for Object match
LINK_NAME_THRESHOLD   = 0.80   # fuzzy name similarity for Link from_name / to_name
LINK_LABEL_THRESHOLD  = 0.70   # fuzzy label similarity for Link match
PASS_THRESHOLD        = 0.70   # overall precision required to PASS

# ---------------------------------------------------------------------------
# Fuzzy string matching
# ---------------------------------------------------------------------------


def similarity(a: str, b: str) -> float:
    """Return [0, 1] string similarity using SequenceMatcher (no extra deps)."""
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


# ---------------------------------------------------------------------------
# Per-element matchers
# ---------------------------------------------------------------------------


def object_matches(extracted: dict, truth: dict) -> bool:
    """
    An extracted Object matches a ground-truth Object when:
      - name similarity >= OBJECT_NAME_THRESHOLD
      - category is identical
    """
    name_ok = similarity(extracted.get("name", ""), truth.get("name", "")) >= OBJECT_NAME_THRESHOLD
    cat_ok  = extracted.get("category", "").lower() == truth.get("category", "").lower()
    return name_ok and cat_ok


def link_matches(extracted: dict, truth: dict) -> bool:
    """
    An extracted Link matches a ground-truth Link when:
      - from_name similarity >= LINK_NAME_THRESHOLD
      - to_name   similarity >= LINK_NAME_THRESHOLD
      - label     similarity >= LINK_LABEL_THRESHOLD
    """
    from_ok  = similarity(extracted.get("from_name", ""), truth.get("from_name", "")) >= LINK_NAME_THRESHOLD
    to_ok    = similarity(extracted.get("to_name",   ""), truth.get("to_name",   "")) >= LINK_NAME_THRESHOLD
    label_ok = similarity(extracted.get("label",     ""), truth.get("label",     "")) >= LINK_LABEL_THRESHOLD
    return from_ok and to_ok and label_ok


# ---------------------------------------------------------------------------
# Precision computation
# ---------------------------------------------------------------------------


def compute_precision(
    extracted_items: list,
    truth_items: list,
    match_fn,
) -> tuple[int, int, float]:
    """
    Compute precision = matched / extracted.

    Each extracted item is counted as matched if at least one truth item
    satisfies match_fn (greedy — first match wins, no double-counting of
    truth items needed for precision).

    Returns:
        (n_extracted, n_matched, precision)
    """
    if not extracted_items:
        return 0, 0, 0.0

    matched = 0
    for ext in extracted_items:
        for truth in truth_items:
            if match_fn(ext, truth):
                matched += 1
                break  # count this extracted item as matched once

    precision = matched / len(extracted_items)
    return len(extracted_items), matched, precision


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------


def print_report(
    n_docs: int,
    obj_extracted: int,
    obj_matched: int,
    obj_precision: float,
    lnk_extracted: int,
    lnk_matched: int,
    lnk_precision: float,
) -> None:
    overall = (
        (obj_matched + lnk_matched) / (obj_extracted + lnk_extracted)
        if (obj_extracted + lnk_extracted) > 0
        else 0.0
    )

    passed = overall >= PASS_THRESHOLD
    verdict = "PASS ✅" if passed else "FAIL ❌"

    print()
    print("=== Accuracy Spike Results ===")
    print(f"Documents tested: {n_docs}")
    print()
    print("Objects:")
    print(
        f"  Extracted: {obj_extracted:<4} | "
        f"Matched: {obj_matched:<4} | "
        f"Precision: {obj_precision * 100:.1f}%"
    )
    print()
    print("Links:")
    print(
        f"  Extracted: {lnk_extracted:<4} | "
        f"Matched: {lnk_matched:<4} | "
        f"Precision: {lnk_precision * 100:.1f}%"
    )
    print()
    print(f"Overall precision: {overall * 100:.1f}%")
    print(f"RESULT: {verdict} (threshold: {int(PASS_THRESHOLD * 100)}%)")
    print()

    return passed


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------


def evaluate(results_dir: Path, ground_truth_dir: Path) -> None:
    # Find documents that have both a result and a ground truth
    result_files = {p.stem: p for p in results_dir.glob("*.json")}
    truth_files  = {p.stem: p for p in ground_truth_dir.glob("*.json")}

    common = sorted(set(result_files) & set(truth_files))
    if not common:
        print(
            f"No matching files found between '{results_dir}' and '{ground_truth_dir}'.\n"
            "Run 'python run_spike.py --docs-dir sample_docs' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    only_results = set(result_files) - set(truth_files)
    only_truth   = set(truth_files) - set(result_files)
    if only_results:
        print(f"Warning: no ground truth for: {', '.join(sorted(only_results))}")
    if only_truth:
        print(f"Warning: no results yet for:  {', '.join(sorted(only_truth))}")

    # Aggregate counts across all documents
    total_obj_extracted = 0
    total_obj_matched   = 0
    total_lnk_extracted = 0
    total_lnk_matched   = 0

    for stem in common:
        result = json.loads(result_files[stem].read_text(encoding="utf-8"))
        truth  = json.loads(truth_files[stem].read_text(encoding="utf-8"))

        ext_objects = result.get("objects", [])
        tru_objects = truth.get("objects", [])
        n_ext, n_mat, _ = compute_precision(ext_objects, tru_objects, object_matches)
        total_obj_extracted += n_ext
        total_obj_matched   += n_mat

        ext_links = result.get("links", [])
        tru_links = truth.get("links", [])
        n_ext, n_mat, _ = compute_precision(ext_links, tru_links, link_matches)
        total_lnk_extracted += n_ext
        total_lnk_matched   += n_mat

    obj_precision = (
        total_obj_matched / total_obj_extracted if total_obj_extracted else 0.0
    )
    lnk_precision = (
        total_lnk_matched / total_lnk_extracted if total_lnk_extracted else 0.0
    )

    passed = print_report(
        n_docs        = len(common),
        obj_extracted = total_obj_extracted,
        obj_matched   = total_obj_matched,
        obj_precision = obj_precision,
        lnk_extracted = total_lnk_extracted,
        lnk_matched   = total_lnk_matched,
        lnk_precision = lnk_precision,
    )

    sys.exit(0 if passed else 1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate ontology extraction precision against ground truth."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directory containing Claude extraction results (default: results/).",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=Path("ground_truth"),
        help="Directory containing ground truth JSON files (default: ground_truth/).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    for d, label in [(args.results_dir, "results"), (args.ground_truth_dir, "ground_truth")]:
        if not d.is_dir():
            print(
                f"Error: {label} directory '{d}' does not exist.\n"
                f"For '{label}', check the path or run the spike first.",
                file=sys.stderr,
            )
            sys.exit(1)

    evaluate(args.results_dir, args.ground_truth_dir)
