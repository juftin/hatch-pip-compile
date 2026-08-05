# Migration Guide: Moving to Upstream Hatch Lockfiles

Hatch v1.17.0 (May 2026) introduced first-class lockfile support as a built-in
feature. This makes `hatch-pip-compile` **no longer necessary** — the upstream
lockfile system covers the same use cases and is the recommended path forward.

This guide maps every `hatch-pip-compile` feature to its upstream equivalent
and provides step-by-step instructions for removing the plugin.

## Quick Start

Remove the plugin and enable native locking:

1.  Delete `hatch-pip-compile` from `[tool.hatch.env]` `requires`.
2.  Replace `type = "pip-compile"` with `locked = true` on each environment.
3.  Delete old `requirements.txt` / `requirements/requirements-*.txt` files.
4.  Run `hatch env lock` to generate `pylock.toml` lockfiles.

**Before** (hatch-pip-compile):

```toml
[tool.hatch.env]
requires = ["hatch-pip-compile"]

[tool.hatch.envs.default]
type = "pip-compile"

[tool.hatch.envs.test]
type = "pip-compile"
dependencies = ["pytest"]
```

**After** (native):

```toml
[tool.hatch.envs.default]
locked = true

[tool.hatch.envs.test]
locked = true
dependencies = ["pytest"]
```

Or enable globally:

```toml
[tool.hatch]
lock-envs = true
```

## Feature Mapping

### Generating Lockfiles

| hatch-pip-compile                      | Upstream Hatch                                                                | Notes                                                                                                 |
| -------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `type = "pip-compile"`                 | `locked = true` (per env) or `lock-envs = true` (global)                      | Built-in; no plugin required                                                                          |
| `lock-filename = "..."`                | `lock-filename = "..."`                                                       | Same option name. Defaults changed: `pylock.toml` / `pylock.<env>.toml` instead of `requirements.txt` |
| `pip-compile-resolver = "uv"`          | `locker = "uv"`                                                               | UV locker uses `uv pip compile` with hashes. Also the default when using the UV installer             |
| `pip-compile-resolver = "pip-compile"` | `locker = "pip"`                                                              | pip locker uses `pip lock` (requires pip ≥ 25.1)                                                      |
| `pip-compile-hashes = true`            | **Always enabled**                                                            | PEP 751 lockfiles include cryptographic hashes by default                                             |
| `pip-compile-args = [...]`             | Environment variables (`UV_*`, `PIP_*`) on the env, or locker-specific config | No direct `args` passthrough; use env vars on the environment                                         |
| `pip-compile-verbose = true`           | Built-in verbose output                                                       | Upstream shows lock progress by default                                                               |

### Installing Dependencies

| hatch-pip-compile                    | Upstream Hatch                                               | Notes                                                     |
| ------------------------------------ | ------------------------------------------------------------ | --------------------------------------------------------- |
| `pip-compile-installer = "pip"`      | Default (pip installer)                                      | Pip is the default installer; no config change needed     |
| `pip-compile-installer = "uv"`       | [Configure the UV installer][uv-installer] + `locker = "uv"` | Installer and locker are separate concepts upstream       |
| `pip-compile-installer = "pip-sync"` | `hatch dep sync` (UV locker only)                            | The pip locker's `apply_lock` is a no-op; use UV for sync |
| `pip-compile-install-args = [...]`   | Environment variables (`PIP_*`, `UV_*`)                      | Use `env-vars` on the environment                         |

[uv-installer]: https://hatch.pypa.io/latest/how-to/environment/select-installer/

### Commands / Workflows

| hatch-pip-compile                              | Upstream Hatch                                                  |
| ---------------------------------------------- | --------------------------------------------------------------- |
| Activate environment → auto-lock               | Activate environment → auto-lock (with `locked = true`)         |
| `rm requirements.txt && hatch env run ...`     | `hatch env lock` (re-lock on demand)                            |
| `PIP_COMPILE_UPGRADE=1 hatch env run ...`      | `hatch env lock --upgrade`                                      |
| `PIP_COMPILE_UPGRADE_PACKAGE=pkg1,pkg2 ...`    | `hatch env lock --upgrade-package pkg1 --upgrade-package pkg2`  |
| `PIP_COMPILE_DISABLE=1 hatch env run ...`      | `hatch env lock --check` (CI verification)                      |
| `hatch-pip-compile --upgrade`                  | `hatch env lock --upgrade`                                      |
| `hatch-pip-compile docs --upgrade`             | `hatch env lock docs --upgrade`                                 |
| `hatch-pip-compile --upgrade-package requests` | `hatch env lock --upgrade-package requests`                     |
| `hatch-pip-compile --upgrade --all`            | `hatch env lock --upgrade` (locks all `locked` envs by default) |

### Constraint Environments

The `pip-compile-constraint` option (pinning shared dependencies across
environments) does not have a direct 1:1 upstream equivalent. With upstream
locking, each environment is resolved independently.

If you need shared pins across environments, consider:

- Using the [**UV locker**][locker] which supports **layered locks** (extras,
  dependency groups) and resolves dependencies in the context of the full
  environment hierarchy.
- Adding explicit lower bounds to shared dependencies to keep them in sync.

[locker]: https://hatch.pypa.io/latest/plugins/locker/

## Lockfile Format Change

Old lockfiles (`requirements.txt`) are standard `pip-compile` output:

```
# This file is autogenerated by hatch-pip-compile ...
# - dep1>=1.0
# - dep2
dep1==1.2.3
    # via ...
dep2==4.5.6
    # via ...
```

New lockfiles (`pylock.toml`) follow the [PEP 751] standard:

```toml
[lock]
version = "1.0"

[[packages]]
name = "dep1"
version = "1.2.3"
# ... hashes, markers, etc.
```

This is a structural change — **you cannot reuse old lockfiles**. Delete them
and regenerate with `hatch env lock`.

[PEP 751]: https://peps.python.org/pep-0751/

## Step-by-Step Migration

### 1. Remove the Plugin

Delete `hatch-pip-compile` from the `[tool.hatch.env]` section:

```diff
- [tool.hatch.env]
- requires = ["hatch-pip-compile"]
```

Also remove it if installed globally:

```shell
pipx uninject hatch hatch-pip-compile
# or
pip uninstall hatch-pip-compile
```

### 2. Update Environment Configuration

Replace `type = "pip-compile"` with `locked = true` on each environment.
Remove plugin-specific options:

```diff
 [tool.hatch.envs.default]
- type = "pip-compile"
- pip-compile-hashes = true
+ locked = true

 [tool.hatch.envs.test]
- type = "pip-compile"
- pip-compile-constraint = "default"
+ locked = true
 dependencies = ["pytest"]

 [tool.hatch.envs.docs]
- type = "pip-compile"
- pip-compile-resolver = "uv"
- pip-compile-installer = "uv"
+ locked = true
+ installer = "uv"
+ locker = "uv"
```

### 3. Select the Locker

- **For UV users** (`pip-compile-resolver = "uv"`): Set `locker = "uv"` or
  configure the [UV installer][uv-installer] — UV is auto-selected as locker
  when the installer is UV.
- **For pip-compile users**: Set `locker = "pip"` (requires pip ≥ 25.1), or
  switch to the UV locker for faster resolution and `dep sync` support.

### 4. Delete Old Lockfiles

```shell
rm requirements.txt
rm -rf requirements/
```

### 5. Generate New Lockfiles

```shell
hatch env lock
```

This produces `pylock.toml` (default env) and `pylock.<name>.toml` for others.

### 6. Update CI / Scripts

| Old                                       | New                              |
| ----------------------------------------- | -------------------------------- |
| `PIP_COMPILE_DISABLE=1 hatch env run ...` | `hatch env lock --check`         |
| `PIP_COMPILE_UPGRADE=1 hatch env run ...` | `hatch env lock --upgrade`       |
| `hatch-pip-compile --upgrade`             | `hatch env lock --upgrade`       |
| `hatch-pip-compile <env> --upgrade`       | `hatch env lock <env> --upgrade` |

### 7. Verify

```shell
hatch env create       # creates envs + auto-locks
hatch env lock --check # verifies lockfiles are up to date (CI)
hatch env run <env> -- python -c "import your_project"
```

## Hatch Version Requirement

The native lockfile feature requires **Hatch ≥ 1.17.0**. Upgrade if needed:

```shell
pip install --upgrade hatch
```

## Getting Help

- [Hatch Lockfile How-To][lockfiles]
- [Dependency Locker Plugins][locker]
- [Hatch v1.17.0 Release Notes][v1170]
- [PEP 751 Specification][pep751]

[lockfiles]: https://hatch.pypa.io/latest/how-to/environment/lockfiles/
[locker]: https://hatch.pypa.io/latest/plugins/locker/
[v1170]: https://hatch.pypa.io/latest/blog/2026/05/30/hatch-v1170/
[pep751]: https://peps.python.org/pep-0751/
