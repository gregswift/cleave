"""ffmpeg orchestration: extract and transcode per-chapter audio files."""

from __future__ import annotations

import json
import os
import subprocess
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .chapters import DEFAULT_TEMPLATE, Chapter, extract_chapters, format_stem
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
    template: str = DEFAULT_TEMPLATE,
    delimiter: str = "_",
    dry_run: bool = False,
    overwrite: bool = False,
    on_chapter_done: Callable[[Chapter, Path], None] | None = None,
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
        template:   Python format string for output filenames.  Placeholders:
                    ``{book}``, ``{title}``, ``{index}`` (supports format
                    specs like ``{index:03d}``).
        delimiter:  Character that replaces spaces and unsafe characters in
                    the sanitized ``{book}`` and ``{title}`` values.
        dry_run:    If ``True``, log what would be done but do not write any
                    files or call ffmpeg.
        overwrite:  If ``True``, overwrite existing output files.  If
                    ``False`` (default), skip chapters that already have an
                    output file.
        on_chapter_done: Optional callback invoked after each chapter is
                    converted, called with ``(chapter, output_path)``.
                    Called from worker threads — must be thread-safe.

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
    book_tags = read_book_tags(input_path)
    book_title = book_tags["title"] or input_path.stem

    if not chapters:
        duration = _get_duration(input_path)
        chapters = [Chapter(index=1, title=book_title, start=0.0, end=duration)]

    ext = EXTENSIONS[fmt]
    track_total = len(chapters)

    # Build the full output list up-front (deterministic order) and identify
    # which chapters actually need conversion.
    work: list[tuple[Chapter, Path]] = []
    outputs: list[Path] = []
    for chapter in chapters:
        stem = format_stem(template, book_title=book_title, chapter=chapter, delimiter=delimiter)
        output_path = resolved_output_dir / f"{stem}{ext}"
        outputs.append(output_path)

        if output_path.exists() and not overwrite:
            continue
        if dry_run:
            continue
        work.append((chapter, output_path))

    if work:
        max_workers = min(len(work), os.cpu_count() or 4)
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    _convert_chapter,
                    input_path,
                    chapter,
                    output_path,
                    fmt=fmt,
                    quality=quality,
                    overwrite=overwrite,
                    book_title=book_title,
                    author=book_tags["author"],
                    track_total=track_total,
                    on_done=on_chapter_done,
                ): chapter
                for chapter, output_path in work
            }
            try:
                for future in as_completed(futures):
                    future.result()
            except KeyboardInterrupt:
                _kill_active_procs()
                for future in futures:
                    future.cancel()
                raise

    return outputs


def _convert_chapter(
    input_path: Path,
    chapter: Chapter,
    output_path: Path,
    *,
    fmt: str,
    quality: int,
    overwrite: bool,
    book_title: str,
    author: str,
    track_total: int,
    on_done: Callable[[Chapter, Path], None] | None = None,
) -> None:
    """Extract and tag a single chapter. Designed to run in a thread pool."""
    cmd = _build_ffmpeg_cmd(
        input_path,
        chapter,
        output_path,
        fmt=fmt,
        quality=quality,
        overwrite=overwrite,
    )
    complete = False
    try:
        _run_ffmpeg(cmd)

        if fmt == "mp3":
            write_tags(
                output_path,
                chapter,
                book_title=book_title,
                author=author,
                track_total=track_total,
            )
        else:
            write_aac_tags(
                output_path,
                chapter,
                book_title=book_title,
                author=author,
                track_total=track_total,
            )
        complete = True
    finally:
        if not complete:
            output_path.unlink(missing_ok=True)

    if on_done is not None:
        on_done(chapter, output_path)


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
        "-ss",
        str(chapter.start),
        "-i",
        str(input_path),
        "-t",
        str(chapter.duration),
    ]

    if fmt == "mp3":
        cmd += ["-c:a", "libmp3lame", "-q:a", str(quality)]
    else:
        cmd += ["-c:a", "copy"]

    cmd.append(str(output_path))
    return cmd


# Active ffmpeg subprocesses, tracked so they can be killed on interrupt.
_active_procs: list[subprocess.Popen[bytes]] = []
_active_procs_lock = threading.Lock()


def _kill_active_procs() -> None:
    """Terminate all tracked ffmpeg subprocesses."""
    with _active_procs_lock:
        for proc in _active_procs:
            proc.terminate()
        _active_procs.clear()


def _run_ffmpeg(cmd: list[str]) -> None:
    """Execute an ffmpeg command, raising on failure.

    Args:
        cmd: Full argument list including the ``ffmpeg`` binary.

    Raises:
        FileNotFoundError: If ffmpeg is not on PATH.
        ValueError:        If ffmpeg exits with a non-zero return code.
    """
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffmpeg not found. Please install ffmpeg: https://ffmpeg.org/download.html"
        ) from None

    with _active_procs_lock:
        _active_procs.append(proc)
    try:
        _, stderr = proc.communicate()
    finally:
        with _active_procs_lock:
            if proc in _active_procs:
                _active_procs.remove(proc)

    if proc.returncode != 0:
        raise ValueError(
            f"ffmpeg exited with status {proc.returncode}:\n"
            f"{stderr.decode(errors='replace').strip()}"
        )


def _get_duration(path: Path) -> float:
    """Return the total duration of an audio file in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
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
