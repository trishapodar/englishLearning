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
        20: {"A": (4, 1), "B": (2, 2), "C": (2, 3), "D": (1, 5)},
        30: {"A": (4, 1), "B": (4, 2), "C": (4, 3), "D": (2, 4)},
        40: {"A": (4, 1), "B": (4, 2), "C": (6, 3), "D": (2, 5)},
        50: {"A": (6, 1), "B": (6, 2), "C": (6, 3), "D": (2, 5)},
        80: {"A": (20,1), "B": (6, 2), "C": (8, 3), "D": (3, 5)},
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
- Difficulty: 40% Easy · 40% Moderate · 20% Challenging (HOTS).
- Include at least 2 real-life / application questions; mark them ★.
- Questions requiring a figure: append [Figure Required] after the stem.
- No hints, notes, or sub-labels inside question stems.

═══════════════════════════════════════
HTML OUTPUT FORMAT (STRICT)
═══════════════════════════════════════
Output ONLY a complete, self-contained HTML document.
No markdown. No ```html fences. No commentary outside the HTML.

CSS RULES (inside <style> tag — use named CSS classes, NOT inline style="" on individual elements):
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:"Times New Roman",Times,serif; font-size:12pt; color:#000; background:#fff;
          max-width:21cm; margin:0 auto; padding:2cm 2.2cm; line-height:1.6; }}
  h1 {{ font-size:15pt; text-align:center; }}
  h2 {{ font-size:13pt; margin:20px 0 6px; }}
  h3 {{ font-size:12pt; margin:14px 0 4px; }}
  h4 {{ font-size:12pt; margin:12px 0 4px; }}
  p  {{ margin:4px 0; }}
  ol {{ margin-left:22px; }}
  li {{ margin-bottom:10px; }}
  table {{ border-collapse:collapse; width:100%; margin-top:10px; }}
  th, td {{ border:1px solid #555; padding:5px 10px; text-align:left; }}
  th {{ background:#e8e8e8; }}
  .school-header {{ text-align:center; border-bottom:3px double #000; padding-bottom:10px; margin-bottom:10px; }}
  .meta-table {{ width:100%; margin:10px 0 16px; font-size:11pt; border-collapse:collapse; }}
  .meta-table td {{ border:none; padding:3px 6px; vertical-align:top; }}
  .meta-right {{ text-align:right; }}
  .instructions {{ border:1px solid #000; padding:8px 14px; margin-bottom:18px; font-size:11pt; }}
  .instructions ol {{ margin-top:4px; }}
  .instructions li {{ margin-bottom:2px; }}
  .section-head {{ background:#000; color:#fff; padding:5px 10px; font-size:11.5pt; font-weight:bold; margin:20px 0 10px; }}
  .section-sub {{ font-size:10pt; font-style:italic; margin-bottom:10px; color:#333; }}
  .question {{ margin-bottom:14px; page-break-inside:avoid; }}
  .q-row {{ display:flex; gap:8px; align-items:flex-start; }}
  .q-num {{ font-weight:bold; min-width:32px; flex-shrink:0; }}
  .q-body {{ flex:1; }}
  .q-marks {{ font-weight:bold; white-space:nowrap; min-width:60px; text-align:right; flex-shrink:0; font-size:10.5pt; }}
  .ans-space {{ border-bottom:1px dashed #aaa; margin-top:6px; }}
  .ans-1 {{ height:1.5cm; }}
  .ans-2 {{ height:3cm; }}
  .ans-3 {{ height:5cm; }}
  .ans-5 {{ height:9cm; }}
  hr.thin {{ border:none; border-top:1px solid #ccc; margin:18px 0; }}
  .answer-key {{ border-top:4px double #000; padding-top:18px; margin-top:30px; }}
  .answer-key h2 {{ text-align:center; font-size:15pt; letter-spacing:1px; margin-bottom:4px; }}
  .ak-subtitle {{ text-align:center; font-size:10pt; font-style:italic; color:#444; margin-bottom:16px; }}
  .ak-section {{ margin-top:18px; }}
  .ak-section h3 {{ font-size:12pt; border-bottom:1.5px solid #000; padding-bottom:3px; margin-bottom:10px; }}
  .ak-q {{ margin-bottom:14px; padding-left:12px; border-left:3px solid #ccc; }}
  .ak-q-head {{ font-weight:bold; margin-bottom:4px; }}
  .rubric {{ margin-top:6px; font-size:10pt; background:#f5f5f5; border:1px solid #ddd; padding:5px 10px; }}
  .rubric strong {{ display:block; margin-bottom:2px; }}
  @media print {{ body {{ padding:1.2cm 1.5cm; }} }}

Document structure — in this EXACT order:

  1. <!DOCTYPE html><html lang="en"><head>
       <meta charset="UTF-8">
       <title>Class {CLASS} {SUBJECT} — Weekly Test</title>
       <style> ... all CSS above ... </style>
     </head><body>

  2. Centered header block (class="school-header"):
       <h1>WEEKLY TEST — {SUBJECT} (CLASS {CLASS})</h1>
       <p><strong>Topics:</strong> {TOPICS_INLINE}</p>

  3. Two-column meta table (class="meta-table"):
     Left cell: School: _____ / Name: _____ / Roll No.: _____
     Right cell (class="meta-right"): Class & Section: {CLASS} — ___ / Date: {DATE} / Time: {TIME} min | Max Marks: {MARKS}

  4. Boxed instructions div (class="instructions"):
     <strong>General Instructions:</strong>
     Numbered <ol> with exactly 5 rules covering:
       all compulsory, four sections A-D, neat diagrams, show all working, marks in brackets.

  5. For each section A → D:
     <div class="section-head">SECTION — [letter] &nbsp;| [Short Answer / Long Answer] | ([n] × [m] = [total] Marks)</div>
     <p class="section-sub"><em>Questions n to m carry <strong>[marks] mark(s)</strong> each.</em></p>

     Each question as:
     <div class="question">
       <div class="q-row">
         <div class="q-num">Qn.</div>
         <div class="q-body">
           [Question stem text. Mark application questions with ★. Append [Figure Required] if needed.]
           <div class="ans-space ans-[N]"></div>
           <p style="text-align:right; font-size:10pt;">[N Mark(s)]</p>
         </div>
         <div class="q-marks">[N Marks]</div>
       </div>
     </div>
     Separate consecutive questions with: <hr class="thin">
     Use class ans-1 / ans-2 / ans-3 / ans-5 matching the mark value.

  6. Marks summary footer after the last section:
     <div style="margin-top:30px; border-top:2px solid #000; padding-top:10px; font-size:10.5pt;">
       <strong>Section Summary:</strong>&nbsp;|&nbsp;
       Section A: [n]×1 = <strong>X Marks</strong> &nbsp;|&nbsp; ... &nbsp;|&nbsp; <strong>Total: {MARKS} Marks</strong>
     </div>

  7. Answer Key block (class="answer-key"):
     <h2>⁂ &nbsp; ANSWER KEY &nbsp; ⁂</h2>
     <p class="ak-subtitle">Class {CLASS} {SUBJECT} — Weekly Test &nbsp;|&nbsp; CBSE Marking Scheme</p>
     <p style="font-size:10pt; text-align:center; margin-bottom:14px;">
       <em>Award marks as indicated. For multi-step questions award marks stepwise for correct reasoning.</em>
     </p>

     For each section, a <div class="ak-section"> with:
       <h3>SECTION [letter] — [marks] Mark(s) Each</h3>

     For each question, a <div class="ak-q"> with:
       <div class="ak-q-head">Q[n]. &nbsp; [brief answer label] &nbsp; [[marks] Mark(s)]</div>
       <p>[Full correct answer.]</p>
       [Step lines each as <p> starting with → ]
       <div class="rubric">
         <strong>Marking:</strong> ... detailed breakdown ...
         <strong>Accept:</strong> ... alternate phrasings or methods ...
         <strong>Common Error:</strong> ... what students typically get wrong ...
       </div>
       <p><em>Ref: NCERT Class {CLASS} {SUBJECT}, Ch. X, Ex. Y.Z</em></p>

  8. Marks distribution table at the very end:
     <table> with columns: Section | Questions | Marks/Q | Total Marks | Content Focus
     Include a bold Total row.

═══════════════════════════════════════
OUTPUT — BEGIN IMMEDIATELY WITH <!DOCTYPE html>
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
