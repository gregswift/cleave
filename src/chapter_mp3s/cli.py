"""Command-line interface for chapter-mp3s."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from . import __version__
from .chapters import Chapter, extract_chapters
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
    help=(
        "MP3 VBR quality level. 0 = best quality / largest file, "
        "9 = smallest. Ignored for --format aac."
    ),
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
    had_error = False

    for input_path in inputs:
        dry_label = " [dim](dry run)[/dim]" if dry_run else ""
        console.print(f"\n[bold]{input_path.name}[/bold]{dry_label}")

        if dry_run:
            try:
                outputs = convert_file(
                    input_path,
                    output_dir=output_dir,
                    fmt=fmt,
                    quality=quality,
                    dry_run=True,
                )
            except (FileNotFoundError, ValueError) as exc:
                console.print(f"  [red]error:[/red] {exc}")
                had_error = True
                continue

            for path in outputs:
                console.print(f"  [dim]~[/dim] {path.name}")
            continue

        # Determine chapter count for the progress bar.
        try:
            chapters = extract_chapters(input_path)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"  [red]error:[/red] {exc}")
            had_error = True
            continue

        total = len(chapters) if chapters else 1

        with Progress(
            TextColumn("  "),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Converting", total=total)

            def on_chapter_done(_chapter: Chapter, _path: Path) -> None:
                progress.advance(task)

            try:
                outputs = convert_file(
                    input_path,
                    output_dir=output_dir,
                    fmt=fmt,
                    quality=quality,
                    overwrite=overwrite,
                    on_chapter_done=on_chapter_done,
                )
            except (FileNotFoundError, ValueError) as exc:
                console.print(f"  [red]error:[/red] {exc}")
                had_error = True
                continue

        for path in outputs:
            console.print(f"  [green]✓[/green] {path.name}")

    if had_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
