# -*- coding: utf-8 -*-
"""Command wrapping other functionalty with useful user output."""
import structlog

from drakkar.gpg import GPG
from drakkar.pre_flight import PreFlight
from drakkar.print import wprint

rlog = structlog.get_logger("commands")


def pgp_key() -> bool:
    """If we do not have the Worldr GPG key, get it.

    We cannot continue without it."""
    _gpg = GPG()
    if not _gpg.worldr_key_exists():
        msg = "Worldr PGP key not found, attempted to import it"
        rlog.warning(msg)
        wprint(msg, level="warning")
        if not _gpg.import_worldr_key():
            msg = "Worldr PGP key could not be imported."
            rlog.error(msg)
            wprint(msg, level="failure")
            return False
        wprint("Worldr PGP key imported.", level="success")
    else:
        wprint("Worldr PGP key found, all is well.", level="info")
    return True


def pre_flight() -> bool:
    """Pre flight check.

    The security ones are advisory only so we can continue if they fail. On
    the other hand, the infrastructure ones are mandatory and we cannot
    continue if they fail."""
    _pre_flight = PreFlight()
    if _pre_flight.security() != 0:
        msg = "Pre flight security checks failed. This is advisory only"
        rlog.warning(msg)
        wprint(msg, level="warning")
    else:
        wprint(
            "Security pre flight checks passed, all is well.", level="success"
        )
    if _pre_flight.infrastructure() != 0:
        msg = "Pre fight infrastructure checks failed. This is mandatory."
        rlog.error(msg)
        wprint(msg, level="failure")
        return False
    else:
        wprint(
            "Infrastructure pre flight checks passed, all is well.",
            level="success",
        )
    return True
