# -*- coding: utf-8 -*-
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import gnupg
import pytest
import requests
import requests_mock
from pendulum.parser import parse
from pendulum.parsing.exceptions import ParserError

from drakkar.get_url import (
    WORLDR_URL_INSTALL,
    Downloader,
    get_file,
    take_backup,
)


def test_take_backup():
    with tempfile.TemporaryDirectory(prefix="drakkar_tests_") as tmpdirname:
        file = Path(tmpdirname, "test.txt")
        with open(file, "w") as fp:
            fp.write("created temporary file 0\n")
        bak = take_backup(file).as_posix()
        date_string = re.findall(
            r"_[0-9]{4}-[0-9]{2}-[0-9]{2}T.*\.", bak, flags=re.IGNORECASE
        )[0][1:-1]
        assert bak.startswith(f"{tmpdirname}/test_")
        assert bak.endswith(".txt")
        try:
            parse(date_string)
            # If we are here, then there is an ISO8601 compliant string in the
            # backup file. Since we checked it starts with and ends with the
            # correct input, we can be fairly sure it is the correct backup
            # file.
        except ParserError:  # pragma: no cover
            # We do not need to cover this case, it is a failure only!
            pytest.fail("Could not parse date string of backup file")


def test_take_backup_no_need():
    sut = Path("/file/does/not/exits/ever/no/really/it/does/not")
    bak = take_backup(sut)
    assert bak is sut


def test_get_file_success():
    with requests_mock.Mocker() as m:
        url = f"{WORLDR_URL_INSTALL}/test"
        m.get(url, text="resp")
        mocked_open = mock_open()
        with patch("drakkar.get_url.open", mocked_open):
            get_file(url, "test")
            mocked_open.assert_called_once_with(
                take_backup(Path.cwd() / Path("test")), "wb"
            )


def test_get_file_http_failure():
    with requests_mock.Mocker() as m:
        url = f"{WORLDR_URL_INSTALL}/test"
        m.get(url, text="resp", status_code=404)
        mocked_open = mock_open()
        with patch("drakkar.get_url.open", mocked_open):
            with pytest.raises(requests.exceptions.HTTPError) as exc_info:
                get_file(url, "test")
            exception_raised = exc_info.value
            assert "404 Client Error" in exception_raised.args[0]
            assert mocked_open.called is False


def test_get_file_OS_error():
    with requests_mock.Mocker() as m:
        url = f"{WORLDR_URL_INSTALL}/test"
        m.get(url, text="resp")
        mocked_open = mock_open()
        mocked_open.side_effect = Exception("Boom!")
        with patch("drakkar.get_url.open", mocked_open):
            with pytest.raises(Exception) as exc_info:
                get_file(url, "test")
            exception_raised = exc_info.value
            assert "Boom!" in exception_raised.args[0]
            mocked_open.assert_called_once_with(
                take_backup(Path.cwd() / Path("test")), "wb"
            )


@pytest.fixture
def downloader():
    with patch("drakkar.gpg.gnupg") as mock_gpg:
        mock_gpg.return_value = MagicMock(spec=gnupg.GPG)
        sut = Downloader()
        assert isinstance(sut._gpg._gpg, MagicMock)
        return sut


@pytest.mark.parametrize(
    "func,what,returned,expected",
    [
        ("_get_files", "install", True, True),
        ("_get_files", "install", False, False),
        ("_get_files", "Elden Ring", True, False),
        ("_get_files", "debug", True, True),
        ("_get_files", "debug", False, False),
        ("_get_files", "Elden Ring", True, False),
    ],
)
def test_downloader_get_files(downloader, func, what, returned, expected):
    with patch.object(downloader, func) as m:
        m.return_value = returned
        assert downloader.get(what, "v1.2.3") is expected


@pytest.mark.parametrize(
    "sig,error,expected",
    [
        (True, None, True),
        (True, OSError("BooM"), False),
        (True, requests.exceptions.RequestException, False),
        (False, None, False),
        (False, OSError, False),
        (False, requests.exceptions.RequestException, False),
    ],
)
def test_get_files(sig, error, expected, downloader):
    with patch("drakkar.get_url.get_file") as mocked_get_file:
        # This can override the return value if error is not None.
        mocked_get_file.side_effect = error
        downloader._gpg.validate_worldr_signature = MagicMock(return_value=sig)
        assert downloader._get_files("test", "v1.2.3") is expected


@pytest.mark.parametrize(
    "hash,error,expected",
    [
        (
            "4362bac71d971fc7d7b69a757de6fbcb5e1c513b393609043cae67b5341bd4af",
            None,
            True,
        ),
        (
            "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            None,
            False,
        ),
        (
            "4362bac71d971fc7d7b69a757de6fbcb5e1c513b393609043cae67b5341bd4af",
            OSError,
            False,
        ),
        (
            "4362bac71d971fc7d7b69a757de6fbcb5e1c513b393609043cae67b5341bd4af",
            requests.exceptions.RequestException,
            False,
        ),
    ],
)
def test_fetch(hash, error, expected, downloader):
    dst = Path(__file__).parent / "charon-lord-dunsany.txt"
    with patch("drakkar.get_url.get_file") as mocked_get_file:
        mocked_get_file.side_effect = error
        assert downloader.fetch("/dev/null", dst.as_posix(), hash) is expected
