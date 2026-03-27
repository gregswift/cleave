"""Command-line interface for cleave."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from . import __version__
from .chapters import DEFAULT_TEMPLATE, Chapter, extract_chapters
from .converter import FORMATS, convert_file

console = Console()
err_console = Console(stderr=True)


def _print_error(exc: Exception) -> None:
    err_console.print(f"  [red]error:[/red] {exc}")


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
    "--template",
    default=DEFAULT_TEMPLATE,
    show_default=True,
    help=(
        "Filename template. Placeholders: {book}, {title}, {index} "
        "(supports format specs, e.g. {index:03d})."
    ),
)
@click.option(
    "--delimiter",
    default="_",
    show_default=True,
    help=(
        "Character used within {book} and {title} values to replace spaces "
        "and unsafe characters. For example, a title 'Chapter One' becomes "
        "'Chapter_One' with the default delimiter. "
        "Colons are always converted to hyphens rather than the delimiter."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Print each chapter filename as it completes instead of showing a progress bar.",
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
    template: str,
    delimiter: str,
    verbose: bool,
    dry_run: bool,
    overwrite: bool,
) -> None:
    """Split m4b audiobook files into per-chapter audio files.

    Reads chapter markers from each INPUT file and writes one output file per
    chapter. The output filename is controlled by --template.

    \b
    Examples:
      cleave book.m4b
      cleave --format aac --output-dir ./out book.m4b
      cleave --quality 0 --overwrite *.m4b
      cleave --template '{index:02d} - {title}' --delimiter ' ' book.m4b
    """
    had_error = False

    for input_path in inputs:
        dest = str(output_dir) if output_dir else "current directory"
        dry_label = " [dim](dry run)[/dim]" if dry_run else ""
        console.print(f"\nCleaving [bold]{input_path.name}[/bold] to {dest}{dry_label}")

        if dry_run:
            try:
                outputs = convert_file(
                    input_path,
                    output_dir=output_dir,
                    fmt=fmt,
                    quality=quality,
                    template=template,
                    delimiter=delimiter,
                    dry_run=True,
                )
            except (FileNotFoundError, ValueError) as exc:
                _print_error(exc)
                had_error = True
                continue

            for path in outputs:
                console.print(f"  [dim]~[/dim] {path.name}")
            continue

        if verbose:

            def on_verbose_done(_chapter: Chapter, path: Path) -> None:
                console.print(f"  [green]✓[/green] {path.name}")

            try:
                convert_file(
                    input_path,
                    output_dir=output_dir,
                    fmt=fmt,
                    quality=quality,
                    template=template,
                    delimiter=delimiter,
                    overwrite=overwrite,
                    on_chapter_done=on_verbose_done,
                )
            except (FileNotFoundError, ValueError) as exc:
                _print_error(exc)
                had_error = True
            continue

        # Determine chapter count for the progress bar.
        try:
            chapters = extract_chapters(input_path)
        except (FileNotFoundError, ValueError) as exc:
            _print_error(exc)
            had_error = True
            continue

        total = len(chapters) if chapters else 1

        with Progress(
            TextColumn("  "),
            BarColumn(),
            MofNCompleteColumn(),
            console=err_console,
        ) as progress:
            task = progress.add_task("Converting", total=total)

            def on_chapter_done(_chapter: Chapter, _path: Path, _task: object = task) -> None:
                progress.advance(_task)

            try:
                outputs = convert_file(
                    input_path,
                    output_dir=output_dir,
                    fmt=fmt,
                    quality=quality,
                    template=template,
                    delimiter=delimiter,
                    overwrite=overwrite,
                    on_chapter_done=on_chapter_done,
                )
            except (FileNotFoundError, ValueError) as exc:
                _print_error(exc)
                had_error = True
                continue

        for path in outputs:
            console.print(f"  [green]✓[/green] {path.name}")

    if had_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
