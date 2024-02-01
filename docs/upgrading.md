# Upgrading Dependencies

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
> automatically. See the [hatch-pip-compile CLI](cli_usage.md#using-the-hatch-pip-compile-cli)
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
