"""Stable application and MCP-tool error definitions."""


class ChurnMcpError(Exception):
    """Base class for errors that can be returned safely to an MCP client."""


class DatasetUnavailableError(ChurnMcpError):
    """The local analytic snapshot has not been bootstrapped."""


class DatasetContractError(ChurnMcpError):
    """The local snapshot cannot support the documented analytic contract."""
