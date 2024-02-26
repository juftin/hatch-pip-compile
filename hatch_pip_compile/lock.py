"""
hatch-pip-compile header operations
"""

from __future__ import annotations

import hashlib
import logging
import pathlib
import re
from textwrap import dedent
from typing import Iterable

from packaging.requirements import Requirement
from packaging.version import Version
from piptools._compat.pip_compat import PipSession, parse_requirements

from hatch_pip_compile.base import HatchPipCompileBase
from hatch_pip_compile.exceptions import LockFileError

logger = logging.getLogger(__name__)


class PipCompileLock(HatchPipCompileBase):
    """
    Pip Compile Lock File Operations
    """

    def process_lock(self, lockfile: pathlib.Path) -> None:
        """
        Post process lockfile
        """
        version = f"{self.current_python_version.major}.{self.current_python_version.minor}"
        raw_prefix = f"""
        #
        # This file is autogenerated by hatch-pip-compile with Python {version}
        #
        """
        prefix = dedent(raw_prefix).strip()
        joined_dependencies = "\n".join([f"# - {dep}" for dep in self.environment.dependencies])
        lockfile_text = lockfile.read_text()
        cleaned_input_file = re.sub(
            rf"-r \S*[\\/]{self.environment.name}\.in",
            f"hatch.envs.{self.environment.name}",
            lockfile_text,
        )
        if self.environment.piptools_constraints_file is not None:
            lockfile_contents = self.environment.piptools_constraints_file.read_bytes()
            cross_platform_contents = lockfile_contents.replace(b"\r\n", b"\n")
            constraint_sha = hashlib.sha256(cross_platform_contents).hexdigest()
            constraints_path = self.environment.piptools_constraints_file.relative_to(
                self.environment.root
            ).as_posix()
            constraints_line = f"# [constraints] {constraints_path} (SHA256: {constraint_sha})"
            joined_dependencies = "\n".join([constraints_line, "#", joined_dependencies])
            cleaned_input_file = re.sub(
                r"-c \S*",
                lambda _: f"-c {constraints_path}",
                cleaned_input_file,
            )
        prefix += "\n" + joined_dependencies + "\n#"
        new_text = prefix + "\n\n" + cleaned_input_file
        lockfile.write_text(new_text)

    def read_header_requirements(self) -> list[Requirement]:
        """
        Read requirements from lock file header
        """
        lock_file_text = self.environment.piptools_lock_file.read_text()
        parsed_requirements = []
        for line in lock_file_text.splitlines():
            if line.startswith("# - "):
                requirement = Requirement(line[4:])
                parsed_requirements.append(requirement)
            elif not line.startswith("#"):
                break
        return parsed_requirements

    @property
    def current_python_version(self) -> Version:
        """
        Get python version

        In the case of running as a hatch plugin, the `virtualenv` will be set,
        otherwise it will be None and the Python version will be read differently.
        """
        if self.environment.virtual_env is not None:
            return Version(self.environment.virtual_env.environment["python_version"])
        else:
            msg = "VirtualEnv is not set"
            raise NotImplementedError(msg)

    @property
    def lock_file_version(self) -> Version:
        """
        Get lock file version
        """
        lock_file_text = self.environment.piptools_lock_file.read_text()
        match = re.search(
            r"# This file is autogenerated by hatch-pip-compile with Python (.*)", lock_file_text
        )
        if match is None:
            msg = "Could not find lock file python version"
            raise LockFileError(msg)
        return Version(match.group(1))

    def compare_python_versions(self, verbose: bool | None = None) -> bool:
        """
        Compare python versions

        Parameters
        ----------
        verbose : Optional[bool]
            Print warning if python versions are different, by default None
            which will print the warning. Used as a plugin flag.
        """
        lock_version = self.lock_file_version
        current_version = self.current_python_version
        match = (current_version.major == lock_version.major) and (
            current_version.minor == lock_version.minor
        )
        if match is False and verbose is not False:
            logger.error(
                "[hatch-pip-compile] Your Python version is different "
                "from the lock file, your results may vary."
            )
        return lock_version == current_version

    def compare_requirements(self, requirements: Iterable[Requirement]) -> bool:
        """
        Compare requirements

        Parameters
        ----------
        requirements : Iterable[Requirement]
            List of requirements to compare against the lock file
        """
        lock_requirements = self.read_header_requirements()
        return set(requirements) == set(lock_requirements)

    def compare_constraint_sha(self, sha: str) -> bool:
        """
        Compare SHA to the SHA on the lockfile
        """
        lock_file_text = self.environment.piptools_lock_file.read_text()
        match = re.search(r"# \[constraints\] \S* \(SHA256: (.*)\)", lock_file_text)
        if match is None:
            return False
        return match.group(1).strip() == sha.strip()

    def get_file_content_hash(self) -> str:
        """
        Get hash of lock file
        """
        lockfile_contents = self.environment.piptools_lock_file.read_bytes()
        cross_platform_contents = lockfile_contents.replace(b"\r\n", b"\n")
        return hashlib.sha256(cross_platform_contents).hexdigest()

    def read_lock_requirements(self) -> list[Requirement]:
        """
        Read all requirements from lock file
        """
        if not self.environment.dependencies:
            return []
        install_requirements = parse_requirements(
            str(self.environment.piptools_lock_file),
            session=PipSession(),
        )
        return [ireq.req for ireq in install_requirements]  # type: ignore[misc]
