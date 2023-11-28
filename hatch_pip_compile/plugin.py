"""
hatch-pip-compile plugin
"""

import hashlib
import logging
import os
import pathlib
import tempfile
from typing import Any, Dict, List, Optional

from hatch.env.virtual import VirtualEnvironment

from hatch_pip_compile.exceptions import HatchPipCompileError, LockFileNotFoundError
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
        }

    def _hatch_pip_compile_install(self):
        """
        Run the full hatch-pip-compile install process

        1) Install pip-tools
        2) Run pip-compile (if lock file does not exist / is out of date)
        3) Run pip-sync
        4) Install project in dev mode
        """
        with self.safe_activation():
            self.virtual_env.platform.check_command(
                self.construct_pip_install_command(["pip-tools"])
            )
            self._pip_compile_cli()
            self._pip_sync_cli()
        if not self.skip_install:
            if self.dev_mode:
                super().install_project_dev_mode()
            else:
                super().install_project()

    def _pip_compile_cli(self) -> None:
        """
        Run pip-compile
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
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "compile",
            "--verbose" if self.config.get("pip-compile-verbose", None) is True else "--quiet",
            "--strip-extras",
            "--no-header",
            "--output-file",
            str(self._piptools_lock_file),
            "--resolver=backtracking",
        ]
        if self.config.get("pip-compile-hashes", True) is True:
            cmd.append("--generate-hashes")
        if self.piptools_constraints_file is not None:
            cmd.extend(["--constraint", str(self.piptools_constraints_file)])
        cmd.extend(self.config.get("pip-compile-args", []))
        cmd.extend(upgrade_args)
        cmd.extend(upgrade_package_args)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            input_file = tmp_path / f"{self.name}.in"
            cmd.append(str(input_file))
            self._piptools_lock_file.parent.mkdir(exist_ok=True)
            input_file.write_text("\n".join([*self.dependencies, ""]))
            self.virtual_env.platform.check_command(cmd)
        self.piptools_lock.process_lock()

    def _pip_sync_cli(self) -> None:
        """
        run pip-sync

        In the event that a lockfile exists, but there are no dependencies,
        pip-sync will uninstall everything in the environment before
        deleting the lockfile.
        """
        _ = self.piptools_lock.compare_python_versions(
            verbose=self.config.get("pip-compile-verbose", None)
        )
        if len(self.dependencies) == 0:
            if self._piptools_lock_file.exists() is True:
                self._piptools_lock_file.write_text("")
        cmd = [
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "sync",
            "--verbose" if self.config.get("pip-compile-verbose", None) is True else "--quiet",
            "--python-executable",
            str(self.virtual_env.python_info.executable),
            str(self._piptools_lock_file),
        ]
        self.virtual_env.platform.check_command(cmd)
        if len(self.dependencies) == 0:
            self._piptools_lock_file.unlink()

    def install_project(self):
        """
        Install the project the first time

        The same implementation as `sync_dependencies`
        due to the way `pip-sync` uninstalls our root package
        """
        self._hatch_pip_compile_install()

    def install_project_dev_mode(self):
        """
        Install the project the first time in dev mode

        The same implementation as `sync_dependencies`
        due to the way `pip-sync` uninstalls our root package
        """
        self._hatch_pip_compile_install()

    def dependencies_in_sync(self) -> bool:
        """
        Whether the environment is in sync

        Behavior
        --------
        1) If there are no dependencies and no lock file, return True.
        2) Validate the constraint lock file if it exists - raise an error if
           checks fail. This is done before any other clauses bypass the
           check return True.
        3) If there are no dependencies and a lock file, return False.
           In this case, the lock file will be deleted and environment
           wiped.
        4) If there are dependencies and no lock file, return False.
        5) If there are dependencies and a lock file...
            a) If the lock file dependencies aren't current, return False.
            b) If the lock file dependencies are current and the lockfile
               has a different sha than its constraints file, return False.
        6) Finally, if all other checks pass, use the built-in hatch behavior
           to check if the environment is in sync by checking the actual
           virtual environment.
        """
        upgrade = os.getenv("PIP_COMPILE_UPGRADE") or False
        upgrade_packages = os.getenv("PIP_COMPILE_UPGRADE_PACKAGE") or False
        force_upgrade = upgrade is not False or upgrade_packages is not False
        if not self.dependencies and not self._piptools_lock_file.exists():
            return True
        constraints_file = self.piptools_constraints_file
        if constraints_file:
            constraint_name = self.config.get("pip-compile-constraint")
            constraint_env = self.get_piptools_environment(environment_name=constraint_name)
            constraint_env.piptools_validate_lock(
                constraints_file=constraints_file, environment=constraint_env
            )
        if self.dependencies == 0 and self._piptools_lock_file.exists() is True:
            return False
        elif force_upgrade:
            return False
        elif self.dependencies and not self._piptools_lock_file.exists():
            return False
        elif self.dependencies and self._piptools_lock_file.exists():
            expected_dependencies = self.piptools_lock.compare_requirements(
                requirements=self.dependencies_complex
            )
            if not expected_dependencies:
                return False
            elif constraints_file is not None:
                current_sha = hashlib.sha256(constraints_file.read_bytes()).hexdigest()
                sha_match = self.piptools_lock.compare_constraint_sha(sha=current_sha)
                if sha_match is False:
                    return False
        return super().dependencies_in_sync()

    def sync_dependencies(self):
        """
        Sync dependencies
        """
        self._hatch_pip_compile_install()

    @property
    def piptools_constraints_file(self) -> Optional[pathlib.Path]:
        """
        Get default lock file
        """
        constraint_env = self.config.get("pip-compile-constraint")
        if constraint_env is None:
            return None
        elif self.name == constraint_env:
            return None
        environment = self.get_piptools_environment(environment_name=constraint_env)
        if environment.config.get("type") != self.PLUGIN_NAME:
            logger.error("The constraint environment is not a hatch-pip-compile environment.")
            constraints_file = None
        else:
            constraints_file = environment._piptools_lock_file
        return constraints_file

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
            platform=self.platform,
            verbosity=self.verbosity,
            app=self.app,
        )

    def piptools_validate_lock(
        self, constraints_file: pathlib.Path, environment: "PipCompileEnvironment"
    ) -> None:
        """
        Validate the lock file

        Parameters
        ----------
        constraints_file : pathlib.Path
            The lock file
        environment : PipCompileEnvironment
            The environment to validate against

        Raises
        ------
        LockFileNotFoundError
            If the lock file does not exist
        HatchPipCompileError
            If the lock file is out of date
        """
        if not constraints_file.exists():
            error_message = (
                f"[hatch-pip-compile] The lock file {constraints_file} does not exist. "
                f"Please create it: `hatch env create {environment.name}`"
            )
            raise LockFileNotFoundError(error_message)
        else:
            up_to_date = environment.piptools_lock.compare_requirements(
                requirements=environment.dependencies_complex
            )
            if up_to_date is False:
                error_message = (
                    f"[hatch-pip-compile] The lock file {constraints_file} is out of date. "
                    "Please update it: "
                    f"`hatch env run --env {environment.name} -- python --version`"
                )
                raise HatchPipCompileError(error_message)

    @property
    def pipools_environment_dict(self) -> Dict[str, Any]:
        """
        Get the environment dictionary
        """
        return self.metadata.hatch.config.get("envs", {})
