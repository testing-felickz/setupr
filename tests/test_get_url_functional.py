# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
import requests

from drakkar.get_url import Downloader
from drakkar.pre_flight import GOSS_VERSION, SHA256SUM


@pytest.mark.slow
def test_get_real_instgall_script():
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
    assert sut.get("install", "v3.6.1") is True

    # Tidy up.
    if not Path("worldr-install-v3.6.1.sh").is_file():  # pragma: no cover
        pytest.fail("The script was not downloaded.")
    Path("worldr-install-v3.6.1.sh").unlink()
    if not Path("worldr-install-v3.6.1.sig").is_file():  # pragma: no cover
        pytest.fail("The signature file was not downloaded.")
    Path("worldr-install-v3.6.1.sig").unlink()


@pytest.mark.slow
def test_fetch_goss():
    """This does it all for real, iff we have access to the internet.

    The test should tidy after itself.
    """
    # Check if we can connect to the Internet.
    try:
        requests.head("http://www.google.com/", timeout=1)
    except requests.ConnectionError:  # pragma: no cover
        pytest.fail("No internet connection.")

    sut = Downloader()
    assert (
        sut.fetch(
            f"https://github.com/aelsabbahy/goss/releases/download/{GOSS_VERSION}/goss-linux-amd64",  # noqa
            "goss-linux-amd64",
            SHA256SUM["goss"],
        )
        is True
    )
    if not Path("goss-linux-amd64").is_file():  # pragma: no cover
        pytest.fail("goss was not downloaded.")
    Path("goss-linux-amd64").unlink()
