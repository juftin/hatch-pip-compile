"""
Hatch Plugin Registration
"""

from typing import Type

from hatchling.plugin import hookimpl

from hatch_pip_compile.plugin import PipCompileEnvironment


@hookimpl
def hatch_register_environment() -> Type[PipCompileEnvironment]:
    """
    Register the PipCompileEnvironment plugin with Hatch
    """
    return PipCompileEnvironment
