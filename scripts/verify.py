"""Run real checks and retain evidence. Skipped tests make verification fail."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Also run real LLM verification (free local Ollama by default).")
    args = parser.parse_args()
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "checks": {}}
    # Capture versions before testing; do not fabricate a lock when dependencies are absent.
    versions = {}
    for package in ("fastmcp", "openai-agents", "python-dotenv"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    report["dependencies"] = versions
    frozen = subprocess.run([sys.executable, "-m", "pip", "freeze"], text=True, capture_output=True)
    if frozen.returncode == 0:
        (evidence / "installed-requirements.txt").write_text(frozen.stdout)
    with (evidence / "test-output.txt").open("w") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.discover(str(ROOT / "tests")))
    passed = result.wasSuccessful() and not result.skipped
    report["checks"]["tests"] = {"passed": passed, "run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped)}
    print((evidence / "test-output.txt").read_text())
    if passed:
        for module, filename in [("campus_toolkit.demo", "mcp-demo-output.txt")] + (
                [("campus_toolkit.live_demo", "live-agent-output.txt")] if args.live else []):
            completed = subprocess.run([sys.executable, "-m", module], cwd=ROOT,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            (evidence / filename).write_text(completed.stdout)
            print(completed.stdout)
            report["checks"][module] = {"passed": completed.returncode == 0,
                                        "returncode": completed.returncode}
    if not args.live:
        report["checks"]["live_agent"] = {"status": "not_requested"}
    (evidence / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if passed and all(c.get("passed", True) for c in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
