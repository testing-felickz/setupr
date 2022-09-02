# -*- coding: utf-8 -*-
"""All the things to do with GPG."""
from pathlib import Path, PurePath

import gnupg  # type: ignore
import structlog

rlog = structlog.get_logger("setupr.gpg")


class GPG:
    """All the things to do with GPG."""

    # gpg: gnupg.GPG  # type: ignore
    _fingerprint = "935D282626A16D1A0430487D65A277F7800F774C"

    def __init__(self) -> None:
        """Initialize."""
        self._gpg = gnupg.GPG()

    def worldr_key_exists(self) -> bool:
        """Check if the worldr key exists in the local key ring."""
        return any(
            self._fingerprint == key["fingerprint"]
            for key in self._gpg.list_keys()
        )

    def import_worldr_key(self) -> bool:
        """Import the included Worldr PGP key."""
        key = PurePath(
            Path(__file__).resolve().parent,
            "Worldr-MST-installation-PGP-key.asc",
        )
        rlog.debug("The path to the key", path=key)
        with open(key, "r") as fd:
            key_data = fd.read()
        import_result = self._gpg.import_keys(key_data)
        if import_result.count == 1:
            fp = import_result.fingerprints[0]
            rlog.info(
                "PGP key imported successfully.",
                fingerprint=[
                    fp[i : i + 4] for i in range(0, len(fp), 4)
                ],  # noqa: E203
            )
            self._gpg.trust_keys(
                import_result.fingerprints[0], "TRUST_ULTIMATE"
            )
            rlog.info("Key is set to trust ultimate.")
            return True
        rlog.error("Could not import PGP key")
        return False

    def validate_worldr_signature(self, filename: str, signature: str) -> bool:
        """Validate a worldr signature."""
        with open(signature, "rb") as stream:
            verified = self._gpg.verify_file(stream, filename)
            if verified.status == "signature bad":
                rlog.error("Signature of is bad.", file=filename)
                return False
            rlog.info("Signature of file is good", file=filename)
            return True
