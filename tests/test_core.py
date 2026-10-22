"""Run without third-party dependencies: python -m unittest discover -s tests -v."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from campus_toolkit.core import DomainError, Toolkit, TZ


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "bookings.sqlite3"
        self.app = Toolkit(self.path, now=lambda: datetime(2030, 1, 1, 9, tzinfo=TZ))
        self.day = "2030-01-02"

    def reserve(self, request="a", **kw):
        args = dict(room_id="CEDAR-2", day=self.day, hour=10, party_size=2,
                    student_name="Rana", request_id=request)
        return self.app.reserve_room(**(args | kw))

    def count(self):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT count(*) FROM reservations").fetchone()[0]

    def test_data_read_only_and_sorted(self):
        before = self.path.read_bytes()
        result = self.app.search_rooms(self.day, 10, 2, True)
        self.assertEqual([r.room_id for r in result.rooms], ["CEDAR-2", "OLIVE-4"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.count(), 0)

    def test_data_empty_is_valid(self):
        self.assertEqual(self.app.search_rooms(self.day, 10, 6, True).rooms, [])

    def test_invalid_inputs(self):
        for day, hour, size, error in [
            ("bad", 10, 2, "INVALID_DATE"), ("2030-02-30", 10, 2, "INVALID_DATE"),
            (self.day, 20, 2, "INVALID_HOUR"), (self.day, 10, 0, "INVALID_PARTY_SIZE"),
            ("2029-12-31", 10, 2, "INVALID_SLOT"), ("2030-02-02", 10, 2, "INVALID_SLOT"),
            ("2030-01-01", 9, 2, "INVALID_SLOT"), (self.day, True, 2, "INVALID_HOUR")]:
            with self.subTest(error=error, day=day), self.assertRaisesRegex(DomainError, error):
                self.app.search_rooms(day, hour, size)

    def test_action_persists_across_restart(self):
        saved = self.reserve()
        restarted = Toolkit(self.path, self.app.now)
        self.assertEqual(restarted.reserve_room("CEDAR-2", self.day, 10, 2, "Rana", "a"), saved)
        self.assertNotIn("CEDAR-2", [r.room_id for r in restarted.search_rooms(self.day, 10, 2).rooms])

    def test_unknown_room_capacity_name_and_request(self):
        for kw, error in [({"room_id": "X"}, "ROOM_NOT_FOUND"),
                          ({"party_size": 3}, "CAPACITY_EXCEEDED"),
                          ({"student_name": " "}, "INVALID_NAME"),
                          ({"request_id": "bad id"}, "INVALID_REQUEST_ID")]:
            with self.subTest(kw=kw), self.assertRaisesRegex(DomainError, error):
                self.reserve(**kw)
        self.assertEqual(self.count(), 0)

    def test_slot_conflict_has_no_second_write(self):
        self.reserve()
        with self.assertRaisesRegex(DomainError, "SLOT_UNAVAILABLE"):
            self.reserve("b")
        self.assertEqual(self.count(), 1)

    def test_idempotency_and_changed_request(self):
        self.assertEqual(self.reserve(), self.reserve())
        with self.assertRaisesRegex(DomainError, "REQUEST_ID_CONFLICT"):
            self.reserve(hour=11)
        self.assertEqual(self.count(), 1)

    def test_orchestration_invokes_both_capabilities(self):
        with patch.object(self.app, "search_rooms", wraps=self.app.search_rooms) as data, \
             patch.object(self.app, "reserve_room", wraps=self.app.reserve_room) as action:
            plan = self.app.find_and_reserve(self.day, 10, 3, "Rana", "plan", True)
            data.assert_called_once_with(self.day, 10, 3, True)
            action.assert_called_once()
        self.assertEqual(plan.reservation.room_id, "OLIVE-4")
        self.assertEqual(plan.steps, ["search_rooms", "reserve_room"])
        self.assertEqual(self.count(), 1)

    def test_plan_replay_does_not_book_a_different_room(self):
        first = self.app.find_and_reserve(self.day, 10, 2, "Rana", "plan")
        second = self.app.find_and_reserve(self.day, 10, 2, "Rana", "plan")
        self.assertEqual(first.reservation, second.reservation)
        self.assertEqual(self.count(), 1)
        with self.assertRaisesRegex(DomainError, "REQUEST_ID_CONFLICT"):
            self.app.find_and_reserve(self.day, 11, 2, "Rana", "plan")

    def test_no_match_no_write(self):
        with self.assertRaisesRegex(DomainError, "NO_MATCHING_ROOM"):
            self.app.find_and_reserve(self.day, 10, 6, "Rana", "plan", True)
        self.assertEqual(self.count(), 0)

    def test_orchestration_recovers_from_race(self):
        real_reserve = self.app.reserve_room
        def raced(room_id, *args, **kwargs):
            if room_id == "CEDAR-2":
                raise DomainError("SLOT_UNAVAILABLE: simulated competing reservation.")
            return real_reserve(room_id, *args, **kwargs)
        with patch.object(self.app, "reserve_room", side_effect=raced):
            plan = self.app.find_and_reserve(self.day, 10, 2, "Rana", "race")
        self.assertEqual(plan.reservation.room_id, "OLIVE-4")
        self.assertEqual(self.count(), 1)

    def test_concurrent_writers_cannot_double_book(self):
        def attempt(i):
            try:
                return self.reserve(f"request-{i}").reservation_id
            except DomainError as error:
                return str(error)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(attempt, range(4)))
        self.assertEqual(sum("SLOT_UNAVAILABLE" in x for x in results), 3)
        self.assertEqual(self.count(), 1)


if __name__ == "__main__":
    unittest.main()
