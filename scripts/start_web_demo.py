"""Start the local demo independently of a terminal or chat connection."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
RUNTIME.mkdir(exist_ok=True)
PORT = int(os.getenv("CAMPUS_DEMO_PORT", "8767"))
URL = f"http://127.0.0.1:{PORT}"


def status():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(URL + "/status", timeout=2) as response:
            return json.load(response)
    except (OSError, ValueError):
        return None


def main():
    existing = status()
    if existing is not None:
        if existing.get("ready"):
            print("Agent already running:", URL)
            return
        raise SystemExit("A server is already starting or needs attention: " + str(existing))
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    with (RUNTIME / "web_demo_server.log").open("a") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "campus_toolkit.web_demo"], cwd=ROOT,
            env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            start_new_session=True,
        )
    (RUNTIME / "web_demo.pid").write_text(str(process.pid))
    for _ in range(60):
        if process.poll() is not None:
            raise SystemExit("Server stopped. See runtime/web_demo_server.log")
        state = status()
        if state and state.get("ready"):
            print("Agent ready:", URL)
            print("Runs independently of this terminal; demo bookings persist across restarts.")
            return
        if state and state.get("error"):
            raise SystemExit(state["error"])
        time.sleep(0.5)
    raise SystemExit("Server is still starting. See runtime/web_demo_server.log")


if __name__ == "__main__":
    main()
