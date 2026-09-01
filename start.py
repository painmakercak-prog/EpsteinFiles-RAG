import os
import signal
import subprocess
import sys
import time
import urllib.request

from bootstrap import ensure_vector_database

processes: list[subprocess.Popen[bytes]] = []


def stop_processes() -> None:
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
    for process in reversed(processes):
        if process.poll() is None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


def handle_signal(_signum: int, _frame: object) -> None:
    stop_processes()
    raise SystemExit(0)


def wait_for_api(timeout_seconds: int = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if processes[0].poll() is not None:
            raise RuntimeError("API process exited during startup")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError("API did not become healthy before the startup deadline")


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    if not 1 <= port <= 65535:
        raise RuntimeError("PORT must be between 1 and 65535")
    if not os.getenv("GROQ_API_KEY", "").strip():
        raise RuntimeError("GROQ_API_KEY is not configured")

    ensure_vector_database()

    api = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]
    )
    processes.append(api)
    wait_for_api()

    environment = os.environ.copy()
    environment.setdefault("API_URL", "http://127.0.0.1:8000/ask")
    ui = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.address",
            "0.0.0.0",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        env=environment,
    )
    processes.append(ui)

    while True:
        for process in processes:
            code = process.poll()
            if code is not None:
                raise RuntimeError(f"A service process exited with code {code}")
        time.sleep(1)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    try:
        main()
    finally:
        stop_processes()
