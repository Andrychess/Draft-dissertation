"""Extract plain text from uploaded lecture files (PDF, DOCX)."""

from pathlib import Path


def load_lecture_text(file_path: str, max_chars: int = 8000) -> str:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return ""

    suffix = path.suffix.lower()
    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
        except Exception:
            return ""
    elif suffix in (".docx", ".doc"):
        try:
            from docx import Document

            doc = Document(str(path))
            text = "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception:
            return ""
    else:
        return ""

    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."
