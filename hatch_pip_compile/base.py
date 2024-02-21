"""
Base classes for hatch-pip-compile
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from hatchling.dep.core import dependencies_in_sync
from packaging.requirements import Requirement

if TYPE_CHECKING:
    from hatch_pip_compile.plugin import PipCompileEnvironment


class HatchPipCompileBase:
    """
    Base Class for hatch-pip-compile tools
    """

    pypi_dependencies: ClassVar[list[str]] = []

    def __init__(self, environment: PipCompileEnvironment) -> None:
        """
        Inject the environment into the base class
        """
        self.environment = environment
        self.pypi_dependencies_installed = False

    def install_pypi_dependencies(self) -> None:
        """
        Install the resolver from PyPI
        """
        if not self.pypi_dependencies:
            return
        elif self.pypi_dependencies_installed:
            return
        with self.environment.safe_activation():
            in_sync = dependencies_in_sync(
                requirements=[Requirement(item) for item in self.pypi_dependencies],
                sys_path=self.environment.virtual_env.sys_path,
                environment=self.environment.virtual_env.environment,
            )
            if not in_sync:
                self.environment.plugin_check_command(
                    self.environment.construct_pip_install_command(self.pypi_dependencies)
                )
            self.pypi_dependencies_installed = True
