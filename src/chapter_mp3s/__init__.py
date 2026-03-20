"""chapter-mp3s: Split m4b audiobooks into per-chapter audio files."""

__version__ = "0.1.0"

from .chapters import Chapter, extract_chapters
from .converter import convert_file

__all__ = [
    "__version__",
    "Chapter",
    "extract_chapters",
    "convert_file",
]
