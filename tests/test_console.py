# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
# type: ignore
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click import Option
from click.core import Context
from click.exceptions import UsageError
from click.testing import CliRunner

from setupr import __version__
from setupr.console import main, validate_semver
from setupr.downloader import Downloader
from setupr.gbucket import InstallationData
from setupr.utils import VersionCheck

SEMVER = "1.2.3"


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "Setupr ships the Worldr infrastructure" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0, f"CLI output: {result.output}"
    assert __version__ in result.output


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("-i", "-d"),
        ("-d", "-b"),
        ("-b", "-i"),
    ],
)
def test_mutually_exclusive(first, second):
    runner = CliRunner()
    result = runner.invoke(main, [first, SEMVER, second, SEMVER])
    assert result.exit_code == 2, f"CLI output: {result.output}"
    assert "Illegal usage" in result.output


@pytest.mark.parametrize(
    ("opt", "value"),
    [
        ("-i", "ook"),
        ("-b", "ook"),
        ("-d", "ook"),
        ("-i", "v1.2.3"),
        ("-i", "v 1.2.3"),
        ("-i", "1.2."),
    ],
)
def test_semver(opt, value):
    runner = CliRunner()
    result = runner.invoke(main, [opt, value])
    assert result.exit_code == 2, f"CLI output: {result.output}"
    assert "is not valid SemVer string" in result.output


@pytest.mark.parametrize(
    ("incoming", "expected", "error"),
    [
        (None, None, None),
        ("1.2.3", "1.2.3", None),
        ("ook", None, UsageError),
    ],
)
def test_verify_semver(incoming, expected, error):
    """We are just testing that the callback works.

    We are not doing an exhaustive test of semver!
    """
    ctx = Mock(spec=Context)
    prm = Mock(spec=Option)
    if error is None:
        assert validate_semver(ctx, prm, incoming) == expected
    else:
        with pytest.raises(error):
            assert validate_semver(ctx, prm, incoming) is None


@pytest.mark.parametrize(
    ("opt", "key", "checks", "get", "exec_ret_code", "yaml_data", "expected"),
    [
        ("-b", False, None, False, True, True, 1),
        ("-b", False, None, True, True, True, 1),
        ("-b", True, None, False, True, True, 1),
        ("-b", True, None, True, True, True, 0),
        ("-d", False, None, False, True, True, 1),
        ("-d", False, None, True, True, True, 1),
        ("-d", True, None, False, True, True, 1),
        ("-d", True, None, True, True, True, 0),
        ("-d", True, None, True, False, True, 2),
        ("-i", False, False, False, True, True, 1),
        ("-i", False, False, True, True, True, 1),
        ("-i", False, True, False, True, True, 1),
        ("-i", False, True, True, True, True, 1),
        ("-i", True, False, False, True, True, 1),
        ("-i", True, False, True, True, True, 1),
        ("-i", True, True, False, True, True, 1),
        ("-i", True, True, True, True, True, 0),
        ("-i", True, True, True, False, True, 2),
        ("-i", True, True, True, True, False, 4),
    ],
)
@patch("setupr.console.pgp_key")
@patch("setupr.console.pre_flight")
@patch("setupr.console.Downloader")
@patch("setupr.console.InstallationData")
def test_console(
    m_installation_data,
    m_downloader,
    m_pre_flight,
    m_pgp_key,
    opt,
    key,
    checks,
    get,
    yaml_data,
    exec_ret_code,
    expected,
):
    m_data = Mock(spec=InstallationData)
    m_data.service_account_json = Path("sa.json")
    m_data.blob_name = "values.yaml"
    m_data.fetch.return_value = yaml_data
    m_installation_data.return_value = m_data
    m_pgp_key.return_value = key
    m_pre_flight.return_value = checks
    m_dlr = Mock(spec=Downloader)
    m_dlr.get.return_value = get
    m_dlr.execute_script.return_value = exec_ret_code
    m_downloader.return_value = m_dlr

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            opt,
            "1.2.3",
            "--service-account",
            f"{Path.cwd()}/tests/ranni-valid.sa.json",
        ],
    )
    assert result.exit_code == expected, f"CLI output: {result.output}"


def test_no_option():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 1


def test_service_account_does_not_exist():
    runner = CliRunner()
    result = runner.invoke(main, ["-i", "1.2.3", "--service-account", "ook"])
    assert result.exit_code == 2, f"CLI output: {result.output}"


def test_service_account_cannot_be_found():
    with patch("pathlib.Path.glob") as mock_glob:
        mock_glob.return_value = []
        runner = CliRunner()
        result = runner.invoke(main, ["-i", "1.2.3"])
        assert result.exit_code == 3, f"CLI output: {result.output}"


@pytest.mark.parametrize(
    ("ask", "check", "code"),
    [
        (True, VersionCheck.LATEST, 3),
        (True, VersionCheck.UNKNOWN, 3),
        (True, VersionCheck.LAGGING, 0),
        (False, VersionCheck.LAGGING, 3),
    ],
)
def test_setupr_version_status(ask, check, code):
    with patch("setupr.console.check_if_latest_version") as mock_check, patch(
        "setupr.console.Confirm.ask"
    ) as mock_ask:
        mock_ask.return_value = ask
        mock_check.return_value = check
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "-i",
                "1.2.3",
            ],
        )
        # We need to check an error further down the stack since
        # a version unknown is fine for running setupr.
        assert result.exit_code == code, f"CLI output: {result.output}"
