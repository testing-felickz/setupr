# Usage

## Notes

The `VERSION` option needs to be a valid [semantic verson](https://semver.org/).

The Worldr PGP key will be downloaded and installed if needed. This is used to
check the digital signatures of all the scripts downloaded. If one of these
signatures is invalid, please contact Worldr immediatly and do not proceed
with the installation.

## Installation

This command will download and verify the installation script: `drakkar --install VERSION`

Pre flight checks will be run:
1. The **securtiy checks** are only advisory and the installation will proceed
   even if there are warnings. Worldr does recommend that you fix these
   warning as soon as possible.
1. The **infrastructure checks** are mandatory and any warning will stop the
   installation process. Please fix those before invoquing drakkar again.

## Debug

This command will download and verify the debug script: `drakkar --debug VERSION`

## Backup & Restore

This command will download and verify the backup and restore script: `drakkar --backup VERSION`

## Logs

Drakkar can be run with variouse logging levels. By default, the level is `info` and this can be changed.

Drakkar will write all logs to its log file (`drakkar.log`) which gets rotated
if too full and archives. In case of failure to install, this log file would
be invaluable to Worldr staff in diagnosing your issue.

## Example of use

![Drakkar](./assets/drakkar-example.gif)
