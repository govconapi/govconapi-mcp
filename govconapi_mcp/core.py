"""Shared infrastructure for every tool module: the FastMCP instance, the HTTP
client, and the one `_get()` helper every tool calls.

Tool modules live in `tools/`, one file per lifecycle stage (Market Research,
Opportunity Discovery, Capture & Teaming, ...), matching the structure in
PLANNING.md. Each does `from ..core import mcp, _get` and
registers its tools onto this ONE shared `mcp` instance via `@mcp.tool()`, an MCP client connects to one server process, so there is one instance, but
the *definitions* are split across files by stage, not jammed into one file.
"""
from __future__ import annotations

import os

import httpx
from mcp.server.fastmcp import FastMCP

from . import __version__

BASE_URL = os.environ.get("GOVCONAPI_BASE", "https://govconapi.com")
API_KEY = os.environ.get("GOVCONAPI_KEY")
TIMEOUT = 30.0

# The version is read once, from installed metadata, in __init__ (a hardcoded copy drifted twice).
USER_AGENT = f"govconapi-mcp/{__version__}"

mcp = FastMCP("govconapi")


def _client() -> httpx.AsyncClient:
    if not API_KEY:
        raise RuntimeError(
            "GOVCONAPI_KEY environment variable is not set. "
            "Get a free trial key at https://govconapi.com and add it to your "
            "MCP client configuration."
        )
    return httpx.AsyncClient(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": USER_AGENT,
        },
        timeout=TIMEOUT,
    )


def _drop_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None and v != ""}


async def _get(path: str, params: dict | None = None) -> dict:
    """Issue a GET request and return parsed JSON, raising friendly errors."""
    async with _client() as client:
        try:
            r = await client.get(path, params=_drop_none(params or {}))
        except httpx.TimeoutException:
            raise RuntimeError(f"GovCon API timed out after {TIMEOUT}s.")
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error reaching GovCon API: {e}")

    if r.status_code == 401:
        raise RuntimeError(
            "Invalid API key. Check GOVCONAPI_KEY in your MCP config. "
            "Get a key at https://govconapi.com."
        )
    if r.status_code == 402:
        try:
            detail = r.json().get("detail", "Payment required.")
        except Exception:
            detail = "Payment required."
        raise RuntimeError(detail)
    if r.status_code == 429:
        raise RuntimeError("Rate limit exceeded. Try again in a moment.")
    if r.status_code == 400:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"Bad request: {detail}")
    if r.status_code >= 500:
        raise RuntimeError(f"GovCon API error {r.status_code}. Please retry.")
    if r.status_code == 404:
        try:
            detail = r.json().get("detail", "Not found")
        except Exception:
            detail = "Not found"
        raise RuntimeError(f"Not found: {detail}")

    return r.json()
