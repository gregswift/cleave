"""Unit tests for ffmpeg command building and input validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from chapter_mp3s.chapters import Chapter
from chapter_mp3s.converter import _build_ffmpeg_cmd, convert_file


CHAPTER = Chapter(index=1, title="Introduction", start=0.0, end=3.0)


class TestBuildFfmpegCmd:
    def test_mp3_includes_libmp3lame(self, tmp_path: Path) -> None:
        cmd = _build_ffmpeg_cmd(
            Path("book.m4b"),
            CHAPTER,
            tmp_path / "01 - Introduction.mp3",
            fmt="mp3",
            quality=2,
            overwrite=False,
        )
        assert "libmp3lame" in cmd

    def test_aac_uses_copy_codec(self, tmp_path: Path) -> None:
        cmd = _build_ffmpeg_cmd(
            Path("book.m4b"),
            CHAPTER,
            tmp_path / "01 - Introduction.m4a",
            fmt="aac",
            quality=2,
            overwrite=False,
        )
        assert "copy" in cmd

    def test_overwrite_flag_included(self, tmp_path: Path) -> None:
        cmd = _build_ffmpeg_cmd(
            Path("book.m4b"),
            CHAPTER,
            tmp_path / "01.mp3",
            fmt="mp3",
            quality=2,
            overwrite=True,
        )
        assert "-y" in cmd

    def test_no_overwrite_flag_absent(self, tmp_path: Path) -> None:
        cmd = _build_ffmpeg_cmd(
            Path("book.m4b"),
            CHAPTER,
            tmp_path / "01.mp3",
            fmt="mp3",
            quality=2,
            overwrite=False,
        )
        assert "-y" not in cmd

    def test_start_and_duration_present(self, tmp_path: Path) -> None:
        cmd = _build_ffmpeg_cmd(
            Path("book.m4b"),
            CHAPTER,
            tmp_path / "01.mp3",
            fmt="mp3",
            quality=2,
            overwrite=False,
        )
        assert "-ss" in cmd
        assert "-t" in cmd

    def test_quality_level_applied(self, tmp_path: Path) -> None:
        cmd = _build_ffmpeg_cmd(
            Path("book.m4b"),
            CHAPTER,
            tmp_path / "01.mp3",
            fmt="mp3",
            quality=5,
            overwrite=False,
        )
        assert "5" in cmd


class TestConvertFileValidation:
    def test_invalid_format_raises(self, tmp_path: Path) -> None:
        fake_m4b = tmp_path / "book.m4b"
        fake_m4b.touch()
        with pytest.raises(ValueError, match="format"):
            convert_file(fake_m4b, fmt="wav")

    def test_invalid_quality_raises(self, tmp_path: Path) -> None:
        fake_m4b = tmp_path / "book.m4b"
        fake_m4b.touch()
        with pytest.raises(ValueError, match="quality"):
            convert_file(fake_m4b, quality=10)

    def test_missing_input_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            convert_file(tmp_path / "nonexistent.m4b")
