import json

from typer.testing import CliRunner

from helm_values_manager.cli import app
from helm_values_manager.models import Schema, SchemaValue

runner = CliRunner()


def test_schema_add_command(tmp_path):
    """Test adding a value to schema interactively."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # First create a schema
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        # Add a value with all inputs
        inputs = [
            "database-host",  # key
            "database.host",  # path
            "Database hostname",  # description
            "string",  # type
            "y",  # required
            "n",  # set default?
            "n",  # sensitive?
        ]
        result = runner.invoke(app, ["schema", "add"], input="\n".join(inputs))

        assert result.exit_code == 0
        assert "Added 'database-host' to schema" in result.output

        # Verify the schema was updated
        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        assert len(schema.values) == 1
        value = schema.values[0]
        assert value.key == "database-host"
        assert value.path == "database.host"
        assert value.description == "Database hostname"
        assert value.type == "string"
        assert value.required is True
        assert value.default is None
        assert value.sensitive is False


def test_schema_add_with_default(tmp_path):
    """Test adding a value with a default."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        inputs = [
            "replicas",  # key
            "deployment.replicas",  # path
            "Number of replicas",  # description
            "number",  # type
            "n",  # required
            "y",  # set default?
            "3",  # default value
            "n",  # sensitive?
        ]
        result = runner.invoke(app, ["schema", "add"], input="\n".join(inputs))

        assert result.exit_code == 0

        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        value = schema.values[0]
        assert value.key == "replicas"
        assert value.default == 3
        assert value.required is False


def test_schema_add_duplicate_key(tmp_path):
    """Test that duplicate keys are rejected."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        # Add first value
        inputs = ["test-key", "test.path", "Test", "string", "y", "n", "n"]
        runner.invoke(app, ["schema", "add"], input="\n".join(inputs))

        # Try to add duplicate
        inputs = [
            "test-key",  # duplicate key
            "test-key2",  # retry with different key
            "test.path2",
            "Test 2",
            "string",
            "y",
            "n",
            "n",
        ]
        result = runner.invoke(app, ["schema", "add"], input="\n".join(inputs))

        assert result.exit_code == 0
        assert "already exists" in result.output


def test_schema_list_empty(tmp_path):
    """Test listing values when schema is empty."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        result = runner.invoke(app, ["schema", "list"])

        assert result.exit_code == 0
        assert "No values defined in schema" in result.output


def test_schema_list_with_values(tmp_path):
    """Test listing values."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with values
        schema = Schema(
            values=[
                SchemaValue(
                    key="required-value",
                    path="test.required",
                    description="A required value",
                    type="string",
                    required=True,
                ),
                SchemaValue(
                    key="optional-value",
                    path="test.optional",
                    description="An optional value",
                    type="number",
                    required=False,
                    default=42,
                ),
                SchemaValue(
                    key="secret-value",
                    path="test.secret",
                    description="A secret value",
                    type="string",
                    required=True,
                    sensitive=True,
                ),
            ]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(app, ["schema", "list"])

        assert result.exit_code == 0
        assert "required-value" in result.output
        assert "optional-value" in result.output
        assert "secret-value" in result.output
        assert "🔒" in result.output  # Lock emoji for sensitive


def test_schema_get_command(tmp_path):
    """Test getting details of a specific value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with a value
        schema = Schema(
            values=[
                SchemaValue(
                    key="test-value",
                    path="test.path",
                    description="Test description",
                    type="string",
                    required=True,
                    default="default-value",
                    sensitive=False,
                )
            ]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(app, ["schema", "get", "test-value"])

        assert result.exit_code == 0
        assert "test-value" in result.output
        assert "test.path" in result.output
        assert "Test description" in result.output
        assert "string" in result.output
        assert "True" in result.output  # required
        assert "default-value" in result.output


def test_schema_get_nonexistent(tmp_path):
    """Test getting a value that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        result = runner.invoke(app, ["schema", "get", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output


def test_parse_array_type(tmp_path):
    """Test adding array type values."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        # Test JSON array input
        inputs = [
            "hosts",
            "ingress.hosts",
            "Ingress hosts",
            "array",
            "y",
            "y",  # set default
            '["example.com", "www.example.com"]',  # JSON array
            "n",
        ]
        result = runner.invoke(app, ["schema", "add"], input="\n".join(inputs))

        assert result.exit_code == 0

        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        value = schema.values[0]
        assert value.type == "array"
        assert value.default == ["example.com", "www.example.com"]


def test_parse_object_type(tmp_path):
    """Test adding object type values."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        inputs = [
            "resources",
            "resources",
            "Resource limits",
            "object",
            "n",
            "y",  # set default
            '{"cpu": "100m", "memory": "128Mi"}',  # JSON object
            "n",
        ]
        result = runner.invoke(app, ["schema", "add"], input="\n".join(inputs))

        assert result.exit_code == 0

        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        value = schema.values[0]
        assert value.type == "object"
        assert value.default == {"cpu": "100m", "memory": "128Mi"}


def test_schema_update_command(tmp_path):
    """Test updating a schema value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with a value
        schema = Schema(
            values=[
                SchemaValue(
                    key="test-value",
                    path="test.path",
                    description="Original description",
                    type="string",
                    required=True,
                    sensitive=False,
                )
            ]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Update the value
        inputs = [
            "new.path",  # new path
            "Updated description",  # new description
            "string",  # keep type
            "n",  # not required anymore
            "y",  # set default
            "default-value",  # default value
            "y",  # sensitive
        ]
        result = runner.invoke(app, ["schema", "update", "test-value"], input="\n".join(inputs))

        assert result.exit_code == 0
        assert "Updated 'test-value' in schema" in result.output

        # Verify the updates
        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        value = schema.values[0]
        assert value.path == "new.path"
        assert value.description == "Updated description"
        assert value.required is False
        assert value.default == "default-value"
        assert value.sensitive is True


def test_schema_update_type_change(tmp_path):
    """Test updating a value's type."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with a value that has a default
        schema = Schema(
            values=[
                SchemaValue(
                    key="test-value",
                    path="test.path",
                    description="Test",
                    type="string",
                    required=False,
                    default="string-default",
                )
            ]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Change type and clear default
        inputs = [
            "",  # keep path
            "",  # keep description
            "number",  # change type
            "y",  # clear default due to type change
            "y",  # required
            "n",  # no new default
            "n",  # not sensitive
        ]
        result = runner.invoke(app, ["schema", "update", "test-value"], input="\n".join(inputs))

        assert result.exit_code == 0

        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        value = schema.values[0]
        assert value.type == "number"
        assert value.default is None


def test_schema_update_nonexistent(tmp_path):
    """Test updating a value that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        result = runner.invoke(app, ["schema", "update", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output


def test_schema_remove_command(tmp_path):
    """Test removing a value from schema."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with multiple values
        schema = Schema(
            values=[
                SchemaValue(key="keep-me", path="keep.path", description="Keep", type="string"),
                SchemaValue(
                    key="remove-me", path="remove.path", description="Remove", type="string"
                ),
            ]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Remove with confirmation
        result = runner.invoke(app, ["schema", "remove", "remove-me"], input="y\n")

        assert result.exit_code == 0
        assert "Removed 'remove-me' from schema" in result.output

        # Verify removal
        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        assert len(schema.values) == 1
        assert schema.values[0].key == "keep-me"


def test_schema_remove_with_force(tmp_path):
    """Test removing a value with --force flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with a value
        schema = Schema(
            values=[SchemaValue(key="remove-me", path="path", description="Remove", type="string")]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Remove with force (no confirmation)
        result = runner.invoke(app, ["schema", "remove", "remove-me", "--force"])

        assert result.exit_code == 0
        assert "Removed 'remove-me' from schema" in result.output

        # Verify removal
        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        assert len(schema.values) == 0


def test_schema_remove_cancel(tmp_path):
    """Test cancelling a removal."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with a value
        schema = Schema(
            values=[SchemaValue(key="keep-me", path="path", description="Keep", type="string")]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Cancel removal
        result = runner.invoke(app, ["schema", "remove", "keep-me"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify not removed
        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        assert len(schema.values) == 1


def test_schema_remove_nonexistent(tmp_path):
    """Test removing a value that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(app, ["init"])

        result = runner.invoke(app, ["schema", "remove", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output


def test_schema_update_remove_default(tmp_path):
    """Test removing default value during schema update."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with a value that has a default
        schema = Schema(
            values=[
                SchemaValue(
                    key="replicas",
                    path="deployment.replicas",
                    description="Number of replicas",
                    type="number",
                    required=False,
                    default=3,
                )
            ]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Update and remove default
        inputs = [
            "",  # keep path
            "",  # keep description
            "number",  # keep type
            "n",  # not required
            "3",  # remove default value
            "n",  # not sensitive
        ]
        result = runner.invoke(app, ["schema", "update", "replicas"], input="\n".join(inputs))

        assert result.exit_code == 0
        assert "Default value removed" in result.output

        # Verify default was removed
        with open("schema.json") as f:
            schema = Schema(**json.load(f))

        value = schema.values[0]
        assert value.default is None


def test_schema_update_remove_default_required_warning(tmp_path):
    """Test warning when removing default from required field."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with required value that has default
        schema = Schema(
            values=[
                SchemaValue(
                    key="app-name",
                    path="app.name",
                    description="App name",
                    type="string",
                    required=True,
                    default="myapp",
                )
            ]
        )

        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Try to remove default but cancel due to warning
        inputs = [
            "",  # keep path
            "",  # keep description
            "string",  # keep type
            "y",  # required
            "3",  # remove default
            "n",  # don't continue after warning
            "1",  # keep current default instead
            "n",  # not sensitive
        ]
        result = runner.invoke(app, ["schema", "update", "app-name"], input="\n".join(inputs))

        assert result.exit_code == 0
        assert "This field is required but will have no default" in result.output
