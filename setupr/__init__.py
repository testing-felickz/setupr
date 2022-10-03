# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""Setupr."""
from importlib import metadata

__version__ = metadata.version(__package__)

del metadata  # optional, avoids polluting the results of dir(__package__)
