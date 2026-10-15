"""Small stdio MCP client used by the FastAPI layer."""
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .schemas import PartSpec


def _decode_tool_result(result: Any) -> dict:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    for block in getattr(result, "content", []):
        text = getattr(block, "text", None)
        if text:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
    if getattr(result, "isError", False):
        raise RuntimeError("MCP CAD tool returned an error.")
    raise RuntimeError("MCP CAD tool returned no structured result.")


async def build_via_mcp(spec: PartSpec) -> dict:
    """Start the local MCP server over stdio and call its structured create_part tool."""
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        env=None,
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "create_part",
                arguments={
                    "name": spec.name,
                    "length_mm": spec.length_mm,
                    "width_mm": spec.width_mm,
                    "thickness_mm": spec.thickness_mm,
                    "holes": [hole.model_dump() for hole in spec.holes],
                },
            )
            if getattr(result, "isError", False):
                messages = [
                    getattr(block, "text", "")
                    for block in getattr(result, "content", [])
                ]
                raise RuntimeError("MCP create_part failed: " + " ".join(messages))
            return _decode_tool_result(result)
