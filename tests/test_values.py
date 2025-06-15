import json

from typer.testing import CliRunner

from helm_values_manager.cli import app
from helm_values_manager.models import Schema, SchemaValue

runner = CliRunner()


def create_test_schema():
    """Create a test schema with various value types."""
    return Schema(
        values=[
            SchemaValue(
                key="app-name",
                path="app.name",
                description="Application name",
                type="string",
                required=True,
            ),
            SchemaValue(
                key="replicas",
                path="deployment.replicas",
                description="Number of replicas",
                type="number",
                required=False,
                default=3,
            ),
            SchemaValue(
                key="enable-debug",
                path="app.debug",
                description="Enable debug mode",
                type="boolean",
                required=False,
                default=False,
            ),
            SchemaValue(
                key="db-password",
                path="database.password",
                description="Database password",
                type="string",
                required=True,
                sensitive=True,
            ),
            SchemaValue(
                key="allowed-hosts",
                path="ingress.hosts",
                description="Allowed hosts",
                type="array",
                required=False,
            ),
        ]
    )


def test_values_set_string(tmp_path):
    """Test setting a string value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(app, ["values", "set", "app-name", "my-app", "--env", "dev"])

        assert result.exit_code == 0
        assert "Set 'app-name' = my-app" in result.output

        # Verify the value was saved
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["app-name"] == "my-app"


def test_values_set_number(tmp_path):
    """Test setting a number value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(app, ["values", "set", "replicas", "5", "--env", "prod"])

        assert result.exit_code == 0
        assert "Set 'replicas'" in result.output
        assert "5" in result.output

        with open("values-prod.json") as f:
            values = json.load(f)
        assert values["replicas"] == 5


def test_values_set_boolean(tmp_path):
    """Test setting a boolean value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(app, ["values", "set", "enable-debug", "true", "--env", "dev"])

        assert result.exit_code == 0
        assert "Set 'enable-debug'" in result.output
        assert "True" in result.output

        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["enable-debug"] is True


def test_values_set_array(tmp_path):
    """Test setting an array value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(
            app, ["values", "set", "allowed-hosts", '["app.com", "www.app.com"]', "--env", "prod"]
        )

        assert result.exit_code == 0
        assert "Set 'allowed-hosts' =" in result.output

        with open("values-prod.json") as f:
            values = json.load(f)
        assert values["allowed-hosts"] == ["app.com", "www.app.com"]


def test_values_set_sensitive_rejected(tmp_path):
    """Test that setting a sensitive value directly is rejected."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(app, ["values", "set", "db-password", "secret123", "--env", "dev"])

        assert result.exit_code == 1
        assert "marked as sensitive" in result.output
        assert "values set-secret" in result.output


def test_values_set_nonexistent_key(tmp_path):
    """Test setting a value for a non-existent key."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(app, ["values", "set", "nonexistent", "value", "--env", "dev"])

        assert result.exit_code == 1
        assert "Key 'nonexistent' not found in schema" in result.output


def test_values_set_secret(tmp_path, monkeypatch):
    """Test setting a secret value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set environment variable
        monkeypatch.setenv("DB_PASSWORD", "secret123")

        result = runner.invoke(
            app, ["values", "set-secret", "db-password", "--env", "prod"], input="1\nDB_PASSWORD\n"
        )

        assert result.exit_code == 0
        assert "Set secret 'db-password'" in result.output
        assert "DB_PASSWORD" in result.output

        with open("values-prod.json") as f:
            values = json.load(f)
        assert values["db-password"] == {"type": "env", "name": "DB_PASSWORD"}


def test_values_set_secret_warning_not_sensitive(tmp_path):
    """Test setting a secret for a non-sensitive value shows warning."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Try to set non-sensitive value as secret, but cancel
        result = runner.invoke(
            app, ["values", "set-secret", "app-name", "--env", "dev"], input="1\nAPP_NAME\nn\n"
        )

        assert result.exit_code == 0
        assert "not marked as sensitive" in result.output


def test_values_set_secret_env_var_not_set(tmp_path):
    """Test warning when environment variable doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(
            app,
            ["values", "set-secret", "db-password", "--env", "dev"],
            input="1\nNONEXISTENT_VAR\n",
        )

        assert result.exit_code == 0
        assert "Environment variable 'NONEXISTENT_VAR' is not set" in result.output


def test_values_get(tmp_path):
    """Test getting a value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create values file
        values = {"app-name": "test-app", "replicas": 3}
        with open("values-dev.json", "w") as f:
            json.dump(values, f)

        result = runner.invoke(app, ["values", "get", "app-name", "--env", "dev"])

        assert result.exit_code == 0
        assert "app-name: test-app" in result.output


def test_values_get_secret(tmp_path):
    """Test getting a secret value (masked)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        values = {"db-password": {"type": "env", "name": "DB_PASSWORD"}}
        with open("values-prod.json", "w") as f:
            json.dump(values, f)

        result = runner.invoke(app, ["values", "get", "db-password", "--env", "prod"])

        assert result.exit_code == 0
        assert "SECRET" in result.output
        assert "DB_PASSWORD" in result.output


def test_values_get_nonexistent(tmp_path):
    """Test getting a non-existent value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create empty values file
        with open("values-dev.json", "w") as f:
            json.dump({}, f)

        result = runner.invoke(app, ["values", "get", "nonexistent", "--env", "dev"])

        assert result.exit_code == 1
        assert "Value 'nonexistent' not set" in result.output


def test_values_list(tmp_path):
    """Test listing values for an environment."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema and values
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        values = {
            "app-name": "my-app",
            "replicas": 5,
            "db-password": {"type": "env", "name": "DB_PASS"},
            "allowed-hosts": ["app.com", "www.app.com"],
        }
        with open("values-prod.json", "w") as f:
            json.dump(values, f)

        result = runner.invoke(app, ["values", "list", "--env", "prod"])

        assert result.exit_code == 0
        assert "Values for environment: prod" in result.output
        assert "app-name" in result.output
        assert "my-app" in result.output
        assert "[SECRET - DB_PASS]" in result.output


def test_values_list_empty(tmp_path):
    """Test listing values when none are set."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["values", "list", "--env", "dev"])

        assert result.exit_code == 0
        assert "No values set for environment 'dev'" in result.output


def test_values_remove(tmp_path):
    """Test removing a value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create values
        values = {"app-name": "test-app", "replicas": 3}
        with open("values-dev.json", "w") as f:
            json.dump(values, f)

        result = runner.invoke(app, ["values", "remove", "replicas", "--env", "dev"], input="y\n")

        assert result.exit_code == 0
        assert "Removed 'replicas' from environment 'dev'" in result.output

        with open("values-dev.json") as f:
            values = json.load(f)
        assert "replicas" not in values
        assert "app-name" in values


def test_values_remove_with_force(tmp_path):
    """Test removing a value with --force."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        values = {"app-name": "test-app"}
        with open("values-dev.json", "w") as f:
            json.dump(values, f)

        result = runner.invoke(app, ["values", "remove", "app-name", "--env", "dev", "--force"])

        assert result.exit_code == 0
        assert "Removed 'app-name'" in result.output


def test_values_remove_cancel(tmp_path):
    """Test cancelling a removal."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        values = {"app-name": "test-app"}
        with open("values-dev.json", "w") as f:
            json.dump(values, f)

        result = runner.invoke(app, ["values", "remove", "app-name", "--env", "dev"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Value should still exist
        with open("values-dev.json") as f:
            values = json.load(f)
        assert "app-name" in values


def test_values_remove_nonexistent(tmp_path):
    """Test removing a non-existent value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open("values-dev.json", "w") as f:
            json.dump({}, f)

        result = runner.invoke(app, ["values", "remove", "nonexistent", "--env", "dev"])

        assert result.exit_code == 1
        assert "Value 'nonexistent' not set" in result.output


def test_values_set_secret_extensible_menu(tmp_path, monkeypatch):
    """Test the extensible secret configuration menu."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set environment variable
        monkeypatch.setenv("DB_PASSWORD", "secret123")

        # Test selecting environment variable option
        result = runner.invoke(
            app, ["values", "set-secret", "db-password", "--env", "dev"], input="1\nDB_PASSWORD\n"
        )

        assert result.exit_code == 0
        assert "Secret configuration types:" in result.output
        assert "Environment variable" in result.output
        assert "Available" in result.output
        assert "Vault secrets" in result.output
        assert "Coming soon" in result.output


def test_values_set_secret_unsupported_type(tmp_path):
    """Test that unsupported secret types are handled gracefully."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # This test would fail since we only allow choice "1" currently
        # But it demonstrates the extensible design for future secret types
        pass


def test_validate_secret_reference():
    """Test secret reference validation."""
    from helm_values_manager.utils import validate_secret_reference

    # Valid env secret
    valid_env = {"type": "env", "name": "DB_PASSWORD"}
    is_valid, error = validate_secret_reference(valid_env)
    assert is_valid
    assert error == ""

    # Invalid - missing name
    invalid_no_name = {"type": "env"}
    is_valid, error = validate_secret_reference(invalid_no_name)
    assert not is_valid
    assert "name is required" in error

    # Invalid - unsupported type
    invalid_type = {"type": "vault", "name": "secret/db"}
    is_valid, error = validate_secret_reference(invalid_type)
    assert not is_valid
    assert "Unsupported secret type: vault" in error

    # Invalid - not a secret reference
    not_secret = "plain-value"
    is_valid, error = validate_secret_reference(not_secret)
    assert not is_valid
    assert "Not a valid secret reference" in error


def test_values_set_existing_value_confirmation(tmp_path):
    """Test confirmation when overwriting existing value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set initial value
        result = runner.invoke(app, ["values", "set", "app-name", "initial-app", "--env", "dev"])
        assert result.exit_code == 0

        # Try to overwrite without force, but cancel
        result = runner.invoke(
            app, ["values", "set", "app-name", "new-app", "--env", "dev"], input="n\n"
        )

        assert result.exit_code == 0
        assert "already set to: initial-app" in result.output
        assert "Value already exists. Overwrite?" in result.output
        assert "Cancelled" in result.output

        # Verify value wasn't changed
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["app-name"] == "initial-app"


def test_values_set_existing_value_overwrite(tmp_path):
    """Test overwriting existing value with confirmation."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set initial value
        result = runner.invoke(app, ["values", "set", "app-name", "initial-app", "--env", "dev"])
        assert result.exit_code == 0

        # Overwrite with confirmation
        result = runner.invoke(
            app, ["values", "set", "app-name", "new-app", "--env", "dev"], input="y\n"
        )

        assert result.exit_code == 0
        assert "already set to: initial-app" in result.output
        assert "Set 'app-name' = new-app" in result.output

        # Verify value was changed
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["app-name"] == "new-app"


def test_values_set_existing_value_force(tmp_path):
    """Test overwriting existing value with --force flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set initial value
        result = runner.invoke(app, ["values", "set", "app-name", "initial-app", "--env", "dev"])
        assert result.exit_code == 0

        # Overwrite with force (no confirmation)
        result = runner.invoke(
            app, ["values", "set", "app-name", "forced-app", "--env", "dev", "--force"]
        )

        assert result.exit_code == 0
        assert "already set" not in result.output  # No confirmation shown
        assert "Set 'app-name' = forced-app" in result.output

        # Verify value was changed
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["app-name"] == "forced-app"


def test_values_set_secret_existing_confirmation(tmp_path, monkeypatch):
    """Test confirmation when overwriting existing secret."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set environment variables
        monkeypatch.setenv("OLD_PASSWORD", "old_secret")
        monkeypatch.setenv("NEW_PASSWORD", "new_secret")

        # Set initial secret
        result = runner.invoke(
            app, ["values", "set-secret", "db-password", "--env", "dev"], input="1\nOLD_PASSWORD\n"
        )
        assert result.exit_code == 0

        # Try to overwrite but cancel
        result = runner.invoke(
            app,
            ["values", "set-secret", "db-password", "--env", "dev"],
            input="1\nNEW_PASSWORD\nn\n",
        )

        assert result.exit_code == 0
        assert "already set as env:OLD_PASSWORD" in result.output
        assert "Overwrite?" in result.output
        assert "Cancelled" in result.output

        # Verify secret wasn't changed
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["db-password"]["name"] == "OLD_PASSWORD"


def test_values_set_secret_existing_overwrite(tmp_path, monkeypatch):
    """Test overwriting existing secret with confirmation."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set environment variables
        monkeypatch.setenv("OLD_PASSWORD", "old_secret")
        monkeypatch.setenv("NEW_PASSWORD", "new_secret")

        # Set initial secret
        result = runner.invoke(
            app, ["values", "set-secret", "db-password", "--env", "dev"], input="1\nOLD_PASSWORD\n"
        )
        assert result.exit_code == 0

        # Overwrite with confirmation
        result = runner.invoke(
            app,
            ["values", "set-secret", "db-password", "--env", "dev"],
            input="1\nNEW_PASSWORD\ny\n",
        )

        assert result.exit_code == 0
        assert "already set as env:OLD_PASSWORD" in result.output
        assert "Set secret 'db-password'" in result.output

        # Verify secret was changed
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["db-password"]["name"] == "NEW_PASSWORD"


def test_values_set_secret_existing_force(tmp_path, monkeypatch):
    """Test overwriting existing secret with --force flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set environment variables
        monkeypatch.setenv("OLD_PASSWORD", "old_secret")
        monkeypatch.setenv("NEW_PASSWORD", "new_secret")

        # Set initial secret
        result = runner.invoke(
            app, ["values", "set-secret", "db-password", "--env", "dev"], input="1\nOLD_PASSWORD\n"
        )
        assert result.exit_code == 0

        # Overwrite with force (no confirmation)
        result = runner.invoke(
            app,
            ["values", "set-secret", "db-password", "--env", "dev", "--force"],
            input="1\nNEW_PASSWORD\n",
        )

        assert result.exit_code == 0
        assert "already set" not in result.output  # No confirmation shown
        assert "Set secret 'db-password'" in result.output

        # Verify secret was changed
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["db-password"]["name"] == "NEW_PASSWORD"


def test_values_set_secret_overwrite_regular_value_warning(tmp_path, monkeypatch):
    """Test warning when overwriting regular value with secret."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Set environment variable
        monkeypatch.setenv("SECRET_PASSWORD", "secret")

        # Set initial regular value (even though it should be secret)
        values = {"db-password": "plain-text-password"}
        with open("values-dev.json", "w") as f:
            json.dump(values, f)

        # Try to overwrite with secret
        result = runner.invoke(
            app,
            ["values", "set-secret", "db-password", "--env", "dev"],
            input="1\nSECRET_PASSWORD\ny\n",
        )

        assert result.exit_code == 0
        assert "currently set to: plain-text-password" in result.output
        assert "This will overwrite a non-secret value with a secret" in result.output

        # Verify it was changed to secret
        with open("values-dev.json") as f:
            values = json.load(f)
        assert values["db-password"]["type"] == "env"
        assert values["db-password"]["name"] == "SECRET_PASSWORD"
