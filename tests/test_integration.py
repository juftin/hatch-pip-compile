"""
Integration Tests

These tests are "integration" tests in that they test the
interaction between the various components of hatch-pip-compile
and external tools (pip-tools / pip).
"""

import sys

import hatch
import packaging.requirements
import pytest

from tests.conftest import PipCompileFixture, installer_param, resolver_param

try:
    match_major, hatch_minor, _ = hatch._version.__version__.split(".")
except AttributeError:
    match_major, hatch_minor, _ = hatch.__about__.__version__.split(".")


@installer_param
@resolver_param
def test_new_dependency(
    installer: str,
    pip_compile: PipCompileFixture,
    resolver: str,
) -> None:
    """
    Test adding a new dependency
    """
    if installer == "pip-sync" and sys.platform == "win32":  # pragma: no cover
        pytest.skip("Flaky test on Windows")
    default_env = pip_compile.update_environment_resolver(environment="default", resolver=resolver)
    original_requirements = default_env.piptools_lock.read_header_requirements()
    assert original_requirements == [packaging.requirements.Requirement("hatch")]
    pip_compile.toml_doc["project"]["dependencies"] = ["requests"]
    pip_compile.update_pyproject()
    updated_environment = pip_compile.update_environment_installer(
        environment=default_env, installer=installer
    )
    assert isinstance(
        updated_environment.installer, updated_environment.dependency_installers[installer]
    )
    assert updated_environment.dependencies == ["requests"]
    pip_compile.application.prepare_environment(environment=updated_environment)
    assert updated_environment.lockfile_up_to_date is True
    new_lockfile_requirements = (
        pip_compile.default_environment.piptools_lock.read_header_requirements()
    )
    assert new_lockfile_requirements == [packaging.requirements.Requirement("requests")]
    result = updated_environment.plugin_check_command(
        command=["python", "-m", "pip", "list"],
        capture_output=True,
    )
    assert "requests" in result.stdout.decode()


@installer_param
@resolver_param
def test_delete_dependencies(
    installer: str,
    pip_compile: PipCompileFixture,
    resolver: str,
) -> None:
    """
    Test deleting all dependencies also deletes the lockfile
    """
    if installer == "pip-sync" and sys.platform == "win32":  # pragma: no cover
        pytest.skip("Flaky test on Windows")
    pip_compile.update_environment_resolver(
        environment=pip_compile.default_environment, resolver=resolver
    )
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = installer
    pip_compile.toml_doc["project"]["dependencies"] = []
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert isinstance(
        updated_environment.installer, updated_environment.dependency_installers[installer]
    )
    assert updated_environment.dependencies == []
    assert updated_environment.lockfile_up_to_date is False
    pip_compile.application.prepare_environment(environment=updated_environment)
    assert updated_environment.lockfile_up_to_date is True
    assert (pip_compile.isolation / ".venv" / "hatch-pip-compile-test").exists()
    assert updated_environment.dependencies == []
    assert updated_environment.piptools_lock_file.exists() is False


@resolver_param
def test_create_constraint_environment(pip_compile: PipCompileFixture, resolver: str) -> None:
    """
    Syncing an environment with a constraint env also syncs the constraint env
    """
    pip_compile.update_environment_resolver(environment="default", resolver=resolver)
    original_requirements = pip_compile.default_environment.piptools_lock.read_header_requirements()
    assert original_requirements == [packaging.requirements.Requirement("hatch")]
    pip_compile.toml_doc["project"]["dependencies"] = ["requests"]
    pip_compile.update_pyproject()
    test_environment = pip_compile.reload_environment("test")
    pip_compile.application.prepare_environment(environment=test_environment)
    new_lockfile_requirements = (
        pip_compile.default_environment.piptools_lock.read_header_requirements()
    )
    assert new_lockfile_requirements == [packaging.requirements.Requirement("requests")]
    result = test_environment.plugin_check_command(
        command=["python", "-m", "pip", "list"],
        capture_output=True,
    )
    assert "pytest" in result.stdout.decode()


@resolver_param
def test_dependency_uninstalled(pip_compile: PipCompileFixture, resolver: str) -> None:
    """
    An environment is prepared, then a dependency is uninstalled,
    the environment should be out of sync even though the lockfile
    is good
    """
    test_env = pip_compile.update_environment_resolver(environment="test", resolver=resolver)
    pip_compile.application.prepare_environment(environment=test_env)
    list_result = test_env.plugin_check_command(
        command=["python", "-m", "pip", "list"],
        capture_output=True,
    )
    assert "pytest" in list_result.stdout.decode()
    assert test_env.dependencies_in_sync() is True
    test_env.plugin_check_command(
        command=["python", "-m", "pip", "uninstall", "pytest", "pytest-cov", "-y"],
    )
    new_list_result = test_env.plugin_check_command(
        command=["python", "-m", "pip", "list"],
        capture_output=True,
    )
    assert "pytest" not in new_list_result.stdout.decode()
    assert test_env.lockfile_up_to_date is True
    assert test_env.dependencies_in_sync() is False


@resolver_param
def test_lockfile_missing(pip_compile: PipCompileFixture, resolver: str) -> None:
    """
    Lockfile missing on previously prepared environment
    """
    # Prepare the test environment, assert it is in sync
    test_env = pip_compile.update_environment_resolver(environment="test", resolver=resolver)
    pip_compile.application.prepare_environment(environment=test_env)
    assert test_env.dependencies_in_sync() is True
    # Delete the lockfile, assert environment is in sync but lockfile is missing
    test_env.piptools_lock_file.unlink()
    updated_environment = pip_compile.reload_environment("test")
    list_result = updated_environment.plugin_check_command(
        command=["python", "-m", "pip", "list"],
        capture_output=True,
    )
    assert "pytest" in list_result.stdout.decode()
    assert updated_environment.dependencies_in_sync() is False
    # Prepare the environment again, assert it is in sync
    pip_compile.application.prepare_environment(environment=updated_environment)
    new_updated_environment = pip_compile.reload_environment("test")
    assert new_updated_environment.dependencies_in_sync() is True
    assert new_updated_environment.piptools_lock_file.exists() is True


@pytest.mark.skipif(match_major == "1" and hatch_minor == "7", reason="hatch 1.8.0+ required")
def test_check_dependency_hash_creates_lock(pip_compile: PipCompileFixture) -> None:
    """
    Calling `dependency_hash` creates a lockfile when one does not exist
    """
    pip_compile.application.prepare_environment(environment=pip_compile.default_environment)
    pip_compile.default_environment.piptools_lock_file.unlink()
    updated_environment = pip_compile.reload_environment("default")
    _ = updated_environment.dependency_hash()
    assert updated_environment.piptools_lock_file.exists() is True


@resolver_param
def test_dependencies_in_sync(pip_compile: PipCompileFixture, resolver: str) -> None:
    """
    Test the `dependencies_in_sync` method
    """
    pip_compile.update_environment_resolver(environment="default", resolver=resolver)
    pip_compile.default_environment.create()
    assert pip_compile.default_environment.lockfile_up_to_date is True
    assert pip_compile.default_environment.dependencies_in_sync() is False
    pip_compile.application.prepare_environment(pip_compile.default_environment)
    assert pip_compile.default_environment.dependencies_in_sync() is True
