# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import re
import argparse
import os
import shutil
from pathlib import Path

CHINESE_CHAR = r"[\u4e00-\u9fa5]"
ASCII_CHAR = r"[\x20-\x7E]"
NON_SPACE_ASCII_CHAR = r"[\x00-\x1F\x21-\x7F]"
ALPHA_DIGIT = r"[_a-zA-Z0-9]"
ADD_SPACE_BETWEEN_TWO_GROUPS = r"\1 \2"

"""
SPACE_MUST_BETWEEN = [ (ptn1, ptn2), ...]
records the list of (ptn1, ptn2) that must have a space between them.
"""
SPACE_MUST_BETWEEN = [
    (CHINESE_CHAR, r"%\d+"),
    (CHINESE_CHAR, rf"\'{ASCII_CHAR}+\'"),
    (CHINESE_CHAR, rf"\"{ASCII_CHAR}+\""),
    (CHINESE_CHAR, rf"<{ASCII_CHAR}+>"),
]

"""
RULES = [(<regex_pattern>, <replacement_pattern>), ...]
"""
RULES = (
    [
        # %select{...} and %diff{...} with leading ASCII letters
        (rf"({CHINESE_CHAR})(%\w+?\{{{NON_SPACE_ASCII_CHAR})", ADD_SPACE_BETWEEN_TWO_GROUPS),
        # %select{...ascii}0汉字
        (rf"(%select\{{.*?{NON_SPACE_ASCII_CHAR}\}}\d+)({CHINESE_CHAR})", ADD_SPACE_BETWEEN_TWO_GROUPS),
        # %diff{...ascii}0,1汉字
        (rf"(%diff\{{.*?{NON_SPACE_ASCII_CHAR}\}}\d+,\d+)({CHINESE_CHAR})", ADD_SPACE_BETWEEN_TWO_GROUPS),
        # 汉字123
        (rf"({CHINESE_CHAR})(\d+)", ADD_SPACE_BETWEEN_TWO_GROUPS),
        # 123汉字 ()
        (rf"( \d+)({CHINESE_CHAR})", ADD_SPACE_BETWEEN_TWO_GROUPS),
        (rf"({CHINESE_CHAR}\d+)({CHINESE_CHAR})", ADD_SPACE_BETWEEN_TWO_GROUPS),
    ]
    + [
        (rf"({ptn1})({ptn2})", ADD_SPACE_BETWEEN_TWO_GROUPS)
        for ptn1, ptn2 in SPACE_MUST_BETWEEN
    ]
    + [
        (rf"({ptn2})({ptn1})", ADD_SPACE_BETWEEN_TWO_GROUPS)
        for ptn1, ptn2 in SPACE_MUST_BETWEEN
    ]
)


def format_text(text: str, verbose=False):
    """Apply Chinese text formatting rules using regex substitutions."""
    for pattern, replacement in RULES:
        # re.ASCII flag let {ASCII_CHAR} does not match non-ASCII characters
        new_text = re.sub(pattern, replacement, text, flags=re.ASCII)
        if new_text != text and verbose:
            print(f"Applied rule: {pattern} -> {replacement}")
            print(f"\tOriginal : {text}")
            print(f"\tNew      : {new_text}")
        text = new_text
    return text


def process_input(content: str, args: argparse.ArgumentParser):
    """Process input content with formatting and optional verbose output."""
    formatted = format_text(content, args.verbose)
    return formatted


def main():
    """Main function with argument parsing and processing logic."""
    parser = argparse.ArgumentParser(
        description="Chinese Text Formatting Tool",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Usage Examples:\n"
        "  Process file:   %this_script -i input.txt -o output.txt\n"
        "  In-place edit:  %this_script -i input.txt --inplace\n"
        '  Process string: %this_script -s "%select{abc}2中文"\n'
        "  Print to stdout:   %this_script -i input.txt -v\n"
        "  Verbose mode:   %this_script -i input.txt -v",
    )

    # Input group (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("-i", "--input", help="Input file path")
    input_group.add_argument("-s", "--string", help="Process string directly")

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("-o", "--output", help="Output file path")
    output_group.add_argument(
        "--inplace",
        action="store_true",
        help="Modify input file in-place (with backup)",
    )

    # Additional options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose processing information",
    )
    parser.add_argument(
        "--backup-ext", default=".bak", help="Backup file extension (default: .bak)"
    )

    args = parser.parse_args()

    # Argument validation
    if args.inplace and not args.input:
        parser.error("--inplace requires -i/--input")
    if args.output and args.inplace:
        parser.error("Cannot use both --output and --inplace")

    # Process content
    try:
        # Handle string input
        if args.string:
            result = process_input(args.string, args)
            print("Formatted Result:".ljust(20, "="))
            print(result)
            return

        # Handle file input
        in_file = Path(args.input)
        if not in_file.exists():
            raise FileNotFoundError(f"Input file not found: {args.input}")

        content = in_file.read_text(encoding="utf-8")

        formatted = process_input(content, args)

        # Handle output destination
        if args.inplace:
            backup_file = args.input + args.backup_ext
            shutil.copy2(args.input, backup_file)
            if args.verbose:
                print(f"Created backup file: {backup_file}")
            in_file.write_text(formatted, encoding="utf-8")
            print(f"Successfully modified: {args.input}")

        elif args.output:
            out_file = Path(args.output)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(formatted, encoding="utf-8")
            if args.verbose:
                print(f"Output saved to: {args.output}")

        else:
            print("Formatted Result:".ljust(20, "="))
            print(formatted)

    except Exception as e:
        print(f"Processing error: {str(e)}")
        if args.verbose:
            raise e


if __name__ == "__main__":
    main()
