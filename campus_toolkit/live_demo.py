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
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in .env before running the live agent demo.")
    day = (datetime.now(ZoneInfo("Asia/Beirut")) + timedelta(days=1)).date().isoformat()
    scenarios = [
        ("search_rooms", f"Which quiet rooms are available for 2 people on {day} at 10:00 Beirut time? Only look up availability."),
        ("reserve_room", f"Book fictional room CEDAR-2 for Rana, 2 people, on {day} at 10:00 Beirut time."),
        ("find_and_reserve", f"Find and book a quiet fictional room for Rana, 3 people, on {day} at 10:00 Beirut time."),
    ]
    with TemporaryDirectory(prefix="campus-live-") as temp:
        async with connection(temp + "/live.sqlite3") as server:
            agent = build_agent(server)
            for index, (expected, prompt) in enumerate(scenarios):
                print("\nUSER:", prompt)
                result = await run_turn(agent, prompt)
                called = [getattr(item.raw_item, "name", "") for item in result.new_items
                          if item.type == "tool_call_item"]
                if expected not in called:
                    raise AssertionError(f"Expected {expected}; actual tool calls: {called}")
                with sqlite3.connect(temp + "/live.sqlite3") as db:
                    rows = db.execute("SELECT room_id FROM reservations ORDER BY room_id").fetchall()
                expected_rooms = [[], [("CEDAR-2",)], [("CEDAR-2",), ("OLIVE-4",)]][index]
                if rows != expected_rooms:
                    raise AssertionError(f"Unexpected persisted state: {rows}; expected {expected_rooms}")
                print("ROUTING CHECK: PASS", expected)
    print("\nAll three live agent routing checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
