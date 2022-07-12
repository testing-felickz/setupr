# -*- coding: utf-8 -*-
"""Wrapper to goss.

This needs to do the following things:
    [X] - Get goss binary.
    [X] - Verify goss binary.
    [X] - Get security checks file.
    [X] - Get infrastructure checks file.
    [X] - Run goss, capture output.

Note that plumbum does not have type hints. Please see the bug [Type hints
        for library #334 ](https://github.com/tomerfiliba/plumbum/issues/334)
for more information.

"""
import logging
import pathlib
import stat
from typing import Any

from plumbum import CommandNotFound, local  # type: ignore

from drakkar.get_url import Downloader

GOSS_EXE = "goss-linux-amd64"
GOSS_URL = "https://github.com/aelsabbahy/goss/releases/download"
GOSS_VERSION = "v0.3.16"
SHA256SUM = {
    "infrastructure": "28a50e5d382ec81da96fe298cf010ea7b78c27674f0ed631f759f5bb0120b234",  # noqa
    "security": "8c2d12b4dd6c555ec558e1d30f862bd352e44217dd6b3626208ad2840e0064fe",  # noqa
    "goss": "827e354b48f93bce933f5efcd1f00dc82569c42a179cf2d384b040d8a80bfbfb",  # noqa
}
URL_BASE_CHECKS = "https://storage.googleapis.com/worldr-install"


class PreFlight:
    """Wrapper to all pre-flight calls."""

    def __init__(self) -> None:
        """Initialisation."""
        self._log = logging.getLogger(self.__class__.__name__)
        self._goss = None
        self._downloader = Downloader()
        self._bin = pathlib.Path.home() / "bin"
        if not self._bin.is_dir():
            self._log.warning("Creating %s directory.", self._bin)
            self._bin.mkdir()
        if self._bin not in local.env.path:
            self._log.debug("Adding %s to PATH.", self._bin)
            local.env.path.append(self._bin)

    @property
    def goss(self) -> Any:
        """Return the goss binary.

        There are three cases:
            1. `goss` is found and correct, just return it.
            1. `goss` is in the PATH, add it has the correct version.
            1. `goss` is not in the PATH or is wrong version: fetch the
                correct one.
        """
        if self._goss is not None:
            # We assume we have the correct version!
            return self._goss
        try:
            # This assumes that `goss` is on the PATH.
            self._goss = local["goss"]
            if GOSS_VERSION not in self._goss("--version"):  # type: ignore
                self._log.warning(
                    "goss version mismatch, getting correct one %s",
                    GOSS_VERSION,
                )
                raise CommandNotFound("goss", local.env.path)
        except CommandNotFound as ex:
            self._log.warning("goss not found: %s", ex)
            dst = self._bin / "goss"
            self._downloader.fetch(
                f"{GOSS_URL}/{GOSS_VERSION}/{GOSS_EXE}",
                dst.as_posix(),
                SHA256SUM["goss"],
            )
            dst.chmod(stat.S_IRWXU)  # Read, write, and execute by owner.
            self._goss = local[dst.as_posix()]
        return self._goss

    def _fetch_file(self, what: str) -> pathlib.Path:
        """Fetches a file, if needed"""
        name = f"goss-{what}.yaml"
        check = pathlib.Path.home() / f"{name}"
        if not check.is_file():
            self._downloader.fetch(
                f"{URL_BASE_CHECKS}/{name}",
                check.as_posix(),
                SHA256SUM[what],
            )
        return check

    def security(self) -> int:
        """Runs the security checks."""
        return self._run("security")

    def infrastructure(self) -> int:
        """Runs the infrastructure checks."""
        return self._run("infrastructure")

    def _run(self, what: str) -> int:
        """Wrapper to run goss."""
        check = self._fetch_file(what)
        retcode, stdout, stderr = self.goss(
            "-g",
            check.as_posix(),
            "validate",
            "--format",
            "documentation",
            "--no-color",
        )().run()
        if retcode != 0:
            self._log.error("{what.title()} checks failed: %s", stdout)
            self._log.error("{what.title()} checks failed: %s", stderr)
        else:
            self._log.info("{what.title()} checks passed.")
        return retcode  # type: ignore