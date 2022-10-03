# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""Wrapper to goss.

Note that plumbum does not have type hints. Please see the bug [Type hints
        for library #334 ](https://github.com/tomerfiliba/plumbum/issues/334)
for more information.
"""
import os
import pathlib
import stat
from typing import Any

import structlog
from plumbum import (  # type: ignore
    CommandNotFound,
    ProcessExecutionError,
    local,
)

from setupr.get_url import Downloader, take_backup

GOSS_EXE = "goss-linux-amd64"
GOSS_URL = "https://github.com/aelsabbahy/goss/releases/download"
GOSS_VERSION = "v0.3.16"
SHA256SUM = {
    "goss-infrastructure.yaml": "ef45088bb00d9e00f54971dbbaf6c1b60f85a419cfc3ce1fdc80d0cabf403aeb",  # noqa
    "goss-linux-amd64": "827e354b48f93bce933f5efcd1f00dc82569c42a179cf2d384b040d8a80bfbfb",  # noqa
    "goss-security.yaml": "8c2d12b4dd6c555ec558e1d30f862bd352e44217dd6b3626208ad2840e0064fe",  # noqa
}
URL_BASE_CHECKS = "https://storage.googleapis.com/worldr-install"


class PreFlight:
    """Wrapper to all pre-flight calls."""

    def __init__(self) -> None:
        """Initialise."""
        self._log = structlog.get_logger("setupr.pre_flight")
        self._goss = None
        self._downloader = Downloader()
        self._bin = pathlib.Path.home() / "bin"
        if not self._bin.is_dir():
            self._log.warning("Creating directory.", dir=self._bin)
            self._bin.mkdir()
        if self._bin not in local.env.path:
            self._log.debug("Adding directory to PATH.", dir=self._bin)
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
                    "goss version mismatch",
                    version=GOSS_VERSION,
                )
                raise CommandNotFound("goss", local.env.path)
        except CommandNotFound as ex:
            self._log.warning("goss not found", error=ex)
            dst = self._bin / "goss-linux-amd64"
            self._downloader.fetch(
                f"{GOSS_URL}/{GOSS_VERSION}/{GOSS_EXE}",
                dst,
                SHA256SUM["goss-linux-amd64"],
            )
            dst.chmod(stat.S_IRWXU)  # Read, write, and execute by owner.
            (self._bin / "goss").symlink_to(dst)
            self._goss = local[dst.as_posix()]
        return self._goss

    def _fetch_file(self, what: str) -> pathlib.Path:
        """Fetch a file, if needed."""
        name = f"goss-{what}.yaml"
        check = pathlib.Path.cwd() / f"{name}"
        self._downloader.fetch(
            f"{URL_BASE_CHECKS}/{name}",
            check,
            SHA256SUM[name],
        )
        return check

    def security(self) -> int:
        """Run the security checks."""
        return self._run("security")

    def infrastructure(self) -> int:
        """Run the infrastructure checks."""
        return self._run("infrastructure")

    def _run(self, what: str) -> int:
        """Run goss."""
        check = self._fetch_file(what)
        try:
            retcode, _, _ = self.goss.run(
                (
                    "-g",
                    check.as_posix(),
                    "validate",
                    "--format",
                    "documentation",
                    "--no-color",
                )
            )
            self._log.info("Checks passed.", checks=what.title())
            return int(retcode)
        except ProcessExecutionError as ex:
            self._log.debug(
                "Pre flight checks failed output",
                checks=what.title(),
                error=ex,
            )
            self._log.warning(
                "Pre flight checks failed",
                checks=what.title(),
                retcode=ex.retcode,
            )
            log = take_backup(pathlib.Path.cwd() / f"goss-{what}.log")
            with os.fdopen(os.open(log, os.O_RDWR | os.O_CREAT), "w") as f:
                f.write(ex.stdout)
                f.write(ex.stderr)
            return int(ex.retcode)
