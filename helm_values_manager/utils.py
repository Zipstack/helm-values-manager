import json
from pathlib import Path
from typing import Any, Dict, Optional

from helm_values_manager.models import Schema, SecretReference, ValuesFile


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


def get_values_file_path(env: str, values_path: Optional[str] = None) -> str:
    """Get the path to the values file for an environment."""
    if values_path:
        return values_path
    return f"values-{env}.json"


def load_values(env: str, values_path: Optional[str] = None) -> Dict[str, Any]:
    """Load values for an environment."""
    path = Path(get_values_file_path(env, values_path))
    if not path.exists():
        return {}
    
    with open(path) as f:
        data = json.load(f)
    
    return data


def save_values(values: Dict[str, Any], env: str, values_path: Optional[str] = None) -> None:
    """Save values for an environment."""
    path = get_values_file_path(env, values_path)
    with open(path, "w") as f:
        json.dump(values, f, indent=2)


def is_secret_reference(value: Any) -> bool:
    """Check if a value is a secret reference."""
    return (
        isinstance(value, dict) 
        and value.get("type") == "env" 
        and "name" in value
    )