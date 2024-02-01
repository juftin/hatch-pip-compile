# Notes

## Dev Dependencies

Using the default hatch configuration, dev dependencies listed in your
`default` environment (like `pytest`) will be included on the default lockfile
(`requirements.txt`). If you want to remove your dev dependencies
from the lockfile you must remove them from the `default` environment
on your `pyproject.toml` / `hatch.toml` file.

## Disabling Changes to the Lockfile

In some scenarios, like in CI/CD, you may want to prevent the plugin from
making changes to the lockfile. If you set the `PIP_COMPILE_DISABLE`
environment variable to any non-empty value, the plugin will raise an error
if it detects that the lockfile needs to be updated.

```shell
PIP_COMPILE_DISABLE=1 hatch env run python --version
```

## Manual Installation

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

[pipx]: https://github.com/pypa/pipx
[pip]: https://pip.pypa.io
