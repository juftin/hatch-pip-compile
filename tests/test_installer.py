"""
Installation Tests
"""

from unittest.mock import Mock

import pytest

from hatch_pip_compile.exceptions import HatchPipCompileError
from tests.conftest import PipCompileFixture, installer_param


def test_pip_install_dependencies(mock_check_command: Mock, pip_compile: PipCompileFixture) -> None:
    """
    Assert the `pip` installation command is called with the expected arguments
    """
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


@installer_param
def test_installer_type(installer: str, pip_compile: PipCompileFixture) -> None:
    """
    Test the `pip-compile-installer` configuration option
    """
    updated_environment = pip_compile.update_environment_installer(
        environment="default", installer=installer
    )
    assert isinstance(
        updated_environment.installer, updated_environment.dependency_installers[installer]
    )


def test_installer_unknown(pip_compile: PipCompileFixture) -> None:
    """
    Test that an exception is raised when an unknown installer is configured
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = "unknown"
    pip_compile.update_pyproject()
    with pytest.raises(HatchPipCompileError):
        _ = pip_compile.reload_environment("default")
