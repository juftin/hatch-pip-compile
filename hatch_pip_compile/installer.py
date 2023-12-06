"""
Package + Dependency Installers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hatch_pip_compile.plugin import PipCompileEnvironment


@dataclass
class PluginInstaller(ABC):
    """
    Package Installer for the plugin

    This abstract base class is used to define the interface for
    how the plugin should install packages and dependencies.
    """

    environment: "PipCompileEnvironment"

    @abstractmethod
    def install_dependencies(self) -> None:
        """
        Install the dependencies
        """

    def sync_dependencies(self) -> None:
        """
        Sync the dependencies - same as `install_dependencies`
        """
        self.install_dependencies()

    def install_project(self) -> None:
        """
        Install the project (`--no-deps`)
        """
        with self.environment.safe_activation():
            self.environment.plugin_check_command(
                self.environment.construct_pip_install_command(
                    args=["--no-deps", str(self.environment.root)]
                )
            )

    def install_project_dev_mode(self) -> None:
        """
        Install the project in editable mode (`--no-deps`)
        """
        with self.environment.safe_activation():
            self.environment.plugin_check_command(
                self.environment.construct_pip_install_command(
                    args=["--no-deps", "--editable", str(self.environment.root)]
                )
            )


class PipInstaller(PluginInstaller):
    """
    Plugin Installer for `pip`
    """

    def install_dependencies(self) -> None:
        """
        Install the dependencies with `pip`
        """
        with self.environment.safe_activation():
            if not self.environment.piptools_lock_file.exists():
                return
            extra_args = self.environment.config.get("pip-compile-install-args", [])
            args = [*extra_args, "--requirement", str(self.environment.piptools_lock_file)]
            install_command = self.environment.construct_pip_install_command(args=args)
            self.environment.plugin_check_command(install_command)


class PipSyncInstaller(PluginInstaller):
    """
    Plugin Installer for `pip-sync`
    """

    def install_dependencies(self) -> None:
        """
        Install the dependencies with `pip-sync`

        In the event that there are no dependencies, pip-sync will
        uninstall everything in the environment before deleting the
        lockfile.
        """
        self.environment.install_pip_tools()
        cmd = [
            self.environment.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "sync",
            "--verbose"
            if self.environment.config.get("pip-compile-verbose", None) is True
            else "--quiet",
            "--python-executable",
            str(self.environment.virtual_env.python_info.executable),
        ]
        if not self.environment.dependencies:
            self.environment.piptools_lock_file.write_text("")
        extra_args = self.environment.config.get("pip-compile-install-args", [])
        cmd.extend(extra_args)
        cmd.append(str(self.environment.piptools_lock_file))
        self.environment.plugin_check_command(cmd)
        if not self.environment.dependencies:
            self.environment.piptools_lock_file.unlink()

    def _full_install(self) -> None:
        """
        Run the full install process

        1) Run pip-compile (if necessary)
        2) Run pip-sync
        3) (re)install project
        """
        with self.environment.safe_activation():
            self.environment.run_pip_compile()
            self.install_dependencies()
        if not self.environment.skip_install:
            if self.environment.dev_mode:
                super().install_project_dev_mode()
            else:
                super().install_project()

    def sync_dependencies(self):
        """
        Sync dependencies
        """
        self._full_install()

    def install_project(self):
        """
        Install the project the first time

        The same implementation as `_full_install`
        due to the way `pip-sync` uninstalls our root package
        """
        self._full_install()

    def install_project_dev_mode(self):
        """
        Install the project the first time in dev mode

        The same implementation as `_full_install`
        due to the way `pip-sync` uninstalls our root package
        """
        self._full_install()
