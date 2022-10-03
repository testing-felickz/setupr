# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console


@pytest.fixture(autouse=True, scope="package")
def mock_console():
    with patch("setupr.print.Console") as mocked:
        console = MagicMock(spec=Console)
        console.print = MagicMock()
        mocked.return_value = console
        yield console
