"""
demo_data.py — Deterministic sample data for the scheduling demonstration.

Creates the exact scenario required by the project specification:
  • 5 courses, 3 teachers, 4 rooms, 3 student-group agents
  • Lecture and laboratory sessions
  • Overlapping student enrolments that produce genuine conflicts
  • A room already occupied during a proposed time slot
  • At least one rejection followed by a successful alternative
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from models import Day, Period, RoomType, TimeSlot, CourseSession


# ─── Room definition ─────────────────────────────────────────────────────────────

@dataclass
class RoomSpec:
    room_id:    str
    capacity:   int
    room_type:  RoomType
    building:   str
    preferences: List[TimeSlot] = field(default_factory=list)


# ─── Teacher definition ──────────────────────────────────────────────────────────

@dataclass
class TeacherSpec:
    teacher_id:        str
    name:              str
    available_slots:   Set[TimeSlot]          = field(default_factory=set)
    preferred_slots:   List[TimeSlot]         = field(default_factory=list)
    priority:          int                    = 1     # higher = more senior


# ─── Student-group definition ────────────────────────────────────────────────────

@dataclass
class StudentSpec:
    student_id:      str
    name:            str
    enrolled_courses: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
#  ROOMS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_rooms() -> List[RoomSpec]:
    """
    R101 — lecture hall, capacity 50  (occupied Mon-P2, injected externally)
    R204 — lecture hall, capacity 70
    R305 — lecture hall, capacity 40
    LAB1 — laboratory,   capacity 35
    """
    return [
        RoomSpec(
            room_id   = "R101",
            capacity  = 50,
            room_type = RoomType.LECTURE,
            building  = "Block-A",
        ),
        RoomSpec(
            room_id   = "R204",
            capacity  = 70,
            room_type = RoomType.LECTURE,
            building  = "Block-B",
        ),
        RoomSpec(
            room_id   = "R305",
            capacity  = 40,
            room_type = RoomType.LECTURE,
            building  = "Block-A",
        ),
        RoomSpec(
            room_id   = "LAB1",
            capacity  = 35,
            room_type = RoomType.LAB,
            building  = "Block-C",
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
#  TEACHERS
# ═══════════════════════════════════════════════════════════════════════════════

def _all_slots_except(exclude: List[TimeSlot]) -> Set[TimeSlot]:
    from models import ALL_SLOTS
    excl = set(exclude)
    return {s for s in ALL_SLOTS if s not in excl}


def _make_teachers() -> List[TeacherSpec]:
    # T1 is unavailable on Friday afternoons (P5-P8)
    t1_unavail = [TimeSlot(Day.FRIDAY, p) for p in (Period.P5, Period.P6, Period.P7, Period.P8)]
    t1_avail   = _all_slots_except(t1_unavail)
    t1_pref    = [
        TimeSlot(Day.MONDAY,    Period.P2),
        TimeSlot(Day.TUESDAY,   Period.P3),
        TimeSlot(Day.WEDNESDAY, Period.P2),
    ]

    # T2 is unavailable on Friday afternoons (P5-P8)
    # NOTE: T2 must be available Monday-P2 because CSE330 is pre-committed there
    t2_unavail = [TimeSlot(Day.FRIDAY, p) for p in (Period.P5, Period.P6, Period.P7, Period.P8)]
    t2_avail   = _all_slots_except(t2_unavail)
    t2_pref    = [
        TimeSlot(Day.MONDAY,    Period.P2),
        TimeSlot(Day.TUESDAY,   Period.P2),
        TimeSlot(Day.WEDNESDAY, Period.P3),
    ]

    # T3 is available all week, prefers mornings
    t3_avail = set()
    t3_pref  = []
    for d in Day:
        for p in (Period.P1, Period.P2, Period.P3, Period.P4):
            t3_avail.add(TimeSlot(d, p))
            t3_pref.append(TimeSlot(d, p))

    return [
        TeacherSpec(
            teacher_id     = "T1",
            name           = "Prof. Arora",
            available_slots = t1_avail,
            preferred_slots = t1_pref,
            priority       = 3,
        ),
        TeacherSpec(
            teacher_id     = "T2",
            name           = "Dr. Mehra",
            available_slots = t2_avail,
            preferred_slots = t2_pref,
            priority       = 2,
        ),
        TeacherSpec(
            teacher_id     = "T3",
            name           = "Dr. Kapoor",
            available_slots = t3_avail,
            preferred_slots = t3_pref,
            priority       = 1,
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
#  STUDENT GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_students() -> List[StudentSpec]:
    return [
        # S7 is enrolled in both CSE401 and CSE330 — the canonical conflict group
        StudentSpec(
            student_id       = "S7",
            name             = "Group-7 (3rd Year Core)",
            enrolled_courses = ["CSE401", "CSE330"],
        ),
        # S2 is enrolled in CSE202 and the lab MAT101L
        StudentSpec(
            student_id       = "S2",
            name             = "Group-2 (2nd Year)",
            enrolled_courses = ["CSE202", "MAT101L"],
        ),
        # S5 is enrolled in CSE330 and CSE501
        StudentSpec(
            student_id       = "S5",
            name             = "Group-5 (Final Year)",
            enrolled_courses = ["CSE330", "CSE501"],
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
#  COURSE SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_sessions() -> List[CourseSession]:
    """
    Five courses → six sessions total (CSE202 has both lecture and lab).
    Enrollment and type chosen to exercise capacity and room-type constraints.
    """
    return [
        # ── Main demonstration session ──────────────────────────────────────
        CourseSession(
            session_id  = "SES_CSE401",
            course_id   = "CSE401",
            course_name = "Advanced Algorithms",
            teacher_id  = "T1",
            enrollment  = 60,
            room_type   = RoomType.LECTURE,
        ),
        # ── Session that creates the canonical student conflict ─────────────
        # Enrollment 48 so it fits in R101 (capacity 50) for the pre-committed slot
        CourseSession(
            session_id  = "SES_CSE330",
            course_id   = "CSE330",
            course_name = "Operating Systems",
            teacher_id  = "T2",
            enrollment  = 48,
            room_type   = RoomType.LECTURE,
        ),
        # ── Large lecture by T1 ────────────────────────────────────────────
        CourseSession(
            session_id  = "SES_CSE501",
            course_id   = "CSE501",
            course_name = "Machine Learning",
            teacher_id  = "T1",
            enrollment  = 45,
            room_type   = RoomType.LECTURE,
        ),
        # ── Lecture component of CSE202 ────────────────────────────────────
        CourseSession(
            session_id  = "SES_CSE202",
            course_id   = "CSE202",
            course_name = "Data Structures",
            teacher_id  = "T3",
            enrollment  = 38,
            room_type   = RoomType.LECTURE,
        ),
        # ── Lab component of CSE202 ────────────────────────────────────────
        CourseSession(
            session_id  = "SES_MAT101L",
            course_id   = "MAT101L",
            course_name = "Discrete Math Lab",
            teacher_id  = "T3",
            enrollment  = 30,
            room_type   = RoomType.LAB,
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
#  PRE-ASSIGNED OCCUPANCY  (creates the R101 conflict)
# ═══════════════════════════════════════════════════════════════════════════════

# R101 is already occupied at Monday-P2 by an external class (not in our system).
# CSE330 is pre-committed to Monday-P2 in R101 to force:
#   (a) R101 to reject CSE401 at Monday-P2 (room occupied)
#   (b) Student-group S7 to send a NOGOOD for CSE401 at Monday-P2 (enrolled in both)
PRE_COMMITTED: List[dict] = [
    {
        "session_id": "SES_CSE330",
        "slot":       TimeSlot(Day.MONDAY, Period.P2),
        "room_id":    "R101",
    }
]


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def build_demo_scenario() -> dict:
    """
    Returns a single dict containing all scenario components.
    Call this once at startup to get reproducible, deterministic data.
    """
    return {
        "rooms":          _make_rooms(),
        "teachers":       _make_teachers(),
        "students":       _make_students(),
        "sessions":       _make_sessions(),
        "pre_committed":  PRE_COMMITTED,
    }


def build_department_scale_scenario() -> dict:
    """
    Scale benchmark: full academic department with 4 teachers, 5 rooms
    (including 2 specialized labs), 4 student cohorts, and 8 sessions.
    Exercises dense multi-cohort scheduling, room auction optimization,
    and concurrent multi-agent negotiation.
    """
    rooms = [
        RoomSpec(room_id="R101", capacity=50, room_type=RoomType.LECTURE, building="Block-A"),
        RoomSpec(room_id="R204", capacity=70, room_type=RoomType.LECTURE, building="Block-B"),
        RoomSpec(room_id="R305", capacity=40, room_type=RoomType.LECTURE, building="Block-A"),
        RoomSpec(room_id="LAB1", capacity=35, room_type=RoomType.LAB, building="Block-C"),
        RoomSpec(room_id="LAB2", capacity=30, room_type=RoomType.LAB, building="Block-C"),
    ]

    t1_unavail = [TimeSlot(Day.FRIDAY, p) for p in (Period.P5, Period.P6, Period.P7, Period.P8)]
    t1_pref = [
        TimeSlot(Day.MONDAY,    Period.P2),
        TimeSlot(Day.TUESDAY,   Period.P3),
        TimeSlot(Day.WEDNESDAY, Period.P2),
    ]

    t2_unavail = [TimeSlot(Day.FRIDAY, p) for p in (Period.P5, Period.P6, Period.P7, Period.P8)]
    t2_pref = [
        TimeSlot(Day.MONDAY,    Period.P2),
        TimeSlot(Day.TUESDAY,   Period.P2),
        TimeSlot(Day.WEDNESDAY, Period.P3),
    ]

    t3_avail = {TimeSlot(d, p) for d in Day for p in (Period.P1, Period.P2, Period.P3, Period.P4)}
    t3_pref  = [TimeSlot(d, p) for d in Day for p in (Period.P1, Period.P2, Period.P3, Period.P4)]

    t4_avail = {TimeSlot(d, p) for d in (Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY) for p in Period}
    t4_pref  = [
        TimeSlot(Day.WEDNESDAY, Period.P3),
        TimeSlot(Day.THURSDAY,  Period.P2),
        TimeSlot(Day.FRIDAY,    Period.P2),
    ]

    teachers = [
        TeacherSpec(teacher_id="T1", name="Prof. Arora", available_slots=_all_slots_except(t1_unavail), preferred_slots=t1_pref, priority=4),
        TeacherSpec(teacher_id="T2", name="Dr. Mehra",   available_slots=_all_slots_except(t2_unavail), preferred_slots=t2_pref, priority=3),
        TeacherSpec(teacher_id="T3", name="Dr. Kapoor", available_slots=t3_avail, preferred_slots=t3_pref, priority=2),
        TeacherSpec(teacher_id="T4", name="Dr. Sen",    available_slots=t4_avail, preferred_slots=t4_pref, priority=1),
    ]

    students = [
        StudentSpec(student_id="S7", name="Group-7 (4th Year Core)", enrolled_courses=["CSE401", "CSE330", "CSE410L"]),
        StudentSpec(student_id="S5", name="Group-5 (3rd Year)",      enrolled_courses=["CSE330", "CSE501", "CSE340"]),
        StudentSpec(student_id="S2", name="Group-2 (2nd Year)",      enrolled_courses=["CSE202", "MAT101L"]),
        StudentSpec(student_id="S1", name="Group-1 (1st Year)",      enrolled_courses=["CSE101"]),
    ]

    sessions = [
        CourseSession(session_id="SES_CSE401",  course_id="CSE401",  course_name="Advanced Algorithms", teacher_id="T1", enrollment=60, room_type=RoomType.LECTURE),
        CourseSession(session_id="SES_CSE330",  course_id="CSE330",  course_name="Operating Systems",   teacher_id="T2", enrollment=48, room_type=RoomType.LECTURE),
        CourseSession(session_id="SES_CSE501",  course_id="CSE501",  course_name="Machine Learning",    teacher_id="T1", enrollment=45, room_type=RoomType.LECTURE),
        CourseSession(session_id="SES_CSE340",  course_id="CSE340",  course_name="Distributed Systems",teacher_id="T2", enrollment=35, room_type=RoomType.LECTURE),
        CourseSession(session_id="SES_CSE202",  course_id="CSE202",  course_name="Data Structures",     teacher_id="T3", enrollment=38, room_type=RoomType.LECTURE),
        CourseSession(session_id="SES_MAT101L", course_id="MAT101L", course_name="Discrete Math Lab",   teacher_id="T3", enrollment=30, room_type=RoomType.LAB),
        CourseSession(session_id="SES_CSE410L", course_id="CSE410L", course_name="AI Software Lab",     teacher_id="T4", enrollment=28, room_type=RoomType.LAB),
        CourseSession(session_id="SES_CSE101",  course_id="CSE101",  course_name="Intro to Programming",teacher_id="T4", enrollment=40, room_type=RoomType.LECTURE),
    ]

    pre_committed = [
        {
            "session_id": "SES_CSE330",
            "slot":       TimeSlot(Day.MONDAY, Period.P2),
            "room_id":    "R101",
        }
    ]

    return {
        "rooms":         rooms,
        "teachers":      teachers,
        "students":      students,
        "sessions":      sessions,
        "pre_committed": pre_committed,
    }

