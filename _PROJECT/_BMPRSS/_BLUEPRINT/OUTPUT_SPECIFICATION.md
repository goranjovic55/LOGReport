
---

### 6. Output Specification
**Path:** `_BMPRSS/_BLUEPRINT/OUTPUT_SPECIFICATION.md`
```markdown
# Output Format Standards

## PDF Requirements
- **Page Size**: A4 portrait
- **Margins**: 20mm all sides
- **Font**: DejaVu Sans Mono 10pt
- **Features**:
  - Cover page with metadata
  - Table of contents
  - File section dividers
  - Page numbers

## DOCX Requirements
- **Styles**:
  - Code style for log content
  - Heading styles for file sections
- **Features**:
  - Hyperlinked TOC
  - Page breaks between files
  - Preserved original spacing

## Sample Configuration
```python
PDF_SETTINGS = {
    "page_size": "A4",
    "margin_left": 20,
    "margin_right": 20,
    "default_font": "DejaVuSansMono",
    "header_font_size": 12
}