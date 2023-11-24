"""
hatch-pip-compile plugin
"""

import logging
import pathlib
import re
import tempfile
from typing import Any, Dict, List, Optional

from hatch.env.virtual import VirtualEnvironment
from packaging.version import Version

from hatch_pip_compile.exceptions import HatchPipCompileError, LockFileNotFoundError
from hatch_pip_compile.header import PipCompileHeader

logger = logging.getLogger(__name__)


class PipCompileEnvironment(VirtualEnvironment):
    """
    Virtual Environment supported by pip-compile
    """

    PLUGIN_NAME = "pip-compile"

    _default_env_name = "default"

    def __init__(self, *args, **kwargs):
        """
        Initialize PipCompileEnvironment with extra attributes
        """
        super().__init__(*args, **kwargs)
        lock_filename_config = self.config.get("lock-filename")
        if lock_filename_config is None:
            if self.name == self._default_env_name:
                lock_filename = "requirements.txt"
            else:
                lock_filename = f"requirements/requirements-{self.name}.txt"
        else:
            with self.metadata.context.apply_context(self.context):
                lock_filename = self.metadata.context.format(lock_filename_config)
        self._piptools_detached_mode: bool = (
            self.metadata.hatch.config.get("envs", {}).get(self.name, {}).get("detached", False)
        )
        self._piptools_lock_file = self.root / lock_filename
        self._piptools_header = PipCompileHeader(
            lock_file=self._piptools_lock_file,
            dependencies=self.dependencies,
            virtualenv=self.virtual_env,
            constraints_file=self._piptools_constraints_file,
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
            "pip-compile-strip-extras": bool,
            "pip-compile-args": List[str],
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
            correct_environment = self._lock_file_compare()
            if correct_environment is True and self._piptools_constraints_file is not None:
                correct_environment = self._piptools_default_environment._lock_file_compare()
            if correct_environment is True:
                return
        cmd = [
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "compile",
            "--verbose" if self.config.get("pip-compile-verbose", None) is True else "--quiet",
            (
                "--strip-extras"
                if self.config.get("pip-compile-strip-extras", True) is True
                else "--no-strip-extras"
            ),
            "--no-header",
            "--output-file",
            str(output_file),
            "--resolver=backtracking",
        ]
        if self.config.get("pip-compile-hashes", True) is True:
            cmd.append("--generate-hashes")

        if self._piptools_constraints_file is not None:
            cmd.extend(["--constraint", str(self._piptools_constraints_file)])
        cmd.extend(self.config.get("pip-compile-args", []))
        cmd.append(str(input_file))
        self.virtual_env.platform.check_command(cmd)
        self._piptools_header.write_header()

    def _pip_compile_cli(self) -> None:
        """
        Run pip-compile
        """
        if self._piptools_lock_file.exists() is True:
            matched_dependencies = self._lock_file_compare()
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
        self._compare_python_versions()
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
            expected_locks = self._lock_file_compare()
            if expected_locks is False:
                return False
        return super().dependencies_in_sync()

    def sync_dependencies(self):
        """
        Sync dependencies
        """
        self._hatch_pip_compile_install()

    def _lock_file_compare(self) -> bool:
        """
        Compare lock file
        """
        parsed_requirements = self._piptools_header.read_requirements()
        expected_output = "\n".join([*parsed_requirements, ""])
        new_output = "\n".join([*self.dependencies, ""])
        return expected_output == new_output

    def _compare_python_versions(self) -> bool:
        """
        Compare python versions
        """
        current_version = Version(self.virtual_env.environment["python_version"])
        lock_file_text = self._piptools_lock_file.read_text()
        match = re.search(
            r"# This file is autogenerated by hatch-pip-compile with Python (.*)", lock_file_text
        )
        if match is not None:
            lock_version = Version(match.group(1))
            if all(
                [
                    (
                        current_version.major != lock_version.major
                        or current_version.minor != lock_version.minor
                    ),
                    self.config.get("pip-compile-verbose", None) is not False,
                ]
            ):
                logger.error(
                    "[hatch-pip-compile] Your Python version is different "
                    "from the lock file, your results may vary."
                )
            return False
        return True

    @property
    def _piptools_constraints_file(self) -> Optional[pathlib.Path]:
        """
        Get default lock file
        """
        if self.name == self._default_env_name:
            constraints_file = None
        else:
            default_config = self.metadata.hatch.config.get("envs", {}).get(
                self._default_env_name, {}
            )
            if default_config.get("type") != self.PLUGIN_NAME:
                constraints_file = None
            elif self._piptools_detached_mode is True:
                constraints_file = None
            else:
                constraints_file = self._piptools_default_environment._piptools_lock_file
        self._validate_default_lock(constraints_file=constraints_file)
        return constraints_file

    @property
    def _piptools_default_environment(self) -> "PipCompileEnvironment":
        """
        Get default pip compile environment
        """
        default_env = PipCompileEnvironment(
            root=self.root,
            metadata=self.metadata,
            name=self._default_env_name,
            config=self.metadata.hatch.config["envs"].get(self._default_env_name, {}),
            matrix_variables=self.matrix_variables,
            data_directory=self.data_directory,
            isolated_data_directory=self.isolated_data_directory,
            platform=self.platform,
            verbosity=self.verbosity,
            app=self.app,
        )
        return default_env

    def _validate_default_lock(self, constraints_file: Optional[pathlib.Path]) -> None:
        """
        Validate the default lock file
        """
        if constraints_file is None:
            return
        elif not constraints_file.exists():
            error_message = (
                f"[hatch-pip-compile] The default lock file {constraints_file} does not exist."
            )
            raise LockFileNotFoundError(error_message)
        else:
            up_to_date = self._piptools_default_environment._lock_file_compare()
            if up_to_date is False:
                error_message = (
                    f"[hatch-pip-compile] The default lock file {constraints_file} is out of date. "
                    "Please update it."
                )
                raise HatchPipCompileError(error_message)
