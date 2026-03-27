"""ID3 tag writing for output audio files via mutagen."""

from __future__ import annotations

from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError, TALB, TPE1, TRCK, TIT2
from mutagen.mp4 import MP4

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
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()

    tags.add(TIT2(encoding=3, text=chapter.title))
    tags.add(TRCK(encoding=3, text=f"{chapter.index}/{track_total}"))
    tags.add(TALB(encoding=3, text=book_title))
    tags.add(TPE1(encoding=3, text=author))
    tags.save(path)


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
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    audio = MP4(str(path))
    if audio.tags is None:
        audio.add_tags()

    audio.tags["\xa9nam"] = [chapter.title]  # Title
    audio.tags["trkn"] = [(chapter.index, track_total)]
    audio.tags["\xa9alb"] = [book_title]  # Album
    audio.tags["\xa9ART"] = [author]  # Artist
    audio.save()


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
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    audio = MP4(str(path))
    tags = audio.tags or {}
    title = str(tags.get("\xa9nam", [""])[0])
    author = str(tags.get("\xa9ART", [""])[0])
    return {"title": title, "author": author}
