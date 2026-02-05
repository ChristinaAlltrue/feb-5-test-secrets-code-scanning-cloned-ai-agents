"""
Multi-Environment Framework Creation Script

Create compliance frameworks across different environments (playground, dev, production).

Usage:
    python scripts/create_framework.py --env playground --config path/to/config.yaml
    python scripts/create_framework.py --env development --framework-id MY_FRAMEWORK --framework-name "My Framework"
    python scripts/create_framework.py --env staging --interactive
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import dotenv

dotenv.load_dotenv()

import requests
from faker import Faker

# Environment Configuration
ENVIRONMENTS = {
    "playground": {
        "base_url": "https://api.playground.alltrue-be.com",
        "description": "Playground environment for testing",
    },
    "development": {
        "base_url": "https://api.development.alltrue-be.com",
        "description": "Development environment",
    },
    "staging": {
        "base_url": "https://api.staging.alltrue-be.com",
        "description": "Staging environment",
    },
    "local": {
        "base_url": "http://localhost:8000",
        "description": "Local development server",
    },
}

# API Endpoints
ENDPOINTS = {
    "CREATE_FRAMEWORK": "/v1/control-plane/ai-agents/agent-customer-framework",
    "DELETE_FRAMEWORK": "/v1/control-plane/ai-agents/agent-customer-framework/delete",
    "LIST_FRAMEWORKS": "/v1/control-plane/graphql",
    "LIST_CUSTOMER_FRAMEWORKS": "/v1/control-plane/ai-agents/active-agent-customer-frameworks",
    "CREATE_CONTROL": "/v1/control-plane/ai-agents/control",
    "CREATE_ENTITY": "/v1/control-plane/ai-agents/entity",
    "CREATE_EXECUTION": "/v1/control-plane/ai-agents/control-execution",
    "CREATE_GROUP_EXECUTION": "/v1/control-plane/ai-agents/control-group-execution",
    "CREATE_CREDENTIAL": "/v1/control-plane/ai-agents/credential",
}


class FrameworkCreator:
    """Create frameworks across different environments."""

    def __init__(self, environment: str, access_token: str, verify_ssl: bool = True):
        """
        Initialize the framework creator.

        Args:
            environment: Target environment (playground, development, staging, production, local)
            access_token: API authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        if environment not in ENVIRONMENTS:
            raise ValueError(
                f"Invalid environment '{environment}'. "
                f"Valid options: {', '.join(ENVIRONMENTS.keys())}"
            )

        self.environment = environment
        self.base_url = ENVIRONMENTS[environment]["base_url"]
        self.access_token = access_token
        self.verify_ssl = verify_ssl

        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        print(f"🌍 Environment: {environment.upper()}")
        print(f"🔗 Base URL: {self.base_url}")
        print(f"📝 {ENVIRONMENTS[environment]['description']}")
        print()

    def get_credential_by_name(self, credential_name: str) -> Optional[dict]:
        """
        Retrieve a credential by its name.

        Args:
            credential_name: Name of the credential to look up

        Returns:
            Credential object as a dict if found, otherwise None.
            Example response:
            {
                "credential_id": "uuid",
                "credential_name": "string",
                "credential_value": {...},
                "notes": "string"
            }
        """
        url = self.base_url + ENDPOINTS["CREATE_CREDENTIAL"]
        params = {"credential_name": credential_name}
        print(f"🔍 Looking up credential by name: '{credential_name}'")
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            data = response.json()
            # Support both a direct object and a list of matches from response.
            if isinstance(data, dict) and "credential_id" in data:
                print(f"✅ Credential found: {data['credential_id']}")
                return data
            elif isinstance(data, list) and data:
                print(f"✅ Credential found: {data[0].get('credential_id')}")
                return data[0]
            else:
                print(f"⚠️  No credential found with name '{credential_name}'.")
                return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            if e.response is not None:
                print(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Error getting credential: {e}")
            return None

    def get_framework_uuid_by_framework_id(self, framework_id: str) -> Optional[str]:
        """
        Find framework UUID by framework_id string.

        Args:
            framework_id: Framework ID string (e.g., "SAMPLE_FRAMEWORK_TEST")

        Returns:
            Framework UUID if found, None otherwise
        """

        # REST API endpoint for customer frameworks (works everywhere including local)
        response = requests.get(
            self.base_url + ENDPOINTS["LIST_CUSTOMER_FRAMEWORKS"],
            headers=self.headers,
            params={
                "framework_id": framework_id
            },  # Filter by framework_id on server side
            timeout=30,
            verify=self.verify_ssl,
        )
        response.raise_for_status()

        result = response.json()

        # Extract frameworks from response
        frameworks = result.get("frameworks", [])

        # Should have at most 1 result due to server-side filtering
        if frameworks:
            framework = frameworks[0]
            print(f"✅ Found existing framework via REST API")
            return framework.get("id")

        return None

    def delete_framework(self, framework_uuid: str) -> bool:
        """
        Delete a framework by its UUID.

        Args:
            framework_uuid: Framework UUID to delete

        Returns:
            True if deletion successful, False otherwise
        """
        print(f"🗑️  Deleting existing framework...")
        print(f"   UUID: {framework_uuid}")

        try:
            response = requests.patch(
                self.base_url + ENDPOINTS["DELETE_FRAMEWORK"] + f"/{framework_uuid}",
                headers=self.headers,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            print(f"✅ Framework deleted successfully!")
            print()
            return True

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error deleting framework: {e}")
            print(f"   Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Error deleting framework: {e}")
            return False

    def create_framework(
        self,
        framework_id: str,
        framework_name: str,
        framework_description: str,
        execution_type: str = "On Demand",
        execution_frequency: str = "Daily",
        force_overwrite: bool = False,
        existing_framework_uuid: Optional[str] = None,
    ) -> str:
        """
        Create a framework.

        Args:
            framework_id: Unique framework identifier
            framework_name: Human-readable framework name
            framework_description: Framework description
            execution_type: Execution type (default: "On Demand")
            execution_frequency: Execution frequency (default: "Daily")
            force_overwrite: If True, delete existing framework with same ID before creating
            existing_framework_uuid: If provided, delete this UUID before creating (used with --force)

        Returns:
            Created framework UUID
        """
        # Check if framework exists and delete if force_overwrite is True
        if force_overwrite:
            # If UUID was explicitly provided, use that
            uuid_to_delete = existing_framework_uuid

            # Otherwise, try to look it up
            if not uuid_to_delete:
                uuid_to_delete = self.get_framework_uuid_by_framework_id(framework_id)

            if uuid_to_delete:
                print(f"⚠️  Framework '{framework_id}' already exists")
                input(f"   Press ENTER to delete and recreate the framework...")
                if not self.delete_framework(uuid_to_delete):
                    raise Exception("Failed to delete existing framework")
                print(f"📦 Now creating new framework...")
                print()
            else:
                print(
                    f"ℹ️  No existing framework found with ID '{framework_id}' (this is OK if creating for the first time)"
                )
                print()
        payload = {
            "framework_id": framework_id,
            "framework_name": framework_name,
            "framework_description": framework_description,
            "execution_type": execution_type,
            "execution_frequency": execution_frequency,
        }

        print(f"📦 Creating framework: {framework_name}")
        print(f"   ID: {framework_id}")
        print(f"   Execution: {execution_type} ({execution_frequency})")

        try:
            response = requests.post(
                self.base_url + ENDPOINTS["CREATE_FRAMEWORK"],
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()
            framework_uuid = result["id"]

            print(f"✅ Framework created successfully!")
            print(f"   UUID: {framework_uuid}")
            print()

            return framework_uuid

        except requests.exceptions.HTTPError as e:
            # Handle 409 Conflict with helpful message
            if e.response.status_code == 409:
                print(f"❌ HTTP Error: {e}")
                print(f"   Response: {e.response.text}")
                print()
                if force_overwrite:
                    print(
                        "⚠️  Framework already exists but could not be automatically deleted."
                    )
                    print(
                        "   This usually happens when the GraphQL endpoint is unavailable."
                    )
                    print()
                    print("   To fix this, you need to:")
                    print("   1. Find the existing framework UUID from the UI or API")
                    print("   2. Delete it manually via the UI, OR")
                    print("   3. Use a different framework_id in your YAML config")
                else:
                    print(
                        "💡 Tip: Use --force to automatically delete and recreate the framework"
                    )
                print()
            else:
                print(f"❌ HTTP Error: {e}")
                print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error creating framework: {e}")
            raise

    def _replace_credential_name_with_uuid(self, action_list: list) -> list:
        """
        Replace credential name with credential UUID in the action list.
        """
        for action in action_list:
            credential_list = []
            if "credentials" in action:
                for credential in action["credentials"]:
                    credential_obj = self.get_credential_by_name(
                        credential["credential_name"]
                    )
                    if credential_obj is None:
                        raise ValueError(
                            f"Credential {credential['credential_name']} not found"
                        )
                    credential_list.append(credential_obj["credential_id"])
                action["credentials"] = credential_list
            else:
                action["credentials"] = []
        return action_list

    def create_control(
        self,
        framework_uuid: str,
        control_name: str,
        control_instruction: str,
        action_list: list,
        edges: Optional[list] = None,
    ) -> str:
        """
        Create a control within a framework.

        Args:
            framework_uuid: Parent framework UUID
            control_name: Control name
            control_instruction: Control instructions
            action_list: List of action configurations
            edges: Graph edges (default: sequential chain)

        Returns:
            Created control UUID
        """
        if edges is None:
            # Default to sequential chain
            edges = [
                {"source": i, "target": i + 1, "condition": ""}
                for i in range(len(action_list) - 1)
            ]
        action_list = self._replace_credential_name_with_uuid(action_list)

        payload = {
            "customer_framework_id": framework_uuid,
            "name": control_name,
            "edges": edges,
            "instructions": control_instruction,
            "action_list": action_list,
        }

        print(f"🎯 Creating control: {control_name}")
        print(f"   Actions: {len(action_list)}")
        print(f"   Edges: {len(edges)}")

        try:
            response = requests.post(
                self.base_url + ENDPOINTS["CREATE_CONTROL"],
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()
            control_uuid = result["id"]

            print(f"✅ Control created successfully!")
            print(f"   UUID: {control_uuid}")
            print()

            return control_uuid

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error creating control: {e}")
            raise

    def create_entity(
        self,
        control_uuid: str,
        entity_name: str,
        independent_variables: list,
        credentials: list,
    ) -> str:
        """
        Create an entity for a control.

        Args:
            control_uuid: Parent control UUID
            entity_name: Entity name
            independent_variables: List of variable dictionaries
            credentials: List of credential names
        Returns:
            Created entity UUID
        """
        # convert credential names to credential IDs
        credential_ids = []
        for credential in credentials:
            credential_obj = self.get_credential_by_name(credential["credential_name"])
            if credential_obj is None:
                raise ValueError(
                    f"Credential {credential['credential_name']} not found"
                )
            credential_ids.append(credential_obj["credential_id"])

        payload = {
            "name": entity_name,
            "independent_variables": independent_variables,
            "agent_control_id": control_uuid,
            "credentials": credential_ids,
        }
        print(f"📋 Creating entity: {entity_name}")
        print(f"   Variables: {len(independent_variables)} action(s)")

        try:
            response = requests.post(
                self.base_url + ENDPOINTS["CREATE_ENTITY"],
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()
            entity_uuid = result["id"]

            print(f"✅ Entity created successfully!")
            print(f"   UUID: {entity_uuid}")
            print()

            return entity_uuid

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error creating entity: {e}")
            raise

    def create_control_group_execution(
        self,
        framework_uuid: str,
        execution_name: str,
        execution_type: str = "On Demand",
    ) -> str:
        """
        Create a control group execution.

        IMPORTANT: A control group execution is REQUIRED for controls to be visible
        and clickable in the UI. Without this, controls will not appear.

        Args:
            framework_uuid: Parent framework UUID
            execution_name: Execution name
            execution_type: Execution type (default: "On Demand")

        Returns:
            Created control group execution UUID
        """
        payload = {
            "agent_customer_framework_id": framework_uuid,
            "name": execution_name,
            "type": execution_type,
            "execution_scheduled_at": datetime.now(timezone.utc).isoformat(),
        }

        print(f"🚀 Creating control group execution: {execution_name}")
        print(f"   ⚠️  NOTE: This is REQUIRED for controls to be visible in the UI")

        try:
            response = requests.post(
                self.base_url + ENDPOINTS["CREATE_GROUP_EXECUTION"],
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()
            execution_uuid = result["id"]

            print(f"✅ Control group execution created successfully!")
            print(f"   UUID: {execution_uuid}")
            print(f"   🔗 Access controls at:")
            print(
                f"   {self.base_url.replace('/v1', '')}/ai-auditor/{framework_uuid}/execution/{execution_uuid}"
            )
            print()

            return execution_uuid

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error creating control group execution: {e}")
            raise

    def trigger_execution(
        self, control_uuid: str, control_group_execution_uuid: str
    ) -> list:
        """
        Trigger control execution.

        Args:
            control_uuid: Control UUID
            control_group_execution_uuid: Control group execution UUID

        Returns:
            List of execution results
        """
        payload = {
            "control_id": control_uuid,
            "control_group_execution_id": control_group_execution_uuid,
        }

        print(f"▶️  Triggering execution...")

        try:
            response = requests.post(
                self.base_url + ENDPOINTS["CREATE_EXECUTION"],
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()
            executions = result.get("results", [])

            print(f"✅ Execution triggered successfully!")
            print(f"   Executions: {len(executions)}")

            for execution in executions:
                print(f"   - Execution ID: {execution.get('execution_id')}")
                print(f"     Entity ID: {execution.get('entity_id')}")

            print()

            return executions

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error triggering execution: {e}")
            raise

    def create_credential(
        self,
        credential_name: str,
        credential_value: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> str:
        """
        Create a credential.

        Args:
            credential_name: Name of the credential
            credential_value: Credential value dictionary. Must be one of:
                - Login credential: {
                    "credential_type": "Login",
                    "user_name": str,
                    "password": str,
                    "mfa": Optional[str]
                  }
                - Secret string credential: {
                    "credential_type": "Secret String",
                    "secret": str
                  }
            notes: Optional notes for the credential

        Returns:
            Created credential UUID
        """
        payload = {
            "credential_name": credential_name,
            "credential_value": credential_value,
        }
        if notes is not None:
            payload["notes"] = notes

        credential_type = credential_value.get("credential_type", "UNKNOWN")
        print(f"🔐 Creating credential: {credential_name}")
        print(f"   Type: {credential_type}")

        try:
            response = requests.post(
                self.base_url + ENDPOINTS["CREATE_CREDENTIAL"],
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()
            credential_uuid = result["id"]

            print(f"✅ Credential created successfully!")
            print(f"   UUID: {credential_uuid}")
            print()

            return credential_uuid

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error creating credential: {e}")
            raise


def load_framework_config(config_path: str) -> Dict[str, Any]:
    """
    Load framework configuration from a YAML or JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    import yaml

    with open(config_path, "r") as f:
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            return yaml.safe_load(f)
        elif config_path.endswith(".json"):
            return json.load(f)
        else:
            raise ValueError("Config file must be .yaml, .yml, or .json")


def load_credential_config(config_path: str) -> list:
    """
    Load credential configuration from a YAML or JSON file.

    Args:
        config_path: Path to credential configuration file

    Returns:
        List of credential configurations
    """
    import yaml

    with open(config_path, "r") as f:
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            config = yaml.safe_load(f)
        elif config_path.endswith(".json"):
            config = json.load(f)
        else:
            raise ValueError("Config file must be .yaml, .yml, or .json")

    # Extract credentials list
    if "credentials" in config:
        return config["credentials"]
    elif isinstance(config, list):
        return config
    else:
        raise ValueError(
            "Credential config must contain a 'credentials' key or be a list"
        )


def create_credentials_from_config(
    creator: FrameworkCreator, config_path: str, force_overwrite: bool = False
) -> Dict[str, str]:
    """
    Create credentials from a YAML or JSON configuration file.

    Args:
        creator: FrameworkCreator instance
        config_path: Path to credential configuration file
        force_overwrite: If True, attempt to create even if credential exists (API will error if conflict).
                         If False, skip existing credentials.

    Returns:
        Dictionary mapping credential names to their UUIDs
    """
    print(f"Loading credential configuration from {config_path}...\n")
    credentials_config = load_credential_config(config_path)

    results = {}

    for cred_config in credentials_config:
        credential_value = cred_config.get("credential_value")
        if not credential_value:
            raise ValueError(
                f"Credential value is required for {cred_config.get('credential_name')}"
            )

        credential_name = cred_config.get("credential_name")
        if not credential_name:
            raise ValueError(
                f"Credential name is required with value: {credential_value}"
            )

        notes = cred_config.get("notes")

        # Check if credential already exists (only if not forcing overwrite)
        if not force_overwrite:
            existing_credential = creator.get_credential_by_name(credential_name)
            if existing_credential:
                print(
                    f"⚠️  Credential '{credential_name}' already exists (skipping). Use --force to attempt creation anyway."
                )
                results[credential_name] = existing_credential["credential_id"]
                continue

        try:
            credential_uuid = creator.create_credential(
                credential_name=credential_name,
                credential_value=credential_value,
                notes=notes,
            )
            results[credential_name] = credential_uuid
        except Exception as e:
            print(f"❌ Failed to create credential '{credential_name}': {e}")
            # Continue with other credentials
            continue

    return results


def create_sample_framework(
    creator: FrameworkCreator,
    force_overwrite: bool = False,
    existing_framework_uuid: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create a sample framework for testing.

    Args:
        creator: FrameworkCreator instance
        force_overwrite: If True, delete existing framework before creating
        existing_framework_uuid: UUID of existing framework to delete

    Returns:
        Dictionary with created resource UUIDs
    """
    faker = Faker()

    # Framework
    framework_id = f"SAMPLE_FRAMEWORK_{faker.word().upper()}"
    framework_name = f"Sample Framework {faker.word().capitalize()}"

    framework_uuid = creator.create_framework(
        framework_id=framework_id,
        framework_name=framework_name,
        framework_description="Sample framework for testing purposes",
        execution_type="On Demand",
        execution_frequency="Daily",
        force_overwrite=force_overwrite,
        existing_framework_uuid=existing_framework_uuid,
    )

    # Control
    control_name = "Sample Control - Add Two Numbers"
    control_instruction = """
    **SKIP COMPLIANCE CHECK** Simple test control that adds 1 to an input twice.
    """

    action_list = [
        {
            "action_name": "Sample Action 1",
            "action_prototype_name": "sample",
            "order": 0,
            "category": "Prebuilt",
            "control_variables": {},
            "reference_variables": {},
            "dependency_schema": [
                {
                    "name": "input",
                    "type": "int",
                    "example": "5",
                    "description": "Input number",
                    "required": True,
                }
            ],
            "independent_variable_schema": {
                "input": {
                    "value_type": "args",
                    "args_schema": {
                        "type": "int",
                        "example": "5",
                        "description": "Input number",
                    },
                }
            },
            "credentials": [
                {
                    "credential_name": "Sample-Credential",
                }
            ],
        },
        {
            "action_name": "Sample Action 2",
            "action_prototype_name": "sample",
            "order": 1,
            "category": "Prebuilt",
            "control_variables": {},
            "reference_variables": {
                "input": {"value_type": "ref", "action_index": 0, "field": "output"}
            },
            "dependency_schema": [],
            "independent_variable_schema": {},
        },
    ]

    control_uuid = creator.create_control(
        framework_uuid=framework_uuid,
        control_name=control_name,
        control_instruction=control_instruction,
        action_list=action_list,
    )

    # Entity
    entity_name = "Sample Entity"
    independent_variables = [{"input": 5}, {}]  # Second action uses reference variable
    entity_credentials = ["Sample-Credential"]
    entity_credentials_ids = []
    for credential_name in entity_credentials:
        credential_obj = creator.get_credential_by_name(credential_name)
        if credential_obj is None:
            raise ValueError(f"Credential {credential_name} not found")
        entity_credentials_ids.append(credential_obj["credential_id"])

    entity_uuid = creator.create_entity(
        control_uuid=control_uuid,
        entity_name=entity_name,
        independent_variables=independent_variables,
        credentials=entity_credentials_ids,
    )

    # Create control group execution (REQUIRED for UI visibility)
    execution_name = "Initial Execution"
    group_execution_uuid = creator.create_control_group_execution(
        framework_uuid=framework_uuid,
        execution_name=execution_name,
        execution_type="On Demand",
    )

    return {
        "framework_uuid": framework_uuid,
        "framework_id": framework_id,
        "control_uuid": control_uuid,
        "entity_uuid": entity_uuid,
        "group_execution_uuid": group_execution_uuid,
    }


def create_sample_credential(
    creator: FrameworkCreator,
    force_overwrite: bool = False,
) -> Dict[str, str]:
    """
    Create a sample credential for testing.
    If the credential already exists and force_overwrite is False, reuse the existing one.
    Otherwise, attempt to create it.
    """
    credential_name = "Sample-Credential"
    credential_value = {
        "credential_type": "Secret String",
        "secret": "sample_secret",
    }

    existing_credential = creator.get_credential_by_name(credential_name)
    if existing_credential and not force_overwrite:
        credential_uuid = existing_credential["credential_id"]
        print(
            f"✅ Credential '{credential_name}' already exists (skipping). Use --force to attempt creation anyway."
        )
    else:
        credential_uuid = creator.create_credential(
            credential_name=credential_name,
            credential_value=credential_value,
        )

    return {
        "credential_uuid": credential_uuid,
        "credential_name": credential_name,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create compliance frameworks across different environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create sample framework in local
  python scripts/create_framework.py --env local --sample

  # Create from config file
  python scripts/create_framework.py --env local --config framework_config.yaml

  # Create credentials from config file
  python scripts/create_framework.py --env local --credential-config credential_config.yaml

  # Create with command-line parameters
  python scripts/create_framework.py --env development \\
    --framework-id MY_FRAMEWORK \\
    --framework-name "My Framework" \\
    --framework-description "Description here"

Environments:
  playground   - Testing environment
  development  - Development environment
  staging      - Staging environment
  local        - Local development server (localhost:8000)
        """,
    )

    parser.add_argument(
        "--env",
        "--environment",
        required=True,
        choices=list(ENVIRONMENTS.keys()),
        help="Target environment",
    )

    parser.add_argument(
        "--token", help="API access token (or set ALLTRUE_ACCESS_TOKEN env var)"
    )

    parser.add_argument(
        "--config", help="Path to framework configuration file (YAML or JSON)"
    )

    parser.add_argument(
        "--sample", action="store_true", help="Create a sample framework for testing"
    )

    parser.add_argument(
        "--framework-id",
        help="Framework ID (required if not using --config or --sample)",
    )

    parser.add_argument(
        "--framework-name",
        help="Framework name (required if not using --config or --sample)",
    )

    parser.add_argument("--framework-description", help="Framework description")

    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification",
    )

    parser.add_argument("--output", help="Save created resource UUIDs to JSON file")

    parser.add_argument(
        "--create-execution",
        action="store_true",
        help="Create a control group execution (REQUIRED for controls to be visible in UI)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing framework if it already exists (deletes and recreates)",
    )

    parser.add_argument(
        "--framework-uuid",
        help="UUID of existing framework to delete when using --force (only needed if auto-lookup fails)",
    )

    parser.add_argument(
        "--sample-credential",
        action="store_true",
        help="Create a sample credential for testing",
    )

    parser.add_argument(
        "--credential-config",
        help="Path to credential configuration file (YAML or JSON) to create multiple credentials",
    )

    args = parser.parse_args()

    # Get access token
    access_token = args.token or os.getenv("ALLTRUE_ACCESS_TOKEN")
    if not access_token:
        print(
            "❌ Error: Access token required. Use --token or set ALLTRUE_ACCESS_TOKEN"
        )
        sys.exit(1)

    # Create framework creator
    try:
        creator = FrameworkCreator(
            environment=args.env,
            access_token=access_token,
            verify_ssl=not args.no_verify_ssl,
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Create framework
    result = {}

    try:
        if args.sample:
            print("Creating sample framework...\n")
            result = create_sample_framework(
                creator,
                force_overwrite=args.force,
                existing_framework_uuid=args.framework_uuid,
            )

        elif args.sample_credential:
            print("Creating sample credential...\n")
            result = create_sample_credential(
                creator,
                force_overwrite=args.force,
            )

        elif args.credential_config:
            print(f"Creating credentials from {args.credential_config}...\n")
            credential_results = create_credentials_from_config(
                creator,
                config_path=args.credential_config,
                force_overwrite=args.force,
            )
            # Convert to result format for consistency
            result = {
                f"credential_{name}_uuid": uuid
                for name, uuid in credential_results.items()
            }
            result["credentials_created"] = str(len(credential_results))

        elif args.config:
            print(f"Loading configuration from {args.config}...\n")
            config = load_framework_config(args.config)

            # Create framework from config
            framework_uuid = creator.create_framework(
                framework_id=config["framework_id"],
                framework_name=config["framework_name"],
                framework_description=config.get("framework_description", ""),
                execution_type=config.get("execution_type", "On Demand"),
                execution_frequency=config.get("execution_frequency", "Daily"),
                force_overwrite=args.force,
                existing_framework_uuid=args.framework_uuid,
            )

            result["framework_uuid"] = framework_uuid
            result["framework_id"] = config["framework_id"]

            # Create controls if defined
            if "controls" in config:
                for control_config in config["controls"]:
                    control_uuid = creator.create_control(
                        framework_uuid=framework_uuid,
                        control_name=control_config["name"],
                        control_instruction=control_config["instructions"],
                        action_list=control_config["action_list"],
                        edges=control_config.get("edges"),
                    )
                    result[f"control_{control_config['name']}_uuid"] = control_uuid

                    # Create entities for this control if defined
                    if "entities" in control_config:
                        for entity_config in control_config["entities"]:
                            entity_uuid = creator.create_entity(
                                control_uuid=control_uuid,
                                entity_name=entity_config["name"],
                                independent_variables=entity_config[
                                    "independent_variables"
                                ],
                                credentials=entity_config.get("credentials", []),
                            )
                            result[f"entity_{entity_config['name']}_uuid"] = entity_uuid

            # Create control group execution if configured
            execution_config = config.get("execution", {})
            if execution_config.get("auto_create", False):
                execution_name = execution_config.get(
                    "name", f"{config['framework_name']} - Initial Execution"
                )
                execution_type = execution_config.get("type", "On Demand")

                group_execution_uuid = creator.create_control_group_execution(
                    framework_uuid=framework_uuid,
                    execution_name=execution_name,
                    execution_type=execution_type,
                )
                result["group_execution_uuid"] = group_execution_uuid

        elif args.framework_id and args.framework_name:
            framework_uuid = creator.create_framework(
                framework_id=args.framework_id,
                framework_name=args.framework_name,
                framework_description=args.framework_description or "",
                execution_type="On Demand",
                execution_frequency="Daily",
                force_overwrite=args.force,
                existing_framework_uuid=args.framework_uuid,
            )

            result["framework_uuid"] = framework_uuid
            result["framework_id"] = args.framework_id

            # Create execution if requested
            if args.create_execution:
                execution_name = f"{args.framework_name} - Initial Execution"
                group_execution_uuid = creator.create_control_group_execution(
                    framework_uuid=framework_uuid, execution_name=execution_name
                )
                result["group_execution_uuid"] = group_execution_uuid

        else:
            print(
                "❌ Error: Must specify --sample, --config, --credential-config, --sample-credential, or --framework-id and --framework-name"
            )
            parser.print_help()
            sys.exit(1)

        # Save output if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"💾 Results saved to {args.output}")

        print("\n" + "=" * 60)
        print("✅ All operations completed successfully!")
        print("=" * 60)
        print("\nCreated Resources:")
        for key, value in result.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
