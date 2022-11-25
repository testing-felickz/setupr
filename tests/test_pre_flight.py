# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
# type: ignore
import pathlib
import stat
from unittest.mock import MagicMock, Mock, PropertyMock, mock_open, patch

import pytest
from plumbum import ProcessExecutionError, local

from setupr.downloader import Downloader
from setupr.pre_flight import SHA256SUM, PreFlight


def test_home_bin():
    with patch.object(
        pathlib.Path, "is_dir", return_value=False
    ), patch.object(pathlib.Path, "mkdir", return_value=False):
        _bin = pathlib.Path.home() / "bin"
        if _bin in local.env.path:  # pragma: no cover
            local.env.path.remove(_bin)
        assert _bin not in local.env.path  # Just to make sure…
        _ = PreFlight()  # No need to keep the instance.
        assert _bin in local.env.path


@pytest.fixture()
def preflight():
    with patch.object(pathlib.Path, "is_dir", return_value=True):
        # Tests should never create a real directory.
        return PreFlight()


def test_goss_version_good(preflight):
    def _side_efect(cmd):  # pragma: no cover
        if "--version" in cmd:
            return "goss version v0.3.16\n"
        pytest.fail("Unexpected call to goss")  # Fail safe!

    mgoss = MagicMock(side_effect=_side_efect)
    preflight._downloader = MagicMock(spec=Downloader)
    with patch("setupr.pre_flight.local") as mlocal:
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
    with patch.object(
        pathlib.Path, "symlink_to", lambda x, _: "goss" in x.as_posix()
    ), patch.object(
        pathlib.Path, "chmod", lambda _, x: x == stat.S_IRWXU
    ), patch(
        "setupr.pre_flight.local"
    ) as mlocal:
        mlocal.__getitem__.return_value = mgoss
        assert preflight.goss is mgoss
        assert preflight._downloader.fetch.called


def test_pre_flight_goss_is_cached(preflight):
    mgoss = MagicMock(spec=local)
    preflight._goss = mgoss
    assert preflight.goss is mgoss


@pytest.fixture()
def mock_preflight():
    with patch(
        "setupr.pre_flight.PreFlight.goss", new_callable=PropertyMock
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
    "retcode",
    [
        (1),
        (0),
    ],
)
def test_run(retcode, mock_preflight):
    with patch(
        "setupr.pre_flight.PreFlight.goss", new_callable=PropertyMock
    ) as mock_goss:
        mgoss = MagicMock(spec=local)
        mgoss.run = Mock(return_value=(retcode, "", ""))
        mock_goss.return_value = mgoss
        mock_preflight._downloader.fetch = Mock()
        assert mock_preflight._run("security") == retcode
        mgoss.run.assert_called_once_with(
            (
                "-g",
                (
                    pathlib.Path.cwd()
                    / f"goss-security-{mock_preflight.OS_TYPE}.yaml"
                ).as_posix(),
                "validate",
                "--format",
                "documentation",
                "--no-color",
            )
        )
        # If is_file is true, then we do not need to fetch it!
        assert mock_preflight._downloader.fetch.called is True


@patch("setupr.pre_flight.PreFlight.goss", new_callable=PropertyMock)
@patch("setupr.pre_flight.take_backup")
def test_run_process_execution_error(m_take_backup, mock_goss, mock_preflight):
    mopen = mock_open()
    mfdopen = Mock()
    with patch("setupr.pre_flight.os.open", mfdopen), patch(
        "setupr.pre_flight.os.fdopen", mopen
    ):
        m_take_backup.return_value = "xUnitTest"
        mgoss = MagicMock(spec=local)
        mgoss.run = Mock(side_effect=ProcessExecutionError("", 1, "", ""))
        mock_goss.return_value = mgoss
        mock_preflight._downloader.fetch = Mock()
        assert mock_preflight._run("security") == 1
        mgoss.run.assert_called_once_with(
            (
                "-g",
                (
                    pathlib.Path.cwd()
                    / f"goss-security-{mock_preflight.OS_TYPE}.yaml"
                ).as_posix(),
                "validate",
                "--format",
                "documentation",
                "--no-color",
            )
        )
        # If is_file is true, then we do not need to fetch it!
        assert mock_preflight._downloader.fetch.called is True
        assert m_take_backup.called
        mfdopen.assert_called_once_with("xUnitTest", 66)
        assert mopen.called


@pytest.mark.parametrize(
    ("os_type", "expected"),
    [
        ("ms-windows", "Unknown"),
        ("rhel", "RHEL"),
        ("ubuntu", "Ubuntu"),
    ],
)
def test_os_type(os_type, expected):
    with patch.object(pathlib.Path, "is_dir", return_value=True), patch(
        "distro.id"
    ) as m_distro:
        # Tests should never create a real directory.
        m_distro.return_value = os_type
        sut = PreFlight()
        assert sut.OS_TYPE == expected
        assert f"goss-infrastructure-{expected}.yaml" in SHA256SUM
        assert f"goss-security-{expected}.yaml" in SHA256SUM
