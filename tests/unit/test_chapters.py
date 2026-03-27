"""Tests for chapter extraction logic."""

from __future__ import annotations

import pytest

from cleave.chapters import (
    Chapter,
    _parse_ffprobe_json,
    extract_chapters,
    format_stem,
    sanitize_for_filename,
)


class TestChapterDataclass:
    def test_duration(self) -> None:
        ch = Chapter(index=1, title="Intro", start=0.0, end=5.0)
        assert ch.duration == pytest.approx(5.0)

    def test_frozen(self) -> None:
        ch = Chapter(index=1, title="Intro", start=0.0, end=5.0)
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            ch.index = 2  # type: ignore[misc]

    def test_output_stem_zero_pads_index(self) -> None:
        ch = Chapter(index=3, title="The Beginning", start=0.0, end=5.0)
        assert ch.output_stem() == "03 - The Beginning"

    def test_output_stem_double_digit_index(self) -> None:
        ch = Chapter(index=12, title="Finale", start=0.0, end=5.0)
        assert ch.output_stem() == "12 - Finale"


class TestSafeTitle:
    def test_clean_title_unchanged(self) -> None:
        ch = Chapter(index=1, title="Chapter One", start=0.0, end=5.0)
        assert ch.safe_title() == "Chapter One"

    def test_strips_invalid_characters(self) -> None:
        ch = Chapter(index=1, title='Bad/Name:Here"', start=0.0, end=5.0)
        result = ch.safe_title()
        assert "/" not in result
        assert ":" not in result
        assert '"' not in result

    def test_empty_title_falls_back_to_index(self) -> None:
        ch = Chapter(index=4, title="", start=0.0, end=5.0)
        assert ch.safe_title() == "Chapter 04"

    def test_whitespace_only_title_falls_back(self) -> None:
        ch = Chapter(index=2, title="   ", start=0.0, end=5.0)
        assert ch.safe_title() == "Chapter 02"

    def test_unicode_title_preserved(self) -> None:
        ch = Chapter(index=1, title="Ünïcödé Títlé", start=0.0, end=5.0)
        assert ch.safe_title() == "Ünïcödé Títlé"

    def test_leading_trailing_dots_stripped(self) -> None:
        ch = Chapter(index=1, title="...hidden", start=0.0, end=5.0)
        result = ch.safe_title()
        assert not result.startswith(".")


class TestParseFfprobeJson:
    def test_parses_three_chapters(self, sample_ffprobe_json: str) -> None:
        chapters = _parse_ffprobe_json(sample_ffprobe_json)
        assert len(chapters) == 3

    def test_chapter_indices_are_one_based(self, sample_ffprobe_json: str) -> None:
        chapters = _parse_ffprobe_json(sample_ffprobe_json)
        assert [ch.index for ch in chapters] == [1, 2, 3]

    def test_chapter_titles(self, sample_ffprobe_json: str) -> None:
        chapters = _parse_ffprobe_json(sample_ffprobe_json)
        assert chapters[0].title == "Introduction"
        assert chapters[1].title == "Chapter One"
        assert chapters[2].title == "Epilogue"

    def test_chapter_times(self, sample_ffprobe_json: str) -> None:
        chapters = _parse_ffprobe_json(sample_ffprobe_json)
        assert chapters[0].start == pytest.approx(0.0)
        assert chapters[0].end == pytest.approx(3.0)
        assert chapters[1].start == pytest.approx(3.0)

    def test_empty_chapters_returns_empty_list(self, empty_chapters_json: str) -> None:
        chapters = _parse_ffprobe_json(empty_chapters_json)
        assert chapters == []

    def test_missing_title_tag_uses_empty_string(self, no_title_chapters_json: str) -> None:
        chapters = _parse_ffprobe_json(no_title_chapters_json)
        assert len(chapters) == 1
        assert chapters[0].title == ""

    def test_malformed_json_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _parse_ffprobe_json("not json at all")

    def test_missing_chapters_key_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _parse_ffprobe_json('{"streams": []}')


class TestSanitizeForFilename:
    def test_spaces_become_delimiter(self) -> None:
        assert sanitize_for_filename("Chapter One") == "Chapter_One"

    def test_custom_delimiter(self) -> None:
        assert sanitize_for_filename("Chapter One", "-") == "Chapter-One"

    def test_colons_become_hyphens(self) -> None:
        assert sanitize_for_filename("Part 1: The Beginning") == "Part_1-The_Beginning"

    def test_colons_become_hyphens_regardless_of_delimiter(self) -> None:
        assert sanitize_for_filename("Part 1: The Beginning", " ") == "Part 1-The Beginning"

    def test_colon_without_space(self) -> None:
        assert sanitize_for_filename("Part 1:The Beginning") == "Part_1-The_Beginning"

    def test_unsafe_chars_replaced(self) -> None:
        assert sanitize_for_filename('Bad<>"/\\|?*Name') == "Bad_Name"

    def test_consecutive_delimiters_collapsed(self) -> None:
        assert sanitize_for_filename("too   many   spaces") == "too_many_spaces"

    def test_leading_trailing_stripped(self) -> None:
        assert sanitize_for_filename("  padded  ") == "padded"

    def test_dots_stripped(self) -> None:
        assert sanitize_for_filename("...hidden") == "hidden"


class TestFormatStem:
    def test_default_template(self) -> None:
        ch = Chapter(index=3, title="The Beginning", start=0.0, end=5.0)
        result = format_stem("{book}-Chapter_{index:03d}", book_title="My Book", chapter=ch)
        assert result == "My_Book-Chapter_003"

    def test_title_placeholder(self) -> None:
        ch = Chapter(index=1, title="An Unexpected Party", start=0.0, end=5.0)
        result = format_stem("{index:02d}-{title}", book_title="The Hobbit", chapter=ch)
        assert result == "01-An_Unexpected_Party"

    def test_custom_delimiter(self) -> None:
        ch = Chapter(index=1, title="Chapter One", start=0.0, end=5.0)
        result = format_stem("{book}-{title}", book_title="My Book", chapter=ch, delimiter="-")
        assert result == "My-Book-Chapter-One"

    def test_index_formatting(self) -> None:
        ch = Chapter(index=7, title="Test", start=0.0, end=5.0)
        assert format_stem("{index}", book_title="X", chapter=ch) == "7"
        assert format_stem("{index:02d}", book_title="X", chapter=ch) == "07"
        assert format_stem("{index:04d}", book_title="X", chapter=ch) == "0007"


class TestExtractChapters:
    def test_missing_ffprobe_raises_file_not_found(self, tmp_path: "Path") -> None:
        """extract_chapters should raise FileNotFoundError if ffprobe is absent."""
        pass  # placeholder — implemented alongside extract_chapters
