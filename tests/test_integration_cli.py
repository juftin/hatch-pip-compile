"""
Integration Tests using the CLI
"""

import hatch.cli
import hatch.cli.env
import pytest
from click.testing import CliRunner

from hatch_pip_compile.exceptions import HatchPipCompileError
from tests.conftest import PipCompileFixture


@pytest.mark.parametrize("environment_name", ["default", "test", "lint", "docs", "misc"])
def test_invoke_environment_creates_env(
    pip_compile: PipCompileFixture, environment_name: str
) -> None:
    """
    Test using the CLI runner
    """
    runner = CliRunner()
    environment = pip_compile.reload_environment(environment=environment_name)
    venv = environment.virtual_env.directory
    assert not venv.exists()
    with runner.isolated_filesystem(pip_compile.isolation):
        result = runner.invoke(
            hatch.cli.hatch,
            args=["env", "run", "--env", environment.name, "--", "python", "--version"],
        )
    assert result.exit_code == 0
    assert venv.exists()


def test_missing_lockfile_created(pip_compile: PipCompileFixture) -> None:
    """
    Running the CLI without a lockfile creates one
    """
    runner = CliRunner()
    environment = pip_compile.default_environment
    venv = environment.virtual_env.directory
    environment.piptools_lock_file.unlink()
    assert not environment.piptools_lock_file.exists()
    with runner.isolated_filesystem(pip_compile.isolation):
        result = runner.invoke(
            hatch.cli.hatch,
            args=["env", "run", "--env", environment.name, "--", "python", "--version"],
        )
    assert result.exit_code == 0
    assert environment.piptools_lock_file.exists()
    assert venv.exists()


def test_constraint_env_created(pip_compile: PipCompileFixture) -> None:
    """
    Running the CLI with a constraint env creates one
    """
    runner = CliRunner()
    environment = pip_compile.test_environment
    environment.piptools_lock_file.unlink()
    environment.constraint_env.piptools_lock_file.unlink()
    with runner.isolated_filesystem(pip_compile.isolation):
        result = runner.invoke(
            hatch.cli.hatch,
            args=["env", "run", "--env", environment.name, "--", "python", "--version"],
        )
    assert result.exit_code == 0
    assert environment.piptools_lock_file.exists()
    assert environment.constraint_env.piptools_lock_file.exists()
    assert environment.virtual_env.directory.exists()
    assert environment.constraint_env.virtual_env.directory.exists()


def test_missing_lockfile_after_prepared(pip_compile: PipCompileFixture) -> None:
    """
    After an environment is prepared the lockfile is deleted and recreated the next time
    """
    runner = CliRunner()
    environment = pip_compile.default_environment
    # Create the environment the first time
    with runner.isolated_filesystem(pip_compile.isolation):
        result = runner.invoke(
            hatch.cli.hatch,
            args=["env", "run", "--env", environment.name, "--", "python", "--version"],
        )
        assert result.exit_code == 0
    # Delete the lockfile
    assert environment.piptools_lock_file.exists()
    environment.piptools_lock_file.unlink()
    assert not environment.piptools_lock_file.exists()
    # Run the environment again
    with runner.isolated_filesystem(pip_compile.isolation):
        result = runner.invoke(
            hatch.cli.hatch,
            args=["env", "run", "--env", environment.name, "--", "python", "--version"],
        )
        assert result.exit_code == 0
    # Assert the lockfile was recreated
    assert environment.piptools_lock_file.exists()


@pytest.mark.parametrize("environment_name", ["default", "test", "lint"])
def test_pip_compile_disable_cli(pip_compile: PipCompileFixture, environment_name: str) -> None:
    """
    Test that the `PIP_COMPILE_DISABLE` environment variable raises an error
    """
    runner = CliRunner()
    environment = pip_compile.reload_environment(environment=environment_name)
    environment.piptools_lock_file.unlink(missing_ok=True)
    with runner.isolated_filesystem(pip_compile.isolation):
        result = runner.invoke(
            hatch.cli.hatch,
            args=["-v", "env", "run", "--env", environment.name, "--", "python", "--version"],
            env={"PIP_COMPILE_DISABLE": "1"},
        )
        assert result.exit_code == 1
        assert isinstance(result.exception, HatchPipCompileError)


def test_prune_removes_all_environments(pip_compile: PipCompileFixture) -> None:
    """
    Assert that running `hatch env prune` removes all environments
    """
    runner = CliRunner()
    pip_compile.default_environment.create()
    pip_compile.test_environment.create()
    venv_dir = pip_compile.isolation / ".venv"
    assert venv_dir.exists()
    assert len(list(venv_dir.iterdir())) == 2
    with runner.isolated_filesystem(pip_compile.isolation):
        result = runner.invoke(
            hatch.cli.hatch,
            args=["env", "prune"],
        )
    assert result.exit_code == 0
    venv_dir.mkdir(exist_ok=True)
    assert len(list(venv_dir.iterdir())) == 0
