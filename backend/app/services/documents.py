"""Document ingestion: extract plain text from PDF / DOCX / TXT uploads.

Uploaded documents are UNTRUSTED content. We only ever read bytes and scan
text — never execute, render or act on anything inside. Failures raise
``IngestionError`` with messages safe to show a recruiter.
"""

from __future__ import annotations

import io
import re
import uuid
from pathlib import Path

from app.core.errors import IngestionError

#: Refuse absurd uploads early (10 MB is plenty for a resume).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
#: Cap on extracted text stored/processed (characters).
MAX_TEXT_CHARS = 200_000
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".text"}

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BLANK_LINES_RE = re.compile(r"\n{3,}")
_SPACES_RE = re.compile(r"[ \t]{2,}")


def extract_text(filename: str, data: bytes) -> str:
    """Extract clean plain text from an uploaded document.

    Raises ``IngestionError`` for unsupported, empty, protected or
    textless (e.g. scanned) documents.
    """
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise IngestionError(
            f"Unsupported file type '{suffix or 'unknown'}'. Upload a PDF, DOCX or TXT file."
        )
    if not data:
        raise IngestionError("The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise IngestionError(
            f"File is too large ({len(data) // (1024 * 1024)} MB). The limit is 10 MB."
        )

    if suffix == ".pdf":
        raw = _extract_pdf(data)
    elif suffix == ".docx":
        raw = _extract_docx(data)
    else:
        raw = _decode_text(data)

    text = sanitize_text(raw)
    if len(text.strip()) < 30:
        raise IngestionError(
            "Could not read meaningful text from this document. "
            "If it is a scanned PDF, export a text-based version and try again."
        )
    return text


def sanitize_text(raw: str) -> str:
    """Normalize whitespace/control characters and cap length."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = text.lstrip("\ufeff")
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _SPACES_RE.sub(" ", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()[:MAX_TEXT_CHARS]


def save_upload(filename: str, data: bytes, upload_dir: str) -> str:
    """Persist an upload under ``upload_dir`` with a collision-proof name.

    Returns the stored path. The original name is preserved (sanitized) after
    a short random prefix so parallel uploads cannot clash.
    """
    directory = Path(upload_dir)
    directory.mkdir(parents=True, exist_ok=True)

    original = Path(filename or "upload").name  # strip any path components
    safe_stem = (
        re.sub(r"[^A-Za-z0-9._ -]+", "_", original.rsplit(".", 1)[0])[:80].strip() or "upload"
    )
    suffix = Path(original).suffix.lower()
    stored_name = f"{uuid.uuid4().hex[:8]}_{safe_stem}{suffix}"
    path = directory / stored_name
    path.write_bytes(data)
    return str(path)


# ── Format readers ──────────────────────────────────────────────────────────


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise IngestionError("PDF support is not installed on this server.") from exc
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")  # some PDFs are "encrypted" with an empty password
            except Exception as exc:
                raise IngestionError("This PDF is password-protected.") from exc
        pages = [page.extract_text() or "" for page in reader.pages]
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError("Could not parse this PDF — the file may be corrupted.") from exc
    text = "\n".join(pages)
    if len(text.strip()) < 30:
        raise IngestionError(
            "This PDF contains no extractable text (it looks like a scan). "
            "Export a text-based PDF and try again."
        )
    return text


def _extract_docx(data: bytes) -> str:
    try:
        import docx
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise IngestionError("DOCX support is not installed on this server.") from exc
    try:
        document = docx.Document(io.BytesIO(data))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
    except Exception as exc:
        raise IngestionError("Could not parse this DOCX file — it may be corrupted.") from exc
    return "\n".join(parts)


def _decode_text(data: bytes) -> str:
    """Best-effort text decoding with BOM/heuristic detection (never guesses silently)."""
    import codecs

    if data.startswith(codecs.BOM_UTF8):
        return data.decode("utf-8-sig")
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # UTF-16 without BOM shows up as many interleaved NUL bytes.
    sample = data[:4096]
    if len(sample) >= 8 and (
        sample[1::2].count(0) > len(sample) // 8 or sample[0::2].count(0) > len(sample) // 8
    ):
        try:
            return data.decode("utf-16-le" if data[1] == 0 else "utf-16-be")
        except UnicodeDecodeError:
            pass
    # Latin-1 decodes any byte sequence; the right last resort for old files.
    return data.decode("latin-1")
