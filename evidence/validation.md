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

## Remaining external steps

- **Live OpenAI LLM routing has not run.** No OPENAI_API_KEY is configured in this task environment. The source, SDK Runner wiring and MCP transport have been tested, but no real model decision is claimed.
- The video is omitted per the user's instruction. C5 still lists a 5-7 minute screencast as a deliverable.

To capture real model evidence, configure your API key locally in `.env`, then run:

```bash
python scripts/verify.py --live
```

Alternatively, configure an OPENAI_API_KEY repository secret yourself and run the manual Live OpenAI agent verification workflow. Do not place a credential in source or chat. API calls use your account's API credit.

The 371-word reading summary and reference-server source review are also included. The reference filesystem server was inspected but not executed. No grade is guaranteed.
