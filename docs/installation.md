# Installation

## PyPI

*This is the recommended way to install setupr… Maybe?*

1. [OPTIONAL] Create a [Python virtual
   environement](https://docs.python.org/3/library/venv.html). This will allow
   for proper isolation with your system. Note that
   [direnv](https://direnv.net/) is a useful to automatically load any
   virtual environement.
1. `pip install setupr` to install setupr itself.

***This will only work after we release it to PyPI…***

## GitHub release

1. Download the wheel file from [the latest
   release](https://github.com/worldr/setupr/releases).
1. [OPTIONAL] Create a [Python virtual
   environement](https://docs.python.org/3/library/venv.html). This will allow
   for proper isolation with your system. Note that
   [direnv](https://direnv.net/) is a useful to automatically load any
   virtual environement.
1. Run `pip install setupr-x.y.z-py3-none-any.whl` where `x.y.z` is the
   latest version.
1. Run `setupr --help`.

## Source

1. Download the source code from GitHub.
1. Run `poetry install`. See [the poetry
   documentation](https://python-poetry.org/docs/cli/#install) for more
   details.
1. Run `setupr --help`.
