# helm-values-manager: LLM Agent Prompt Plan

## Architecture Decisions
1. **Values Files**: Separate per-environment (`values-{env}.json`) with flat structure
2. **Secret Handling**: Resolve to actual values during generation, output to stdout
3. **Defaults**: Apply schema defaults during generation
4. **Error Handling**: Aggregate all validation errors before exit

## Execution Plan

### Phase 1: Core Setup & Initialization ✅
#### Task 1.1: Project Scaffolding ✅
```prompt
Create Python project structure for Helm plugin:
- plugin.yaml: Name "values-manager", points to virtualenv entrypoint
- install.sh: Creates venv, installs from requirements.txt
- requirements.txt: Includes typer==0.9.0, pyyaml==6.0
- main.py: CLI entrypoint using Typer
- src/ directory with:
  • __init__.py
  • schema.py (empty)
  • values.py (empty)
  • generator.py (empty)
  • validator.py (empty)
  • utils.py (empty)
```
**Status**: Completed - Used uv for package management, created proper plugin structure

#### Task 1.2: `init` Command ✅
```prompt
Implement `helm values-manager init`:
1. Check for existing schema.json
2. Prompt for overwrite confirmation if exists
3. Create minimal schema.json: {"version": "1.0", "values": []}
4. Use Typer with clean error handling
5. Support --schema flag for custom path
```
**Status**: Completed - Implemented with --force flag, tests passing

### Phase 2: Schema Management ✅
#### Task 2.1: `schema add` ✅
```prompt
Create interactive `schema add`:
1. Prompt for fields:
   • key (unique, slug format)
   • path (dot-separated YAML path)
   • description
   • type (choice: string/number/boolean/array/object)
   • required (boolean)
   • default (type-aware input)
   • sensitive (boolean)
2. Validate path format (alphanumeric + dots)
3. Append to schema.json
```
**Status**: Completed - Interactive prompts with full validation

#### Task 2.2: Schema Query Commands ✅
```prompt
Implement:
- `schema list`: Tabular output (key, path, type, required)
- `schema get <key>`: Pretty-printed JSON with all fields
- Both support --schema flag
- Handle missing keys gracefully
```
**Status**: Completed - List shows colored status, get shows detailed info

#### Task 2.3: Schema Modification ✅
```prompt
Build:
- `schema update <key>`: Interactive update (pre-fill current values)
- `schema remove <key>`: Confirm removal + check values references
- Prevent removal if key exists in any values file
```
**Status**: Completed - Update preserves values, remove has --force flag

### Phase 3: Values Management ✅
#### Task 3.1: `values set` ✅
```prompt
Implement `values set <key> <value> --env <env>`:
1. Parse <value> based on schema type (JSON for arrays/objects)
2. Reject if key is sensitive (suggest set-secret)
3. Create values-<env>.json if missing
4. Support --values flag for custom path
```
**Status**: Completed - Full type validation and environment isolation

#### Task 3.2: `values set-secret` ✅
```prompt
Create interactive `values set-secret <key> --env <env>`:
1. Validate key is sensitive in schema
2. Prompt for environment variable name
3. Store as {"type": "env", "name": "VAR"}
4. Validate env var exists (warning only)
```
**Status**: Completed - Interactive prompts with env var validation

#### Task 3.3: Values Query/Delete ✅
```prompt
Implement:
- `values get <key> --env <env>`: Print value (mask secrets)
- `values list --env <env>`: Tabular output (key, value_preview)
- `values remove <key> --env <env>`: Remove key with confirmation
```
**Status**: Completed - Rich table output with secret masking

#### Task 3.4: Default Value Removal in Schema Update ✅
```prompt
Enhance `schema update <key>` command to:
1. When editing a schema entry that has a default value:
   - Add "Remove default value" option to interactive menu
2. If selected:
   - Clear the default value from the schema entry
   - Warn if field is required: "Warning: This field is required but has no default"
3. Preserve backward compatibility with existing schema format
```
**Status**: Completed - Option-based menu with warning system

#### Task 3.5: Extensible Secret Configuration ✅
```prompt
Update `values set-secret` command to:
1. Prompt for secret type with options:
   - Environment variable (env) - current MVP
   - [Reserved: vault/aws/azure] - placeholder for future
2. For 'env' type:
   - Prompt for environment variable name
   - Validate env var exists (warning only)
3. Store in values file with type metadata:
   {
     "database-password": {
       "type": "env",
       "name": "PROD_DB_PASSWORD"
     }
   }
4. Add validation to generator:
   - Support only 'env' type for now
   - Error on unsupported types
```
**Status**: Completed - Extensible menu with validation framework

### Phase 4: Core Engine
#### Task 4.1: Validator
```prompt
Create `validate` command:
1. Check schema integrity (required fields, valid types)
2. Validate values:
   • Type matches
   • Required values present
   • Secret structures valid
3. Aggregate all errors before exit
4. Support --env for single environment check
```

#### Task 4.2: Generator
```prompt
Implement `generate --env <env>`:
1. Run validation first (exit on error)
2. Merge process:
   a. Start with schema defaults
   b. Override with values from values-<env>.json
   c. Resolve secrets from environment variables
3. Build nested YAML structure using dot paths
4. Output to stdout as valid YAML
5. Handle missing env vars (error)
```

### Phase 5: CLI Polish
#### Task 5.1: Command Organization
```prompt
Organize commands:
- Main groups: [schema, values, core]
- Global flags:
   • --schema: path to schema.json
   • --values: base path for values files
- Help texts for all commands
```

#### Task 5.2: Error Handling
```prompt
Implement consistent errors:
- Format: "Error: [context] - [specific issue]"
- Validation: List all failures
- Use rich formatting with fallback for non-TTY
- Suggest solutions where possible
```

### Phase 6: Testing & Docs
#### Task 6.1: Unit Tests
```prompt
Write pytest tests for:
- Schema CRUD operations
- Value setting/getting
- Path nesting logic
- Secret resolution
- Validation scenarios
Use temporary files and monkeypatch for env vars
```

#### Task 6.2: Documentation
```prompt
Draft README.md with:
1. Installation: helm plugin install
2. Quickstart: vendor and customer workflows
3. Security best practices
4. Command reference table
5. Troubleshooting common errors
```

## Workflow Sequence
```mermaid
sequenceDiagram
    Vendor->>+Agent: Run Task 1.1
    Agent-->>-Vendor: Project scaffold
    Vendor->>+Agent: Run Task 1.2
    Agent-->>-Vendor: init command
    Vendor->>+Agent: Run Task 2.1
    Agent-->>-Vendor: schema add
    ... continue sequentially ...
    Vendor->>+Agent: Run Task 6.2
    Agent-->>-Vendor: Documentation
```

## Security Notes
- Never store resolved secrets on disk
- Always pipe generate output directly to Helm
- Validate all inputs before processing
- Mask secrets in CLI output
