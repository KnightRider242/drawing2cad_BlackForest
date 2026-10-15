from pathlib import Path
import cadquery as cq
from .schemas import PartSpec


def build_and_export(spec: PartSpec, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    step_path = output_dir / f"{spec.name}.step"

    model = cq.Workplane("XY").box(
        spec.length_mm,
        spec.width_mm,
        spec.thickness_mm,
        centered=(True, True, False),
    )

    for hole in spec.holes:
        model = (
            model.faces(">Z")
            .workplane()
            .pushPoints([(hole.x_mm, hole.y_mm)])
            .hole(hole.diameter_mm)
        )

    solids = model.solids().vals()
    if len(solids) != 1:
        raise ValueError(f"Expected one solid, found {len(solids)}.")

    solid = solids[0]
    if not solid.isValid():
        raise ValueError("CAD kernel reports the solid is invalid.")

    bb = solid.BoundingBox()
    measured = {
        "length_mm": round(bb.xlen, 4),
        "width_mm": round(bb.ylen, 4),
        "thickness_mm": round(bb.zlen, 4),
    }
    expected = {
        "length_mm": spec.length_mm,
        "width_mm": spec.width_mm,
        "thickness_mm": spec.thickness_mm,
    }
    dimension_checks = {
        key: {
            "expected_mm": round(value, 4),
            "measured_mm": measured[key],
            "pass": abs(measured[key] - value) <= 0.01,
        }
        for key, value in expected.items()
    }

    cq.exporters.export(model, str(step_path), exportType="STEP")

    imported = cq.importers.importStep(str(step_path))
    imported_solids = imported.solids().vals()
    reimport_ok = bool(imported_solids) and all(s.isValid() for s in imported_solids)
    if not reimport_ok:
        raise ValueError("STEP re-import did not contain valid solids.")

    return {
        "name": spec.name,
        "step_file": str(step_path),
        "solid_count": len(solids),
        "solid_valid": solid.isValid(),
        "dimensions": measured,
        "dimension_checks": dimension_checks,
        "step_reimport_ok": reimport_ok,
        "review_flags": [],
    }
