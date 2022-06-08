# Changelog for `greatday`

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to
[Semantic Versioning].

[Keep a Changelog]: https://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: https://semver.org/


## [Unreleased](https://github.com/bbugyi200/greatday/compare/1.0.0...HEAD)

No notable changes have been made.


## [1.0.0](https://github.com/bbugyi200/greatday/compare/0.4.0...1.0.0) - 2022-06-08

### Changed

* Multiple significant optimizations (e.g. caching `GreatTag.from_line()` calls).
* Major refactoring to support v1.0.0 of magodo library.

### Miscellaneous

* Increase test coverage to >=80% (currently at 82%).
* First stable release of greatday.


## [0.4.0](https://github.com/bbugyi200/greatday/compare/0.3.0...0.4.0) - 2022-05-01

### Added

* Added new `greatday tui` subcommand (intended to be the main interface to greatday).

### Removed

* *BREAKING CHANGE*: Remove `greatday start` subcommand. Use `greatday tui` instead.

### Miscellaneous

* Many other changes were made. I have not been diligent about releasing new versions.


## [0.3.0](https://github.com/bbugyi200/greatday/compare/0.2.0...0.3.0) - 2022-02-13

### Added

* The `greatday start` command now works.


## [0.2.0](https://github.com/bbugyi200/greatday/compare/0.1.0...0.2.0) - 2022-01-15

## Added

* The `greatday add` command now works.

## Miscellaneous

* First _real_ release (the last release's code was 100% generic---still not a working product).


## [0.1.0](https://github.com/bbugyi200/greatday/releases/tag/0.1.0) - 2022-01-09

### Miscellaneous

* First release.
