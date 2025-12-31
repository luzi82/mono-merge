#!/usr/bin/env python3
"""
CodeCJK Font Build Script

This script builds the CodeCJK font by:
1. Downloading required font files (JetBrains Mono and Noto Sans Mono CJK)
2. Scaling and shifting the CJK font to match the Latin font
3. Merging the fonts together
4. Creating variant fonts with different metadata

The script can be run from any folder and works on both Linux and Windows.
Output and tmp folders are created in the working directory.
"""

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

my_env = os.environ.copy()
my_env["PYTHONIOENCODING"] = "utf-8"

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
        "id": "cjk",
        "type": "ttf",
        "ttf_url": "https://github.com/notofonts/noto-cjk/raw/refs/heads/main/Sans/Variable/TTF/Mono/NotoSansMonoCJKhk-VF.ttf",
        "ttf_filename": "NotoSansMonoCJKhk-VF.ttf",
        "ttf_md5": "ffde7dc37f0754c486b1cc5486a7ae93",
    },
]

def get_datetime_string():
    """Get current datetime in YYYYMMDDHHMMSS format."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def get_script_dir():
    """Get the directory containing this script."""
    return Path(__file__).parent.absolute()


def get_project_root():
    """Get the project root directory (parent of script directory)."""
    return get_script_dir().parent


def create_folders():
    """Create tmp and output folders in the working directory."""
    os.makedirs("tmp", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    print("Created tmp and output folders")


def download_file(url, output_path):
    """Download a file from URL to output path."""
    print(f"Downloading {url} to {output_path}")
    urllib.request.urlretrieve(url, output_path)
    print(f"Downloaded {output_path}")


def extract_zip(zip_path, extract_dir):
    """Extract a zip file to the specified directory."""
    print(f"Extracting {zip_path} to {extract_dir}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"Extracted to {extract_dir}")


def check_md5(file_path, expected_hash):
    """Check if a file's MD5 hash matches the expected hash."""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest() == expected_hash


def setup_python_environment(project_root):
    """Set up Python virtual environment and install dependencies."""
    print("Setting up Python environment...")
    venv_dir = Path("tmp/venv")
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, env=my_env)
    
    # Determine the python executable in the venv
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
    
    # Upgrade pip (use python -m pip instead of calling pip directly)
    subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True, env=my_env)
    
    # Install requirements
    requirements_file = project_root / "requirements.txt"
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)], check=True, env=my_env)
    
    print("Python environment setup complete")
    return str(python_exe)


def run_python_script(python_exe, script_path, *args):
    """Run a Python script with the given arguments."""
    cmd = [python_exe, str(script_path)] + list(args)
    print(f"Running: {' '.join(cmd)}")
    
    # Run process and capture output while also printing to stdout
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
        env=my_env
    )
    
    output_lines = []
    for line in process.stdout:
        # Print to stdout with encoding error handling
        try:
            print(line, end='')
        except UnicodeEncodeError:
            # If console can't display the character, encode with replacement
            print(line.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding), end='')
        output_lines.append(line)
    
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)
    
    return ''.join(output_lines).strip()


def read_yaml_value(yaml_file, key):
    """Read a value from a YAML file."""
    import yaml
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    return data.get(key)


def download_fonts(src_font_list, project_root):
    """Download and prepare fonts based on SRC_FONT_LIST configuration.
    
    Args:
        src_font_list: List of font configuration dictionaries
        project_root: Path to the project root directory
        
    Returns:
        None. Downloads and copies fonts to tmp/{font_id}.ttf
    """
    for font_config in src_font_list:
        font_id = font_config["id"]
        font_type = font_config["type"]
        ttf_filename = font_config["ttf_filename"]
        expected_md5 = font_config.get("ttf_md5")
        
        print(f"\n--- Processing font: {font_id} ---")
        
        # Target TTF file in tmp folder
        target_ttf = Path(f"tmp/{ttf_filename}")
        
        if not target_ttf.exists():
            # Check if file exists in input folder
            input_ttf = project_root / "input" / ttf_filename
            if input_ttf.exists():
                print(f"Found {input_ttf}, copying to {target_ttf}")
                shutil.copy(input_ttf, target_ttf)
            else:
                if font_type == "download_zip":
                    # Handle zip download type
                    zip_url = font_config["zip_url"]
                    ttf_path_in_zip = font_config["ttf_path_in_zip"]
                    
                    # Extract zip filename from URL
                    zip_filename = zip_url.split("/")[-1]
                    zip_path = Path(f"tmp/{zip_filename}")
                    
                    # Download zip if not exists
                    if not zip_path.exists():
                        download_file(zip_url, zip_path)
                    
                    # Extract zip
                    extract_dir_name = zip_filename.replace(".zip", "")
                    extract_dir = Path(f"tmp/{extract_dir_name}")
                    extract_zip(zip_path, extract_dir)
                    
                    # Copy TTF file from extracted location
                    extracted_ttf = extract_dir / ttf_path_in_zip
                    shutil.copy(extracted_ttf, target_ttf)
                    
                elif font_type == "ttf":
                    # Handle direct TTF download
                    ttf_url = font_config["ttf_url"]
                    download_file(ttf_url, target_ttf)
                else:
                    raise ValueError(f"Unknown font type: {font_type}")
        else:
            print(f"{target_ttf} already exists, skipping download")
        
        # Verify MD5 checksum if specified
        if expected_md5:
            print(f"Verifying MD5 checksum for {target_ttf}")
            if not check_md5(target_ttf, expected_md5):
                print(f"ERROR: MD5 mismatch for {target_ttf}")
                print(f"Expected: {expected_md5}")
                # Calculate actual MD5 for error message
                md5_hash = hashlib.md5()
                with open(target_ttf, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                print(f"Actual: {md5_hash.hexdigest()}")
                sys.exit(1)
            print(f"MD5 checksum verified: OK")
        else:
            # Calculate and print MD5 for reference
            md5_hash = hashlib.md5()
            with open(target_ttf, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            print(f"MD5 checksum: {md5_hash.hexdigest()}")
        
        # Copy to {font_id}.ttf for processing
        output_path = Path(f"tmp/{font_id}.ttf")
        print(f"Copying {target_ttf} to {output_path}")
        shutil.copy(target_ttf, output_path)


def main():
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
    yyyymmddhhmmss = get_datetime_string()
    print(f"Current datetime: {yyyymmddhhmmss}")
    
    # Get script and project directories
    script_dir = get_script_dir()
    project_root = get_project_root()
    print(f"Script directory: {script_dir}")
    print(f"Project root directory: {project_root}")
    
    # Create folders
    create_folders()
    
    # Download and prepare fonts (includes MD5 verification)
    download_fonts(SRC_FONT_LIST, project_root)
    
    # Set up Python environment
    python_exe = setup_python_environment(project_root)
    
    # Dump input font char CSV
    print("Dumping input font char CSV...")
    run_python_script(
        python_exe,
        project_root / "ttf/dump_char_csv.py",
        "tmp/base.ttf",
        "tmp/base.char.csv"
    )
    run_python_script(
        python_exe,
        project_root / "ttf/dump_char_csv.py",
        "tmp/cjk.ttf",
        "tmp/cjk.char.csv"
    )
    
    # Get the advance_width of char O
    print("Getting advance width of character 'O'...")
    advance_width_o_jb = run_python_script(
        python_exe,
        project_root / "utils/csv_query.py",
        "tmp/base.char.csv",
        "codepoint_dec", "79",
        "advance_width"
    )
    advance_width_o_noto = run_python_script(
        python_exe,
        project_root / "utils/csv_query.py",
        "tmp/cjk.char.csv",
        "codepoint_dec", "79",
        "advance_width"
    )
    print(f"Advance width of 'O' in JetBrains Mono: {advance_width_o_jb}")
    print(f"Advance width of 'O' in Noto Sans Mono CJK HK: {advance_width_o_noto}")
    
    # Calculate scale factor
    scale_factor = float(advance_width_o_jb) / float(advance_width_o_noto)
    print(f"Scale factor: {scale_factor}")
    
    # Scale Noto Sans Mono CJK HK VF font
    print("Scaling Noto Sans Mono CJK HK VF font...")
    run_python_script(
        python_exe,
        project_root / "ttf/scale_ttf.py",
        "tmp/cjk.ttf",
        str(scale_factor),
        "tmp/cjk-Scaled.ttf"
    )
    
    # Dump scaled font char CSV
    print("Dumping scaled font char CSV...")
    run_python_script(
        python_exe,
        project_root / "ttf/dump_char_csv.py",
        "tmp/cjk-Scaled.ttf",
        "tmp/cjk-Scaled.char.csv"
    )
    
    # Filter ASCII chars from JetBrains Mono
    print("Filtering ASCII characters from JetBrains Mono...")
    run_python_script(
        python_exe,
        project_root / "ttf/filter_char_csv.py",
        "tmp/base.char.csv",
        "ascii",
        "tmp/base.ascii.char.csv"
    )
    
    # Filter big chars from JetBrains Mono
    print("Filtering big characters from JetBrains Mono...")
    run_python_script(
        python_exe,
        project_root / "ttf/filter_char_csv.py",
        "tmp/base.char.csv",
        "upper,number",
        "tmp/base.big.char.csv"
    )
    
    # Filter common CJK chars from scaled Noto Sans Mono CJK HK
    print("Filtering common CJK characters from scaled Noto Sans Mono CJK HK...")
    run_python_script(
        python_exe,
        project_root / "ttf/filter_char_csv.py",
        "tmp/cjk-Scaled.char.csv",
        "common_cjk",
        "tmp/cjk-Scaled.common_cjk.char.csv"
    )
    
    # Calculate shift y offset
    print("Calculating shift Y offset...")
    run_python_script(
        python_exe,
        project_root / "ttf/cal_shift_y.py",
        "tmp/base.big.char.csv",
        "tmp/cjk-Scaled.common_cjk.char.csv",
        "tmp/shift_y_offset.yaml"
    )
    
    # Read shift_y value from YAML using venv Python
    shift_y_value = run_python_script(
        python_exe,
        project_root / "utils/yq.py",
        "tmp/shift_y_offset.yaml",
        "shift_y"
    )
    print(f"Shift Y value: {shift_y_value}")
    
    # Apply shift y to scaled Noto Sans Mono CJK HK VF font
    print("Applying shift Y to scaled Noto Sans Mono CJK HK VF font...")
    run_python_script(
        python_exe,
        project_root / "ttf/font_shift_y.py",
        "tmp/cjk-Scaled.ttf",
        str(shift_y_value),
        "tmp/cjk-Scaled-Shifted.ttf"
    )
    
    # Dump shifted font char CSV
    print("Dumping shifted font char CSV...")
    run_python_script(
        python_exe,
        project_root / "ttf/dump_char_csv.py",
        "tmp/cjk-Scaled-Shifted.ttf",
        "tmp/cjk-Scaled-Shifted.char.csv"
    )
    
    # Pick chars from JetBrains Mono and shifted scaled Noto Sans Mono CJK HK VF font
    print("Picking characters from JetBrains Mono and shifted scaled Noto Sans Mono CJK HK VF font...")
    run_python_script(
        python_exe,
        project_root / "ttf/pick_font.py",
        "tmp/base.char.csv,tmp/cjk-Scaled-Shifted.char.csv",
        "tmp/pick.char.csv"
    )
    
    # Calculate font meta
    print("Calculating font meta...")
    run_python_script(
        python_exe,
        project_root / "ttf/cal_meta.py",
        "tmp/base.ascii.char.csv",
        "tmp/base.big.char.csv",
        "--height-multiplier", "1.3",
        "tmp/pick.meta.yaml"
    )
    
    # Merge fonts
    print("Merging fonts...")
    run_python_script(
        python_exe,
        project_root / "ttf/merge_font.py",
        "tmp/base.ttf,tmp/cjk-Scaled-Shifted.ttf",
        "tmp/pick.char.csv",
        "tmp/pick.meta.yaml",
        "--input-info-meta-yaml", str(project_root / "CodeCJK/codecjk_meta.yaml"),
        "--font-name", OUTPUT_FONT_FULL_NAME,
        "--font-version", f"{OUTPUT_FONT_VERSION}.{yyyymmddhhmmss}",
        "--override-datetime", yyyymmddhhmmss,
        "--output", f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf"
    )
    
    # Dump output font char CSV
    print("Dumping output font char CSV...")
    run_python_script(
        python_exe,
        project_root / "ttf/dump_char_csv.py",
        f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
        f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular.char.csv"
    )
    
    # Compare box metrics between output font and picked chars
    print("Comparing box metrics between output font and picked characters...")
    run_python_script(
        python_exe,
        project_root / "ttf/csv_compare_box.py",
        f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular.char.csv",
        "tmp/pick.char.csv"
    )
    
    # Check if output font is mono width
    print("Checking if output font is mono width...")
    run_python_script(
        python_exe,
        project_root / "ttf/check_mono_width.py",
        f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf"
    )
    
    # Create preview images
    print("Creating preview images...")
    run_python_script(
        python_exe,
        project_root / "font_preview.py",
        f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
        "中あ강A2 1Il| 0O",
        "output/preview"
    )
    run_python_script(
        python_exe,
        project_root / "font_preview.py",
        f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
        "中あ강A2 1Il| 0O",
        "output/debug",
        "--debug"
    )
    
    # Generate variant fonts with replaced metadata
    print("Generating variant fonts with replaced metadata...")
    run_python_script(
        python_exe,
        project_root / "ttf/ttf_replace_meta.py",
        f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
        OUTPUT_FONT_FULL_NAME,
        OUTPUT_FONT_NAME,
        f"output/{OUTPUT_FONT_NAME}-{yyyymmddhhmmss}-Regular.ttf"
    )
    
    run_python_script(
        python_exe,
        project_root / "ttf/ttf_unmono.py",
        f"output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf",
        f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular-Unmono.ttf"
    )
    
    run_python_script(
        python_exe,
        project_root / "ttf/ttf_replace_meta.py",
        f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular-Unmono.ttf",
        OUTPUT_FONT_FULL_NAME,
        f"P{OUTPUT_FONT_FULL_NAME}",
        f"output/P{OUTPUT_FONT_FULL_NAME}-Regular.ttf"
    )
    
    run_python_script(
        python_exe,
        project_root / "ttf/ttf_replace_meta.py",
        f"tmp/{OUTPUT_FONT_FULL_NAME}-Regular-Unmono.ttf",
        OUTPUT_FONT_FULL_NAME,
        f"P{OUTPUT_FONT_NAME}",
        f"output/P{OUTPUT_FONT_NAME}-{yyyymmddhhmmss}-Regular.ttf"
    )
    
    print("\n" + "="*60)
    print("Build completed successfully!")
    print("="*60)
    print(f"Main output: output/{OUTPUT_FONT_FULL_NAME}-Regular.ttf")
    print(f"Variant with timestamp: output/{OUTPUT_FONT_NAME}-{yyyymmddhhmmss}-Regular.ttf")
    print(f"Proportional variants: output/P{OUTPUT_FONT_FULL_NAME}-Regular.ttf, output/P{OUTPUT_FONT_NAME}-{yyyymmddhhmmss}-Regular.ttf")
    print(f"Preview images: output/preview.png, output/debug.png")


if __name__ == "__main__":
    main()
