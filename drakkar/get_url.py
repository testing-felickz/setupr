# -*- coding: utf-8 -*-
"""Wrapper to requests to get thing from URL and verify their PGP signatures.


"""
import signal
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import FrameType
from typing import Iterable, Optional

import pendulum
import requests
import structlog
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from sha256sum import sha256sum

from drakkar.gpg import GPG

progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)

rlog = structlog.get_logger("get-url")

CHUNK_SIZE = 8 * 1024
WORLDR_URL_INSTALL = "https://storage.googleapis.com/worldr-install"


done_event = Event()


def handle_sigint(
    signum: int, frame: Optional[FrameType]
) -> None:  # pragma: no cover  # noqa
    """Handle SIGINT signal.

    There is little point in unit testing this function. A functional test
    would take a lot of setup for very gain.
    """
    rlog.debug("signal handle", signum=signum, frame=frame)
    done_event.set()


signal.signal(signal.SIGINT, handle_sigint)


def copy_url(task_id: TaskID, url: str, path: str) -> None:
    """Copy data from a url to a local file."""
    rlog.info("Requesting", url=url)
    response = requests.get(url, stream=True)

    progress.update(
        task_id, total=int(str(response.headers.get("content-length")))
    )
    with open(path, "wb") as dest_file:
        progress.start_task(task_id)
        for data in response.iter_content(chunk_size=4096):
            dest_file.write(data)
            progress.update(task_id, advance=len(data))
            if done_event.is_set():
                return
    rlog.info("Downloaded", path=path)


def download(urls: Iterable[str], dest_dir: str) -> None:
    """Download multiple files to the given directory."""
    with progress:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for url in urls:
                filename = url.split("/")[-1]
                dest_path = take_backup(Path(dest_dir) / Path(filename))
                task_id = progress.add_task(
                    "download", filename=filename, start=False
                )
                pool.submit(copy_url, task_id, url, dest_path.as_posix())


def take_backup(filename: Path) -> Path:
    """Move the file to a backup one with the date."""
    if filename.is_file():
        new_name = f"{filename.parent}/{filename.stem}_{pendulum.now().to_iso8601_string()}{filename.suffix}"  # noqa
        filename.rename(new_name)
    return filename


class Downloader:
    """A class wrapping the download and verify process."""

    def __init__(self) -> None:
        """Initialize the class."""
        self._gpg = GPG()
        self._log = structlog.get_logger(self.__class__.__name__)
        self._log.debug("Downloader Initialized")

    def _get_files(self, what: str, version: str) -> bool:
        """Download and verify some files."""
        try:
            script = f"{what}-{version}.sh"
            signature = f"{what}-{version}.sig"
            download(
                (
                    f"{WORLDR_URL_INSTALL}/{script}",
                    f"{WORLDR_URL_INSTALL}/{signature}",
                ),
                Path.cwd().as_posix(),
            )
            return self._gpg.validate_worldr_signature(
                (Path.cwd() / script).as_posix(),
                (Path.cwd() / signature).as_posix(),
            )
        except requests.exceptions.RequestException as ex:
            self._log.exception(ex)
            self._log.error("Could not downlaod script", script=what, error=ex)
            return False
        except OSError as ex:
            self._log.exception(ex)
            self._log.error("Could not write script", script=what, error=ex)
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
            self._log.warning("Option not supported", option=what)
            return False

    def fetch(self, source: str, destination: str, expected_hash: str) -> bool:
        """Fetches a package from the Internet and verifies it."""
        try:
            download((source,), Path.cwd().as_posix())
        except requests.exceptions.RequestException as ex:
            self._log.exception(ex)
            self._log.error(
                "Could not downlaod script", script=source, error=ex
            )
            return False
        except OSError as ex:
            self._log.exception(ex)
            self._log.error("Could not write script", script=source, error=ex)
            return False
        if expected_hash != sha256sum(destination):
            self._log.error("Wrong hash", file=destination)
            return False
        return True
