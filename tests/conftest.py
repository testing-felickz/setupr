# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console


@pytest.fixture(autouse=True, scope="package")
def mock_console():
    with patch("drakkar.print.Console") as mocked:
        console = MagicMock(spec=Console)
        console.print = MagicMock()
        mocked.return_value = console
        yield console
