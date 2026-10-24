"""Regression tests for unsupported availability claims and mismatched receipts."""
from types import SimpleNamespace
import unittest

from campus_toolkit.presentation import ReceiptError, present, render, validate_receipt


ARGS = dict(day="2030-01-02", hour=10, party_size=2, quiet_only=True)
DATA = dict(day="2030-01-02", hour=10, timezone="Asia/Beirut", duration_minutes=60,
    rooms=[dict(room_id="CEDAR-2", name="Cedar Study Pod", capacity=2, quiet=True)])


class PresentationTests(unittest.TestCase):
    def test_summary_projects_only_verified_fields(self):
        receipt = validate_receipt("search_rooms", ARGS, DATA)
        self.assertEqual(render(receipt),
            "Available quiet rooms for 2 people, 2030-01-02 10:00-11:00 (Asia/Beirut):\n"
            "- Cedar Study Pod (CEDAR-2): 2 seats, quiet.\nNo reservation was created.")

    def test_no_match_does_not_invent_availability(self):
        receipt = validate_receipt("search_rooms", ARGS, DATA | {"rooms": []})
        self.assertIn("No matching rooms", render(receipt))
        self.assertNotIn("6 people", render(receipt))

    def test_bad_preference_and_mismatched_results_are_rejected(self):
        cases = [(ARGS | {"quiet_only": None}, DATA),
                 (ARGS, DATA | {"hour": 11}),
                 (ARGS, DATA | {"rooms": [DATA["rooms"][0] | {"quiet": False}]}),
                 (ARGS, DATA | {"rooms": [DATA["rooms"][0] | {"capacity": 1}]})]
        for arguments, data in cases:
            with self.subTest(data=data), self.assertRaises(ReceiptError):
                validate_receipt("search_rooms", arguments, data)

    def test_unverifiable_action_never_becomes_a_confirmation(self):
        args = dict(room_id="CEDAR-2", day="2030-01-02", hour=10, party_size=2,
                    student_name="Rana", request_id="regression")
        call = SimpleNamespace(type="tool_call_item", raw_item=dict(
            name="reserve_room", call_id="x", arguments=__import__('json').dumps(args)))
        output = SimpleNamespace(type="tool_call_output_item", raw_item={"call_id": "x"},
            output={"reservation_id": "r", "room_id": "OLIVE-4", "day": "2030-01-02",
                    "hour": 10, "party_size": 2, "student_name": "Rana"})
        sdk = SimpleNamespace(new_items=[call, output], final_output="Successfully booked CEDAR-2!")
        result = present(sdk)
        self.assertIn("RESULT_UNVERIFIED", result.final_output)
        self.assertNotIn("Reserved", result.final_output)

    def test_no_tool_receipt_does_not_repeat_a_model_claim(self):
        result = present(SimpleNamespace(new_items=[], final_output="All rooms are booked!"))
        self.assertIn("Please provide", result.final_output)
        self.assertNotIn("All rooms are booked", result.final_output)
