# Validation record

Verified October 24, 2026. Tested code commit: eb77975cfd0ecc54b2355943bc51499df8189db5.

- Integration suite: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5/actions/runs/40095974780
- Real free-model verification: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5/actions/runs/40095974824
- Repository: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5

## Actual results

| Check | Result |
|---|---|
| Complete suite on Python 3.11 and 3.13 | 19 tests passed on each, zero skips |
| MCP discovery | Exactly search_rooms, reserve_room and find_and_reserve |
| Required preference | Both SDK and server reject omitted quiet_only |
| Real Qwen2.5 3B tool selection | All three tools selected and executed |
| Live arguments | Expected date, hour, party size, name, room ID and quiet preference checked |
| Live lookup constraints | Only CEDAR-2 and OLIVE-4 for the quiet query |
| Factual presentation | Displayed answers rendered from validated MCP receipts |
| Reservation state | Exact expected room reservations checked after each request |
| Conversation history | Discarded model narratives excluded from subsequent turns |

The real-model run uses local Ollama through the OpenAI Agents SDK and FastMCP. It has no forced tool_choice and uses no scripted model for its decisions. The separate SDK regression test uses an explicitly scripted model to inject fabricated prose and confirm that the host discards it. No paid model API or API key was used.

## Fix for the reported issue

Both preference-taking MCP tools now require an explicit strict boolean quiet_only; there is no silent default. Descriptions specify true for quiet requests and false when either room type is acceptable.

The LLM still selects tools and supplies arguments. The host correlates each output with its call ID, validates typed contents against the call arguments and renders the displayed answer from those facts. Inconsistent output produces an unverified-result warning rather than a booking confirmation. Raw model narratives are neither displayed nor reused in conversation history. No fourth MCP tool was added.

The stronger live check validates all expected argument values, result constraints, displayed-answer regression conditions and database state. The latest output explicitly includes quiet_only=true for both quiet requests. It contains no invented six-person availability claim.

The new regressions inject that historical false claim and confirm it reaches neither displayed answers nor later history. Other cases reject inconsistent slots, non-quiet rooms in quiet-only results, undersized rooms and mismatched reservation results.

## Actual retained evidence

- test-output.txt: latest real test runner output without GitHub timestamp prefixes.
- ci-python313-log.txt and ci-jobs.json: integration job log and both job results.
- mcp-demo-output.txt: actual protocol demonstration.
- live-agent-output.txt: actual latest model prompts, calls, outputs, factual summaries and checks.
- free-live-ci-log.txt and free-live-jobs.json: complete actual live-model log and status.
- installed-requirements.txt: resolved packages from the successful integration job.
- free-llm-first-attempt.txt: historical failed development attempt, not passing evidence.

Earlier failed runs remain visible. During this fix, a test initially expected an omitted argument to return an MCP error while the SDK correctly rejected it before transmission. The corrected test verifies that SDK exception and separately tests the server through its session. Both subsequent workflows passed.

## Scope and remaining submission work

The successful live run demonstrates these three scenarios, not perfect interpretation of every possible natural-language request. Required fields cannot guarantee semantic correctness on unseen prompts; the stronger checks detect the reported argument regressions. Displayed claims are constrained to verified receipts.

The summary remains 371 words and the reflection remains two paragraphs. The user still needs to rehearse locally and record the required 5-7 minute screencast unless the instructor waives it. The video is omitted per the user's instruction. No grade is guaranteed.
