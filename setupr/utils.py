# -*- coding: utf-8 -*-
"""Utilities."""
from typing import Any, Sequence


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
