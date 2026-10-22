"""Real wire tests; require installed FastMCP + OpenAI Agents SDK. No API key."""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from campus_toolkit.agent import connection


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_calls_resource_and_errors_over_stdio(self):
        day = (datetime.now(ZoneInfo("Asia/Beirut")) + timedelta(days=1)).date().isoformat()
        with TemporaryDirectory() as temp:
            async with connection(str(Path(temp) / "test.sqlite3")) as server:
                tools = await server.list_tools()
                self.assertEqual({t.name for t in tools},
                    {"search_rooms", "reserve_room", "find_and_reserve"})
                for tool in tools:
                    self.assertTrue(tool.description)
                    self.assertTrue(tool.outputSchema)
                search = await server.call_tool("search_rooms", dict(day=day, hour=10, party_size=2))
                self.assertFalse(search.isError)
                args = dict(room_id="CEDAR-2", day=day, hour=10, party_size=2,
                            student_name="Rana", request_id="wire-action")
                saved = await server.call_tool("reserve_room", args)
                self.assertFalse(saved.isError)
                repeated = await server.call_tool("reserve_room", args)
                self.assertEqual(saved.structuredContent, repeated.structuredContent)
                conflict = await server.call_tool("reserve_room", args | {"request_id": "wire-conflict"})
                self.assertTrue(conflict.isError)
                self.assertIn("SLOT_UNAVAILABLE", str(conflict.content))
                plan = await server.call_tool("find_and_reserve", dict(day=day, hour=10,
                    party_size=3, student_name="Rana", request_id="wire-plan", quiet_only=True))
                self.assertFalse(plan.isError)
                self.assertIn("OLIVE-4", str(plan.content))
                no_match = await server.call_tool("find_and_reserve", dict(day=day, hour=10,
                    party_size=6, student_name="Rana", request_id="wire-empty", quiet_only=True))
                self.assertTrue(no_match.isError)
                invalid = await server.call_tool("search_rooms", dict(day="bad", hour=10, party_size=2))
                self.assertTrue(invalid.isError)
                # Resource is a separate MCP primitive; it does not expand the tool count.
                resource = await server.session.read_resource("campus://catalog")
                self.assertIn("fictional", str(resource.contents))
