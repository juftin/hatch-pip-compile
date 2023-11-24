"""
hatch-pip-compile exceptions
"""


class HatchPipCompileError(Exception):
    """
    Base exception for hatch-pip-compile
    """


class LockFileNotFoundError(HatchPipCompileError, FileNotFoundError):
    """
    A lock file was not found
    """
