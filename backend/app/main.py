from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .schemas import PartSpec
from .cad_builder import build_and_export

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"

app = FastAPI(title="Drawing2CAD Local API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "drawing2cad-local-api"}


@app.post("/api/build")
def build_part(spec: PartSpec):
    try:
        return build_and_export(spec, OUTPUT_DIR)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/files/{filename}")
def download_step(filename: str):
    if Path(filename).name != filename or not filename.endswith(".step"):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    path = OUTPUT_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="STEP file not found.")
    return FileResponse(path, media_type="application/step", filename=filename)
