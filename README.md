<h1 align="center">hatch-pip-compile</h1>

<div align="center">
  <a href="https://github.com/juftin/hatch-pip-compile">
    <img src="https://raw.githubusercontent.com/juftin/hatch-pip-compile/main/docs/logo.png" alt="hatch-pip-compile" width="250" />
  </a>
</div>

<p align="center">
<a href="https://github.com/pypa/hatch">hatch</a> plugin to use <a href="https://github.com/jazzband/pip-tools">pip-compile</a> to manage project dependencies and lockfiles.
</p>

<p align="center">
  <a href="https://github.com/juftin/hatch-pip-compile"><img src="https://img.shields.io/pypi/v/hatch-pip-compile?color=blue&label=%F0%9F%94%A8%20hatch-pip-compile" alt="PyPI"></a>
  <a href="https://pypi.python.org/pypi/hatch-pip-compile/"><img src="https://img.shields.io/pypi/pyversions/hatch-pip-compile" alt="PyPI - Python Version"></a>
  <a href="https://github.com/juftin/hatch-pip-compile/blob/main/LICENSE"><img src="https://img.shields.io/github/license/juftin/hatch-pip-compile?color=blue&label=License" alt="GitHub License"></a>
  <a href="https://github.com/juftin/hatch-pip-compile/actions/workflows/tests.yaml?query=branch%3Amain"><img src="https://github.com/juftin/hatch-pip-compile/actions/workflows/tests.yaml/badge.svg?branch=main" alt="Testing Status"></a>
  <a href="https://codecov.io/gh/juftin/hatch-pip-compile"><img src="https://codecov.io/gh/juftin/hatch-pip-compile/graph/badge.svg?token=PCGB5QIC8M"/></a>
  <a href="https://github.com/pypa/hatch"><img src="https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg" alt="Hatch project"></a>
  <a href="https://github.com/jazzband/pip-tools"><img src="https://raw.githubusercontent.com/jazzband/website/main/jazzband/static/img/badge.svg" alt="Pip Tools project"></a>
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
the plugin will install the lockfile into your virtual environment.

-   [lock-filename](#lock-filename) - changing the default lockfile path
-   [pip-compile-constraint](#pip-compile-constraint) - syncing dependency versions across environments
-   [Upgrading Dependencies](#upgrading-dependencies) - how to upgrade dependencies
-   [Using Hashes](#pip-compile-hashes) - how to include hashes in your lockfile

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

The plugin gives you options to configure how lockfiles are generated and how they are installed
into your environment.

#### Generating Lockfiles

| name                   | type        | description                                                                                                                           |
| ---------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| lock-filename          | `str`       | The filename of the ultimate lockfile. `default` env is `requirements.txt`, non-default is `requirements/requirements-{env_name}.txt` |
| pip-compile-constraint | `str`       | An environment to use as a constraint file, ensuring that all shared dependencies are pinned to the same versions.                    |
| pip-compile-hashes     | `bool`      | Whether to generate hashes in the lockfile. Defaults to `false`.                                                                      |
| pip-compile-verbose    | `bool`      | Set to `true` to run `pip-compile` in verbose mode instead of quiet mode, set to `false` to silence warnings                          |
| pip-compile-args       | `list[str]` | Additional command-line arguments to pass to `pip-compile`                                                                            |

#### Installing Lockfiles

| name                     | type        | description                                                                                    |
| ------------------------ | ----------- | ---------------------------------------------------------------------------------------------- |
| pip-compile-installer    | `str`       | Whether to use `pip` or `pip-sync` to install dependencies into the project. Defaults to `pip` |
| pip-compile-install-args | `list[str]` | Additional command-line arguments to pass to `pip-compile-installer`                           |

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
same versions. `pip-compile-constraint` can also be set to an empty string to disable
the feature.

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

Whether to generate hashes in the lockfile. Defaults to `false`.

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

##### pip-compile-installer

Whether to use [pip] or [pip-sync] to install dependencies into the project. Defaults to `pip`.
When you choose the `pip` option the plugin will run `pip install -r {lockfile}` under the hood
to install the dependencies. When you choose the `pip-sync` option `pip-sync {lockfile}` is invoked
by the plugin.

The key difference between these options is that `pip-sync` will uninstall any packages that are
not in the lockfile and remove them from your environment. `pip-sync` is useful if you want to ensure
that your environment is exactly the same as the lockfile. If the environment should be used
across different Python versions and platforms `pip` is the safer option to use.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    pip-compile-installer = "pip-sync"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    pip-compile-installer = "pip-sync"
    ```

##### pip-compile-install-args

Extra arguments to pass to `pip-compile-installer`. For example, if you'd like to use `pip` as the
installer but want to pass the `--no-deps` flag to `pip install` you can do so with this option:

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    pip-compile-installer = "pip"
    pip-compile-install-args = [
        "--no-deps"
    ]
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    pip-compile-installer = "pip"
    pip-compile-install-args = [
        "--no-deps"
    ]
    ```

## Upgrading Dependencies

Upgrading all dependencies can be as simple as deleting your lockfile and
recreating it by reactivating the environment:

```shell
rm requirements.txt
hatch env run --env default -- python --version
```

If you're a user of the `--upgrade` / `--upgrade-package` options on `pip-compile`,
these features can be enabled on this plugin by using the environment variables
`PIP_COMPILE_UPGRADE` and `PIP_COMPILE_UPGRADE_PACKAGE`. When either of these
environment variables are set `hatch` will force the lockfile to be regenerated
whenever the environment is activated.

> NOTE: **command line interface**
>
> `hatch-pip-compile` also makes a CLI available to handle the
> the `PIP_COMPILE_UPGRADE` / `PIP_COMPILE_UPGRADE_PACKAGE` workflow
> automatically. See the [hatch-pip-compile CLI](#using-the-hatch-pip-compile-cli)
> section for more information.

To run with `upgrade` functionality on the `default` environment:

```shell
PIP_COMPILE_UPGRADE=1 hatch env run --env default -- python --version
```

To run with `upgrade-package` functionality on the `docs` environment:

```shell
PIP_COMPILE_UPGRADE_PACKAGE="mkdocs,mkdocs-material" hatch env run --env docs -- python --version
```

The above commands call `python --version` on a particular environment,
but the same behavior applies to any script that activates the environment.

## Using the `hatch-pip-compile` CLI

For convenience this package also makes a CLI available to handle the setting /
unsetting of the `PIP_COMPILE_UPGRADE` / `PIP_COMPILE_UPGRADE_PACKAGE` environment variables
and invoking the `hatch env run` command for you automatically. To use the CLI you'll need to
install it outside your `pyproject.toml` / `hatch.toml` file.

I recommend using [pipx] to
install the CLI, but you can also install it directly with [pip]:

```shell
pipx install hatch-pip-compile
```

Once installed, you can run the CLI with the `hatch-pip-compile` command.

### Examples

#### Upgrade the `default` environment

The below command will upgrade all packages in the `default` environment.

```shell
hatch-pip-compile --upgrade
```

#### Upgrade a non-default environment

The below command will upgrade all packages in the `docs` environment.

```shell
hatch-pip-compile docs --upgrade
```

#### Upgrade a specific package

The below command will upgrade the `requests` package in the `default`
environment.

```shell
hatch-pip-compile --upgrade-package requests
```

#### Upgrade all `pip-compile` environments

The below command will upgrade all packages in all `pip-compile` environments.

```shell
hatch-pip-compile --upgrade --all
```

## Notes

### Dev Dependencies

Using the default hatch configuration, dev dependencies listed in your
`default` environment (like `pytest`) will be included on the default lockfile
(`requirements.txt`). If you want to remove your dev dependencies
from the lockfile you must remove them from the `default` environment
on your `pyproject.toml` / `hatch.toml` file.

### Disabling Changes to the Lockfile

In some scenarios, like in CI/CD, you may want to prevent the plugin from
making changes to the lockfile. If you set the `PIP_COMPILE_DISABLE`
environment variable to any non-empty value, the plugin will raise an error
if it detects that the lockfile needs to be updated.

```shell
PIP_COMPILE_DISABLE=1 hatch env run python --version
```

### Manual Installation

If you want to manually install this plugin instead of adding it to the
`[tool.hatch.env]` table, you can do so with [pipx]:

```bash
pipx install hatch
pipx inject hatch hatch-pip-compile
```

`pipx` also supports upgrading the plugin when any new versions are released:

```shell
pipx runpip hatch install --upgrade hatch-pip-compile
```

Alternatively, you can install the plugin directly with [pip]:

```bash
pip install hatch hatch-pip-compile
```

<!--skip-->

---

---

#### Check Out the [Docs]

#### Looking to contribute? See the [Contributing Guide]

#### See the [Changelog]

<!--skip-->

[pip-compile]: https://github.com/jazzband/pip-tools
[pip-sync]: https://github.com/jazzband/pip-tools
[hatch]: https://github.com/pypa/hatch
[pipx]: https://github.com/pypa/pipx
[Docs]: https://juftin.github.io/hatch-pip-compile/
[Contributing Guide]: https://juftin.github.io/hatch-pip-compile/contributing
[Changelog]: https://github.com/juftin/hatch-pip-compile/releases
[environment plugin]: https://hatch.pypa.io/latest/plugins/environment/
[pip]: https://pip.pypa.io/en/stable/
[inheritance]: https://hatch.pypa.io/1.7/config/environment/overview/#inheritance
