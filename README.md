# cleave

Split m4b audiobook files into per-chapter audio files.

```
$ cleave "The Hobbit.m4b"

The Hobbit.m4b
  ✓ 01 - An Unexpected Party.mp3
  ✓ 02 - Roast Mutton.mp3
  ✓ 03 - A Short Rest.mp3
  ...
```

## Requirements

- Python 3.14+
- [ffmpeg](https://ffmpeg.org/download.html) on your `PATH`

## Installation

### pip

```sh
pip install cleave
```

### Container

No Python or ffmpeg installation needed — everything is bundled:

```sh
docker run --rm -v "$PWD":/data ghcr.io/gregswift/cleave /data/book.m4b
```

To write output to a specific directory on the host:

```sh
docker run --rm \
  -v "$PWD":/data \
  -v "$HOME/Audiobooks":/out \
  ghcr.io/gregswift/cleave -o /out /data/book.m4b
```

## Usage

### Basic

```sh
# Convert a single book (outputs mp3 files next to the input)
cleave book.m4b

# Convert multiple books at once
cleave book1.m4b book2.m4b

# Write output to a specific directory
cleave -o ~/Audiobooks/output book.m4b
```

### Format options

By default the tool transcodes AAC audio to MP3 for maximum player
compatibility. If your player supports AAC, use `--format aac` to remux
chapters losslessly with no re-encoding:

```sh
# MP3 (default) — transcodes, universally compatible
cleave book.m4b

# AAC — lossless remux, outputs .m4a files
cleave --format aac book.m4b
```

### MP3 quality

Quality is controlled with LAME VBR presets. Lower numbers are higher quality:

| `--quality` | Typical bitrate | Use case |
|:-----------:|:---------------:|---------|
| 0           | ~245 kbps       | Archival |
| 2 (default) | ~190 kbps       | Transparent to most ears |
| 5           | ~130 kbps       | Smaller files |
| 9           | ~65 kbps        | Smallest files |

```sh
cleave --quality 0 book.m4b   # best quality
cleave --quality 5 book.m4b   # smaller files
```

### Filename template

Output filenames are controlled by `--template`. The default produces names
like `The_Hobbit-Chapter_001.mp3`. Available placeholders:

| Placeholder | Description |
|-------------|-------------|
| `{book}`    | Sanitized book title from file metadata |
| `{title}`   | Sanitized chapter title |
| `{index}`   | Chapter number (supports format specs, e.g. `{index:03d}`) |

Spaces and unsafe filesystem characters inside `{book}` and `{title}` are
replaced with the `--delimiter` character (default `_`). Colons are always
converted to hyphens.

```sh
# Default template
cleave book.m4b
# → The_Hobbit-Chapter_001.mp3, The_Hobbit-Chapter_002.mp3, ...

# Classic "01 - Title" style with spaces
cleave --template '{index:02d} - {title}' --delimiter ' ' book.m4b
# → 01 - An Unexpected Party.mp3, 02 - Roast Mutton.mp3, ...

# Book and title with hyphens
cleave --template '{book}-{index:02d}-{title}' --delimiter '-' book.m4b
# → The-Hobbit-01-An-Unexpected-Party.mp3, ...
```

### Other options

```sh
# Preview what would be written without doing anything
cleave --dry-run book.m4b

# Overwrite files that already exist
cleave --overwrite book.m4b
```

## CLI reference

```
Usage: cleave [OPTIONS] INPUT...

  Split m4b audiobook files into per-chapter audio files.

  Reads chapter markers from each INPUT file and writes one output file per
  chapter. The output filename is controlled by --template.

  Examples:
    cleave book.m4b
    cleave --format aac --output-dir ./out book.m4b
    cleave --quality 0 --overwrite *.m4b
    cleave --template '{index:02d} - {title}' --delimiter ' ' book.m4b

Options:
  -o, --output-dir DIR    Directory for output files. Defaults to the same
                          directory as each input.
  --format [mp3|aac]      Output format. 'mp3' transcodes to MP3 (universal
                          compatibility). 'aac' remuxes chapters losslessly
                          into .m4a files (no re-encoding).  [default: mp3]
  --quality 0-9           MP3 VBR quality level. 0 = best quality / largest
                          file, 9 = smallest. Ignored for --format aac.
                          [default: 2]
  --template TEXT         Filename template. Placeholders: {book}, {title},
                          {index} (supports format specs, e.g. {index:03d}).
                          [default: {book}-Chapter_{index:03d}]
  --delimiter TEXT        Character used within {book} and {title} values to
                          replace spaces and unsafe characters. Colons are
                          always converted to hyphens.  [default: _]
  -v, --verbose           Print each chapter filename as it completes instead
                          of showing a progress bar.
  --dry-run               Show what would be done without writing any files.
  --overwrite             Overwrite existing output files. By default existing
                          files are skipped.
  -V, --version           Show the version and exit.
  -h, --help              Show this message and exit.
```

## Python API

The library can also be used directly from Python:

```python
from cleave import convert_file, extract_chapters

# Inspect chapters without converting
chapters = extract_chapters("book.m4b")
for ch in chapters:
    print(f"{ch.index:02d} - {ch.title} ({ch.duration:.0f}s)")

# Convert a file
outputs = convert_file(
    "book.m4b",
    output_dir="./out",
    fmt="mp3",
    quality=2,
)
```

## Files with no chapter markers

If an m4b file contains no chapter markers, the entire file is written as a
single track using the book title tag (or the filename stem if no title tag
is present).

## Development

Docker and GNU Make are required. No local Python installation needed.

```sh
# Set up the project (installs dependencies via uv in a container)
make setup

# Run all tests
make test

# Or run test suites separately
# Run unit tests (no ffmpeg required)
make test-unit

# Run integration tests (ffmpeg required inside the container)
make test-integration

# Lint (all linting)
make lint

# Build (both python and container)
make build
```

## Performance notes

Chapters are extracted concurrently using multiple ffmpeg processes. On
Linux this is typically fast. On macOS, running inside a container
(Docker/Podman) can be significantly slower due to the overhead of
file I/O through the container VM's filesystem bridge. For best
performance on macOS, install and run natively rather than via the
container image.

## License

[GNU General Public License v3.0](LICENSE)
