"""Compliance screening, used pre-award (screening a teammate/sub before you bid) and
post-award (ongoing monitoring), so it isn't filed under one lifecycle stage."""
from __future__ import annotations

import json
from typing import Optional

from ..core import mcp, _get
from mcp.types import ToolAnnotations


@mcp.tool(title="Check Exclusions for a Vendor", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def check_exclusion(
    name: Optional[str] = None,
    uei: Optional[str] = None,
    cage_code: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Check the SAM.gov exclusions list (debarred / suspended entities).

    Use this before subcontracting or teaming, and again periodically post-award to
    catch a teammate getting excluded mid-performance. Provide at least one of:
    - name: company or individual name (partial match)
    - uei: Unique Entity ID (same identifier search_companies/search_entities return)
    - cage_code: CAGE code

    Returns matching exclusion records with the reason, agency, and dates.
    """
    if not (name or uei or cage_code):
        raise RuntimeError("Provide at least one of: name, uei, cage_code")
    params = {"name": name, "uei": uei, "cage_code": cage_code, "limit": limit}
    data = await _get("/api/v1/exclusions/search", params)
    return json.dumps(data, indent=2, default=str)
