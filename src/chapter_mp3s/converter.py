"""ffmpeg orchestration: extract and transcode per-chapter audio files."""

from __future__ import annotations

import json
import subprocess
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
    if fmt not in FORMATS:
        raise ValueError(f"Invalid format {fmt!r}. Must be one of: {', '.join(FORMATS)}")
    if not 0 <= quality <= 9:
        raise ValueError(f"Invalid quality {quality!r}. Must be between 0 and 9 inclusive.")

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    resolved_output_dir = Path(output_dir) if output_dir is not None else input_path.parent
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    chapters = extract_chapters(input_path)
    if not chapters:
        book_tags = read_book_tags(input_path)
        title = book_tags["title"] or input_path.stem
        duration = _get_duration(input_path)
        chapters = [Chapter(index=1, title=title, start=0.0, end=duration)]
    else:
        book_tags = read_book_tags(input_path)

    ext = EXTENSIONS[fmt]
    outputs: list[Path] = []

    for chapter in chapters:
        output_path = resolved_output_dir / f"{chapter.output_stem()}{ext}"
        outputs.append(output_path)

        if output_path.exists() and not overwrite:
            continue
        if dry_run:
            continue

        cmd = _build_ffmpeg_cmd(
            input_path, chapter, output_path,
            fmt=fmt, quality=quality, overwrite=overwrite,
        )
        _run_ffmpeg(cmd)

        if fmt == "mp3":
            write_tags(
                output_path, chapter,
                book_title=book_tags["title"],
                author=book_tags["author"],
                track_total=len(chapters),
            )
        else:
            write_aac_tags(
                output_path, chapter,
                book_title=book_tags["title"],
                author=book_tags["author"],
                track_total=len(chapters),
            )

    return outputs


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
    cmd = ["ffmpeg"]
    if overwrite:
        cmd.append("-y")

    cmd += [
        "-i", str(input_path),
        "-ss", str(chapter.start),
        "-t", str(chapter.duration),
    ]

    if fmt == "mp3":
        cmd += ["-c:a", "libmp3lame", "-q:a", str(quality)]
    else:
        cmd += ["-c:a", "copy"]

    cmd.append(str(output_path))
    return cmd


def _run_ffmpeg(cmd: list[str]) -> None:
    """Execute an ffmpeg command, raising on failure.

    Args:
        cmd: Full argument list including the ``ffmpeg`` binary.

    Raises:
        FileNotFoundError: If ffmpeg is not on PATH.
        ValueError:        If ffmpeg exits with a non-zero return code.
    """
    try:
        result = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL, check=False)
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffmpeg not found. Please install ffmpeg: https://ffmpeg.org/download.html"
        ) from None

    if result.returncode != 0:
        raise ValueError(
            f"ffmpeg exited with status {result.returncode}:\n"
            f"{result.stderr.decode(errors='replace').strip()}"
        )


def _get_duration(path: Path) -> float:
    """Return the total duration of an audio file in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(path),
        ],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    try:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise ValueError(f"Could not determine duration of {path}: {exc}") from exc
