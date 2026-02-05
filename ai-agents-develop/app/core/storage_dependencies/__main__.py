import os
from uuid import uuid4

import logfire

from app.core.models.models import ActionExecution, ControlExecution
from app.core.storage_dependencies.storage_dependencies import (
    get_provider,
    get_sync_provider,
)


async def run_demo():
    """Runs a demonstration of the repository pattern."""
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    logfire.info(f"--- Running Demo (Backend: {backend}) ---")

    async with get_provider(backend) as provider:
        # Inside the context, we use the same method to get repos,
        # regardless of the backend.
        control_repo = provider.get_repository(ControlExecution)
        action_repo = provider.get_repository(ActionExecution)
        await execute_workflow(control_repo, action_repo)


def run_sync_demo():
    """Runs a demonstration of the sync repository pattern."""
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    logfire.info(f"--- Running Sync Demo (Backend: {backend}) ---")

    with get_sync_provider(backend) as provider:
        # Inside the context, we use the same method to get repos,
        # regardless of the backend.
        control_repo = provider.get_repository(ControlExecution)
        action_repo = provider.get_repository(ActionExecution)
        execute_sync_workflow(control_repo, action_repo)


async def execute_workflow(control_repo, action_repo):
    """
    A helper function with the corrected logic to respect foreign key constraints.
    """
    logfire.warn(f"STORAGE_BACKEND: {os.getenv('STORAGE_BACKEND')}")
    logfire.info("\nStep 1: Create the Parent ControlExecution first...")
    # Create the parent object but leave the list of child IDs empty for now.
    control_id = uuid4()
    logfire.warn(f"control_id: {control_id}, type: {type(control_id)}")
    control = await control_repo.create(
        ControlExecution(
            control_id=control_id,
            edges=[{"source": "start", "target": "end"}],
            action_execution_ids=[],  # Start with an empty list
        )
    )
    logfire.info(f"Created Control: {control.id}")
    logfire.warn(f"type of control.id: {type(control.id)}")

    logfire.info("\nStep 2: Create Action children linked to the existing parent...")
    # Now that `control.id` exists in the database, we can use it as a valid foreign key.

    action1 = await action_repo.create(
        ActionExecution(
            action_prototype_name="Login",
            order=1,
            control_execution_id=control.id,  # Use the REAL parent ID
        )
    )
    action2 = await action_repo.create(
        ActionExecution(
            action_prototype_name="Click Button",
            order=2,
            control_execution_id=control.id,  # Use the REAL parent ID
        )
    )
    logfire.info(f"Created Action 1: {action1.id}")
    logfire.info(f"Created Action 2: {action2.id}")

    logfire.info("\nStep 3: Update the parent with the list of child IDs...")
    # Now that the children exist, update the parent's list.
    control.action_execution_ids = [str(action1.id), str(action2.id)]
    await control_repo.update(control)
    logfire.info("Updated Control with Action IDs.")

    logfire.info("\nStep 4: Retrieving and verifying data...")
    logfire.info(f"control.id: {control.id}, type: {type(control.id)}")
    retrieved_control = await control_repo.get(control.id)
    logfire.info(
        f"retrieved_control.id: {retrieved_control.id}, type: {type(retrieved_control.id)}"
    )
    logfire.info(f"Retrieved Control: {retrieved_control.id}")
    assert retrieved_control is not None
    assert len(retrieved_control.action_execution_ids) == 2

    # This part can now use the model validator without issue
    retrieved_actions = [
        await action_repo.get(aid) for aid in retrieved_control.action_execution_uuids
    ]
    logfire.info("Retrieved the following Actions based on IDs stored in the Control:")
    assert len(retrieved_actions) == 2
    for act in retrieved_actions:
        logfire.info(f"- {act.action_prototype_name} (ID: {act.id})")

    logfire.info("\nStep 5: Cleaning up demo data...")
    # Important: Delete children before the parent
    await action_repo.delete(action1.id)
    await action_repo.delete(action2.id)
    await control_repo.delete(control.id)
    logfire.info("Demo data has been deleted.")


def execute_sync_workflow(control_repo, action_repo):
    """
    A helper function with the corrected logic to respect foreign key constraints (Sync Version).
    """
    logfire.warn(f"STORAGE_BACKEND: {os.getenv('STORAGE_BACKEND')}")
    logfire.info("\nStep 1: Create the Parent ControlExecution first...")
    # Create the parent object but leave the list of child IDs empty for now.
    control_id = uuid4()
    logfire.warn(f"control_id: {control_id}, type: {type(control_id)}")
    control = control_repo.create(
        ControlExecution(
            control_id=control_id,
            edges=[{"source": "start", "target": "end"}],
            action_execution_ids=[],  # Start with an empty list
        )
    )
    logfire.info(f"Created Control: {control.id}")
    logfire.warn(f"type of control.id: {type(control.id)}")

    logfire.info("\nStep 2: Create Action children linked to the existing parent...")
    # Now that `control.id` exists in the database, we can use it as a valid foreign key.

    action1 = action_repo.create(
        ActionExecution(
            action_prototype_name="Login",
            order=1,
            control_execution_id=control.id,  # Use the REAL parent ID
        )
    )
    action2 = action_repo.create(
        ActionExecution(
            action_prototype_name="Click Button",
            order=2,
            control_execution_id=control.id,  # Use the REAL parent ID
        )
    )
    logfire.info(f"Created Action 1: {action1.id}")
    logfire.info(f"Created Action 2: {action2.id}")

    logfire.info("\nStep 3: Update the parent with the list of child IDs...")
    # Now that the children exist, update the parent's list.
    control.action_execution_ids = [str(action1.id), str(action2.id)]
    control_repo.update(control)
    logfire.info("Updated Control with Action IDs.")

    logfire.info("\nStep 4: Retrieving and verifying data...")
    logfire.info(f"control.id: {control.id}, type: {type(control.id)}")
    retrieved_control = control_repo.get(control.id)
    logfire.info(
        f"retrieved_control.id: {retrieved_control.id}, type: {type(retrieved_control.id)}"
    )
    logfire.info(f"Retrieved Control: {retrieved_control.id}")
    assert retrieved_control is not None
    assert len(retrieved_control.action_execution_ids) == 2

    # This part can now use the model validator without issue
    retrieved_actions = [
        action_repo.get(aid) for aid in retrieved_control.action_execution_uuids
    ]
    logfire.info("Retrieved the following Actions based on IDs stored in the Control:")
    assert len(retrieved_actions) == 2
    for act in retrieved_actions:
        logfire.info(f"- {act.action_prototype_name} (ID: {act.id})")

    logfire.info("\nStep 5: Cleaning up demo data...")
    # Important: Delete children before the parent
    action_repo.delete(action1.id)
    action_repo.delete(action2.id)
    control_repo.delete(control.id)
    logfire.info("Demo data has been deleted.")


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    logfire.configure()

    load_dotenv()
    # To run, you can set environment variables:
    #
    # (Default) Uses SQLite:
    # python main.py
    #
    # Uses Redis:
    # STORAGE_BACKEND=redis python main.py
    #
    # Uses PostgreSQL:
    # STORAGE_BACKEND=postgres DATABASE_URL="postgresql://user:pass@host:port/db" python main.py

    # Run both async and sync demos
    print("Running Async Demo...")
    asyncio.run(run_demo())

    print("\n" + "=" * 50 + "\n")

    print("Running Sync Demo...")
    run_sync_demo()

    print("\nBoth demos completed successfully!")
