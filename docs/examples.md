# Examples

## lock-filename

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

## pip-compile-constraint

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

## pip-compile-hashes

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

## pip-compile-resolver

Which resolver to use to generate the lockfile. Defaults to `pip-compile`.

[uv] is a drop in replacement for `pip-compile` with a much faster resolver written in rust.
If you'd like to use `uv` instead of `pip-compile` you can set the `pip-compile-resolver` option.

> NOTE: **pip-compile-installer**
>
> [uv] can also be used as the default installer instead of `pip`. See
> the [pip-compile-installer](#pip-compile-installer) option for more
> information.

-   **_pyproject.toml_**

    ```toml
    [tool.hatch.envs.<envName>]
    type = "pip-compile"
    pip-compile-resolver = "uv"
    ```

-   **_hatch.toml_**

    ```toml
    [envs.<envName>]
    type = "pip-compile"
    pip-compile-resolver = "uv"
    ```

## pip-compile-args

Extra arguments to pass to `pip-compile-resolver`. Custom PyPI indexes can be specified here.

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

## pip-compile-verbose

Set to `true` to run `pip-compile` in verbose mode instead of quiet mode.

Optionally, if you would like to silence any warnings set the `pip-compile-verbose` option
to `false`.

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

## pip-compile-installer

Whether to use [pip], [pip-sync], or [uv] to install dependencies into the project. Defaults
to `pip`. When you choose the `pip` option the plugin will run `pip install -r {lockfile}`
under the hood to install the dependencies. When you choose the `pip-sync` option
`pip-sync {lockfile}` is invoked by the plugin. [uv] is a drop in replacement for
`pip`, it has the same behavior as `pip` installer, `uv pip install -r {lockfile}`.

The key difference between these options is that `pip-sync` will uninstall any packages that are
not in the lockfile and remove them from your environment. `pip-sync` is useful if you want to
ensure that your environment is exactly the same as the lockfile. If the environment should
be used across different Python versions and platforms `pip` is the safer option to use.

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

## pip-compile-install-args

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

[pip-sync]: https://github.com/jazzband/pip-tools
[pip]: https://pip.pypa.io
[inheritance]: hhttps://hatch.pypa.io/latest/config/environment/overview/#inheritance
[uv]: https://github.com/astral-sh/uv
