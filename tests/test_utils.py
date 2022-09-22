# -*- coding: utf-8 -*-
"""Utilities."""
from pathlib import Path

import pytest  # type: ignore

from setupr.utils import join_with_oxford_commas


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
