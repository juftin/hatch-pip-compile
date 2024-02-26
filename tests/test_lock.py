"""
Testing the `lock` module
"""
from textwrap import dedent

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
    assert set(pip_compile.default_environment.piptools_lock.read_header_requirements()) == {
        Requirement("hatch")
    }
    assert set(pip_compile.test_environment.piptools_lock.read_header_requirements()) == {
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


def test_read_lock_requirements(pip_compile: PipCompileFixture) -> None:
    """
    Test the `read_lock_requirements` method
    """
    linting_env = pip_compile.reload_environment("lint")
    requirements = linting_env.piptools_lock.read_lock_requirements()
    string_requirements = set(map(str, requirements))
    assert string_requirements == {
        "mypy==1.7.1",
        "mypy-extensions==1.0.0",
        "ruff==0.1.6",
        "typing-extensions==4.8.0",
    }


def test_replace_temporary_lockfile_windows(pip_compile: PipCompileFixture) -> None:
    """
    Regex Replace Temporary File Path: Windows
    """
    lock_raw = r"""
    httpx==0.22.0
        # via -r C:\Users\xxx\AppData\Local\Temp\tmp_kn984om\default.in
    """
    lock_body = dedent(lock_raw).strip()
    cleaned_text = pip_compile.default_environment.piptools_lock.replace_temporary_lockfile(
        lock_body
    )
    expected_raw = r"""
    httpx==0.22.0
        # via hatch.envs.default
    """
    assert cleaned_text == dedent(expected_raw).strip()


def test_replace_temporary_lockfile_unix(pip_compile: PipCompileFixture) -> None:
    """
    Regex Replace Temporary File Path: Unix
    """
    lock_raw = r"""
    httpx==0.22.0
        # via -r /tmp/tmp_kn984om/default.in
    """
    lock_body = dedent(lock_raw).strip()
    cleaned_text = pip_compile.default_environment.piptools_lock.replace_temporary_lockfile(
        lock_body
    )
    expected_raw = r"""
    httpx==0.22.0
        # via hatch.envs.default
    """
    assert cleaned_text == dedent(expected_raw).strip()
