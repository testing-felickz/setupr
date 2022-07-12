# -*- coding: utf-8 -*-
"""Wrapper to requests to get thing from URL and verify their PGP signatures.


"""
import logging
from pathlib import Path

import pendulum
import requests
from sha256sum import sha256sum

from drakkar.gpg import GPG

rlog = logging.getLogger("get-url")

CHUNK_SIZE = 8 * 1024
WORLDR_URL_INSTALL = "https://storage.googleapis.com/worldr-install"


def take_backup(filename: Path) -> Path:
    """Move the file to a backup one with the date."""
    if filename.is_file():
        new_name = f"{filename.parent}/{filename.stem}_{pendulum.now().to_iso8601_string()}{filename.suffix}"  # noqa
        filename.rename(new_name)
        return Path(new_name)
    return filename


def get_file(source: str, destination: str) -> None:
    """Get file from URL and verify its PGP signature."""
    rlog.debug("Getting %s from %s.", destination, source)
    take_backup(Path.cwd() / Path(destination))
    with requests.get(source, stream=True) as r:
        r.raise_for_status()
        with open(Path.cwd() / Path(destination), "wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:  # pragma: no cover
                    f.write(chunk)


class Downloader:
    """A class wrapping the download and verify process."""

    def __init__(self) -> None:
        """Initialize the class."""
        self._gpg = GPG()
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.debug("Downloader Initialized")

    def _get_files(self, what: str, version: str) -> bool:
        """Download and verify some files."""
        try:
            script = f"{what}-{version}.sh"
            get_file(f"{WORLDR_URL_INSTALL}/{script}", script)
            signature = f"{what}-{version}.sig"
            get_file(f"{WORLDR_URL_INSTALL}/{signature}", signature)
            return self._gpg.validate_worldr_signature(
                (Path.cwd() / script).as_posix(),
                (Path.cwd() / signature).as_posix(),
            )
        except requests.exceptions.RequestException as ex:
            self._log.exception(ex)
            self._log.error("Could not downlaod %s script: %s", what, ex)
            return False
        except OSError as ex:
            self._log.exception(ex)
            self._log.error("Could not write %s script: %s", what, ex)
            return False

    def get(self, what: str, version: str) -> bool:
        """Download a file and its signature to verify it."""
        if what in ["install"]:
            self._log.info("Downloading installation script")
            return self._get_files("worldr-install", version)
        elif what in ["debug"]:
            self._log.info("Downloading debug script")
            return self._get_files("worldr-debug", version)
        elif what in ["backup"]:
            self._log.info("Downloading backup script")
            return self._get_files("backup-restore", version)
        else:
            self._log.warning("Option %s not supported", what)
            return False

    def fetch(self, source: str, destination: str, expected_hash: str) -> bool:
        """Fetches a package from the Internet and verifies it."""
        try:
            get_file(source, destination)
        except requests.exceptions.RequestException as ex:
            self._log.exception(ex)
            self._log.error("Could not downlaod %s script: %s", source, ex)
            return False
        except OSError as ex:
            self._log.exception(ex)
            self._log.error("Could not write %s script: %s", source, ex)
            return False
        if expected_hash != sha256sum(destination):
            self._log.error("%s has wrong hash", destination)
            return False
        return True
