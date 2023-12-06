"""
Testing the `lock` module
"""


from packaging.requirements import Requirement
from packaging.version import Version

from hatch_pip_compile.plugin import PipCompileEnvironment


def test_lockfile_python_version(
    default_environment: PipCompileEnvironment,
    test_environment: PipCompileEnvironment,
):
    """
    Test the expected Python version from the lockfiles
    """
    assert default_environment.piptools_lock.lock_file_version == Version("3.11")
    assert test_environment.piptools_lock.lock_file_version == Version("3.11")


def test_lockfile_dependencies(
    default_environment: PipCompileEnvironment,
    test_environment: PipCompileEnvironment,
):
    """
    Test the expected dependencies from reading the lockfiles
    """
    assert set(default_environment.piptools_lock.read_requirements()) == {Requirement("hatch")}
    assert set(test_environment.piptools_lock.read_requirements()) == {
        Requirement("pytest"),
        Requirement("pytest-cov"),
        Requirement("hatch"),
    }


def test_compare_requirements_match(default_environment: PipCompileEnvironment):
    """
    Test the `compare_requirements` method with a match
    """
    default_check = default_environment.piptools_lock.compare_requirements(
        requirements=[Requirement("hatch")],
    )
    assert default_check is True


def test_compare_requirements_mismatch(test_environment: PipCompileEnvironment):
    """
    Test the `compare_requirements` method with a mismatch
    """
    test_check = test_environment.piptools_lock.compare_requirements(
        requirements=[Requirement("hatch")],
    )
    assert test_check is False
