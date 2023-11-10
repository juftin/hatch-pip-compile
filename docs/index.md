# hatch-pip-compile

hatch plugin to use pip-compile to manage project dependencies

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

Personally, I use [pipx](https://github.com/pypa/pipx) to install and use hatch. If you do too,
you will need to inject the `hatch-pip-compile` plugin into the hatch environment.

```shell
pipx install hatch
pipx inject hatch hatch-pip-compile
```

## Usage

The `hatch-pip-compile` plugin will automatically run `pip-compile` whenever your
environment needs to be updated. Behind the scenes, this plugin creates a lockfile
at `.hatch/<ENV_NAME>.lock`. Alongside `pip-compile`, this plugin also uses
`pip-sync` to install the dependencies from the lockfile into your environment.

## Configuration

The [environment plugin](https://hatch.pypa.io/latest/plugins/environment/) name is `pip-compile`.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    type = "pip-compile"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<ENV_NAME>]
    type = "pip-compile"
    ```

### lock-directory

The directory where the lockfiles will be stored. Defaults to `.hatch`.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    type = "pip-compile"
    lock-directory = "requirements"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<ENV_NAME>]
    type = "pip-compile"
    lock-directory = "requirements"
    ```

### pip-compile-hashes

Whether or not to use hashes in the lockfile. Defaults to `true`.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    type = "pip-compile"
    pip-compile-hashes = true
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<ENV_NAME>]
    type = "pip-compile"
    pip-compile-hashes = true
    ```

### pip-compile-args

Extra arguments to pass to `pip-compile`. Defaults to None.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<ENV_NAME>]
    type = "pip-compile"
    pip-compile-args = [
        "--index-url",
        "https://pypi.org/simple",
    ]
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<ENV_NAME>]
    type = "pip-compile"
    pip-compile-args = [
        "--index-url",
        "https://pypi.org/simple",
    ]
    ```

---

---

<br/>

<p align="center"><a href="https://github.com/juftin"><img src="https://raw.githubusercontent.com/juftin/juftin/main/static/juftin.png" width="120" height="120" alt="logo"></p>
