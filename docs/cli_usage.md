# Using the `hatch-pip-compile` CLI

> [!WARNING]
> **This plugin is deprecated.** Hatch v1.17.0+ has first-class lockfile
> support. See the **[Migration Guide]** to replace `hatch-pip-compile`.
> The `hatch env lock`, `hatch dep lock`, and `hatch lock` commands
> replace this CLI tool.
>
> [Migration Guide]: migration.md

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
[pip]: https://pip.pypa.io
