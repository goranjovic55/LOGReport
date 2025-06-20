from pathlib import Path
from typing import List


def filter_lines(lines: List[str], mode: str = "all", limit: int = 0,
                 start: int = 0, end: int = 0) -> List[str]:
    """Filter a list of lines based on the requested mode."""
    if not lines:
        return []
    mode = mode.lower()
    if mode == 'first' and limit > 0:
        return lines[:limit]
    if mode == 'last' and limit > 0:
        return lines[-limit:]
    if mode == 'range' and start > 0 and end > start:
        return lines[start - 1:end]
    return lines


def read_text_file(filepath: Path, encodings=None) -> List[str]:
    """Read text file using a list of encodings and return lines."""
    encodings = encodings or ['utf-8', 'ascii', 'latin-1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return [line.rstrip('\n') for line in f.readlines()]
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {filepath} with any supported encoding")

