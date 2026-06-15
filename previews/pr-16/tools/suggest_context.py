#!/usr/bin/env python3
"""
suggest_context.py — NCERT Subtopic Suggester
===============================================
Fetches the latest 2026-27 NCERT subtopics for a given class/subject/topic
using the Gemini API, lets you cherry-pick, and outputs a ready-to-use
generate_test.py command.

Usage:
  python3 tools/suggest_context.py \
      --class 9 \
      --subject "Social Science" \
      --topics "Democracy"

  # With optional marks/time (for the final command):
  python3 tools/suggest_context.py \
      --class 9 \
      --subject "Social Science" \
      --topics "Shaping Of Earth" \
      --marks 45 --time 60

Requirements:
  pip install google-generativeai python-dotenv
  Set GEMINI_API_KEY in tools/.env
"""

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path

# ── Load .env from same directory as this script ──────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ── Gemini import ─────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


# ══════════════════════════════════════════════════════════════
# PROMPT FOR SUBTOPIC EXTRACTION
# ══════════════════════════════════════════════════════════════

SUBTOPIC_PROMPT = """\
You are an expert on the latest 2026-27 NCERT curriculum aligned with
NCF-SE 2023 and NEP 2020.

For Class {CLASS} {SUBJECT}, the chapter/topic is: "{TOPICS}"

List ALL the major subtopics covered in this chapter in the latest
2026-27 NCERT textbook. Be comprehensive — include every testable
subtopic a student should study.

IMPORTANT RULES:
1. Use the 2026-27 integrated textbook structure (NOT old textbooks).
2. For Social Science: the textbook is "Gateway to Social Science" (integrated).
3. Each subtopic should be a short, clear phrase (5-10 words max).
4. Include 8-15 subtopics covering the FULL chapter scope.
5. Order them logically as they appear in the chapter.

Output ONLY a JSON array of strings. No markdown, no explanation.
Example: ["Subtopic 1", "Subtopic 2", "Subtopic 3"]

BEGIN OUTPUT:
"""


def build_subtopic_prompt(class_num: str, subject: str, topics: str) -> str:
    """Build the prompt for subtopic extraction."""
    return SUBTOPIC_PROMPT.format(
        CLASS=class_num,
        SUBJECT=subject,
        TOPICS=topics,
    )


def fetch_subtopics(class_num: str, subject: str, topics: str, api_key: str) -> list[str]:
    """Call Gemini to get subtopics for a chapter."""
    prompt = build_subtopic_prompt(class_num, subject, topics)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )

    raw = response.text.strip()
    # Strip markdown fences if present
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        subtopics = json.loads(raw)
        if isinstance(subtopics, list):
            return [str(s) for s in subtopics]
    except json.JSONDecodeError:
        pass

    # Fallback: try line-by-line parsing
    lines = [l.strip().lstrip("-•*0123456789.) ") for l in raw.splitlines() if l.strip()]
    return lines if lines else ["(Could not parse subtopics — try again)"]


def interactive_select(subtopics: list[str]) -> list[str]:
    """Let the user cherry-pick subtopics interactively."""
    print()
    print("─" * 56)
    print("  SELECT SUBTOPICS (enter numbers separated by spaces)")
    print("  Type 'all' to select all, or 'q' to quit")
    print("─" * 56)
    print()

    for i, topic in enumerate(subtopics, 1):
        print(f"  [{i:2d}] {topic}")

    print()
    selection = input("  Your selection → ").strip()

    if selection.lower() == 'q':
        print("\n  Cancelled.")
        sys.exit(0)

    if selection.lower() == 'all':
        return subtopics

    try:
        indices = [int(x) for x in selection.replace(",", " ").split()]
        selected = [subtopics[i - 1] for i in indices if 1 <= i <= len(subtopics)]
        return selected
    except (ValueError, IndexError):
        print("  ⚠  Invalid selection. Using all subtopics.")
        return subtopics


def build_command(args, selected: list[str]) -> str:
    """Build the final generate_test.py command."""
    parts = [
        "python3 tools/generate_test.py",
        f'    --class {args.class_num}',
        f'    --subject "{args.subject}"',
    ]

    # Topics
    topic_args = " ".join(f'"{t}"' for t in args.topics)
    parts.append(f'    --topics {topic_args}')

    parts.append(f'    --marks {args.marks}')
    parts.append(f'    --time {args.time}')

    # Context
    if selected:
        context_args = " \\\n        ".join(f'"{s}"' for s in selected)
        parts.append(f'    --context \\\n        {context_args}')

    parts.append('    --dry-run')

    return " \\\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        prog="suggest_context.py",
        description="Fetch NCERT subtopics and build a generate_test.py command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
          ─────────────────────────────────────────────────
          Examples
          ─────────────────────────────────────────────────
          # Social Science — Democracy
          python3 tools/suggest_context.py \\
              --class 9 --subject "Social Science" \\
              --topics "Democracy"

          # Science — Motion
          python3 tools/suggest_context.py \\
              --class 9 --subject "Science" \\
              --topics "Motion" \\
              --marks 40 --time 90
          ─────────────────────────────────────────────────
        """),
    )

    parser.add_argument("--class", dest="class_num", required=True, metavar="NUM")
    parser.add_argument("--subject", required=True, metavar="NAME")
    parser.add_argument("--topics", nargs="+", required=True, metavar="TOPIC")
    parser.add_argument("--marks", type=int, default=40, metavar="N")
    parser.add_argument("--time", type=int, default=90, metavar="MIN")
    parser.add_argument("--api-key", default=None, metavar="KEY")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the prompt that would be sent to Gemini, without calling the API",
    )
    parser.add_argument(
        "--show-prompt", action="store_true",
        help="Print the prompt AND call the API (useful for debugging)",
    )

    args = parser.parse_args()

    topics_str = ", ".join(args.topics)

    # ── Dry run or show prompt ───────────────────────────────
    if args.dry_run or args.show_prompt:
        prompt = build_subtopic_prompt(args.class_num, args.subject, topics_str)
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

    # ── Fetch subtopics ──────────────────────────────────────
    print(f"\n⏳  Fetching subtopics for Class {args.class_num} {args.subject} — {topics_str} ...")

    subtopics = fetch_subtopics(args.class_num, args.subject, topics_str, api_key)

    print(f"\n✅  Found {len(subtopics)} subtopics from 2026-27 NCERT syllabus:\n")

    # ── Interactive selection ────────────────────────────────
    selected = interactive_select(subtopics)

    if not selected:
        print("  ⚠  No subtopics selected. Command will be generated without --context.")

    # ── Build and display command ────────────────────────────
    cmd = build_command(args, selected)

    print()
    print("═" * 56)
    print("  READY-TO-USE COMMAND")
    print("  (remove --dry-run when ready to generate)")
    print("═" * 56)
    print()
    print(cmd)
    print()

    # ── Copy hint ────────────────────────────────────────────
    print("💡  Tip: Copy the command above, review it, then run!")
    print("    Remove --dry-run to call the API and generate JSON.\n")


if __name__ == "__main__":
    main()
