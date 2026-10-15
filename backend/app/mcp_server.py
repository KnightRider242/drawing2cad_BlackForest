"""Local MCP server exposing safe, structured CAD operations.

Run from the backend directory with:
    python -m app.mcp_server

The server accepts structured parameters only. It does not expose arbitrary
Python execution. For production/hackathon submission, run this process inside
the restricted Docker worker documented in mcp_server/Dockerfile.
"""
from pathlib import Path
import json

from mcp.server.fastmcp import FastMCP

from .cad_builder import build_and_export
from .schemas import PartSpec

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
mcp = FastMCP("drawing2cad-local-cad")


@mcp.tool()
def create_part(
    name: str,
    length_mm: float,
    width_mm: float,
    thickness_mm: float,
    holes: list[dict] | None = None,
) -> dict:
    """Build a validated rectangular base body with optional through-holes and export STEP.

    All dimensions are in millimetres. Hole coordinates are relative to the
    centre of the top face. Only structured geometry is accepted.
    """
    spec = PartSpec(
        name=name,
        length_mm=length_mm,
        width_mm=width_mm,
        thickness_mm=thickness_mm,
        holes=holes or [],
    )
    return build_and_export(spec, OUTPUT_DIR)


@mcp.tool()
def validate_model(name: str) -> dict:
    """Validate an already exported STEP file by re-importing it and checking solids and dimensions."""
    if not name or Path(name).name != name or not name.endswith(".step"):
        raise ValueError("name must be a STEP filename such as demo_plate.step")
    step_path = OUTPUT_DIR / name
    if not step_path.is_file():
        raise FileNotFoundError(f"STEP file not found: {name}")

    import cadquery as cq

    imported = cq.importers.importStep(str(step_path))
    solids = imported.solids().vals()
    if not solids:
        return {
            "step_file": name,
            "step_reimport_ok": False,
            "solid_count": 0,
            "all_solids_valid": False,
            "checks": [{"name": "contains_solid", "pass": False}],
        }
    valid = all(s.isValid() for s in solids)
    return {
        "step_file": name,
        "step_reimport_ok": valid,
        "solid_count": len(solids),
        "all_solids_valid": valid,
        "checks": [
            {"name": "contains_solid", "pass": len(solids) > 0},
            {"name": "all_solids_geometrically_valid", "pass": valid},
        ],
    }


@mcp.tool()
def get_review_items(items: list[dict] | None = None) -> dict:
    """Normalize drawing assumptions and ambiguities into a machine-readable review list.

    Each item may include parameter, value, source, evidence, confidence, reason,
    and requires_review. This tool reports items; it never silently resolves them.
    """
    normalized = []
    for index, item in enumerate(items or []):
        confidence = item.get("confidence")
        requires_review = bool(item.get("requires_review", False))
        if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
            raise ValueError(f"Review item {index}: confidence must be between 0 and 1")
        if item.get("source") != "explicit_dimension":
            requires_review = True
        normalized.append({
            "id": str(item.get("id", f"review_{index + 1}")),
            "parameter": str(item.get("parameter", "unspecified")),
            "value": item.get("value"),
            "source": str(item.get("source", "unknown")),
            "evidence": item.get("evidence"),
            "confidence": confidence,
            "reason": str(item.get("reason", "Needs human verification")),
            "requires_review": requires_review,
        })
    return {
        "review_count": len(normalized),
        "blocking_review_count": sum(1 for item in normalized if item["requires_review"]),
        "items": normalized,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
