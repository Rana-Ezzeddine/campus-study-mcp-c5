# 5–7 minute demonstration guide

A real 1:27 three-tool screen recording is available: https://drive.google.com/file/d/1-6kNFAOYEox10yscdkUFsxriu9GgYd8s/view?usp=drivesdk. All three tools succeed and their MCP calls/results are expanded. Keep this clip. Add approximately four minutes introducing the project, explaining the architecture, showing the source and tests, and discussing challenges. The combined recording should be 5–7 minutes. `demo_narration.md` supplies a draft for the additional explanation.

## Before recording

Install requirements, run all tests with no skips, start Ollama, pull `qwen2.5:3b`, and run `python -m campus_toolkit.live_demo` once to check your model access. The default local-model mode needs no API key and makes no paid API calls. Both scripted demos use fresh temporary databases.

## Recording outline (approximately 6 minutes)

| Time | Show | Explain |
|---|---|---|
| 0:00-0:45 | README tool table | Fictional campus theme; name Data, Action and Orchestration tools |
| 0:45-1:30 | `server.py`, then `agent.py` | Exactly three decorators; host/client/server roles; stdio subprocess |
| 1:30-3:30 | `python -m campus_toolkit.live_demo` | Natural-language requests; actual MCP CALL and MCP RESULT output; all three routing, argument, result-constraint and factual-presentation checks |
| 3:30-4:20 | `python -m campus_toolkit.demo` | Occupied slot error and identical request replay; distinguish client script from model routing |
| 4:20-5:15 | `python -m unittest discover -s tests -v` | No skips; no duplicate booking; failure coverage; real transport test |
| 5:15-6:00 | `core.py` and reflection | Shared implementations, race handling, persistent action, limitations and next steps |

Explain the full round trip: user prompt -> host model -> SDK MCP client -> FastMCP server -> SQLite/catalog -> MCP result -> model answer. The printed SDK items are real run evidence, not illustrative screenshots. The orchestration's internal two calls are domain calls, not two extra host MCP calls.

## Submission checklist

- [ ] Read and understand the code, summary and reflection; adapt the reflection to your own experience.
- [x] Retain the dependency versions resolved during real CI verification.
- [x] Run all tests, including transport and SDK Runner: 19 passed, zero skips, Python 3.11 and 3.13.
- [x] Run both demos and retain actual output, including real local-model routing for all three tools.
- [x] Publish source without `.env` or runtime databases: repository link below.
- [ ] Include the 300-400 word reading summary and two-paragraph reflection.
- [ ] Complete the required 5–7 minute screencast and submit accessible repository and video links.
- [x] Record the real three-tool interaction with expanded MCP calls and results (1:27).

Repository: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5

The current video is a short demonstration, not yet the full required presentation. No grade is guaranteed.
