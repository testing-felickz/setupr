# -*- coding: utf-8 -*-
""" … """
import logging
from logging.handlers import RotatingFileHandler

import click
from click_help_colors import HelpColorsCommand  # type: ignore
from rich.logging import RichHandler
from rich.traceback import install

# Click.
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

# Rich.
install(show_locals=True)
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True),
        RotatingFileHandler(
            "drekkar.log", maxBytes=13 * 1024 * 1024, backupCount=7
        ),
    ],
)
rlog = logging.getLogger()


@click.command(
    context_settings=CONTEXT_SETTINGS,
    cls=HelpColorsCommand,
    help_headers_color="blue",
    help_options_color="magenta",
)
def main() -> int:
    """Drekkar ships the Worldr infrastructure."""
    rlog.info("Start")
    rlog.info("End")
    return 0


if __name__ == "__main__":
    from sys import exit

    exit(main())
