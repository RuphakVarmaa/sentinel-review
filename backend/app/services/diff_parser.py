from dataclasses import dataclass, field
from typing import Optional
import re

LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
    '.tsx': 'tsx', '.jsx': 'jsx', '.go': 'go', '.rs': 'rust',
    '.java': 'java', '.rb': 'ruby', '.php': 'php', '.cs': 'csharp',
    '.cpp': 'cpp', '.c': 'c', '.h': 'c', '.swift': 'swift',
    '.kt': 'kotlin', '.sh': 'bash', '.sql': 'sql', '.yml': 'yaml',
    '.yaml': 'yaml', '.json': 'json', '.md': 'markdown',
}


@dataclass
class LineInfo:
    line_no: int
    content: str


@dataclass
class Hunk:
    file_path: str
    change_type: str  # 'add', 'modify', 'delete'
    language: str
    added_lines: list = field(default_factory=list)
    removed_lines: list = field(default_factory=list)
    context_lines: list = field(default_factory=list)
    hunk_header: str = ""
    raw_diff: str = ""


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    if not file_path:
        return 'text'
    # Find the last extension
    parts = file_path.rsplit('.', 1)
    if len(parts) < 2:
        return 'text'
    ext = '.' + parts[-1].lower()
    return LANGUAGE_MAP.get(ext, 'text')


def parse_diff(diff_text: str) -> list:
    """Parse unified diff format into Hunk objects.

    Handles: diff --git a/... b/..., --- a/..., +++ b/..., @@ ... @@
    Groups multiple hunks in same file together.
    """
    hunks = []
    if not diff_text or not diff_text.strip():
        return hunks

    lines = diff_text.splitlines(keepends=True)

    current_file = None
    current_old_file = None
    current_new_file = None
    change_type = 'modify'
    in_hunk = False
    hunk_lines = []
    hunk_header = ""
    old_line_no = 0
    new_line_no = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n').rstrip('\r')

        # New file in diff
        if stripped.startswith('diff --git '):
            # Flush previous hunk
            if current_file and hunk_lines:
                hunk = _build_hunk(
                    current_file, change_type,
                    hunk_lines, hunk_header,
                    old_line_no, new_line_no
                )
                hunks.append(hunk)
                hunk_lines = []
                hunk_header = ""

            # Reset state
            current_old_file = None
            current_new_file = None
            change_type = 'modify'
            in_hunk = False
            i += 1
            continue

        if stripped.startswith('--- '):
            path = stripped[4:]
            if path.startswith('a/'):
                path = path[2:]
            current_old_file = path
            i += 1
            continue

        if stripped.startswith('+++ '):
            path = stripped[4:]
            if path.startswith('b/'):
                path = path[2:]
            current_new_file = path

            # Determine change type
            if current_old_file and '/dev/null' in current_old_file:
                change_type = 'add'
                current_file = current_new_file
            elif current_new_file and '/dev/null' in current_new_file:
                change_type = 'delete'
                current_file = current_old_file
            else:
                change_type = 'modify'
                current_file = current_new_file if current_new_file else current_old_file

            i += 1
            continue

        # Hunk header: @@ -old_start,old_count +new_start,new_count @@
        hunk_match = re.match(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', stripped)
        if hunk_match:
            # Flush previous hunk if any
            if current_file and hunk_lines:
                hunk = _build_hunk(
                    current_file, change_type,
                    hunk_lines, hunk_header,
                    old_line_no, new_line_no
                )
                hunks.append(hunk)
                hunk_lines = []

            old_line_no = int(hunk_match.group(1))
            new_line_no = int(hunk_match.group(2))
            hunk_header = stripped
            in_hunk = True
            hunk_lines = [line]
            i += 1
            continue

        if in_hunk:
            hunk_lines.append(line)

        i += 1

    # Flush last hunk
    if current_file and hunk_lines:
        hunk = _build_hunk(
            current_file, change_type,
            hunk_lines, hunk_header,
            old_line_no, new_line_no
        )
        hunks.append(hunk)

    return hunks


def _build_hunk(
    file_path: str,
    change_type: str,
    hunk_lines: list,
    hunk_header: str,
    old_start: int,
    new_start: int
) -> Hunk:
    """Build a Hunk object from raw diff lines."""
    language = detect_language(file_path)
    added_lines = []
    removed_lines = []
    context_lines = []
    raw_diff = ''.join(hunk_lines)

    old_line_no = old_start
    new_line_no = new_start

    for line in hunk_lines:
        stripped = line.rstrip('\n').rstrip('\r')

        # Skip hunk headers
        if stripped.startswith('@@'):
            continue

        if stripped.startswith('+'):
            added_lines.append(LineInfo(line_no=new_line_no, content=stripped[1:]))
            new_line_no += 1
        elif stripped.startswith('-'):
            removed_lines.append(LineInfo(line_no=old_line_no, content=stripped[1:]))
            old_line_no += 1
        else:
            # Context line
            content = stripped[1:] if stripped.startswith(' ') else stripped
            context_lines.append(LineInfo(line_no=new_line_no, content=content))
            old_line_no += 1
            new_line_no += 1

    return Hunk(
        file_path=file_path,
        change_type=change_type,
        language=language,
        added_lines=added_lines,
        removed_lines=removed_lines,
        context_lines=context_lines,
        hunk_header=hunk_header,
        raw_diff=raw_diff,
    )


def group_by_file(hunks: list) -> dict:
    """Group hunks by file_path, return dict."""
    grouped: dict = {}
    for hunk in hunks:
        if hunk.file_path not in grouped:
            grouped[hunk.file_path] = []
        grouped[hunk.file_path].append(hunk)
    return grouped


def diff_to_llm_context(hunks: list) -> str:
    """Format hunks as readable text for LLM consumption.

    Includes file path, language, and raw diff content.
    Truncates to 80k chars if too long.
    """
    MAX_CHARS = 80000
    parts = []

    grouped = group_by_file(hunks)

    for file_path, file_hunks in grouped.items():
        language = file_hunks[0].language if file_hunks else 'text'
        parts.append(f"### File: {file_path} ({language})")
        parts.append(f"Change type: {file_hunks[0].change_type}")
        parts.append("")

        for hunk in file_hunks:
            parts.append(f"```{language}")
            parts.append(hunk.hunk_header)
            parts.append(hunk.raw_diff.rstrip())
            parts.append("```")
            parts.append("")

    result = '\n'.join(parts)

    if len(result) > MAX_CHARS:
        result = result[:MAX_CHARS] + '\n\n[... diff truncated at 80k chars ...]'

    return result
