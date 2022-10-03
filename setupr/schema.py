# -*- coding: utf-8 -*-
# Copyright © 2022-present Worldr Technologies Limited. All Rights Reserved.
"""YAML schema for setupr via Cerebrus."""

# Vicously taken form:
# https://validators.readthedocs.io/en/latest/_modules/validators/domain.html#domain
domain_pattern = (
    r"^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|"
    r"([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|"
    r"([a-zA-Z0-9][-_.a-zA-Z0-9]{0,61}[a-zA-Z0-9]))\."
    r"([a-zA-Z]{2,13}|[a-zA-Z0-9-]{2,30}.[a-zA-Z]{2,3})$"
)

# A simple email pattern. It is not RFC compliant but should be good enough
# for our needs.
email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# The schema…
WORLDR_INSTALLATION_DATA_SCHEMA = {
    "WORLDR_COMPANY_NAME": {"required": True, "type": "string"},
    "WORLDR_DOMAIN": {
        "required": True,
        "type": "string",
        "regex": domain_pattern,
    },
    "MST_ENABLED": {"required": True, "type": "boolean"},
    "HELM_USERNAME": {"required": True, "type": "string"},
    "DEPLOYMENT_ID": {"required": True, "type": "string"},
    "LICENSE_SERVER_SECRET": {
        "required": True,
        "type": "string",
        "minlength": 64,
    },
    "HELM_PASSWORD": {"required": True, "type": "string", "minlength": 23},
    "WORLDR_ADMIN_EMAIL": {
        "required": True,
        "type": "string",
        "regex": email_pattern,
    },
    "type": {"required": True, "type": "string", "regex": r"(^mst|core|wa$)"},
    "mst": {
        "required": False,
        "type": "dict",
        "schema": {
            "MST_FULLNAME": {"required": True, "type": "string"},
            "MST_CLIENT_ID": {
                "required": True,
                "type": "string",
                "minlength": 36,
                "maxlength": 36,
            },
            "AZURE_CLIENT_SECRET": {"required": True, "type": "string"},
        },
    },
    "core-type": {
        "required": False,
        "type": "dict",
        "schema": {
            "ADMIN_TOOL_ENABLED": {"required": True, "type": "boolean"},
            "PUSH_PROXY_ENABLED": {"required": True, "type": "boolean"},
            "WORLDR_SENDPUSHNOTIFICATIONS": {
                "required": True,
                "type": "boolean",
            },
        },
    },
    "wa-type": {
        "required": False,
        "type": "dict",
        "schema": {
            "WA_ENABLED": {"required": True, "type": "boolean"},
        },
    },
    "ADDITIONAL_ENV": {
        "required": False,
        "type": "dict",
        "schema": {
            "SONIC_SEARCH_ENABLED": {"required": False, "type": "boolean"},
            "WORLDR_ADMIN_PASSWORD": {"required": False, "type": "string"},
        },
    },
}
