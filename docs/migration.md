# Migration Guide: Moving to Upstream Hatch Lockfiles

[Hatch v1.17.0] introduced first-class [PEP 751] lockfile support, making
`hatch-pip-compile` unnecessary. The upstream feature covers all the same
use cases — lockfile generation with `uv` or `pip`, installing from
lockfiles, upgrading dependencies, and CI verification — without a plugin.

## Quick Start

```diff
- [tool.hatch.env]
- requires = ["hatch-pip-compile"]

  [tool.hatch.envs.default]
- type = "pip-compile"
- pip-compile-hashes = true
+ locked = true
+ installer = "uv"

  [tool.hatch.envs.test]
- type = "pip-compile"
+ locked = true
+ installer = "uv"
  dependencies = ["pytest"]
```

Then:

```shell
rm requirements.txt requirements/    # delete old lockfiles
hatch env lock                        # generate pylock.toml
```

The `uv` locker is recommended — it handles `--check` (CI), `--upgrade`, and
`dep sync` correctly. The `pip` locker works for generation but has limited
`--check` and no `apply_lock` support.

Prefer per-env `locked = true` over global `lock-envs = true`. As of
writing (Hatch 1.17.1), `lock-envs = true` also affects internal Hatch
environments (`hatch-build`, `hatch-uv`) and can cause spurious CI
failures — this may be addressed in a future release.

See the upstream [lockfile how-to] for full usage details.

## Feature Mapping

| hatch-pip-compile                      | Upstream Hatch                       |
| -------------------------------------- | ------------------------------------ |
| `type = "pip-compile"`                 | `locked = true`                      |
| `lock-filename = "..."`                | `lock-filename = "..."`              |
| `pip-compile-resolver = "uv"`          | `installer = "uv"` → auto-selects `locker = "uv"` |
| `pip-compile-resolver = "pip-compile"` | `locker = "pip"` (pip ≥ 25.1)        |
| `pip-compile-hashes = true`            | Always on in PEP 751 lockfiles       |
| `pip-compile-installer = "uv"`         | `installer = "uv"`                   |
| `pip-compile-installer = "pip-sync"`   | `hatch dep sync` (UV locker only)    |
| `pip-compile-constraint = "..."`       | No direct equivalent; UV's layered locks approximate this |
| `pip-compile-args = [...]`             | Use `env-vars` (`PIP_*` / `UV_*`)    |

## Command Equivalents

| Old                                          | New                                           |
| -------------------------------------------- | --------------------------------------------- |
| Activate env → auto-lock                     | Activate env → auto-lock (with `locked=true`) |
| `PIP_COMPILE_UPGRADE=1 hatch env run ...`    | `hatch env lock --upgrade`                    |
| `PIP_COMPILE_UPGRADE_PACKAGE=pkg ...`        | `hatch env lock --upgrade-package pkg`        |
| `PIP_COMPILE_DISABLE=1 hatch env run ...`    | `hatch env lock --check`                      |
| `hatch-pip-compile --upgrade`                | `hatch env lock --upgrade`                    |
| `hatch-pip-compile --upgrade-package pkg`    | `hatch env lock --upgrade-package pkg`        |

## Requirements

- **Hatch ≥ 1.17.0**: `pip install --upgrade hatch`
- Old `requirements.txt` lockfiles are **not reusable** — the new format is `pylock.toml` ([PEP 751]).
  Delete old lockfiles and regenerate with `hatch env lock`.

[lockfile how-to]: https://hatch.pypa.io/latest/how-to/environment/lockfiles/
[Hatch v1.17.0]: https://hatch.pypa.io/latest/blog/2026/05/30/hatch-v1170/
[PEP 751]: https://peps.python.org/pep-0751/
