"""
Dependency Resolvers
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import ClassVar

from hatch_pip_compile.base import HatchPipCompileBase


class BaseResolver(HatchPipCompileBase, ABC):
    """
    Base Resolver for the plugin
    """

    resolver_options: ClassVar[list[str]] = []

    @property
    @abstractmethod
    def resolver_executable(self) -> list[str]:
        """
        Resolver Executable
        """

    def get_pip_compile_args(self, input_file: os.PathLike, output_file: os.PathLike) -> list[str]:
        """
        Get the pip compile arguments
        """
        upgrade = bool(os.getenv("PIP_COMPILE_UPGRADE"))
        upgrade_packages = os.getenv("PIP_COMPILE_UPGRADE_PACKAGE") or None
        upgrade_args = []
        upgrade_package_args = []
        if upgrade:
            upgrade_args.append("--upgrade")
        if upgrade_packages:
            upgrade_packages_sep = upgrade_packages.split(",")
            for package in upgrade_packages_sep:
                upgrade_package_args.append(f"--upgrade-package={package.strip()}")
        cmd = [
            *self.resolver_executable,
            "--verbose"
            if self.environment.config.get("pip-compile-verbose", None) is True
            else "--quiet",
            "--no-header",
            *self.resolver_options,
        ]
        if self.environment.config.get("pip-compile-hashes", False) is True:
            cmd.append("--generate-hashes")
        if self.environment.piptools_constraints_file is not None:
            cmd.extend(["--constraint", str(self.environment.piptools_constraints_file)])
        cmd.extend(self.environment.config.get("pip-compile-args", []))
        cmd.extend(upgrade_args)
        cmd.extend(upgrade_package_args)
        cmd.extend(["--output-file", str(output_file), str(input_file)])
        return cmd


class PipCompileResolver(BaseResolver):
    """
    Pip Compile Resolver
    """

    pypi_dependencies: ClassVar[list[str]] = ["pip-tools"]
    resolver_options: ClassVar[list[str]] = ["--resolver=backtracking", "--strip-extras"]

    @property
    def resolver_executable(self) -> list[str]:
        """
        Resolver Executable
        """
        return [
            self.environment.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "compile",
        ]


class UvResolver(BaseResolver):
    """
    Uv Resolver
    """

    pypi_dependencies: ClassVar[list[str]] = ["uv"]

    @property
    def resolver_executable(self) -> list[str]:
        """
        Resolver Executable
        """
        return [
            self.environment.virtual_env.python_info.executable,
            "-m",
            "uv",
            "pip",
            "compile",
        ]
