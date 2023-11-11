# Changelog

## 0.5.2 (2023-11-11)

### Bugs Fixed

- Convert module to package, enabling us to ship the default template
  as package data. ([#26][])

[#26]: https://github.com/lektor/lektor-tags/pull/26

## 0.5.1 (2022-10-19)

### Bugs Fixed

- Ignore duplicate tags (on a single page) when counting. ([#25][])
- When applicable, limit tags to those specified in the
  [`tags`][config-tags] config setting ([#25][])

[#25]: https://github.com/lektor/lektor-tags/pull/25
[config-tags]: https://github.com/lektor/lektor-tags#tags

## 0.5.0 (2022-02-11)

Added a `tagweights` jinja global that provides reference counts of
tags and other bits useful for constructing tag clouds or similar types
of tag lists. ([#19][] — Thank you Louis Paternault!)

[#19]: https://github.com/lektor/lektor-tags/pull/19

## 0.4.1 (2022-01-09)

Switch to setup.cfg and a PEP517-build.

## 0.4.0 (2021-09-18)

Update to the README as well as test, pre-commit and CI configuration.

## 0.3 (2018-12-15)

Fixes #2, persisting self.pad. Version bump.

## 0.2 (2018-05-13)

Readme and setup.py updates, changed the name and description, bump to 0.2.
