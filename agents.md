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
