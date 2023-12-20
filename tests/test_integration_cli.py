"""
Integration Tests using the CLI
"""

import hatch.cli
import hatch.cli.env
from click.testing import CliRunner

from tests.conftest import PipCompileFixture


def test_invoke_environment_creates_env(pip_compile: PipCompileFixture) -> None:
    """
    Test using the CLI runner
    """
    runner = CliRunner()
    environment = pip_compile.test_environment
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
