# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
# type: ignore
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from setupr.get_url import Downloader
from setupr.pre_flight import (
    GOSS_EXE,
    GOSS_URL,
    GOSS_VERSION,
    SHA256SUM,
    URL_BASE_CHECKS,
)


@pytest.mark.slow()
@pytest.mark.parametrize(
    ("what", "version", "basename"),
    [
        ("install", "v3.6.1", "worldr-install-v3.6.1"),
        ("debug", "v0.10.0", "worldr-debug-v0.10.0"),
        ("backup", "v3.7.9", "backup-restore-v3.7.9"),
    ],
)
def test_get_real_scripts(what: str, version: str, basename: str) -> None:
    """Run iff we have the PGP key & access to the internet.

    The test should tidy after itself.
    """
    # Check if we can connect to the Internet.
    try:
        requests.head("http://www.google.com/", timeout=1)
    except requests.ConnectionError:  # pragma: no cover
        pytest.fail("No internet connection.")

    # Check that we have a PGP key.
    sut = Downloader()
    if (
        not sut._gpg.worldr_key_exists() and not sut._gpg.import_worldr_key()
    ):  # pragma: no cover
        pytest.skip(
            "Worldr PGP key cannot be imported, "
            "therefore this test cannot run."
        )

    # Call.
    assert sut.get(f"{what}", f"{version}") is True

    # Tidy up.
    if not Path(f"{basename}.sh").is_file():  # pragma: no cover
        pytest.fail("The script was not downloaded.")
    Path(f"{basename}.sh").unlink()
    if not Path(f"{basename}.sig").is_file():  # pragma: no cover
        pytest.fail("The signature file was not downloaded.")
    Path(f"{basename}.sig").unlink()


@pytest.mark.slow()
@pytest.mark.parametrize(
    ("file", "url"),
    [
        ("goss-linux-amd64", f"{GOSS_URL}/{GOSS_VERSION}/{GOSS_EXE}"),
        (
            "goss-infrastructure-Ubuntu.yaml",
            f"{URL_BASE_CHECKS}/goss-infrastructure-Ubuntu.yaml",
        ),
        (
            "goss-security-Ubuntu.yaml",
            f"{URL_BASE_CHECKS}/goss-security-Ubuntu.yaml",
        ),
        (
            "goss-infrastructure-RHEL.yaml",
            f"{URL_BASE_CHECKS}/goss-infrastructure-RHEL.yaml",
        ),
        (
            "goss-security-RHEL.yaml",
            f"{URL_BASE_CHECKS}/goss-security-RHEL.yaml",
        ),
    ],
)
def test_fetch_goss(file: str, url: str) -> None:
    """This does it all for real, iff we have access to the internet.

    It tests that we can download all the goss definition files, and
    that the checksum are correct.

    The test should tidy after itself.
    """
    # Check if we can connect to the Internet.
    try:
        requests.head("http://www.google.com/", timeout=1)
    except requests.ConnectionError:  # pragma: no cover
        pytest.fail("No internet connection.")

    sut = Downloader()
    assert sut.fetch(f"{url}", Path(file), SHA256SUM[f"{file}"]) is True
    if not Path(f"{file}").is_file():  # pragma: no cover
        pytest.fail(f"{file} was not downloaded.")
    Path(f"{file}").unlink()


@pytest.mark.slow()
def test_execute_script() -> None:
    """This does things for real and will take time."""
    with patch("setupr.get_url.Confirm") as mocked_confirm:
        mocked_confirm.ask = Mock(return_value=True)
        sut = Downloader()
        assert sut.execute_script("tests/runme", "v1.0.0") is True
        assert mocked_confirm.ask.called
