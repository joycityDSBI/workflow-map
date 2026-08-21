"""Fetch page content from Notion API."""
from __future__ import annotations

import re

from notion_client import AsyncClient

from app.config import settings


async def get_page_text(page_id: str) -> str:
    """Fetch a Notion page and return its text content as a plain string."""
    client = AsyncClient(auth=settings.NOTION_TOKEN)
    blocks = await _fetch_blocks(client, page_id)
    return _blocks_to_text(blocks)


async def _fetch_blocks(client: AsyncClient, block_id: str) -> list:
    """Fetch all blocks for a page (handles pagination)."""
    blocks = []
    cursor = None
    while True:
        kwargs: dict = {"block_id": block_id}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = await client.blocks.children.list(**kwargs)
        blocks.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response["next_cursor"]
    return blocks


def _blocks_to_text(blocks: list) -> str:
    """Convert Notion blocks to plain text."""
    lines = []
    for block in blocks:
        btype = block.get("type", "")
        rich_text = block.get(btype, {}).get("rich_text", [])
        text = "".join(rt.get("plain_text", "") for rt in rich_text)
        if text.strip():
            lines.append(text)
    return "\n".join(lines)


def extract_page_id(ref: str) -> str:
    """Extract a clean Notion page ID from a URL or raw ID string.

    Strips hyphens, takes the last 32 hex characters, and reformats
    into the standard 8-4-4-4-12 UUID form.
    """
    # Remove hyphens and extract last 32 hex characters
    clean = re.sub(r"[^a-f0-9]", "", ref.lower())
    if len(clean) >= 32:
        raw = clean[-32:]
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    return ref  # return as-is if can't parse
