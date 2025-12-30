"""
Utility functions for font character classification.
"""


def is_ascii_char(codepoint):
    """Check if a codepoint is an ASCII character."""
    # ASCII range: 0x0000-0x007F (0-127)
    return 0x0000 <= codepoint <= 0x007F


def is_cjk_char(codepoint):
    """Check if a codepoint is a CJK character."""
    # CJK Unified Ideographs (0x4E00-0x9FFF)
    # CJK Unified Ideographs Extension A (0x3400-0x4DBF)
    # CJK Unified Ideographs Extension B (0x20000-0x2A6DF)
    # CJK Unified Ideographs Extension C (0x2A700-0x2B73F)
    # CJK Unified Ideographs Extension D (0x2B740-0x2B81F)
    # CJK Unified Ideographs Extension E (0x2B820-0x2CEAF)
    # CJK Unified Ideographs Extension F (0x2CEB0-0x2EBEF)
    # CJK Compatibility Ideographs (0xF900-0xFAFF)
    # CJK Compatibility Ideographs Supplement (0x2F800-0x2FA1F)
    # Hiragana (0x3040-0x309F)
    # Katakana (0x30A0-0x30FF)
    # Hangul Syllables (0xAC00-0xD7AF)
    return (
        (0x4E00 <= codepoint <= 0x9FFF) or
        (0x3400 <= codepoint <= 0x4DBF) or
        (0x20000 <= codepoint <= 0x2A6DF) or
        (0x2A700 <= codepoint <= 0x2B73F) or
        (0x2B740 <= codepoint <= 0x2B81F) or
        (0x2B820 <= codepoint <= 0x2CEAF) or
        (0x2CEB0 <= codepoint <= 0x2EBEF) or
        (0xF900 <= codepoint <= 0xFAFF) or
        (0x2F800 <= codepoint <= 0x2FA1F) or
        (0x3040 <= codepoint <= 0x309F) or
        (0x30A0 <= codepoint <= 0x30FF) or
        (0xAC00 <= codepoint <= 0xD7AF)
    )


def is_upper_char(codepoint):
    """Check if a codepoint is an uppercase letter."""
    # ASCII uppercase (A-Z): 0x41-0x5A (65-90)
    return 0x41 <= codepoint <= 0x5A


def is_lower_char(codepoint):
    """Check if a codepoint is a lowercase letter."""
    # ASCII lowercase (a-z): 0x61-0x7A (97-122)
    return 0x61 <= codepoint <= 0x7A


def is_number_char(codepoint):
    """Check if a codepoint is a digit."""
    # ASCII digits (0-9): 0x30-0x39 (48-57)
    return 0x30 <= codepoint <= 0x39


def is_common_cjk_char(codepoint):
    """Check if a codepoint is a common CJK character."""
    # CJK Unified Ideographs (U+4E00-U+9FFF)
    return 0x4E00 <= codepoint <= 0x9FFF
