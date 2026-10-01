"""GovCon API MCP server, federal contract data for AI assistants."""
from importlib.metadata import PackageNotFoundError, version

# The version's one home is pyproject.toml; read it from the installed metadata. A hardcoded
# string here said 0.1.0 through the 0.3.1 release. `unknown` only in a never-installed source tree.
try:
    __version__ = version("govconapi-mcp")
except PackageNotFoundError:  # pragma: no cover - source checkout, not an install
    __version__ = "unknown"
