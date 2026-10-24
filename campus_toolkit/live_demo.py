"""Three natural-language requests, real LLM routing, actual MCP tool assertions."""
import asyncio
from datetime import datetime, timedelta
import os
import sqlite3
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from agents import set_tracing_disabled
from dotenv import load_dotenv
from .agent import ROOT, build_agent, connection, run_turn


async def main():
    load_dotenv(ROOT / ".env")
    set_tracing_disabled(True)
    provider = os.getenv("MODEL_PROVIDER", "ollama")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b") if provider == "ollama" else os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    print(f"REAL LLM VERIFICATION: provider={provider}, model={model}")
    day = (datetime.now(ZoneInfo("Asia/Beirut")) + timedelta(days=1)).date().isoformat()
    scenarios = [
        ("search_rooms", f"Which quiet rooms are available for 2 people on {day} at 10:00 Beirut time? Only look up availability.",
            dict(day=day, hour=10, party_size=2, quiet_only=True)),
        ("reserve_room", f"Book fictional room CEDAR-2 for Rana, 2 people, on {day} at 10:00 Beirut time.",
            dict(room_id="CEDAR-2", day=day, hour=10, party_size=2, student_name="Rana")),
        ("find_and_reserve", f"Find and book a quiet fictional room for Rana, 3 people, on {day} at 10:00 Beirut time.",
            dict(day=day, hour=10, party_size=3, student_name="Rana", quiet_only=True)),
    ]
    with TemporaryDirectory(prefix="campus-live-") as temp:
        async with connection(temp + "/live.sqlite3") as server:
            agent = build_agent(server)
            for index, (expected, prompt, expected_arguments) in enumerate(scenarios):
                print("\nUSER:", prompt)
                result = await run_turn(agent, prompt)
                called = [getattr(item.raw_item, "name", "") for item in result.new_items
                          if item.type == "tool_call_item"]
                if expected not in called:
                    raise AssertionError(f"Expected {expected}; actual tool calls: {called}")
                if called != [expected]:
                    raise AssertionError(f"Unexpected extra tool calls: {called}")
                if len(result.receipts) != 1 or result.receipts[0].error:
                    raise AssertionError("Tool output failed receipt validation.")
                receipt = result.receipts[0]
                for key, value in expected_arguments.items():
                    if receipt.arguments.get(key) != value or type(receipt.arguments.get(key)) is not type(value):
                        raise AssertionError(f"Incorrect argument {key}: {receipt.arguments.get(key)!r}; expected {value!r}")
                if expected == "search_rooms":
                    if any(not room["quiet"] or room["capacity"] < 2 for room in receipt.data["rooms"]):
                        raise AssertionError("Lookup returned rooms outside the requested constraints.")
                    if {r["room_id"] for r in receipt.data["rooms"]} != {"CEDAR-2", "OLIVE-4"}:
                        raise AssertionError("Unexpected availability in the fresh demo database.")
                if "available for 6 people" in result.final_output or "SEA-6" in result.final_output:
                    raise AssertionError("Displayed answer contains an unsupported room or capacity claim.")
                with sqlite3.connect(temp + "/live.sqlite3") as db:
                    rows = db.execute("SELECT room_id FROM reservations ORDER BY room_id").fetchall()
                expected_rooms = [[], [("CEDAR-2",)], [("CEDAR-2",), ("OLIVE-4",)]][index]
                if rows != expected_rooms:
                    raise AssertionError(f"Unexpected persisted state: {rows}; expected {expected_rooms}")
                print("ROUTING CHECK: PASS", expected)
                print("ARGUMENTS, RESULT CONSTRAINTS AND FACTUAL PRESENTATION: PASS", expected)
    print("\nAll three live agent routing checks passed with a real language model.")


if __name__ == "__main__":
    asyncio.run(main())
