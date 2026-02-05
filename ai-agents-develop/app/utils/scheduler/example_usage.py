#!/usr/bin/env python3
"""
Standalone example showing how to use the APScheduler service without FastAPI.

This demonstrates how to:
1. Initialize and start the scheduler manually
2. Add jobs with different trigger types
3. Manage jobs (pause, resume, remove)
4. Run the scheduler independently
"""

import asyncio
from datetime import datetime, timedelta

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.utils.scheduler.scheduler import SchedulerService


def example_interval_job(message: str = "Hello from interval job!"):
    """Example job that runs at intervals."""
    print(f"[{datetime.now()}] Interval job: {message}")


def example_cron_job(message: str = "Hello from cron job!"):
    """Example job that runs on a cron schedule."""
    print(f"[{datetime.now()}] Cron job: {message}")


def example_date_job(message: str = "Hello from date job!"):
    """Example job that runs at a specific date/time."""
    print(f"[{datetime.now()}] Date job: {message}")


def example_background_task(data: dict):
    """Example job that processes some data."""
    print(f"[{datetime.now()}] Processing data: {data}")
    # Simulate some work
    import time

    time.sleep(2)
    print(f"[{datetime.now()}] Data processing completed: {data}")


async def demonstrate_standalone_scheduler():
    """Demonstrate how to use the scheduler service standalone."""
    print("🚀 Standalone APScheduler Demo")
    print("=" * 50)

    # Create and start the scheduler manually
    scheduler = SchedulerService()
    await scheduler.start()

    print(f"Scheduler is running: {scheduler.is_running}")
    print(f"Current jobs: {len(scheduler.get_jobs())}")
    print()

    try:
        # 1. Add an interval job (runs every 5 seconds)
        print("1. Adding an interval job...")
        job_id = scheduler.add_job(
            func=example_interval_job,
            trigger=IntervalTrigger(seconds=5),
            id="demo_interval_job",
            name="Demo Interval Job",
            kwargs={"message": "This runs every 5 seconds!"},
        )
        print(f"✅ Added interval job: {job_id}")

        # 2. Add a cron job (runs every 10 seconds)
        print("\n2. Adding a cron job...")
        job_id = scheduler.add_job(
            func=example_cron_job,
            trigger=CronTrigger(second="*/10"),  # Every 10 seconds
            id="demo_cron_job",
            name="Demo Cron Job",
            kwargs={"message": "This runs every 10 seconds!"},
        )
        print(f"✅ Added cron job: {job_id}")

        # 3. Add a date job (runs in 15 seconds)
        print("\n3. Adding a date job...")
        future_time = datetime.now() + timedelta(seconds=15)
        job_id = scheduler.add_job(
            func=example_date_job,
            trigger=DateTrigger(run_date=future_time),
            id="demo_date_job",
            name="Demo Date Job",
            kwargs={"message": "This runs once in 15 seconds!"},
        )
        print(f"✅ Added date job: {job_id}")

        # 4. Add a background task with data processing
        print("\n4. Adding a background data processing job...")
        job_id = scheduler.add_job(
            func=example_background_task,
            trigger=IntervalTrigger(seconds=12),
            id="demo_data_processing",
            name="Demo Data Processing",
            kwargs={"data": {"user_id": 123, "action": "process_data"}},
        )
        print(f"✅ Added data processing job: {job_id}")

        # 5. List all jobs
        print("\n5. Current jobs:")
        jobs = scheduler.get_jobs()
        for job in jobs:
            print(f"  - {job.id}: {job.name} (next run: {job.next_run_time})")

        # 6. Pause a job
        print("\n6. Pausing the interval job...")
        scheduler.pause_job("demo_interval_job")
        print("✅ Interval job paused")

        # 7. Resume the job after a delay
        print("\n7. Waiting 3 seconds, then resuming...")
        await asyncio.sleep(3)
        scheduler.resume_job("demo_interval_job")
        print("✅ Interval job resumed")

        print("\n==Demo completed!==")
        print("Jobs are now running in the background.")
        print("Let's wait 30 seconds to see the jobs execute...")

        # Wait to see jobs running
        await asyncio.sleep(30)

        print("\nCleaning up...")
        # Clean up all jobs
        job_ids = [
            "demo_interval_job",
            "demo_cron_job",
            "demo_date_job",
            "demo_data_processing",
        ]
        for job_id in job_ids:
            try:
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
                    print(f"✅ Removed job: {job_id}")
                else:
                    print(
                        f"ℹ️  Job {job_id} not found (likely already executed and removed)"
                    )
            except Exception as e:
                print(f"❌ Failed to remove job {job_id}: {e}")

    except Exception as e:
        print(f"❌ Error during demo: {e}")

    finally:
        # Always shutdown the scheduler
        await scheduler.shutdown()
        print("✅ Scheduler shutdown completed")


if __name__ == "__main__":
    print("This example shows how to use the scheduler service standalone.")
    print()

    try:
        asyncio.run(demonstrate_standalone_scheduler())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
