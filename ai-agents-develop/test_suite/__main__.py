#!/usr/bin/env python3
"""
Test Suite CLI Tool

A command-line interface for running tests across different sub-modules in the test suite.
Allows interactive selection of sub-modules and test cases.
"""

import argparse
import importlib
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from alltrue.agents.schema.action_execution import (
    ActionInstance,
    ArgsDeps,
    ArgsDepsSchema,
    PrimitiveDeps,
    RefDeps,
)
from alltrue.agents.schema.control_execution import PostControlExecutionRequest
from alltrue.client.client import Client
from alltrue.client.client_config import Client_Config

from test_suite.credential import ACCESS_TOKEN


class TestSuiteCLI:
    """CLI tool for managing and running test suite modules."""

    def __init__(self):
        self.test_modules = self._discover_modules()

    def _discover_modules(self) -> Dict[str, Dict[str, Any]]:
        """Dynamically discover test modules from their config files."""
        test_modules = {}
        test_suite_path = Path(__file__).parent

        # Look for subdirectories that contain config.py files
        for subdir in test_suite_path.iterdir():
            if subdir.is_dir() and subdir.name not in ["__pycache__"]:
                config_file = subdir / "config.py"
                if config_file.exists():
                    try:
                        # Import the config module
                        config_module = importlib.import_module(
                            f"test_suite.{subdir.name}.config"
                        )
                        module_config = getattr(config_module, "MODULE_CONFIG", {})

                        if module_config:
                            test_modules[subdir.name] = module_config
                            print(f"✅ Discovered module: {subdir.name}")
                        else:
                            print(f"⚠️  No MODULE_CONFIG found in {subdir.name}")

                    except ImportError as e:
                        print(f"⚠️  Could not import config from {subdir.name}: {e}")
                    except Exception as e:
                        print(f"❌ Error loading config from {subdir.name}: {e}")

        if not test_modules:
            raise Exception(
                "⚠️  No test modules discovered. Using fallback configuration..."
            )

        return test_modules

    def get_schema_parameters(self, module_name: str) -> Dict[str, Any]:
        """Dynamically load schema parameters from the action prototype schema."""
        try:
            module_info = self.test_modules[module_name]
            schema_module = importlib.import_module(module_info["schema_module"])
            schema_class = getattr(schema_module, module_info["schema_class"])

            # Extract schema information
            schema = schema_class.model_json_schema()
            properties = schema.get("properties", {})

            # Convert to the format expected by the API
            independent_variables = {}
            for field_name, field_info in properties.items():
                independent_variables[field_name] = {
                    "value_type": "args",
                    "args_schema": {
                        "type": field_info.get("type", "string"),
                        "example": field_info.get("example", ""),
                        "description": field_info.get("description", ""),
                    },
                }

            return independent_variables

        except (ImportError, AttributeError) as e:
            print(f"⚠️  Warning: Could not load schema for {module_name}: {e}")
            raise e

    def process_test_variables(
        self, test_settings: Dict[str, Any], module_name: str
    ) -> tuple[
        Dict[str, PrimitiveDeps],
        Dict[str, RefDeps],
        Dict[str, ArgsDeps],
        Dict[str, Any],
        Dict[str, Any],
    ]:
        """
        Process test settings to separate variables into different types.

        Returns:
            tuple: (control_variables, reference_variables, independent_variables, entity_variables)
        """
        control_variables = {}
        reference_variables = {}
        independent_variables = {}
        entity_variables = {}

        # Get the full schema for reference
        try:
            full_schema = self.get_schema_parameters(module_name)
        except Exception:
            full_schema = {}

        # Process entity variables (these go to entity_exec_args)
        if "entity" in test_settings:
            entity_variables = test_settings["entity"]

        credentials = {}
        if "credentials" in test_settings:
            credentials = test_settings["credentials"]

        # Process control variables (PrimitiveDeps)
        if "control_variables" in test_settings:
            for var_name, var_value in test_settings["control_variables"].items():
                control_variables[var_name] = PrimitiveDeps(
                    value_type="primitive", value=var_value
                )

        # Process reference variables (RefDeps)
        if "reference_variables" in test_settings:
            for var_name, var_config in test_settings["reference_variables"].items():
                reference_variables[var_name] = RefDeps(
                    value_type="ref",
                    action_index=var_config.get("action_index", 0),
                    field=var_config.get("field", ""),
                )

        # Process independent variables (ArgsDeps)
        if "independent_variables" in test_settings:
            # Check if it's a list (new format) or dict (old format)
            if isinstance(test_settings["independent_variables"], list):
                # New format: list of variable sets for each action
                for i, var_set in enumerate(test_settings["independent_variables"]):
                    if isinstance(var_set, dict):
                        for var_name, var_value in var_set.items():
                            # Convert simple values to ArgsDeps
                            if (
                                not isinstance(var_value, dict)
                                or "args_schema" not in var_value
                            ):
                                independent_variables[f"action_{i}_{var_name}"] = (
                                    ArgsDeps(
                                        value_type="args",
                                        args_schema=ArgsDepsSchema(
                                            type="string",
                                            example=(
                                                str(var_value)
                                                if var_value is not None
                                                else ""
                                            ),
                                            description=f"Variable {var_name} for action {i}",
                                        ),
                                    )
                                )
                            else:
                                # Handle args_schema format
                                independent_variables[f"action_{i}_{var_name}"] = (
                                    ArgsDeps(
                                        value_type="args",
                                        args_schema=ArgsDepsSchema(
                                            **var_value["args_schema"]
                                        ),
                                    )
                                )
            else:
                # Old format: dict of variables
                for var_name, var_config in test_settings[
                    "independent_variables"
                ].items():
                    # If it's a simple value, convert to ArgsDeps with schema info
                    if isinstance(var_config, dict) and "args_schema" in var_config:
                        independent_variables[var_name] = ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(**var_config["args_schema"]),
                        )
                    else:
                        # Use schema info from full schema if available
                        schema_info = full_schema.get(var_name, {})
                        args_schema = schema_info.get(
                            "args_schema",
                            {
                                "type": "string",
                                "example": (
                                    str(var_config) if var_config is not None else ""
                                ),
                                "description": f"Variable {var_name}",
                            },
                        )
                        independent_variables[var_name] = ArgsDeps(
                            value_type="args", args_schema=ArgsDepsSchema(**args_schema)
                        )

        # # If no independent_variables specified, use the full schema as fallback
        # if not independent_variables and full_schema:
        #     for var_name, var_config in full_schema.items():
        #         independent_variables[var_name] = ArgsDeps(
        #             value_type="args",
        #             args_schema=ArgsDepsSchema(**var_config["args_schema"]),
        #         )

        return (
            control_variables,
            reference_variables,
            independent_variables,
            entity_variables,
            credentials,
        )

    def list_modules(self) -> None:
        """Display available test modules."""
        print("\n📋 Available Test Modules:")
        print("=" * 50)
        for i, (module_name, module_info) in enumerate(self.test_modules.items(), 1):
            print(f"{i}. {module_name}")
            print(f"   Description: {module_info['description']}")

            if "action_prototype" in module_info:
                print(f"   Action Prototype: {module_info['action_prototype']}")
            elif "control_type" in module_info:
                print(f"   Control Type: {module_info['control_type']}")

            print()

    def select_module(self) -> str:
        """Interactive module selection."""
        self.list_modules()

        while True:
            try:
                choice = input("Select a module (number or name): ").strip()

                # Try to parse as number
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(self.test_modules):
                        return list(self.test_modules.keys())[choice_num - 1]
                    else:
                        print(
                            f"❌ Invalid number. Please enter 1-{len(self.test_modules)}"
                        )
                        continue

                # Try to parse as name
                if choice in self.test_modules:
                    return choice
                else:
                    print(f"❌ Unknown module '{choice}'. Please try again.")
                    continue

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

    def list_test_cases(self, module_name: str) -> Dict[str, dict]:
        """Get available test cases for a module."""
        try:
            module_info = self.test_modules[module_name]
            settings_module = importlib.import_module(
                module_info["test_settings_module"]
            )
            return getattr(settings_module, "TEST_SETTINGS", {})
        except ImportError as e:
            print(f"❌ Error importing module {module_name}: {e}")
            return {}
        except AttributeError as e:
            print(f"❌ Error accessing TEST_SETTINGS in {module_name}: {e}")
            # Fallback to old ENTITY_SETTINGS for backward compatibility
            try:
                return getattr(settings_module, "ENTITY_SETTINGS", {})
            except AttributeError:
                return {}

    def select_test_case(self, module_name: str) -> str | None:
        """Interactive test case selection."""
        test_cases = self.list_test_cases(module_name)

        if not test_cases:
            print(f"❌ No test cases found for module '{module_name}'")
            return None

        print(f"\n🧪 Available Test Cases for '{module_name}':")
        print("=" * 50)
        for i, (case_name, case_info) in enumerate(test_cases.items(), 1):
            print(f"{i}. {case_name}")
            if "entity" in case_info and "goal" in case_info["entity"]:
                goal = (
                    case_info["entity"]["goal"][:100] + "..."
                    if len(case_info["entity"]["goal"]) > 100
                    else case_info["entity"]["goal"]
                )
                print(f"   Goal: {goal}")
            if "entity" in case_info and "target_PR" in case_info["entity"]:
                print(f"   Target PR: {case_info['entity']['target_PR']}")
            print()

        while True:
            try:
                choice = input("Select a test case (number or name): ").strip()

                # Try to parse as number
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(test_cases):
                        return list(test_cases.keys())[choice_num - 1]
                    else:
                        print(f"❌ Invalid number. Please enter 1-{len(test_cases)}")
                        continue

                # Try to parse as name
                if choice in test_cases:
                    return choice
                else:
                    print(f"❌ Unknown test case '{choice}'. Please try again.")
                    continue

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

    def run_test(self, module_name: str, test_case: str) -> None:
        """Execute a specific test case."""
        print(f"\n🚀 Running test case '{test_case}' for module '{module_name}'...")
        print("=" * 60)

        # Get test case settings
        test_cases = self.list_test_cases(module_name)
        if test_case not in test_cases:
            print(f"❌ Test case '{test_case}' not found in module '{module_name}'")
            return

        settings = test_cases[test_case]
        module_info = self.test_modules[module_name]

        # Process variables into different types
        (
            control_variables,
            reference_variables,
            independent_variables,
            entity_variables,
            credentials,
        ) = self.process_test_variables(settings, module_name)

        print(f"📊 Variable Summary:")
        print(f"   Control Variables: {len(control_variables)}")
        print(f"   Reference Variables: {len(reference_variables)}")
        print(f"   Independent Variables: {len(independent_variables)}")
        print(f"   Entity Variables: {len(entity_variables)}")

        # Initialize client
        try:
            client = Client(access_token=ACCESS_TOKEN)
            client._client_config = Client_Config(
                api_endpoint="localhost",
                endpoint_port=8001,
                schema="http",
                access_token=ACCESS_TOKEN,
            )
            client = client.agents()
        except Exception as e:
            print(f"❌ Error initializing client: {e}")
            return

        # Prepare control execution request
        try:
            control_id = "00000000-0000-0000-0000-000000000000"
            entity_id = "11111111-1111-1111-1111-111111111111"
            if test_case == "Pause" or test_case == "Resume":
                execution_id = "76e7ecbb-ac08-44c8-8a7b-e47eb37f8d67"
                action_execution_id = "f19cf4c7-8865-4416-8643-b346e3d4eaa1"

            else:
                execution_id = str(uuid.uuid4())
                action_execution_id = str(uuid.uuid4())

            # Check if this test uses the new agent_control and agent_actions format
            if (
                "setting_type" in settings
                and settings["setting_type"] == "Multiple Actions"
            ):
                # Use the new format with multiple actions and edges
                action_instances = []
                edges = []

                # Process agent_actions
                for action_config in settings["agent_actions"]:
                    action_instance = ActionInstance(
                        id=uuid.uuid4(),
                        action_prototype_name=action_config["action_prototype_name"],
                        order=action_config["order"],
                        control_variables=action_config.get("control_variables", {}),
                        reference_variables=action_config.get(
                            "reference_variables", {}
                        ),
                        independent_variables=action_config.get(
                            "independent_variable_schema", {}
                        ),
                    )
                    action_instances.append(action_instance)

                # Process agent_control edges
                edges = settings["agent_control"]["edges"]
                entity_variables = settings["independent_variables"]

            else:
                # Use the old format with single action
                action_instances = [
                    ActionInstance(
                        id=action_execution_id,
                        action_prototype_name=module_info["action_prototype"],
                        order=0,
                        control_variables=control_variables,
                        reference_variables=reference_variables,
                        independent_variables=independent_variables,
                    ),
                ]
                edges = []
                independent_variables = independent_variables

            # Check if this test uses the new agent_control and agent_actions format
            if (
                "setting_type" in settings
                and settings["setting_type"] == "Multiple Actions"
            ):
                # Use the new format with multiple actions and edges
                action_instances = []
                edges = []

                fixed_action_id = [
                    "f19cf4c7-8865-4416-8643-111111111111",
                    "f19cf4c7-8865-4416-8643-222222222222",
                    "f19cf4c7-8865-4416-8643-333333333333",
                    "f19cf4c7-8865-4416-8643-444444444444",
                    "f19cf4c7-8865-4416-8643-555555555555",
                    "f19cf4c7-8865-4416-8643-666666666666",
                    "f19cf4c7-8865-4416-8643-777777777777",
                    "f19cf4c7-8865-4416-8643-888888888888",
                    "f19cf4c7-8865-4416-8643-999999999999",
                    "f19cf4c7-8865-4416-8643-000000000000",
                ]
                if test_case in [
                    "Pause-Resume",
                    "GHCO-CO2-CONTROL",
                    "GHCO-DEKKO-CO2-CONTROL",
                    "GHCO-DEKKO-CO2-CONTROL-MULTIPLE",
                    "End to End Test",
                ]:
                    execution_id = "88888888-8888-8888-8888-888888888888"
                    if test_case == "End to End Test":
                        execution_id = "16408602-d82e-4c67-a7e1-4ec6ef2a94a4"
                        fixed_action_id = [
                            "0ab528e4-bb59-49fd-9b14-78439876cc66",
                            "9d3b8a91-9bc1-4421-a7e9-a98a2cc25349",
                        ]
                    input("Ensure")
                    for i, action_config in enumerate(settings["agent_actions"]):
                        action_instance = ActionInstance(
                            id=fixed_action_id[i],
                            action_prototype_name=action_config[
                                "action_prototype_name"
                            ],
                            order=action_config["order"],
                            control_variables=action_config.get(
                                "control_variables", {}
                            ),
                            reference_variables=action_config.get(
                                "reference_variables", {}
                            ),
                            independent_variables=action_config.get(
                                "independent_variable_schema", {}
                            ),
                        )
                        action_instances.append(action_instance)
                else:
                    for action_config in settings["agent_actions"]:
                        action_instance = ActionInstance(
                            id=str(uuid.uuid4()),
                            action_prototype_name=action_config[
                                "action_prototype_name"
                            ],
                            order=action_config["order"],
                            control_variables=action_config.get(
                                "control_variables", {}
                            ),
                            reference_variables=action_config.get(
                                "reference_variables", {}
                            ),
                            independent_variables=action_config.get(
                                "independent_variable_schema", {}
                            ),
                        )
                        action_instances.append(action_instance)

                # Process agent_control edges
                edges = settings["agent_control"]["edges"]
                entity_variables = settings["independent_variables"]

            else:
                # Use the old format with single action
                action_instances = [
                    ActionInstance(
                        id=action_execution_id,
                        action_prototype_name=module_info["action_prototype"],
                        order=0,
                        control_variables=control_variables,
                        reference_variables=reference_variables,
                        independent_variables=independent_variables,
                    ),
                ]
                edges = []
                independent_variables = independent_variables

            print(f"execution_id: {execution_id}")
            print(f"action_instances_ids: {[i.id for i in action_instances]}")
            control_execution_response = client.run_control_execution(
                PostControlExecutionRequest(
                    customer_id="42072582-95f4-46ef-be06-bb7aa2cdcff8",
                    control_execution_id=execution_id,
                    control_id=control_id,
                    entity_id=entity_id,
                    compliance_instruction=settings["control_instruction"],
                    action_instances=action_instances,
                    edges=edges,
                    entity_exec_args=(
                        [entity_variables]
                        if isinstance(entity_variables, dict)
                        else entity_variables
                    ),
                    credentials=(
                        [credentials] if isinstance(credentials, dict) else credentials
                    ),
                )
            )

            print("✅ Control execution started successfully!")
            print(
                f"📊 Control Execution ID: {control_execution_response.control_execution.id}"
            )
            print(control_execution_response)

            # Wait and check status
            print("\n⏳ Waiting for control execution to finish...")
            time.sleep(2)

            print("📈 Getting action execution status...")
            control_execution_status_response = client.get_control_execution_status(
                control_execution_response.control_execution.id
            )
            print(control_execution_status_response)

        except Exception as e:
            print(f"❌ Error running test: {e}")
            import traceback

            print(traceback.format_exc())
            return

    def interactive_mode(self) -> None:
        """Run the CLI in interactive mode."""
        print("🎯 Test Suite CLI - Interactive Mode")
        print("=" * 40)

        while True:
            try:
                # Select module
                module_name = self.select_module()
                if not module_name:
                    continue

                # Select test case
                test_case = self.select_test_case(module_name)
                if not test_case:
                    continue

                # Run test
                self.run_test(module_name, test_case)

                # Ask if user wants to run another test
                print("\n" + "=" * 60)
                choice = input("Run another test? (y/n): ").strip().lower()
                if choice not in ["y", "yes"]:
                    print("👋 Goodbye!")
                    break

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                import traceback

                print(traceback.format_exc())
                continue


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Test Suite CLI Tool - Run tests across different sub-modules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m test_suite                    # Interactive mode
  python -m test_suite --list             # List available modules
  python -m test_suite --module github_pr_auditor --test test1
        """,
    )

    parser.add_argument(
        "--list", "-l", action="store_true", help="List available test modules and exit"
    )

    parser.add_argument("--module", "-m", help="Specify the test module to run")

    parser.add_argument("--test", "-t", help="Specify the test case to run")

    args = parser.parse_args()

    cli = TestSuiteCLI()

    # Handle --list option
    if args.list:
        cli.list_modules()
        return

    # Handle non-interactive mode
    if args.module:
        if args.test:
            cli.run_test(args.module, args.test)
        else:
            test_case = cli.select_test_case(args.module)
            if test_case:
                cli.run_test(args.module, test_case)
        return

    # Default to interactive mode
    cli.interactive_mode()


if __name__ == "__main__":
    main()
