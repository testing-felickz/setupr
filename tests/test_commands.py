# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

import pytest

from setupr.commands import pgp_key, pre_flight
from setupr.gpg import GPG
from setupr.pre_flight import PreFlight


@pytest.mark.parametrize(
    "key_exists,imported,expected",
    [
        (True, True, True),
        (False, True, True),
        (False, False, False),
    ],
)
def test_pgp_key(key_exists, imported, expected, mock_console):
    with patch("setupr.commands.GPG") as m_gpg:
        mocked = Mock(spec=GPG)
        mocked.worldr_key_exists.return_value = key_exists
        mocked.import_worldr_key.return_value = imported
        m_gpg.return_value = mocked
        assert pgp_key() is expected
        assert mock_console.print.called


@pytest.mark.parametrize(
    "sec,infra,expected",
    [
        (0, 0, True),
        (1, 0, True),
        (1, 1, False),
        (0, 1, False),
    ],
)
def test_pre_flight(sec, infra, expected, mock_console):
    with patch("setupr.commands.PreFlight") as m_pre_flight:
        mocked = Mock(spec=PreFlight)
        mocked.security.return_value = sec
        mocked.infrastructure.return_value = infra
        m_pre_flight.return_value = mocked
        assert pre_flight() is expected
        assert mock_console.print.called
