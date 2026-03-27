"""Shared pytest fixtures."""

from __future__ import annotations

import json

import pytest

SAMPLE_FFPROBE_JSON = json.dumps(
    {
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
    }
)

EMPTY_CHAPTERS_JSON = json.dumps({"chapters": []})

NO_TITLE_CHAPTERS_JSON = json.dumps(
    {
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
    }
)


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
