"""Shared pytest fixtures."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_FFPROBE_JSON = json.dumps({
    "chapters": [
        {
            "id": 0,
            "time_base": "1/1000",
            "start": 0,
            "start_time": "0.000000",
            "end": 3000,
            "end_time": "3.000000",
            "tags": {"title": "Introduction"},
        },
        {
            "id": 1,
            "time_base": "1/1000",
            "start": 3000,
            "start_time": "3.000000",
            "end": 7000,
            "end_time": "7.000000",
            "tags": {"title": "Chapter One"},
        },
        {
            "id": 2,
            "time_base": "1/1000",
            "start": 7000,
            "start_time": "7.000000",
            "end": 10000,
            "end_time": "10.000000",
            "tags": {"title": "Epilogue"},
        },
    ]
})

EMPTY_CHAPTERS_JSON = json.dumps({"chapters": []})

NO_TITLE_CHAPTERS_JSON = json.dumps({
    "chapters": [
        {
            "id": 0,
            "time_base": "1/1000",
            "start": 0,
            "start_time": "0.000000",
            "end": 5000,
            "end_time": "5.000000",
            "tags": {},
        },
    ]
})


# ---------------------------------------------------------------------------
# Unit test fixtures (no ffmpeg required)
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_ffprobe_json() -> str:
    """Raw ffprobe JSON with three well-formed chapters."""
    return SAMPLE_FFPROBE_JSON


@pytest.fixture()
def empty_chapters_json() -> str:
    """Raw ffprobe JSON with no chapter markers."""
    return EMPTY_CHAPTERS_JSON


@pytest.fixture()
def no_title_chapters_json() -> str:
    """Raw ffprobe JSON where chapters have no title tag."""
    return NO_TITLE_CHAPTERS_JSON


# ---------------------------------------------------------------------------
# Integration test fixtures (require ffmpeg on PATH)
# ---------------------------------------------------------------------------

def _ffmpeg_available() -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            capture_output=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


requires_ffmpeg = pytest.mark.skipif(
    not _ffmpeg_available(),
    reason="ffmpeg not found on PATH",
)


@pytest.fixture(scope="session")
@pytest.mark.integration
def synthetic_m4b(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a tiny 10-second silent m4b with three chapter markers.

    Requires ffmpeg. The file is created once per test session and reused
    across all integration tests.
    """
    out_dir = tmp_path_factory.mktemp("fixtures")
    metadata_file = out_dir / "chapters.txt"
    m4b_path = out_dir / "sample.m4b"

    # ffmpeg metadata format for chapter markers
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
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "10",
            "-i", str(metadata_file),
            "-map_metadata", "1",
            "-c:a", "aac",
            "-b:a", "32k",
            str(m4b_path),
        ],
        check=True,
        capture_output=True,
    )

    return m4b_path
