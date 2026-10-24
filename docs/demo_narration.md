# Complete the presentation

Keep the existing 1:27 tool demonstration. Record about four additional minutes using this outline, then combine the clips for a 5–7 minute presentation.

## First minute: introduce the project and tools

This project is a fictional campus study-room assistant. It demonstrates how an AI agent can use external capabilities through MCP. It has exactly three tools: search_rooms reads availability without making a reservation; reserve_room books the exact user-selected room; find_and_reserve chooses a suitable room and combines the same search and reservation implementations. The orchestration prefers the smallest suitable room. The catalog is demonstration data, not real AUB facilities.

Show the README tool table and the three decorators in server.py.

## Second minute: explain the round trip

The host coordinates the user and language model. The MCP client communicates with the server. The server publishes and executes capabilities. The OpenAI Agents SDK supplies the agent and client connection; FastMCP publishes the tools with typed input/output schemas. The model chooses a tool from the natural-language request. The SDK sends the call to a separate server process, which validates inputs and returns results. The host validates those results and presents the factual answer.

Show agent.py and server.py. Explain that Ollama runs the model locally without a paid API. Browser buttons send complete natural-language requests, not forced tool calls. Browser requests are independent; the terminal agent also supports conversation history.

## Third minute: explain reliability and show tests

The small model sometimes selected the right tool but omitted the quiet preference or added an unsupported statement. The tools now require an explicit quiet flag. The host validates MCP receipts against actual arguments and renders factual answers from verified results. The live checks test argument values and database state, not only tool names.

Show presentation.py and evidence/validation.md. Run the test command from README or show the retained actual results: 19 tests passed with no skips. Explain the distinction between scripted SDK tests and separate real-model checks.

## Fourth minute: discuss challenges and limitations

SQLite stores reservations. A unique room-and-time constraint prevents double booking. Operation IDs make identical retries return the original reservation. The orchestration can try another matching room if a competing request takes its first choice. Invalid inputs, occupied rooms and no-match cases return clear errors. Show core.py and the failure cases in tests/test_core.py.

A production version would need authenticated identities, real campus data and access controls. Keeping exactly three tools makes the assignment focused. Read the reflection and explain the design choices in your own words.

## Include the existing clip

The 1:27 recording shows the actual lookup, exact-room booking, and orchestration, including expanded MCP calls and results. Play it as the practical demonstration. Check that the combined recording lasts 5–7 minutes and that the instructor can access its final link.
