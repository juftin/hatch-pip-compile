"""
Installation Tests
"""

from subprocess import CompletedProcess
from unittest.mock import Mock, patch

from hatch_pip_compile.plugin import PipCompileEnvironment


@patch("hatch_pip_compile.plugin.PipCompileEnvironment.plugin_check_command")
def test_pip_install_dependencies(
    mock_check_command: Mock, default_environment: PipCompileEnvironment
) -> None:
    """
    Assert the `pip` installation command is called with the expected arguments
    """
    mock_check_command.return_value = CompletedProcess(
        args=[], returncode=0, stdout=b"", stderr=b""
    )
    default_environment.create()
    default_environment.installer.install_dependencies()
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
