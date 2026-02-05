import os
import shlex
import signal
import subprocess
import time

import logfire
import psutil


def get_pid_status(pid: int) -> str:
    """
    Get the status of a process by its PID
    """
    if not isinstance(pid, int) or pid <= 0:
        return "Invalid PID"

    try:
        command = f"ps -p {pid} -o stat="

        result = subprocess.run(
            shlex.split(command), capture_output=True, text=True, check=False, timeout=5
        )

        status = result.stdout.strip()

        if status:
            return status

        if result.returncode != 0 and not status:
            return "Not Found"

        return status if status else "Not Found"

    except subprocess.CalledProcessError:
        return "Execution Error"
    except subprocess.TimeoutExpired:
        return "Timeout"
    except FileNotFoundError:
        return "Command Not Found"
    except Exception as e:
        return f"Error: {e}"


def is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception as e:
        logfire.warning(f"PID {pid} is not running: {e}")
        return False


def stop_mcp_server_process(pid: int):
    if not is_pid_running(pid):
        return

    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        processes = [parent] + children

        # Try graceful shutdown with SIGTERM
        logfire.warning(f"Sending SIGTERM to external MCP server with PID: {pid}")
        for proc in processes:
            try:
                proc.send_signal(signal.SIGTERM)
            except psutil.NoSuchProcess:
                pass

        # Wait up to 9 seconds for graceful shutdown
        for _ in range(3):
            if not is_pid_running(pid):
                logfire.warning(
                    f"MCP server process with PID: {pid} stopped successfully"
                )
                return
            time.sleep(3)

        # Force kill with SIGKILL
        logfire.warning(
            f"Failed to stop external MCP server with PID: {pid}, killing it forcefully"
        )
        logfire.warning(f"Sending SIGKILL to external MCP server with PID: {pid}")

        # Refresh process list in case children changed
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            processes = children + [parent]  # Kill children first, then parent
        except psutil.NoSuchProcess:
            pass

        for proc in processes:
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass

        time.sleep(3)
        res = get_pid_status(pid)
        logfire.info(f"PID {pid} status: {res}")

        if not is_pid_running(pid):
            logfire.warning(f"External MCP server with PID: {pid} stopped successfully")
        else:
            logfire.warning(
                f"Failed to stop external MCP server with PID: {pid}, may need to kill it manually"
            )

    except psutil.NoSuchProcess:
        logfire.warning(f"Process {pid} no longer exists")
        return
