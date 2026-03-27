"""Integration tests for the CLI (requires ffmpeg)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from cleave.cli import main


runner = CliRunner()


class TestDryRun:
    def test_dry_run_lists_files(self, synthetic_m4b: Path) -> None:
        result = runner.invoke(main, ["--dry-run", str(synthetic_m4b)])
        assert result.exit_code == 0
        assert "dry run" in result.output
        assert ".mp3" in result.output

    def test_dry_run_writes_nothing(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        result = runner.invoke(
            main, ["--dry-run", "-o", str(tmp_path), str(synthetic_m4b)]
        )
        assert result.exit_code == 0
        assert not list(tmp_path.glob("*.mp3"))


class TestVerbose:
    def test_verbose_prints_filenames(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        result = runner.invoke(
            main, ["-v", "-o", str(tmp_path), str(synthetic_m4b)]
        )
        assert result.exit_code == 0
        assert "✓" in result.output

    def test_verbose_creates_files(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        runner.invoke(main, ["-v", "-o", str(tmp_path), str(synthetic_m4b)])
        assert len(list(tmp_path.glob("*.mp3"))) == 3


class TestDefaultProgress:
    def test_creates_files(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        result = runner.invoke(main, ["-o", str(tmp_path), str(synthetic_m4b)])
        assert result.exit_code == 0
        assert len(list(tmp_path.glob("*.mp3"))) == 3

    def test_shows_checkmarks(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        result = runner.invoke(main, ["-o", str(tmp_path), str(synthetic_m4b)])
        assert "✓" in result.output


class TestOutputDir:
    def test_output_dir_in_header(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        result = runner.invoke(main, ["-o", str(tmp_path), "--dry-run", str(synthetic_m4b)])
        assert str(tmp_path) in result.output

    def test_current_directory_in_header(self, synthetic_m4b: Path) -> None:
        result = runner.invoke(main, ["--dry-run", str(synthetic_m4b)])
        assert "current directory" in result.output


class TestTemplateAndDelimiter:
    def test_custom_template(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            ["--template", "{index:02d}-{title}", "-o", str(tmp_path), str(synthetic_m4b)],
        )
        assert result.exit_code == 0
        names = sorted(p.name for p in tmp_path.glob("*.mp3"))
        assert names[0] == "01-Introduction.mp3"

    def test_custom_delimiter(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            ["--delimiter", "-", "-o", str(tmp_path), str(synthetic_m4b)],
        )
        assert result.exit_code == 0
        names = sorted(p.name for p in tmp_path.glob("*.mp3"))
        assert "Test-Audiobook" in names[0]


class TestOverwrite:
    def test_skips_existing_by_default(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        runner.invoke(main, ["-v", "-o", str(tmp_path), str(synthetic_m4b)])
        # Run again — should succeed but skip existing
        result = runner.invoke(main, ["-v", "-o", str(tmp_path), str(synthetic_m4b)])
        assert result.exit_code == 0

    def test_overwrite_flag(self, synthetic_m4b: Path, tmp_path: Path) -> None:
        runner.invoke(main, ["-v", "-o", str(tmp_path), str(synthetic_m4b)])
        result = runner.invoke(
            main, ["-v", "--overwrite", "-o", str(tmp_path), str(synthetic_m4b)]
        )
        assert result.exit_code == 0
        assert "✓" in result.output
