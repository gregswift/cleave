# chapter-mp3s

Split m4b audiobook files into per-chapter audio files.

```
$ chapter-mp3s "The Hobbit.m4b"

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
pip install chapter-mp3s
```

### Container

No Python or ffmpeg installation needed — everything is bundled:

```sh
docker run --rm -v "$PWD":/data ghcr.io/gregswift/chapter-mp3s /data/book.m4b
```

To write output to a specific directory on the host:

```sh
docker run --rm \
  -v "$PWD":/data \
  -v "$HOME/Audiobooks":/out \
  ghcr.io/gregswift/chapter-mp3s -o /out /data/book.m4b
```

## Usage

### Basic

```sh
# Convert a single book (outputs mp3 files next to the input)
chapter-mp3s book.m4b

# Convert multiple books at once
chapter-mp3s book1.m4b book2.m4b

# Write output to a specific directory
chapter-mp3s -o ~/Audiobooks/output book.m4b
```

### Format options

By default the tool transcodes AAC audio to MP3 for maximum player
compatibility. If your player supports AAC, use `--format aac` to remux
chapters losslessly with no re-encoding:

```sh
# MP3 (default) — transcodes, universally compatible
chapter-mp3s book.m4b

# AAC — lossless remux, outputs .m4a files
chapter-mp3s --format aac book.m4b
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
chapter-mp3s --quality 0 book.m4b   # best quality
chapter-mp3s --quality 5 book.m4b   # smaller files
```

### Other options

```sh
# Preview what would be written without doing anything
chapter-mp3s --dry-run book.m4b

# Overwrite files that already exist
chapter-mp3s --overwrite book.m4b
```

## CLI reference

```
Usage: chapter-mp3s [OPTIONS] INPUT...

  Split m4b audiobook files into per-chapter audio files.

  Reads chapter markers from each INPUT file and writes one output file per
  chapter, named "01 - Chapter Title.mp3" (or .m4a for --format aac).

  Examples:
    chapter-mp3s book.m4b
    chapter-mp3s --format aac --output-dir ./out book.m4b
    chapter-mp3s --quality 0 --overwrite *.m4b

Options:
  -o, --output-dir DIR    Directory for output files. Defaults to the same
                          directory as each input.
  --format [mp3|aac]      Output format. 'mp3' transcodes to MP3 (universal
                          compatibility). 'aac' remuxes chapters losslessly
                          into .m4a files (no re-encoding).  [default: mp3]
  --quality 0-9           MP3 VBR quality level. 0 = best quality / largest
                          file, 9 = smallest. Ignored for --format aac.
                          [default: 2]
  --dry-run               Show what would be done without writing any files.
  --overwrite             Overwrite existing output files. By default existing
                          files are skipped.
  -V, --version           Show the version and exit.
  -h, --help              Show this message and exit.
```

## Python API

The library can also be used directly from Python:

```python
from chapter_mp3s import convert_file, extract_chapters

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

# Run unit tests (no ffmpeg required)
make test-unit

# Run integration tests (ffmpeg required inside the container)
make test-integration

# Lint
make lint-py

# Build
make build-python
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
