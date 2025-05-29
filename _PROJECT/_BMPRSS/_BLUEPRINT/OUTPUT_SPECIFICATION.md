
---

### 6. Output Specification
**Path:** `_BMPRSS/_BLUEPRINT/OUTPUT_SPECIFICATION.md`
```markdown
# Output Format Standards

## PDF Requirements
- **Page Size**: A4 portrait
- **Margins**: 20mm all sides
- **Font**: Courier 10pt (monospaced)
- **Features**:
  - Cover page with metadata
  - Table of contents
  - File section dividers
  - Page numbers
  - Preserved whitespace using Preformatted text blocks

## DOCX Requirements
- **Styles**:
  - Body: Courier New 10pt (monospaced)
  - Heading styles for file sections
- **Features**:
  - Hyperlinked TOC
  - Page breaks between files
  - Preserved whitespace using combined paragraphs
  - Newline-preserving formatting

## Whitespace Preservation Standard
- All original whitespace characters (spaces, tabs) must be preserved exactly
- Empty lines should be maintained in output
- Output generators must use monospaced fonts to maintain column alignment
- For PDFs: Use Preformatted text blocks to prevent line wrapping
- For DOCX: Combine file content into single paragraphs with \n separators

## Output Standards v2.1

## New Formatting Features
| Element          | Style                           |
|------------------|--------------------------------|
| Filtered Header  | "(Filtered: First 50 lines)"   |
| Range Display    | "Lines 100-150"                |
| Truncated Alert  | "[...truncated...]" footer     |

## Sample Configuration
```python
PDF_SETTINGS = {
    "page_size": "A4",
    "margin_left": 20,
    "margin_right": 20,
    "default_font": "DejaVuSansMono",
    "header_font_size": 12
}