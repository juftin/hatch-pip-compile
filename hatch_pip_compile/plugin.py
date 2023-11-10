"""
hatch-pip-compile plugin
"""

from __future__ import annotations

import pathlib
import tempfile
from typing import Any, ClassVar

from hatch.env.virtual import VirtualEnvironment
from pip._internal.req import InstallRequirement
from piptools._compat import parse_requirements
from piptools.cache import DependencyCache
from piptools.locations import CACHE_DIR
from piptools.repositories import PyPIRepository
from piptools.resolver import BacktrackingResolver
from piptools.writer import OutputWriter


class DummyContext:
    """
    Dummy Context for Click
    """

    params: ClassVar[dict[str, Any]] = {}


class PipCompileEnvironment(VirtualEnvironment):
    """
    Virtual Environment supported by pip-compile
    """

    PLUGIN_NAME = "pip-compile"

    def _get_piptools_repo(self) -> PyPIRepository:
        """
        Get a pip-tools PyPIRepository instance
        """
        return PyPIRepository(pip_args=[], cache_dir=CACHE_DIR)

    def _get_piptools_requirements(self, repository: PyPIRepository) -> list[InstallRequirement]:
        """
        Generate Requirements
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements_file = pathlib.Path(temp_dir) / "requirements.in"
            requirements_file.write_text("\n".join(self.dependencies))
            requirements = list(
                parse_requirements(
                    filename=str(requirements_file),
                    session=repository.session,
                    finder=repository.finder,
                    options=repository.options,
                )
            )
        return requirements

    def _get_piptools_resolver(
        self, repository: PyPIRepository, requirements: list[InstallRequirement]
    ) -> BacktrackingResolver:
        """
        Get a pip-tools BacktrackingResolver instance
        """
        return BacktrackingResolver(
            constraints=requirements,
            existing_constraints={},
            repository=repository,
            prereleases=False,
            cache=DependencyCache(CACHE_DIR),
            clear_caches=False,
            allow_unsafe=False,
            unsafe_packages=None,
        )

    def _get_piptools_results(
        self, resolver: BacktrackingResolver
    ) -> tuple[set[InstallRequirement], dict[InstallRequirement, set[str]]]:
        """
        Fetch pip-tools results
        """
        results = resolver.resolve(max_rounds=10)
        hashes = resolver.resolve_hashes(results)
        return results, hashes

    def _write_piptools_results(
        self,
        repository: PyPIRepository,
        results: set[InstallRequirement],
        hashes: dict[InstallRequirement, set[str]],
        resolver: BacktrackingResolver,
    ) -> None:
        """
        Write pip-tools results to requirements.txt
        """
        output_file = self.root / "requirements.txt"
        writer = OutputWriter(
            dst_file=output_file.open("wb"),
            click_ctx=DummyContext(),  # type: ignore
            dry_run=False,
            emit_header=True,
            emit_index_url=False,
            emit_trusted_host=False,
            annotate=False,
            annotation_style="split",
            strip_extras=True,
            generate_hashes=True,
            default_index_url=repository.DEFAULT_INDEX_URL,
            index_urls=repository.finder.index_urls,
            trusted_hosts=repository.finder.trusted_hosts,
            format_control=repository.finder.format_control,
            linesep="\n",
            allow_unsafe=False,
            find_links=repository.finder.find_links,
            emit_find_links=False,
            emit_options=False,
        )
        writer.write(
            results=results,
            unsafe_packages=resolver.unsafe_packages,
            unsafe_requirements=resolver.unsafe_constraints,
            markers={},
            hashes=hashes,
        )

    def _pip_compile(self) -> None:
        """
        Compile requirements.txt
        """
        repository = self._get_piptools_repo()
        requirements = self._get_piptools_requirements(repository=repository)
        resolver = self._get_piptools_resolver(repository=repository, requirements=requirements)
        results, hashes = self._get_piptools_results(resolver=resolver)
        self._write_piptools_results(
            repository=repository, results=results, hashes=hashes, resolver=resolver
        )

    def install_project(self):
        msg = "Project must be installed in dev mode in pip-compile environments."
        raise NotImplementedError(msg)

    def _pip_install_piptools(self) -> None:
        """
        Install pip-tools
        """
        output_file = self.root / "requirements.txt"
        cmd = [
            "python",
            "-u",
            "-m",
            "pip",
            "install",
            "-r",
            str(output_file),
        ]
        self.platform.check_command(cmd)

    def install_project_dev_mode(self):
        """
        Install the project the first time in dev mode
        """
        with self.safe_activation():
            self._pip_compile()
            self._pip_install_piptools()

    def dependencies_in_sync(self):
        """
        Always return False to force sync_dependencies
        """
        return False

    def sync_dependencies(self):
        """
        Sync dependencies
        """
        with self.safe_activation():
            self._pip_compile()
            self._pip_install_piptools()
