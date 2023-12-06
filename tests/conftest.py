"""
Shared fixtures for tests.
"""

import os
import pathlib
import shutil
from typing import Generator

import pytest
from hatch.config.constants import AppEnvVars, ConfigEnvVars, PublishEnvVars
from hatch.project.core import Project
from hatch.utils.fs import Path, temp_directory
from hatch.utils.platform import Platform
from platformdirs import user_cache_dir, user_data_dir

from hatch_pip_compile.plugin import PipCompileEnvironment


@pytest.fixture(scope="session")
def platform() -> Platform:
    """
    Platform information.
    """
    return Platform()


@pytest.fixture()
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
        if platform.windows:
            default_env_vars["COMSPEC"] = "cmd.exe"
        else:
            default_env_vars["SHELL"] = "sh"

        with temp_dir.as_cwd(default_env_vars):
            os.environ.pop(AppEnvVars.ENV_ACTIVE, None)
            os.environ.pop(AppEnvVars.FORCE_COLOR, None)
            yield temp_dir


@pytest.fixture
def isolated_data_dir() -> Path:
    """
    Isolated data directory for testing.
    """
    return Path(os.environ[ConfigEnvVars.DATA])


@pytest.fixture
def default_data_dir() -> Path:
    """
    Path to Data Directory
    """
    return Path(user_data_dir("hatch", appauthor=False))


@pytest.fixture
def default_cache_dir() -> Path:
    """
    Path to Cache Directory
    """
    return Path(user_cache_dir("hatch", appauthor=False))


@pytest.fixture
def project(isolation: Path) -> Project:
    """
    Standard project configuration
    """
    return Project(isolation)


@pytest.fixture
def default_environment(
    project: Project, isolated_data_dir: Path, platform: Platform, isolation: Path
) -> PipCompileEnvironment:
    """
    Isolated PipCompileEnvironment - `default`
    """
    environment = PipCompileEnvironment(
        root=isolation,
        metadata=project.metadata,
        name="default",
        config=project.config.envs["default"],
        matrix_variables={},
        data_directory=isolated_data_dir,
        isolated_data_directory=isolated_data_dir,
        platform=platform,
        verbosity=0,
    )
    return environment


@pytest.fixture
def test_environment(
    project: Project, isolated_data_dir: Path, platform: Platform, isolation: Path
) -> PipCompileEnvironment:
    """
    Isolated PipCompileEnvironment - `test`
    """
    environment = PipCompileEnvironment(
        root=isolation,
        metadata=project.metadata,
        name="test",
        config=project.config.envs["test"],
        matrix_variables={},
        data_directory=isolated_data_dir,
        isolated_data_directory=isolated_data_dir,
        platform=platform,
        verbosity=0,
    )
    return environment
