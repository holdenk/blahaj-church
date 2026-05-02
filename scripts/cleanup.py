#!/usr/bin/env python3
"""
Blahaj Church — site content cleanup script.

Scans all HTML, Markdown, and YAML source files for known typos, casing
errors, and tracked-change artifacts, then reports (and optionally fixes)
them in-place.

Usage:
    # Report only (dry run):
    python3 scripts/cleanup.py

    # Apply fixes in-place:
    python3 scripts/cleanup.py --fix

    # Limit to specific files or directories:
    python3 scripts/cleanup.py --fix path/to/file.html _data/

The script is intentionally conservative: it only replaces patterns that
are unambiguous and have no expected false-positives in this codebase.
Patterns that require human judgement are flagged as warnings only.
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Root of the Jekyll site (directory that contains _config.yml).
# The script locates it relative to its own location so it can be run from
# any working directory.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

# File extensions to process.
EXTENSIONS = {".html", ".md", ".yml", ".yaml"}

# ---------------------------------------------------------------------------
# AUTO-FIX RULES
# Each entry is (description, compiled_regex, replacement_string).
# Replacements use standard re.sub() syntax (backreferences like \1 work).
# Rules are applied in order; earlier rules take priority.
# ---------------------------------------------------------------------------
AUTO_FIX_RULES = [
    # --- Tracked-change merge artifacts ---
    ("Merge artifact: Cchurch", re.compile(r"\bCchurch\b"), "Church"),
    ("Merge artifact: Mminister", re.compile(r"\bMminister\b"), "Minister"),
    ("Merge artifact: BlahajBlahaj", re.compile(r"\bBlahajBlahaj\b"), "Blahaj"),
    ("Merge artifact: normalynormally", re.compile(r"\bnormalynormally\b"), "normally"),
    ("Merge artifact: is notisn't", re.compile(r"\bis notisn't\b"), "isn't"),
    (
        "Merge artifact: both dangers both structural…",
        re.compile(
            r"both dangers both structural and physical"
            r"structural and physical dangers",
            re.IGNORECASE,
        ),
        "both structural and physical dangers",
    ),

    # --- Common typos ---
    ("Typo: conjuction → conjunction", re.compile(r"\bconjuction\b"), "conjunction"),
    ("Typo: awarness → awareness", re.compile(r"\bawarness\b"), "awareness"),
    ("Typo: normaly → normally", re.compile(r"\bnormaly\b"), "normally"),
    ("Typo: polices → policies (venue context)", re.compile(r"\bvenue polices\b"), "venue policies"),
    ("Typo: v.s. → vs.", re.compile(r"\bv\.s\.\b"), "vs."),
    ("Typo: annot afford → cannot afford", re.compile(r"\bannot afford\b"), "cannot afford"),
    ("Typo: awayy → away", re.compile(r"\bawayy\b"), "away"),

    # --- Capitalisation: church name and titles ---
    # "blahaj church" → "Blahaj Church" (case-insensitive, but not inside URLs or code)
    (
        "Casing: blahaj church → Blahaj Church",
        re.compile(r"\bblahaj church\b", re.IGNORECASE),
        "Blahaj Church",
    ),
    # "first minister" (lower-case) → "First Minister" when used as a title
    # Matches "first minister" not already capitalised.
    (
        "Casing: first minister → First Minister (title)",
        re.compile(r"\bfirst minister\b"),
        "First Minister",
    ),
    # "lead minister" is an outdated term for "First Minister"
    (
        "Outdated term: lead minister → First Minister",
        re.compile(r"\blead minister\b", re.IGNORECASE),
        "First Minister",
    ),
    # "google groups" → "Google Groups"
    (
        "Casing: google groups → Google Groups",
        re.compile(r"\bgoogle groups\b", re.IGNORECASE),
        "Google Groups",
    ),
    # "third party" (no hyphen) as adjective → "third-party"
    (
        "Hyphenation: third party tools → third-party tools",
        re.compile(r"\bthird party\b"),
        "third-party",
    ),

    # --- Punctuation / phrasing ---
    # Allegorical— (em-dash glued to word) → allegorical —  (space before dash)
    # The brief's artifact was "allegorical— stories" but the approved form is "allegorical —"
    (
        "Spacing: allegorical— → allegorical —",
        re.compile(r"allegorical—"),
        "allegorical —",
    ),
]

# ---------------------------------------------------------------------------
# WARNING-ONLY PATTERNS (reported but never auto-fixed)
# Each entry is (description, compiled_regex).
# ---------------------------------------------------------------------------
WARN_ONLY_PATTERNS = [
    # Duplicate punctuation
    ("Possible duplicate punctuation: ..", re.compile(r"\.{2}(?!\.)")),  # .. but not ...
    ("Possible double exclamation: !!", re.compile(r"!!")),
    ("Possible double question: ??", re.compile(r"\?\?")),

    # Competing tracked-change fragments that should have been resolved
    ("Possible unresolved tracked change: 'earning their right'",
     re.compile(r"\bearing their right\b")),
]

# ---------------------------------------------------------------------------
# Files / directories to skip entirely.
# ---------------------------------------------------------------------------
SKIP_DIRS = {".git", "_site", "node_modules", ".bundle", "vendor"}
SKIP_FILES = {"cleanup.py"}  # don't self-modify


def should_process(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS:
            return False
    if path.name in SKIP_FILES:
        return False
    return path.suffix in EXTENSIONS


def collect_files(targets: list[Path]) -> list[Path]:
    """Expand directories recursively; return deduplicated file list."""
    result: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        if target.is_dir():
            for p in sorted(target.rglob("*")):
                if p.is_file() and should_process(p) and p not in seen:
                    result.append(p)
                    seen.add(p)
        elif target.is_file():
            if should_process(target) and target not in seen:
                result.append(target)
                seen.add(target)
    return result


def process_file(path: Path, fix: bool) -> list[tuple[str, int, str, str]]:
    """
    Scan *path* for known issues.

    Returns a list of (rule_description, line_number, old_text, new_text).
    If fix=True, writes corrected content back to disk.
    """
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"  [SKIP] Cannot decode {path} as UTF-8", file=sys.stderr)
        return []

    findings: list[tuple[str, int, str, str]] = []
    content = original

    # --- Auto-fix rules ---
    for description, pattern, replacement in AUTO_FIX_RULES:
        for m in pattern.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            old = m.group(0)
            new = pattern.sub(replacement, old)
            if old != new:
                findings.append((description, line_no, old, new))
        content = pattern.sub(replacement, content)

    # --- Warning-only patterns (operate on original to get accurate line nos) ---
    for description, pattern in WARN_ONLY_PATTERNS:
        for m in pattern.finditer(original):
            line_no = original[: m.start()].count("\n") + 1
            findings.append((f"[WARN] {description}", line_no, m.group(0), m.group(0)))

    if fix and content != original:
        path.write_text(content, encoding="utf-8")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan (and optionally fix) Blahaj Church site content."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply fixes in-place. Without this flag the script only reports.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        type=Path,
        help="Files or directories to process. Defaults to the whole site.",
    )
    args = parser.parse_args()

    targets = args.targets if args.targets else [REPO_ROOT]
    files = collect_files(targets)

    if not files:
        print("No matching files found.")
        return 0

    total_issues = 0
    total_files_with_issues = 0

    for path in files:
        findings = process_file(path, fix=args.fix)
        if findings:
            total_files_with_issues += 1
            rel = path.relative_to(REPO_ROOT)
            print(f"\n{rel}")
            for description, line_no, old, new in findings:
                total_issues += 1
                if old == new:
                    # Warning only
                    print(f"  line {line_no:4d}  {description}: {old!r}")
                else:
                    action = "FIXED" if args.fix else "FOUND"
                    print(f"  line {line_no:4d}  [{action}] {description}")
                    print(f"           before: {old!r}")
                    print(f"            after: {new!r}")

    print(
        f"\n{'─' * 60}\n"
        f"  Files scanned : {len(files)}\n"
        f"  Files with issues: {total_files_with_issues}\n"
        f"  Total issues  : {total_issues}\n"
        + ("  Changes written to disk." if args.fix else "  Run with --fix to apply changes.")
    )

    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(main())
