"""
Shared fixtures for tests.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
import shutil
from dataclasses import dataclass, field
from subprocess import CompletedProcess
from typing import Generator
from unittest.mock import patch

import pytest
import tomlkit
from hatch.cli.application import Application
from hatch.config.constants import AppEnvVars, ConfigEnvVars, PublishEnvVars
from hatch.project.core import Project
from hatch.utils.fs import Path, temp_directory
from hatch.utils.platform import Platform

from hatch_pip_compile.plugin import PipCompileEnvironment


@pytest.fixture
def mock_check_command() -> Generator[patch, None, None]:
    """
    Disable the `plugin_check_command` for testing
    """
    with patch("hatch_pip_compile.plugin.PipCompileEnvironment.plugin_check_command") as mock:
        mock.return_value = CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")
        yield mock


@pytest.fixture
def subprocess_run() -> Generator[patch, None, None]:
    """
    Disable the `subprocess.run` for testing
    """
    with patch("subprocess.run") as mock:
        mock.return_value = CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")
        yield mock


@pytest.fixture
def platform() -> Platform:
    """
    Platform
    """
    return Platform()


@pytest.fixture
def isolation(platform: Platform) -> Generator[Path, None, None]:
    """
    Isolated hatch environment for testing.
    """
    with temp_directory() as temp_dir:
        data_dir = pathlib.Path(__file__).parent / "data"
        shutil.copytree(data_dir, temp_dir, dirs_exist_ok=True)
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()
        default_env_vars = {
            AppEnvVars.NO_COLOR: "1",
            ConfigEnvVars.DATA: str(data_dir),
            ConfigEnvVars.CACHE: str(cache_dir),
            PublishEnvVars.REPO: "dev",
            "HATCH_SELF_TESTING": "true",
            "PYAPP_COMMAND_NAME": os.urandom(4).hex(),
            "GIT_AUTHOR_NAME": "Foo Bar",
            "GIT_AUTHOR_EMAIL": "foo@bar.baz",
            "COLUMNS": "80",
            "LINES": "24",
        }
        if platform.windows:  # pragma: no cover
            default_env_vars["COMSPEC"] = "cmd.exe"
        else:
            default_env_vars["SHELL"] = "sh"

        with temp_dir.as_cwd(default_env_vars):
            os.environ.pop(AppEnvVars.ENV_ACTIVE, None)
            os.environ.pop(AppEnvVars.FORCE_COLOR, None)
            yield temp_dir


@dataclass
class PipCompileFixture:
    """
    Testing Fixture Data Container
    """

    __test__ = False

    isolation: pathlib.Path
    toml_doc: tomlkit.TOMLDocument
    pyproject: pathlib.Path
    project: Project
    platform: Platform
    isolated_data_dir: pathlib.Path

    application: Application = field(init=False)
    default_environment: PipCompileEnvironment = field(init=False)
    test_environment: PipCompileEnvironment = field(init=False)

    def __post_init__(self) -> None:
        """
        Post Init
        """
        self.application = Application(
            exit_func=lambda x: None,  # noqa: ARG005
            verbosity=0,
            interactive=False,
            enable_color=False,
        )
        self.application.data_dir = self.isolated_data_dir
        self.application.project = self.project
        self.default_environment = self.reload_environment("default")
        self.test_environment = self.reload_environment("test")

    def reload_environment(self, environment: str | PipCompileEnvironment) -> PipCompileEnvironment:
        """
        Reload a new environment given the current state of the isolated project
        """
        if isinstance(environment, PipCompileEnvironment):
            environment_name = environment.name
        else:
            environment_name = environment
        new_project = Project(self.isolation)
        return PipCompileEnvironment(
            root=self.isolation,
            metadata=new_project.metadata,
            name=environment_name,
            config=new_project.config.envs[environment_name],
            matrix_variables={},
            data_directory=self.isolated_data_dir,
            isolated_data_directory=self.isolated_data_dir,
            platform=self.platform,
            verbosity=0,
        )

    def update_pyproject(self) -> None:
        """
        Update pyproject.toml
        """
        tomlkit.dump(self.toml_doc, self.pyproject.open("w"))

    @contextlib.contextmanager
    def chdir(self) -> Generator[None, None, None]:
        """
        Change the working directory to the isolation
        """
        current_dir = os.getcwd()
        try:
            os.chdir(self.isolation)
            yield
        finally:
            os.chdir(current_dir)

    def update_environment_resolver(
        self, environment: str | PipCompileEnvironment, resolver: str
    ) -> PipCompileEnvironment:
        """
        Update the environment resolver
        """
        if isinstance(environment, PipCompileEnvironment):
            environment_name = environment.name
        else:
            environment_name = environment
        self.toml_doc["tool"]["hatch"]["envs"][environment_name]["pip-compile-resolver"] = resolver
        self.update_pyproject()
        return self.reload_environment(environment_name)

    def update_environment_installer(
        self, environment: str | PipCompileEnvironment, installer: str
    ) -> PipCompileEnvironment:
        """
        Update the environment installer
        """
        if isinstance(environment, PipCompileEnvironment):
            environment_name = environment.name
        else:
            environment_name = environment
        self.toml_doc["tool"]["hatch"]["envs"][environment_name][
            "pip-compile-installer"
        ] = installer
        self.update_pyproject()
        return self.reload_environment(environment_name)


@pytest.fixture
def pip_compile(
    isolation: Path,
    platform: Platform,
) -> PipCompileFixture:
    """
    PipCompile testing fixture
    """
    pyproject = isolation / "pyproject.toml"
    isolated_data_dir = Path(os.environ[ConfigEnvVars.DATA])
    return PipCompileFixture(
        isolation=isolation,
        toml_doc=tomlkit.parse(string=pyproject.read_text()),
        pyproject=pyproject,
        project=Project(path=isolation),
        platform=platform,
        isolated_data_dir=isolated_data_dir,
    )


@pytest.fixture(autouse=True)
def pip_compile_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Delete the PIP_COMPILE_DISABLE environment variable
    """
    monkeypatch.delenv("PIP_COMPILE_DISABLE", raising=False)


resolver_param = pytest.mark.parametrize("resolver", ["pip-compile", "uv"])
installer_param = pytest.mark.parametrize("installer", ["pip", "pip-sync", "uv"])
