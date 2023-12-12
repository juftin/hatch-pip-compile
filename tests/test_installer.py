"""
Installation Tests
"""

from subprocess import CompletedProcess
from unittest.mock import Mock, patch

import pytest

from hatch_pip_compile.exceptions import HatchPipCompileError
from hatch_pip_compile.installer import PipInstaller, PipSyncInstaller
from tests.conftest import PipCompileFixture


@patch("hatch_pip_compile.plugin.PipCompileEnvironment.plugin_check_command")
def test_pip_install_dependencies(mock_check_command: Mock, pip_compile: PipCompileFixture) -> None:
    """
    Assert the `pip` installation command is called with the expected arguments
    """
    mock_check_command.return_value = CompletedProcess(
        args=[], returncode=0, stdout=b"", stderr=b""
    )
    pip_compile.default_environment.create()
    pip_compile.default_environment.installer.install_dependencies()
    expected_call = [
        "python",
        "-u",
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-python-version-warning",
        "-q",
        "--requirement",
    ]
    call_args = list(mock_check_command.call_args)[0][0][:-1]
    assert call_args == expected_call


def test_installer_pip(pip_compile: PipCompileFixture) -> None:
    """
    Test that the `pip` installer is used when configured
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = "pip"
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert isinstance(updated_environment.installer, PipInstaller)


def test_installer_pip_sync(pip_compile: PipCompileFixture) -> None:
    """
    Test that the `pip-sync` installer is used when configured
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = "pip-sync"
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert isinstance(updated_environment.installer, PipSyncInstaller)


def test_installer_unknown(pip_compile: PipCompileFixture) -> None:
    """
    Test that an exception is raised when an unknown installer is configured
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = "unknown"
    pip_compile.update_pyproject()
    with pytest.raises(HatchPipCompileError):
        _ = pip_compile.reload_environment("default")
