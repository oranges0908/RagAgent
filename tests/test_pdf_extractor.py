import struct
import zlib
from pathlib import Path

import pytest

from backend.core.pdf_extractor import PDFExtractor, PageSection

PDF_PATH = Path(__file__).parent / "pointer networks.pdf"


@pytest.fixture(scope="module")
def sections():
    extractor = PDFExtractor()
    return extractor.extract(PDF_PATH.read_bytes())


def test_section_count(sections):
    assert len(sections) >= 4, "Expected at least 4 sections (Body, Abstract, Introduction, ...)"


def test_section_types(sections):
    names = [s.section for s in sections]
    assert any("Abstract" in n for n in names)
    assert any("Introduction" in n for n in names)


def test_no_empty_sections(sections):
    for s in sections:
        assert len(s.text.strip()) > 0, f"Section '{s.section}' has empty text"


def test_total_text_length(sections):
    total = sum(len(s.text) for s in sections)
    assert total > 5000, "Total extracted text too short; likely extraction failure"


def test_section_is_dataclass(sections):
    for s in sections:
        assert isinstance(s, PageSection)
        assert isinstance(s.page_num, int)
        assert isinstance(s.section, str)
        assert isinstance(s.text, str)


def test_body_fallback_when_no_headings():
    """A plain-text-only PDF with no section headings should produce a single 'Body' section."""
    extractor = PDFExtractor()
    # Build a minimal valid single-page PDF with no headings
    pdf_bytes = _make_minimal_pdf("Just some text without any headings here.")
    result = extractor.extract(pdf_bytes)
    assert len(result) == 1
    assert result[0].section == "Body"
    assert "Just some text" in result[0].text


def _make_minimal_pdf(text: str) -> bytes:
    """Build the smallest valid PDF containing a single text string."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    return doc.tobytes()
