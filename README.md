# Drawing2CAD — BlackForestHackathon

AI-assisted conversion of 2D technical engineering drawings into validated 3D CAD models.

## Project status

This repository starts with a deterministic CAD baseline. The first milestone is to construct a parameterized part, validate the solid, export a STEP file, and verify that it can be imported again. Drawing recognition, AI interpretation, MCP integration, and sandbox hardening are planned next.

## Architecture

- **Frontend:** React + TypeScript + Vite
- **Backend:** Python + FastAPI
- **CAD kernel:** CadQuery / OpenCascade
- **Drawing intelligence (planned):** OpenCV, OCR, optional local VLM
- **CAD tool interface (planned):** Local MCP server with structured parameters
- **Output:** STEP file and machine-readable validation report

The AI layer will interpret drawings into a structured part description. Deterministic CAD tools will build and validate geometry rather than relying on an AI-generated mesh.

## Repository layout

```text
backend/
  app/
    main.py
    schemas.py
    cad_builder.py
  requirements.txt
frontend/
  src/
    App.tsx
    main.tsx
    style.css
  package.json
  index.html
  tsconfig.json
  vite.config.ts
```

## Requirements

- Linux
- Python 3.11 recommended
- Node.js 20+
- CadQuery installed in a compatible Python environment

## Run locally

### Backend

Install CadQuery in a suitable environment first, then:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API docs are available at `http://127.0.0.1:8000/docs`.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Use **Build & validate STEP** to generate a demo plate with two holes. This tests the CAD pipeline only; it does not yet extract geometry from an uploaded drawing.

## API example

`POST /api/build`:

```json
{
  "name": "demo_plate",
  "length_mm": 80,
  "width_mm": 40,
  "thickness_mm": 8,
  "holes": [
    { "x_mm": -20, "y_mm": 0, "diameter_mm": 6 },
    { "x_mm": 20, "y_mm": 0, "diameter_mm": 6 }
  ]
}
```

The response includes solid validity, overall dimension checks, STEP re-import status, and review flags.

## Planned milestones

1. Verify local CAD build and STEP export.
2. Inspect the provided challenge drawings and select three representative parts.
3. Extract drawing features and dimension text using image processing and OCR.
4. Produce an intermediate JSON representation with evidence, confidence, and review flags.
5. Expose CAD operations as structured tools through a local MCP server.
6. Execute model generation in a restricted sandbox with no network access.
7. Validate three sample parts and document uncertain or assumed dimensions.

## Important limitations

- The current demo geometry is manually parameterized, not inferred from a drawing.
- The initial validation checks solid validity, overall bounding dimensions, and STEP re-import. It is not a complete mechanical-design verification system.
- Do not run untrusted model scripts directly on the host. Sandboxing is a required future milestone.

## License

License to be selected by the project owner.
