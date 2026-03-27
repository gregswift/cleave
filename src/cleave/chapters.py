"""Chapter extraction from m4b files via ffprobe."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: Default filename template for output files.
DEFAULT_TEMPLATE = "{book}-Chapter_{index:03d}"


def sanitize_for_filename(value: str, delimiter: str = "_") -> str:
    """Make a string safe for use in filenames.

    Colons are converted to hyphens (they often act as semantic separators in
    titles).  Other filesystem-unsafe characters and whitespace are replaced
    with *delimiter*.  Consecutive delimiters are collapsed and
    leading/trailing delimiters, dots, and spaces are stripped.

    Args:
        value:     The raw string to sanitize.
        delimiter: Character used to replace spaces and unsafe characters.
    """
    # Colons → hyphen (semantic separator, not junk); consume trailing space
    sanitized = re.sub(r":\s*", "-", value)
    # Replace remaining unsafe chars with the delimiter
    sanitized = re.sub(r'[<>"/\\|?*\x00-\x1f]', delimiter, sanitized)
    sanitized = sanitized.replace(" ", delimiter)
    # Collapse runs of the delimiter
    if delimiter:
        sanitized = re.sub(re.escape(delimiter) + r"+", delimiter, sanitized)
    sanitized = sanitized.strip(f"{delimiter}. ")
    return sanitized


def format_stem(
    template: str,
    *,
    book_title: str,
    chapter: Chapter,
    delimiter: str = "_",
) -> str:
    """Format a filename template with chapter and book metadata.

    Supported placeholders:
        ``{book}``   — sanitized book title
        ``{title}``  — sanitized chapter title
        ``{index}``  — 1-based chapter number (supports format specs, e.g. ``{index:03d}``)

    Args:
        template:    A Python format string.
        book_title:  The book's title tag (sanitized automatically).
        chapter:     The chapter to format for.
        delimiter:   Passed through to :func:`sanitize_for_filename`.

    Returns:
        The formatted filename stem (no extension).
    """
    return template.format(
        book=sanitize_for_filename(book_title, delimiter),
        title=sanitize_for_filename(chapter.title, delimiter),
        index=chapter.index,
    )


@dataclass(frozen=True)
class Chapter:
    """A single chapter extracted from an audiobook file.

    Attributes:
        index:    1-based track number.
        title:    Chapter title as stored in the file metadata.
        start:    Start time in seconds from the beginning of the file.
        end:      End time in seconds from the beginning of the file.
    """

    index: int
    title: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        """Duration of the chapter in seconds."""
        return self.end - self.start

    def safe_title(self) -> str:
        """Return a filesystem-safe version of the chapter title.

        Strips or replaces characters that are invalid in filenames on
        Windows, macOS, and Linux.
        """
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", self.title)
        sanitized = sanitized.strip(". ")
        return sanitized or f"Chapter {self.index:02d}"

    def output_stem(self) -> str:
        """Return the suggested output filename stem (no extension).

        Format: ``{index:02d} - {safe_title}``
        """
        return f"{self.index:02d} - {self.safe_title()}"


def extract_chapters(path: str | Path) -> list[Chapter]:
    """Extract chapter metadata from an m4b (or any MPEG-4) file.

    Uses ``ffprobe`` to read chapter markers embedded in the file container.
    If the file contains no chapter markers an empty list is returned; the
    caller is responsible for deciding how to handle that case (e.g. treat
    the whole file as a single track).

    Args:
        path: Path to the input audio file.

    Returns:
        Ordered list of :class:`Chapter` objects, one per chapter marker.

    Raises:
        FileNotFoundError: If ``path`` does not exist, or if ``ffprobe`` is
                           not found on ``PATH``.
        ValueError:        If ``ffprobe`` exits with a non-zero status or
                           returns unexpected output.
    """
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Input file not found: {resolved}")
    json_text = _run_ffprobe(resolved)
    return _parse_ffprobe_json(json_text)


def _run_ffprobe(path: Path) -> str:
    """Invoke ffprobe and return its JSON output as a string.

    Args:
        path: Path to the audio file to probe.

    Returns:
        Raw JSON string from ffprobe.

    Raises:
        FileNotFoundError: If ffprobe is not on PATH.
        ValueError:        If ffprobe exits non-zero.
    """
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_chapters",
        str(path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, check=False
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffprobe not found. Please install ffmpeg: https://ffmpeg.org/download.html"
        ) from None

    if result.returncode != 0:
        raise ValueError(
            f"ffprobe exited with status {result.returncode}:\n{result.stderr.strip()}"
        )
    return result.stdout


def _parse_ffprobe_json(json_text: str) -> list[Chapter]:
    """Parse ffprobe chapter JSON into a list of Chapter objects.

    Args:
        json_text: Raw JSON string as returned by ffprobe ``-show_chapters``.

    Returns:
        Ordered list of :class:`Chapter` objects.

    Raises:
        ValueError: If the JSON is malformed or missing expected keys.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"ffprobe returned invalid JSON: {exc}") from exc

    if "chapters" not in data:
        raise ValueError(f"ffprobe JSON missing 'chapters' key. Got keys: {list(data.keys())}")

    chapters: list[Chapter] = []
    for i, raw in enumerate(data["chapters"], start=1):
        tags = raw.get("tags", {})
        title = tags.get("title", "")
        start = float(raw["start_time"])
        end = float(raw["end_time"])
        chapters.append(Chapter(index=i, title=title, start=start, end=end))

    return chapters
