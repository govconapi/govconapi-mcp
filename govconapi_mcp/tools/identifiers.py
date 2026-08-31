"""Cross-cutting helper, bridges the legacy DUNS identifier (still seen in older
records) to the current UEI every other tool uses."""
from __future__ import annotations

import json

from ..core import mcp, _get
from mcp.types import ToolAnnotations


@mcp.tool(title="Resolve Identifier", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def resolve_identifier(identifier: str) -> str:
    """Resolve between legacy DUNS (9 digits, or 13-digit DUNS+4) and current UEI
    (12 alphanumeric), accepts either side, returns both plus the entity name.

    Free tier.

    - identifier: a DUNS or a UEI

    COVERAGE TRUTH: built from FFATA subaward filings since FY2025 where both
    identifiers co-exist (~24K firms indexed). A 404 means "not in this FFATA-derived
    crosswalk," NOT "not in SAM", the official SAM DUNS↔UEI translator is admin-gated
    and not publicly available, so a 404 here is inconclusive, not a negative proof.
    """
    data = await _get(f"/api/v1/identifiers/{identifier}")
    return json.dumps(data, indent=2, default=str)
