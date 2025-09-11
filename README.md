# BibTeX Extraction from PDFs (Python)

Generate a complete `articles.bib` file from a folder of PDFs — locally, reproducibly, and without manual typing.  
The script scans each PDF, pulls embedded metadata when available, falls back to first-page text heuristics (title/author/year/DOI), and writes a valid BibTeX entry per file.

---

## Features

- **Local & offline**: no external APIs required.
- **Smart heuristics**: guesses title, authors, year from first-page text when metadata is missing.
- **DOI detection**: recognizes DOI patterns and adds the canonical `https://doi.org/...` URL.
- **Deterministic keys**: stable BibTeX keys based on author–year–title.
- **Auditable output**: always generates usable entries (`@article` if DOI present, else `@misc`) with a `file` link to the local PDF.

---

## Repository Structure

```
.
├─ articles/              # Put your PDFs here (input)
├─ articles.bib           # Generated bibliography (output)
├─ main_bibtex_v1.py      # Run this script
└─ README.md              # You are here
```

---

## Requirements

- Python **3.9+**
- OS: Windows / macOS / Linux

### Python packages

Minimal (recommended for this project):
```bash
pip install pypdf langchain-community
```

Optional (if you plan to integrate with an existing LangChain/RAG stack):
```bash
pip install langchain langchain-community langchain-huggingface langchain-chroma chromadb \
            sentence-transformers transformers torch accelerate
```

---

## Quick Start

1. **Clone** the project (or copy `main_bibtex_v1.py` into your working directory).
2. **Create the input folder** and drop PDFs there:
   ```bash
   mkdir articles
   # copy your .pdf files into ./articles
   ```
3. **Install dependencies**:
   ```bash
   pip install pypdf langchain-community
   ```
4. **Run**:
   ```bash
   python main_bibtex_v1.py
   ```
5. **Result**:
   - A new **`articles.bib`** file is created (or overwritten) in the project root.
   - The console prints a line per processed PDF:
     ```
     [BIB] my_paper.pdf -> Interesting Title (2021)
     Saved 10 entries to /path/to/articles.bib
     ```

---

## How It Works (High-Level)

1. **Enumerate PDFs**  
   Iterates over `./articles/*.pdf` in alphabetical order.

2. **Extract metadata (best-effort)**  
   - **Embedded PDF metadata** via `pypdf.PdfReader.metadata`: `title`, `author`, `creation_date`.
   - **Heuristics from first page** via `PyPDFLoader`:
     - **DOI** (regex `10.\d{4,9}/...`)
     - **Title** candidates from first non-empty lines
     - **Authors** line (commas / “and” / semicolons)
     - **Year** (`19xx`/`20xx`) sanity-checked (≤ current year)

3. **Fallbacks**  
   If still missing:
   - `title` ← sanitized filename
   - `authors` ← `["Unknown Author"]`
   - `year` ← `UnknownYear`

4. **Format BibTeX**  
   - With DOI → `@article{...}` including `title`, `author`, `year`, `doi`, `url`, `file`
   - Without DOI → `@misc{...}` including `title`, `author`, `year`, `howpublished`, `note`, `file`

5. **Write output**  
   Appends all entries into **`articles.bib`**.

---

## Configuration & Customization

Open `main_bibtex_v1.py` and adjust:

- **Input/Output paths**
  ```python
  PDF_DIR = Path("articles")
  OUT_BIB = Path("articles.bib")
  ```

- **Regex patterns**
  ```python
  DOI_RE  = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
  YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
  ```

- **Key generation**  
  Update `make_bibtex_key(...)` to change key style (e.g., include full first author, journal tag, etc.).

- **Heuristics**  
  In `extract_pdf_metadata(...)` you can refine:
  - How “title-looking” lines are chosen
  - How authors are split/normalized
  - Year filters (e.g., restrict to 1950–current year)

---

## Tips for Best Results

- **Prefer publisher PDFs**: They often have cleaner metadata and first-page structure.
- **Stable filenames**: If metadata is poor, filenames are used for fallback titles.
- **Manual pass** (optional): After generation, quickly scan `articles.bib` for any `Unknown...` fields to tidy edge cases.

---

## Advanced Usage

- **Run from anywhere**:
  ```bash
  python /abs/path/to/main_bibtex_v1.py
  ```
- **Integrate into Makefile**:
  ```makefile
  bib:
      python main_bibtex_v1.py
  build: bib
      latexmk -pdf main.tex
  ```
- **Pre-commit hook** (pseudo):
  ```bash
  # .git/hooks/pre-commit
  python main_bibtex_v1.py
  git add articles.bib
  ```

- **Use without LangChain**:  
  Replace `PyPDFLoader` with `PdfReader.pages[0].extract_text()` for a zero-extra-deps version.

---

## Troubleshooting

- **“ModuleNotFoundError: No module named 'pypdf'”**  
  Install dependencies in the same interpreter you’re using to run the script:
  ```bash
  pip install pypdf langchain-community
  ```

- **Empty/incorrect metadata**  
  Some PDFs are scanned or poorly tagged. The script falls back to heuristics, but quality can vary. Consider a quick manual edit in `articles.bib`.

- **Unicode/accents in keys**  
  Keys are slugified; if you prefer diacritics preserved elsewhere, adjust `_slug(...)` or add transliteration as needed.

- **Spyder / IDE using wrong environment**  
  Make sure Spyder’s **Python interpreter** points to the environment where you installed the deps (install `spyder-kernels` in that env and select it in `Tools → Preferences → Python interpreter`).

---

## Security & Privacy

- All processing is **local**.  
- No network calls, analytics, or external services are used by default.

---

## Roadmap (Ideas)

- Crossref/DOI enrichment (optional online mode)  
- Journal/conference detection  
- Config file for per-field rules and custom templates  
- Unit tests on a small sample corpus

---

## License

Choose a license that matches your goals (e.g., MIT/Apache-2.0).  
Add a `LICENSE` file in the repo root.

---

## Acknowledgements

- Built with **pypdf** and a simple first-page text heuristic.  
- Optional **langchain-community** `PyPDFLoader` for convenience.

---

## Citation

If this tool helps your workflow, a quick mention or a star ⭐ on the repo is appreciated!
