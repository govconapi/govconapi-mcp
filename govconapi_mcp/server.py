"""GovCon API MCP server, entry point.

Exposes federal procurement data (opportunities, contracts, companies, entities, market intelligence, and more)
as MCP tools. By default that is six task-shaped tools (`composite.py`: resolve, search, get, market, price,
contact) that reach every capability of the 53 single-purpose tools in `tools/`, one file per lifecycle stage.
GOVCONAPI_TOOLS=all serves the 53 instead.

The FastMCP instance for the 53 and the shared HTTP helper live in `core.py`; importing `tools` registers every
one of them on it via `@mcp.tool()`, and the six call those functions.

Configuration: set GOVCONAPI_KEY in your client's MCP config (see README).
Get a free trial key at https://govconapi.com.
"""
from __future__ import annotations

import os

from .core import mcp
from . import tools  # noqa: F401, import side-effect registers every @mcp.tool()
from .composite import build

__all__ = ["mcp", "main", "build"]


def main() -> None:
    """Entry point, runs the MCP server over stdio.

    Default: the six task-shaped tools (composite.py). GOVCONAPI_TOOLS=all serves the 53 single-purpose tools
    instead, for anyone whose prompts or agents call them by name.
    """
    if os.environ.get("GOVCONAPI_TOOLS", "").strip().lower() == "all":
        mcp.run()
    else:
        build().run()


if __name__ == "__main__":
    main()
