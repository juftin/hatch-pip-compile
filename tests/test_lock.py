"""
Testing the `lock` module
"""

from packaging.requirements import Requirement
from packaging.version import Version

from tests.conftest import PipCompileFixture


def test_lockfile_python_version(
    pip_compile: PipCompileFixture,
):
    """
    Test the expected Python version from the lockfiles
    """
    assert pip_compile.default_environment.piptools_lock.lock_file_version == Version("3.11")
    assert pip_compile.test_environment.piptools_lock.lock_file_version == Version("3.11")


def test_lockfile_dependencies(
    pip_compile: PipCompileFixture,
):
    """
    Test the expected dependencies from reading the lockfiles
    """
    assert set(pip_compile.default_environment.piptools_lock.read_requirements()) == {
        Requirement("hatch")
    }
    assert set(pip_compile.test_environment.piptools_lock.read_requirements()) == {
        Requirement("pytest"),
        Requirement("pytest-cov"),
        Requirement("hatch"),
    }


def test_compare_requirements_match(pip_compile: PipCompileFixture):
    """
    Test the `compare_requirements` method with a match
    """
    default_check = pip_compile.default_environment.piptools_lock.compare_requirements(
        requirements=[Requirement("hatch")],
    )
    assert default_check is True


def test_compare_requirements_mismatch(pip_compile: PipCompileFixture):
    """
    Test the `compare_requirements` method with a mismatch
    """
    test_check = pip_compile.test_environment.piptools_lock.compare_requirements(
        requirements=[Requirement("hatch")],
    )
    assert test_check is False
