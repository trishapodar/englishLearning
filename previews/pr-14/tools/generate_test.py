#!/usr/bin/env python3
"""
generate_test.py — CBSE Weekly Test Generator CLI
==================================================
Generates a print-ready, DOCX-compatible CBSE test paper
by calling the Gemini API with a structured prompt.

Usage:
  python3 generate_test.py \\
      --class 9 \\
      --subject Mathematics \\
      --topics "Coordinate Geometry" "Congruent Triangles" \\
      --time 90 \\
      --marks 40 \\
      --output ../math_tests/

Requirements:
  pip install google-generativeai python-dotenv
  Set GEMINI_API_KEY in tools/.env  (or pass --api-key)
"""

import argparse
import os
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path

# ── Load .env from same directory as this script ──────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # python-dotenv optional; fall back to env vars

# ── Gemini import ─────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


# ══════════════════════════════════════════════════════════════
# SECTION DISTRIBUTION
# ══════════════════════════════════════════════════════════════

def compute_distribution(total_marks: int) -> dict:
    """
    Return the CBSE section breakdown for a given total-marks target.
    Each value is a tuple (question_count, marks_per_question).
    """
    presets = {
        20: {"A": (5, 1), "B": (2, 2), "C": (2, 3), "D": (1, 5)},
        30: {"A": (6, 1), "B": (4, 2), "C": (2, 3), "D": (2, 5)},
        40: {"A": (4, 1), "B": (4, 2), "C": (6, 3), "D": (2, 5)},
        50: {"A": (10, 1), "B": (5, 2), "C": (5, 3), "D": (3, 5)},
        80: {"A": (20, 1), "B": (5, 2), "C": (6, 3), "D": (4, 5), "E": (3, 4)},
    }
    if total_marks in presets:
        return presets[total_marks]

    # Auto-scale for arbitrary totals
    a_marks = max(4, total_marks // 10)
    b_marks = max(8, total_marks // 5)
    d_marks = 10
    c_marks = total_marks - a_marks - b_marks - d_marks
    return {
        "A": (a_marks,       1),
        "B": (b_marks // 2,  2),
        "C": (c_marks // 3,  3),
        "D": (d_marks // 5,  5),
    }


def distribution_summary(dist: dict) -> str:
    lines = []
    total_q = 0
    total_m = 0
    for sec, (count, marks) in dist.items():
        q_total = count * marks
        lines.append(
            f"  Section {sec} → {marks} mark{'s' if marks > 1 else ''}  "
            f"× {count} questions = {q_total} marks"
        )
        total_q += count
        total_m += q_total
    lines.append(f"  TOTAL  → {total_q} questions = {total_m} marks")
    return "\n".join(lines)


def per_topic_constraint(dist: dict, n_topics: int) -> str:
    """Tell the LLM exactly how many questions per topic per section."""
    lines = []
    for sec, (count, _) in dist.items():
        per = max(1, count // n_topics)
        lines.append(f"  Section {sec}: at least {per} question(s) per topic")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# PROMPT TEMPLATE
# ══════════════════════════════════════════════════════════════

# NOTE: All literal { } in the template that are NOT format placeholders
# must be doubled {{ }} so str.format() does not mistake them for fields.
PROMPT_TEMPLATE = """\
You are an expert CBSE paper setter working to the 2026–27 syllabus.

Generate a Class {CLASS} CBSE {SUBJECT} Weekly Test paper.

═══════════════════════════════════════
INPUTS
═══════════════════════════════════════
Class         : {CLASS}
Subject       : {SUBJECT}
Topics        :
{TOPICS}
Time Allowed  : {TIME} minutes
Total Marks   : {MARKS}
Date          : {DATE}

═══════════════════════════════════════
PAPER DESIGN — MANDATORY RULES
═══════════════════════════════════════
Section distribution (FOLLOW EXACTLY):
{DISTRIBUTION}

Topic balance per section:
{TOPIC_BALANCE}

Additional rules:
- Every topic must appear in EVERY section (A, B, C, D).
- No concept repeated across questions.
- Source: strictly NCERT textbook + NCERT Exemplar for Class {CLASS}.
  Cite chapter/exercise in the marking scheme, not in question stems.
- Difficulty: 20% Easy · 60% Moderate · 20% Challenging (HOTS).
- At least 40% of the questions must be Competency-Based Questions (CBQs) assessing application and analysis. 
- Include at least 2 real-life / application questions; mark them ★.
- Questions requiring a figure: append [Figure Required] after the stem.
- No hints, notes, or sub-labels inside question stems.

═══════════════════════════════════════
JSON OUTPUT FORMAT (STRICT)
═══════════════════════════════════════
Output ONLY a raw JSON object string. Fasten it tightly and do not use Markdown bounds like ```json.
The JSON must strictly follow this structure:

{{
  "metadata": {{
    "class": "{CLASS}",
    "subject": "{SUBJECT}",
    "topics_inline": "{TOPICS_INLINE}",
    "date": "{DATE}",
    "time": "{TIME}",
    "marks": {MARKS}
  }},
  "sections": [
    {{
      "letter": "A",
      "type": "Very Short Answer",
      "marks_per_q": 1,
      "questions": [
        {{
          "q_num": 1,
          "stem": "Question text here. HTML math formulas like \\(\\frac{{a}}{{b}}\\) are allowed. Mark application questions with ★. Append [Figure Required] if needed.",
          "marks": 1,
          "ak_label": "brief answer label",
          "ak_answer": "<p>[Full correct answer.]</p>\\n<p>→ [Step 1]</p>",
          "ak_marking": "detailed breakdown",
          "ak_accept": "alternate phrasings or methods",
          "ak_common_error": "what students typically get wrong",
          "ak_ref": "NCERT Class {CLASS} {SUBJECT}, Ch. X, Ex. Y.Z",
          "content_focus": "Specific sub-topic tested"
        }}
      ]
    }}
  ]
}}

═══════════════════════════════════════
OUTPUT — BEGIN IMMEDIATELY WITH {{
═══════════════════════════════════════
"""


# ══════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ══════════════════════════════════════════════════════════════

def build_prompt(args) -> str:
    topics_bulleted = "\n".join(f"- {t}" for t in args.topics)
    topics_inline   = ", ".join(args.topics)
    dist            = compute_distribution(args.marks)
    date_str        = datetime.now().strftime("%d %B %Y")

    return PROMPT_TEMPLATE.format(
        CLASS          = args.class_num,
        SUBJECT        = args.subject,
        TOPICS         = topics_bulleted,
        TOPICS_INLINE  = topics_inline,
        TIME           = args.time,
        MARKS          = args.marks,
        DATE           = date_str,
        DISTRIBUTION   = distribution_summary(dist),
        TOPIC_BALANCE  = per_topic_constraint(dist, len(args.topics)),
    )


# ══════════════════════════════════════════════════════════════
# API CALL
# ══════════════════════════════════════════════════════════════

def call_gemini(prompt: str, api_key: str, model_name: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.65,
            max_output_tokens=8192,
        ),
    )
    return response.text


# ══════════════════════════════════════════════════════════════
# OUTPUT HANDLING
# ══════════════════════════════════════════════════════════════

def clean_html(raw: str) -> str:
    """Strip markdown code fences if the model wraps its output."""
    raw = raw.strip()
    raw = re.sub(r"^```html?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def validate_html(html: str) -> list[str]:
    """Return a list of warnings if the output looks malformed."""
    warnings = []
    if not html.lower().startswith("<!doctype"):
        warnings.append("Output does not start with <!DOCTYPE html>")
    if "SECTION" not in html.upper():
        warnings.append("No SECTION headings found — paper may be malformed")
    if "ANSWER KEY" not in html.upper():
        warnings.append("Answer Key block not found")
    if html.count("<li>") < 10:
        warnings.append(f"Only {html.count('<li>')} <li> items — expected ≥ 20")
    return warnings


def make_output_path(args) -> Path:
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    subject_slug = re.sub(r"[^a-z0-9]+", "_", args.subject.lower()).strip("_")
    topics_slug  = "_".join(
        re.sub(r"[^a-z0-9]+", "", t.lower().split()[0])
        for t in args.topics
    )[:40]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    filename = f"class{args.class_num}_{subject_slug}_{topics_slug}_{timestamp}.html"
    return out_dir / filename


# ══════════════════════════════════════════════════════════════
# ARGUMENT PARSER
# ══════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_test.py",
        description="CBSE Weekly Test Generator — powered by Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
          ─────────────────────────────────────────────────
          Examples
          ─────────────────────────────────────────────────
          # Math test, 40 marks, 90 minutes
          python3 generate_test.py \\
              --class 9 \\
              --subject Mathematics \\
              --topics "Coordinate Geometry" "Congruent Triangles" \\
              --time 90 --marks 40

          # Science test, 30 marks, dry-run to preview prompt
          python3 generate_test.py \\
              --class 10 \\
              --subject Science \\
              --topics "Light — Reflection" "Human Eye" "Prism and Dispersion" \\
              --marks 30 \\
              --output ../science_tests/ \\
              --dry-run

          # English grammar test, custom output directory
          python3 generate_test.py \\
              --class 9 \\
              --subject English \\
              --topics "Tenses" "Subject-Verb Agreement" \\
              --marks 40 \\
              --output ../english_tests/
          ─────────────────────────────────────────────────
          API key: set GEMINI_API_KEY in tools/.env  (see .env.example)
        """),
    )

    parser.add_argument(
        "--class", dest="class_num", required=True, metavar="NUM",
        help="Class number, e.g. 9 or 10",
    )
    parser.add_argument(
        "--subject", required=True, metavar="NAME",
        help='Subject name, e.g. "Mathematics" or "Science"',
    )
    parser.add_argument(
        "--topics", nargs="+", required=True, metavar="TOPIC",
        help="One or more topic names (use quotes for multi-word topics). Max 4 recommended.",
    )
    parser.add_argument(
        "--time", type=int, default=90, metavar="MINUTES",
        help="Duration in minutes (default: 90)",
    )
    parser.add_argument(
        "--marks", type=int, default=40, metavar="N",
        help="Total marks (default: 40). Common: 20, 30, 40, 50, 80",
    )
    parser.add_argument(
        "--output", default="./generated_tests/", metavar="DIR",
        help="Output directory (default: ./generated_tests/)",
    )
    parser.add_argument(
        "--model", default="gemini-2.0-flash", metavar="MODEL",
        help='Gemini model (default: gemini-2.0-flash). Try "gemini-2.5-pro" for best quality.',
    )
    parser.add_argument(
        "--api-key", default=None, metavar="KEY",
        help="Gemini API key (overrides GEMINI_API_KEY env var)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the final prompt without calling the API",
    )
    parser.add_argument(
        "--show-prompt", action="store_true",
        help="Print the prompt AND call the API (useful for debugging)",
    )
    return parser


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    # ── Warnings ────────────────────────────────────────────
    if len(args.topics) > 4:
        print(
            "⚠  Warning: More than 4 topics may reduce quality. "
            "Consider splitting into two tests.\n"
        )

    # ── Build prompt ─────────────────────────────────────────
    prompt = build_prompt(args)

    if args.dry_run or args.show_prompt:
        sep = "═" * 64
        print(sep)
        print("PROMPT (to be sent to Gemini)")
        print(sep)
        print(prompt)
        print(sep)
        if args.dry_run:
            sys.exit(0)

    # ── API key ──────────────────────────────────────────────
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌  Error: No API key found.")
        print("    → Set GEMINI_API_KEY in tools/.env, or use --api-key KEY")
        sys.exit(1)

    if not HAS_GEMINI:
        print("❌  google-generativeai not installed.")
        print("    → Run: pip install google-generativeai")
        sys.exit(1)

    # ── Call Gemini ──────────────────────────────────────────
    print(f"\n⏳  Calling Gemini ({args.model}) …")
    print(f"    Class {args.class_num} · {args.subject} · "
          f"{', '.join(args.topics)} · {args.marks} marks")

    try:
        raw = call_gemini(prompt, api_key, args.model)
    except Exception as exc:
        print(f"❌  Gemini API error: {exc}")
        sys.exit(1)

    # ── Clean & validate ─────────────────────────────────────
    html = clean_html(raw)
    warnings = validate_html(html)
    if warnings:
        print("\n⚠  Validation warnings:")
        for w in warnings:
            print(f"   • {w}")

    # ── Save ─────────────────────────────────────────────────
    out_path = make_output_path(args)
    out_path.write_text(html, encoding="utf-8")

    print(f"\n✅  Test paper saved:")
    print(f"    {out_path.resolve()}")
    print(f"\n📄  Summary:")
    print(f"    Topics  : {', '.join(args.topics)}")
    print(f"    Marks   : {args.marks}  |  Time: {args.time} min")
    dist = compute_distribution(args.marks)
    total_q = sum(c for c, _ in dist.values())
    print(f"    Questions: {total_q}")
    print(f"\n💡  To convert to DOCX:")
    print(f"    pandoc \"{out_path}\" -o \"{out_path.stem}.docx\"")


if __name__ == "__main__":
    main()
