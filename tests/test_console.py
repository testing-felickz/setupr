# -*- coding: utf-8 -*-
# type: ignore
from unittest.mock import Mock, patch

import pytest
from click import Option
from click.core import Context
from click.exceptions import UsageError
from click.testing import CliRunner

from setupr import __version__
from setupr.console import main, validate_semver
from setupr.get_url import Downloader

SEMVER = "1.2.3"


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "Setupr ships the Worldr infrastructure" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
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
    assert result.exit_code == 2
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
    assert result.exit_code == 2
    assert "is not valid SemVer string" in result.output


@pytest.mark.parametrize(
    ("input", "expected", "error"),
    [
        (None, None, None),
        ("1.2.3", "1.2.3", None),
        ("ook", None, UsageError),
    ],
)
def test_verify_semver(input, expected, error):
    """We are just testing that the callback works.

    We are not doing an exhaustive test of semver!
    """
    ctx = Mock(spec=Context)
    prm = Mock(spec=Option)
    if error is None:
        assert validate_semver(ctx, prm, input) == expected
    else:
        with pytest.raises(error):
            assert validate_semver(ctx, prm, input) is None


@pytest.mark.parametrize(
    ("opt", "key", "checks", "get", "exec_ret_code", "expected"),
    [
        ("-b", False, None, False, True, 1),
        ("-b", False, None, True, True, 1),
        ("-b", True, None, False, True, 1),
        ("-b", True, None, True, True, 0),
        ("-d", False, None, False, True, 1),
        ("-d", False, None, True, True, 1),
        ("-d", True, None, False, True, 1),
        ("-d", True, None, True, True, 0),
        ("-d", True, None, True, False, 2),
        ("-i", False, False, False, True, 1),
        ("-i", False, False, True, True, 1),
        ("-i", False, True, False, True, 1),
        ("-i", False, True, True, True, 1),
        ("-i", True, False, False, True, 1),
        ("-i", True, False, True, True, 1),
        ("-i", True, True, False, True, 1),
        ("-i", True, True, True, True, 0),
        ("-i", True, True, True, False, 2),
    ],
)
@patch("setupr.console.pgp_key")
@patch("setupr.console.pre_flight")
@patch("setupr.console.Downloader")
def test_console(
    m_downloader,
    m_pre_flight,
    m_pgp_key,
    opt,
    key,
    checks,
    get,
    exec_ret_code,
    expected,
):
    m_pgp_key.return_value = key
    m_pre_flight.return_value = checks
    m_dlr = Mock(spec=Downloader)
    m_dlr.get.return_value = get
    m_dlr.execute_script.return_value = exec_ret_code
    m_downloader.return_value = m_dlr

    runner = CliRunner()
    result = runner.invoke(main, [opt, "1.2.3"])
    assert result.exit_code == expected


def test_no_option():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 1
