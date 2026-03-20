"""Chapter extraction from m4b files via ffprobe."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


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
        FileNotFoundError: If ``ffprobe`` is not found on ``PATH``.
        ValueError:        If ``ffprobe`` exits with a non-zero status or
                           returns unexpected output.
    """
    raise NotImplementedError


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
    raise NotImplementedError


def _parse_ffprobe_json(json_text: str) -> list[Chapter]:
    """Parse ffprobe chapter JSON into a list of Chapter objects.

    Args:
        json_text: Raw JSON string as returned by ffprobe ``-show_chapters``.

    Returns:
        Ordered list of :class:`Chapter` objects.

    Raises:
        ValueError: If the JSON is malformed or missing expected keys.
    """
    raise NotImplementedError
