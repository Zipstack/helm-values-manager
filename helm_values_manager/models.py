from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


ValueType = Literal["string", "number", "boolean", "array", "object"]


class SchemaValue(BaseModel):
    key: str = Field(..., description="Unique identifier for the value")
    path: str = Field(..., description="Dot-separated path in YAML structure")
    description: str = Field(..., description="Human-readable description")
    type: ValueType = Field(..., description="Data type of the value")
    required: bool = Field(True, description="Whether this value is required")
    default: Optional[Any] = Field(None, description="Default value if not provided")
    sensitive: bool = Field(False, description="Whether this value contains sensitive data")


class Schema(BaseModel):
    version: str = Field(default="1.0", description="Schema version")
    values: list[SchemaValue] = Field(default_factory=list, description="List of value definitions")