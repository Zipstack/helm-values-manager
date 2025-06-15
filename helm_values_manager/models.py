from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, RootModel


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


class SecretReference(BaseModel):
    type: Literal["env"] = Field("env", description="Secret type (only 'env' supported)")
    name: str = Field(..., description="Environment variable name")


# Type for a value in the values file - can be a regular value or a secret reference
ValueEntry = Union[str, int, float, bool, list, dict, SecretReference]


class ValuesFile(RootModel[dict[str, Any]]):
    """Represents a values file for an environment."""

    root: dict[str, Any] = Field(default_factory=dict)
