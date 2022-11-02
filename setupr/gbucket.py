# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""Get installation data from Google Cloud Storage bucket.

```python
from google.cloud import storage
storage_client = storage.Client.from_service_account_json('test.sa.json')
bucket = storage_client.bucket("worldr-customer-test")
blob = bucket.blob("test-values.yaml")
blob.download_to_filename("test-values.yaml")
```
"""
from pathlib import Path
from typing import Optional

import structlog
from google.cloud import storage  # type: ignore
from google.cloud.exceptions import NotFound

from setupr.utils import join_with_oxford_commas

rlog = structlog.get_logger("setupr.get-url")


class InstallationDataError(AttributeError):
    """Installation data error."""

    pass


class InstallationData:
    """Get installation data from Google Cloud Storage bucket."""

    def __init__(self, service_account_json: Optional[Path] = None) -> None:
        """Initialize."""
        self.service_account_json = service_account_json
        if not self.service_account_json:
            sa_files = sorted(Path(".").glob("*.sa.json"))
            if len(sa_files) == 1:
                self.service_account_json = sa_files[0]
            else:
                text = "No service account file found"
                if len(sa_files) > 1:
                    text = "Too many service account file found"
                raise InstallationDataError(
                    f"{text}: {join_with_oxford_commas(sa_files)}"
                )
        _stem = self.service_account_json.name.replace(".sa.json", "")
        self.bucket_name = f"worldr-customer-{_stem}"
        self.blob_value = f"{_stem}-values.yaml"
        self.blob_name = (
            f"{self.service_account_json.parent.as_posix()}/{self.blob_value}"
        )
        rlog.info("Bucket name", value=self.bucket_name)
        rlog.info("Blob value", value=self.blob_value)
        rlog.info("Blob name", value=self.blob_name)

    def get(self) -> bool:
        """Get installation data from Google Cloud Storage bucket.

        If `self.blob_name` exists on the file system, it will be
        overwritten. This is desired behaviour.

        It is best to validate the yaml file after downloading it, however,
        there is not point in enforcing it. If that is desired, use the `fetch`
        method.
        """
        storage_client = storage.Client.from_service_account_json(
            self.service_account_json
        )
        bucket = storage_client.bucket(self.bucket_name)
        blob = bucket.blob(self.blob_value)
        try:
            blob.download_to_filename(self.blob_name)
            rlog.info(f"Downloaded {self.blob_name} from {self.bucket_name}")
        except NotFound as err:
            msg = f"Installation data {self.blob_name} not found because {err}"
            rlog.error(msg)
            return False
        return True

    def fetch(self) -> bool:
        """Fetch and verify installation data from bucket."""
        return self.get()
