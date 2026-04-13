# generate_test.py — CBSE Weekly Test Generator

A command-line tool that generates a print-ready, DOCX-compatible CBSE  
weekly test paper (with answer key and marking scheme) by calling the  
Gemini API with a structured prompt.

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

## Usage

```bash
python3 generate_test.py \
  --class   <class_number> \
  --subject <subject_name> \
  --topics  <"Topic 1"> <"Topic 2"> [<"Topic 3">] \
  [--time   <minutes>]   \  # default: 90
  [--marks  <total>]     \  # default: 40
  [--output <directory>] \  # default: ./generated_tests/
  [--model  <model_name>]   # default: gemini-2.0-flash
```

---

## Examples

### Class 9 Mathematics
```bash
python3 generate_test.py \
  --class 9 \
  --subject Mathematics \
  --topics "Coordinate Geometry" "Congruent Triangles" \
  --time 90 --marks 40 \
  --output ../math_tests/
```

### Class 10 Science (3 topics)
```bash
python3 generate_test.py \
  --class 10 \
  --subject Science \
  --topics "Light — Reflection" "Human Eye" "Glass Prism and Dispersion" \
  --marks 30 \
  --output ../science_tests/
```

### Class 9 English Grammar
```bash
python3 generate_test.py \
  --class 9 \
  --subject English \
  --topics "Tenses" "Subject-Verb Agreement" \
  --marks 40 \
  --output ../english_tests/
```

### Preview prompt without calling the API (free, instant)
```bash
python3 generate_test.py \
  --class 9 \
  --subject Mathematics \
  --topics "Polynomials" "Linear Equations" \
  --dry-run
```

---

## Output

The tool saves a timestamped HTML file:
```
../math_tests/class9_mathematics_coordinate_congruent_20260409_1945.html
```

Open in any browser to preview, or convert to DOCX:
```bash
# Using pandoc
pandoc output_file.html -o output_file.docx

# Or: Browser → Print → Save as PDF
```

---

## Supported Total Marks

The section distribution auto-adjusts for common mark targets:

| `--marks` | Sec A (1m) | Sec B (2m) | Sec C (3m) | Sec D (5m) | Total Qs |
|-----------|-----------|-----------|-----------|-----------|----------|
| 20        | 4         | 2         | 2         | 1         | 9        |
| 30        | 4         | 4         | 4         | 2         | 14       |
| **40**    | **4**     | **4**     | **6**     | **2**     | **16**   |
| 50        | 6         | 6         | 6         | 2         | 20       |
| 80        | 20        | 6         | 8         | 3         | 37       |

---

## Available Gemini Models

| Model | Speed | Quality | Use for |
|-------|-------|---------|---------|
| `gemini-2.0-flash` | ⚡ Fast | Good | Daily use (default) |
| `gemini-2.5-pro` | Slower | Best | Final / important papers |

Pass with `--model gemini-2.5-pro`.

---

## File Structure

```
tools/
├── generate_test.py    ← Main CLI script
├── requirements.txt    ← Python dependencies
├── .env                ← Your API key (gitignored)
├── .env.example        ← Template to copy
├── .gitignore          ← Keeps .env and outputs out of git
└── README.md           ← This file
```
