"""
models.py — Core data models for Agent-Based University Scheduling.

Defines immutable value types for time slots, sessions, messages, and enums.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ─── Enumerations ───────────────────────────────────────────────────────────────

class Day(str, Enum):
    MONDAY    = "Monday"
    TUESDAY   = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY  = "Thursday"
    FRIDAY    = "Friday"

    def __str__(self) -> str:
        return self.value


class Period(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"
    P6 = "P6"
    P7 = "P7"
    P8 = "P8"

    def __str__(self) -> str:
        return self.value

    @property
    def index(self) -> int:
        return int(self.value[1]) - 1   # 0-based


class RoomType(str, Enum):
    LECTURE = "Lecture"
    LAB     = "Lab"

    def __str__(self) -> str:
        return self.value


class MsgType(str, Enum):
    CFP       = "CFP"
    BID       = "BID"
    REJECT    = "REJECT"
    AWARD     = "AWARD"
    RELEASE   = "RELEASE"
    ACCEPT    = "ACCEPT"
    NOGOOD    = "NOGOOD"
    BACKTRACK = "BACKTRACK"
    COMMIT    = "COMMIT"
    VALIDATE  = "VALIDATE"

    def __str__(self) -> str:
        return self.value


class AgentState(str, Enum):
    IDLE        = "Idle"
    NEGOTIATING = "Negotiating"
    COMMITTED   = "Committed"
    FAILED      = "Failed"

    def __str__(self) -> str:
        return self.value


# ─── Value Objects ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TimeSlot:
    """An immutable (day, period) pair — the atomic scheduling unit."""
    day: Day
    period: Period

    def __str__(self) -> str:
        return f"{self.day} {self.period}"

    def __repr__(self) -> str:
        return f"TimeSlot({self.day}, {self.period})"


@dataclass
class CourseSession:
    """
    A single scheduled class session owned by one teacher.
    Distinct from a Course — one course may have multiple sessions (lecture + lab).
    """
    session_id:  str
    course_id:   str
    course_name: str
    teacher_id:  str
    enrollment:  int
    room_type:   RoomType
    required_slots: int = 1       # hours / periods needed

    # filled after negotiation
    assigned_slot: Optional[TimeSlot] = None
    assigned_room: Optional[str]      = None
    tentative_slot: Optional[TimeSlot] = None
    tentative_room: Optional[str]      = None
    is_committed:  bool = False
    failed:        bool = False

    def __repr__(self) -> str:
        return (f"<Session {self.session_id} | {self.course_id} | "
                f"teacher={self.teacher_id} | enrolled={self.enrollment} | "
                f"slot={self.assigned_slot} | room={self.assigned_room}>")


# ─── Messages ───────────────────────────────────────────────────────────────────

@dataclass
class Message:
    """
    Agent-to-agent message envelope.
    All negotiation traffic passes through explicit Message objects.
    """
    msg_type:   MsgType
    sender_id:  str
    receiver_id: str
    session_id: str
    payload:    dict = field(default_factory=dict)
    round_num:  int  = 0

    def __repr__(self) -> str:
        return (f"[R{self.round_num}] {self.msg_type} "
                f"{self.sender_id}→{self.receiver_id} "
                f"({self.session_id})")


# ─── Utility helpers ─────────────────────────────────────────────────────────────

ALL_DAYS: list[Day]    = list(Day)
ALL_PERIODS: list[Period] = list(Period)

ALL_SLOTS: list[TimeSlot] = [
    TimeSlot(d, p) for d in ALL_DAYS for p in ALL_PERIODS
]
