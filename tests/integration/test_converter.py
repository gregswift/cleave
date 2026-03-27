"""Integration tests for the full conversion pipeline."""

from __future__ import annotations

from pathlib import Path

from cleave.converter import convert_file


def test_produces_correct_number_of_files(synthetic_m4b: Path, tmp_path: Path) -> None:
    outputs = convert_file(synthetic_m4b, output_dir=tmp_path)
    assert len(outputs) == 3


def test_output_filenames_match_default_template(synthetic_m4b: Path, tmp_path: Path) -> None:
    outputs = convert_file(synthetic_m4b, output_dir=tmp_path)
    names = [p.name for p in outputs]
    assert names[0] == "Test_Audiobook-Chapter_001.mp3"
    assert names[1] == "Test_Audiobook-Chapter_002.mp3"
    assert names[2] == "Test_Audiobook-Chapter_003.mp3"


def test_dry_run_writes_no_files(synthetic_m4b: Path, tmp_path: Path) -> None:
    outputs = convert_file(synthetic_m4b, output_dir=tmp_path, dry_run=True)
    assert len(outputs) == 3
    for path in outputs:
        assert not path.exists()


def test_skip_existing_by_default(synthetic_m4b: Path, tmp_path: Path) -> None:
    convert_file(synthetic_m4b, output_dir=tmp_path)
    convert_file(synthetic_m4b, output_dir=tmp_path)


def test_aac_format_produces_m4a_files(synthetic_m4b: Path, tmp_path: Path) -> None:
    outputs = convert_file(synthetic_m4b, output_dir=tmp_path, fmt="aac")
    assert all(p.suffix == ".m4a" for p in outputs)
