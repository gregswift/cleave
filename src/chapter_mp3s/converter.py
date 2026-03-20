"""ffmpeg orchestration: extract and transcode per-chapter audio files."""

from __future__ import annotations

from pathlib import Path

from .chapters import Chapter, extract_chapters
from .metadata import read_book_tags, write_aac_tags, write_tags

#: Supported output formats.
FORMATS = ("mp3", "aac")

#: Maps output format to file extension.
EXTENSIONS: dict[str, str] = {
    "mp3": ".mp3",
    "aac": ".m4a",
}


def convert_file(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    fmt: str = "mp3",
    quality: int = 2,
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[Path]:
    """Convert an m4b audiobook file into per-chapter audio files.

    For each chapter marker found in *input_path*, a separate audio file is
    written to *output_dir* named ``"{index:02d} - {title}.{ext}"``.

    When *fmt* is ``"mp3"`` the audio is transcoded from AAC to MP3 using
    LAME VBR at the given *quality* level (0 = best, 9 = smallest).

    When *fmt* is ``"aac"`` the AAC stream is remuxed into an ``.m4a``
    container with no re-encoding (lossless chapter extraction).

    If the file contains no chapter markers the entire file is treated as a
    single track (index 1, title taken from the file's title tag or the stem
    of the filename).

    Args:
        input_path: Path to the source ``.m4b`` file.
        output_dir: Directory in which to write output files.  Defaults to
                    the same directory as *input_path*.
        fmt:        Output format — ``"mp3"`` (default) or ``"aac"``.
        quality:    MP3 VBR quality level 0–9 (ignored for ``"aac"`` format).
                    Lower values produce larger, higher-quality files.
        dry_run:    If ``True``, log what would be done but do not write any
                    files or call ffmpeg.
        overwrite:  If ``True``, overwrite existing output files.  If
                    ``False`` (default), skip chapters that already have an
                    output file.

    Returns:
        List of :class:`pathlib.Path` objects for every output file written
        (or that *would* be written in dry-run mode).

    Raises:
        FileNotFoundError: If *input_path* does not exist, or if ``ffmpeg``
                           is not found on ``PATH``.
        ValueError:        If *fmt* is not a recognised format, if *quality*
                           is outside 0–9, or if ffmpeg exits non-zero.
    """
    raise NotImplementedError


def _build_ffmpeg_cmd(
    input_path: Path,
    chapter: Chapter,
    output_path: Path,
    *,
    fmt: str,
    quality: int,
    overwrite: bool,
) -> list[str]:
    """Build the ffmpeg argument list for a single chapter extraction.

    Args:
        input_path:  Source file.
        chapter:     Chapter to extract.
        output_path: Destination file.
        fmt:         ``"mp3"`` or ``"aac"``.
        quality:     VBR quality level (mp3 only).
        overwrite:   Whether to pass ``-y`` to ffmpeg.

    Returns:
        List of strings suitable for passing to :func:`subprocess.run`.
    """
    raise NotImplementedError


def _run_ffmpeg(cmd: list[str]) -> None:
    """Execute an ffmpeg command, raising on failure.

    Args:
        cmd: Full argument list including the ``ffmpeg`` binary.

    Raises:
        FileNotFoundError: If ffmpeg is not on PATH.
        ValueError:        If ffmpeg exits with a non-zero return code.
    """
    raise NotImplementedError
