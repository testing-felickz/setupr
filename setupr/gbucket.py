# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""Get installation data from Google Cloud Storage bucket.

```python
from google.cloud import storage
storage_client = storage.Client.from_service_account_json('test.sa.json')
bucket = storage_client.bucket("worldr-customer-test")
blob = bucket.blob("test.env.yaml")
blob.download_to_filename("test.env.yaml")
```
"""
from pathlib import Path
from typing import Optional

import structlog
from cerberus import Validator  # type:ignore
from google.cloud import storage  # type: ignore
from google.cloud.exceptions import NotFound
from ruamel.yaml import YAML

from setupr.schema import WORLDR_INSTALLATION_DATA_SCHEMA
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
        self.blob_name = (
            f"{self.service_account_json.parent.as_posix()}/{_stem}.env.yaml"
        )
        self._validator = Validator(
            WORLDR_INSTALLATION_DATA_SCHEMA, allow_unknown={"type": "string"}
        )

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
        blob = bucket.blob(self.blob_name)
        try:
            blob.download_to_filename(self.blob_name)
            rlog.info(f"Downloaded {self.blob_name} from {self.bucket_name}")
        except NotFound as err:
            msg = f"Installation data {self.blob_name} not found because {err}"
            rlog.error(msg)
            return False
        return True

    def validate(self) -> bool:
        """Validate the installation data.

        Returns:
            True if the installation data is valid, False otherwise.
        """
        yaml = YAML()
        with open(self.blob_name) as f:
            data = yaml.load(f)
        if not self._validator.validate(data):  # pyright: ignore
            rlog.error(
                "There are validation errors: "
                f"{self._validator.errors}"  # pyright: ignore
            )
            return False
        rlog.info(f"Validated {self.blob_name}")
        return True

    def fetch(self) -> bool:
        """Fetch and verify installation data from bucket."""
        return self.get() and self.validate()
