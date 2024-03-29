# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""gBucket tests."""
from pathlib import Path, PosixPath
from unittest.mock import Mock, patch

import pytest
from google.cloud.exceptions import NotFound

from setupr.gbucket import InstallationData, InstallationDataError


def test_implicit_data() -> None:
    sut = InstallationData(PosixPath("EldenRing"))
    assert sut.bucket_name == "worldr-customer-EldenRing"
    assert sut.blob_name == "./EldenRing-values.yaml"


@pytest.fixture()
def sut() -> InstallationData:
    """Fixture: We provide a simple sample service account file."""
    with patch("pathlib.Path.glob") as mock_glob:
        mock_glob.return_value = [Path("xUnit-test.sa.json")]
        return InstallationData()


def test_derived_data(sut: InstallationData) -> None:
    """Test derived data."""
    assert sut.bucket_name == "worldr-customer-xUnit-test"
    assert sut.blob_name == "./xUnit-test-values.yaml"


@pytest.mark.parametrize(
    ("items"),
    [
        (Path("xUnit-test.sa.json"), Path("xUnit-test.sa.json")),
        ([]),
    ],
)
def test_error_sa_files(items: InstallationData) -> None:
    with patch("pathlib.Path.glob") as mock_glob:
        mock_glob.return_value = items
        with pytest.raises(InstallationDataError):
            InstallationData()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (None, True),
        (NotFound("Not found"), False),
    ],
)
def test_get(
    error: NotFound | None, expected: bool, sut: InstallationData
) -> None:
    """Test get."""
    with patch(
        "setupr.gbucket.storage.Client.from_service_account_json"
    ) as m_from_service_account_json:
        m_blob = Mock()
        m_blob.download_to_filename = Mock(side_effect=error)
        m_bucket = Mock()
        m_bucket.blob.return_value = m_blob
        m_storage_client = Mock()
        m_storage_client.bucket.return_value = m_bucket
        m_from_service_account_json.return_value = m_storage_client

        assert sut.get() is expected

        m_blob.download_to_filename.assert_called_once_with(
            "./xUnit-test-values.yaml"
        )
        m_bucket.blob.assert_called_once_with("xUnit-test-values.yaml")
        m_storage_client.bucket.assert_called_once_with(
            "worldr-customer-xUnit-test"
        )
        m_from_service_account_json.assert_called_once_with(
            PosixPath("xUnit-test.sa.json")
        )


@pytest.mark.parametrize(
    ("rget", "expected"),
    [
        (True, True),
        (False, False),
    ],
)
def test_fetch(rget: bool, expected: bool, sut: InstallationData) -> None:
    sut.get = Mock(return_value=rget)  # type: ignore
    assert sut.fetch() is expected


def test_sa_is_path() -> None:
    sut = InstallationData(PosixPath("tests/EldenRing.sa.json"))
    assert sut.bucket_name == "worldr-customer-EldenRing"
    assert sut.blob_name == "tests/EldenRing-values.yaml"
