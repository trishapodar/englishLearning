# tools/ — CBSE Weekly Test Generator

A two-step CLI pipeline that generates print-ready CBSE weekly test papers
(with answer key and marking scheme) using a token-efficient JSON workflow.

**Step 1 — `generate_test.py`**: Produces a prompt for the AI to generate a lightweight JSON file with only questions, marks, and rubrics.  
**Step 2 — `build_test.py`**: Merges the AI-generated JSON into the master HTML template and saves the final test to the correct subject folder — at zero additional token cost.

---

## Setup

### 1. Install dependencies
```bash
cd tools/
pip3 install -r requirements.txt
```

### 2. Set your API key
```bash
# Copy the example file
cp .env.example .env

# Edit .env and paste your key
# Get a free key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_key_here
```

---

## Workflow

### Step 1 — Generate the AI Prompt (dry-run)
```bash
python3 tools/generate_test.py \
  --class   <class_number> \
  --subject <subject_name> \
  --topics  <"Topic 1"> ["Topic 2"] \
  [--time   <minutes>]   \  # default: 90
  [--marks  <total>]        # default: 40
  --dry-run
```

Copy the printed prompt, send it to the AI (e.g. in this chat), and ask it to act on the prompt. The AI will return a raw JSON file — save it as `temp.json` in the project root.

### Step 2 — Build the Final Test
```bash
python3 tools/build_test.py temp.json
```

This will:
- Parse the JSON and inject all questions and the answer key into the master HTML template.
- Auto-route the output to the correct subject folder (`math_tests/`, `science_tests/`, etc.).
- Delete `temp.json` automatically after the HTML is generated.

---

## Examples

### Class 9 Mathematics (dry-run then build)
```bash
# Step 1: generate the prompt
python3 tools/generate_test.py --class 9 --subject Mathematics --topics "Coordinate Geometry" --time 90 --marks 40 --dry-run

# Act on the prompt in the AI chat → save output as temp.json

# Step 2: build the HTML
python3 tools/build_test.py temp.json
```

### Class 4 Science
```bash
python3 tools/generate_test.py --class 4 --subject Science --topics "Plants" --marks 20 --dry-run
# → get JSON from AI → save as temp.json
python3 tools/build_test.py temp.json
```

### Class 10 Science (3 topics)
```bash
python3 tools/generate_test.py --class 10 --subject Science --topics "Light — Reflection" "Human Eye" "Glass Prism and Dispersion" --marks 30 --dry-run
```

---

## Output

`build_test.py` saves a timestamped HTML file automatically in the subject folder:

| Subject | Output Folder |
|---|---|
| Mathematics | `math_tests/` |
| Science | `science_tests/` |
| Any other | `<subject>_tests/` |

Example filename: `science_tests/class4_science_plants_20260416.html`

Open in any browser to preview, or convert to PDF:
```bash
# Browser → Print → Save as PDF
```

---

## Supported Total Marks

The section distribution in the prompt auto-adjusts for common mark targets:

| `--marks` | Sec A (1m) | Sec B (2m) | Sec C (3m) | Sec D (5m) | Total Qs |
|-----------|-----------|-----------|-----------|-----------|----------|
| 20        | 4         | 2         | 2         | 1         | 9        |
| 30        | 4         | 4         | 4         | 2         | 14       |
| **40**    | **4**     | **4**     | **6**     | **2**     | **16**   |
| 50        | 6         | 6         | 6         | 2         | 20       |
| 80        | 20        | 6         | 8         | 3         | 37       |

---

## Available Gemini Models

When using `generate_test.py` with direct API mode (without `--dry-run`):

| Model | Speed | Quality | Use for |
|-------|-------|---------|---------|
| `gemini-2.0-flash` | ⚡ Fast | Good | Daily use (default) |
| `gemini-2.5-pro` | Slower | Best | Final / important papers |

Pass with `--model gemini-2.5-pro`.

---

## File Structure

```
tools/
├── generate_test.py          ← Step 1: Generates the structured AI prompt
├── build_test.py             ← Step 2: Merges JSON into HTML template
├── requirements.txt          ← Python dependencies
├── .env                      ← Your API key (gitignored)
├── .env.example              ← Template to copy
├── .gitignore                ← Keeps .env out of git
└── README.md                 ← This file

tests/templates/
└── weekly_test_template.html ← Master HTML/CSS template (single source of truth)
```

---

## How It Saves Tokens

The old workflow asked the AI to generate a full HTML document (~400+ lines of CSS + HTML boilerplate on every single call). The new workflow asks the AI only for the raw data (questions, marks, rubrics) in a compact JSON format, which is then merged locally. This saves approximately **60–70% of completion tokens** per test generated.
