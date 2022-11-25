# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
# type: ignore
from pathlib import Path, PurePath
from unittest.mock import MagicMock, patch

import gnupg  # ignore: type
import pytest

from setupr.gpg import GPG

CHARON_LORD_DUNSANY_TXT = "charon-lord-dunsany.txt"


@pytest.fixture()
def mocked_gpg():
    with patch("setupr.gpg.gnupg") as mock_gpg:
        mock_gpg.return_value = MagicMock(spec=gnupg.GPG)
        sut = GPG()
        mock_gpg.GPG.assert_called_once()
        assert isinstance(sut._gpg, MagicMock)
        return sut


def test_worldr_key_exists(mocked_gpg):
    mocked_gpg._gpg.list_keys = MagicMock(
        return_value=[
            {"fingerprint": "935D282626A16D1A0430487D65A277F7800F774C"}
        ]
    )
    assert mocked_gpg.worldr_key_exists() is True, "Worldr key should be there"


def test_worldr_key_does_not_exist(mocked_gpg):
    mocked_gpg._gpg.list_keys = MagicMock(return_value=[])
    assert (
        mocked_gpg.worldr_key_exists() is False
    ), "Worldr key should not be there"


def test_worldr_key_does_not_exist_but_there_are_others(mocked_gpg):
    mocked_gpg._gpg.list_keys = MagicMock(
        return_value=[
            {"fingerprint": "0000000000000000000000000000000000000000"},
            {"fingerprint": "1111111111111111111111111111111111111111"},
        ]
    )
    assert (
        mocked_gpg.worldr_key_exists() is False
    ), "Worldr key should not be there"


def test_import_key_failure(mocked_gpg):
    imported = MagicMock(spec=gnupg.ImportResult)
    imported.count = 0
    mocked_gpg._gpg.import_keys = MagicMock(return_value=imported)
    assert (
        mocked_gpg.import_worldr_key() is False
    ), "Key should not be imported"
    mocked_gpg._gpg.trust_keys.assert_not_called()


def test_import_key_success(mocked_gpg):
    imported = MagicMock(spec=gnupg.ImportResult)
    imported.count = 1
    imported.fingerprints = ["935D282626A16D1A0430487D65A277F7800F774C"]
    mocked_gpg._gpg.import_keys = MagicMock(return_value=imported)
    assert mocked_gpg.import_worldr_key() is True, "Key should be imported"
    mocked_gpg._gpg.trust_keys.assert_called_with(
        imported.fingerprints[0], "TRUST_ULTIMATE"
    )


def test_verify_failure(mocked_gpg):
    verified = MagicMock(spec=gnupg.Verify)
    verified.status = "signature bad"
    mocked_gpg._gpg.verify_file = MagicMock(return_value=verified)
    filename = PurePath(
        Path(__file__).resolve().parent, CHARON_LORD_DUNSANY_TXT
    )
    signature = PurePath(
        Path(__file__).resolve().parent, "charon-lord-dunsany-bad.sig"
    )
    assert (
        mocked_gpg.validate_worldr_signature(
            filename.as_posix(), signature.as_posix()
        )
        is False
    ), "Signature should be bad"
    mocked_gpg._gpg.verify_file.assert_called()


def test_verify_success(mocked_gpg):
    verified = MagicMock(spec=gnupg.Verify)
    verified.status = "signature valid"
    mocked_gpg._gpg.verify_file = MagicMock(return_value=verified)
    filename = PurePath(
        Path(__file__).resolve().parent, CHARON_LORD_DUNSANY_TXT
    )
    signature = PurePath(
        Path(__file__).resolve().parent, "charon-lord-dunsany-good.sig"
    )
    assert (
        mocked_gpg.validate_worldr_signature(
            filename.as_posix(), signature.as_posix()
        )
        is True
    ), "Signature should be valid"
    mocked_gpg._gpg.verify_file.assert_called()


@pytest.mark.filterwarnings("ignore:setDaemon")
def test_verify_for_real():
    """Verify the `charon-lord-dunsany.txt` file for real.

    This can only run if the current user has the Worldr key in their keyring.
    This should be true of any developer but not of CI. Thus, the test is
    skipped if the key is not found.

    Suppressing this warning: `gnupg.py:1004: DeprecationWarning: setDaemon()
    is deprecated, set the daemon attribute instead dr.setDaemon(True)` since
    it is beyond out control.
    """
    sut = GPG()
    if (
        not sut.worldr_key_exists() and not sut.import_worldr_key()
    ):  # pragma: no cover
        pytest.skip(
            "Worldr PGP key cannot be imported, "
            "therefore this test cannot run."
        )
    filename = PurePath(
        Path(__file__).resolve().parent, CHARON_LORD_DUNSANY_TXT
    )
    signature = PurePath(
        Path(__file__).resolve().parent, "charon-lord-dunsany-good.sig"
    )
    assert (
        sut.validate_worldr_signature(
            filename.as_posix(), signature.as_posix()
        )
        is True
    ), "Signature should be valid"

    signature = PurePath(
        Path(__file__).resolve().parent, "charon-lord-dunsany-bad.sig"
    )
    assert (
        sut.validate_worldr_signature(
            filename.as_posix(), signature.as_posix()
        )
        is False
    ), "Signature should be bad"
