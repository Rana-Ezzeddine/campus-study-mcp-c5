# Validation record

Verified October 22, 2026, using actual GitHub Actions execution.

- Repository: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5
- Successful run: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5/actions/runs/39840397595
- Tested source commit: `66ec8633667d31408e3b7f9cb5bbb149757b132d`

## Executed and passed

| Check | Actual result |
|---|---|
| Complete test suite, Python 3.11 | 14 tests passed; zero skips |
| Complete test suite, Python 3.13 | 14 tests passed; zero skips |
| Real FastMCP subprocess discovery | Exactly search_rooms, reserve_room and find_and_reserve |
| Real stdio MCP calls | All three tools executed successfully |
| Resource access | campus://catalog returned fictional catalog |
| Error propagation | Malformed date, occupied slot and no-match returned MCP errors |
| Persistent action and replay | Reservation persisted; identical retry returned the existing reservation |
| Agents SDK Runner round trip | Three scripted model tool calls executed through real MCP and returned to the model |
| MCP-only terminal demonstration | Executed successfully; real output retained |

The Runner check uses a clearly labeled scripted model. It verifies SDK tool discovery, execution and result feedback, not natural-language tool selection by a real LLM. `campus_toolkit.live_demo` is the separate real-model check.

## Actual evidence retained

- `ci-jobs.json`: GitHub's job and step results for both Python versions.
- `ci-python313-log.txt`: complete actual Python 3.13 job log.
- `test-output.txt`: the actual test runner output extracted from that log, without GitHub timestamp prefixes.
- `mcp-demo-output.txt`: the actual MCP demonstration output extracted from the same log.
- `installed-requirements.txt`: exact pip-freeze entries from that job.

The same run's downloadable workflow artifacts retain the original evidence files from each runner. These local text extracts do not fabricate or replace any model response.

## Fixes made after real execution

The first run failed because the current MCP 2 SDK uses Python attributes `output_schema`, `is_error` and `structured_content`, while the initial tests expected older camelCase names. The tests now use the current API. The broad ImportError skip was removed: dependency/import failures now fail the suite. The verification script also rejects all skipped tests.

Direct dependencies are pinned to the versions actually resolved in the real run: FastMCP 4.1.3, OpenAI Agents SDK 0.24.0, MCP 2.3.0 and python-dotenv 1.2.4. Both Python versions passed with those pins. The first failed run remains visible in repository history; subsequent verified runs passed.

## Live language-model verification (free)

Verified run: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5/actions/runs/39845692818

Source commit: `636e66417931c2796746147dd8f081c16260112f`.

A real Qwen2.5 3B model ran locally through Ollama on a standard GitHub Linux runner. It selected and executed search_rooms, reserve_room and find_and_reserve from three natural-language requests. The check verified the tool names and database state after every request. All three routing checks passed; the complete 14-test suite also passed. No OpenAI API key or paid model endpoint was used. The OpenAI Agents SDK and FastMCP remained the host framework and server implementation.

`live-agent-output.txt` retains actual prompts, model-selected calls, MCP results and model answers. The output is extracted from the original CI log without its timestamp prefixes. `free-live-ci-log.txt` retains that full log; the workflow artifacts preserve the original verification files.

The first local-model attempt selected orchestration for a named-room booking. Clarifying the mutually exclusive tool descriptions and host instructions corrected this in the successful run. The failed attempt is retained in `free-llm-first-attempt.txt`; it is not presented as passing evidence.

### Scope and observed limitation

This establishes real model tool selection for the three demonstrated scenarios, not guaranteed correctness for every future prompt. In the successful lookup, the small model omitted quiet_only, then filtered the returned quiet flags in its answer. It also added an unsupported sentence about six-person availability. The routing test does not grade every sentence of the model answer. A production host should validate result summaries or use a stronger local model. The recorded output is left intact.

### Running without payment

Start Ollama, pull qwen2.5:3b, then run `python scripts/verify.py --live`. The default configuration uses a local endpoint and needs no API credential. See `docs/free_model_setup.md`.

The video remains omitted per the user's request. C5 still lists a 5-7 minute screencast. The 371-word reading summary and reference-server source review are included. No grade is guaranteed.
