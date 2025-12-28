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

## Coding Standards

### Python Scripts
- For Python executable main scripts, must use `argparse` instead of `sys.argv` for command-line argument parsing

## Use Cases

- Creating custom monospace fonts for multilingual development
- Combining Western and Eastern character sets with consistent spacing
- Building fonts optimized for programming with CJK language support

## Tools

- [debug_font.py](debug_font.py): CLI inspector to print cmap membership, glyph metrics (width/LSB), glyph bounding boxes, and whether each glyph is simple or composite. Supports selecting TTC font index, custom character lists, and optional scaling simulation (`--scale`) to preview how glyph bounds change under em-size scaling.
- [font_preview.py](font_preview.py): Renders sample text to PNG and emits a YAML debug report. Supports TTC font index, custom font size, and a `--debug` flag that overlays text bounding boxes, per-character boxes, and baseline/ascender/descender guides for quick visual inspection.
