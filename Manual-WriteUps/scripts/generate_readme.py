#!/usr/bin/env python3
"""
Regenerates the auto-generated sections of the top-level README.md (difficulty
stats table and full machine list) by scanning every <MachineName>/README.md
in the repo root.

Repo layout expected:

  README.md              <- this file, auto-updated
  Checkpoint/README.md
  Lame/README.md
  Jerry/README.md
  ...

Each machine's README.md must start with a metadata table like:

| Field      | Details                                                        |
|------------|------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Checkpoint)   |
| Difficulty | Hard                                                             |
| OS         | Windows                                                          |
| Author     | Landau                                                           |
| Date       | June 16, 2026                                                    |

The machine name is taken from the directory name (e.g. "Checkpoint").

Usage:
  python3 scripts/generate_readme.py
"""

import re
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"

# Directories to never treat as a machine write-up
EXCLUDE_DIRS = {".git", ".github", "scripts", "node_modules", ".idea", ".vscode"}

STATS_START = "<!-- STATS:START -->"
STATS_END = "<!-- STATS:END -->"
TABLE_START = "<!-- MACHINES:START -->"
TABLE_END = "<!-- MACHINES:END -->"

DIFFICULTY_EMOJI = {
    "Easy": "🟢",
    "Medium": "🟡",
    "Hard": "🔴",
    "Insane": "⚫",
}
DIFFICULTY_ORDER = ["Easy", "Medium", "Hard", "Insane"]

FIELD_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def find_machine_dirs() -> list:
    """Return every top-level directory containing a README.md, excluding known non-machine dirs."""
    dirs = []
    for p in sorted(REPO_ROOT.iterdir()):
        if not p.is_dir():
            continue
        if p.name in EXCLUDE_DIRS or p.name.startswith("."):
            continue
        if (p / "README.md").exists():
            dirs.append(p)
    return dirs


def parse_writeup(dir_path: Path) -> dict:
    readme = dir_path / "README.md"
    text = readme.read_text(encoding="utf-8")

    name = dir_path.name  # machine name = folder name

    fields = {}
    for key, value in FIELD_ROW_RE.findall(text):
        key_clean = key.strip().lower()
        if key_clean in ("field", "") or set(key.strip()) <= {"-"}:
            continue
        fields[key_clean] = value.strip()

    platform_raw = fields.get("platform", "")
    link_match = LINK_RE.search(platform_raw)
    htb_url = link_match.group(2) if link_match else ""

    difficulty = fields.get("difficulty", "Unknown").strip()
    os_name = fields.get("os", "Unknown").strip()
    author = fields.get("author", "").strip()
    date_str = fields.get("date", "").strip()

    return {
        "name": name,
        "difficulty": difficulty,
        "os": os_name,
        "author": author,
        "date": date_str,
        "url": htb_url,
        "file": f"{dir_path.name}/README.md",
    }


def parse_date(date_str: str):
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.min


def build_stats_table(machines: list) -> str:
    counts = {d: 0 for d in DIFFICULTY_ORDER}
    for m in machines:
        if m["difficulty"] in counts:
            counts[m["difficulty"]] += 1

    descriptions = {
        "Easy": "Beginner-friendly machines with straightforward paths",
        "Medium": "Moderate complexity, requiring intermediate skills",
        "Hard": "Complex machines requiring advanced techniques",
        "Insane": "Expert-level challenges with multiple layers",
    }

    lines = [
        "| Difficulty | Count | Description |",
        "|------------|-------|-------------|",
    ]
    for d in DIFFICULTY_ORDER:
        emoji = DIFFICULTY_EMOJI[d]
        lines.append(f"| {emoji} **{d}** | {counts[d]} | {descriptions[d]} |")
    lines.append("")
    lines.append(f"**Total machines documented: {len(machines)}**")
    return "\n".join(lines)


def build_machines_table(machines: list) -> str:
    if not machines:
        return "*No write-ups yet — check back soon!*"

    machines_sorted = sorted(machines, key=lambda m: parse_date(m["date"]), reverse=True)

    lines = [
        "| Machine | Difficulty | OS | Date | Write-up |",
        "|---------|------------|----|------|----------|",
    ]
    for m in machines_sorted:
        emoji = DIFFICULTY_EMOJI.get(m["difficulty"], "⚪")
        link = f"[{m['name']}]({m['file']})"
        lines.append(
            f"| {link} | {emoji} {m['difficulty']} | {m['os']} | {m['date']} | [Read more]({m['file']}) |"
        )
    return "\n".join(lines)


def replace_section(content: str, start_marker: str, end_marker: str, new_body: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL
    )
    replacement = f"{start_marker}\n{new_body}\n{end_marker}"
    if not pattern.search(content):
        print(f"ERROR: markers {start_marker} / {end_marker} not found in README.md", file=sys.stderr)
        sys.exit(1)
    return pattern.sub(replacement, content)


def main():
    machine_dirs = find_machine_dirs()
    machines = [parse_writeup(d) for d in machine_dirs]

    if not README_PATH.exists():
        print(f"ERROR: {README_PATH} does not exist", file=sys.stderr)
        sys.exit(1)

    content = README_PATH.read_text(encoding="utf-8")
    content = replace_section(content, STATS_START, STATS_END, build_stats_table(machines))
    content = replace_section(content, TABLE_START, TABLE_END, build_machines_table(machines))

    README_PATH.write_text(content, encoding="utf-8")
    print(f"README.md updated with {len(machines)} machine(s): {', '.join(m['name'] for m in machines) or '(none)'}")


if __name__ == "__main__":
    main()
