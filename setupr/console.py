# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""Console entry point."""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Optional

import click
import semver  # type: ignore
import structlog
from click_help_colors import HelpColorsCommand  # type: ignore
from rich.console import Console
from rich.prompt import Confirm
from rich.traceback import install

from setupr import __version__
from setupr.commands import pgp_key, pre_flight
from setupr.downloader import Downloader
from setupr.gbucket import InstallationData, InstallationDataError
from setupr.print import COLOUR_INFO, wprint
from setupr.utils import VersionCheck, check_if_latest_version

# Rich.
install(show_locals=True)

EXIT_CODE_SUCCESS = 0
EXIT_CODE_OPERATION_FAILED = 1
EXIT_CODE_SCRIPT_FAILED = 2
EXIT_CODE_SERVICE_ACCOUNT_FAILED = 3
EXIT_CODE_YAML_DATA_FAILED = 4


pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    # Add extra attributes of LogRecord objects to the event dictionary
    # so that values passed in the extra parameter of log methods pass
    # through to log output.
    structlog.stdlib.ExtraAdder(),
]


def configure_logging(log_level: str, verbose: bool) -> None:
    """Configure all the logging."""
    # Logging levels
    # https://www.structlog.org/en/stable/_modules/structlog/_log_levels.html?highlight=log%20level
    _lvl = {
        "critical": 50,
        "error": 40,
        "warning": 30,
        "info": 20,
        "debug": 10,
        "notset": 0,
    }

    # Structlog processors. Order appears to matter…
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    class VerboseFilter(logging.Filter):
        """Filter log entries on verbose flag."""

        def __init__(self, param: str = "") -> None:
            self.param = param
            super()

        def filter(self, _: logging.LogRecord) -> bool:
            # We do not care about record thus mark it as _.
            return verbose

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,  # tabula raza.
            "filters": {
                "myfilter": {
                    "()": VerboseFilter,
                    "param": "noshow",
                }
            },
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": shared_processors
                    + [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,  # noqa: E501
                        structlog.processors.JSONRenderer(),
                    ],
                    "foreign_pre_chain": pre_chain,
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": shared_processors
                    + [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,  # noqa: E501
                        structlog.dev.ConsoleRenderer(colors=True),
                    ],
                    "foreign_pre_chain": pre_chain,
                },
            },
            "handlers": {
                "default": {
                    "level": _lvl[log_level],
                    "class": "logging.StreamHandler",
                    "filters": ["myfilter"],
                    "formatter": "colored",
                },
                "file": {
                    "level": _lvl[log_level],
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": "setupr.log",
                    "formatter": "plain",
                },
            },
            # Define all the loggers you want!
            "loggers": {
                "setupr": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
                "gnupg": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
                "concurrent": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
                "plumbum": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
                "urllib3": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
                "requests": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
                "rich": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
                "asyncio": {
                    "handlers": ["default", "file"],
                    "level": _lvl[log_level],
                    "propagate": True,
                },
            },
        }
    )
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],  # type: ignore [arg-type]
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(_lvl[log_level]),
        cache_logger_on_first_use=True,
    )


class MutuallyExclusiveOption(click.Option):
    """Mutually Exclusive Option.

    This is a click option that can be used to make sure that only one of a
    set of options can be used at the same time.

    Note that there is no type hinting… I tried and failed.
    """

    def __init__(self, *args, **kwargs):  # type: ignore
        """Initialize."""
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
        """Handle parse result."""
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                f"Illegal usage: `{self.name}` is mutually exclusive with "
                f"arguments `{', '.join(self.mutually_exclusive)}`."
            )
        return super().handle_parse_result(ctx, opts, args)


def validate_semver(
    ctx: click.core.Context, param: click.Option, value: str
) -> Optional[Any]:
    """Validate the option is semver compliante.

    If the option is None, do nothing.
    """
    # logger = structlog.get_logger("setupr")
    # logger.debug("params", ctx=ctx, param=param, value=value)
    if value is None:
        return None
    try:
        ver = semver.VersionInfo.parse(value)
        return ver
    except ValueError as ex:
        raise click.UsageError(f"{value}: {ex}")


@click.command(
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
    "-s",
    "--service-account",
    default=None,
    type=click.Path(exists=True),
    metavar="<X.sa.json>",
    help=(
        "The service account to use."
        "if not provided, the program will guess…"
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
    help="Chose the logging level from the available options. "
    "This affect the file logs as well.",
)
@click.option(
    "-v", "--version", is_flag=True, help="Print the version and exit"
)
@click.option("--verbose", is_flag=True, help="Print the logs to stdout")
def main(  # noqa: C901
    install: click.Option,
    debug: click.Option,
    backup: click.Option,
    service_account: str,
    log_level: str,
    version: bool,
    verbose: bool,
) -> None:
    """Setupr ships the Worldr infrastructure.

    Note that <semver> must be a valid semantic version. This is
    different for all the scripts. Please check the user documentation
    for the exact values.
    """
    # Version
    if version:
        click.echo(__version__)
        sys.exit(EXIT_CODE_SUCCESS)

    configure_logging(log_level, verbose)
    logger = structlog.get_logger("setupr")
    logger.debug(
        "All the loggers",
        loggers=list(logging.root.manager.loggerDict),
    )

    console = Console()
    console.rule(f"[{COLOUR_INFO}]WORLDR setupr script")

    # Version check.
    check = check_if_latest_version()
    if check == VersionCheck.LATEST:
        wprint(f"This is the latest version {__version__}.", level="info")
    elif check == VersionCheck.LAGGING:
        wprint(
            "there is a new version available: please update.", level="warning"
        )
        if Confirm.ask("Exit and update?", default=True):
            wprint(
                "Please run [i]python -m pip install -U setupr[/i]",
                level="info",
            )
            sys.exit(EXIT_CODE_SUCCESS)
        wprint("Proceeding with old version…", level="warning")
    elif check == VersionCheck.UNKNOWN:
        wprint("Could not check for newer versons.", level="warning")
    else:  # pragma: no cover
        # This should never, ever happen!
        wprint("This is bug, please report!", level="error")

    # sys.exit(EXIT_CODE_SUCCESS)
    dlr = Downloader()

    if install is not None:
        data = None
        try:
            # import pdb; pdb.set_trace()
            path = None
            # We need to covert that option to a Path. We cannot set it as
            # default to "" since that will cause an error at the click level:
            # it will complain that this file does not exists. However, we
            # should be able to not specify the option, so it could be None.
            # However, then Path will raise because you cannot instanciate it
            # with None. Urgh.
            if service_account is None:
                path = None
            else:
                path = Path(service_account)
            data = InstallationData(service_account_json=path)
            if data.fetch():
                wprint("Got YMAL installation data.", level="info")
            else:
                wprint(
                    "YAML installation data was not found. We cannot proceed.",
                    level="failure",
                )
                sys.exit(EXIT_CODE_YAML_DATA_FAILED)
        except InstallationDataError as ex:
            logger.error("Error", ex=ex)
            wprint(f"{ex}.", level="failure")
            sys.exit(EXIT_CODE_SERVICE_ACCOUNT_FAILED)

        wprint(
            f"Using service account file {data.service_account_json}.",
            level="info",
        )

        wprint(
            f"Downloading [i]installation[/i] script at version [b]{install}[/b]",  # noqa: E501
            level="info",
        )
        if (
            not pgp_key()
            or not pre_flight()
            or not dlr.get("install", f"v{install}")
        ):
            logger.error("Failure to get install script.", version=install)
            wprint("Operation failed.", level="failure")
            sys.exit(EXIT_CODE_OPERATION_FAILED)
        if not dlr.execute_script(
            "worldr-aa",
            f"v{install}",
            data.service_account_json.as_posix(),  # type: ignore
            [data.blob_name],
        ):
            logger.error("Failure to execute install script.", version=install)
            wprint("Installation script failed.", level="failure")
            sys.exit(EXIT_CODE_SCRIPT_FAILED)
        logger.info("Success", script="install")

    elif debug is not None:
        wprint(
            f"Downloading [i]debugging[/i] script at version [b]{debug}[/b]",
            level="info",
        )
        if not pgp_key() or not dlr.get("debug", f"v{debug}"):
            logger.error("Failure to get debug script.", version=debug)
            wprint("Operation failed.", level="failure")
            sys.exit(EXIT_CODE_OPERATION_FAILED)
        if not dlr.execute_script("worldr-debug", f"v{debug}", "", []):
            logger.error("Failure to execute debug script.", version=install)
            wprint("Debug script failed.", level="failure")
            sys.exit(EXIT_CODE_SCRIPT_FAILED)
        logger.info("Success", script="debug")

    elif backup is not None:
        wprint(
            f"Downloading [i]backup & restore[/i] script at version [b]{backup}[/b]",  # noqa: E501
            level="info",
        )
        if not pgp_key() or not dlr.get("backup", f"v{backup}"):
            logger.error("Failure to get backup script.", version=backup)
            wprint("Operation failed.", level="failure")
            sys.exit(EXIT_CODE_OPERATION_FAILED)
        logger.info("Success", script="backup-restore")

    else:
        wprint(
            "You [i]must[/i] specify -i, -b, or -d and a semver version",
            level="warning",
        )
        logger.error("You must specify an option.")
        wprint("Operation failed.", level="failure")
        sys.exit(EXIT_CODE_OPERATION_FAILED)

    wprint("Operation was successful.", level="success")
    sys.exit(EXIT_CODE_SUCCESS)


if __name__ == "__main__":  # pragma: no cover
    main()
