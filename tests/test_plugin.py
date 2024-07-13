"""
Plugin tests.
"""

from unittest.mock import Mock

import pytest

from hatch_pip_compile.exceptions import HatchPipCompileError
from hatch_pip_compile.resolver import PipCompileResolver
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
        "--no-header",
        "--resolver=backtracking",
        "--strip-extras",
        "--output-file",
    ]
    call_args = list(mock_check_command.call_args)[0][0][:-2]
    assert call_args == expected_call


def test_env_var_disabled(pip_compile: PipCompileFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test the `lockfile_up_to_date` property when the lockfile is empty
    """
    monkeypatch.setenv("PIP_COMPILE_DISABLE", "1")
    with pytest.raises(HatchPipCompileError, match="attempted to run a lockfile update"):
        pip_compile.default_environment.pip_compile_cli()


@pytest.mark.parametrize("environment_name", ["default", "misc", "docs"])
def test_constraint_env_self(pip_compile: PipCompileFixture, environment_name: str) -> None:
    """
    Test the value of the constraint env b/w the default and test environments
    """
    environment = pip_compile.reload_environment(environment=environment_name)
    assert environment.constraint_env is environment


@pytest.mark.parametrize("environment_name", ["test"])
def test_constraint_env_other(pip_compile: PipCompileFixture, environment_name: str) -> None:
    """
    Test the value of the constraint env b/w the default and test environments
    """
    environment = pip_compile.reload_environment(environment=environment_name)
    assert environment.constraint_env.name == pip_compile.default_environment.name


@pytest.mark.parametrize("environment_name", ["default", "docs", "misc"])
def test_prepare_environment(pip_compile: PipCompileFixture, environment_name: str) -> None:
    """
    Test the `prepare_environment` method
    """
    environment = pip_compile.reload_environment(environment=environment_name)
    environment.prepare_environment()
    if environment.dependencies:
        assert environment.piptools_lock_file.exists()
    else:
        assert not environment.piptools_lock_file.exists()
    assert environment.dependencies_in_sync() is True
    assert environment.lockfile_up_to_date is True


def test_resolver_instance_default(pip_compile: PipCompileFixture) -> None:
    """
    Test the `pip-compile-resolver` option on default resolver
    """
    assert isinstance(pip_compile.default_environment.resolver, PipCompileResolver)


def test_resolver_instance_pip_compile(pip_compile: PipCompileFixture) -> None:
    """
    Test that the `PipCompileResolver` is used
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-resolver"] = "pip-compile"
    pip_compile.update_pyproject()
    environment = pip_compile.reload_environment("default")
    assert isinstance(environment.resolver, PipCompileResolver)
