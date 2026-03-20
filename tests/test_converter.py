"""Tests for ffmpeg orchestration."""

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


class TestConvertFile:
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

    @pytest.mark.integration
    def test_produces_correct_number_of_files(
        self, synthetic_m4b: Path, tmp_path: Path
    ) -> None:
        outputs = convert_file(synthetic_m4b, output_dir=tmp_path)
        assert len(outputs) == 3

    @pytest.mark.integration
    def test_output_filenames_match_chapters(
        self, synthetic_m4b: Path, tmp_path: Path
    ) -> None:
        outputs = convert_file(synthetic_m4b, output_dir=tmp_path)
        names = [p.name for p in outputs]
        assert names[0] == "01 - Introduction.mp3"
        assert names[1] == "01 - Chapter One.mp3"
        assert names[2] == "03 - Epilogue.mp3"

    @pytest.mark.integration
    def test_dry_run_writes_no_files(
        self, synthetic_m4b: Path, tmp_path: Path
    ) -> None:
        outputs = convert_file(synthetic_m4b, output_dir=tmp_path, dry_run=True)
        assert len(outputs) == 3
        for path in outputs:
            assert not path.exists()

    @pytest.mark.integration
    def test_skip_existing_by_default(
        self, synthetic_m4b: Path, tmp_path: Path
    ) -> None:
        convert_file(synthetic_m4b, output_dir=tmp_path)
        # Second run should not raise even without --overwrite
        convert_file(synthetic_m4b, output_dir=tmp_path)

    @pytest.mark.integration
    def test_aac_format_produces_m4a_files(
        self, synthetic_m4b: Path, tmp_path: Path
    ) -> None:
        outputs = convert_file(synthetic_m4b, output_dir=tmp_path, fmt="aac")
        assert all(p.suffix == ".m4a" for p in outputs)
