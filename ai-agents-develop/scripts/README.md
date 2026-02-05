# Create Credential

This guide explains how to create credentials using the `create_framework.py` script.

## Overview

The script allows you to create multiple credentials from a YAML or JSON configuration file. Credentials can be of two types:
- **Secret String**: For storing API tokens, secrets, or other string-based credentials
- **Login**: For storing username/password credentials (with optional MFA)

## Prerequisites

1. Set your access token as an environment variable:
   ```bash
   export ALLTRUE_ACCESS_TOKEN="your-token-here"
   ```

   Or use the `--token` argument (see Usage below).

2. Ensure you have the required Python packages installed (requests, pyyaml, python-dotenv).

## Credential Configuration File Format

Create a YAML or JSON file with the following structure:

### YAML Format

```yaml
credentials:
  - credential_name: My-Secret-Token
    credential_value:
      credential_type: Secret String
      secret: "your-secret-value-here"
    notes: "Optional description of this credential"

  - credential_name: My-Login-Credential
    credential_value:
      credential_type: Login
      user_name: "username"
      password: "password"
      mfa: "optional-mfa-code"  # Optional field
    notes: "Optional description"
```

### Supported Credential Types

1. **Secret String** (`credential_type: Secret String` or `Secret String`)
   - Required field: `secret` (string)
   - Use for: API tokens, OAuth tokens, API keys, etc.

2. **Login** (`credential_type: Login`)
   - Required fields: `user_name` (string), `password` (string)
   - Optional field: `mfa` (string)
   - Use for: Username/password authentication

### Example Configuration Files

See `scripts/credential_configs/test_credential_example.yaml` for a template example.

## Usage

### Basic Usage

Create credentials from a configuration file:

```bash
python scripts/create_framework.py --env local --credential-config scripts/credential_configs/test_credential_example.yaml
```

### With Custom Token

```bash
python scripts/create_framework.py --env local --token "your-token" --credential-config path/to/credentials.yaml
```

### Available Environments

- `local` - Local development server (http://localhost:8000)
- `playground` - Playground environment for testing
- `development` - Development environment
- `staging` - Staging environment

### Command-Line Options

- `--env` (required): Target environment (local, playground, development, staging)
- `--credential-config` (required for credential creation): Path to credential configuration file
- `--token`: API access token (or set `ALLTRUE_ACCESS_TOKEN` env var)
- `--force`: Attempt to create credentials even if they already exist (will error if conflict)
- `--no-verify-ssl`: Disable SSL certificate verification
- `--output`: Save created credential UUIDs to a JSON file

### Examples

#### Create credentials in local environment

```bash
python scripts/create_framework.py \
  --env local \
  --credential-config scripts/credential_configs/test_credential.yaml
```

#### Create credentials with force flag (attempts creation even if exists)

```bash
python scripts/create_framework.py \
  --env development \
  --credential-config credentials.yaml \
  --force
```

#### Save results to a file

```bash
python scripts/create_framework.py \
  --env local \
  --credential-config credentials.yaml \
  --output results.json
```

## Behavior

- **Duplicate Handling**: By default, if a credential with the same name already exists, it will be skipped with a warning. Use `--force` to attempt creation anyway (API will error if there's a conflict).

- **Error Handling**: If one credential fails to create, the script continues processing the remaining credentials.

## Output

The script will:
1. Display progress for each credential being created
2. Show success messages with credential UUIDs
3. Report any errors or skipped credentials
4. Optionally save all credential UUIDs to a JSON file (with `--output`)

Example output:
```
Loading credential configuration from credentials.yaml...

🔐 Creating credential: My-Secret-Token
   Type: SECRET_STRING
✅ Credential created successfully!
   UUID: 123e4567-e89b-12d3-a456-426614174000

🔐 Creating credential: My-Login-Credential
   Type: LOGIN
✅ Credential created successfully!
   UUID: 123e4567-e89b-12d3-a456-426614174001

============================================================
✅ All operations completed successfully!
============================================================

Created Resources:
  credential_My-Secret-Token_uuid: 123e4567-e89b-12d3-a456-426614174000
  credential_My-Login-Credential_uuid: 123e4567-e89b-12d3-a456-426614174001
  credentials_created: 2
```

## Troubleshooting

### Credential Already Exists

If you see:
```
⚠️  Credential 'My-Credential' already exists (skipping). Use --force to attempt creation anyway.
```

Either:
- Use a different credential name, or
- Use `--force` flag to attempt creation (will error if API rejects it)

### Missing Required Fields

Ensure your YAML includes:
- `credential_name`: Name of the credential
- `credential_value`: Object containing credential data
  - For Secret String: `credential_type` and `secret`
  - For Login: `credential_type`, `user_name`, and `password`

### Authentication Errors

Make sure your access token is valid:
```bash
export ALLTRUE_ACCESS_TOKEN="your-valid-token"
```

Or pass it directly:
```bash
python scripts/create_framework.py --env local --token "your-token" --credential-config credentials.yaml
```
