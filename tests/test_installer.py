"""
Installation Tests
"""

from typing import Dict, Type
from unittest.mock import Mock

import pytest

from hatch_pip_compile.exceptions import HatchPipCompileError
from hatch_pip_compile.installer import PluginInstaller
from tests.conftest import PipCompileFixture


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


@pytest.mark.parametrize("installer", ["pip", "pip-sync"])
def test_installer_type(
    installer: str, installer_dict: Dict[str, Type[PluginInstaller]], pip_compile: PipCompileFixture
) -> None:
    """
    Test the `pip-compile-installer` configuration option
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = installer
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert isinstance(updated_environment.installer, installer_dict[installer])


def test_installer_unknown(pip_compile: PipCompileFixture) -> None:
    """
    Test that an exception is raised when an unknown installer is configured
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = "unknown"
    pip_compile.update_pyproject()
    with pytest.raises(HatchPipCompileError):
        _ = pip_compile.reload_environment("default")
