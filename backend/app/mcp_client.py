"""stdio MCP client used by the FastAPI layer.

Set DRAWING2CAD_MCP_DOCKER=1 to run the MCP server inside the restricted
Docker container built from mcp_server/Dockerfile.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .schemas import PartSpec

BACKEND_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BACKEND_DIR / "outputs"


def _server_parameters() -> StdioServerParameters:
    if os.getenv("DRAWING2CAD_MCP_DOCKER", "").lower() in {"1", "true", "yes"}:
        output_path = str(OUTPUT_DIR.resolve())
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "--rm", "-i",
                "--network", "none",
                "--read-only",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
                "--memory=2g",
                "--cpus=2",
                "--pids-limit=128",
                "-v", f"{output_path}:/app/backend/outputs",
                "drawing2cad-mcp:local",
            ],
            env=None,
        )
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        env=None,
        cwd=str(BACKEND_DIR),
    )


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
    """Build a part exclusively by calling the MCP create_part tool."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with stdio_client(_server_parameters()) as (read_stream, write_stream):
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
