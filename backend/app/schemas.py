from pydantic import BaseModel, Field, model_validator


class Hole(BaseModel):
    x_mm: float
    y_mm: float
    diameter_mm: float = Field(gt=0)


class PartSpec(BaseModel):
    name: str = Field(default="part", pattern=r"^[A-Za-z0-9_-]{1,64}$")
    length_mm: float = Field(gt=0, le=2000)
    width_mm: float = Field(gt=0, le=2000)
    thickness_mm: float = Field(gt=0, le=2000)
    holes: list[Hole] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def holes_must_fit_inside_plate(self):
        for hole in self.holes:
            if abs(hole.x_mm) + hole.diameter_mm / 2 > self.length_mm / 2:
                raise ValueError("A hole extends beyond the plate length.")
            if abs(hole.y_mm) + hole.diameter_mm / 2 > self.width_mm / 2:
                raise ValueError("A hole extends beyond the plate width.")
            if hole.diameter_mm >= min(self.length_mm, self.width_mm):
                raise ValueError("Hole diameter is too large for this plate.")
        return self
