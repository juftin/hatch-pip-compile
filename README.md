<h1 align="center">hatch-pip-compile</h1>

<div align="center">
  <a href="https://github.com/juftin/hatch-pip-compile">
    <img src="https://raw.githubusercontent.com/juftin/hatch-pip-compile/main/docs/logo.png" alt="hatch-pip-compile" width="250" />
  </a>
</div>

<p align="center">
<a href="https://github.com/pypa/hatch">hatch</a> plugin to use <a href="https://github.com/jazzband/pip-tools">pip-compile</a> (or <a href="https://github.com/astral-sh/uv">uv</a>) to manage project dependencies and lockfiles.
</p>

<p align="center">
  <a href="https://github.com/juftin/hatch-pip-compile"><img src="https://img.shields.io/pypi/v/hatch-pip-compile?color=blue&label=%F0%9F%94%A8%20hatch-pip-compile" alt="PyPI"></a>
  <a href="https://pypi.python.org/pypi/hatch-pip-compile/"><img src="https://img.shields.io/pypi/pyversions/hatch-pip-compile" alt="PyPI - Python Version"></a>
  <a href="https://github.com/juftin/hatch-pip-compile/blob/main/LICENSE"><img src="https://img.shields.io/github/license/juftin/hatch-pip-compile?color=blue&label=License" alt="GitHub License"></a>
  <a href="https://juftin.github.io/hatch-pip-compile/"><img src="https://img.shields.io/static/v1?message=docs&color=526CFE&logo=Material+for+MkDocs&logoColor=FFFFFF&label=" alt="docs"></a>
  <a href="https://github.com/juftin/hatch-pip-compile/actions/workflows/tests.yaml?query=branch%3Amain"><img src="https://github.com/juftin/hatch-pip-compile/actions/workflows/tests.yaml/badge.svg?branch=main" alt="Testing Status"></a>
  <a href="https://codecov.io/gh/juftin/hatch-pip-compile"><img src="https://codecov.io/gh/juftin/hatch-pip-compile/graph/badge.svg?token=PCGB5QIC8M"/></a>
  <a href="https://github.com/pypa/hatch"><img src="https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg" alt="Hatch project"></a>
  <a href="https://github.com/jazzband/pip-tools"><img src="https://raw.githubusercontent.com/jazzband/website/main/jazzband/static/img/badge.svg" alt="Pip Tools project"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-lightgreen?logo=pre-commit" alt="pre-commit"></a>
  <a href="https://github.com/semantic-release/semantic-release"><img src="https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg" alt="semantic-release"></a>
  <a href="https://gitmoji.dev"><img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg" alt="Gitmoji"></a>
</p>

## Usage

The `hatch-pip-compile` plugin will automatically run `pip-compile` whenever your
environment needs to be updated. Behind the scenes, this plugin creates a lockfile
at `requirements.txt` (non-default lockfiles are located at
`requirements/requirements-{env_name}.txt`). Once the dependencies are resolved
the plugin will install the lockfile into your virtual environment and keep it
up-to-date.

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

## Configuration

Set your environment type to `pip-compile` to use this plugin for the respective environment:

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

### Common Scenarios

-   [lock-filename](docs/examples.md#lock-filename) - changing the default lockfile path
-   [pip-compile-constraint](docs/examples.md#pip-compile-constraint) - syncing dependency versions across environments
-   [Upgrading Dependencies](docs/examples.md#upgrading-dependencies) - how to upgrade dependencies
-   [Using Hashes](docs/examples.md#pip-compile-hashes) - how to include hashes in your lockfile
-   [Using uv instead of pip-compile](docs/examples.md#pip-compile-resolver) - how to use `uv` instead of `pip-compile`

### Configuration Options

The plugin gives you options to configure how lockfiles are generated and how they are installed
into your environment.

The following example shows how to specify the `pip-compile-hashes` option
on your environment in your `pyproject.toml` file:

```toml
[tool.hatch.envs.default]
type = "pip-compile"
pip-compile-hashes = true
```

#### Generating Lockfiles

| name                                                              | type        | description                                                                                                                           |
| ----------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [lock-filename](docs/examples.md#lock-filename)                   | `str`       | The filename of the ultimate lockfile. `default` env is `requirements.txt`, non-default is `requirements/requirements-{env_name}.txt` |
| [pip-compile-constraint](docs/examples.md#pip-compile-constraint) | `str`       | An environment to use as a constraint file, ensuring that all shared dependencies are pinned to the same versions.                    |
| [pip-compile-hashes](docs/examples.md#pip-compile-hashes)         | `bool`      | Whether to generate hashes in the lockfile. Defaults to `false`.                                                                      |
| [pip-compile-resolver](docs/examples.md#pip-compile-resolver)     | `str`       | Whether to use `pip-compile` or `uv` to resolve dependencies into the project. Defaults to `pip-compile`                              |
| [pip-compile-args](docs/examples.md#pip-compile-args)             | `list[str]` | Additional command-line arguments to pass to `pip-compile-resolver`                                                                   |
| [pip-compile-verbose](docs/examples.md#pip-compile-verbose)       | `bool`      | Set to `true` to run `pip-compile` in verbose mode instead of quiet mode, set to `false` to silence warnings                          |

#### Installing Lockfiles

| name                                                                  | type        | description                                                                                           |
| --------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------- |
| [pip-compile-installer](docs/examples.md#pip-compile-installer)       | `str`       | Whether to use `pip`, `pip-sync`, or `uv` to install dependencies into the project. Defaults to `pip` |
| [pip-compile-install-args](docs/examples.md#pip-compile-install-args) | `list[str]` | Additional command-line arguments to pass to `pip-compile-installer`                                  |

<!--skip-->

---

---

#### Check Out the [Docs]

-   [Examples 📚](docs/examples.md)
-   [Upgrading 🚀](docs/upgrading.md)
-   [Command Line Usage 📦](docs/cli_usage.md)
-   [Notes 📝](docs/notes.md)

#### Looking to contribute? See the [Contributing Guide]

#### See the [Changelog]

<!--skip-->

[Docs]: https://juftin.github.io/hatch-pip-compile/
[Contributing Guide]: https://juftin.github.io/hatch-pip-compile/contributing
[Changelog]: https://github.com/juftin/hatch-pip-compile/releases
