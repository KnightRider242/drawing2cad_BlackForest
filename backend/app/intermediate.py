"""Intermediate representation for drawing interpretation.

The VLM/OCR stage should populate this schema. Values inferred from geometry
must carry evidence and review metadata rather than being presented as explicit
drawing dimensions.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class DimensionEvidence(BaseModel):
    value: float
    source: Literal["explicit_dimension", "inferred_from_geometry", "default", "unknown"]
    evidence: str | None = None
    confidence: float = Field(ge=0, le=1)
    reason: str | None = None
    requires_review: bool = False

    @model_validator(mode="after")
    def inferred_values_require_review(self):
        if self.source != "explicit_dimension":
            self.requires_review = True
            if not self.reason:
                self.reason = "Value is not explicitly dimensioned in the drawing."
        if self.confidence < 0.75:
            self.requires_review = True
        return self


class FeatureDescription(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    type: Literal[
        "rectangular_prism",
        "through_hole",
        "pocket",
        "extrusion",
        "circle",
        "unknown",
    ]
    parameters: dict[str, Any]
    dimensions: dict[str, DimensionEvidence] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)
    requires_review: bool = False


class PartDescription(BaseModel):
    part_id: str = Field(min_length=1, max_length=64)
    units: Literal["mm"] = "mm"
    features: list[FeatureDescription] = Field(min_length=1)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    review_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def propagate_review_flags(self):
        for feature in self.features:
            if feature.requires_review or feature.confidence < 0.75:
                self.review_flags.append(
                    f"Feature '{feature.id}' needs review (confidence={feature.confidence:.2f})."
                )
            for name, dimension in feature.dimensions.items():
                if dimension.requires_review:
                    self.review_flags.append(
                        f"Dimension '{feature.id}.{name}' requires review: {dimension.reason or dimension.source}."
                    )
        # Keep the result deterministic if the same issue is reported twice.
        self.review_flags = list(dict.fromkeys(self.review_flags))
        return self
