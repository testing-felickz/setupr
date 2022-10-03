# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
from pathlib import Path

from cerberus import Validator  # type: ignore
from ruamel.yaml import YAML

from setupr.schema import WORLDR_INSTALLATION_DATA_SCHEMA


def test_schema_success() -> None:
    """Test that the schema validates successfully."""
    v = Validator(
        WORLDR_INSTALLATION_DATA_SCHEMA, allow_unknown={"type": "string"}
    )
    assert v.validate(  # pyright: ignore
        YAML().load(Path("tests/ranni-valid.env.yaml"))
    ), f"There are validation errors: {v.errors}"  # pyright: ignore
