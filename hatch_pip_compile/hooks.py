"""
Hatch Plugin Registration
"""


from hatchling.plugin import hookimpl

from hatch_pip_compile.plugin import PipCompileEnvironment


@hookimpl
def hatch_register_environment() -> type[PipCompileEnvironment]:
    """
    Register the PipCompileEnvironment plugin with Hatch
    """
    return PipCompileEnvironment
