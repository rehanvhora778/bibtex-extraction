## pip install pypdf langchain-community

# === BibTeX generation for all PDFs in `articles/` ===
import re
import unicodedata
from pathlib import Path
from datetime import datetime

from pypdf import PdfReader
from langchain_community.document_loaders import PyPDFLoader

PDF_DIR = Path("articles")
OUT_BIB = Path("articles.bib")

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

def _slug(s: str, maxlen: int = 40) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "", s)
    return s[:maxlen] or "ref"

def _clean_line(l: str) -> str:
    l = l.strip()
    l = re.sub(r"\s+", " ", l)
    return l

def _first_nonempty_lines(text: str, k: int = 8):
    lines = [_clean_line(x) for x in text.splitlines()]
    return [x for x in lines if x][:k]

def extract_pdf_metadata(pdf_path: Path):
    meta = {"title": None, "authors": None, "year": None, "doi": None, "url": None}
    # 1) Embedded PDF metadata
    try:
        reader = PdfReader(str(pdf_path))
        info = reader.metadata or {}
        if getattr(info, "title", None):
            meta["title"] = info.title.strip()
        if getattr(info, "author", None):
            # split on ; or , if needed
            auth = info.author.strip()
            if ";" in auth:
                meta["authors"] = [a.strip() for a in auth.split(";") if a.strip()]
            elif "," in auth and " and " not in auth.lower():
                # might be "Last, First, Last, First"
                parts = [p.strip() for p in auth.split(",")]
                # group pairs if looks like "Last, First, Last, First"
                if len(parts) % 2 == 0:
                    meta["authors"] = [", ".join(parts[i:i+2]) for i in range(0, len(parts), 2)]
                else:
                    meta["authors"] = [auth]
            else:
                meta["authors"] = [x.strip() for x in re.split(r"\band\b|;", auth) if x.strip()]
        # Creation date like D:YYYYMMDD...
        cdate = getattr(info, "creation_date", None) or getattr(info, "CreationDate", None)
        if cdate:
            m = re.search(r"(19|20)\d{2}", str(cdate))
            if m:
                meta["year"] = m.group(0)
    except Exception:
        pass

    # 2) Heuristics from the first page text
    try:
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        if pages:
            first_text = pages[0].page_content or ""
            # DOI
            doi_match = DOI_RE.search(first_text)
            if doi_match:
                meta["doi"] = doi_match.group(0)
                meta["url"] = f"https://doi.org/{meta['doi']}"
            # Title guess: first 1–3 non-empty lines that look title-ish
            lines = _first_nonempty_lines(first_text, k=10)
            if not meta["title"] and lines:
                # skip obvious headers like "Original Article", "Review", journal headings
                candidates = [l for l in lines if len(l) > 8 and not re.search(r"(journal|volume|issue|review|original|www\.|http)", l, re.I)]
                if candidates:
                    meta["title"] = candidates[0]
            # Year guess if missing
            if not meta["year"]:
                ym = YEAR_RE.findall(first_text)
                if ym:
                    # pick the first reasonable year
                    for yr in re.findall(r"(19|20)\d{2}", first_text):
                        y = int(yr)
                        if 1900 <= y <= datetime.now().year:
                            meta["year"] = str(y)
                            break
            # Crude authors guess if missing (comma-separated names line)
            if not meta["authors"]:
                # look for a line with many commas and capitalized words
                author_line = None
                for l in lines[:6]:
                    if (l.count(",") >= 2 or " and " in l.lower()) and len(l.split()) <= 25:
                        author_line = l
                        break
                if author_line:
                    parts = re.split(r";| and |,(?=\s*[A-Z])", author_line)
                    parts = [p.strip() for p in parts if len(p.split()) <= 6 and len(p) >= 3]
                    if parts:
                        meta["authors"] = parts
    except Exception:
        pass

    # Defaults if still missing
    if not meta["title"]:
        meta["title"] = pdf_path.stem.replace("_", " ").strip() or "Unknown Title"
    if not meta["authors"]:
        meta["authors"] = ["Unknown Author"]
    if not meta["year"]:
        meta["year"] = "UnknownYear"

    return meta

def make_bibtex_key(authors, year, title):
    first_author = authors[0]
    # try "Last" from "Last, First" or last token
    last_name = first_author.split(",")[0].split()[-1]
    return _slug(last_name) + year + _slug(title, 20)

def to_bibtex(entry, pdf_path: Path):
    authors_bib = " and ".join(entry["authors"])
    key = make_bibtex_key(entry["authors"], entry["year"], entry["title"])
    # Prefer @article if DOI was found; else @misc
    if entry.get("doi"):
        tpl = (
f"@article{{{key},\n"
f"  title   = {{{entry['title']}}},\n"
f"  author  = {{{authors_bib}}},\n"
f"  year    = {{{entry['year']}}},\n"
f"  doi     = {{{entry['doi']}}},\n"
f"  url     = {{{entry.get('url','')}}},\n"
f"  file    = {{{pdf_path.as_posix()}}}\n"
f"}}\n"
        )
    else:
        tpl = (
f"@misc{{{key},\n"
f"  title   = {{{entry['title']}}},\n"
f"  author  = {{{authors_bib}}},\n"
f"  year    = {{{entry['year']}}},\n"
f"  howpublished = {{PDF}},\n"
f"  note    = {{Local file}},\n"
f"  file    = {{{pdf_path.as_posix()}}}\n"
f"}}\n"
        )
    return tpl

def build_bib_for_folder(pdf_dir: Path, out_bib: Path):
    bib_entries = []
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        meta = extract_pdf_metadata(pdf)
        bib = to_bibtex(meta, pdf)
        bib_entries.append(bib)
        print(f"[BIB] {pdf.name} -> {meta['title']} ({meta['year']})")
    out_bib.write_text("\n".join(bib_entries), encoding="utf-8")
    print(f"\nSaved {len(bib_entries)} entries to: {out_bib.resolve()}")

# Call it
build_bib_for_folder(PDF_DIR, OUT_BIB)
