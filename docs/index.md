# hatch-pip-compile

[hatch] plugin to use [pip-compile] to manage project dependencies and lockfiles.

[![PyPI](https://img.shields.io/pypi/v/hatch-pip-compile?color=blue&label=🔨%20hatch-pip-compile)](https://github.com/juftin/hatch-pip-compile)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-pip-compile)](https://pypi.python.org/pypi/hatch-pip-compile/)
[![GitHub License](https://img.shields.io/github/license/juftin/hatch-pip-compile?color=blue&label=License)](https://github.com/juftin/hatch-pip-compile/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-lightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![Gitmoji](https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg)](https://gitmoji.dev)

## Installation

```shell
pip install hatch-pip-compile
```

### pipx

If you use [pipx] to install and use hatch you will need to inject
the `hatch-pip-compile` plugin into the hatch environment.

```shell
pipx install hatch
pipx inject hatch hatch-pip-compile
```

## Usage

The `hatch-pip-compile` plugin will automatically run `pip-compile` whenever your
environment needs to be updated. Behind the scenes, this plugin creates a lockfile
at `requirements.txt` (non-default lockfiles are located at `.hatch/<envName>.lock`).
Alongside `pip-compile`, this plugin also uses [pip-sync] to install the dependencies
from the lockfile into your environment.

## Configuration

The [environment plugin] name is `pip-compile`.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.default]
    type = "pip-compile"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.default]
    type = "pip-compile"
    ```

### Configuration Options

| name                     | type        | description                                                                                                 |
| ------------------------ | ----------- | ----------------------------------------------------------------------------------------------------------- |
| lock-directory           | `str`       | The directory where the lockfiles will be stored. `default` env is project root, non-default is `.hatch`    |
| lock-filename            | `str`       | The filename of the ultimate lockfile. `default` env is `requirements.txt`, non-default is `<envName>.lock` |
| pip-compile-hashes       | `bool`      | Whether to generate hashes in the lockfile. Defaults to `true`.                                             |
| pip-compile-header       | `bool`      | Whether to use the `pip-compile` header instead of the `hatch-pip-compile` header, defaults to `false`      |
| pip-compile-strip-extras | `bool`      | Whether to strip the extras from the lockfile ensuring it is constraints compatible, defaults to `true`     |
| pip-compile-args         | `list[str]` | Additional command-line arguments to pass to `pip-compile`                                                  |

#### Examples

##### lock-directory

The directory where the lockfiles will be stored. Defaults to
the project root for the `default` environment, and `.hatch` for
non-default environments.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    lock-directory = "requirements"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    lock-directory = "requirements"
    ```

##### lock-filename

The filename of the ultimate lockfile. Defaults to `requirements.txt`
for the `default` environment, and `<envName>.lock` for non-default environments.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.lint]
    type = "pip-compile"
    lock-directory = "."
    lock-filename = "linting-lockfile.txt"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.lint]
    type = "pip-compile"
    lock-directory = "."
    lock-filename = "linting-lockfile.txt"
    ```

##### pip-compile-hashes

Whether to generate hashes in the lockfile. Defaults to `true`.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    pip-compile-hashes = true
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    pip-compile-hashes = true
    ```

##### pip-compile-args

Extra arguments to pass to `pip-compile`. Custom PyPI indexes can be
specified here.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    pip-compile-args = [
        "--index-url",
        "https://pypi.org/simple",
    ]
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    pip-compile-args = [
        "--index-url",
        "https://pypi.org/simple",
    ]
    ```

## Notes

### Dev Dependencies

Using the default hatch configuration, dev dependencies listed in your
`default` environment (like `pytest`) will be included on the default lockfile
(`requirements.txt`). If you want to remove your dev dependencies
from the lockfile you must remove them from the `default` environment
on your `pyproject.toml` / `hatch.toml` file.

---

---

<br/>

<p align="center"><a href="https://github.com/juftin"><img src="https://raw.githubusercontent.com/juftin/juftin/main/static/juftin.png" width="120" height="120" alt="logo"></p>

[pip-compile]: https://pip-tools.readthedocs.io/en/latest/
[pip-sync]: https://pip-tools.readthedocs.io/en/latest/
[hatch]: https://hatch.pypa.io/latest/
[pipx]: https://pipxproject.github.io/pipx/
[Docs]: https://juftin.github.io/hatch-pip-compile/
[Contributing Guide]: https://juftin.github.io/hatch-pip-compile/contributing
[Changelog]: https://github.com/juftin/hatch-pip-compile/releases
[environment plugin]: https://hatch.pypa.io/latest/plugins/environment/
