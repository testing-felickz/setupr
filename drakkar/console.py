# -*- coding: utf-8 -*-
""" … """
import logging
import logging.config
import sys
import typing

import click
import semver
import structlog
from click_help_colors import HelpColorsCommand  # type: ignore
from rich.traceback import install

from drakkar import __version__
from drakkar.commands import pgp_key, pre_flight
from drakkar.get_url import Downloader
from drakkar.print import wprint

# Click.
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

# Rich.
install(show_locals=True)


pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    # Add extra attributes of LogRecord objects to the event dictionary
    # so that values passed in the extra parameter of log methods pass
    # through to log output.
    structlog.stdlib.ExtraAdder(),
]


logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "drakkar.log",
                "formatter": "plain",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 7,
            },
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }
)


class MutuallyExclusiveOption(click.Option):
    """Mutually Exclusive Option.

    This is a click option that can be used to make sure that only one of a
    set of options can be used at the same time.

    Note that there is no type hinting… I tried and failed.
    """

    def __init__(self, *args, **kwargs):  # type: ignore
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")
        if self.mutually_exclusive:  # pragma: no cover
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help + (
                " NOTE: This argument is mutually exclusive with "
                " arguments: [" + ex_str + "]."
            )
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):  # type: ignore
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                f"Illegal usage: `{self.name}` is mutually exclusive with "
                f"arguments `{', '.join(self.mutually_exclusive)}`."
            )
        return super().handle_parse_result(ctx, opts, args)


def validate_semver(
    ctx: click.core.Context, param: click.Option, value: str
) -> typing.Union[None, semver.version.Version]:
    """Validate the option is semver compliante.

    If the option is None, do nothing."""
    if value is None:
        return None
    try:
        ver = semver.version.VersionInfo.parse(value)
        return ver
    except ValueError as ex:
        raise click.UsageError(f"{value}: {ex}")


@click.command(
    context_settings=CONTEXT_SETTINGS,
    cls=HelpColorsCommand,
    help_headers_color="blue",
    help_options_color="magenta",
)
@click.option(
    "-i",
    "--install",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["debug", "backup"],
    default=None,
    nargs=1,
    type=str,
    metavar="<semver>",
    callback=validate_semver,
    help=(
        "Gets Worldr PGP key (if needed), run pre-flight checks, and "
        "download the installation script with signature to verify it."
    ),
)
@click.option(
    "-d",
    "--debug",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["install", "backup"],
    default=None,
    nargs=1,
    type=str,
    metavar="<semver>",
    callback=validate_semver,
    help=(
        "Gets Worldr PGP key (if needed), and "
        "download the debug script with signature to verify it."
    ),
)
@click.option(
    "-b",
    "--backup",
    default=None,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["debug", "install"],
    nargs=1,
    type=str,
    metavar="<semver>",
    callback=validate_semver,
    help=(
        "Gets Worldr PGP key (if needed), and "
        "download the backup & restore script with signature to verify it."
    ),
)
@click.option(
    "-l",
    "--log-level",
    default="info",
    show_default=True,
    type=click.Choice(
        ["notset", "debug", "info", "warning", "error", "critical"],
        case_sensitive=False,
    ),
    help="Chose the logging level from the available options.",
)
@click.option(
    "-v", "--version", is_flag=True, help="Print the version and exit"
)
@click.option("--verbose", is_flag=True, help="Print the logs to stdout")
def main(
    install: click.Option,
    debug: click.Option,
    backup: click.Option,
    log_level: str,
    version: bool,
    verbose: bool,
) -> None:
    """Drakkar ships the Worldr infrastructure.

    Note that <semver> must be a valid semantic version. This is different for
    all the scripts. Please check the user documentation for the exact values.
    """
    # Version
    if version:
        click.echo(__version__)
        sys.exit(0)

    # Logging levels
    # https://www.structlog.org/en/stable/_modules/structlog/_log_levels.html?highlight=log%20level  # noqa
    _lvl = {
        "critical": 50,
        "error": 40,
        "warning": 30,
        "info": 20,
        "debug": 10,
        "notset": 0,
    }
    if not verbose:  # pragma: no cover
        # We remove the handlers if we do not want it…
        logging.getLogger().removeHandler(logging.getLogger().handlers[0])
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.filter_by_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            # structlog.processors.format_exc_info,  # Pretty exceptions!
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        # wrapper_class=structlog.stdlib.BoundLogger,
        wrapper_class=structlog.make_filtering_bound_logger(_lvl[log_level]),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger("main")
    # logger.debug("This is a debug message")
    # logger.info("This is a info message", lvl=log_level)
    # logger.warning("This is a warn message")
    # logger.error("This is a error message")
    # logger.critical("This is a critical message")
    # sys.exit(0)

    dlr = Downloader()

    if install is not None:
        wprint(
            f"Downloading [i]installation[/i] script at version [b]{install}[/b]",  # noqa
            level="info",
        )
        if (
            not pgp_key()
            or not pre_flight()
            or not dlr.get("install", f"v{install}")
        ):
            logger.error("Failure to get install script.", version=install)
            wprint("Operation failed.", level="failure")
            sys.exit(1)
        logger.info("Success", script="install")

    elif debug is not None:
        wprint(
            f"Downloading [i]debugging[/i] script at version [b]{debug}[/b]",
            level="info",
        )
        if not pgp_key() or not dlr.get("debug", f"v{debug}"):
            logger.error("Failure to get debug script.", version=debug)
            wprint("Operation failed.", level="failure")
            sys.exit(1)
        logger.info("Success", script="debug")

    elif backup is not None:
        wprint(
            f"Downloading [i]backup & restore[/i] script at version [b]{backup}[/b]",  # noqa
            level="info",
        )
        if not pgp_key() or not dlr.get("backup", f"v{backup}"):
            logger.error("Failure to get backup script.", version=backup)
            wprint("Operation failed.", level="failure")
            sys.exit(1)
        logger.info("Success", script="backup-restore")

    else:
        wprint(
            "You [i]must[/i] specify -i, -b, or -d and a semver version",
            level="warning",
        )  # noqa
        logger.error("You must specify an option.")
        wprint("Operation failed.", level="failure")
        sys.exit(1)

    wprint("Operation was successful.", level="success")
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
