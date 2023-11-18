"""
hatch-pip-compile plugin
"""

import pathlib
import re
import tempfile
from textwrap import dedent
from typing import Any, Dict, List

from hatch.env.virtual import VirtualEnvironment


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
                lock_filename = f".hatch/{self.name}.lock"
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
            "pip-compile-header": bool,
            "pip-compile-strip-extras": bool,
            "pip-compile-args": List[str],
        }

    def _pip_compile_command(self, output_file: pathlib.Path, input_file: pathlib.Path) -> None:
        """
        Run pip-compile
        """
        self.platform.check_command(self.construct_pip_install_command(["pip-tools"]))
        cmd = [
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "compile",
            "--quiet",
            (
                "--strip-extras"
                if self.config.get("pip-compile-strip-extras", True) is True
                else "--no-strip-extras"
            ),
            "--header" if self.config.get("pip-compile-header", False) is True else "--no-header",
            "--output-file",
            str(output_file),
            "--resolver=backtracking",
        ]
        if self.config.get("pip-compile-hashes", True) is True:
            cmd.append("--generate-hashes")
        cmd.extend(self.config.get("pip-compile-args", []))
        cmd.append(str(input_file))
        self.platform.check_command(cmd)
        if self.config.get("pip-compile-header", False) is False:
            self._post_process_lockfile()

    def _pip_compile_cli(self) -> None:
        """
        Run pip-compile
        """
        self._piptools_lock_file.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            input_file = tmp_path / f"{self.name}.in"
            input_file.write_text("\n".join([*self.dependencies, ""]))
            self._pip_compile_command(output_file=self._piptools_lock_file, input_file=input_file)

    def _root_requirements(self) -> None:
        """
        Run pip-compile
        """
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
        cmd = [
            self.virtual_env.python_info.executable,
            "-m",
            "piptools",
            "sync",
            "--python-executable",
            str(self.virtual_env.python_info.executable),
            str(self._piptools_lock_file),
        ]
        self.platform.check_command(cmd)

    def install_project_dev_mode(self):
        """
        Install the project the first time in dev mode
        """
        with self.safe_activation():
            self._pip_compile_cli()
            self._pip_sync_cli()
            super().install_project_dev_mode()

    def dependencies_in_sync(self):
        """
        Handle whether dependencies should be synced
        """
        if len(self.dependencies) > 0 and (self._piptools_lock_file.exists() is False):
            return False
        elif len(self.dependencies) > 0 and (self._piptools_lock_file.exists() is True):
            if self.config.get("pip-compile-header", False) is True:
                expected_locks = True
            else:
                expected_locks = self._lock_file_compare()
            if expected_locks is False:
                return False
        return super().dependencies_in_sync()

    def sync_dependencies(self):
        """
        Sync dependencies
        """
        with self.safe_activation():
            self._pip_compile_cli()
            self._pip_sync_cli()
            super().install_project_dev_mode()

    def _post_process_lockfile(self) -> None:
        """
        Post process lockfile
        """
        joined_dependencies = "\n        # - ".join(self.dependencies)
        prefix = f"""
        ####################################################################################
        # 🔒 hatch-pip-compile 🔒
        #
        # - {joined_dependencies}
        #
        ####################################################################################
        """
        lockfile_text = self._piptools_lock_file.read_text()
        new_data = re.sub(
            rf"-r \S*/{self.name}\.in",
            f"{self.metadata.name} (pyproject.toml)",
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
