import json
from pathlib import Path

from typer.testing import CliRunner

from helm_values_manager.cli import app

runner = CliRunner()


def test_init_creates_schema_file(tmp_path):
    """Test that init command creates a schema.json file."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "Created schema.json" in result.output

        # Check that the file was created
        schema_path = Path("schema.json")
        assert schema_path.exists()

        # Check the content of the file
        with open(schema_path) as f:
            schema = json.load(f)

        assert schema == {"values": []}


def test_init_fails_if_schema_exists(tmp_path):
    """Test that init command fails if schema.json already exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create an existing schema.json
        existing_schema = {"values": [{"key": "test"}]}
        with open("schema.json", "w") as f:
            json.dump(existing_schema, f)

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "schema.json already exists" in result.output


def test_init_force_overwrites_existing(tmp_path):
    """Test that init --force overwrites existing schema.json."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create an existing schema.json with some content
        existing_schema = {"values": [{"key": "test"}]}
        with open("schema.json", "w") as f:
            json.dump(existing_schema, f)

        result = runner.invoke(app, ["init", "--force"])

        assert result.exit_code == 0
        assert "Created schema.json" in result.output

        # Check that the file was overwritten
        with open("schema.json") as f:
            schema = json.load(f)

        assert schema == {"values": []}
