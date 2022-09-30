# -*- coding: utf-8 -*-
"""Utilities."""
import enum
from typing import Any, Sequence

import requests

from setupr import __version__

GITHUB_URL = "https://api.github.com/repos/worldr/setupr/releases/latest"


class VersionCheck(enum.Enum):
    """Version check ENUM."""

    LATEST = enum.auto()
    LAGGING = enum.auto()
    UNKNOWN = enum.auto()


def join_with_oxford_commas(obj_list: Sequence[Any]) -> str:
    """Oxford commas for lists.

    Takes a list of objects and returns their string representations,
    separated by commas and with 'and' between the penultimate and final
    items
    """
    if not obj_list:
        return ""
    size = len(obj_list)
    if size == 1:
        return f"{str(obj_list[0])}"
    else:
        return (
            ", ".join(str(obj) for obj in obj_list[: size - 1])
            + f", and {str(obj_list[size - 1])}"
        )


def check_if_latest_version() -> VersionCheck:
    """Check if there is a new version published on GitHub."""
    response = requests.get(GITHUB_URL)
    if response.status_code == 200:
        latest_version = response.json()["tag_name"]
        if latest_version == f"v{__version__}":
            return VersionCheck.LATEST
        return VersionCheck.LAGGING
    return VersionCheck.UNKNOWN
