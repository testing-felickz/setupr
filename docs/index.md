# drakkar

[![Release](https://img.shields.io/github/v/release/worldr/drakkar)](https://img.shields.io/github/v/release/worldr/drakkar)
[![Build status](https://img.shields.io/github/workflow/status/worldr/drakkar/merge-to-main)](https://img.shields.io/github/workflow/status/worldr/drakkar/merge-to-main)
[![Commit activity](https://img.shields.io/github/commit-activity/m/worldr/drakkar)](https://img.shields.io/github/commit-activity/m/worldr/drakkar)
[![License](https://img.shields.io/github/license/worldr/drakkar)](https://img.shields.io/github/license/worldr/drakkar)

***Drakkar ships the Worldr infrastructure…***

## Drakkar: The New Way

A installing is as simple as running two commands:

1. `pip install drakkar` to install drakkar itself.
1. `drakkar -i 1.2.3` for installing version `1.2.3`.

Note that currently drakkar does not execute the installation script. This
feature is coming soon…

![Drakkar](./assets/drakkar-example.gif)

## The Old Way

This is what the `worldr_setup.bash` (in gitops) script did:

* Install GPG Worldr key & install GPG if needed.
* Downloads & verify the infrastructure installation script.
* Downloads & verify the debug script.
* Downloads & verify the backup & restore script.
* Downloads & installs [goss](https://github.com/aelsabbahy/goss).
* Runs security pre-flight checks.
* Runs infrastructure pre-flight checks.
* Verifies that all downloaded scripts are `bash` ones.

When we install it (via `curl`), we need to check its `sha256sum` which is
cumbersome.
