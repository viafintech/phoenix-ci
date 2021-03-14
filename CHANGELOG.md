# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [1.0.5] - 2021-03-14
- first public release of Phoenix-CI
- renamed all occurences of "worker" to "runner" to be more consistent
- fixed using default servertype if none is given in a CI run

## [1.0.4] - 2020-01-24 (Internal release)
- added documentation and code comments for better understanding

## [1.0.3] - 2019-09-12 (Internal release)
- added a shell-runner fix for [debian buster issue](https://gitlab.com/gitlab-org/gitlab-runner/issues/4449)

## [1.0.2] - 2019-09-11 (Internal release)
- Changed default OS to Debian 10 Buster

## [1.0.1] - 2019-07-23 (Internal release)
- Reduced verbose output when running scale-up/down for pip/virtualenv
- Added feature to check for a running docker-daemon before registering runner
- Fixed issue with newest docker:dind image and automatic TLS generation
- Fixed smaller bugs

## [1.0.0] - 2019-06-05 (Internal release)
- Rewrite of worker creation/deletion without static numbering
  Now UUIDs are being used, so it's possible to delete any worker
  without having Phoenix-CI to fail deleting the others afterwards

## [1.0.0-beta2] - 2019-06-01 (Internal release)
- Renamed Gitlab-HCloud-CI to Phoenix-CI
- Removed unused hcloud imports
- Removed support for Python 2.x due to upcoming EOL
- Fixed reading cloud-config data without using CLI tools
- Merged both worker scaling methods to a single generic one
- Refactoring of the print methods
- Renamed cloud-config yaml to yml
- Added packer 1.4.1 installation for shell workers
- Added docker & docker-compose installation for shell workers
- Added shellcheck & bashate installation for shell workers
- Added ansible installation for shell workers
- Made shell workers only run jobs with "shell" tag

## [1.0.0-beta1] - 2019-05-12 (Internal release)
- Initial release / MVP
