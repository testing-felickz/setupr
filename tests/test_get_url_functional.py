# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
import requests

from drakkar.get_url import Downloader
from drakkar.pre_flight import (
    GOSS_EXE,
    GOSS_URL,
    GOSS_VERSION,
    SHA256SUM,
    URL_BASE_CHECKS,
)


@pytest.mark.slow
@pytest.mark.parametrize(
    "what,version,basename",
    [
        ("install", "v3.6.1", "worldr-install-v3.6.1"),
        ("debug", "v0.10.0", "worldr-debug-v0.10.0"),
        ("backup", "v3.7.9", "backup-restore-v3.7.9"),
    ],
)
def test_get_real_scripts(what, version, basename):
    """This does it all for real, iff we have the PGP key & access to the
    internet.

    The test should tidy after itself.
    """
    # Check if we can connect to the Internet.
    try:
        requests.head("http://www.google.com/", timeout=1)
    except requests.ConnectionError:  # pragma: no cover
        pytest.fail("No internet connection.")

    # Check that we have a PGP key.
    sut = Downloader()
    if not sut._gpg.worldr_key_exists():  # pragma: no cover
        pytest.skip(
            "Worldr PGP key is not found, therefore this test cannot run."
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


@pytest.mark.slow
@pytest.mark.parametrize(
    "file, url",
    [
        ("goss-linux-amd64", f"{GOSS_URL}/{GOSS_VERSION}/{GOSS_EXE}"),
        (
            "goss-infrastructure.yaml",
            f"{URL_BASE_CHECKS}/goss-infrastructure.yaml",
        ),
        (
            "goss-security.yaml",
            f"{URL_BASE_CHECKS}/goss-security.yaml",
        ),
    ],
)
def test_fetch_goss(file, url):
    """This does it all for real, iff we have access to the internet.

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
