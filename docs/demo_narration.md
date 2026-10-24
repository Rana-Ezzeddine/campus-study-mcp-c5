# Caption transcript — silent submission video

0:00:00.00–0:00:08.00  A fictional campus room assistant: inspect availability, reserve a room, or coordinate both steps.

0:00:08.00–0:00:17.00  The catalog is local demonstration data, not real AUB facilities or a campus booking service.

0:00:17.00–0:00:26.00  Bookings last one hour in Beirut time. The model runs locally without a paid API key.

0:00:26.00–0:00:36.00  The data tool reads availability and creates no reservation.

0:00:36.00–0:00:46.00  The action tool changes persistent state by booking the exact requested room.

0:00:46.00–0:00:56.00  The orchestration tool combines the same search and reservation implementations into one goal.

0:00:56.00–0:01:05.00  The host coordinates model interaction. Its MCP client discovers the server’s typed tools.

0:01:05.00–0:01:15.00  A natural-language request becomes a model-selected tool call sent over the stdio connection.

0:01:15.00–0:01:24.00  FastMCP validates and executes the call; the result returns through the client to the host.

0:01:24.00–0:01:35.00  Descriptions explain purpose and effects. Typed inputs constrain dates, hours, group sizes and operation IDs.

0:01:35.00–0:01:46.00  Both preference-taking tools require quiet_only explicitly. A catalog resource does not add a fourth tool.

0:01:46.00–0:02:00.00  Real screen recording • original timing and Mac cursor retained. The buttons send natural- language requests.

0:02:00.00–0:02:09.00  DATA: search_rooms receives party_size=2 and quiet_only=true, then returns matching rooms.

0:02:09.00–0:02:12.00  The result lists CEDAR-2 and OLIVE-4. The host confirms that no reservation was created.

0:02:12.00–0:02:28.00  ACTION: the user requests CEDAR-2 for Rana. The local model chooses reserve_room.

0:02:28.00–0:02:37.00  The confirmation includes the exact room, time and reservation ID. The actual MCP trace is expanded.

0:02:37.00–0:02:57.00  ORCHESTRATION: find and book a quiet room for Rana, three people, at the same hour.

0:02:57.00–0:03:13.47  find_and_reserve selects OLIVE-4 and saves the booking. Its result records search_rooms → reserve_room.

0:03:13.47–0:03:24.47  find_and_reserve first calls search_rooms, then calls reserve_room for a matching candidate.

0:03:24.47–0:03:35.47  It chooses the smallest suitable room and can try the next match after a competing booking.

0:03:35.47–0:03:46.47  Room-and-time uniqueness prevents double booking. An identical operation retry returns its original reservation.

0:03:46.47–0:03:57.47  The action rechecks capacity and availability. A no-match orchestration returns a clear error without a write.

0:03:57.47–0:04:08.47  Earlier tests checked routing and saved state but did not fully check arguments or displayed claims.

0:04:08.47–0:04:19.47  The fix checks both. Displayed answers come from validated receipts, not unverified model- written prose.

0:04:19.47–0:04:28.47  The suite covers core logic, failures, concurrency, real MCP communication and SDK Runner integration.

0:04:28.47–0:04:37.47  The SDK unit test uses a scripted model. Separate live checks use the real local Qwen2.5 3B model.

0:04:37.47–0:04:45.47  All three real-model checks passed, including exact arguments, factual presentation and database state.

0:04:45.47–0:04:55.47  Three tools are enough for this focused task. Shared core functions avoid duplicated behavior.

0:04:55.47–0:05:05.47  This is a local educational demonstration. Real deployment would require identities, authorization and live data.

0:05:05.47–0:05:17.47  The repository contains the FastMCP server, SDK host/client, setup instructions, tests and written deliverables.
