import json
from pathlib import Path
from typing import Optional

from helm_values_manager.models import Schema


def load_schema(schema_path: str = "schema.json") -> Optional[Schema]:
    """Load schema from JSON file."""
    path = Path(schema_path)
    if not path.exists():
        return None
    
    with open(path) as f:
        data = json.load(f)
    
    return Schema(**data)


def save_schema(schema: Schema, schema_path: str = "schema.json") -> None:
    """Save schema to JSON file."""
    with open(schema_path, "w") as f:
        json.dump(schema.model_dump(), f, indent=2)


def validate_key_unique(schema: Schema, key: str) -> bool:
    """Check if a key is unique in the schema."""
    return not any(v.key == key for v in schema.values)


def validate_path_format(path: str) -> bool:
    """Validate that path contains only alphanumeric characters and dots."""
    if not path:
        return False
    
    parts = path.split(".")
    return all(part.replace("-", "").replace("_", "").isalnum() for part in parts if part)