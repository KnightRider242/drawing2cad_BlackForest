# Drawing2CAD — BlackForestHackathon

Local-first prototype for converting 2D engineering drawings into structured feature descriptions and validated 3D CAD models.

## Goal

The AI interprets a drawing; it does **not** generate CAD geometry directly. It produces a structured intermediate representation (JSON) containing features, dimensions, evidence, confidence and review flags. All CAD construction and STEP export go through the local MCP server's structured tools.

The prototype is designed to:
- recognize contours, dimensions, holes and basic geometric features;
- preserve the evidence and source of every dimension;
- flag missing, inferred or ambiguous dimensions for human review;
- build CAD geometry through MCP tools;
- validate solid geometry, dimensions and STEP round-trip imports;
- export STEP files with machine-readable validation/review metadata.

## Architecture

- **Frontend:** React + TypeScript + Vite
- **API/orchestrator:** FastAPI
- **Drawing interpretation:** local VLM and/or OCR/image-processing stage (integration in progress)
- **Intermediate representation:** Pydantic-validated JSON in backend/app/intermediate.py
- **CAD tool interface:** local MCP server in backend/app/mcp_server.py
- **CAD kernel:** CadQuery / OpenCascade
- **Sandbox:** Docker MCP worker with no network, read-only root filesystem, resource limits and a dedicated output mount
- **Output:** STEP file plus validation/review metadata

The /api/build route calls the MCP server using MCP stdio. It does not call the CAD builder directly. For stronger isolation, enable the Docker worker mode below.

## Repository layout

~~~text
backend/
  app/
    main.py                 # FastAPI orchestration
    schemas.py              # Structured CAD build request
    intermediate.py         # Drawing-to-CAD JSON schema + review rules
    cad_builder.py          # Deterministic CadQuery geometry/validation
    mcp_server.py           # Structured MCP CAD tools
    mcp_client.py           # FastAPI -> MCP stdio client
  requirements.txt
mcp_server/
  environment.yml           # Isolated CAD environment
  Dockerfile                # Restricted worker image
frontend/
  src/
  package.json
~~~

## Requirements

- Python 3.11 or 3.12, 64-bit
- Node.js 20+
- CadQuery installed in a compatible environment
- Docker Desktop for isolated MCP worker mode

### Windows: install dependencies

Install CadQuery using Conda-forge in an environment compatible with your installation. For example:

~~~powershell
conda create -n drawing2cad python=3.11 -y
conda activate drawing2cad
conda install -c conda-forge cadquery -y
~~~

Then install the API/MCP packages in that same environment:

~~~powershell
cd backend
python -m pip install -r requirements.txt
~~~

Do not use Python 3.15 for this project unless the CadQuery/OpenCascade packages explicitly support it.

## Run locally

### Backend/API

From the repository root, activate the environment that has CadQuery installed:

~~~powershell
cd backend
python -m uvicorn app.main:app --reload
~~~

API docs: http://127.0.0.1:8000/docs

### Frontend

In another terminal:

~~~powershell
cd frontend
npm install
npm run dev
~~~

Open http://127.0.0.1:5173.

Use **Build & validate STEP** to create a parameterized demo plate. This verifies the MCP → CadQuery → STEP validation path; drawing recognition is not yet wired into the UI.

## Isolated MCP worker (Docker)

Build the worker image from the repository root:

~~~powershell
docker build -f mcp_server/Dockerfile -t drawing2cad-mcp:local .
~~~

Ensure Docker Desktop is running, then set this environment variable in the terminal used to start FastAPI:

~~~powershell
$env:DRAWING2CAD_MCP_DOCKER = "1"
cd backend
python -m uvicorn app.main:app --reload
~~~

With this setting, the API launches the MCP server in a short-lived Docker container for each build. The worker is run with --network none, a read-only root filesystem, a bounded temporary filesystem, CPU/memory/process limits, and only the STEP output directory mounted writable. The host must have the image built before using this mode.

For local development without Docker, leave DRAWING2CAD_MCP_DOCKER unset. The MCP server still runs as a separate local process, but this mode is **not an OS security sandbox**.

## MCP tools

- **create_part:** build a rectangular base body and optional through-holes from structured parameters, validate it and export STEP.
- **validate_model:** re-import a STEP file and report solid validity.
- **get_review_items:** return assumptions and ambiguous values as a structured review list.

The toolset is intentionally narrow. Arbitrary code execution is not exposed.

## API example

POST /api/build:

~~~json
{
  "name": "demo_plate",
  "length_mm": 80,
  "width_mm": 40,
  "thickness_mm": 8,
  "holes": [
    {"x_mm": -20, "y_mm": 0, "diameter_mm": 6},
    {"x_mm": 20, "y_mm": 0, "diameter_mm": 6}
  ]
}
~~~

POST /api/description/validate accepts the intermediate representation and reports whether any feature/dimension needs review before build approval.

## Validation

Each build reports:
- solid count and geometric validity;
- measured bounding-box dimensions versus requested dimensions;
- individual dimension checks;
- STEP export and re-import status;
- review flags.

A successful STEP re-import alone does not prove that the model matches the drawing. Validation of hole positions/diameters and drawing-derived expectations is being expanded. Always open exported files in a target CAD system (e.g. NX) as part of acceptance testing.

## Success metric

The acceptance target is at least three provided sample drawings converted into STEP, with all exported files passing the MCP validation pipeline and opening in a CAD application. Every dimension inferred because it is absent from the drawing must be listed with its reason and require review.

## Current limitations / next milestones

1. Integrate a local VLM/OCR pipeline for contours, dimension text and feature recognition.
2. Add provenance to every feature parameter and show review questions in the React UI.
3. Extend the CAD toolset to pockets, extrusions and supported contour profiles.
4. Compare hole sizes/positions and all known feature dimensions, including after STEP re-import.
5. Run the three sample parts through the Docker sandbox and verify outputs in NX.
6. Consider STEP AP242 semantic PMI only after the core success metric is met.

## License

License to be selected by the project owner.
