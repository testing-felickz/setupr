# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""Wrapper to all console output."""

from rich.console import Console

# https://www.nordtheme.com/docs/colors-and-palettes
COLOUR_FAIL = "#bf616a"
COLOUR_INFO = "#5e81ac"
COLOUR_NOTE = "#81a1c1"
COLOUR_SUCC = "#a3be8c"
COLOUR_WARN = "#d08770"
COLOUR_GREY = "#777777"


def wprint(text: str, level: str = "") -> None:
    """Print wrapper.

    If there is no level, we just print it with whatever markup.
    """
    console = Console()
    if level == "note":
        console.print(f"   {text}", style=COLOUR_NOTE)
    elif level == "info":
        console.print(f":thumbs_up: {text}", style=COLOUR_INFO)
    elif level == "warning":
        console.print(f":warning-emoji:  {text}", style=COLOUR_WARN)
    elif level == "success":
        console.print(f":heavy_check_mark:  {text}", style=COLOUR_SUCC)
    elif level == "failure":
        console.print(f":x: {text}", style=COLOUR_FAIL)
    else:
        console.print(f"   {text}")


if __name__ == "__main__":  # pragma: no cover
    # We do not need to test any of this… It is just an example!
    # >>> python setupr/print.py
    TEXT = (
        "[i]I Am Malenia[/i], "
        "[b]Blade Of Miquella[/b], And "
        "[i][b]I Have Never Known Defeat.[/i][/b] "
        "[black]:skull:[/black]"
    )
    print("Nothing:   ", end="")
    wprint(f"{TEXT}")
    print("Note:      ", end="")
    wprint(f"{TEXT}", "note")
    print("Info:      ", end="")
    wprint(f"{TEXT}", "info")
    print("Success:   ", end="")
    wprint(f"{TEXT}", "success")
    print("Warning:   ", end="")
    wprint(f"{TEXT}", "warning")
    print("Failure:   ", end="")
    wprint(f"{TEXT}", "failure")
