from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .intermediate import PartDescription
from .mcp_client import OUTPUT_DIR, build_via_mcp
from .schemas import PartSpec

app = FastAPI(title="Drawing2CAD Local API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "drawing2cad-local-api",
        "cad_execution": "mcp",
    }


@app.post("/api/build")
async def build_part(spec: PartSpec):
    """Build geometry through the local MCP server, not directly in the API."""
    try:
        return await build_via_mcp(spec)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/description/validate")
def validate_description(description: PartDescription):
    """Validate the intermediate drawing description and return review requirements."""
    review_flags = list(description.review_flags)
    assumptions = []
    for assumption in description.assumptions:
        item = dict(assumption)
        if item.get("source") != "explicit_dimension":
            item["requires_review"] = True
        if item.get("requires_review"):
            assumptions.append(item)
    return {
        "part_id": description.part_id,
        "feature_count": len(description.features),
        "status": "review_required" if review_flags or assumptions else "ready_for_build",
        "review_flags": review_flags,
        "assumptions": assumptions,
        "build_allowed": not review_flags and not assumptions,
    }


@app.get("/api/files/{filename}")
def download_step(filename: str):
    if Path(filename).name != filename or not filename.endswith(".step"):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    path = OUTPUT_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="STEP file not found.")
    return FileResponse(path, media_type="application/step", filename=filename)
