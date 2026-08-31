# Image for running the GovCon API MCP server (stdio transport). Used by Glama's build and
# security checks, and by anyone who wants to run the client in a container.
#
# Introspection works with no configuration: the API key is read at CALL time inside core._get(),
# not at import, so `tools/list` returns all 53 tool definitions without a key and without network
# access. Actually invoking a tool does need a key, since every tool is a live query against
# https://govconapi.com. Free 14-day trial, no credit card: https://govconapi.com
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir .

# GOVCONAPI_KEY is required to call tools, not to list them.
# GOVCONAPI_BASE is optional and defaults to https://govconapi.com.
ENTRYPOINT ["govconapi-mcp"]
