"""Tests for ID3 and MP4 tag writing."""

from __future__ import annotations

import pytest

from chapter_mp3s.chapters import Chapter
from chapter_mp3s.metadata import read_book_tags, write_aac_tags, write_tags


CHAPTER = Chapter(index=2, title="Chapter One", start=3.0, end=7.0)
BOOK_TITLE = "My Great Audiobook"
AUTHOR = "Jane Author"
TRACK_TOTAL = 5


class TestWriteTags:
    def test_missing_file_raises(self, tmp_path: "Path") -> None:
        missing = tmp_path / "ghost.mp3"
        with pytest.raises(FileNotFoundError):
            write_tags(
                missing,
                CHAPTER,
                book_title=BOOK_TITLE,
                author=AUTHOR,
                track_total=TRACK_TOTAL,
            )


class TestWriteAacTags:
    def test_missing_file_raises(self, tmp_path: "Path") -> None:
        missing = tmp_path / "ghost.m4a"
        with pytest.raises(FileNotFoundError):
            write_aac_tags(
                missing,
                CHAPTER,
                book_title=BOOK_TITLE,
                author=AUTHOR,
                track_total=TRACK_TOTAL,
            )


class TestReadBookTags:
    def test_missing_file_raises(self, tmp_path: "Path") -> None:
        missing = tmp_path / "ghost.m4b"
        with pytest.raises(FileNotFoundError):
            read_book_tags(missing)
