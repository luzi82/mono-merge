#!/bin/bash -e

# get current datetime in format YYYYMMDDHHMMSS
YYYYMMDDHHMMSS=$(date +"%Y%m%d%H%M%S")
echo "Current datetime: ${YYYYMMDDHHMMSS}"

# get the folder path of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: ${SCRIPT_DIR}"

# get the folder path of the project root
PROJECT_ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
echo "Project root directory: ${PROJECT_ROOT_DIR}"

# create folders
mkdir -p tmp
mkdir -p output

# check if tmp/JetBrainsMonoNL-Regular.ttf exists
if [ ! -f "tmp/JetBrainsMonoNL-Regular.ttf" ]; then
    # check if tmp/JetBrainsMono-2.304.zip exists
    if [ ! -f "tmp/JetBrainsMono-2.304.zip" ]; then
        # download JetBrains Mono font
        wget -O tmp/JetBrainsMono-2.304.zip "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip"
    fi
    # unzip JetBrainsMono-2.304.zip
    unzip -o tmp/JetBrainsMono-2.304.zip -d tmp/JetBrainsMono-2.304
    # copy JetBrainsMonoNL-Regular.ttf to tmp folder
    cp tmp/JetBrainsMono-2.304/fonts/ttf/JetBrainsMonoNL-Regular.ttf tmp/
fi 

# check if tmp/NotoSansMonoCJKhk-VF.ttf exists
if [ ! -f "tmp/NotoSansMonoCJKhk-VF.ttf" ]; then
    # download Noto Sans Mono CJK HK VF font
    wget -O tmp/NotoSansMonoCJKhk-VF.ttf "https://github.com/notofonts/noto-cjk/raw/refs/heads/main/Sans/Variable/TTF/Mono/NotoSansMonoCJKhk-VF.ttf"
fi

# check md5sums
echo "Checking md5sums..."
md5sum -c "${SCRIPT_DIR}/input_files.md5"

# init python environment
echo "Setting up Python environment..."
python3 -m venv "tmp/venv"
source "tmp/venv/bin/activate"
pip install --upgrade pip
pip install -r "${PROJECT_ROOT_DIR}/requirements.txt"

# dump input font char csv
echo "Dumping input font char CSV..."
python "${PROJECT_ROOT_DIR}/ttf/dump_char_csv.py" \
    "tmp/JetBrainsMonoNL-Regular.ttf" \
    "tmp/JetBrainsMonoNL-Regular.char.csv"
python "${PROJECT_ROOT_DIR}/ttf/dump_char_csv.py" \
    "tmp/NotoSansMonoCJKhk-VF.ttf" \
    "tmp/NotoSansMonoCJKhk-VF.char.csv"

# get the advance_width of char O
echo "Getting advance width of character 'O'..."
ADVANCE_WIDTH_O_JB=$(python "${PROJECT_ROOT_DIR}/utils/csv_query.py" \
    "tmp/JetBrainsMonoNL-Regular.char.csv" \
    "codepoint_dec" "79" \
    "advance_width")
ADVANCE_WIDTH_O_NOTO=$(python "${PROJECT_ROOT_DIR}/utils/csv_query.py" \
    "tmp/NotoSansMonoCJKhk-VF.char.csv" \
    "codepoint_dec" "79" \
    "advance_width")
echo "Advance width of 'O' in JetBrains Mono: ${ADVANCE_WIDTH_O_JB}"
echo "Advance width of 'O' in Noto Sans Mono CJK HK: ${ADVANCE_WIDTH_O_NOTO}"

# calculate scale factor
SCALE_FACTOR=$(echo "scale=6; ${ADVANCE_WIDTH_O_JB} / ${ADVANCE_WIDTH_O_NOTO}" | bc)
echo "Scale factor: ${SCALE_FACTOR}"

# scale Noto Sans Mono CJK HK VF font
echo "Scaling Noto Sans Mono CJK HK VF font..."
python "${PROJECT_ROOT_DIR}/ttf/scale_ttf.py" \
    "tmp/NotoSansMonoCJKhk-VF.ttf" \
    "${SCALE_FACTOR}" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled.ttf"

# dump scaled font char csv
echo "Dumping scaled font char CSV..."
python "${PROJECT_ROOT_DIR}/ttf/dump_char_csv.py" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled.ttf" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled.char.csv"

# filter ascii chars from JetBrains Mono
echo "Filtering ASCII characters from JetBrains Mono..."
python "${PROJECT_ROOT_DIR}/ttf/filter_char_csv.py" \
    "tmp/JetBrainsMonoNL-Regular.char.csv" \
    "ascii" \
    "tmp/JetBrainsMonoNL-Regular.ascii.char.csv"

# filter big chars from JetBrains Mono
echo "Filtering big characters from JetBrains Mono..."
python "${PROJECT_ROOT_DIR}/ttf/filter_char_csv.py" \
    "tmp/JetBrainsMonoNL-Regular.char.csv" \
    "upper,number" \
    "tmp/JetBrainsMonoNL-Regular.big.char.csv"

# filter common CJK chars from scaled Noto Sans Mono CJK HK
echo "Filtering common CJK characters from scaled Noto Sans Mono CJK HK..."
python "${PROJECT_ROOT_DIR}/ttf/filter_char_csv.py" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled.char.csv" \
    "common_cjk" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled.common_cjk.char.csv"

# calculate shift y offset
echo "Calculating shift Y offset..."
python "${PROJECT_ROOT_DIR}/ttf/cal_shift_y.py" \
    "tmp/JetBrainsMonoNL-Regular.big.char.csv" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled.common_cjk.char.csv" \
    "tmp/shift_y_offset.yaml"
SHIFT_Y_VALUE=$(yq -r '.shift_y' tmp/shift_y_offset.yaml)
echo "Shift Y value: ${SHIFT_Y_VALUE}"

# apply shift y to scaled Noto Sans Mono CJK HK VF font
echo "Applying shift Y to scaled Noto Sans Mono CJK HK VF font..."
python "${PROJECT_ROOT_DIR}/ttf/font_shift_y.py" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled.ttf" \
    "${SHIFT_Y_VALUE}" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled-Shifted.ttf"

# dump shifted font char csv
echo "Dumping shifted font char CSV..."
python "${PROJECT_ROOT_DIR}/ttf/dump_char_csv.py" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled-Shifted.ttf" \
    "tmp/NotoSansMonoCJKhk-VF-Scaled-Shifted.char.csv"

# pick chars from JetBrains Mono and shifted scaled Noto Sans Mono CJK HK VF font
echo "Picking characters from JetBrains Mono and shifted scaled Noto Sans Mono CJK HK VF font..."
python "${PROJECT_ROOT_DIR}/ttf/pick_font.py" \
    "tmp/JetBrainsMonoNL-Regular.char.csv,tmp/NotoSansMonoCJKhk-VF-Scaled-Shifted.char.csv" \
    "tmp/pick.char.csv"

# calculate font meta
echo "Calculating font meta..."
python "${PROJECT_ROOT_DIR}/ttf/cal_meta.py" \
    "tmp/JetBrainsMonoNL-Regular.ascii.char.csv" \
    "tmp/JetBrainsMonoNL-Regular.big.char.csv" \
    --height-multiplier 1.3 \
    "tmp/pick.meta.yaml"

# merge fonts
echo "Merging fonts..."
python "${PROJECT_ROOT_DIR}/ttf/merge_font.py" \
    "tmp/JetBrainsMonoNL-Regular.ttf,tmp/NotoSansMonoCJKhk-VF-Scaled-Shifted.ttf" \
    "tmp/pick.char.csv" \
    "tmp/pick.meta.yaml" \
    --input-info-meta-yaml "${PROJECT_ROOT_DIR}/CodeCJK/codecjk_meta.yaml" \
    --font-name "CodeCJK004" \
    --font-version "004.${YYYYMMDDHHMMSS}" \
    --override-datetime "${YYYYMMDDHHMMSS}" \
    --output "output/CodeCJK004-Regular.ttf"

# dump output font char csv
echo "Dumping output font char CSV..."
python "${PROJECT_ROOT_DIR}/ttf/dump_char_csv.py" \
    "output/CodeCJK004-Regular.ttf" \
    "tmp/CodeCJK004-Regular.char.csv"

# compare box metrics between output font and picked chars
echo "Comparing box metrics between output font and picked characters..."
python "${PROJECT_ROOT_DIR}/ttf/csv_compare_box.py" \
    "tmp/CodeCJK004-Regular.char.csv" \
    "tmp/pick.char.csv"

# check if output font is mono width
echo "Checking if output font is mono width..."
python "${PROJECT_ROOT_DIR}/ttf/check_mono_width.py" \
    "output/CodeCJK004-Regular.ttf"

# create preview images
echo "Creating preview images..."
python "${PROJECT_ROOT_DIR}/font_preview.py" \
    "output/CodeCJK004-Regular.ttf" \
    "中あ강A2 1Il| 0O" \
    "output/preview"
python "${PROJECT_ROOT_DIR}/font_preview.py" \
    "output/CodeCJK004-Regular.ttf" \
    "中あ강A2 1Il| 0O" \
    "output/debug" \
    --debug

# generate variant fonts with replaced metadata

python "${PROJECT_ROOT_DIR}/ttf/ttf_replace_meta.py" \
    "output/CodeCJK004-Regular.ttf" \
    "CodeCJK004" \
    "CodeCJK" \
    "output/CodeCJK-${YYYYMMDDHHMMSS}-Regular.ttf"

python "${PROJECT_ROOT_DIR}/ttf/ttf_unmono.py" \
    "output/CodeCJK004-Regular.ttf" \
    "tmp/CodeCJK004-Regular-Unmono.ttf"

python "${PROJECT_ROOT_DIR}/ttf/ttf_replace_meta.py" \
    "tmp/CodeCJK004-Regular-Unmono.ttf" \
    "CodeCJK004" \
    "PCodeCJK004" \
    "output/PCodeCJK004-Regular.ttf"

python "${PROJECT_ROOT_DIR}/ttf/ttf_replace_meta.py" \
    "tmp/CodeCJK004-Regular-Unmono.ttf" \
    "CodeCJK004" \
    "PCodeCJK" \
    "output/PCodeCJK-${YYYYMMDDHHMMSS}-Regular.ttf"
