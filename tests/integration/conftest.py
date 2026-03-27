"""Integration test fixtures — require ffmpeg on PATH."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


if not _ffmpeg_available():
    collect_ignore_glob = ["*.py"]


@pytest.fixture(scope="session")
def synthetic_m4b(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a tiny 10-second silent m4b with three chapter markers.

    Created once per test session and reused across all integration tests.
    """
    out_dir = tmp_path_factory.mktemp("fixtures")
    metadata_file = out_dir / "chapters.txt"
    m4b_path = out_dir / "sample.m4b"

    metadata_file.write_text(
        ";FFMETADATA1\n"
        "title=Test Audiobook\n"
        "artist=Test Author\n"
        "\n"
        "[CHAPTER]\n"
        "TIMEBASE=1/1000\n"
        "START=0\n"
        "END=3000\n"
        "title=Introduction\n"
        "\n"
        "[CHAPTER]\n"
        "TIMEBASE=1/1000\n"
        "START=3000\n"
        "END=7000\n"
        "title=Chapter One\n"
        "\n"
        "[CHAPTER]\n"
        "TIMEBASE=1/1000\n"
        "START=7000\n"
        "END=10000\n"
        "title=Epilogue\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-t", "10", "-i", "anullsrc=r=44100:cl=mono",
            "-i", str(metadata_file),
            "-map_metadata", "1",
            "-c:a", "aac",
            "-b:a", "32k",
            str(m4b_path),
        ],
        check=True,
        capture_output=True,
        stdin=subprocess.DEVNULL,
    )

    return m4b_path
