#!/usr/bin/env python3

import argparse
import sys
import difflib


def main():
    parser = argparse.ArgumentParser(
        description='Compare two files and output diff format'
    )
    parser.add_argument('FILE1', help='First file to compare')
    parser.add_argument('FILE2', help='Second file to compare')
    
    args = parser.parse_args()
    
    try:
        # Read both files
        with open(args.FILE1, 'r', encoding='utf-8') as f1:
            file1_lines = f1.read().splitlines(keepends=True)
        
        with open(args.FILE2, 'r', encoding='utf-8') as f2:
            file2_lines = f2.read().splitlines(keepends=True)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Generate unified diff
    diff = difflib.unified_diff(
        file1_lines,
        file2_lines,
        fromfile=args.FILE1,
        tofile=args.FILE2
    )
    
    # Convert to list to check if there are differences
    diff_lines = list(diff)
    
    if diff_lines:
        # Print the diff (rstrip to remove trailing newlines as they're already in the lines)
        for line in diff_lines:
            print(line.rstrip())
        sys.exit(1)  # Files differ
    else:
        # Files are the same (no output, like diff command)
        sys.exit(0)


if __name__ == '__main__':
    main()
