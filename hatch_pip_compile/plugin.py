"""
hatch-pip-compile plugin
"""

import logging
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

    def _pip_compile_command(self, output_file: pathlib.Path, input_file: pathlib.Path) -> None:
        """
        Run pip-compile
        """
        if self._piptools_lock_file.exists() is True:
            correct_environment = self.piptools_lock.compare_requirements(
                requirements=self.dependencies_complex
            )
            if correct_environment is True and self.piptools_constraints_file is not None:
                constraints_env = self.config["pip-compile-constraint"]
                environment = self.get_piptools_environment(environment_name=constraints_env)
                correct_environment = environment.piptools_lock.compare_requirements(
                    requirements=environment.dependencies_complex
                )
            if correct_environment is True:
                return
        cmd = [
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "compile",
            "--verbose" if self.config.get("pip-compile-verbose", None) is True else "--quiet",
            "--strip-extras",
            "--no-header",
            "--output-file",
            str(output_file),
            "--resolver=backtracking",
        ]
        if self.config.get("pip-compile-hashes", True) is True:
            cmd.append("--generate-hashes")

        if self.piptools_constraints_file is not None:
            cmd.extend(["--constraint", str(self.piptools_constraints_file)])
        cmd.extend(self.config.get("pip-compile-args", []))
        cmd.append(str(input_file))
        self.virtual_env.platform.check_command(cmd)
        self.piptools_lock.process_lock()

    def _pip_compile_cli(self) -> None:
        """
        Run pip-compile
        """
        if self._piptools_lock_file.exists() is True:
            matched_dependencies = self.piptools_lock.compare_requirements(
                requirements=self.dependencies_complex
            )
            if matched_dependencies is True:
                return
        self._piptools_lock_file.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            input_file = tmp_path / f"{self.name}.in"
            input_file.write_text("\n".join([*self.dependencies, ""]))
            self._pip_compile_command(output_file=self._piptools_lock_file, input_file=input_file)

    def _pip_sync_cli(self) -> None:
        """
        Run pip-sync
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
            str(self._piptools_lock_file),
        ]
        self.virtual_env.platform.check_command(cmd)

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

    def dependencies_in_sync(self):
        """
        Handle whether dependencies should be synced
        """
        if len(self.dependencies) > 0 and (self._piptools_lock_file.exists() is False):
            return False
        elif len(self.dependencies) > 0 and (self._piptools_lock_file.exists() is True):
            expected_locks = self.piptools_lock.compare_requirements(
                requirements=self.dependencies_complex
            )
            if expected_locks is False:
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
        environment.piptools_validate_lock(
            constraints_file=constraints_file, environment=environment
        )
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
        self, constraints_file: Optional[pathlib.Path], environment: "PipCompileEnvironment"
    ) -> None:
        """
        Validate the lock file

        Parameters
        ----------
        constraints_file : Optional[pathlib.Path]
            The optional lock file
        environment : PipCompileEnvironment
            The environment to validate against

        Raises
        ------
        LockFileNotFoundError
            If the lock file does not exist
        HatchPipCompileError
            If the lock file is out of date
        """
        if constraints_file is None:
            return
        elif not constraints_file.exists():
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
