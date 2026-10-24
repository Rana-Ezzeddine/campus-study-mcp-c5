"""Validate MCP receipts and render user-visible facts without model-written claims.

This module does not choose tools or infer preferences from user text. The LLM
still supplies tool names and arguments. Only verified server results are shown.
"""
from dataclasses import asdict, dataclass
import json
from typing import Any

from pydantic import TypeAdapter
from .core import PlanResult, Reservation, SearchResult, ROOMS


class ReceiptError(ValueError):
    pass


def field(item: Any, name: str):
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


def payload(value: Any) -> dict:
    """Decode SDK text blocks; never treat arbitrary model text as tool data."""
    if isinstance(value, str):
        try:
            return payload(json.loads(value))
        except (json.JSONDecodeError, RecursionError):
            raise ReceiptError(value) from None
    if isinstance(value, list) and len(value) == 1:
        return payload(value[0])
    if isinstance(value, dict):
        if value.get("type") == "text":
            return payload(value.get("text"))
        if any(key in value for key in ("rooms", "reservation_id", "reservation")):
            return value
    raise ReceiptError("Unrecognized MCP output format.")


@dataclass
class Receipt:
    tool: str
    arguments: dict
    data: dict | None
    error: str | None = None


def validate_receipt(tool: str, arguments: dict, output: Any) -> Receipt:
    types = {"search_rooms": SearchResult, "reserve_room": Reservation,
             "find_and_reserve": PlanResult}
    if tool not in types:
        raise ReceiptError("Unknown tool in receipt.")
    data = asdict(TypeAdapter(types[tool]).validate_python(payload(output)))
    booking = data.get("reservation", data)
    for name in ("day", "hour"):
        if booking[name] != arguments[name]:
            raise ReceiptError("Returned slot differs from the requested slot.")
    if booking["timezone"] != "Asia/Beirut" or booking["duration_minutes"] != 60:
        raise ReceiptError("Unexpected booking timezone or duration.")
    if tool == "search_rooms":
        if type(arguments.get("quiet_only")) is not bool:
            raise ReceiptError("The quiet_only preference must be explicit.")
        for room in data["rooms"]:
            if room["capacity"] < arguments["party_size"]:
                raise ReceiptError("Room does not satisfy the party size.")
            if arguments["quiet_only"] and not room["quiet"]:
                raise ReceiptError("A non-quiet room was returned for a quiet-only query.")
    else:
        for name in ("party_size", "student_name"):
            if booking[name] != arguments[name]:
                raise ReceiptError("Returned reservation differs from the request.")
        if tool == "reserve_room" and booking["room_id"] != arguments["room_id"]:
            raise ReceiptError("A different room was reserved.")
        if tool == "find_and_reserve" and type(arguments.get("quiet_only")) is not bool:
            raise ReceiptError("The quiet_only preference must be explicit.")
        room = next((r for r in ROOMS if r.room_id == booking["room_id"]), None)
        if room is None or room.capacity < arguments["party_size"]:
            raise ReceiptError("Reserved room does not meet the party size.")
        if arguments.get("quiet_only") and not room.quiet:
            raise ReceiptError("Reserved room does not satisfy the quiet preference.")
    return Receipt(tool, arguments, data)


def render(receipt: Receipt) -> str:
    """A fixed factual projection: no capacity, availability or ID is invented."""
    if receipt.error:
        return "Tool error: " + receipt.error
    data = receipt.data
    booking = data.get("reservation", data)
    slot = (f"{booking['day']} {booking['hour']:02d}:00-"
            f"{booking['hour'] + 1:02d}:00 ({booking['timezone']})")
    if receipt.tool == "search_rooms":
        qualifier = "quiet " if receipt.arguments["quiet_only"] else ""
        heading = f"Available {qualifier}rooms for {receipt.arguments['party_size']} people, {slot}:"
        if not data["rooms"]:
            return heading + "\nNo matching rooms. No reservation was created."
        rows = [f"- {r['name']} ({r['room_id']}): {r['capacity']} seats, "
                f"{'quiet' if r['quiet'] else 'collaborative'}." for r in data["rooms"]]
        return "\n".join([heading, *rows, "No reservation was created."])
    text = (f"Reserved {booking['room_id']} for {booking['student_name']}, "
            f"{booking['party_size']} people, {slot}.\n"
            f"Reservation ID: {booking['reservation_id']}.")
    if receipt.tool == "find_and_reserve":
        text += "\nSelection: " + data["selection_reason"]
    return text


@dataclass
class PresentedTurn:
    sdk_result: Any
    receipts: list[Receipt]
    final_output: str

    @property
    def new_items(self):
        return self.sdk_result.new_items

    def to_input_list(self):
        # Do not feed discarded model narratives back into the next turn.
        history = [item for item in self.sdk_result.to_input_list()
                   if not (field(item, "role") == "assistant" and
                           field(item, "type") in (None, "message"))]
        return history + [{"role": "assistant", "content": self.final_output}]


def present(result: Any) -> PresentedTurn:
    calls = {}
    receipts = []
    for item in result.new_items:
        if item.type == "tool_call_item":
            raw = item.raw_item
            calls[field(raw, "call_id")] = (field(raw, "name"), json.loads(field(raw, "arguments")))
        elif item.type == "tool_call_output_item":
            call_id = field(item.raw_item, "call_id")
            if call_id not in calls:
                raise ReceiptError("Tool output has no matching call.")
            name, arguments = calls[call_id]
            try:
                receipts.append(validate_receipt(name, arguments, item.output))
            except (ValueError, KeyError, TypeError) as error:
                # Preserve explicit server error codes, but never confirm unverifiable writes.
                message = str(error)
                if not (message.split(":", 1)[0].isupper() and ":" in message):
                    message = ("RESULT_UNVERIFIED: the tool ran but its result could not be verified. "
                               "Check existing bookings before retrying a reservation.")
                receipts.append(Receipt(name, arguments, None, message))
    text = "\n\n".join(render(r) for r in receipts) if receipts else (
        "Please provide the date, start hour, party size and whether you need a quiet room. "
        "For a booking, include your name and any specific room ID.")
    return PresentedTurn(result, receipts, text)
