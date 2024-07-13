"""
Integration Tests using the CLI
"""

import platform

import pytest

from hatch_pip_compile.exceptions import HatchPipCompileError
from tests.conftest import PipCompileFixture, installer_param, resolver_param


@installer_param
@resolver_param
@pytest.mark.parametrize("environment_name", ["default", "test", "lint", "docs", "misc"])
def test_invoke_environment_creates_env(
    pip_compile: PipCompileFixture, environment_name: str, resolver: str, installer: str
) -> None:
    """
    Test using the CLI runner
    """
    if installer == "pip-sync" and platform.system().lower() == "windows":
        pytest.skip("pip-sync + CLI runner not supported on Windows")
    environment = pip_compile.update_environment_resolver(
        environment=environment_name, resolver=resolver
    )
    environment = pip_compile.update_environment_installer(
        environment=environment, installer=installer
    )
    assert not pip_compile.virtualenv_exists(environment=environment)
    result = pip_compile.invoke_environment(environment=environment)
    assert result.exit_code == 0
    assert pip_compile.virtualenv_exists(environment=environment)


def test_missing_lockfile_created(pip_compile: PipCompileFixture) -> None:
    """
    Running the CLI without a lockfile creates one
    """
    environment = pip_compile.default_environment
    environment.piptools_lock_file.unlink()
    assert not environment.piptools_lock_file.exists()
    result = pip_compile.invoke_environment(environment=environment)
    assert result.exit_code == 0
    assert environment.piptools_lock_file.exists()
    assert pip_compile.virtualenv_exists(environment=environment)


def test_constraint_env_created(pip_compile: PipCompileFixture) -> None:
    """
    Running the CLI with a constraint env creates one
    """
    environment = pip_compile.test_environment
    environment.piptools_lock_file.unlink()
    environment.constraint_env.piptools_lock_file.unlink()
    result = pip_compile.invoke_environment(environment=environment)
    assert result.exit_code == 0
    assert environment.piptools_lock_file.exists()
    assert environment.constraint_env.piptools_lock_file.exists()
    assert environment.virtual_env.directory.exists()
    assert environment.constraint_env.virtual_env.directory.exists()


def test_missing_lockfile_after_prepared(pip_compile: PipCompileFixture) -> None:
    """
    After an environment is prepared the lockfile is deleted and recreated the next time
    """
    environment = pip_compile.default_environment
    # Create the environment the first time
    result = pip_compile.invoke_environment(environment=environment)
    assert result.exit_code == 0
    # Delete the lockfile
    assert environment.piptools_lock_file.exists()
    environment.piptools_lock_file.unlink()
    assert not environment.piptools_lock_file.exists()
    # Run the environment again
    result = pip_compile.invoke_environment(
        environment=environment,
    )
    assert result.exit_code == 0
    # Assert the lockfile was recreated
    assert environment.piptools_lock_file.exists()


@resolver_param
@pytest.mark.parametrize("environment_name", ["default", "test", "lint"])
def test_pip_compile_disable_cli(
    pip_compile: PipCompileFixture, environment_name: str, resolver: str
) -> None:
    """
    Test that the `PIP_COMPILE_DISABLE` environment variable raises an error
    """
    environment = pip_compile.update_environment_resolver(
        environment=environment_name, resolver=resolver
    )
    environment.piptools_lock_file.unlink(missing_ok=True)
    result = pip_compile.invoke_environment(
        environment=environment,
        env={"PIP_COMPILE_DISABLE": "1"},
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, HatchPipCompileError)


def test_prune_removes_all_environments(pip_compile: PipCompileFixture) -> None:
    """
    Assert that running `hatch env prune` removes all environments
    """
    pip_compile.default_environment.create()
    pip_compile.test_environment.create()
    assert pip_compile.default_environment.virtual_env.directory.exists()
    assert pip_compile.test_environment.virtual_env.directory.exists()
    result = pip_compile.cli_invoke(args=["env", "prune"])
    assert result.exit_code == 0
    assert not pip_compile.default_environment.virtual_env.directory.exists()
    assert not pip_compile.test_environment.virtual_env.directory.exists()


@installer_param
@resolver_param
def test_add_new_dependency(pip_compile: PipCompileFixture, installer: str, resolver: str) -> None:
    """
    Create a new environment, assert that it exists without the `requests` package,
    then add the `requests` package to the environment, assert that it is installed.
    """
    if platform.system().lower() == "windows" and installer == "pip-sync":
        pytest.skip("pip-sync + CLI runner not supported on Windows")
    environment = pip_compile.default_environment
    assert not environment.virtual_env.directory.exists()
    pip_compile.update_environment_resolver(environment=environment, resolver=resolver)
    pip_compile.update_environment_installer(environment=environment, installer=installer)
    result = pip_compile.invoke_environment(environment=environment)
    assert result.exit_code == 0
    if result.exit_code != 0:
        raise result.exception
    assert environment.virtual_env.directory.exists()
    assert not pip_compile.is_installed(environment=environment, package="requests")
    assert "requests" not in environment.piptools_lock_file.read_text()
    pip_compile.toml_doc["project"]["dependencies"] += ["requests"]
    pip_compile.update_pyproject()
    new_result = pip_compile.invoke_environment(environment=environment)
    if new_result.exit_code != 0:
        raise new_result.exception
    assert "requests" in environment.piptools_lock_file.read_text()
    assert pip_compile.is_installed(environment=environment, package="requests")


@installer_param
@resolver_param
def test_add_new_dependency_constraint_env(
    pip_compile: PipCompileFixture, installer: str, resolver: str
) -> None:
    """
    Test dependency workflow in a constraint environment
    """
    if platform.system().lower() == "windows" and installer == "pip-sync":
        pytest.skip("pip-sync + CLI runner not supported on Windows")
    environment = pip_compile.default_environment
    constraint_env = pip_compile.test_environment
    # Start with a clean slate, no environments
    assert not pip_compile.virtualenv_exists(environment=environment)
    assert not pip_compile.virtualenv_exists(environment=constraint_env)
    pip_compile.update_environment_resolver(environment=environment, resolver=resolver)
    pip_compile.update_environment_installer(environment=environment, installer=installer)
    # Invoke the constraint environment first. The default environment should not exist yet
    result = pip_compile.invoke_environment(environment=constraint_env)
    if result.exit_code != 0:
        raise result.exception
    assert not pip_compile.virtualenv_exists(environment=environment)
    assert pip_compile.is_installed(environment=constraint_env, package="pytest")
    assert "requests" not in environment.piptools_lock_file.read_text()
    assert not pip_compile.is_installed(environment=constraint_env, package="requests")
    # Now add the `requests` package to the default environment, and invoke the constraint env
    # The `requests` package should be installed in both environments and both lockfiles updated
    pip_compile.toml_doc["project"]["dependencies"] += ["requests"]
    pip_compile.update_pyproject()
    pip_compile.invoke_environment(environment=constraint_env)
    assert "requests" in environment.piptools_lock_file.read_text()
    assert "requests" in constraint_env.piptools_lock_file.read_text()
    assert pip_compile.is_installed(environment=environment, package="requests")
    assert pip_compile.is_installed(environment=constraint_env, package="requests")
