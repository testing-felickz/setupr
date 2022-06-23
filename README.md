# drekkar

[![Release](https://img.shields.io/github/v/release/worldr/drekkar)](https://img.shields.io/github/v/release/worldr/drekkar)
[![Build status](https://img.shields.io/github/workflow/status/worldr/drekkar/merge-to-main)](https://img.shields.io/github/workflow/status/worldr/drekkar/merge-to-main)
[![Commit activity](https://img.shields.io/github/commit-activity/m/worldr/drekkar)](https://img.shields.io/github/commit-activity/m/worldr/drekkar)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://worldr.github.io/drekkar/)
[![Code style with black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports with isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/)
[![License](https://img.shields.io/github/license/worldr/drekkar)](https://img.shields.io/github/license/worldr/drekkar)

Drekkar ships the Worldr infrastructure…

- **Github repository**: <https://github.com/worldr/drekkar/>
- **Documentation** <https://worldr.github.io/drekkar/>

## Releasing a new version

- Create an API Token on [Pypi](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting
[this page](https://github.com/worldr/drekkar/settings/secrets/actions/new).
- Create a [new release](https://github.com/worldr/drekkar/releases/new) on Github.
Create a new tag in the form ``*.*.*``.

For more details, see [here](https://fpgmaas.github.io/cookiecutter-poetry/releasing.html).

## Development

### pre-commit

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
