# mono-merge

A Python tool for merging different monospace fonts into a single unified monospace font, supporting both English and CJK (Chinese, Japanese, Korean) characters.

## Overview

mono-merge allows you to combine multiple monospace fonts to create a custom font that works seamlessly across different character sets. This is particularly useful for developers who want consistent monospace rendering across English and CJK characters in their code editors and terminals.

## Features

- Merge multiple monospace fonts into one
- Support for English and CJK character sets
- Maintains monospace properties across all glyphs
- Multiple font format support:
  - **TTC** (TrueType Collection)
  - **TTF** (TrueType Font)
  - **OTF** (OpenType/CFF) - automatically converted to TrueType
- Automatic font format conversion (OTF to TTF)
- Smart glyph replacement based on character width detection
- Built with Python and fonttools library

## Requirements

- Python 3.x
- fonttools >= 4.38.0
- Pillow >= 9.0.0
- PyYAML >= 6.0
- cu2qu >= 1.6.7 (for OTF support)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Merge with default fonts (Consola + NotoSansMonoCJKhk)
python3 monomerge.py

# Specify custom fonts
python3 monomerge.py -l input/cour.ttf -c input/mingliu.ttc

# Set custom output name
python3 monomerge.py -n MyCustomFont -o output/custom.ttf
```

### Command-Line Options

- `-l, --latin-font PATH` - Path to the Latin/English font file (default: input/consola.ttf)
- `-c, --cjk-font PATH` - Path to the CJK font file (supports TTC, TTF, and OTF formats)
- `-n, --name NAME` - Output font name (for font metadata)
- `-o, --output PATH` - Path for the output merged font
- `-i, --cjk-index N` - Font index in TTC file (0-based, default: 0). Only applies to TTC files
- `--char CHARS` - Specific characters to include (for debugging/testing)

### Examples

```bash
# Use OTF CJK font with custom Latin font
python3 monomerge.py -l input/consola.ttf -c input/NotoSansMonoCJKhk-Regular.otf

# Use specific TTC font index
python3 monomerge.py -c input/mingliu.ttc -i 0

# Test with specific characters only
python3 monomerge.py --char "你好World123"
```

## Dependencies

- [fonttools](https://github.com/fonttools/fonttools) - Library for manipulating fonts

## License

WTFPL (Do What The F*** You Want To Public License)

## CodeCJK?

[CodeCJK.md](CodeCJK.md)

