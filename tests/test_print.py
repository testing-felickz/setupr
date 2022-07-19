# -*- coding: utf-8 -*-
import pytest

from drakkar.print import wprint

TXT = "I Am Malenia, Blade Of Miquella, And I Have Never Known Defeat."
TXT_FMT = (
    "[i]I Am Malenia[/i], "
    "[b][red]Blade Of Miquella[/red][/b], And "
    "[i][b]I Have [blue]Never[/blue] Known Defeat.[/i][/b]"
    ":skull:"
)


@pytest.mark.parametrize(
    "level,extra,text",
    [
        (None, None, TXT),
        ("note", None, TXT),
        ("info", ":thumbs_up:", TXT),
        ("warning", ":warning-emoji:", TXT),
        ("success", ":heavy_check_mark:", TXT),
        ("failure", ":x:", TXT),
        (None, None, TXT_FMT),
        ("note", None, TXT_FMT),
        ("info", ":thumbs_up:", TXT_FMT),
        ("warning", ":warning-emoji:", TXT_FMT),
        ("success", ":heavy_check_mark:", TXT_FMT),
        ("failure", ":x:", TXT_FMT),
    ],
)
def test_wprint(level, extra, text, mock_console):
    wprint(text, level)
    assert mock_console.print.called
    assert text in mock_console.print.call_args.args[0]
    if extra is not None:
        assert extra in mock_console.print.call_args.args[0]
