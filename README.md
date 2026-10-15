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
- **Intermediate representation:** Pydantic-validated JSON in `backend/app/intermediate.py`
- **CAD tool interface:** local MCP server in `backend/app/mcp_server.py`
- **CAD kernel:** CadQuery / OpenCascade
- **Execution:** local MCP worker process communicating over stdio
- **Output:** STEP file plus validation/review metadata

The `/api/build` route calls the MCP server using MCP stdio. It does not call the CAD builder directly. The MCP server runs locally as a separate process; Docker isolation is intentionally out of scope for the initial prototype and may be added later.

## Repository layout

```text
backend/
  app/
    main.py                 # FastAPI orchestration
    schemas.py              # Structured CAD build request
    intermediate.py         # Drawing-to-CAD JSON schema + review rules
    cad_builder.py          # Deterministic CadQuery geometry/validation
    mcp_server.py           # Structured MCP CAD tools
    mcp_client.py           # FastAPI -> MCP stdio client
  requirements.txt
frontend/
  src/
  package.json
```

## Requirements

Install these tools before setting up the project:

- **Git**
- **Python 3.11 or 3.12, 64-bit**
- **Conda or Miniforge** (recommended to install CadQuery consistently across operating systems)
- **Node.js 20+ and npm**

CadQuery depends on native OpenCascade libraries. We recommend installing it from the `conda-forge` channel rather than trying to install it with pip. Use the same Conda environment for the backend, MCP server and CadQuery.

## Setup

### 1. Clone the repository

Run in Terminal, PowerShell, or your preferred shell:

```bash
git clone https://github.com/KnightRider242/drawing2cad_BlackForest.git
cd drawing2cad_BlackForest
```

### 2. Create the Python environment

These commands are the same on Windows, Linux and macOS if Conda/Miniforge is installed and available in your terminal:

```bash
conda create -n drawing2cad -c conda-forge python=3.11 cadquery -y
conda activate drawing2cad
```

If your Conda installation does not initialize your shell, run `conda init` for your shell, restart the terminal, and activate the environment again. Miniforge is a good alternative if you do not already have Conda.

**Important:** Do not use Python 3.15 for this project unless CadQuery and its OpenCascade dependencies explicitly support it.

### 3. Install backend/API and MCP dependencies

Activate the `drawing2cad` environment first, then run the commands for your operating system.

**Windows (PowerShell):**

```powershell
cd backend
python -m pip install -r requirements.txt
```

**Linux or macOS (Bash/Zsh):**

```bash
cd backend
python -m pip install -r requirements.txt
```

The commands are identical here; the separate sections are shown to make the setup easier to follow. If you are already in the `backend` directory, do not run `cd backend` a second time.

### 4. Start the backend/API

From the repository root, activate the `drawing2cad` environment and run:

**Windows (PowerShell):**

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

**Linux or macOS (Bash/Zsh):**

```bash
cd backend
python -m uvicorn app.main:app --reload
```

The API will be available at:

- API: http://127.0.0.1:8000
- Interactive API docs: http://127.0.0.1:8000/docs

Keep this terminal open while using the application. The API starts the MCP server as a local Python subprocess; you do not need to launch the MCP server separately.

### 5. Install and start the frontend

Open a **second terminal** at the repository root. Install Node.js 20+ first if it is not already installed.

**Windows (PowerShell):**

```powershell
cd frontend
npm install
npm run dev
```

**Linux or macOS (Bash/Zsh):**

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally http://127.0.0.1:5173).

Use **Build & validate STEP** to create a parameterized demo plate. This currently verifies the MCP → CadQuery → STEP validation path; drawing recognition is not yet wired into the UI.

## Quick checks

Before starting the API, verify that CadQuery and MCP are importable in the active environment:

```bash
python -c "import cadquery, mcp; print('CadQuery and MCP OK')"
```

Check Python and Node.js versions:

```bash
python --version
node --version
npm --version
```

If `python` points to the wrong interpreter, activate the `drawing2cad` Conda environment and rerun the checks. On some Linux/macOS installations, `python3` is the usual system command, but after activating the environment, use the environment's `python` executable.

## MCP tools

- **create_part:** build a rectangular base body and optional through-holes from structured parameters, validate it and export STEP.
- **validate_model:** re-import a STEP file and report solid validity.
- **get_review_items:** return assumptions and ambiguous values as a structured review list.

The toolset is intentionally narrow. Arbitrary code execution is not exposed.

## API example

`POST /api/build`:

```json
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
```

`POST /api/description/validate` accepts the intermediate representation and reports whether any feature/dimension needs review before build approval.

## Outputs and validation

Generated STEP files are written to `backend/outputs/`.

Each build reports:
- solid count and geometric validity;
- measured bounding-box dimensions versus requested dimensions;
- individual dimension checks;
- STEP export and re-import status;
- review flags.

A successful STEP re-import alone does not prove that the model matches the drawing. Validation of hole positions/diameters and drawing-derived expectations is being expanded. Always open exported files in a target CAD system (e.g. NX) as part of acceptance testing.

## Troubleshooting

- **CadQuery import fails:** confirm that the `drawing2cad` environment is active and that CadQuery was installed from `conda-forge`.
- **MCP import fails:** run `python -m pip install -r requirements.txt` inside the active environment.
- **Frontend command fails:** confirm Node.js 20+ and npm are installed; run `npm install` from `frontend/`.
- **Port already in use:** stop the other process or configure the app to use a free port.
- **Shell cannot find `conda`:** initialize Conda for the shell or open a terminal configured by your Conda/Miniforge installation.

## Success metric

The acceptance target is at least three provided sample drawings converted into STEP, with all exported files passing the MCP validation pipeline and opening in a CAD application. Every dimension inferred because it is absent from the drawing must be listed with its reason and require review.

## Current limitations / next milestones

1. Integrate a local VLM/OCR pipeline for contours, dimension text and feature recognition.
2. Add provenance to every feature parameter and show review questions in the React UI.
3. Extend the CAD toolset to pockets, extrusions and supported contour profiles.
4. Compare hole sizes/positions and all known feature dimensions, including after STEP re-import.
5. Add optional Docker-based isolation later, after the local pipeline and acceptance tests are stable.
6. Consider STEP AP242 semantic PMI only after the core success metric is met.

## License

License to be selected by the project owner.
