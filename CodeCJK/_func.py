"""
Helper functions for CodeCJK build script.
"""

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


# Module-level variables to store configuration
_python_exe = None
_my_env = None
_project_root = None


_my_env = os.environ.copy()
_my_env["PYTHONIOENCODING"] = "utf-8"


def set_my_env(my_env):
    """Set the environment variables to be used by run_python_script."""
    global _my_env
    _my_env = my_env


def get_datetime_string():
    """Get current datetime in YYYYMMDDHHMMSS format."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def get_script_dir():
    """Get the directory containing this script."""
    return Path(__file__).parent.absolute()


def get_project_root():
    """Get the project root directory (parent of script directory).
    
    Automatically caches the result in _project_root for use by run_python_script.
    """
    global _project_root
    if _project_root is None:
        _project_root = get_script_dir().parent
    return _project_root


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


def setup_python_environment():
    """Set up Python virtual environment and install dependencies."""
    global _python_exe

    project_root = get_project_root()

    print("Setting up Python environment...")
    venv_dir = Path("tmp/venv")
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, env=_my_env)
    
    # Determine the python executable in the venv
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
    
    # Upgrade pip (use python -m pip instead of calling pip directly)
    subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True, env=_my_env)
    
    # Install requirements
    requirements_file = project_root / "requirements.txt"
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)], check=True, env=_my_env)
    
    _python_exe = str(python_exe)

    print("Python environment setup complete")
    return _python_exe


def py(script_path, *args):
    """Run a Python script with the given arguments.
    
    script_path is relative to project_root and will be automatically prefixed.
    """
    if _python_exe is None:
        raise RuntimeError("Python executable not set. Call set_python_exe() first.")
    
    if _my_env is None:
        raise RuntimeError("Environment not set. Call set_my_env() first.")
    
    project_root = get_project_root()
    full_script_path = project_root / script_path
    cmd = [_python_exe, str(full_script_path)] + list(args)
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
        env=_my_env
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


def download_fonts(src_font_list):
    """Download and prepare fonts based on SRC_FONT_LIST configuration.
    
    Args:
        src_font_list: List of font configuration dictionaries
        
    Returns:
        None. Downloads and copies fonts to tmp/{font_id}.ttf
    """
    project_root = get_project_root()

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


def check_font(ttf_path):
    """Check if a font file is valid using ots-sanitize on Linux.
    
    Args:
        ttf_path: Path to the font file to check
        
    Raises:
        RuntimeError: If the font validation fails on Linux
    """
    if platform.system() == "Linux":
        try:
            print(f"Checking font: {ttf_path}")
            result = subprocess.run(
                ["ots-sanitize", str(ttf_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Font validation passed: {ttf_path}")
        except subprocess.CalledProcessError as e:
            error_msg = f"Font validation failed for {ttf_path}"
            if e.stderr:
                error_msg += f"\n{e.stderr}"
            raise RuntimeError(error_msg) from e
        except FileNotFoundError:
            raise RuntimeError("ots-sanitize command not found. Please install ots-tools.") from None
    else:
        print(f"Skipping font validation on {platform.system()} platform: {ttf_path}")
