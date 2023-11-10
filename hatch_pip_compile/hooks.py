"""
Hatch Plugin Registration
"""

from hatchling.plugin import hookimpl

from hatch_pip_compile.plugin import PipCompileEnvironment


@hookimpl
def hatch_register_environment():
    return PipCompileEnvironment
