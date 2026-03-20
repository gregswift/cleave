"""ID3 tag writing for output audio files via mutagen."""

from __future__ import annotations

from pathlib import Path

from .chapters import Chapter


def write_tags(
    path: Path,
    chapter: Chapter,
    *,
    book_title: str,
    author: str,
    track_total: int,
) -> None:
    """Write ID3 tags to a transcoded mp3 file.

    Sets the following tags:
    - TIT2  (Title)       → chapter title
    - TRCK  (Track)       → ``{chapter.index}/{track_total}``
    - TALB  (Album)       → book title
    - TPE1  (Artist)      → author

    Args:
        path:        Path to the mp3 file to tag.
        chapter:     The chapter whose metadata should be applied.
        book_title:  Title of the audiobook (used as the album tag).
        author:      Author/narrator (used as the artist tag).
        track_total: Total number of chapters in the book.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        mutagen.MutagenError: If the file cannot be opened or written.
    """
    raise NotImplementedError


def write_aac_tags(
    path: Path,
    chapter: Chapter,
    *,
    book_title: str,
    author: str,
    track_total: int,
) -> None:
    """Write MP4/iTunes tags to an AAC (.m4a) output file.

    Sets the equivalent tags to :func:`write_tags` but using the MP4 tag
    format appropriate for ``.m4a`` files.

    Args:
        path:        Path to the m4a file to tag.
        chapter:     The chapter whose metadata should be applied.
        book_title:  Title of the audiobook.
        author:      Author/narrator.
        track_total: Total number of chapters in the book.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        mutagen.MutagenError: If the file cannot be opened or written.
    """
    raise NotImplementedError


def read_book_tags(path: Path) -> dict[str, str]:
    """Read top-level metadata tags from an m4b file.

    Extracts the book title and author from the source file so they can be
    propagated to the per-chapter output files without requiring the user to
    supply them manually.

    Args:
        path: Path to the source m4b file.

    Returns:
        Dict with keys ``"title"`` and ``"author"``.  Either value may be an
        empty string if the tag is absent from the file.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    raise NotImplementedError
