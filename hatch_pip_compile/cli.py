"""
hatch-pip-compile CLI
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
from typing import Any, Sequence

import click
import rich.traceback

from hatch_pip_compile.__about__ import __application__, __version__


@dataclasses.dataclass
class HatchCommandRunner:
    """
    Hatch Command Runner
    """

    environments: Sequence[str] = dataclasses.field(default_factory=list)
    upgrade: bool = False
    upgrade_all: bool = False
    upgrade_packages: Sequence[str] = dataclasses.field(default_factory=list)

    former_env_vars: dict[str, Any] = dataclasses.field(init=False, default_factory=dict)
    console: rich.console.Console = dataclasses.field(init=False)
    supported_environments: set[str] = dataclasses.field(init=False)

    def __post_init__(self):
        """
        Initialize the internal state
        """
        self.console = rich.console.Console()
        rich.traceback.install(show_locals=True, console=self.console)
        self.supported_environments = self._get_supported_environments()
        if all(
            [not self.environments, "default" in self.supported_environments, not self.upgrade_all]
        ):
            self.environments = ["default"]
        elif not self.environments and not self.upgrade_all:
            msg = "Either `--all` or an environment name must be specified"
            raise click.BadParameter(msg)
        elif self.upgrade_all:
            self.environments = list(self.supported_environments)
        unsupported_environments = set(self.environments).difference(self.supported_environments)
        if unsupported_environments:
            msg = (
                f"The following environments are not supported or unknown: "
                f"{', '.join(unsupported_environments)}. "
                f"Supported environments are: {', '.join(sorted(self.supported_environments))}"
            )
            raise click.BadParameter(msg)

    def __enter__(self) -> HatchCommandRunner:
        """
        Set the environment variables
        """
        env_vars = {"__PIP_COMPILE_FORCE__": "1"}
        if self.upgrade:
            env_vars["PIP_COMPILE_UPGRADE"] = "1"
            self.console.print(
                "[bold green]hatch-pip-compile[/bold green]: Upgrading all dependencies"
            )
        elif self.upgrade_packages:
            env_vars["PIP_COMPILE_UPGRADE_PACKAGES"] = ",".join(self.upgrade_packages)
            message = (
                "[bold green]hatch-pip-compile[/bold green]: "
                f"Upgrading packages: {', '.join(self.upgrade_packages)}"
            )
            self.console.print(message)
        self.former_env_vars = {
            key: os.environ.get(key) for key in env_vars.keys() if os.environ.get(key) is not None
        }
        os.environ.update(env_vars)
        return self

    def __exit__(self, *args, **kwargs):
        """
        Restore the environment variables
        """
        os.environ.update(self.former_env_vars)

    def hatch_cli(self):
        """
        Run the `hatch` CLI
        """
        self.console.print(
            "[bold green]hatch-pip-compile[/bold green]: Targeting environments: "
            f"{', '.join(sorted(self.environments))}"
        )
        for environment in sorted(self.environments):
            environment_command = [
                "hatch",
                "env",
                "run",
                "--env",
                environment,
                "--",
                "python",
                "--version",
            ]
            self.console.print(
                f"[bold green]hatch-pip-compile[/bold green]: Running "
                f"`[bold blue]{' '.join(environment_command)}`[/bold blue]"
            )
            result = subprocess.run(
                args=environment_command,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:  # pragma: no cover
                self.console.print(
                    "[bold yellow]hatch command[/bold yellow]: "
                    f"[bold blue]`{' '.join(environment_command)}`[/bold blue]"
                )
                self.console.print(result.stdout.decode("utf-8"))
                self.console.print(
                    "[bold red]hatch-pip-compile[/bold red]: Error running hatch command"
                )
                raise click.exceptions.Exit(1)

    @classmethod
    def _get_supported_environments(cls) -> set[str]:
        """
        Get the names of the environments from `hatch env show --json`

        Returns
        -------
        List[str]
            The name of the environments
        """
        result = subprocess.run(
            args=["hatch", "env", "show", "--json"],
            capture_output=True,
            check=True,
        )
        environment_dict: dict[str, Any] = json.loads(result.stdout)
        return {
            key for key, value in environment_dict.items() if value.get("type") == "pip-compile"
        }


@click.command("hatch-pip-compile")
@click.version_option(version=__version__, prog_name=__application__)
@click.argument("environment", default=None, type=click.STRING, required=False, nargs=-1)
@click.option(
    "-U",
    "--upgrade/--no-upgrade",
    is_flag=True,
    default=False,
    help="Try to upgrade all dependencies to their latest versions",
)
@click.option(
    "-P",
    "--upgrade-package",
    "upgrade_packages",
    nargs=1,
    multiple=True,
    help="Specify a particular package to upgrade; may be used more than once",
)
@click.option(
    "--all",
    "upgrade_all",
    is_flag=True,
    default=False,
    help="Upgrade all environments",
)
def cli(
    environment: Sequence[str],
    upgrade: bool,
    upgrade_packages: Sequence[str],
    upgrade_all: bool,
):
    """
    Upgrade your `hatch-pip-compile` managed dependencies
    from the command line.
    """
    with HatchCommandRunner(
        environments=environment,
        upgrade=upgrade,
        upgrade_packages=upgrade_packages,
        upgrade_all=upgrade_all,
    ) as hatch_runner:
        hatch_runner.hatch_cli()


if __name__ == "__main__":
    cli()
