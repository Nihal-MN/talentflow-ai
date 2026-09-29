"""Document ingestion unit tests: PDF/DOCX/TXT extraction + sanitization."""

from __future__ import annotations

import pytest
from app.core.errors import IngestionError
from app.services.documents import extract_text, sanitize_text
from tests.conftest import resume_path


def test_extract_text_from_pdf():
    text = extract_text(
        "amira_haddad.resume.pdf", resume_path("amira_haddad.resume.pdf").read_bytes()
    )
    assert "Amira Haddad" in text
    assert "Cedar Freight" in text
    assert "FastAPI" in text


def test_extract_text_from_docx():
    text = extract_text(
        "daniel_okafor.resume.docx", resume_path("daniel_okafor.resume.docx").read_bytes()
    )
    assert "Daniel Okafor" in text
    assert "Paystream Africa" in text


def test_extract_text_from_txt_handles_encodings():
    text = extract_text(
        "note.txt", "Café résumé — naïve text used for encoding checks".encode("utf-16")
    )
    assert "Café" in text

    latin = "München Straße - brief text used for encoding checks".encode("latin-1")
    assert "München" in extract_text("note.txt", latin)


def test_unsupported_extension_is_rejected():
    with pytest.raises(IngestionError, match="Unsupported file type"):
        extract_text("image.png", b"\x89PNG\r\n")


def test_empty_and_tiny_documents_are_rejected():
    with pytest.raises(IngestionError, match="empty"):
        extract_text("a.txt", b"")
    with pytest.raises(IngestionError, match="meaningful text"):
        extract_text("a.txt", b"hi")


def test_corrupt_pdf_gives_friendly_error():
    with pytest.raises(IngestionError, match="PDF"):
        extract_text("broken.pdf", b"%PDF-1.4 this is not really a pdf")


def test_sanitize_strips_control_chars_and_collapses_blank_lines():
    dirty = "Line one\x00\x07  with\tcontrols\n\n\n\n\nLine two\u00a0end"
    clean = sanitize_text(dirty)
    assert "\x00" not in clean and "\x07" not in clean
    assert "\n\n\n" not in clean
    assert "Line one" in clean and "Line two" in clean


def test_extract_text_caps_length():
    huge = ("Hello world. " * 20_000).encode()
    text = extract_text("big.txt", huge)
    assert len(text) <= 200_000
