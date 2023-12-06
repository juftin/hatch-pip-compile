"""
Plugin tests.
"""

from subprocess import CompletedProcess
from unittest.mock import Mock, patch

from hatch.utils.fs import Path

from hatch_pip_compile.plugin import PipCompileEnvironment


def test_lockfile_path(
    isolation: Path,
    default_environment: PipCompileEnvironment,
    test_environment: PipCompileEnvironment,
):
    """
    Test the default lockfile paths
    """
    assert default_environment.piptools_lock_file == isolation / "requirements.txt"
    assert (
        test_environment.piptools_lock_file == isolation / "requirements" / "requirements-test.txt"
    )


def test_piptools_constraints_file(
    default_environment: PipCompileEnvironment,
    test_environment: PipCompileEnvironment,
):
    """
    Test constraints paths
    """
    assert default_environment.piptools_constraints_file is None
    assert test_environment.piptools_constraints_file == default_environment.piptools_lock_file


def test_expected_dependencies(
    default_environment: PipCompileEnvironment,
    test_environment: PipCompileEnvironment,
):
    """
    Test expected dependencies from `PipCompileEnvironment`
    """
    assert set(default_environment.dependencies) == {"hatch"}
    assert set(test_environment.dependencies) == {"pytest", "pytest-cov", "hatch"}


def test_lockfile_up_to_date(
    default_environment: PipCompileEnvironment,
    test_environment: PipCompileEnvironment,
):
    """
    Test the prepared lockfiles are up-to-date
    """
    assert default_environment.lockfile_up_to_date is True
    assert test_environment.lockfile_up_to_date is True


def test_lockfile_up_to_date_missing(
    default_environment: PipCompileEnvironment,
):
    """
    Test the `lockfile_up_to_date` property when the lockfile is missing
    """
    default_environment.piptools_lock_file.unlink()
    assert default_environment.lockfile_up_to_date is False
    assert default_environment.dependencies_in_sync() is False


def test_lockfile_up_to_date_empty(
    default_environment: PipCompileEnvironment,
):
    """
    Test the `lockfile_up_to_date` property when the lockfile is empty
    """
    default_environment.piptools_lock_file.write_text("")
    assert default_environment.lockfile_up_to_date is False
    assert default_environment.dependencies_in_sync() is False


def test_lockfile_up_to_date_mismatch(
    default_environment: PipCompileEnvironment,
):
    """
    Test the `lockfile_up_to_date` property when the lockfile is mismatched
    """
    lock_text = default_environment.piptools_lock_file.read_text()
    lock_text = lock_text.replace("# - hatch", "#")
    default_environment.piptools_lock_file.write_text(lock_text)
    assert default_environment.lockfile_up_to_date is False


@patch("hatch_pip_compile.plugin.PipCompileEnvironment.plugin_check_command")
def test_pip_compile_cli(mock_check_command: Mock, default_environment: PipCompileEnvironment):
    """
    Test the `pip_compile_cli` method is called with the expected arguments
    """
    mock_check_command.return_value = CompletedProcess(
        args=[], returncode=0, stdout=b"", stderr=b""
    )
    default_environment.pip_compile_cli()
    expected_call = [
        "python",
        "-m",
        "piptools",
        "compile",
        "--quiet",
        "--strip-extras",
        "--no-header",
        "--resolver=backtracking",
        "--output-file",
    ]
    call_args = list(mock_check_command.call_args)[0][0][:-2]
    assert call_args == expected_call
