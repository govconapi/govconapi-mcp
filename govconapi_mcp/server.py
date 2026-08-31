"""GovCon API MCP server, entry point.

Exposes federal procurement data (opportunities, contracts, companies, entities,
market intelligence, and more) as MCP tools, organized by GovCon lifecycle stage
(see PLANNING.md), so an AI client can build its own workflow across them
instead of us prescribing one.

The FastMCP instance and shared HTTP helper live in `core.py`. The actual tool
definitions live in `tools/`, one file per lifecycle stage, importing `tools`
registers every tool onto the one shared instance via `@mcp.tool()`.

Configuration: set GOVCONAPI_KEY in your client's MCP config (see README).
Get a free trial key at https://govconapi.com.
"""
from __future__ import annotations

from .core import mcp
from . import tools  # noqa: F401, import side-effect registers every @mcp.tool()

__all__ = ["mcp", "main"]


def main() -> None:
    """Entry point, runs the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
