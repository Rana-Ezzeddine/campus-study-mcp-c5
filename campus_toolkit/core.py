"""Dependency-free domain logic. Only reserve_room writes reservation state."""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
import json
import re
import sqlite3
from typing import Callable
from uuid import uuid4
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Beirut")


class DomainError(ValueError):
    """A stable CODE: explanation that can be exposed to an MCP caller."""


@dataclass(frozen=True)
class Room:
    room_id: str
    name: str
    capacity: int
    quiet: bool


ROOMS = (
    Room("CEDAR-2", "Cedar Study Pod", 2, True),
    Room("OLIVE-4", "Olive Study Room", 4, True),
    Room("SEA-6", "Sea View Collaboration Room", 6, False),
)


@dataclass(frozen=True)
class SearchResult:
    day: str
    hour: int
    timezone: str
    duration_minutes: int
    rooms: list[Room]


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    room_id: str
    day: str
    hour: int
    party_size: int
    student_name: str
    timezone: str = "Asia/Beirut"
    duration_minutes: int = 60


@dataclass(frozen=True)
class PlanResult:
    reservation: Reservation
    selection_reason: str
    steps: list[str]


class Toolkit:
    def __init__(self, db_path: Path, now: Callable[[], datetime] | None = None):
        self.db_path = Path(db_path)
        self.now = now or (lambda: datetime.now(TZ))
        # Startup initialization is separate from the read-only data tool.
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                room_id TEXT NOT NULL, day TEXT NOT NULL, hour INTEGER NOT NULL,
                party_size INTEGER NOT NULL, student_name TEXT NOT NULL,
                request_id TEXT NOT NULL UNIQUE, fingerprint TEXT NOT NULL,
                UNIQUE(room_id, day, hour))""")

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db_path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def validate_slot(self, day: str, hour: int, party_size: int) -> None:
        try:
            parsed = date.fromisoformat(day)
            if parsed.isoformat() != day:
                raise ValueError
        except (ValueError, TypeError):
            raise DomainError("INVALID_DATE: use YYYY-MM-DD.") from None
        if type(hour) is not int or not 8 <= hour <= 19:
            raise DomainError("INVALID_HOUR: choose an integer from 8 to 19 (Beirut time).")
        if type(party_size) is not int or not 1 <= party_size <= 6:
            raise DomainError("INVALID_PARTY_SIZE: choose an integer from 1 to 6.")
        now = self.now().astimezone(TZ)
        start = datetime.combine(parsed, time(hour), tzinfo=TZ)
        if start <= now or parsed > now.date() + timedelta(days=30):
            raise DomainError("INVALID_SLOT: choose a future hour within the next 30 days.")

    @staticmethod
    def identity(student_name: str, request_id: str) -> str:
        name = student_name.strip()
        if not 1 <= len(name) <= 80 or any(ord(c) < 32 for c in name):
            raise DomainError("INVALID_NAME: provide 1-80 printable characters.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request_id):
            raise DomainError("INVALID_REQUEST_ID: use 1-64 letters, digits, underscores or hyphens.")
        return name

    @staticmethod
    def fingerprint(kind: str, **kwargs: object) -> str:
        return json.dumps({"kind": kind, **kwargs}, sort_keys=True)

    @staticmethod
    def from_row(row: sqlite3.Row) -> Reservation:
        return Reservation(**{key: row[key] for key in (
            "reservation_id", "room_id", "day", "hour", "party_size", "student_name")})

    def replay(self, db: sqlite3.Connection, request_id: str,
               fingerprint: str) -> Reservation | None:
        row = db.execute("SELECT * FROM reservations WHERE request_id = ?", (request_id,)).fetchone()
        if row is None:
            return None
        if row["fingerprint"] != fingerprint:
            raise DomainError("REQUEST_ID_CONFLICT: use a new request_id for a different request.")
        return self.from_row(row)

    def search_rooms(self, day: str, hour: int, party_size: int,
                     quiet_only: bool = False) -> SearchResult:
        """Data capability: inspect one-hour availability; never writes."""
        self.validate_slot(day, hour, party_size)
        if type(quiet_only) is not bool:
            raise DomainError("INVALID_QUIET: quiet_only must be a boolean.")
        with closing(self.connect()) as db:
            booked = {r[0] for r in db.execute(
                "SELECT room_id FROM reservations WHERE day=? AND hour=?", (day, hour))}
        rooms = [r for r in ROOMS if r.capacity >= party_size and
                 (not quiet_only or r.quiet) and r.room_id not in booked]
        return SearchResult(day, hour, "Asia/Beirut", 60, sorted(rooms, key=lambda r: (r.capacity, r.room_id)))

    def reserve_room(self, room_id: str, day: str, hour: int, party_size: int,
                     student_name: str, request_id: str,
                     *, workflow_fingerprint: str | None = None) -> Reservation:
        """Action capability: commit exactly one local SQLite reservation.

        The keyword-only fingerprint is private to orchestration, never an MCP input.
        BEGIN IMMEDIATE + a unique slot constraint prevent double booking.
        """
        name = self.identity(student_name, request_id)
        fingerprint = workflow_fingerprint or self.fingerprint(
            "reserve", room_id=room_id, day=day, hour=hour,
            party_size=party_size, student_name=name)
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            old = self.replay(db, request_id, fingerprint)
            if old:
                return old
            self.validate_slot(day, hour, party_size)
            room = next((r for r in ROOMS if r.room_id == room_id), None)
            if room is None:
                raise DomainError("ROOM_NOT_FOUND: use a room_id returned by search_rooms.")
            if party_size > room.capacity:
                raise DomainError("CAPACITY_EXCEEDED: choose a larger room.")
            reservation = Reservation(str(uuid4()), room_id, day, hour, party_size, name)
            try:
                db.execute("INSERT INTO reservations VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                    reservation.reservation_id, room_id, day, hour, party_size, name,
                    request_id, fingerprint))
            except sqlite3.IntegrityError:
                raise DomainError("SLOT_UNAVAILABLE: room was booked; search again or choose another hour.") from None
            return reservation

    def find_and_reserve(self, day: str, hour: int, party_size: int,
                         student_name: str, request_id: str,
                         quiet_only: bool = False) -> PlanResult:
        """Orchestration: invoke the data capability, then the action capability."""
        name = self.identity(student_name, request_id)
        if type(quiet_only) is not bool:
            raise DomainError("INVALID_QUIET: quiet_only must be a boolean.")
        fingerprint = self.fingerprint("plan", day=day, hour=hour,
            party_size=party_size, student_name=name, quiet_only=quiet_only)
        with closing(self.connect()) as db:
            old = self.replay(db, request_id, fingerprint)
        if old:
            return PlanResult(old, "Existing result for this request_id.", ["idempotency replay"])
        found = self.search_rooms(day, hour, party_size, quiet_only)
        for room in found.rooms:
            try:
                saved = self.reserve_room(room.room_id, day, hour, party_size, name,
                    request_id, workflow_fingerprint=fingerprint)
                return PlanResult(saved, "Smallest available room meeting your constraints.",
                                  ["search_rooms", "reserve_room"])
            except DomainError as exc:
                if not str(exc).startswith("SLOT_UNAVAILABLE:"):
                    raise
                # Another caller won this room: try the next match, not a duplicate write.
        raise DomainError("NO_MATCHING_ROOM: no room meets the constraints; try another hour or fewer people.")
