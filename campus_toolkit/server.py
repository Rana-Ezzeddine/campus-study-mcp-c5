"""FastMCP adapter: exactly three registered tools, one optional data resource."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Iterator

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .core import DomainError, PlanResult, Reservation, ROOMS, SearchResult, Toolkit

ROOT = Path(__file__).resolve().parents[1]
Day = Annotated[str, Field(description="Booking date as YYYY-MM-DD; future, within 30 days.")]
Hour = Annotated[int, Field(ge=8, le=19, description="Start hour in Asia/Beirut; one-hour booking.")]
Size = Annotated[int, Field(ge=1, le=6, description="Number of people.")]
Name = Annotated[str, Field(min_length=1, max_length=80, description="Student name supplied by the user.")]
Request = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$", description="Unique operation ID; reuse unchanged on retry.")]


@contextmanager
def exposed_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as exc:
        raise ToolError(str(exc)) from None
    except sqlite3.Error:
        raise ToolError("STORAGE_UNAVAILABLE: reservation database cannot be accessed; retry later.") from None


def create_server(db_path: Path | None = None) -> FastMCP:
    service = Toolkit(db_path or Path(os.getenv("CAMPUS_DB_PATH", str(ROOT / "runtime/bookings.sqlite3"))))
    mcp = FastMCP("Campus Study Toolkit")

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def search_rooms(day: Day, hour: Hour, party_size: Size,
                     quiet_only: bool = False) -> SearchResult:
        """DATA: Look up available fictional campus rooms for one hour. No reservation is created.
        Results are ordered by capacity then ID. Empty rooms means no match.
        Invalid or past dates produce a clear error. Use before a specific-room reservation.
        """
        with exposed_errors():
            return service.search_rooms(day, hour, party_size, quiet_only)

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False,
                            "idempotentHint": True, "openWorldHint": False})
    def reserve_room(room_id: Annotated[str, Field(description="Exact room ID from search_rooms.")],
                     day: Day, hour: Hour, party_size: Size, student_name: Name,
                     request_id: Request) -> Reservation:
        """ACTION: Persist one reservation in the local demo database. Only use on an explicit booking request.
        Returns a reservation ID after commit. Identical request_id retries return the same reservation;
        changed inputs with that ID fail. Unknown rooms, insufficient capacity and occupied slots fail.
        This does not book any real university room.
        """
        with exposed_errors():
            return service.reserve_room(room_id, day, hour, party_size, student_name, request_id)

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False,
                            "idempotentHint": True, "openWorldHint": False})
    def find_and_reserve(day: Day, hour: Hour, party_size: Size,
                         student_name: Name, request_id: Request,
                         quiet_only: bool = False) -> PlanResult:
        """ORCHESTRATION: Fulfill an explicit request to find and book a suitable fictional study room.
        Calls search_rooms logic then reserve_room logic, choosing the smallest available match.
        Returns the reservation, reason and steps. No match raises NO_MATCHING_ROOM with no write.
        Reuse the request_id only for identical retries. Do not call for availability-only questions.
        """
        with exposed_errors():
            return service.find_and_reserve(day, hour, party_size, student_name, request_id, quiet_only)

    @mcp.resource("campus://catalog", mime_type="application/json")
    def catalog() -> dict:
        """Static fictional room catalog; not live availability and not a fourth tool."""
        return {"fictional": True, "timezone": "Asia/Beirut", "duration_minutes": 60,
                "rooms": [asdict(r) for r in ROOMS]}

    return mcp


if __name__ == "__main__":
    create_server().run(transport="stdio")
