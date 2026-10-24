# Validation record

Verified October 24, 2026. Tested code commit: `eb77975cfd0ecc54b2355943bc51499df8189db5`.

- Integration suite: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5/actions/runs/40095974780
- Real free-model verification: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5/actions/runs/40095974824
- Repository: https://github.com/Rana-Ezzeddine/campus-study-mcp-c5

## Actual results

| Check | Result |
|---|---|
| Full suite on Python 3.11 and 3.13 | 19 passed on each; zero skips |
| MCP discovery | Exactly search_rooms, reserve_room and find_and_reserve |
| Server and SDK preference validation | Missing quiet_only rejected at both boundaries |
| Real Qwen2.5 3B tool selection | All three tools selected and executed |
| Live input arguments | Exact date, hour, party size, name, room ID and quiet preference checked |
| Live lookup constraints | Only CEDAR-2 and OLIVE-4 returned for the quiet query |
| Displayed answers | Rendered from validated MCP receipts; regression claim absent |
| Action and orchestration state | Exact expected room reservations checked after each request |
| Conversation history | Discarded model narratives excluded from subsequent turns |
| Failure behavior | Invalid inputs, conflicts and inconsistent results cannot silently become success |

The live run uses a real Qwen2.5 3B model through local Ollama and the OpenAI Agents SDK. It has no forced tool_choice and uses no scripted model for its decisions. The separate SDK unit test uses an explicitly scripted model to inject fabricated prose and verify that the host discards it. No paid API or API key was used.

## Fix for the reported issue

Both preference-taking MCP tools now require an explicit strict boolean quiet_only. There is no silent default. Descriptions and host instructions specify true for quiet requests and false when either room type is acceptable.

The LLM still selects tools and supplies arguments. After execution, the host correlates each output with its call ID, validates its typed contents against the call arguments, and renders the user-visible answer from those facts. Invalid or inconsistent output produces an unverified-result warning, not a booking confirmation. Raw model narratives are neither displayed nor reused in conversation history. No fourth MCP tool was added.

The live demo now checks the actual values of every expected argument, output constraints, displayed-answer regression conditions and database state. The latest output explicitly includes quiet_only=true for both quiet requests and contains no invented six-person availability claim.

The 19-test suite includes regressions that inject the historical false claim and confirm that it reaches neither the displayed answer nor subsequent history. Additional cases reject inconsistent slots, non-quiet rooms for quiet-only requests, undersized rooms and mismatched reservation results.

## Retained evidence

- test-output.txt: actual latest test runner output, extracted without GitHub timestamp prefixes.
- ci-python313-log.txt and ci-jobs.json: actual integration job log and both job results.
- mcp-demo-output.txt: actual protocol demonstration.
- live-agent-output.txt: actual latest real-model prompts, calls, outputs, factual summaries and checks.
- free-live-ci-log.txt and free-live-jobs.json: complete actual free-model job log and status.
- installed-requirements.txt: resolved package versions from the successful integration job.
- free-llm-first-attempt.txt: historical failed development attempt; not passing evidence.

Earlier failed runs remain visible in GitHub history. During this fix, a test initially expected a missing argument to return an MCP error while the SDK correctly rejected it before transmission. The corrected test verifies that SDK exception and separately tests the server through its session. Both subsequent workflows passed.

## Scope and remaining submission work

The successful live run proves the demonstrated three scenarios, not perfect interpretation of every possible natural-language request. Required fields do not guarantee semantic correctness on unseen prompts; the stronger live checks detect the specific preference and argument regressions. Displayed factual claims are constrained to verified receipts.

The reading summary remains 371 words and the reflection remains two paragraphs. A 1:27 local screen recording now demonstrates all three successful real-agent calls and expanded MCP results. It remains shorter than the required 5–7 minute screencast. An optional browser interface and detached launcher reproduce the recorded interaction. The browser uses independent complete requests; the original terminal agent retains conversation history. Local Mac verification also passed all 19 tests, the three live checks, and all three browser demo buttons. A subsequent local-server stop was fixed by a detached background launcher and persistent demo database; an orchestration HTTP request and database write passed after that fix. No grade is guaranteed.
