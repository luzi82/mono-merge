#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# do not modify build.py directly.
# build.py is generated from build.ipynb

import argparse
import copy
import itertools
import os
import shutil
import unicodedata
from pathlib import Path

from _func import * # just import all helper functions


# In[ ]:


OUTPUT_FONT_NAME = "CodeCJK"
OUTPUT_FONT_VERSION = "006"
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

SRC_FONT_DICT = {font["id"]: font for font in SRC_FONT_LIST}

FONT_KEY_LIST = [font["id"] for font in SRC_FONT_LIST]



# In[ ]:


# check if running in a notebook

def is_notebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

IN_NOTEBOOK = is_notebook()

print(f"Running in notebook: {IN_NOTEBOOK}")


# In[ ]:


if IN_NOTEBOOK:
    # get this ipynb script directory
    if 'original_cwd' not in globals():
        original_cwd = Path(os.getcwd())
        if os.path.exists(str(original_cwd / "build")):
            shutil.rmtree(str(original_cwd / "build"))
    # mkdir build
    os.makedirs(str(original_cwd / "build"), exist_ok=True)
    # change working directory to build
    os.chdir(str(original_cwd / "build"))


# In[ ]:


if not IN_NOTEBOOK:
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


# In[ ]:


def ttf_milestone(next_milestone):
    last_milestone_str = f"{int(next_milestone)-1:02d}"
    next_milestone_str = f"{int(next_milestone):02d}"

    os.makedirs(f"tmp/z{next_milestone_str}", exist_ok=True)

    print(f"Z{next_milestone_str} milestone")
    for font_key in FONT_KEY_LIST:

        check_font(
            f"tmp/z{last_milestone_str}/{font_key}.z{last_milestone_str}.99.ttf"
        )

        shutil.copyfile(
            f"tmp/z{last_milestone_str}/{font_key}.z{last_milestone_str}.99.ttf",
            f"tmp/z{next_milestone_str}/{font_key}.z{next_milestone_str}.00.ttf"
        )

        py(
            "ttf/dump_data_yaml.py",
            f"tmp/z{next_milestone_str}/{font_key}.z{next_milestone_str}.00.ttf",
            f"tmp/z{next_milestone_str}/{font_key}.z{next_milestone_str}.00.ttf.data.yaml",
        )
        py(
            "ttf/dump_char_csv.py",
            f"tmp/z{next_milestone_str}/{font_key}.z{next_milestone_str}.00.ttf",
        )


# In[ ]:


# Get script and project directories
script_dir = get_script_dir()
project_root = get_project_root()
print(f"Script directory: {script_dir}")
print(f"Project root directory: {project_root}")


# In[ ]:


# Create folders
"""Create tmp and output folders in the working directory."""
os.makedirs("tmp", exist_ok=True)
os.makedirs("output", exist_ok=True)
print("Created tmp and output folders")


# In[ ]:


os.makedirs("tmp/z00", exist_ok=True)


# In[ ]:


# Download and prepare fonts (includes MD5 verification)
download_fonts(SRC_FONT_LIST,'tmp/z00')


# In[ ]:


# Set up Python environment
python_exe = setup_python_environment()
print(f"Using Python executable: {python_exe}")


# In[ ]:


for font_key in FONT_KEY_LIST:
    shutil.copyfile(
        f"tmp/z00/{font_key}.ttf",
        f"tmp/z00/{font_key}.z00.99.ttf",
    )


# In[ ]:


ttf_milestone(1)


# In[ ]:


print("Clear unused data from ttf files")
for font_key in FONT_KEY_LIST:

    linux_cmd(
        "ttfautohint",
        "--dehint",
        f"tmp/z01/{font_key}.z01.00.ttf",
        f"tmp/z01/{font_key}.z01.01.ttf",
    )

    py(
        "ttf/ttf_rm_table.py",
        f"tmp/z01/{font_key}.z01.01.ttf",
        "GPOS,GSUB,vmtx,vhea,VORG,gasp,DSIG",
        f"tmp/z01/{font_key}.z01.02.ttf",
    )

    py(
        "ttf/ttf_post3.py",
        f"tmp/z01/{font_key}.z01.02.ttf",
        f"tmp/z01/{font_key}.z01.03.ttf"
    )

    shutil.copyfile(
        f"tmp/z01/{font_key}.z01.03.ttf",
        f"tmp/z01/{font_key}.z01.99.ttf",
    )


# In[ ]:


ttf_milestone(2)


# In[ ]:


# decompose composite glyphs
print("Decomposing composite glyphs...")
for font_key in FONT_KEY_LIST:
    py(
        "ttf/ttf_decompose_composite_glyph.py",
        f"tmp/z02/{font_key}.z02.00.ttf",
        f"tmp/z02/{font_key}.z02.01.ttf"
    )

    py(
        "ttf/dump_char_csv.py",
        f"tmp/z02/{font_key}.z02.01.ttf",
    )

    py(
        "utils/csv_rm_column.py",
        f"tmp/z02/{font_key}.z02.00.ttf.codepoint.csv",
        "glyph_index,glyph_name,cmap_used,num_contours",
        f"tmp/z02/{font_key}.z02.02.ttf.codepoint.expected.0.csv",
    )
    py(
        "utils/csv_set_col.py",
        f"tmp/z02/{font_key}.z02.02.ttf.codepoint.expected.0.csv",
        "is_composite:False,glyf_used:0,num_glyph:0",
        f"tmp/z02/{font_key}.z02.02.ttf.codepoint.expected.9.csv",
    )
    py(
        "utils/csv_rm_column.py",
        f"tmp/z02/{font_key}.z02.01.ttf.codepoint.csv",
        "glyph_index,glyph_name,cmap_used,num_contours",
        f"tmp/z02/{font_key}.z02.02.ttf.codepoint.actual.csv",
    )
    py(
        "utils/diff.py",
        f"tmp/z02/{font_key}.z02.02.ttf.codepoint.expected.9.csv",
        f"tmp/z02/{font_key}.z02.02.ttf.codepoint.actual.csv",
    )

    num_contours_list = py(
        "utils/csv_dump_col.py",
        f"tmp/z02/{font_key}.z02.01.ttf.codepoint.csv",
        "num_contours",
        stdout = False,
    ).split('\n')
    assert('-1' not in num_contours_list), "Error: still have composite glyphs!"

    is_composite_list = py(
        "utils/csv_dump_col.py",
        f"tmp/z02/{font_key}.z02.01.ttf.glyph.csv",
        "is_composite",
        stdout = False,
    ).split('\n')
    assert('True' not in is_composite_list), "Error: still have composite glyphs!"

    shutil.copyfile(
        f"tmp/z02/{font_key}.z02.01.ttf",
        f"tmp/z02/{font_key}.z02.99.ttf",
    )


# In[ ]:


ttf_milestone(3)


# In[ ]:


# rm unused glyphs
for font_key in FONT_KEY_LIST:

    py(
        "ttf/glyphcsv_used_mark_rm.py",
        f"tmp/z03/{font_key}.z03.00.ttf.glyph.csv",
        f"tmp/z03/{font_key}.z03.00.ttf.glyphref.csv",
        f"tmp/z03/{font_key}.z03.01.rm_glyph.csv"
    )

    py(
        "ttf/ttf_rm_glyph.py",
        f"tmp/z03/{font_key}.z03.00.ttf",
        f"tmp/z03/{font_key}.z03.01.rm_glyph.csv",
        f"tmp/z03/{font_key}.z03.02.ttf"
    )

    py(
        "ttf/dump_char_csv.py",
        f"tmp/z03/{font_key}.z03.02.ttf",
    )

    py(
        "utils/csv_rm_column.py",
        f"tmp/z03/{font_key}.z03.00.ttf.codepoint.csv",
        "glyph_index,glyph_name",
        f"tmp/z03/{font_key}.z03.03.ttf.codepoint.expected.csv",
    )
    py(
        "utils/csv_rm_column.py",
        f"tmp/z03/{font_key}.z03.02.ttf.codepoint.csv",
        "glyph_index,glyph_name",
        f"tmp/z03/{font_key}.z03.03.ttf.codepoint.actual.csv",
    )
    py(
        "utils/diff.py",
        f"tmp/z03/{font_key}.z03.03.ttf.codepoint.expected.csv",
        f"tmp/z03/{font_key}.z03.03.ttf.codepoint.actual.csv",
    )

    shutil.copyfile(
        f"tmp/z03/{font_key}.z03.02.ttf",
        f"tmp/z03/{font_key}.z03.99.ttf",
    )



# In[ ]:


ttf_milestone(4)


# In[ ]:


# get base font informations

# Get ASCII chars from base font
print("Getting ASCII characters from base font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/z04/base.z04.00.ttf.codepoint.csv",
    "ascii",
    "tmp/z04/base.z04.01.ascii.csv"
)

# Get big chars from base font
print("Getting big characters from base font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/z04/base.z04.00.ttf.codepoint.csv",
    "upper,number",
    "tmp/z04/base.z04.01.big.csv"
)

base_half_advance_width = py(
    "utils/csv_query.py",
    "tmp/z04/base.z04.00.ttf.codepoint.csv",
    "codepoint_dec", "79", "advance_width",
    stdout=False,
)
base_half_advance_width = int(base_half_advance_width)
print("Base font half advance width:", base_half_advance_width)

base_big_max_height = py(
    "utils/csv_query.py",
    "tmp/z04/base.z04.01.big.csv",
    "yMax", "__MAX__", "yMax",
    stdout=False,
)
base_big_max_height = int(base_big_max_height)
print("Base font big max height:", base_big_max_height)

# # Make a copy of base font as final checkpoint
# shutil.copyfile(
#     "tmp/z04/base.z04.00.ttf",
#     "tmp/z04/base.z04.99.ttf",
# )

pass


# In[ ]:


py(
    "ttf/cal_shift_x_csv.py",
    "tmp/z04/base.z04.00.ttf.glyph.csv",
    str(base_half_advance_width),
    "tmp/z04/base.z04.01.shift_x.csv"
)

py(
    "ttf/modify_advance_width.py",
    "tmp/z04/base.z04.00.ttf",
    "tmp/z04/base.z04.01.shift_x.csv",
    "tmp/z04/base.z04.02.ttf"
)

# check shift_x result

py(
    "ttf/dump_char_csv.py",
    "tmp/z04/base.z04.02.ttf",
)

py(
    "utils/csv_rm_column.py",
    "tmp/z04/base.z04.01.shift_x.csv",
    "shift_x",
    "tmp/z04/base.z04.03.expect.glyph.csv",
)
py(
    "utils/diff.py",
    "tmp/z04/base.z04.02.ttf.glyph.csv",
    "tmp/z04/base.z04.03.expect.glyph.csv",
)

pass


# In[ ]:


# Make a copy of base font as final checkpoint
shutil.copyfile(
    "tmp/z04/base.z04.02.ttf",
    "tmp/z04/base.z04.99.ttf",
)

pass


# In[ ]:


## Scale patch0 font to match base font

# Get big chars from patch0 font
print("Getting big characters from patch0 font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/z04/patch0.z04.00.ttf.codepoint.csv",
    "upper,number",
    "tmp/z04/patch0.z04.01.big.csv"
)

patch0_big_max_height = py(
    "utils/csv_query.py",
    "tmp/z04/patch0.z04.01.big.csv",
    "yMax", "__MAX__", "yMax",
    stdout=False,
)
patch0_big_max_height = int(patch0_big_max_height)
print("Patch0 font big max height:", patch0_big_max_height)

patch0_scale_factor = float(base_big_max_height) / float(patch0_big_max_height)
print("Patch0 font scale factor:", patch0_scale_factor)


# In[ ]:


# Scale patch0 font
print("Scaling patch0 font...")
py(
    "ttf/scale_ttf.py",
    "tmp/z04/patch0.z04.00.ttf",
    "tmp/z04/patch0.z04.00.ttf.glyph.csv",
    str(patch0_scale_factor),
    "tmp/z04/patch0.z04.02.ttf"
)

# Dump scaled patch0 font char CSV
print("Dumping scaled patch0 font char CSV...")
py(
    "ttf/dump_char_csv.py",
    "tmp/z04/patch0.z04.02.ttf"
)

# py(
#     "ttf/dump_data_yaml.py",
#     "tmp/patch0.z04.02.ttf",
#     "tmp/patch0.z04.02.ttf.data.yaml",
# )

pass


# In[ ]:


# update units_per_em, ascent, descent

## get base font units_per_em
base_units_per_em = py(
    "utils/yq.py",
    "tmp/z04/base.z04.00.ttf.data.yaml",
    "head.unitsPerEm",
    stdout=False,
)
base_units_per_em = int(base_units_per_em)
print("Base font units_per_em:", base_units_per_em)

base_ascender = py(
    "utils/yq.py",
    "tmp/z04/base.z04.00.ttf.data.yaml",
    "hhea.ascender",
    stdout=False,
)
base_ascender = int(base_ascender)
print("Base font base_ascender:", base_ascender)

base_descender = py(
    "utils/yq.py",
    "tmp/z04/base.z04.00.ttf.data.yaml",
    "hhea.descender",
    stdout=False,
)
base_descender = int(base_descender)
print("Base font base_descender:", base_descender)


py(
    "ttf/ttf_set_data.py",
    "tmp/z04/patch0.z04.02.ttf",
    "--units-per-em", str(base_units_per_em),
    "--ascender", str(base_ascender),
    "--descender", str(base_descender),
    "tmp/z04/patch0.z04.03.ttf",
)

py(
    "ttf/dump_data_yaml.py",
    "tmp/z04/patch0.z04.03.ttf",
    "tmp/z04/patch0.z04.03.ttf.data.yaml",
)
py(
    "ttf/dump_char_csv.py",
    "tmp/z04/patch0.z04.03.ttf",
)

pass


# In[ ]:


# modify advance_width of patch0.scaled.ttf to match base font half advance width
print("Modifying advance_width of patch0.scaled.ttf to match base font half advance width...")
py(
    "ttf/cal_shift_x_csv.py",
    "tmp/z04/patch0.z04.03.ttf.glyph.csv",
    str(base_half_advance_width),
    "tmp/z04/patch0.z04.04.shift_x.csv"
)

py(
    "ttf/modify_advance_width.py",
    "tmp/z04/patch0.z04.03.ttf",
    "tmp/z04/patch0.z04.04.shift_x.csv",
    "tmp/z04/patch0.z04.05.ttf"
)

# check shift_x result

py(
    "ttf/dump_char_csv.py",
    "tmp/z04/patch0.z04.05.ttf",
)

py(
    "utils/csv_rm_column.py",
    "tmp/z04/patch0.z04.04.shift_x.csv",
    "shift_x",
    "tmp/z04/patch0.z04.06.expect.glyph.csv",
)
py(
    "utils/diff.py",
    "tmp/z04/patch0.z04.05.ttf.glyph.csv",
    "tmp/z04/patch0.z04.06.expect.glyph.csv",
)
pass


# In[ ]:


shutil.copyfile(
    "tmp/z04/patch0.z04.05.ttf",
    "tmp/z04/patch0.z04.99.ttf",
)

pass


# In[ ]:


# scale cjk font

## Get the advance_width of char O
print("Getting advance width of character 'O'...")
cjk_half_advance_width = py(
    "utils/csv_query.py",
    "tmp/z04/cjk.z04.00.ttf.codepoint.csv",
    "codepoint_dec", "79",
    "advance_width"
)
print(f"CJK half advance width: {cjk_half_advance_width}")

cjk_scale_factor = float(base_half_advance_width) / float(cjk_half_advance_width)
print("CJK font scale factor:", cjk_scale_factor)


# In[ ]:


# Scale cjk font
print("Scaling cjk font...")
py(
    "ttf/scale_ttf.py",
    "tmp/z04/cjk.z04.00.ttf",
    "tmp/z04/cjk.z04.00.ttf.glyph.csv",
    str(cjk_scale_factor),
    "tmp/z04/cjk.z04.01.ttf"
)

# Dump scaled cjk font char CSV
print("Dumping scaled cjk font char CSV...")
py(
    "ttf/dump_char_csv.py",
    "tmp/z04/cjk.z04.01.ttf"
)

pass


# In[ ]:


# check 2E3A and 2E3B glyph id

u2E3A_glyph_id = py(
    "utils/csv_query.py",
    "tmp/z04/cjk.z04.01.ttf.codepoint.csv",
    "codepoint", "U+2E3A",
    "glyph_index",
    stdout=False,
)
u2E3B_glyph_id = py(
    "utils/csv_query.py",
    "tmp/z04/cjk.z04.01.ttf.codepoint.csv",
    "codepoint", "U+2E3B",
    "glyph_index",
    stdout=False,
)
print(f"U+2E3A glyph id: {u2E3A_glyph_id}")
print(f"U+2E3B glyph id: {u2E3B_glyph_id}")

# modify advance_width of cjk.scaled.ttf to match base font half advance width
print("Modifying advance_width of cjk.scaled.ttf to match base font half advance width...")
py(
    "ttf/cal_shift_x_csv.py",
    "tmp/z04/cjk.z04.01.ttf.glyph.csv",
    "--update-width-unit", f"{u2E3A_glyph_id}:4,{u2E3B_glyph_id}:6",
    str(base_half_advance_width),
    "tmp/z04/cjk.z04.02.shift_x.csv"
)

py(
    "ttf/modify_advance_width.py",
    "tmp/z04/cjk.z04.01.ttf",
    "tmp/z04/cjk.z04.02.shift_x.csv",
    "tmp/z04/cjk.z04.03.ttf"
)

# check shift_x result

py(
    "ttf/dump_char_csv.py",
    "tmp/z04/cjk.z04.03.ttf",
)

py(
    "utils/csv_rm_column.py",
    "tmp/z04/cjk.z04.02.shift_x.csv",
    "shift_x",
    "tmp/z04/cjk.z04.04.expect.glyph.csv",
)
py(
    "utils/diff.py",
    "tmp/z04/cjk.z04.03.ttf.glyph.csv",
    "tmp/z04/cjk.z04.04.expect.glyph.csv",
)

pass


# In[ ]:


# y shift

print("Getting common CJK characters from cjk font...")
py(
    "ttf/filter_char_csv.py",
    "tmp/z04/cjk.z04.03.ttf" ".codepoint.csv",
    "common_cjk",
    "tmp/z04/cjk.z04.05.ccjk.csv"
)

base_anchor_y = base_big_max_height / 2
print("Base font anchor y:", base_anchor_y)

cjk_top_y = py(
    "utils/csv_query.py",
    "tmp/z04/cjk.z04.05.ccjk.csv",
    "yMax", "__99%__", "yMax",
    stdout=False,
)
print("CJK font top y:", cjk_top_y)
cjk_top_y = int(cjk_top_y)

cjk_low_y = py(
    "utils/csv_query.py",
    "tmp/z04/cjk.z04.05.ccjk.csv",
    "yMin", "__1%__", "yMin",
    stdout=False,
)
print("CJK font low y:", cjk_low_y)
cjk_low_y = int(cjk_low_y)

cjk_anchor_y = (cjk_top_y + cjk_low_y) / 2
print("CJK font anchor y:", cjk_anchor_y)

cjk_shift_y = int(base_anchor_y - cjk_anchor_y)
print("CJK font shift y:", cjk_shift_y)


# In[ ]:


py(
    "ttf/ttf_shift_y.py",
    "tmp/z04/cjk.z04.03.ttf",
    str(cjk_shift_y),
    "tmp/z04/cjk.z04.06.ttf"
)

pass


# In[ ]:


shutil.copyfile(
    "tmp/z04/cjk.z04.06.ttf",
    "tmp/z04/cjk.z04.99.ttf",
)


# In[ ]:


ttf_milestone(5)


# In[ ]:


# py(
#     "ttf/filter_char_csv.py",
#     "tmp/z05/base.z05.00.ttf.codepoint.csv",
#     "ascii",
#     "tmp/z05/base.z05.01.ascii.csv",
# )

py(
    "ttf/filter_char_csv.py",
    "tmp/z05/base.z05.00.ttf.codepoint.csv",
    "upper,number",
    "tmp/z05/base.z05.01.big.csv",
)

# ymin = py(
#     "utils/csv_query.py",
#     "tmp/z05/base.z05.01.big.csv",
#     "yMin", "__MIN__", "yMin",
#     stdout=False,
# )
ymax = py(
    "utils/csv_query.py",
    "tmp/z05/base.z05.01.big.csv",
    "yMax", "__MAX__", "yMax",
    stdout=False,
)
ymax = int(ymax)

ymid = ymax / 2
print("Big char mid y:", ymid)

# ymin = py(
#     "utils/csv_query.py",
#     "tmp/z05/base.z05.01.ascii.csv",
#     "yMin", "__MIN__", "yMin",
#     stdout=False,
# )
# ymax = py(
#     "utils/csv_query.py",
#     "tmp/z05/base.z05.01.ascii.csv",
#     "yMax", "__MAX__", "yMax",
#     stdout=False,
# )
# yheight = int(ymax) - int(ymin)
# print("ASCII height:", yheight)

xAvgCharWidth = py(
    "utils/yq.py",
    "tmp/z05/base.z05.00.ttf.data.yaml",
    "os2.xAvgCharWidth",
    stdout=False,
)
xAvgCharWidth = int(xAvgCharWidth)
print("xAvgCharWidth:", xAvgCharWidth)

yheight = xAvgCharWidth * 2 * 17 / 16
print("Font height:", yheight)

ascender = int(ymid + yheight / 2)
print("New ascender:", ascender)
descender = int(ymid - yheight / 2)
print("New descender:", descender)

unitsPerEm = py(
    "utils/yq.py",
    "tmp/z05/base.z05.00.ttf.data.yaml",
    "head.unitsPerEm",
    stdout=False,
)
print("unitsPerEm:", unitsPerEm)

pass


# In[ ]:


fontkey_to_fontdata_dict = {}

for font_key in FONT_KEY_LIST:
    fontkey_to_fontdata_dict[font_key] = {
        "codepoint_dl": read_csv(f"tmp/z05/{font_key}.z05.00.ttf.codepoint.csv"),
        "glyph_dl": read_csv(f"tmp/z05/{font_key}.z05.00.ttf.glyph.csv"),
        "font_key": font_key,
    }

    src_codepoint_dl = fontkey_to_fontdata_dict[font_key]["codepoint_dl"]
    glyph_dl = fontkey_to_fontdata_dict[font_key]["glyph_dl"]

    for d in src_codepoint_dl:
        codepoint_int = d['codepoint_int'] = int(d['codepoint_dec'])

    src_codepoint_dl = copy.deepcopy(src_codepoint_dl)
    for d in src_codepoint_dl:
        d["src"] = font_key
        d["src_glyph_index"] = d["glyph_index"]
    fontkey_to_fontdata_dict[font_key]["src_codepoint_dl"] = src_codepoint_dl

    codepointint_to_src_d_dict = {d['codepoint_int']: d for d in src_codepoint_dl}
    fontkey_to_fontdata_dict[font_key]["codepointint_to_src_d_dict"] = codepointint_to_src_d_dict

base_codepointint_to_src_d_dict = fontkey_to_fontdata_dict['base']["codepointint_to_src_d_dict"]
patch0_codepointint_to_src_d_dict = fontkey_to_fontdata_dict['patch0']["codepointint_to_src_d_dict"]
cjk_codepointint_to_src_d_dict = fontkey_to_fontdata_dict['cjk']["codepointint_to_src_d_dict"]

codepointint_set = set()
codepointint_set.update(base_codepointint_to_src_d_dict.keys())
codepointint_set.update(patch0_codepointint_to_src_d_dict.keys())
codepointint_set.update(cjk_codepointint_to_src_d_dict.keys())
codepointint_list = list(sorted(codepointint_set))

output_codepointint_to_select_d_dict = {}

for codepointint in codepointint_list:
    select_d = {}
    # codepoint_dec = d['codepoint_dec']
    select_d['codepoint'] = f"U+{codepointint:04X}"
    select_d['codepoint_int'] = codepointint
    codepoint_dec = str(codepointint)
    select_d['codepoint_dec'] = codepoint_dec
    select_d['eaw'] = unicodedata.east_asian_width(chr(int(codepoint_dec)))
    select_d['name'] = unicodedata.name(chr(int(codepoint_dec)), '')
    output_codepointint_to_select_d_dict[codepointint] = select_d

hardcode_widthunit_dl = read_csv(str(project_root / "CodeCJK/widthunit.csv"))
for d in hardcode_widthunit_dl:
    codepoint_min_int = int(d['codepoint_min'])
    codepoint_max_int = int(d['codepoint_max'])
    widthunit_int = int(d['width_unit'])
    for codepointint in range(codepoint_min_int, codepoint_max_int + 1):
        if codepointint in output_codepointint_to_select_d_dict:
            output_codepointint_to_select_d_dict[codepointint]['hardcode_widthunit_int'] = widthunit_int
            output_codepointint_to_select_d_dict[codepointint]['hardcode_widthunit'] = str(widthunit_int)

for codepointint, select_d in output_codepointint_to_select_d_dict.items():
    target_widthunit_int = 1
    if 'hardcode_widthunit_int' in select_d:
        target_widthunit_int = select_d['hardcode_widthunit_int']
    elif select_d['eaw'] in ['F', 'W']:
        target_widthunit_int = 2
    else:
        target_widthunit_int = 1
    select_d['target_widthunit_int'] = target_widthunit_int
    select_d['target_widthunit'] = str(target_widthunit_int)

    base_widthunit   = select_d['base']   = base_codepointint_to_src_d_dict.get(codepointint, {}).get('width_unit', '')
    patch0_widthunit = select_d['patch0'] = patch0_codepointint_to_src_d_dict.get(codepointint, {}).get('width_unit', '')
    cjk_widthunit    = select_d['cjk']    = cjk_codepointint_to_src_d_dict.get(codepointint, {}).get('width_unit', '')
    target_diff = float('inf')
    select_src = ''
    for src, widthunit in [('base', base_widthunit), ('patch0', patch0_widthunit), ('cjk', cjk_widthunit)]:
        if widthunit != '':
            diff = abs(int(widthunit) - target_widthunit_int)
            if diff < target_diff:
                target_diff = diff
                select_src = src
    select_d['src'] = select_src

# hardcode src selection
output_codepointint_to_select_d_dict[38]['src'] = 'patch0'  # '&'
output_codepointint_to_select_d_dict[64]['src'] = 'patch0'  # '@'
output_codepointint_to_select_d_dict[65378]['src'] = 'cjk'
output_codepointint_to_select_d_dict[65379]['src'] = 'cjk'

for codepointint, select_d in output_codepointint_to_select_d_dict.items():
    src = select_d['src']
    if src == 'base':
        src_d = base_codepointint_to_src_d_dict[codepointint]
    elif src == 'patch0':
        src_d = patch0_codepointint_to_src_d_dict[codepointint]
    elif src == 'cjk':
        src_d = cjk_codepointint_to_src_d_dict[codepointint]
    else:
        continue
    select_d['widthunit'] = src_d['width_unit']

output_select_dl = list(output_codepointint_to_select_d_dict.values())
output_select_dl = list(sorted(output_select_dl, key=lambda d: d['codepoint_int']))

output_codepointint_to_src_d_dict = {}

for codepointint, select_d in output_codepointint_to_select_d_dict.items():
    src = select_d['src']
    if src == 'base':
        src_d = base_codepointint_to_src_d_dict[codepointint]
    elif src == 'patch0':
        src_d = patch0_codepointint_to_src_d_dict[codepointint]
    elif src == 'cjk':
        src_d = cjk_codepointint_to_src_d_dict[codepointint]
    else:
        continue
    output_codepointint_to_src_d_dict[codepointint] = src_d


# for codepointint, src_d in cjk_codepointint_to_src_d_dict.items():
#     add = False
#     c = chr(codepointint)
#     eaw = unicodedata.east_asian_width(c)
#     if codepointint not in output_codepointint_to_src_d_dict:
#         add = True
#     elif c.isalpha() and c.isascii():
#         add = False
#     elif 'LATIN' in unicodedata.name(c):
#         add = False
#     elif 'CYRILLIC' in unicodedata.name(c):
#         add = False
#     elif 'GREEK' in unicodedata.name(c):
#         add = False
#     elif codepointint <= 0xFF:
#         add = False
#     elif eaw in ['F', 'W']:
#         add = True
#     elif eaw == ['Na', 'H']:
#         add = False
#     elif int(src_d['width_unit']) > int(output_codepointint_to_src_d_dict[codepointint]['width_unit']):
#         add = True
#     if add:
#         output_codepointint_to_src_d_dict[codepointint] = src_d

output_codepoint_dl = list(output_codepointint_to_src_d_dict.values())
output_codepoint_dl = list(sorted(output_codepoint_dl, key=lambda d: d['codepoint_int']))
tmp_glyph_index = 1
src_src_glyph_index_to_glyph_index_dict = {}
output_glyphclone_dl = []
for d in output_codepoint_dl:
    src = d['src']
    src_glyph_index = d['src_glyph_index']
    key = (src, src_glyph_index)
    if key in src_src_glyph_index_to_glyph_index_dict:
        dest_glyph_index = src_src_glyph_index_to_glyph_index_dict[key]
    else:
        src_src_glyph_index_to_glyph_index_dict[key] = tmp_glyph_index
        dest_glyph_index = tmp_glyph_index

        output_glyphclone_dl.append({
            "glyph_index": str(dest_glyph_index),
            "src": src,
            "src_glyph_index": src_glyph_index,
        })

        tmp_glyph_index += 1

    dest_glyph_index_str = str(dest_glyph_index)
    d['glyph_index'] = dest_glyph_index_str


write_csv(
    output_select_dl,
    ["codepoint","codepoint_dec","eaw","base","patch0","cjk","src","widthunit","name"],
    "tmp/z05/output.z05.01.picksrc.width_unit.csv",
)

write_csv(
    output_glyphclone_dl,
    ["glyph_index","src","src_glyph_index"],
    "tmp/z05/output.z05.01.picksrc.glyphclone.csv",
)

col_list = [
    "codepoint","codepoint_dec","glyph_index","glyph_name","advance_width",
    "lsb","xMin","yMin","xMax","yMax",
    "width","height","width_unit",
    "is_empty_glyph","is_composite","num_contours","num_glyph",
    "cmap_used","glyf_used","gsub_used","gpos_used",
    "has_glyf","has_hmtx","has_vmtx",
    "src","src_glyph_index"
]

write_csv(
    output_codepoint_dl,
    col_list,
    "tmp/z05/output.z05.01.picksrc.codepoint.csv",
)


# In[ ]:


# gen string

name_list = []

for font_key in FONT_KEY_LIST:
    name = py(
        "utils/yq.py",
        f"tmp/z01/{font_key}.z01.00.ttf.data.yaml",
        "name.family_name",
        stdout=False,
    )
    name_list.append(name)
    print(f"{font_key} font name: {name}")

name_list_str = " + ".join(name_list)
long_description = f"Luzi82, merging {name_list_str}"


# In[ ]:


# Get datetime string
YYYYMMDDHHMMSS = get_datetime_string()
print(f"Current datetime: {YYYYMMDDHHMMSS}")

py(
    "ttf/ttf_build.py",
    "tmp/z05/output.z05.01.picksrc.codepoint.csv",
    "tmp/z05/output.z05.01.picksrc.glyphclone.csv",
    "base:tmp/z05/base.z05.00.ttf,patch0:tmp/z05/patch0.z05.00.ttf,cjk:tmp/z05/cjk.z05.00.ttf",
    "--default=base",
    f"--font-name=__FONT_NAME__",
    "--url-vendor=https://github.com/luzi82/mono-merge/blob/main/CodeCJK/CodeCJK.md",
    f"--name-unique-id=__FONT_NAME__-Luzi82-{YYYYMMDDHHMMSS}",
    "--license=SIL Open Font License, Version 1.1",
    f"--copyright={long_description}",
    "--manufacturer=Luzi82",
    f"--designer={long_description}",
    f"--version={YYYYMMDDHHMMSS}",
    f"--ascender={ascender}",
    f"--descender={descender}",
    f"--xAvgCharWidth={xAvgCharWidth}",
    f"--unitsPerEm={unitsPerEm}",
    "tmp/z05/output.z05.02.ttf"
)

py(
    "ttf/dump_char_csv.py",
    "tmp/z05/output.z05.02.ttf",
)
py(
    "ttf/dump_data_yaml.py",
    "tmp/z05/output.z05.02.ttf",
    "tmp/z05/output.z05.02.ttf.data.yaml",
)

pass


# In[ ]:


# final checking

check_font("tmp/z05/output.z05.02.ttf")

py(
    "utils/csv_rm_column.py",
    "tmp/z05/output.z05.01.picksrc.codepoint.csv",
    "glyph_name,src,src_glyph_index,cmap_used",
    "tmp/z05/output.z05.03.expect.codepoint.csv",
)
py(
    "utils/csv_rm_column.py",
    "tmp/z05/output.z05.02.ttf.codepoint.csv",
    "glyph_name,cmap_used",
    "tmp/z05/output.z05.03.actual.codepoint.csv",
)
py(
    "utils/diff.py",
    "tmp/z05/output.z05.03.expect.codepoint.csv",
    "tmp/z05/output.z05.03.actual.codepoint.csv",
)

py(
    "ttf/check_mono_width.py",
    "tmp/z05/output.z05.02.ttf",
)


# In[ ]:


linux_cmd(
    "ttfautohint",
    "--ignore-restrictions",
    "-f","none","--fallback-scaling",
    "tmp/z05/output.z05.02.ttf",
    "tmp/z05/output.z05.04.ttf",
)

check_font("tmp/z05/output.z05.04.ttf")


# In[ ]:


py(
    "ttf/dump_char_csv.py",
    "tmp/z05/output.z05.04.ttf",
)

py(
    "ttf/filter_char_csv.py",
    "tmp/z05/output.z05.04.ttf.codepoint.csv",
    "ascii,upper,number,common_cjk",
    "tmp/z05/output.z05.05.ttf.preview_chars.csv",
)

maxy_char_codepoint = py(
    "utils/csv_query.py",
    "tmp/z05/output.z05.05.ttf.preview_chars.csv",
    "yMax", "__MAX__", "codepoint_dec",
    stdout=False,
)
maxy_char = chr(int(maxy_char_codepoint))
print("Character with max yMax in preview chars:", maxy_char, f"(U+{int(maxy_char_codepoint):04X})")
miny_char_codepoint = py(
    "utils/csv_query.py",
    "tmp/z05/output.z05.05.ttf.preview_chars.csv",
    "yMin", "__MIN__", "codepoint_dec",
    stdout=False,
)
miny_char = chr(int(miny_char_codepoint))
print("Character with min yMin in preview chars:", miny_char, f"(U+{int(miny_char_codepoint):04X})")

FONT_SIZE_LIST = list(range(8, 17))+list(range(18, 25, 2))+[36,48]

for font_size in FONT_SIZE_LIST:
    py(
        "font_preview.py",
        "tmp/z05/output.z05.04.ttf",
        f"你好嗎 0O1Il| $@& {maxy_char}{miny_char}",
        f"tmp/z05/output.z05.06.{font_size:02d}",
        "--font-size", str(font_size),
    )

py(
    "font_preview.py",
    "tmp/z05/output.z05.04.ttf",
    f"你好嗎 0O1Il| $@& {maxy_char}{miny_char}",
    f"tmp/z05/output.z05.06.debug",
    "--debug"
)

for font_size in FONT_SIZE_LIST:

    py(
        "font_preview.py",
        "tmp/z05/output.z05.04.ttf",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        f"tmp/z05/output.z05.06.upper.{font_size:02d}",
        "--font-size", str(font_size),
    )

    py(
        "font_preview.py",
        "tmp/z05/output.z05.04.ttf",
        "abcdefghijklmnopqrstuvwxyz",
        f"tmp/z05/output.z05.06.lower.{font_size:02d}",
        "--font-size", str(font_size),
    )

    py(
        "font_preview.py",
        "tmp/z05/output.z05.04.ttf",
        "0123456789",
        f"tmp/z05/output.z05.06.num.{font_size:02d}",
        "--font-size", str(font_size),
    )

    py(
        "font_preview.py",
        "tmp/z05/output.z05.04.ttf",
        "~!@#$%^&*()_+`-={}|:\"<>?[]\;',./",
        f"tmp/z05/output.z05.06.punctuation.{font_size:02d}",
        "--font-size", str(font_size),
    )


# In[ ]:


def create_font_preview(ttf_path, preview_text, output_png_path, font_size=48):
    os.makedirs("tmp/tmp", exist_ok=True)
    os.makedirs(os.path.dirname(output_png_path), exist_ok=True)

    py(
      "font_preview.py",
      ttf_path,
      preview_text,
      "tmp/tmp/tmp",
      "--font-size", str(font_size),
      "--debug"
    )

    x0 = py(
      "utils/yq.py",
      "tmp/tmp/tmp.yaml",
      "render_info.text_bounding_box_in_png.left",
    )
    x0 = int(x0)

    x1 = py(
      "utils/yq.py",
      "tmp/tmp/tmp.yaml",
      "render_info.text_bounding_box_in_png.right",
      stdout=False,
    )
    x1 = int(x1)

    y0 = py(
      "utils/yq.py",
      "tmp/tmp/tmp.yaml",
      "render_info.ascent_line_y",
      stdout=False,
    )
    y0 = int(y0)

    y1 = py(
      "utils/yq.py",
      "tmp/tmp/tmp.yaml",
      "render_info.descent_line_y",
      stdout=False,
    )
    y1 = int(y1)

    height = y1 - y0
    expend = height // 8

    box_x0 = x0 - expend
    box_y0 = y0 - expend
    box_x1 = x1 + expend
    box_y1 = y1 + expend

    linux_cmd(
      "convert",
      "tmp/tmp/tmp.png",
      "-crop",
      f"{box_x1 - box_x0}x{box_y1 - box_y0}+{box_x0}+{box_y0}",
      output_png_path,
    )


# In[ ]:


create_font_preview(
    "tmp/z05/output.z05.04.ttf",
    f"中あ한 0O 1Il|",
    str(project_root / "CodeCJK/img/debug_clip.png"),
)

create_font_preview(
    "tmp/z05/output.z05.04.ttf",
    f"中 ABC",
    str(project_root / "CodeCJK/img/vcenter.png"),
)

create_font_preview(
    "tmp/z05/output.z05.04.ttf",
    f"ABC&@",
    str(project_root / "CodeCJK/img/patch.png"),
)

create_font_preview(
    "tmp/z05/output.z05.04.ttf",
    f"===",
    str(project_root / "CodeCJK/img/no_ligatures.png"),
)

create_font_preview(
    "tmp/z05/output.z05.04.ttf",
    f"E",
    str(project_root / "CodeCJK/img/E14.png"),
    font_size=14
)

create_font_preview(
    "tmp/z05/output.z05.04.ttf",
    f"E",
    str(project_root / "CodeCJK/img/E16.png"),
    font_size=16
)


# In[ ]:


fontname_list = [
    OUTPUT_FONT_NAME,
    OUTPUT_FONT_FULL_NAME,
]
monospace_config_list = [
    {'prefix': '', 'monospace': True},
    {'prefix': 'P', 'monospace': False},
]

cross_list = itertools.product(fontname_list, monospace_config_list)

if os.path.exists("tmp/zip"):
    shutil.rmtree("tmp/zip")
os.makedirs(f"tmp/zip", exist_ok=True)

for (fontname, monospace_config) in cross_list:
    prefix = monospace_config['prefix']
    monospace = monospace_config['monospace']

    output_ttf_path0 = f"output/{prefix}{fontname}-Regular-{YYYYMMDDHHMMSS}.ttf"
    output_ttf_path1 = f"tmp/zip/{prefix}{fontname}-Regular-{YYYYMMDDHHMMSS}.ttf"

    if monospace:
        shutil.copyfile(
            "tmp/z05/output.z05.04.ttf",
            f"tmp/z05/tmp0.ttf",
        )
    else:
        py(
            "ttf/ttf_unmono.py",
            "tmp/z05/output.z05.04.ttf",
            f"tmp/z05/tmp0.ttf",
        )


    py(
        "ttf/ttf_replace_meta.py",
        "tmp/z05/tmp0.ttf",
        "__FONT_NAME__", prefix+fontname,
        "tmp/z05/tmp1.ttf",
    )

    check_font(f"tmp/z05/tmp1.ttf")

    shutil.copyfile(
        "tmp/z05/tmp1.ttf",
        output_ttf_path0,
    )
    shutil.copyfile(
        "tmp/z05/tmp1.ttf",
        output_ttf_path1,
    )

shutil.copytree(
    str(project_root / "CodeCJK/export/"),
    "tmp/zip/",
    dirs_exist_ok=True,
)

shutil.make_archive(
    f"output/{OUTPUT_FONT_FULL_NAME}",
    'zip',
    root_dir=f"tmp/zip"
)

pass


# In[ ]:


'''
python -m nbconvert \
  --clear-output \
  --inplace CodeCJK/build.ipynb && \
python -m nbconvert \
  --to script CodeCJK/build.ipynb \
  --output build \
&& \
rm -rf xxx && \
mkdir xxx && \
cd xxx && \
python ../CodeCJK/build.py
'''

pass

