# Contributing


## How to submit feedback?

The best way to submit feedback is to [file an issue][1].

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions are
  welcome :).


## Developer's Guide

### Basic Usage 🔢

Before making a PR please run the following

* Optional one time setup: run `make use-docker` if you need to build/test this
  with docker
* `make lint` to check for any format or convention issues
* `make test` to run all tests

### How do I ... ❓

<details><summary>🔧 See available make targets</summary>

To see available make targets, simply run `make`.

</details>

<details><summary>🐳 Switch to and from using Docker</summary>

To start using Docker, run `make use-docker`. Every subsequent make command you
run will then be run inside the associated container whenever appropriate.

To stop using Docker, run `make remove-docker`. Every subsequent make command
you run will then be run inside your native virtual environment whenever
appropriate.

</details>

<details><summary>🛠 Add a new pip dependency</summary>

New dependencies need to be added to `requirements.in`. Your `requirements.txt`
will then automatically be updated to reflect those changes the next time a
relevant make target is run. Alternatively, you can run `make
update-requirements`.

Note:
* Before any make command is run, requirements are synced so that the
  development environment matches your `requirements.txt` exactly i.e. extra
  packages that are not present in the `requirements.txt` are removed and any
  missing packages are installed. This helps providing a consistent environment
  across platforms, and ensures that whenever requirements change, only minimal
  updates are performed.
* Check out
  [pip-tools](https://github.com/jazzband/pip-tools#pip-tools--pip-compile--pip-sync)
  for more information.

</details>

<details><summary>🙈 Ignore linting violations</summary>

For
[flake8](https://flake8.pycqa.org/en/latest/user/configuration.html#configuration-locations)
[violations](https://wemake-python-stylegui.de/en/latest/pages/usage/violations/index.html),
you can:
* ignore a rule for a single line of code using a `#noqa` comment e.g.
  ```python x = 1 # noqa: WPS111 ```
* [ignore](https://flake8.pycqa.org/en/latest/user/violations.html#in-line-ignoring-errors)
  a rule for an entire file by adding it to `flake8.per-file-ignores` inside
  `setup.cfg`.
* [exclude](https://flake8.pycqa.org/en/latest/user/violations.html#ignoring-entire-files)
  an entire file from flake8 checks by adding it to `flake8.exclude` inside
  `setup.cfg`.
* ignore a rule for all files by adding it to the `flake8.ignore` list inside
  `setup.cfg`.

For
[mypy](https://mypy.readthedocs.io/en/stable/config_file.html#the-mypy-configuration-file)
violations, you can:
* [ignore](https://mypy.readthedocs.io/en/stable/common_issues.html#spurious-errors-and-locally-silencing-the-checker)
  type checking for a single line of code using a `# type: ignore` comment.
* [ignore](https://mypy.readthedocs.io/en/stable/common_issues.html#ignoring-a-whole-file)
  type checking for an entire file by putting a `# type: ignore` comment at the
  top of a module (before any statements, including imports or docstrings).

For
[pydocstyle](http://www.pydocstyle.org/en/5.0.1/usage.html#configuration-files)
violations, you can:
* [ignore](http://www.pydocstyle.org/en/5.0.1/usage.html#in-file-configuration)
  a rule for a single line of code using a `# noqa` comment (this can be
  combined with flake8 exclusions).
* exclude an entire file from pydocstyle checks by excluding it from
  `pydocstyle.match` inside `setup.cfg`.
* ignore a rule for all files by adding it to the `pydocstyle.ignore` list
  inside `setup.cfg`.

For [coverage](https://coverage.readthedocs.io/en/v4.5.x/config.html#)
violations, you can:
* [exclude](http://www.pydocstyle.org/en/5.0.1/usage.html#in-file-configuration)
  a single line of code using a `# pragma: no cover` comment.
* [exclude](https://coverage.readthedocs.io/en/v4.5.x/source.html#specifying-source-files)
  an entire file from coverage checks by adding it to the `coverage:run.omit`
  list inside `setup.cfg`.
* [exclude](https://coverage.readthedocs.io/en/v4.5.x/excluding.html#advanced-exclusion)
  all lines matching a given pattern by adding it to the
  `coverage:report.exclude_lines` list inside `setup.cfg`.

</details>

<details><summary>🧪 Run specific tests</summary>

First, get a shell inside your development environment by running `make
dev-shell`.

You can then use the pytest `-k` option to select tests based on their names,
e.g.

```bash
python -m pytest -k "included_test"
```

You can also use "and", "or" and "not" keywords e.g.

```bash
python -m pytest -k "included_test or not excluded"
```

</details>

<details><summary>📄 Build and view docs from a local version</summary>

You can generate docs locally by running `make build-docs`. You can then see
the generated docs by running

```bash
cd docs/build
python -m http.server
```

and going to http://localhost:8000/

</details>

<details><summary>🍪
Update my project to match the cookiecutter which generated it
</summary>

This project is enabled with `cruft` to be able to update the template with any
improvements made in the [cc-python][4] cookiecutter which generated it.

* `make check-cc` will report if this project is up to date or out of sync with
  the cookiecutter.
* `make update-cc` will update this project to be in sync with the cc-python
  cookiecutter. This can give improvements or new features which are added to
  the template after this project was created. Note one should do this on a
  clean branch. After running this it is a good idea to run `make all` to
  rebuild everything and ensure things still work after the update.

</details>

### Badges 📛

Every badge shown below corresponds with a development tool used to maintain
this project. Every badge is clickable and links back to that project's github
/ documentation site:

_tools / frameworks used by test suite (i.e. used by `make test`):_

[![Framework: pytest](https://img.shields.io/badge/framework-pytest-a76465)](https://github.com/pytest-dev/pytest)
[![Framework: doctest](https://img.shields.io/badge/framework-doctest-66a6f6)](https://docs.python.org/3/library/doctest.html)
[![Runner: tox](https://img.shields.io/badge/runner-tox-9da246)](https://github.com/tox-dev/tox)
[![Mocks: pytest-mock](https://img.shields.io/static/v1?label=mocks&message=pytest-mock&color=9c70d7)](https://github.com/pytest-dev/pytest-mock)
[![Snapshots: syrupy](https://img.shields.io/static/v1?label=snapshots&message=syrupy&color=436fa8)](https://github.com/tophat/syrupy)

_linters used to maintain code quality (i.e. used by `make lint`):_

[![Linter: pylint](https://img.shields.io/badge/linter-pylint-ffff00)](https://github.com/PyCQA/pylint)
[![Linter: flake8](https://img.shields.io/badge/linter-flake8-008080)](https://github.com/PyCQA/flake8)
[![Types: mypy](https://img.shields.io/badge/types-mypy-cd00cd)](https://github.com/python/mypy)
[![Docstrings: pydocstyle](https://img.shields.io/badge/docstrings-pydocstyle-AFD3E6)](https://github.com/PyCQA/pydocstyle)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/imports-isort-ef8336)](https://github.com/PyCQA/isort)

_tools / frameworks used to render documentation (i.e used by `make build-docs`):_

[![Rendered By: sphinx](https://img.shields.io/badge/rendered%20by-sphinx-9cc676)](https://github.com/sphinx-doc/sphinx)
[![Hosted On: ReadTheDocs](https://img.shields.io/badge/hosted%20on-ReadTheDocs-e08839)](https://docs.readthedocs.io/en/stable/)
[![Types: sphinx-autodoc-typehints](https://img.shields.io/static/v1?label=API&message=sphinx-autodoc-typehints&color=9c70d7)](https://github.com/agronholm/sphinx-autodoc-typehints)
[![Markdown: m2r2](https://img.shields.io/badge/markdown-m2r2-8e1e3d)](https://github.com/CrossNox/m2r2)

_miscellaneous tools used to maintain this project:_

[![Cookiecutter Updates: cruft](https://img.shields.io/badge/cc%20updates-cruft-6a4aef)](https://github.com/cruft/cruft)
[![Requirements: pip-tools](https://img.shields.io/static/v1?label=requirements&message=pip-tools&color=a77bb5)](https://github.com/jazzband/pip-tools)
[![Releases: bump2version](https://img.shields.io/badge/releases-bump2version-163b1a)](https://github.com/c4urself/bump2version)
[![Versioning: setuptools_scm](https://img.shields.io/static/v1?label=versioning&message=setuptools-scm&color=f61a61)](https://github.com/pypa/setuptools_scm)


## New Releases

This section serves as a reminder to the maintainers of this project on how to
release a new version of this package to [PyPI][3].

Make sure all your changes are committed, that you have added a new section to
the [CHANGELOG.md][5] file, and that you have [bumpversion][2] installed. Then
run:

```bash
bumpversion patch  # possible values: major / minor / patch
git push
git push --tags
```

A new version of `greatday` will then deploy to
PyPI if all CI checks pass.


[1]: https://github.com/bbugyi200/greatday/issues/new/choose
[2]: https://github.com/c4urself/bump2version
[3]: https://pypi.org/project/greatday
[4]: https://github.com/python-boltons/cc-python
[5]: https://github.com/bbugyi200/greatday/blob/master/CHANGELOG.md
