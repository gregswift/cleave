"""Command-line interface for chapter-mp3s."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from . import __version__
from .converter import FORMATS, convert_file

console = Console(stderr=True)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version")
@click.argument(
    "inputs",
    nargs=-1,
    required=True,
    metavar="INPUT...",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=None,
    metavar="DIR",
    help="Directory for output files. Defaults to the same directory as each input.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(list(FORMATS), case_sensitive=False),
    default="mp3",
    show_default=True,
    help=(
        "Output format. 'mp3' transcodes to MP3 (universal compatibility). "
        "'aac' remuxes chapters losslessly into .m4a files (no re-encoding)."
    ),
)
@click.option(
    "--quality",
    type=click.IntRange(0, 9),
    default=2,
    show_default=True,
    metavar="0-9",
    help="MP3 VBR quality level. 0 = best quality / largest file, 9 = smallest. Ignored for --format aac.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be done without writing any files.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing output files. By default existing files are skipped.",
)
def main(
    inputs: tuple[Path, ...],
    output_dir: Path | None,
    fmt: str,
    quality: int,
    dry_run: bool,
    overwrite: bool,
) -> None:
    """Split m4b audiobook files into per-chapter audio files.

    Reads chapter markers from each INPUT file and writes one output file per
    chapter, named "01 - Chapter Title.mp3" (or .m4a for --format aac).

    \b
    Examples:
      chapter-mp3s book.m4b
      chapter-mp3s --format aac --output-dir ./out book.m4b
      chapter-mp3s --quality 0 --overwrite *.m4b
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
