"""
Integration Tests

These tests are "integration" tests in that they test the
interaction between the various components of hatch-pip-compile
and external tools (pip-tools / pip).
"""

from typing import Dict, Type

import packaging.requirements
import pytest

from hatch_pip_compile.installer import PluginInstaller
from tests.conftest import PipCompileFixture


@pytest.mark.parametrize("installer", ["pip", "pip-sync"])
def test_new_dependency(
    installer: str, installer_dict: Dict[str, Type[PluginInstaller]], pip_compile: PipCompileFixture
) -> None:
    """
    Test adding a new dependency
    """
    original_requirements = pip_compile.default_environment.piptools_lock.read_requirements()
    assert original_requirements == [packaging.requirements.Requirement("hatch")]
    pip_compile.toml_doc["project"]["dependencies"] = ["requests"]
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = installer
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert isinstance(updated_environment.installer, installer_dict[installer])
    assert updated_environment.dependencies == ["requests"]
    pip_compile.application.prepare_environment(environment=updated_environment)
    assert updated_environment.lockfile_up_to_date is True
    new_lockfile_requirements = pip_compile.default_environment.piptools_lock.read_requirements()
    assert new_lockfile_requirements == [packaging.requirements.Requirement("requests")]


@pytest.mark.parametrize("installer", ["pip", "pip-sync"])
def test_delete_dependencies(
    installer: str, installer_dict: Dict[str, Type[PluginInstaller]], pip_compile: PipCompileFixture
) -> None:
    """
    Test deleting all dependencies also deletes the lockfile
    """
    pip_compile.toml_doc["tool"]["hatch"]["envs"]["default"]["pip-compile-installer"] = installer
    pip_compile.toml_doc["project"]["dependencies"] = []
    pip_compile.update_pyproject()
    updated_environment = pip_compile.reload_environment("default")
    assert isinstance(updated_environment.installer, installer_dict[installer])
    assert updated_environment.dependencies == []
    assert updated_environment.lockfile_up_to_date is False
    pip_compile.application.prepare_environment(environment=updated_environment)
    assert updated_environment.lockfile_up_to_date is True
    assert (pip_compile.isolation / ".venv" / "hatch-pip-compile-test").exists()
    assert updated_environment.dependencies == []
    assert updated_environment.piptools_lock_file.exists() is False


def test_create_constraint_environment(pip_compile: PipCompileFixture) -> None:
    """
    Syncing an environment with a constraint env also syncs the constraint env
    """
    original_requirements = pip_compile.default_environment.piptools_lock.read_requirements()
    assert original_requirements == [packaging.requirements.Requirement("hatch")]
    pip_compile.toml_doc["project"]["dependencies"] = ["requests"]
    pip_compile.update_pyproject()
    test_environment = pip_compile.reload_environment("test")
    pip_compile.application.prepare_environment(environment=test_environment)
    new_lockfile_requirements = pip_compile.default_environment.piptools_lock.read_requirements()
    assert new_lockfile_requirements == [packaging.requirements.Requirement("requests")]
