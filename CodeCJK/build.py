#!/usr/bin/env python3
"""
CodeCJK Font Build Script

This script builds the CodeCJK font by:
1. Downloading required font files
2. Scaling and shifting the CJK font to match the Latin font
3. Merging the fonts together
4. Creating variant fonts with different metadata

The script can be run from any folder and works on both Linux and Windows.
Output and tmp folders are created in the working directory.
"""

import argparse
import os
import shutil

from _func import * # just import all helper functions

OUTPUT_FONT_NAME = "CodeCJK"
OUTPUT_FONT_VERSION = "005"
OUTPUT_FONT_FULL_NAME = f"{OUTPUT_FONT_NAME}{OUTPUT_FONT_VERSION}"

SRC_FONT_LIST = [
    {
        "id": "base",
        "type": "download_zip",
        "zip_url": "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip",
        "ttf_path_in_zip": "ttf/FiraCode-Regular.ttf",
        "ttf_filename": "FiraCode-Regular.ttf",
        "ttf_md5": "a09618fdaaa2aef4b7b45e26b7267763",
    },
    {
        "id": "patch0",
        "type": "ttf",
        "ttf_url": "https://github.com/googlefonts/Inconsolata/raw/refs/heads/main/fonts/ttf/Inconsolata-Regular.ttf",
        "ttf_filename": "Inconsolata-Regular.ttf",
        "ttf_md5": "6acebfd97d8edc5226a384f77c613398",
    },
    {
        "id": "cjk",
        "type": "ttf",
        "ttf_url": "https://github.com/notofonts/noto-cjk/raw/refs/heads/main/Sans/Variable/TTF/Mono/NotoSansMonoCJKhk-VF.ttf",
        "ttf_filename": "NotoSansMonoCJKhk-VF.ttf",
        "ttf_md5": "ffde7dc37f0754c486b1cc5486a7ae93",
    },
]


parser = argparse.ArgumentParser(description='Build CodeCJK font')
parser.add_argument('--clean', action='store_true', help='Clean output and tmp folders before building')
args = parser.parse_args()

if args.clean:
    print("Cleaning output and tmp folders...")
    if os.path.exists("tmp"):
        shutil.rmtree("tmp")
    if os.path.exists("output"):
        shutil.rmtree("output")
    print("Cleaned.")

# Get datetime string
YYYYMMDDHHMMSS = get_datetime_string()
print(f"Current datetime: {YYYYMMDDHHMMSS}")

# Get script and project directories
script_dir = get_script_dir()
project_root = get_project_root()
print(f"Script directory: {script_dir}")
print(f"Project root directory: {project_root}")

# Create folders
"""Create tmp and output folders in the working directory."""
os.makedirs("tmp", exist_ok=True)
os.makedirs("output", exist_ok=True)
print("Created tmp and output folders")

# Download and prepare fonts (includes MD5 verification)
download_fonts(SRC_FONT_LIST)

# Set up Python environment
setup_python_environment()

# Dump input font char CSV
print("Dumping input font char CSV...")
py(
    "ttf/dump_char_csv.py",
    "tmp/base.ttf",
    "tmp/base.char.csv"
)
py(
    "ttf/dump_char_csv.py",
    "tmp/patch0.ttf",
    "tmp/patch0.char.csv"
)
py(
    "ttf/dump_char_csv.py",
    "tmp/cjk.ttf",
    "tmp/cjk.char.csv"
)

# Get the advance_width of char O
print("Getting advance width of character 'O'...")
base_half_advance_width = py(
    "utils/csv_query.py",
    "tmp/base.char.csv",
    "codepoint_dec", "79",
    "advance_width"
)
cjk_half_advance_width = py(
    "utils/csv_query.py",
    "tmp/cjk.char.csv",
    "codepoint_dec", "79",
    "advance_width"
)
print(f"Base half advance width: {base_half_advance_width}")
print(f"CJK half advance width: {cjk_half_advance_width}")

# Get ASCII chars from base font
print("Getting ASCII characters from base font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/base.char.csv",
    "ascii",
    "tmp/base.ascii.char.csv"
)

# Get big chars from base font
print("Getting big characters from base font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/base.char.csv",
    "upper,number",
    "tmp/base.big.char.csv"
)

## Scale patch0 font to match base font

print("Scaling patch0 font to match base font...")
patch0_half_advance_width = py(
    "utils/csv_query.py",
    "tmp/patch0.char.csv",
    "codepoint_dec", "79",
    "advance_width"
)
print(f"Patch0 half advance width: {patch0_half_advance_width}")

# Get big chars from patch0 font
print("Getting big characters from patch0 font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/patch0.char.csv",
    "upper,number",
    "tmp/patch0.big.char.csv"
)

## Scale CJK font to match base font

# Calculate CJK scale factor
cjk_scale_factor = float(base_half_advance_width) / float(cjk_half_advance_width)
print(f"Scale factor: {cjk_scale_factor}")

# Scale CJK font
print("Scaling CJK font...")
py(
    "ttf/scale_ttf.py",
    "tmp/cjk.ttf",
    str(cjk_scale_factor),
    "tmp/cjk-Scaled.ttf"
)

# Dump scaled font char CSV
print("Dumping scaled font char CSV...")
py(
    "ttf/dump_char_csv.py",
    "tmp/cjk-Scaled.ttf",
    "tmp/cjk-Scaled.char.csv"
)

# Get common CJK chars from scaled CJK font
print("Getting common CJK characters from scaled CJK font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/cjk-Scaled.char.csv",
    "common_cjk",
    "tmp/cjk-Scaled.common_cjk.char.csv"
)

# Calculate shift y offset
print("Calculating shift Y offset...")
py(
    "ttf/cal_shift_y.py",
    "tmp/base.big.char.csv",
    "tmp/cjk-Scaled.common_cjk.char.csv",
    "tmp/cjk-Scaled.shift_y_offset.yaml"
)

# Read shift_y value from YAML using venv Python
shift_y_value = py(
    "utils/yq.py",
    "tmp/cjk-Scaled.shift_y_offset.yaml",
    "shift_y"
)
print(f"Shift Y value: {shift_y_value}")

# Apply shift y to scaled CJK font
print("Applying shift Y to scaled CJK font...")
py(
    "ttf/font_shift_y.py",
    "tmp/cjk-Scaled.ttf",
    str(shift_y_value),
    "tmp/cjk-Scaled-Shifted.ttf"
)

# Dump shifted font char CSV
print("Dumping shifted font char CSV...")
py(
    "ttf/dump_char_csv.py",
    "tmp/cjk-Scaled-Shifted.ttf",
    "tmp/cjk-Scaled-Shifted.char.csv"
)

# Pick chars from base font and shifted scaled CJK font
print("Picking characters from base font and shifted scaled CJK font...")
py(
    "ttf/pick_font.py",
    "tmp/base.char.csv,tmp/cjk-Scaled-Shifted.char.csv",
    "tmp/pick.char.csv"
)

# Calculate font meta
print("Calculating font meta...")
py(
    "ttf/cal_meta.py",
    "tmp/base.ascii.char.csv",
    "tmp/base.big.char.csv",
    "--height-multiplier", "1.3",
    "tmp/pick.meta.yaml"
)

# Merge fonts
print("Merging fonts...")
py(
    "ttf/merge_font.py",
    "tmp/base.ttf,tmp/cjk-Scaled-Shifted.ttf",
    "tmp/pick.char.csv",
    "tmp/pick.meta.yaml",
    "--input-info-meta-yaml", str(project_root / "CodeCJK/codecjk_meta.yaml"),
    "--font-name", OUTPUT_FONT_FULL_NAME,
    "--font-version", f"{OUTPUT_FONT_VERSION}.{YYYYMMDDHHMMSS}",
    "--override-datetime", YYYYMMDDHHMMSS,
    "--output", f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf"
)

# Dump output font char CSV
print("Dumping output font char CSV...")
py(
    "ttf/dump_char_csv.py",
    f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
    f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular.char.csv"
)

# Compare box metrics between output font and picked chars
print("Comparing box metrics between output font and picked characters...")
py(
    "ttf/csv_compare_box.py",
    f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular.char.csv",
    "tmp/pick.char.csv"
)

# Check if output font is mono width
print("Checking if output font is mono width...")
py(
    "ttf/check_mono_width.py",
    f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf"
)

# Create preview images
print("Creating preview images...")
py(
    "font_preview.py",
    f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
    "中あ강A2 1Il| 0O",
    "output/preview"
)
py(
    "font_preview.py",
    f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
    "中あ강A2 1Il| 0O",
    "output/debug",
    "--debug"
)

# Generate variant fonts with replaced metadata
print("Generating variant fonts with replaced metadata...")
py(
    "ttf/ttf_replace_meta.py",
    f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
    OUTPUT_FONT_FULL_NAME,
    OUTPUT_FONT_NAME,
    f"output/{OUTPUT_FONT_NAME}-{YYYYMMDDHHMMSS}-Regular.ttf"
)

py(
    "ttf/ttf_unmono.py",
    f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
    f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular-Unmono.ttf"
)

py(
    "ttf/ttf_replace_meta.py",
    f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular-Unmono.ttf",
    OUTPUT_FONT_FULL_NAME,
    f"P{OUTPUT_FONT_FULL_NAME}",
    f"output/P{OUTPUT_FONT_FULL_NAME}-Regular.ttf"
)

py(
    "ttf/ttf_replace_meta.py",
    f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular-Unmono.ttf",
    OUTPUT_FONT_FULL_NAME,
    f"P{OUTPUT_FONT_NAME}",
    f"output/P{OUTPUT_FONT_NAME}-{YYYYMMDDHHMMSS}-Regular.ttf"
)

print("\n" + "="*60)
print("Build completed successfully!")
print("="*60)
print(f"Main output: output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf")
print(f"Variant with timestamp: output/{OUTPUT_FONT_NAME}-{YYYYMMDDHHMMSS}-Regular.ttf")
print(f"Proportional variants: output/P{OUTPUT_FONT_FULL_NAME}-Regular.ttf, output/P{OUTPUT_FONT_NAME}-{YYYYMMDDHHMMSS}-Regular.ttf")
print(f"Preview images: output/preview.png, output/debug.png")
