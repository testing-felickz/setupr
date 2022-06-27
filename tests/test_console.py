# -*- coding: utf-8 -*-
from click.testing import CliRunner

from drakkar.console import main


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "Drakkar ships the Worldr infrastructure" in result.output
