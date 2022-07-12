# -*- coding: utf-8 -*-
import pathlib
import stat
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest
from plumbum import local

from drakkar.get_url import Downloader
from drakkar.pre_flight import PreFlight


def test_home_bin():
    with patch.object(pathlib.Path, "is_dir", lambda _: False):
        with patch.object(pathlib.Path, "mkdir", lambda _: False):
            _bin = pathlib.Path.home() / "bin"
            if _bin in local.env.path:  # pragma: no cover
                local.env.path.remove(_bin)
            assert _bin not in local.env.path  # Just to make sure…
            _ = PreFlight()  # No need to keep the instance.
            assert _bin in local.env.path


@pytest.fixture
def preflight():
    with patch.object(pathlib.Path, "is_dir", lambda _: True):
        # Tests should never create a real directory.
        return PreFlight()


def test_goss_version_good(preflight):
    def _side_efect(cmd):  # pragma: no cover
        if "--version" in cmd:
            return "goss version v0.3.16\n"
        pytest.fail("Unexpected call to goss")  # Fail safe!

    mgoss = MagicMock(side_effect=_side_efect)
    preflight._downloader = MagicMock(spec=Downloader)
    with patch("drakkar.pre_flight.local") as mlocal:
        mlocal.__getitem__.return_value = mgoss
        assert preflight.goss is mgoss
        assert not preflight._downloader.fetch.called


def test_goss_version_bad(preflight):
    def _side_efect(cmd):  # pragma: no cover
        if "--version" in cmd:
            return "goß älért"  # Non chance!
        pytest.fail("Unexpected call to goss")  # Fail safe!

    mgoss = MagicMock(side_effect=_side_efect)
    preflight._downloader = MagicMock(spec=Downloader)
    with patch.object(pathlib.Path, "chmod", lambda _, x: x == stat.S_IRWXU):
        with patch("drakkar.pre_flight.local") as mlocal:
            mlocal.__getitem__.return_value = mgoss
            assert preflight.goss is mgoss
            assert preflight._downloader.fetch.called


def test_PreFlight_goss_is_cached(preflight):
    mgoss = MagicMock(spec=local)
    preflight._goss = mgoss
    assert preflight.goss is mgoss


@pytest.fixture
def mock_preflight():
    with patch(
        "drakkar.pre_flight.PreFlight.goss", new_callable=PropertyMock
    ) as mock_goss:
        preflight = PreFlight()
        mgoss = MagicMock(spec=local)
        mock_goss.return_value = mgoss
        assert preflight.goss is mgoss
        return preflight


def test_security(mock_preflight):
    mock_preflight._run = Mock(return_value=0)
    assert mock_preflight.security() == 0
    mock_preflight._run.assert_called_once_with("security")


def test_infrastructure(mock_preflight):
    mock_preflight._run = Mock(return_value=13)
    assert mock_preflight.infrastructure() == 13
    mock_preflight._run.assert_called_once_with("infrastructure")


@pytest.mark.parametrize(
    "is_file,retcode",
    [
        (True, 1),
        (False, 0),
    ],
)
def test_run(is_file, retcode, mock_preflight):
    with patch(
        "drakkar.pre_flight.PreFlight.goss", new_callable=PropertyMock
    ) as mock_goss:
        with patch.object(pathlib.Path, "is_file", lambda _: is_file):
            turtle = Mock()
            turtle.run = Mock(return_value=(retcode, "stdout", "stderr"))
            mgoss = MagicMock(
                spec=local, return_value=Mock(return_value=turtle)
            )
            mock_goss.return_value = mgoss
            mock_preflight._downloader.fetch = Mock()
            assert mock_preflight._run("security") == retcode
            mgoss.assert_called_once_with(
                "-g",
                (pathlib.Path.home() / "goss-security.yaml").as_posix(),
                "validate",
                "--format",
                "documentation",
                "--no-color",
            )
            # If is_file is true, then we do not need to fetch it!
            assert mock_preflight._downloader.fetch is not is_file