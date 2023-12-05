"""
hatch-pip-compile plugin
"""

import functools
import hashlib
import logging
import os
import pathlib
import shutil
import tempfile
from typing import Any, Dict, List, Optional

from hatch.env.virtual import VirtualEnvironment
from hatch.utils.platform import Platform

from hatch_pip_compile.exceptions import HatchPipCompileError
from hatch_pip_compile.lock import PipCompileLock

logger = logging.getLogger(__name__)


class PipCompileEnvironment(VirtualEnvironment):
    """
    Virtual Environment supported by pip-compile
    """

    PLUGIN_NAME = "pip-compile"

    default_env_name = "default"

    def __repr__(self):
        """
        Get representation of PipCompileEnvironment
        """
        return f"<{self.__class__.__name__} - {self.name}>"

    def __init__(self, *args, **kwargs):
        """
        Initialize PipCompileEnvironment with extra attributes
        """
        super().__init__(*args, **kwargs)
        lock_filename_config = self.config.get("lock-filename")
        if lock_filename_config is None:
            if self.name == self.default_env_name:
                lock_filename = "requirements.txt"
            else:
                lock_filename = f"requirements/requirements-{self.name}.txt"
        else:
            with self.metadata.context.apply_context(self.context):
                lock_filename = self.metadata.context.format(lock_filename_config)
        self._piptools_lock_file = self.root / lock_filename
        self.piptools_lock = PipCompileLock(
            lock_file=self._piptools_lock_file,
            dependencies=self.dependencies,
            virtualenv=self.virtual_env,
            constraints_file=self.piptools_constraints_file,
            project_root=self.root,
            env_name=self.name,
            project_name=self.metadata.name,
        )
        self.install_method = self.config.get("pip-compile-installer", "pip")
        if self.install_method not in ["pip", "pip-sync"]:
            msg = (
                f"Invalid pip-tools install method: {self.install_method} - "
                "must be 'pip' or 'pip-sync'"
            )
            raise HatchPipCompileError(msg)

    @staticmethod
    def get_option_types() -> Dict[str, Any]:
        """
        Get option types
        """
        return {
            "lock-filename": str,
            "pip-compile-hashes": bool,
            "pip-compile-args": List[str],
            "pip-compile-constraint": str,
            "pip-compile-installer": str,
            "pip-compile-install-args": List[str],
        }

    def _hatch_pip_compile_install(self):
        """
        Run the full hatch-pip-compile install process

        1) Create virtual environment if not exists
        2) Install pip-tools
        3) Run pip-compile (if lock file does not exist / is out of date)
        4) Install the dependencies (using `pip` or `pip-sync`)
        5) Install the project (if not skipped)
        """
        try:
            _ = self.virtual_env.executables_directory
        except OSError:
            self.create()
        with self.safe_activation():
            self.virtual_env.platform.check_command(
                self.construct_pip_install_command(["pip-tools"])
            )
            if not self.lockfile_up_to_date:
                self._pip_compile_cli()
            self._piptools_install_dependencies()
            if not self.skip_install:
                if self.dev_mode:
                    self.install_project_no_deps_dev()
                else:
                    self.install_project_no_deps()

    def _pip_compile_cli(self) -> None:
        """
        Run pip-compile
        """
        if not self.dependencies and self._piptools_lock_file.exists():
            self._piptools_lock_file.unlink()
            return
        no_compile = bool(os.getenv("PIP_COMPILE_DISABLE"))
        if no_compile:
            msg = "hatch-pip-compile is disabled but attempted to run a lockfile update."
            raise HatchPipCompileError(msg)
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
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "compile",
            "--verbose" if self.config.get("pip-compile-verbose", None) is True else "--quiet",
            "--strip-extras",
            "--no-header",
            "--resolver=backtracking",
        ]
        if self.config.get("pip-compile-hashes", False) is True:
            cmd.append("--generate-hashes")
        if self.piptools_constraints_file is not None:
            cmd.extend(["--constraint", str(self.piptools_constraints_file)])
        cmd.extend(self.config.get("pip-compile-args", []))
        cmd.extend(upgrade_args)
        cmd.extend(upgrade_package_args)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            input_file = tmp_path / f"{self.name}.in"
            output_file = tmp_path / "lock.txt"
            cmd.extend(["--output-file", str(output_file), str(input_file)])
            input_file.write_text("\n".join([*self.dependencies, ""]))
            if self._piptools_lock_file.exists():
                shutil.copy(self._piptools_lock_file, output_file)
            self._piptools_lock_file.parent.mkdir(exist_ok=True, parents=True)
            self.virtual_env.platform.check_command(cmd)
            self.piptools_lock.process_lock(lockfile=output_file)
            shutil.move(output_file, self._piptools_lock_file)

    def _pip_sync_cli(self) -> None:
        """
        Install the dependencies with `pip-sync`

        In the event that a lockfile exists, but there are no dependencies,
        pip-sync will uninstall everything in the environment.

        This method also re-installs the project after it's uninstalled by
        pip-sync.
        """
        _ = self.piptools_lock.compare_python_versions(
            verbose=self.config.get("pip-compile-verbose", None)
        )
        cmd = [
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "sync",
            "--verbose" if self.config.get("pip-compile-verbose", None) is True else "--quiet",
            "--python-executable",
            str(self.virtual_env.python_info.executable),
        ]
        if not self.dependencies:
            self._piptools_lock_file.write_text("")
        extra_args = self.config.get("pip-compile-install-args", [])
        cmd.extend(extra_args)
        cmd.append(str(self._piptools_lock_file))
        self.virtual_env.platform.check_command(cmd)
        if not self.dependencies:
            self._piptools_lock_file.unlink()

    def install_project(self):
        """
        Install the project the first time
        """
        self._hatch_pip_compile_install()

    def install_project_dev_mode(self):
        """
        Install the project the first time in dev mode
        """
        self._hatch_pip_compile_install()

    def _pip_install_cli(self) -> None:
        """
        Install the project with `pip`
        """
        extra_args = self.config.get("pip-compile-install-args", [])
        args = [*extra_args, "--requirement", str(self._piptools_lock_file)]
        install_command = self.construct_pip_install_command(args=args)
        self.virtual_env.platform.check_command(install_command)

    @functools.cached_property
    def lockfile_up_to_date(self) -> bool:
        """
        Check if the lockfile is up-to-date

        Behavior
        --------
        1) If there are no dependencies and no lock file, exit early and return True.
        2) If the constraint file / environment is out of date, sync it and return False.
        3) If there are no dependencies and a lock file, return False.
        4) If there are dependencies and no lock file, return False.
        5) If a force upgrade is requested, return False.
        6) If there are dependencies and a lock file...
            a) If there is a constraint file...
                i) If the file is valid but the SHA is different, return False.
            b) If the lock file dependencies aren't current, return False.
            c) If the lock file dependencies are current but the lockfile
               has a different sha than its constraints file, return False.
        7) Otherwise, return True.
        """
        upgrade = os.getenv("PIP_COMPILE_UPGRADE") or False
        upgrade_packages = os.getenv("PIP_COMPILE_UPGRADE_PACKAGE") or False
        force_upgrade = upgrade is not False or upgrade_packages is not False
        if not self.dependencies and not self._piptools_lock_file.exists():
            return True
        if self.piptools_constraints_file:
            valid_constraint = self.validate_constraints_file(
                constraints_file=self.piptools_constraints_file, environment=self.constraint_env
            )
            if not valid_constraint:
                return False
        if not self.dependencies and self._piptools_lock_file.exists():
            return False
        elif force_upgrade:
            return False
        elif self.dependencies and not self._piptools_lock_file.exists():
            return False
        elif self.dependencies and self._piptools_lock_file.exists():
            if self.piptools_constraints_file:
                current_sha = hashlib.sha256(
                    self.piptools_constraints_file.read_bytes()
                ).hexdigest()
                sha_match = self.piptools_lock.compare_constraint_sha(sha=current_sha)
                if sha_match is False:
                    return False
            expected_dependencies = self.piptools_lock.compare_requirements(
                requirements=self.dependencies_complex
            )
            if not expected_dependencies:
                return False
        return True

    def dependencies_in_sync(self):
        """
        Whether the dependencies are in sync
        """
        if not self.lockfile_up_to_date:
            return False
        else:
            return super().dependencies_in_sync()

    def sync_dependencies(self):
        """
        Sync dependencies
        """
        self._hatch_pip_compile_install()

    @property
    def piptools_constraints_file(self) -> Optional[pathlib.Path]:
        """
        Get the constraint file path
        """
        if self.constraint_env.name == self.name:
            return None
        else:
            return self.constraint_env._piptools_lock_file

    def get_piptools_environment(self, environment_name: str) -> "PipCompileEnvironment":
        """
        Get a `PipCompileEnvironment` instance for an environment
        other than the current instance. This is useful
        for recursively checking other environments for lock file
        validity and defining inheritance.
        """
        if environment_name not in self.pipools_environment_dict.keys():
            error_message = (
                f"[hatch-pip-compile] The environment {environment_name} does not exist."
            )
            raise HatchPipCompileError(error_message)
        return PipCompileEnvironment(
            root=self.root,
            metadata=self.metadata,
            name=environment_name,
            config=self.pipools_environment_dict.get(environment_name, {}),
            matrix_variables=self.matrix_variables,
            data_directory=self.data_directory,
            isolated_data_directory=self.isolated_data_directory,
            platform=Platform(),
            verbosity=self.verbosity,
            app=None,
        )

    @functools.cached_property
    def constraint_env(self) -> "PipCompileEnvironment":
        """
        Get the constraint environment
        """
        constraint_env = self.config.get("pip-compile-constraint")
        if constraint_env is None:
            return self
        elif self.name == constraint_env:
            return self
        environment = self.get_piptools_environment(environment_name=constraint_env)
        if environment.config.get("type") != self.PLUGIN_NAME:
            logger.error("The constraint environment is not a hatch-pip-compile environment.")
            return self
        else:
            return environment

    def validate_constraints_file(
        self, constraints_file: pathlib.Path, environment: "PipCompileEnvironment"
    ) -> bool:
        """
        Validate the constraints file

        Parameters
        ----------
        constraints_file : pathlib.Path
            The lock file
        environment : PipCompileEnvironment
            The environment to validate against

        Returns
        -------
        bool
            Whether the constraints file is valid
        """
        if not constraints_file.exists():
            self.constraint_env._hatch_pip_compile_install()
            return False
        else:
            up_to_date = environment.piptools_lock.compare_requirements(
                requirements=environment.dependencies_complex
            )
            if not up_to_date:
                self.constraint_env._hatch_pip_compile_install()
                return False
        return True

    @property
    def pipools_environment_dict(self) -> Dict[str, Any]:
        """
        Get the environment dictionary
        """
        return self.metadata.hatch.config.get("envs", {})

    def _piptools_install_dependencies(self) -> None:
        """
        Install dependencies with `pip-sync` or `pip`-install`
        """
        if self.install_method == "pip" and self.dependencies:
            self._pip_install_cli()
        elif self.install_method == "pip-sync":
            self._pip_sync_cli()
        else:
            msg = f"Invalid pip-tools install method: {self.install_method}"
            raise NotImplementedError(msg)

    def install_project_no_deps(self) -> None:
        """
        Install the project (`--no-deps`)
        """
        with self.safe_activation():
            self.platform.check_command(
                self.construct_pip_install_command(args=["--no-deps", str(self.root)])
            )

    def install_project_no_deps_dev(self) -> None:
        """
        Install the project in editable mode (`--no-deps`)
        """
        with self.safe_activation():
            self.platform.check_command(
                self.construct_pip_install_command(args=["--no-deps", "--editable", str(self.root)])
            )
