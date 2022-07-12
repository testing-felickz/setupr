---
tags:
  - worldr
  - setup
  - infrastructure
  - k8s
  - k3s
  - gitops
  - GPG
---
# Requirements

## Setup

### The old way

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

### The new way

If we release this as open source, we can use the [Python Package
Index](https://pypi.org/) and thus all customers need to do is run `python -m
pip install drakkar` to get it. Updating the script is simper too: `python -m
pip install --update drakkar`.

If not, we can provide a wheel file (needs checksums) or run our own package
index. The former is the most cumbersome, whereas the latter is much more work
than just using [pypi](https://pypi.org/).

* [X] GPG: Install and setup then uploads the Worldr GPG key -- if needed.
* [X] Downloads & verify the infrastructure installation script.
* [X] Downloads & verify the infrastructure debug script.
* [X] Runs all pre-flight checks with [goss](https://github.com/aelsabbahy/goss) -- if needed.
* [X] Backup and restore.
* [ ] Easy Vault credentials access for first time: backups!

All these steps can have (unit? BDD?) tests so we can be sure they work as
intended and new changes do not break functionality.

## Installation

***⚠ We are not replacing the installation script, just yet.***

This is premature as the installation script is a high state of flux at the
time. Importantly, the DevOps use the install script without running the
setup. This allows for faster testing cycles.
