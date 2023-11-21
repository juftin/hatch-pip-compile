"""
hatch-pip-compile plugin
"""

import logging
import pathlib
import re
import tempfile
from textwrap import dedent
from typing import Any, Dict, List

from hatch.env.virtual import VirtualEnvironment
from packaging.version import Version

logger = logging.getLogger(__name__)


class PipCompileEnvironment(VirtualEnvironment):
    """
    Virtual Environment supported by pip-compile
    """

    PLUGIN_NAME = "pip-compile"

    def __init__(self, *args, **kwargs):
        """
        Initialize PipCompileEnvironment with extra attributes
        """
        super().__init__(*args, **kwargs)
        lock_filename_config = self.config.get("lock-filename")
        if lock_filename_config is None:
            if self.name == "default":
                lock_filename = "requirements.txt"
            else:
                lock_filename = f"requirements/requirements-{self.name}.txt"
        else:
            with self.metadata.context.apply_context(self.context):
                lock_filename = self.metadata.context.format(lock_filename_config)
        self._piptools_lock_file = self.root / lock_filename

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
            super().install_project_dev_mode()

    def _pip_compile_command(self, output_file: pathlib.Path, input_file: pathlib.Path) -> None:
        """
        Run pip-compile
        """
        if self._piptools_lock_file.exists() is True:
            correct_environment = self._lock_file_compare()
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
        cmd.extend(self.config.get("pip-compile-args", []))
        cmd.append(str(input_file))
        self.virtual_env.platform.check_command(cmd)
        self._post_process_lockfile()

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
        _ = self._compare_python_versions()
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

    def install_project_dev_mode(self):
        """
        Install the project the first time in dev mode

        The same implementation as `sync_dependencies`
        due to the way `pip-sync` uninstalls our editable root
        package
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

    def _post_process_lockfile(self) -> None:
        """
        Post process lockfile
        """
        python_version = self._get_python_version()
        version = f"{python_version.major}.{python_version.minor}"
        joined_dependencies = "\n        # - ".join(self.dependencies)
        prefix = f"""
        #
        # This file is autogenerated by hatch-pip-compile with Python {version}
        #
        # - {joined_dependencies}
        #
        """
        lockfile_text = self._piptools_lock_file.read_text()
        new_data = re.sub(
            rf"-r \S*/{self.name}\.in",
            f"{self.metadata.name}",
            lockfile_text,
        )
        new_text = dedent(prefix).strip() + "\n\n" + new_data
        self._piptools_lock_file.write_text(new_text)

    def _lock_file_compare(self) -> bool:
        """
        Compare lock file
        """
        lock_file_text = self._piptools_lock_file.read_text()
        parsed_requirements = []
        for line in lock_file_text.splitlines():
            if line.startswith("# - "):
                rest_of_line = line[4:]
                parsed_requirements.append(rest_of_line)
            elif not line.startswith("#"):
                break
        expected_output = "\n".join([*parsed_requirements, ""])
        new_output = "\n".join([*self.dependencies, ""])
        return expected_output == new_output

    def _get_python_version(self) -> Version:
        """
        Get python version
        """
        python_version_output = self.virtual_env.platform.check_command(
            [self.virtual_env.python_info.executable, "--version"],
            capture_output=True,
        )
        version_str = python_version_output.stdout.decode("utf-8").strip()
        version_number = version_str.split(" ")[1]
        return Version(version_number)

    def _compare_python_versions(self) -> bool:
        """
        Compare python versions
        """
        current_version = self._get_python_version()
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
