# Agents

## Project Overview

**mono-merge** is a Python-based font merging tool designed to combine different monospace fonts into a single unified font file.

## Technical Details

### Language
- Python

### Purpose
The project aims to merge different monospace fonts into one monospace font, specifically targeting:
- English characters
- CJK (Chinese, Japanese, Korean) characters

This ensures consistent monospace rendering across different character sets, which is essential for:
- Code editors
- Terminal applications
- Development environments
- Any application requiring uniform character width

### Key Libraries
- **fonttools**: The primary library used for font manipulation and merging operations
- **cu2qu**: Cubic-to-quadratic Bezier conversion for OTF to TTF conversion
- **Pillow**: Image rendering for font preview
- **PyYAML**: Configuration and debug output

### Font Format Support
The tool supports multiple font formats:
- **TTC (TrueType Collection)**: Multi-font container files, selectable by index
- **TTF (TrueType Font)**: Standard TrueType outline fonts
- **OTF (OpenType/CFF)**: PostScript-based outline fonts, automatically converted to TrueType

#### OTF Conversion Process
When an OTF (CFF-based) font is used as the CJK source:
1. CFF glyphs are extracted from the font
2. Cubic Bezier curves are converted to quadratic Bezier curves using Cu2QuPen
3. New glyf and loca tables are created for TrueType format
4. Font signature (sfntVersion) is changed from 'OTTO' to TrueType format
5. maxp table is updated with TrueType-specific fields
6. CFF table is removed

## Coding Standards

### Python Scripts
- For Python executable main scripts, must use `argparse` instead of `sys.argv` for command-line argument parsing

### Environment
- Always use the Python environment in `.venv` when running scripts.

### Version Control
- Version control of `cheatsheet.txt` will be managed by human. Do not manage its version control unless requested.

## Use Cases

- Creating custom monospace fonts for multilingual development
- Combining Western and Eastern character sets with consistent spacing
- Building fonts optimized for programming with CJK language support
- Converting OTF fonts to TTF while merging with Latin fonts

## Tools

- [monomerge.py](monomerge.py): Main font merging tool. Merges Latin and CJK fonts, automatically detecting half-width vs full-width characters and replacing half-width glyphs with scaled Latin glyphs. Supports TTC, TTF, and OTF input formats.
- [debug_font.py](debug_font.py): CLI inspector to print cmap membership, glyph metrics (width/LSB), glyph bounding boxes, and whether each glyph is simple or composite. Supports selecting TTC font index, custom character lists, and optional scaling simulation (`--scale`) to preview how glyph bounds change under em-size scaling.
- [font_preview.py](font_preview.py): Renders sample text to PNG and emits a YAML debug report. Supports TTC font index, custom font size, and a `--debug` flag that overlays text bounding boxes, per-character boxes, and baseline/ascender/descender guides for quick visual inspection.
