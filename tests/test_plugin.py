"""
Plugin tests.
"""

from unittest.mock import Mock

import pytest

from hatch_pip_compile.exceptions import HatchPipCompileError
from tests.conftest import PipCompileFixture


def test_lockfile_path(
    pip_compile: PipCompileFixture,
) -> None:
    """
    Test the default lockfile paths
    """
    assert (
        pip_compile.default_environment.piptools_lock_file
        == pip_compile.isolation / "requirements.txt"
    )
    assert (
        pip_compile.test_environment.piptools_lock_file
        == pip_compile.isolation / "requirements" / "requirements-test.txt"
    )


def test_piptools_constraints_file(
    pip_compile: PipCompileFixture,
) -> None:
    """
    Test constraints paths
    """
    assert pip_compile.default_environment.piptools_constraints_file is None
    assert (
        pip_compile.test_environment.piptools_constraints_file
        == pip_compile.default_environment.piptools_lock_file
    )


def test_expected_dependencies(pip_compile: PipCompileFixture) -> None:
    """
    Test expected dependencies from `PipCompileEnvironment`
    """
    assert set(pip_compile.default_environment.dependencies) == {"hatch"}
    assert set(pip_compile.test_environment.dependencies) == {"pytest", "pytest-cov", "hatch"}


def test_lockfile_up_to_date(pip_compile: PipCompileFixture) -> None:
    """
    Test the prepared lockfiles are up-to-date
    """
    assert pip_compile.default_environment.lockfile_up_to_date is True
    assert pip_compile.test_environment.lockfile_up_to_date is True


def test_lockfile_up_to_date_missing(pip_compile: PipCompileFixture) -> None:
    """
    Test the `lockfile_up_to_date` property when the lockfile is missing
    """
    pip_compile.default_environment.piptools_lock_file.unlink()
    assert pip_compile.default_environment.lockfile_up_to_date is False
    assert pip_compile.default_environment.dependencies_in_sync() is False


def test_lockfile_up_to_date_empty(pip_compile: PipCompileFixture) -> None:
    """
    Test the `lockfile_up_to_date` property when the lockfile is empty
    """
    pip_compile.default_environment.piptools_lock_file.write_text("")
    assert pip_compile.default_environment.lockfile_up_to_date is False
    assert pip_compile.default_environment.dependencies_in_sync() is False


def test_lockfile_up_to_date_mismatch(pip_compile: PipCompileFixture) -> None:
    """
    Test the `lockfile_up_to_date` property when the lockfile is mismatched
    """
    lock_text = pip_compile.default_environment.piptools_lock_file.read_text()
    lock_text = lock_text.replace("# - hatch", "#")
    pip_compile.default_environment.piptools_lock_file.write_text(lock_text)
    assert pip_compile.default_environment.lockfile_up_to_date is False


def test_pip_compile_cli(mock_check_command: Mock, pip_compile: PipCompileFixture) -> None:
    """
    Test the `pip_compile_cli` method is called with the expected arguments
    """
    pip_compile.default_environment.pip_compile_cli()
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


def test_environment_change(
    pip_compile: PipCompileFixture,
) -> None:
    """
    Override the `dependencies` property and assert the `lockfile_up_to_date` property is False
    """
    assert pip_compile.test_environment.lockfile_up_to_date is True
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["test"]["dependencies"] = ["requests"]
    pip_compile.update_pyproject()
    new_environment = pip_compile.reload_environment("test")
    assert new_environment.dependencies == ["requests", "hatch"]
    assert new_environment.lockfile_up_to_date is False


def test_constraint_dependency_change(
    pip_compile: PipCompileFixture, mock_check_command: Mock
) -> None:
    """
    Update the constraint environment and assert it and its downstream environments are out-of-sync
    """
    assert pip_compile.default_environment.lockfile_up_to_date is True
    assert pip_compile.test_environment.lockfile_up_to_date is True
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["dependencies"] = ["requests"]
    pip_compile.update_pyproject()
    new_default_env = pip_compile.reload_environment("default")
    new_test_env = pip_compile.reload_environment("test")
    assert new_default_env.lockfile_up_to_date is False
    assert new_test_env.lockfile_up_to_date is False


def test_env_var_disabled(pip_compile: PipCompileFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test the `lockfile_up_to_date` property when the lockfile is empty
    """
    monkeypatch.setenv("PIP_COMPILE_DISABLE", "1")
    with pytest.raises(HatchPipCompileError, match="attempted to run a lockfile update"):
        pip_compile.default_environment.pip_compile_cli()


def test_constraint_env_self(pip_compile: PipCompileFixture) -> None:
    """
    Test the value of the constraint env b/w the default and test environments
    """
    assert (
        pip_compile.default_environment.constraint_env.name == pip_compile.default_environment.name
    )
    assert pip_compile.test_environment.constraint_env.name == pip_compile.default_environment.name
