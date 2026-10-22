# Campus Study MCP Toolkit

**Rana Ezzeddine - EECE 503P / C5**

Repository: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5

Verified run: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5/actions/runs/39840397595

**Verification: 14 tests passed with zero skips on Python 3.11 and 3.13.** Real MCP calls, resource access, failures, replay and the SDK Runner integration passed. The runner test uses an explicitly scripted model. The separate live verification uses an actual local language model through Ollama; see the validation record for its execution status.

A fictional campus room assistant built with **FastMCP** and the **OpenAI Agents SDK**, using a **free local Ollama model by default**. No OpenAI API key, payment method, or paid API is required for this mode. It exposes exactly three MCP tools and one read-only catalog resource. The catalog and bookings are local demonstration data, not AUB facilities or a real campus reservation service.

| Category | MCP tool | Single responsibility | Output |
|---|---|---|---|
| Data | `search_rooms` | Look up suitable available rooms for one hour | `SearchResult`: day, hour, timezone, duration, rooms |
| Action | `reserve_room` | Save one specified room reservation | `Reservation`: ID, room, day, hour, party size, name, timezone, duration |
| Orchestration | `find_and_reserve` | Obtain a suitable room through search then reservation | `PlanResult`: reservation, selection reason, steps |

## Start here

Python 3.11+ is required. Run commands from this project folder.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip freeze > evidence/installed-requirements.txt
python scripts/verify.py
```

Windows activation: `.venv\Scripts\activate`. The direct dependencies are pinned to current stable versions resolved during verification on October 22, 2026: FastMCP 4.1.3, OpenAI Agents SDK 0.24.0, MCP 2.3.0 and python-dotenv 1.2.4. `evidence/installed-requirements.txt` retains the complete resolved Ubuntu/Python 3.13 environment. The freeze command records your own platform-specific environment.

The **MCP-only demo needs no API key**. It launches a real FastMCP subprocess and calls it through `MCPServerStdio` from the OpenAI Agents SDK. It demonstrates all three tools, a slot conflict and an idempotent retry. Its temporary database is removed after the demo, so rerunning is safe. This checks the protocol round trip but does not test model tool selection.

## Run the actual agent

```bash
cp .env.example .env
# Defaults to MODEL_PROVIDER=ollama. No API key needed.
# Start the Ollama application first, then download the model:
ollama pull qwen2.5:3b
python -m campus_toolkit.agent
```

Install [Ollama](https://ollama.com/download), start its application or run `ollama serve` in another terminal, and run `ollama pull qwen2.5:3b` once. The model download is about 1.9 GB. Inference uses your computer rather than a paid API. The SDK uses `OpenAIChatCompletionsModel` with Ollama's OpenAI-compatible endpoint at localhost. The dummy string `ollama` is a client placeholder, not a credential. The free mode rejects non-local endpoints. `.env` and the booking database are gitignored.

Optional paid OpenAI support remains available only if you explicitly set `MODEL_PROVIDER=openai` and configure `OPENAI_API_KEY`; it is disabled by default. You do not need it for this assignment.

Example conversation (replace the date with tomorrow, within 30 days):

1. "Which quiet rooms are available for 2 people tomorrow at 10:00 Beirut time? Only search."
2. "Book CEDAR-2 for Rana, 2 people, tomorrow at 10:00 Beirut time."
3. "Find and book a quiet room for Rana, 3 people, tomorrow at 10:00 Beirut time."

Single prompt mode:

```bash
python -m campus_toolkit.agent --prompt "Which quiet rooms are available for 2 people tomorrow at 10:00 Beirut time?"
```

To automatically exercise **real model routing** for all three tools against a fresh temporary database:

```bash
python scripts/verify.py --live
```

The verification command runs the tests, rejects any skips, captures the real MCP demo, and saves timestamped JSON and text evidence under `evidence/`. With `--live`, it also runs the live agent demo, which prints actual SDK tool-call items and results and checks the selected tools and persisted reservations. A model may still make a bad decision or an API request may fail; the demo raises an error instead of reporting an invented pass. Review the returned reservation IDs and output. For a full recording outline, see `docs/demo_guide.md`.

## Architecture and boundaries

The Python application (`agent.py`) is the **Host**. Its SDK `MCPServerStdio` connection owns the **Client** that launches `server.py`, the **Server**, using the same Python interpreter as the host. SDK-managed discovery exposes schemas to the agent. The model selects a tool, the SDK sends an MCP call, FastMCP validates inputs and dispatches the handler, and the result returns to the agent for a final answer. The context manager closes the subprocess connection when finished.

`find_and_reserve` calls `Toolkit.search_rooms` and then `Toolkit.reserve_room`, which are the same implementations used by the two standalone MCP handlers. Helpers and database methods are not registered as additional tools. Internal calls are local function calls; the host-to-server boundary uses MCP. `campus://catalog` is a separate `@mcp.resource`, not a fourth tool, and is not automatically injected into the model context. It is available to resource-aware clients and tested separately.

Output types are dataclasses that FastMCP uses to derive structured schemas. Input annotations and `Field` metadata document types and constraints. The discovery test asserts exactly three tool names and nonempty descriptions/output schemas.

## Behavior and data contracts

- One-hour bookings, starting at integer hours **08:00 through 19:00**, in **Asia/Beirut**. The start must be in the future and no more than 30 calendar days ahead. Dates use `YYYY-MM-DD`. Timezone rules come from Python `zoneinfo`.
- Party size: 1-6. `quiet_only=true` excludes collaboration rooms. Matches are ordered by capacity, then room ID.
- Static fictional rooms: CEDAR-2 (2 seats, quiet), OLIVE-4 (4 seats, quiet), SEA-6 (6 seats, collaborative).
- `reserve_room` requires room ID, day, hour, party size, student name and request ID. It validates the room and capacity again, independently of prior searches.
- `find_and_reserve` requires day, hour, party size, name, request ID, and optional quiet flag. Its single goal is a successful suitable reservation. When no match exists it raises a clear error without creating a reservation.
- Request IDs: 1-64 letters/digits/underscores/hyphens. Identical retries return the same reservation, even after restarting. Reusing an ID for changed arguments or another write tool produces `REQUEST_ID_CONFLICT`. A request ID is not an authentication token.
- The host supplies a new UUID per user turn. SDK retries within a turn reuse the operation ID. A new chat turn is a new operation: if a user explicitly asks for another booking, the assistant does not treat it as a network retry.
- SQLite `BEGIN IMMEDIATE` and a unique `(room_id, day, hour)` constraint prevent double booking. The orchestration can try the next result after a race. No files are written by the data lookup after server startup initialization.
- `runtime/bookings.sqlite3` persists ordinary agent bookings. Use `CAMPUS_DB_PATH` for an isolated run. Both demonstration scripts use disposable databases. There is no cancellation tool because the assignment requires exactly three tools.

| Predictable condition | Result |
|---|---|
| Malformed, past or too-distant date | `INVALID_DATE` or `INVALID_SLOT` |
| Invalid hour or party size | Schema validation error or domain validation error |
| Unknown room / too many people | `ROOM_NOT_FOUND` / `CAPACITY_EXCEEDED` |
| Occupied room | `SLOT_UNAVAILABLE` |
| No suitable room | Search returns empty `rooms`; orchestration raises `NO_MATCHING_ROOM` |
| Changed arguments with reused request ID | `REQUEST_ID_CONFLICT` |
| Database failure | `STORAGE_UNAVAILABLE` at the MCP adapter |

Domain failures become `ToolError`, so MCP callers receive error results instead of a success-shaped silent failure. Unexpected exceptions remain framework errors. Initialization failures stop startup rather than advertising a broken server. Tool annotations describe side effects; they are hints, not security enforcement. Explicit booking intent is an agent instruction in this local demo, not a substitute for production authorization.

## Files and verification

| File | Purpose |
|---|---|
| `campus_toolkit/core.py` | Domain logic, typed outputs and SQLite persistence |
| `campus_toolkit/server.py` | FastMCP server; exactly three tools plus catalog resource |
| `campus_toolkit/agent.py` | OpenAI Agents SDK host, interactive chat and printed tool evidence |
| `campus_toolkit/demo.py` | MCP client round trip without model calls |
| `campus_toolkit/live_demo.py` | Live model routing through all three tools |
| `tests/test_core.py` | Domain success/failure, read-only behavior, concurrency and replay tests |
| `tests/test_mcp.py` | Real subprocess discovery, calls, errors and resource test |
| `tests/test_agent_runner.py` | Real SDK Runner and MCP transport with a scripted model; not an LLM test |
| `scripts/verify.py` | Evidence capture; fails on errors or skipped tests |
| `docs/reading_summary.md` | Required 300-400 word summary with sources |
| `docs/reflection.md` | Two-paragraph reflection |
| `docs/demo_guide.md` | Optional recording plan and submission checklist |
| `evidence/validation.md` | Honest validation status from this preparation environment |

Run `python -m unittest discover -s tests -p test_core.py -v` for dependency-free tests. The complete suite fails on dependency/import errors instead of silently skipping integration. `python scripts/verify.py` also rejects any skipped tests. GitHub Actions runs this verification on Python 3.11 and 3.13 and retains its actual evidence as downloadable artifacts. Do not count the MCP-only demo as proof of model routing. See the validation file for what was actually executed.

## Submission

Submit this source folder or a repository containing it, plus the reading summary and reflection. The repository link is provided above. The original brief also requires a 5-7 minute screencast. The video is intentionally omitted per your request; use the guide if your instructor still requires it. Review the reflection in your own voice and use the live verification evidence before claiming a complete model demonstration. The Free local LLM verification workflow also performs this check on a standard Linux runner in this public repository, without any API secret. The separate paid-OpenAI workflow is optional and requires explicit selection.

References: [FastMCP tools](https://gofastmcp.com/servers/tools), [OpenAI Agents SDK MCP](https://openai.github.io/openai-agents-python/mcp/), and sources in the reading summary.
