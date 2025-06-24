"""
Testing the hatch-pip-compile CLI
"""

from unittest.mock import Mock

import click
import pytest
from click.testing import CliRunner

from hatch_pip_compile import __version__
from hatch_pip_compile.cli import HatchCommandRunner, cli
from tests.conftest import PipCompileFixture


def test_cli_help() -> None:
    """
    Test the CLI with the --help flag
    """
    runner = CliRunner()
    result = runner.invoke(cli=cli, args=["--help"])
    assert result.exit_code == 0


def test_cli_version() -> None:
    """
    Test the CLI with the --version flag
    """
    runner = CliRunner()
    result = runner.invoke(cli=cli, args=["--version"])
    assert result.exit_code == 0
    assert f"hatch-pip-compile, version {__version__}" in result.output


@pytest.mark.parametrize(
    "hatch_version, expected_args",
    [
        (b"Hatch, version 1.7.0", ["hatch", "env", "show", "--json"]),
        (b"Hatch, version 1.12.0", ["hatch", "env", "show", "--json", "--internal"]),
    ],
)
def test_cli_no_args_mocked(
    hatch_version: bytes,
    expected_args: list[str],
    pip_compile: PipCompileFixture,
    subprocess_run: Mock,
) -> None:
    """
    Test the CLI with no arguments - mock the result
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        version_mock = Mock()
        version_mock.stdout = hatch_version
        environment_mock = Mock()
        environment_mock.stdout = b"{}"
        subprocess_run.side_effect = [
            version_mock,
            environment_mock,
        ]
        _ = runner.invoke(cli=cli)
        assert subprocess_run.call_count == 2
        subprocess_run.assert_called_with(args=expected_args, capture_output=True, check=True)


def test_cli_no_args(pip_compile: PipCompileFixture) -> None:
    """
    Test the full CLI with no arguments
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        result = runner.invoke(cli=cli)
        assert result.exit_code == 0
        assert "hatch-pip-compile: Targeting environments: default" in result.output
        assert (
            "hatch-pip-compile: Running `hatch env run --env default -- python --version`"
            in result.output
        )


def test_cli_bad_env(pip_compile: PipCompileFixture) -> None:
    """
    Test the full CLI with a non-existent environment
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        result = runner.invoke(cli=cli, args=["bad_env"])
        assert result.exit_code != 0
        assert "error" in result.output.lower()
        assert (
            "The following environments are not supported or unknown: bad_env. "
            "Supported environments are: default, docs, lint, misc, test"
        ) in result.output


def test_cli_test_env(pip_compile: PipCompileFixture) -> None:
    """
    Test the full CLI with the `test` argument
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        result = runner.invoke(cli=cli, args=["test"])
        assert result.exit_code == 0
        assert "hatch-pip-compile: Targeting environments: test" in result.output
        assert (
            "hatch-pip-compile: Running `hatch env run --env test -- python --version`"
            in result.output
        )


def test_cli_all(pip_compile: PipCompileFixture) -> None:
    """
    Test the full CLI with the `--all` argument
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        result = runner.invoke(cli=cli, args=["--all"])
        assert result.exit_code == 0
        assert (
            "hatch-pip-compile: Targeting environments: default, docs, lint, misc, test"
            in result.output
        )


def test_cli_upgrade(pip_compile: PipCompileFixture) -> None:
    """
    Test the full CLI with the `--upgrade` argument
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        result = runner.invoke(cli=cli, args=["--upgrade"])
        assert result.exit_code == 0
        assert "hatch-pip-compile: Upgrading all dependencies" in result.output


def test_cli_upgrade_packages(pip_compile: PipCompileFixture) -> None:
    """
    Test the full CLI with the `--upgrade-package` argument
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        result = runner.invoke(
            cli=cli, args=["--upgrade-package", "requests", "--upgrade-package", "urllib3"]
        )
        assert result.exit_code == 0
        assert "hatch-pip-compile: Upgrading packages: requests, urllib3" in result.output


def test_cli_upgrade_test(pip_compile: PipCompileFixture) -> None:
    """
    Test the full CLI with the `--upgrade` argument for the `test` environment
    """
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=pip_compile.isolation):
        result = runner.invoke(cli=cli, args=["test", "--upgrade"])
        assert result.exit_code == 0
        assert "hatch-pip-compile: Upgrading all dependencies" in result.output
        assert "hatch-pip-compile: Targeting environments: test" in result.output


def test_command_runner_supported_environments(
    monkeypatch: pytest.MonkeyPatch,
    pip_compile: PipCompileFixture,
) -> None:
    """
    Test the `supported_environments` attribute
    """
    with pip_compile.chdir():
        command_runner = HatchCommandRunner(
            environments=["test"],
            upgrade=True,
            upgrade_packages=[],
        )
        assert command_runner.supported_environments == {"default", "test", "lint", "docs", "misc"}


def test_command_runner_non_supported_environments(
    monkeypatch: pytest.MonkeyPatch,
    pip_compile: PipCompileFixture,
) -> None:
    """
    Test that a bad environment raises a `BadParameter` exception
    """
    with pip_compile.chdir():
        with pytest.raises(
            click.BadParameter,
            match=(
                "The following environments are not supported or unknown: bad_env. "
                "Supported environments are: default, docs, lint, misc, test"
            ),
        ):
            _ = HatchCommandRunner(
                environments=["bad_env"],
                upgrade=True,
                upgrade_packages=[],
            )
