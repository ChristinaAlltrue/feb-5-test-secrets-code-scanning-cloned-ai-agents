#!/usr/bin/env python3
"""
Example demonstrating the Gmail Listener recurring job feature.

This example shows how the Gmail Listener agent automatically:
1. Registers a recurring job when the trigger is "no" (no matching emails found)
2. Continues running the job when subsequent triggers are "no" (keeps monitoring)
3. Cancels the recurring job when the trigger is "yes" (matching emails found)
4. Reruns the control execution every 3 seconds until a match is found

The recurring job will continue running until:
- A "yes" trigger is returned (emails found)
- The job is manually cancelled
- The scheduler is shut down
"""

import asyncio
from datetime import datetime
from uuid import uuid4

# Note: In a real implementation, these would be used:
# from app.api.services.control_execution_service import (
#     create_recurring_control_execution_job,
#     cancel_recurring_control_execution_job,
#     get_recurring_control_execution_jobs,
#     get_control_execution_job_status,
# )
from app.utils.scheduler.scheduler import SchedulerService

# Global variable to store the scheduler instance for the demo
_demo_scheduler = None


def simulate_gmail_listener_result(trigger: str, feedback: str) -> dict:
    """Simulate a Gmail Listener result."""
    return {
        "trigger": trigger,
        "feedback": feedback,
    }


def simulate_control_execution_run(control_execution_id: str) -> dict:
    """Simulate running a control execution (this would normally call run_graph_by_execution_id)."""
    print(f"[{datetime.now()}] 🔄 Running control execution: {control_execution_id}")

    # Simulate some processing time
    import time

    time.sleep(1)

    # Simulate different outcomes
    import random

    if random.random() < 0.2:  # 20% chance of finding emails (80% chance of "no")
        result = simulate_gmail_listener_result(
            "yes",
            "Found 2 emails matching the criteria: 'urgent update' and 'project deadline'",
        )
        print(
            f"[{datetime.now()}] ✅ Found matching emails! Trigger: {result['trigger']}"
        )
        print(f"[{datetime.now()}] 📧 Feedback: {result['feedback']}")

        # Job cancellation is now handled in the wrapper function

    else:  # 70% chance of not finding emails
        result = simulate_gmail_listener_result(
            "no", "No emails found matching the criteria. Will continue monitoring..."
        )
        print(
            f"[{datetime.now()}] ❌ No matching emails found. Trigger: {result['trigger']}"
        )
        print(f"[{datetime.now()}] 📧 Feedback: {result['feedback']}")

    return result


def simulate_control_execution_wrapper(control_execution_id: str) -> None:
    """
    Wrapper function that simulates the actual control execution.
    This is what gets called by the scheduler.
    """
    global _demo_scheduler

    try:
        result = simulate_control_execution_run(control_execution_id)

        # Handle job cancellation based on trigger result
        if result["trigger"] == "yes":
            # Cancel the recurring job since we found what we were looking for
            if _demo_scheduler:
                try:
                    demo_job_id = f"demo_recurring_control_exec_{control_execution_id}"
                    if _demo_scheduler.get_job(demo_job_id):
                        _demo_scheduler.remove_job(demo_job_id)
                        print(
                            f"[{datetime.now()}] 🛑 Cancelled recurring job for control execution: {control_execution_id}"
                        )
                    else:
                        print(
                            f"[{datetime.now()}] ℹ️  Job already cancelled or not found: {control_execution_id}"
                        )
                except Exception as e:
                    print(f"[{datetime.now()}] ⚠️  Failed to cancel job: {e}")
            else:
                print(
                    f"[{datetime.now()}] 🛑 Would cancel recurring job for control execution: {control_execution_id}"
                )
        elif result["trigger"] == "no":
            # Job continues running - no action needed
            print(
                f"[{datetime.now()}] 🔄 Job continues running - no matching emails found yet"
            )

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error in control execution: {e}")
        import traceback

        traceback.print_exc()


async def demonstrate_gmail_listener_recurring_feature():
    """Demonstrate the Gmail Listener recurring job feature."""
    global _demo_scheduler

    print("🚀 Gmail Listener Recurring Job Demo")
    print("=" * 60)

    # Create and start the scheduler
    scheduler = SchedulerService()
    _demo_scheduler = scheduler  # Set global reference
    await scheduler.start()

    print(f"Scheduler is running: {scheduler.is_running}")
    print()

    try:
        # Create a mock control execution ID
        control_execution_id = str(uuid4())
        print(f"Created mock control execution ID: {control_execution_id}")
        print()

        # Simulate the first run of the Gmail Listener
        print("1. 🎯 First run of Gmail Listener...")
        first_result = simulate_control_execution_run(control_execution_id)

        # If the first result is "no", register a recurring job
        if first_result["trigger"] == "no":
            print("\n2. 📅 Registering recurring job (every 3 seconds)...")
            # For demo purposes, we'll create a custom job that uses our simulation
            from apscheduler.triggers.interval import IntervalTrigger

            demo_job_id = f"demo_recurring_control_exec_{control_execution_id}"

            actual_job_id = scheduler.add_job(
                func=simulate_control_execution_wrapper,
                trigger=IntervalTrigger(seconds=3),
                id=demo_job_id,
                name=f"Demo Recurring Control Execution {control_execution_id}",
                args=(control_execution_id,),
                replace_existing=True,
            )
            print(f"✅ Created demo recurring job: {actual_job_id}")

            # Show job status
            job = scheduler.get_job(demo_job_id)
            if job:
                print(
                    f"📊 Job status: {job.id} - {job.name} (next run: {job.next_run_time})"
                )
            else:
                print(f"📊 Job status: Job not found")

            # List all jobs
            all_jobs = scheduler.get_jobs()
            print(f"📋 Total jobs: {len(all_jobs)}")
            for job in all_jobs:
                print(f"  - {job.id}: {job.name} (next run: {job.next_run_time})")

            print("\n3. ⏰ Waiting for recurring job executions...")
            print("   (The job will run every 3 seconds until emails are found)")

            # Wait for the recurring job to run a few times
            await asyncio.sleep(21)  # Wait 90 seconds to see multiple executions

            # Check final job status
            final_job = scheduler.get_job(demo_job_id)
            if final_job:
                print(
                    f"\n4. 📊 Final job status: {final_job.id} - {final_job.name} (next run: {final_job.next_run_time})"
                )
            else:
                print(f"\n4. 📊 Final job status: Job not found (likely cancelled)")

        else:
            print("\n2. ✅ Found emails on first run - no recurring job needed!")

        # Show final state
        print("\n5. 📋 Final jobs list:")
        final_jobs = scheduler.get_jobs()
        if final_jobs:
            for job in final_jobs:
                print(f"  - {job.id}: {job.name} (next run: {job.next_run_time})")
        else:
            print("  No jobs active")

        print("\n== Demo completed! ==")

    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        try:
            # Remove demo job
            demo_job_id = f"demo_recurring_control_exec_{control_execution_id}"
            if scheduler.get_job(demo_job_id):
                scheduler.remove_job(demo_job_id)
                print(f"✅ Cleaned up demo job: {demo_job_id}")

            print("✅ Cleaned up test job")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        # Shutdown scheduler
        await scheduler.shutdown()
        print("✅ Scheduler shutdown completed")


if __name__ == "__main__":
    print("This example demonstrates the Gmail Listener recurring job feature.")
    print("The Gmail Listener will automatically:")
    print("  - Register a recurring job when no emails are found (trigger: 'no')")
    print(
        "  - Continue running the job when subsequent triggers are 'no' (keeps monitoring)"
    )
    print("  - Cancel the recurring job when emails are found (trigger: 'yes')")
    print("  - Rerun the control execution every 3 seconds until a match is found")
    print()
    try:
        asyncio.run(demonstrate_gmail_listener_recurring_feature())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
