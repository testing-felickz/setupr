# Development

## Virtual Environment

Please use a virtual environment when developing and do run `tox` from time to
time to make sure that your changes are compatible with all the Python version
we have to support.

## pre-commit

Please use [pre-commit](https://pre-commit.com/) which can be setup via:

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

## Conventional commits

We use [conventional
commits](https://www.conventionalcommits.org/en/v1.0.0/).

You can use [commitizen](https://github.com/commitizen-tools/commitizen) to
create correct conventional commits if it helps you. If not, the `pre-commit`
hooks should validate if your commit is correct or not.

Note that a GHA should run to make sure that the RP title is a valide
[conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).

## Testing

### PyTest

There are two sets of test one can run `task tests-fast` and `task tests`. The
former will not run the functional tests that actually do use the network and
take time to run. The latter will run all the tests.

### Coverage

We have 100% test coverage — with a few cheats using `pragma: no sover` for
code should be excluded.

The GHA should create a nice coverage report.

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
```

There is a test that runs iff the Worldr key is in the local key ring. This
should be true for most developers. If not, the test is skipped.

The script `runme.sh` and its signature `runme.sig` are used in the functinal tests. Any changes to that script will require a new signature so that the script can run.

```bash
gpg --default-key "worldr-for-mst@worldr.com" --armour --output tests/runme-v1.0.0.sig --detach-sign tests/runme-v1.0.0.sh
```

## Logs

If you run setupr and get files, then you might get a lot of log files. Those
are generally safe to remove en mass.

## Release

There is a GitHub Action that will creeate a [semantic
release](https://python-semantic-release.readthedocs.io/en/latest/) for
Setupr.

This is why [conventional
commits](https://www.conventionalcommits.org/en/v1.0.0/) are essential,
especially in PR titles.

## Linters

We replaced flake8 by [flakehaven](https://github.com/flakeheaven/flakeheaven) ([docs](https://flakeheaven.readthedocs.io/en/latest/index.html)) which uses some [awesome flake8 plugins](https://github.com/DmytroLitvinov/awesome-flake8-extensions).

## Worldr installation data YAML

Do ensure that [yamllint](https://github.com/adrienverge/yamllint) returns without either errors or warnings:

```bash
yamllint --strict tests/test.env.yaml
yamllint --strict worldr-env-schema.yaml
```

We use [ruamel.yaml](https://yaml.readthedocs.io/en/latest/index.html) for parsing.

```python
from pathlib import Path
from ruamel.yaml import YAML
yaml = YAML()
data = yaml.load(Path("test.env.yaml"))
```

We use [Cerebus](https://docs.python-cerberus.org/en/stable/index.html#) as a schema-like validator for installation data YAML. There is a unit test to check that the schema is valid.

```python
from setupr.schema import WORLDR_INSTALLATION_DATA_SCHEMA
    v = Validator(WORLDR_INSTALLATION_DATA_SCHEMA)
    v.validate(YAML().load(Path("tests/test.env.yaml")))
    print(v.errors)
```
