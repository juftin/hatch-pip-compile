# hatch-pip-compile

[hatch] plugin to use [pip-compile] to manage project dependencies and lockfiles.

[![PyPI](https://img.shields.io/pypi/v/hatch-pip-compile?color=blue&label=🔨%20hatch-pip-compile)](https://github.com/juftin/hatch-pip-compile)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-pip-compile)](https://pypi.python.org/pypi/hatch-pip-compile/)
[![GitHub License](https://img.shields.io/github/license/juftin/hatch-pip-compile?color=blue&label=License)](https://github.com/juftin/hatch-pip-compile/blob/main/LICENSE)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-lightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![Gitmoji](https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg)](https://gitmoji.dev)

## Installation

Declare `hatch-pip-compile` as a dependency in your `pyproject.toml` file under the
`[tool.hatch.env]` table and hatch will automatically install it. You must also have
your environment type set to `pip-compile` (see [Configuration](#configuration)).

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.env]
    requires = [
        "hatch-pip-compile"
    ]

    [tool.hatch.envs.default]
    type = "pip-compile"
    ```

-   **_hatch.toml_**

    ```toml
    [env]
    requires = [
        "hatch-pip-compile"
    ]

    [envs.default]
    type = "pip-compile"
    ```

## Usage

The `hatch-pip-compile` plugin will automatically run `pip-compile` whenever your
environment needs to be updated. Behind the scenes, this plugin creates a lockfile
at `requirements.txt` (non-default lockfiles are located at
`requirements/requirements-{env_name}.txt`). Alongside `pip-compile`, this plugin also
uses [pip-sync] to install the dependencies from the lockfile into your environment.

See [lock-filename](#lock-filename) for more information on changing the default
lockfile paths and [pip-compile-constraint](#pip-compile-constraint) for more
information on syncing dependency versions across environments.

## Configuration

The [environment plugin] name is `pip-compile`. Set your environment
type to `pip-compile` to use this plugin for the respective environment.

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

| name                   | type        | description                                                                                                                           |
| ---------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| lock-filename          | `str`       | The filename of the ultimate lockfile. `default` env is `requirements.txt`, non-default is `requirements/requirements-{env_name}.txt` |
| pip-compile-constraint | `str`       | An environment to use as a constraint file, ensuring that all shared dependencies are pinned to the same versions.                    |
| pip-compile-hashes     | `bool`      | Whether to generate hashes in the lockfile. Defaults to `true`.                                                                       |
| pip-compile-verbose    | `bool`      | Set to `true` to run `pip-compile` in verbose mode instead of quiet mode, set to `false` to silence warnings                          |
| pip-compile-args       | `list[str]` | Additional command-line arguments to pass to `pip-compile`                                                                            |

#### Examples

##### lock-filename

The path (including the directory) to the ultimate lockfile. Defaults to `requirements.txt` in the project root
for the `default` environment, and `requirements/requirements-{env_name}.txt` for non-default environments.

Changing the lock file path:

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    lock-filename = "locks/{env_name}.lock"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    lock-filename = "locks/{env_name}.lock"
    ```

Changing the lock filename to a path in the project root:

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.lint]
    type = "pip-compile"
    lock-filename = "linting-requirements.txt"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.lint]
    type = "pip-compile"
    lock-filename = "linting-requirements.txt"
    ```

##### pip-compile-constraint

An environment to use as a constraint, ensuring that all shared dependencies are
pinned to the same versions. For example, if you have a `default` environment and
a `test` environment, you can set the `pip-compile-constraint` option to `default`
on the `test` environment to ensure that all shared dependencies are pinned to the
same versions.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.default]
    type = "pip-compile"

    [tool.hatch.envs.test]
    dependencies = [
        "pytest"
    ]
    type = "pip-compile"
    pip-compile-constraint = "default"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.default]
    type = "pip-compile"

    [envs.test]
    dependencies = [
        "pytest"
    ]
    type = "pip-compile"
    pip-compile-constraint = "default"
    ```

By default, all environments inherit from the `default` environment via
[inheritance]. A common use case is to set the `pip-compile-constraint`
and `type` options on the `default` environment and inherit them on
all other environments. It's important to note that when `detached = true`,
inheritance is disabled and the `type` and `pip-compile-constraint` options
must be set explicitly.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.default]
    type = "pip-compile"
    pip-compile-constraint = "default"

    [tool.hatch.envs.test]
    dependencies = [
        "pytest"
    ]
    ```

-   **_hatch.toml_**

    ```toml
    [envs.default]
    type = "pip-compile"
    pip-compile-constraint = "default"

    [envs.test]
    dependencies = [
        "pytest"
    ]
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

Extra arguments to pass to `pip-compile`. Custom PyPI indexes can be specified here.

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

##### pip-compile-verbose

Set to `true` to run `pip-compile` in verbose mode instead of quiet mode.

Optionally, if you would like to silence any warnings set the `pip-compile-verbose` option to `false`.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    pip-compile-verbose = true
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    pip-compile-verbose = true
    ```

## Notes

### Dev Dependencies

Using the default hatch configuration, dev dependencies listed in your
`default` environment (like `pytest`) will be included on the default lockfile
(`requirements.txt`). If you want to remove your dev dependencies
from the lockfile you must remove them from the `default` environment
on your `pyproject.toml` / `hatch.toml` file.

### Manual Installation

If you want to manually install this plugin instead of adding it to the
`[tool.hatch.env]` table, you can do so with [pipx]:

```bash
pipx install hatch
pipx inject hatch hatch-pip-compile
```

Alternatively, you can install it with [pip]:

```bash
pip install hatch hatch-pip-compile
```

---

---

#### Check Out the [Docs]

#### Looking to contribute? See the [Contributing Guide]

#### See the [Changelog]

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
[pip]: https://pip.pypa.io/en/stable/
[inheritance]: https://hatch.pypa.io/1.7/config/environment/overview/#inheritance
