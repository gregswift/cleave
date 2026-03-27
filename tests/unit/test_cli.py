"""Unit tests for the CLI (no ffmpeg required)."""

from __future__ import annotations

from click.testing import CliRunner

from cleave import __version__
from cleave.cli import main

runner = CliRunner()


class TestHelpAndVersion:
    def test_help_flag(self) -> None:
        result = runner.invoke(main, ["-h"])
        assert result.exit_code == 0
        assert "Split m4b audiobook" in result.output

    def test_version_flag(self) -> None:
        result = runner.invoke(main, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestInputValidation:
    def test_no_arguments_shows_usage(self) -> None:
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_nonexistent_file(self) -> None:
        result = runner.invoke(main, ["nonexistent.m4b"])
        assert result.exit_code != 0

    def test_invalid_format(self) -> None:
        result = runner.invoke(main, ["--format", "wav", "dummy.m4b"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_invalid_quality(self) -> None:
        result = runner.invoke(main, ["--quality", "99", "dummy.m4b"])
        assert result.exit_code != 0
