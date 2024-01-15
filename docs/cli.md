# Command Line Interface

It's recommend to use [pipx] to install the CLI, but
you can also install it with [pip]:

```shell
pipx install hatch-pip-compile
```

::: mkdocs-click
    :module: hatch_pip_compile.cli
    :command: cli
    :prog_name: hatch-pip-compile
    :style: table
    :list_subcommands: True

## How it works

The `hatch-pip-compile` CLI is a wrapper around `hatch` that simply
sets the `PIP_COMPILE_UPGRADE` / `PIP_COMPILE_UPGRADE_PACKAGE` environment
variables before running a `hatch` command in a given environment.

These environment variables are used by the `hatch-pip-compile` plugin
to run the `pip-compile` command with the `--upgrade` / `--upgrade-package`
flags.

## Examples

### Upgrade the `default` environment

The below command will upgrade all packages in the `default` environment.

```shell
hatch-pip-compile --upgrade
```

### Upgrade a non-default environment

The below command will upgrade all packages in the `docs` environment.

```shell
hatch-pip-compile docs --upgrade
```

### Upgrade a specific package

The below command will upgrade the `requests` package in the `default`
environment.

```shell
hatch-pip-compile --upgrade-package requests
```

### Upgrade all `pip-compile` environments

The below command will upgrade all packages in all `pip-compile` environments.

```shell
hatch-pip-compile --upgrade --all
```

[pipx]: https://github.com/pypa/pipx
[pip]: https://pip.pypa.io/en/stable/
