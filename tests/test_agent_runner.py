"""Real Agents Runner + real MCP transport, using an explicitly scripted model.

This checks host wiring without API usage. It does NOT test LLM tool selection;
campus_toolkit.live_demo is the separate real-model verification.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from agents.items import ModelResponse
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText

from campus_toolkit.agent import build_agent, connection, run_turn


class ScriptedToolModel(Model):
    """Request one specified tool; then acknowledge the actual returned output."""
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
        self.calls = 0
        self.received_tool_output = False

    async def get_response(self, system_instructions, input, model_settings, tools,
                           output_schema, handoffs, tracing, **kwargs):
        self.calls += 1
        if self.calls == 1:
            available = {tool.name for tool in tools}
            assert available == {"search_rooms", "reserve_room", "find_and_reserve"}, available
            output = [ResponseFunctionToolCall(type="function_call", name=self.name,
                arguments=json.dumps(self.arguments), call_id="scripted-" + self.name)]
        else:
            self.received_tool_output = any(
                isinstance(item, dict) and item.get("type") == "function_call_output"
                for item in input)
            assert self.received_tool_output, "Runner did not return the MCP result to the model."
            output = [ResponseOutputMessage(id="scripted-message", type="message", role="assistant",
                status="completed", content=[ResponseOutputText(type="output_text",
                    text="None of the rooms are available for 6 people.", annotations=[])])]
        return ModelResponse(output=output, usage=Usage(), response_id=None)

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError("This test uses Runner.run, not streaming.")
        yield  # pragma: no cover - makes this an async iterator


class AgentRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_runner_executes_three_tools_and_returns_results_to_model(self):
        day = (datetime.now(ZoneInfo("Asia/Beirut")) + timedelta(days=1)).date().isoformat()
        scenarios = [
            ("search_rooms", dict(day=day, hour=10, party_size=2, quiet_only=True), []),
            ("reserve_room", dict(room_id="CEDAR-2", day=day, hour=10, party_size=2,
                student_name="Rana", request_id="runner-action"), [("CEDAR-2",)]),
            ("find_and_reserve", dict(day=day, hour=10, party_size=3, quiet_only=True,
                student_name="Rana", request_id="runner-plan"), [("CEDAR-2",), ("OLIVE-4",)]),
        ]
        with TemporaryDirectory() as temp:
            db_path = Path(temp) / "runner.sqlite3"
            async with connection(str(db_path)) as server:
                for name, arguments, expected_rows in scenarios:
                    with self.subTest(tool=name):
                        model = ScriptedToolModel(name, arguments)
                        agent = build_agent(server).clone(model=model)
                        result = await run_turn(agent, "Scripted host integration check for " + name)
                        self.assertTrue(model.received_tool_output)
                        self.assertEqual(model.calls, 2)
                        self.assertNotIn("available for 6 people", result.final_output)
                        self.assertNotIn("available for 6 people", json.dumps(result.to_input_list()))
                        self.assertTrue(result.receipts)
                        self.assertTrue(all(r.error is None for r in result.receipts))
                        self.assertEqual(sum(i.type == "tool_call_item" for i in result.new_items), 1)
                        with sqlite3.connect(db_path) as db:
                            self.assertEqual(db.execute(
                                "SELECT room_id FROM reservations ORDER BY room_id").fetchall(), expected_rows)
