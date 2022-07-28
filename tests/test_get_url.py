# -*- coding: utf-8 -*-
import pathlib
import re
import stat
import tempfile
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from unittest.mock import ANY, MagicMock, Mock, patch

import gnupg
import pytest
import requests
import requests_mock

# import requests_mock
from pendulum.parser import parse
from pendulum.parsing.exceptions import ParserError
from rich.progress import Progress, TaskID

from setupr.get_url import Downloader, copy_url, download, take_backup


@pytest.mark.parametrize("is_set", [True, False])
@patch("setupr.get_url.done_event")
def test_copy_url(mocked_done_event, is_set):
    mocked_done_event.is_set = Mock(return_value=is_set)  # Branch coverage.
    with tempfile.TemporaryDirectory(prefix="setupr_tests_") as tmpdirname:
        with requests_mock.Mocker() as mocked:
            url = "https://worldr.com/index.html"
            mocked.get(url, text="resp", headers={"content-length": "13"})
            dst = tmpdirname + "/index.html"
            progress = MagicMock(spec=Progress)
            copy_url(MagicMock(spec=TaskID), url, dst, progress)
            assert progress.start_task.called
            assert progress.update.called


@patch("setupr.get_url.done_event")
def test_copy_url_RequestException(mocked_done_event):
    mocked_done_event.is_set = Mock(return_value=False)  # Branch coverage.
    with tempfile.TemporaryDirectory(prefix="setupr_tests_") as tmpdirname:
        with requests_mock.Mocker() as mocked:
            url = "https://worldr.com/index.html"
            mocked.get(url, text="resp", status_code=400)
            dst = tmpdirname + "/index.html"
            progress = MagicMock(spec=Progress)
            with pytest.raises(requests.exceptions.RequestException):
                copy_url(MagicMock(spec=TaskID), url, dst, progress)
            assert not progress.start_task.called
            assert not progress.update.called


def test_download():
    with tempfile.TemporaryDirectory(prefix="setupr_tests_") as tmpdirname:
        with patch(
            "setupr.get_url.ThreadPoolExecutor"
        ) as mocked_ThreadPoolExecutor:
            pool = MagicMock(spec=ThreadPoolExecutor)
            fut = Mock()
            fut.result = Mock()
            pool.submit = Mock(return_value=fut)
            mocked_ThreadPoolExecutor.return_value.__enter__ = Mock(
                return_value=pool
            )
            url = "https://worldr.com/index.html"
            download(
                [
                    url,
                ],
                tmpdirname,
            )

            pool.submit.assert_called_once_with(
                ANY, ANY, url, tmpdirname + "/index.html", ANY
            )
            assert fut.result.called


def test_download_failed():
    with tempfile.TemporaryDirectory(prefix="setupr_tests_") as tmpdirname:
        with patch(
            "setupr.get_url.ThreadPoolExecutor"
        ) as mocked_ThreadPoolExecutor:
            pool = MagicMock(spec=ThreadPoolExecutor)
            fut = Mock()
            fut.result = Mock(side_effect=requests.exceptions.RequestException)
            pool.submit = Mock(return_value=fut)
            mocked_ThreadPoolExecutor.return_value.__enter__ = Mock(
                return_value=pool
            )

            url = "https://worldr.com/index.html"
            with pytest.raises(requests.exceptions.RequestException):
                download(
                    [
                        url,
                    ],
                    tmpdirname,
                )

            pool.submit.assert_called_once_with(
                ANY, ANY, url, tmpdirname + "/index.html", ANY
            )
            assert fut.result.called


def test_take_backup():
    with tempfile.TemporaryDirectory(prefix="setupr_tests_") as tmpdirname:
        file = pathlib.Path(tmpdirname, "test.txt")
        with open(file, "w") as fp:
            fp.write("created temporary file 0\n")
        assert take_backup(file) == file
        all_files = glob(f"{tmpdirname}/archives/test*.txt")
        assert len(all_files) == 1, "There should be only one…"
        date_string = re.findall(
            r"_[0-9]{4}-[0-9]{2}-[0-9]{2}T.*\.",
            all_files[0],
            flags=re.IGNORECASE,
        )[0][1:-1]
        assert all_files[0].startswith(f"{tmpdirname}/archives/test_")
        assert all_files[0].endswith(".txt")
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
    with patch.object(pathlib.Path, "is_dir", lambda _: True):
        sut = pathlib.Path("/file/does/not/exits/ever/no/really/it/does/not")
        bak = take_backup(sut)
        assert bak is sut


@pytest.fixture
def downloader():
    with patch("setupr.gpg.gnupg") as mock_gpg:
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
        ("_get_files", "backup", True, True),
        ("_get_files", "backup", False, False),
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
    with patch("setupr.get_url.download") as mocked_download:
        # This can override the return value if error is not None.
        mocked_download.side_effect = error
        downloader._gpg.validate_worldr_signature = MagicMock(return_value=sig)
        with patch.object(
            pathlib.Path, "chmod", lambda _, x: x == stat.S_IRWXU
        ):
            assert downloader._get_files("test", "v1.2.3") is expected
        assert mocked_download.called


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
    dst = pathlib.Path(__file__).parent / "charon-lord-dunsany.txt"
    with patch("setupr.get_url.download") as mocked_download:
        mocked_download.side_effect = error
        assert downloader.fetch("/dev/null", dst, hash) is expected
        assert mocked_download.called
