# -*- coding: utf-8 -*-
"""Wrapper to requests to get thing from URL and verify their PGP signatures.

.. code-block:: bash
  :linenos:
      pytest -o log_cli=true tests/test_get_url.py -k test_XXX

"""
import logging
from pathlib import Path

import pendulum
import requests

from drakkar.gpg import GPG

rlog = logging.getLogger("get-url")

WORLDR_URL_INSTALL = "https://storage.googleapis.com/worldr-install"
CHUNK_SIZE = 8 * 1024


def take_backup(filename: Path) -> Path:
    """Move the file to a backup one with the date."""
    if filename.is_file():
        new_name = f"{filename.parent}/{filename.stem}_{pendulum.now().to_iso8601_string()}{filename.suffix}"  # noqa
        filename.rename(new_name)
        return Path(new_name)
    return filename


def get_file(filename: str) -> None:
    """Get file from URL and verify its PGP signature."""
    rlog.debug("Getting %s", filename)
    url = f"{WORLDR_URL_INSTALL}/{filename}"
    take_backup(Path.cwd() / Path(filename))
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(Path.cwd() / Path(filename), "wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:  # pragma: no cover
                    f.write(chunk)


class Downloader:
    """A class wrapping the download and verify process."""

    def __init__(self) -> None:
        """Initialize the class."""
        self._gpg = GPG()
        rlog.debug("Downloader Initialized")

    def _get_files(self, what: str, version: str) -> bool:
        """Download and verify some files."""
        try:
            script = f"{what}-{version}.sh"
            get_file(script)
            signature = f"{what}-{version}.sig"
            get_file(signature)
            return self._gpg.validate_worldr_signature(
                (Path.cwd() / script).as_posix(),
                (Path.cwd() / signature).as_posix(),
            )
        except requests.exceptions.RequestException as ex:
            rlog.exception(ex)
            rlog.error("Could not downlaod %s script: %s", what, ex)
            return False
        except OSError as ex:
            rlog.exception(ex)
            rlog.error("Could not write %s script: %s", what, ex)
            return False

    def get(self, what: str, version: str) -> bool:
        """Download a file and its signature to verify it."""
        if what in ["install"]:
            rlog.info("Downloading installation script")
            return self._get_files("worldr-install", version)
        elif what in ["debug"]:
            rlog.info("Downloading debug script")
            return self._get_files("worldr-debug", version)
        else:
            rlog.warning("Option %s not supported", what)
            return False
