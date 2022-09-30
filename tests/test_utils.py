# -*- coding: utf-8 -*-
"""Utilities."""
from pathlib import Path

import pytest
import requests_mock

from setupr import __version__
from setupr.utils import (
    GITHUB_URL,
    VersionCheck,
    check_if_latest_version,
    join_with_oxford_commas,
)


@pytest.mark.parametrize(
    ("items", "text"),
    [
        (("",), ""),
        (("apples",), "apples"),
        (("apples", "oranges"), "apples, and oranges"),
        (("apples", "oranges", "pears"), "apples, oranges, and pears"),
        ("abc", "a, b, and c"),
        ((1, 2, 3), "1, 2, and 3"),
        (
            (
                Path(""),
                Path(""),
                Path(""),
            ),
            "., ., and .",
        ),
    ],
)
def test_join_with_oxford_commas(items: tuple, text: str) -> None:
    assert join_with_oxford_commas(items) == text


@pytest.mark.parametrize(
    ("payload", "status", "expected"),
    [
        ({}, 500, VersionCheck.UNKNOWN),
        ({}, 404, VersionCheck.UNKNOWN),
        ({"tag_name": "v0.0.0"}, 200, VersionCheck.LAGGING),
        ({"tag_name": f"v{__version__}"}, 200, VersionCheck.LATEST),
    ],
)
def test_check_if_latest_version(
    payload: dict, status: int, expected: VersionCheck
) -> None:
    with requests_mock.Mocker() as mocked:
        mocked.get(GITHUB_URL, json=payload, status_code=status)
        assert check_if_latest_version() == expected
