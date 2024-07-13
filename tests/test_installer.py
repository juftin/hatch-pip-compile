"""
Installation Tests
"""

from unittest.mock import Mock

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
