import json
import argparse
import sys
import os
from datetime import datetime

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "tests", "templates", "weekly_test_template.html")

def build_test(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            sys.exit(1)

    meta = data.get("metadata", {})
    sections = data.get("sections", [])

    subject = meta.get("subject", "Science")
    class_num = meta.get("class", "4")
    topics_inline = meta.get("topics_inline", "Topics")
    date_str = meta.get("date", datetime.now().strftime("%d %B %Y"))
    time_min = meta.get("time", 45)
    total_marks = meta.get("marks", 20)

    # ── Derive base_subject and sub_subject from any subject string ────────
    # e.g. "Science - Biology" → base="science", sub="biology"
    # e.g. "Maths" → base="maths", sub=""
    
    # Split by hyphen if present, clean up spaces
    subj_raw = subject.replace("—", "-").replace(" - ", "-")
    subj_parts = [p.strip().lower() for p in subj_raw.split("-") if p.strip()]
    
    base_subject = subj_parts[0].replace(" ", "_")
    sub_subject = subj_parts[1].replace(" ", "_") if len(subj_parts) > 1 else ""

    # Normalise common aliases
    if base_subject in ["math", "mathematics"]: 
        base_subject = "maths"

    # ── Build the nested output directory path ────────────────────────────
    # pattern: tests/class<num>/<base_subject>/<sub_subject>
    out_dir_parts = ["..", "tests", f"class{class_num}"]
    if base_subject:
        out_dir_parts.append(base_subject)
    if sub_subject:
        out_dir_parts.append(sub_subject)

    out_dir = os.path.join(os.path.dirname(__file__), *out_dir_parts)
    os.makedirs(out_dir, exist_ok=True)

    # ── Build a clean filename (no spaces, colons, or raw hyphens) ────────
    def _slugify(text):
        """Convert arbitrary text to a safe, lowercase filename slug."""
        import re
        text = text.lower()
        text = text.replace(" & ", "_").replace(" - ", "_")
        text = re.sub(r"[\s]+", "_", text)          # spaces → underscore
        text = re.sub(r"[^a-z0-9_]", "", text)      # strip everything else
        text = re.sub(r"_+", "_", text).strip("_")  # collapse duplicate underscores
        return text

    topics_slug = _slugify(topics_inline)
    subject_file_slug = _slugify(subject)
    date_slug = datetime.now().strftime("%Y%m%d")
    out_filename = f"class{class_num}_{subject_file_slug}_{topics_slug}_{date_slug}.html"
    out_path = os.path.join(out_dir, out_filename)

    questions_html = ""
    section_summary_html = ""
    answer_key_html = ""
    marks_distribution_html = ""
    total_questions = 0

    section_summaries = []

    for sec in sections:
        letter = sec.get("letter", "A")
        q_type = sec.get("type", "Questions")
        marks_per_q = sec.get("marks_per_q", 1)
        questions = sec.get("questions", [])
        
        num_qs = len(questions)
        total_questions += num_qs
        total_sec_marks = num_qs * marks_per_q
        
        # Section Summary
        section_summaries.append(f"Section {letter}: {num_qs}×{marks_per_q} = <strong>{total_sec_marks} Marks</strong>")
        
        # Marks distribution Table
        content_focuses = ", ".join(list(set(q.get("content_focus", "") for q in questions if q.get("content_focus"))))
        marks_distribution_html += f"<tr><td>Section {letter}</td><td>{num_qs}</td><td>{marks_per_q}</td><td>{total_sec_marks}</td><td>{content_focuses}</td></tr>\n"

        # Questions HTML
        q_start = questions[0].get('q_num', 1) if questions else 1
        q_end = questions[-1].get('q_num', 1) if questions else 1
        
        questions_html += f"""
        <div class="section-head">SECTION — {letter} &nbsp;| {q_type} | ({num_qs} × {marks_per_q} = {total_sec_marks} Marks)</div>
        <p class="section-sub"><em>Questions {q_start} to {q_end} carry <strong>{marks_per_q} mark(s)</strong> each.</em></p>
        """

        answer_key_html += f"""
        <div class="ak-section">
            <h3>SECTION {letter} — {marks_per_q} Mark(s) Each</h3>
        """

        for q in questions:
            q_num = q.get("q_num", 1)
            stem = q.get("stem", "")
            ans_class = f"ans-1"
            if marks_per_q == 2: ans_class = "ans-2"
            if marks_per_q == 3: ans_class = "ans-3"
            if marks_per_q >= 4: ans_class = "ans-5"

            questions_html += f"""
            <div class="question">
              <div class="q-row">
                <div class="q-num">Q{q_num}.</div>
                <div class="q-body">
                  {stem}
                  <div class="ans-space {ans_class}"></div>
                  <p style="text-align:right; font-size:10pt;">[{marks_per_q} Mark(s)]</p>
                </div>
                <div class="q-marks">[{marks_per_q} Marks]</div>
              </div>
            </div>
            <hr class="thin">
            """

            ak_label = q.get("ak_label", "")
            ak_answer = q.get("ak_answer", "")
            ak_marking = q.get("ak_marking", "")
            ak_accept = q.get("ak_accept", "")
            ak_error = q.get("ak_common_error", "")
            ak_ref = q.get("ak_ref", "")

            answer_key_html += f"""
            <div class="ak-q">
              <div class="ak-q-head">Q{q_num}. &nbsp; {ak_label} &nbsp; [{marks_per_q} Mark(s)]</div>
              {ak_answer}
              <div class="rubric">
                <strong>Marking:</strong> {ak_marking}<br>
                <strong>Accept:</strong> {ak_accept}<br>
                <strong>Common Error:</strong> {ak_error}
              </div>
              <p><em>Ref: {ak_ref}</em></p>
            </div>
            """

        answer_key_html += "</div>\n"

    section_summary_html = " &nbsp;|&nbsp; ".join(section_summaries)

    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: Template not found at {TEMPLATE_PATH}")
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    replacements = {
        "{{ CLASS }}": str(class_num),
        "{{ SUBJECT }}": str(subject),
        "{{ TOPICS }}": str(topics_inline),
        "{{ DATE }}": str(date_str),
        "{{ TIME }}": str(time_min),
        "{{ MARKS }}": str(total_marks),
        "{{ QUESTIONS_HTML }}": questions_html,
        "{{ SECTION_SUMMARY_HTML }}": section_summary_html,
        "{{ ANSWER_KEY_HTML }}": answer_key_html,
        "{{ MARKS_DISTRIBUTION_HTML }}": marks_distribution_html,
        "{{ TOTAL_QUESTIONS }}": str(total_questions)
    }

    for k, v in replacements.items():
        html = html.replace(k, v)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Successfully generated {os.path.basename(out_path)} in {os.path.basename(out_dir)}/")
    print(f"Full path: {out_path}")
    
    # Clean up the json file since it's no longer needed
    try:
        os.remove(json_path)
        print(f"Cleaned up {json_path}")
    except OSError as e:
        print(f"Failed to delete {json_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Test HTML from JSON")
    parser.add_argument("json_file", help="Path to input JSON file")
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"Error: {args.json_file} does not exist.")
        sys.exit(1)
        
    build_test(args.json_file)
