"""No API key: real stdio transport via the OpenAI Agents SDK MCP client."""
import asyncio
from datetime import datetime, timedelta
import json
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from .agent import connection


async def main():
    day = (datetime.now(ZoneInfo("Asia/Beirut")) + timedelta(days=1)).date().isoformat()
    with TemporaryDirectory(prefix="campus-mcp-demo-") as temp:
        async with connection(temp + "/demo.sqlite3") as server:
            tools = await server.list_tools()
            assert {t.name for t in tools} == {"search_rooms", "reserve_room", "find_and_reserve"}
            print("DISCOVERY:", ", ".join(t.name for t in tools))
            queries = [
                ("search_rooms", dict(day=day, hour=10, party_size=2, quiet_only=True)),
                ("reserve_room", dict(room_id="CEDAR-2", day=day, hour=10,
                     party_size=2, student_name="Rana", request_id="demo-specific")),
                ("find_and_reserve", dict(day=day, hour=10, party_size=3,
                     student_name="Rana", request_id="demo-plan", quiet_only=True)),
                ("reserve_room", dict(room_id="CEDAR-2", day=day, hour=10,
                     party_size=2, student_name="Rana", request_id="demo-conflict")),
                ("find_and_reserve", dict(day=day, hour=10, party_size=3,
                     student_name="Rana", request_id="demo-plan", quiet_only=True)),
            ]
            for name, args in queries:
                print("\nCLIENT -> SERVER", name, json.dumps(args))
                result = await server.call_tool(name, args)
                print("SERVER -> CLIENT", result.model_dump_json(indent=2))
            print("\nThis is an MCP-client demonstration, not an LLM routing demonstration.")
            print("For the live agent, start Ollama, pull qwen2.5:3b, and run python -m campus_toolkit.agent.")


if __name__ == "__main__":
    asyncio.run(main())
