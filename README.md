# Drakkar

<img src="https://github.com/worldr/drakkar/blob/main/docs/assets/logo.png" width=25% height=25% >

[![Release](https://img.shields.io/github/v/release/worldr/drakkar)](https://img.shields.io/github/v/release/worldr/drakkar)
[![Build status](https://img.shields.io/github/workflow/status/worldr/drakkar/merge-to-main)](https://img.shields.io/github/workflow/status/worldr/drakkar/merge-to-main)
[![Commit activity](https://img.shields.io/github/commit-activity/m/worldr/drakkar)](https://img.shields.io/github/commit-activity/m/worldr/drakkar)

[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://worldr.github.io/drakkar/)
[![Code style with black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports with isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/)
[![License](https://img.shields.io/github/license/worldr/drakkar)](https://img.shields.io/github/license/worldr/drakkar)

----

## Drakkar ships the Worldr infrastructure…

- **Github repository**: <https://github.com/worldr/drakkar/>
- **Documentation** <https://worldr.github.io/drakkar/>

## Releasing a new version

- Create an API Token on [Pypi](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting
[this page](https://github.com/worldr/drakkar/settings/secrets/actions/new).
- Create a [new release](https://github.com/worldr/drakkar/releases/new) on Github.
Create a new tag in the form ``*.*.*``.

For more details, see [here](https://fpgmaas.github.io/cookiecutter-poetry/releasing.html).

## Development

### pre-commit

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

### Conventional commits

You can use [commitizen](https://github.com/commitizen-tools/commitizen) to
create correct conventional commits if it helps you. If not, the `pre-commit`
hooks should validate if your commit is correct or not.

More on [conventional
commits](https://www.conventionalcommits.org/en/v1.0.0/).

Note that a GHA should run to make sure that the RP title is a valide
[conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).

## Testing

### GnuPG

We use [python-gnupg](https://gnupg.readthedocs.io/en/latest/#) and
[GnuPG](https://gnupg.org/).

The file `tests/charon-lord-dunsany.txt` is a short story by [Lord
Dunsany](https://en.wikipedia.org/wiki/Lord_Dunsany) about Charon. It has a
valid and an invalid signature files. *If the main file is edited, a new valid
signature needs to be generated.*

```bash
gpg --default-key "worldr-for-mst@worldr.com" --armour --output tests/NEW-charon-lord-dunsany-good.sig --detach-sign tests/charon-lord-dunsany.txt
```

You can test the signature files like so:

```bash
√ .venv; gpg --verify tests/charon-lord-dunsany-good.sig tests/charon-lord-dunsany.txt
gpg: Signature made Tue 28 Jun 2022 11:27:22 BST
gpg:                using RSA key 935D282626A16D1A0430487D65A277F7800F774C
gpg:                issuer "worldr-for-mst@worldr.com"
gpg: Good signature from "Worldr Technologies (MST application) <worldr-for-mst@worldr.com>" [ultimate]
√ .venv; gpg --verify tests/charon-lord-dunsany-bad.sig tests/charon-lord-dunsany.txt
gpg: Signature made Tue 28 Jun 2022 11:24:42 BST
gpg:                using RSA key 935D282626A16D1A0430487D65A277F7800F774C
gpg:                issuer "worldr-for-mst@worldr.com"
gpg: BAD signature from "Worldr Technologies (MST application) <worldr-for-mst@worldr.com>" [ultimate]
```

There is a test that runs iff the Worldr key is in the local key ring. This
should be true for most developers. If not, the test is skipped.

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
