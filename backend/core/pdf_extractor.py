import re
from dataclasses import dataclass

import fitz  # pymupdf

# Matches common academic section headings that appear on their own line
_SECTION_RE = re.compile(
    r"^(Abstract|Introduction|Related Work|Background|Model|Method|Experiment|"
    r"Result|Discussion|Conclusion|Training|Evaluation)",
    re.IGNORECASE,
)
# A heading line should be short (not a sentence starting with one of those words)
_MAX_HEADING_LEN = 60


@dataclass
class PageSection:
    page_num: int   # page index (0-based) where this section starts
    section: str    # section name, e.g. "Abstract", "Introduction", "Body"
    text: str       # full text of this section


class PDFExtractor:
    def extract(self, file_bytes: bytes) -> list[PageSection]:
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        sections: list[PageSection] = []
        current_section = "Body"
        current_page = 0
        current_lines: list[str] = []
        found_named = False

        for page_num in range(doc.page_count):
            page_text = doc[page_num].get_text()
            for line in page_text.splitlines():
                stripped = line.strip()
                if stripped and _SECTION_RE.match(stripped) and len(stripped) <= _MAX_HEADING_LEN:
                    # Flush accumulated text into current section
                    text = "\n".join(current_lines).strip()
                    if text:
                        sections.append(PageSection(
                            page_num=current_page,
                            section=current_section,
                            text=text,
                        ))
                    current_section = stripped
                    current_page = page_num
                    current_lines = []
                    found_named = True
                else:
                    current_lines.append(line)

        # Flush the last section
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(PageSection(
                page_num=current_page,
                section=current_section,
                text=text,
            ))

        # If no headings were found, collapse everything into one "Body" section
        if not found_named:
            all_text = "\n".join(s.text for s in sections).strip()
            if all_text:
                return [PageSection(page_num=0, section="Body", text=all_text)]
            return []

        return sections
