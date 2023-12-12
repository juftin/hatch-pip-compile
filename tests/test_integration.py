"""
Integration Tests

These tests are "integration" tests in that they test the
interaction between the various components of hatch-pip-compile
and external tools (pip-tools / pip).
"""

from hatch_pip_compile.installer import PipSyncInstaller
from tests.conftest import PipCompileFixture


def test_new_dependency(pip_compile: PipCompileFixture) -> None:
    """
    Test adding a new dependency
    """
    original_lockfile_contents = pip_compile.default_environment.piptools_lock_file.read_text()
    pip_compile.toml_doc["project"]["dependencies"] = ["requests"]
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert updated_environment.dependencies == ["requests"]
    assert updated_environment.lockfile_up_to_date is False
    updated_environment.sync_dependencies()
    assert updated_environment.lockfile_up_to_date is True
    new_lockfile_contents = pip_compile.default_environment.piptools_lock_file.read_text()
    assert new_lockfile_contents != original_lockfile_contents


def test_new_dependency_pip_sync(pip_compile: PipCompileFixture) -> None:
    """
    Test adding a new dependency with pip-sync
    """
    original_lockfile_contents = pip_compile.default_environment.piptools_lock_file.read_text()
    pip_compile.toml_doc["project"]["dependencies"] = ["requests"]
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = "pip-sync"
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert isinstance(updated_environment.installer, PipSyncInstaller)
    updated_environment.sync_dependencies()
    assert updated_environment.lockfile_up_to_date is True
    new_lockfile_contents = pip_compile.default_environment.piptools_lock_file.read_text()
    assert new_lockfile_contents != original_lockfile_contents


def test_delete_dependencies(pip_compile: PipCompileFixture) -> None:
    """
    Test deleting all dependencies also deletes the lockfile
    """
    pip_compile.toml_doc["project"]["dependencies"] = []
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert updated_environment.dependencies == []
    assert updated_environment.lockfile_up_to_date is False
    updated_environment.create()
    updated_environment.sync_dependencies()
    assert updated_environment.lockfile_up_to_date is True
    assert (pip_compile.isolation / ".venv" / "hatch-pip-compile").exists()
    assert updated_environment.dependencies == []
    assert updated_environment.piptools_lock_file.exists() is False


def test_create_constraint_environment(pip_compile: PipCompileFixture) -> None:
    """
    Syncing an environment with a constraint env also syncs the constraint env
    """
    default_lockfile_contents = pip_compile.default_environment.piptools_lock_file.read_text()
    pip_compile.toml_doc["project"]["dependencies"] = ["requests"]
    pip_compile.update_pyproject()
    test_environment = pip_compile.reload_environment("test")
    assert (  # this is the call that updates the constraint lockfile
        test_environment.lockfile_up_to_date is False
    )
    new_lockfile_contents = pip_compile.default_environment.piptools_lock_file.read_text()
    assert new_lockfile_contents != default_lockfile_contents
