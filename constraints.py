"""
constraints.py — Independent hard-constraint validator.

Validates the final timetable against H1–H6.
Returns detailed per-constraint results so the UI can display pass/fail
with explanatory messages.

This module has no dependency on the agent classes and can be used
as a standalone verification tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from models import CourseSession, RoomType, TimeSlot
from demo_data import RoomSpec, TeacherSpec


# ─── Result types ────────────────────────────────────────────────────────────────

@dataclass
class ConstraintResult:
    constraint_id:   str          # H1 … H6
    constraint_name: str
    passed:          bool
    violations:      List[str]    # human-readable descriptions

    @property
    def status(self) -> str:
        return "✅ PASS" if self.passed else "❌ FAIL"


@dataclass
class ValidationReport:
    results:           List[ConstraintResult]
    total_violations:  int
    is_fully_valid:    bool

    def summary(self) -> str:
        if self.is_fully_valid:
            return "✅ Timetable is fully valid — zero hard-constraint violations."
        return (f"❌ Timetable has {self.total_violations} hard-constraint violation(s).")


# ─── Validator ───────────────────────────────────────────────────────────────────

class ConstraintValidator:
    """
    Independent validator — instantiate with static room/teacher specs
    and call validate(sessions) after scheduling completes.
    """

    def __init__(
        self,
        rooms:    List[RoomSpec],
        teachers: List[TeacherSpec],
    ) -> None:
        self._rooms:    Dict[str, RoomSpec]    = {r.room_id: r for r in rooms}
        self._teachers: Dict[str, TeacherSpec] = {t.teacher_id: t for t in teachers}

    def validate(
        self,
        sessions:         List[CourseSession],
        student_courses:  Dict[str, List[str]],  # student_id → [course_id]
    ) -> ValidationReport:
        """
        Run all six hard constraints against committed sessions.
        student_courses maps each student agent to its enrolled course IDs.
        """
        committed = [s for s in sessions if s.is_committed]

        results = [
            self._check_h1(committed),
            self._check_h2(committed),
            self._check_h3(committed, student_courses),
            self._check_h4(committed),
            self._check_h5(committed),
            self._check_h6(committed),
        ]

        total = sum(len(r.violations) for r in results)
        return ValidationReport(
            results          = results,
            total_violations = total,
            is_fully_valid   = total == 0,
        )

    # ── H1 — Teacher non-overlap ──────────────────────────────────────────────

    def _check_h1(self, committed: List[CourseSession]) -> ConstraintResult:
        violations: List[str] = []
        # teacher_id → (slot → session_id)
        teacher_map: Dict[str, Dict[TimeSlot, str]] = {}
        for s in committed:
            if s.assigned_slot is None:
                continue
            teacher_map.setdefault(s.teacher_id, {})
            slot = s.assigned_slot
            if slot in teacher_map[s.teacher_id]:
                clash_sid = teacher_map[s.teacher_id][slot]
                violations.append(
                    f"Teacher {s.teacher_id} teaches {s.session_id} AND "
                    f"{clash_sid} simultaneously at {slot}"
                )
            else:
                teacher_map[s.teacher_id][slot] = s.session_id

        return ConstraintResult(
            constraint_id   = "H1",
            constraint_name = "Teacher Non-Overlap",
            passed          = len(violations) == 0,
            violations      = violations,
        )

    # ── H2 — Room non-overlap ─────────────────────────────────────────────────

    def _check_h2(self, committed: List[CourseSession]) -> ConstraintResult:
        violations: List[str] = []
        room_map: Dict[str, Dict[TimeSlot, str]] = {}
        for s in committed:
            if s.assigned_slot is None or s.assigned_room is None:
                continue
            room_map.setdefault(s.assigned_room, {})
            slot = s.assigned_slot
            if slot in room_map[s.assigned_room]:
                clash_sid = room_map[s.assigned_room][slot]
                violations.append(
                    f"Room {s.assigned_room} hosts {s.session_id} AND "
                    f"{clash_sid} simultaneously at {slot}"
                )
            else:
                room_map[s.assigned_room][slot] = s.session_id

        return ConstraintResult(
            constraint_id   = "H2",
            constraint_name = "Room Non-Overlap",
            passed          = len(violations) == 0,
            violations      = violations,
        )

    # ── H3 — Student non-overlap ──────────────────────────────────────────────

    def _check_h3(
        self,
        committed: List[CourseSession],
        student_courses: Dict[str, List[str]],
    ) -> ConstraintResult:
        violations: List[str] = []
        # Build slot → course_id map for committed sessions
        slot_course: Dict[TimeSlot, str] = {}
        for s in committed:
            if s.assigned_slot is not None:
                slot_course[s.assigned_slot] = s.course_id

        for student_id, courses in student_courses.items():
            student_slots: Dict[str, TimeSlot] = {}
            for course_id in courses:
                # find session for this course
                sess = next(
                    (s for s in committed if s.course_id == course_id), None
                )
                if sess is None or sess.assigned_slot is None:
                    continue
                slot = sess.assigned_slot
                for other_course, other_slot in student_slots.items():
                    if other_slot == slot:
                        violations.append(
                            f"Student {student_id} has clash: "
                            f"{course_id} and {other_course} both at {slot}"
                        )
                student_slots[course_id] = slot

        return ConstraintResult(
            constraint_id   = "H3",
            constraint_name = "Student Non-Overlap",
            passed          = len(violations) == 0,
            violations      = violations,
        )

    # ── H4 — Room capacity ────────────────────────────────────────────────────

    def _check_h4(self, committed: List[CourseSession]) -> ConstraintResult:
        violations: List[str] = []
        for s in committed:
            if s.assigned_room is None:
                continue
            room = self._rooms.get(s.assigned_room)
            if room and room.capacity < s.enrollment:
                violations.append(
                    f"Room {s.assigned_room} capacity {room.capacity} < "
                    f"enrollment {s.enrollment} for {s.session_id}"
                )
        return ConstraintResult(
            constraint_id   = "H4",
            constraint_name = "Room Capacity",
            passed          = len(violations) == 0,
            violations      = violations,
        )

    # ── H5 — Room type ────────────────────────────────────────────────────────

    def _check_h5(self, committed: List[CourseSession]) -> ConstraintResult:
        violations: List[str] = []
        for s in committed:
            if s.assigned_room is None:
                continue
            room = self._rooms.get(s.assigned_room)
            if room and room.room_type != s.room_type:
                violations.append(
                    f"Session {s.session_id} requires {s.room_type} but "
                    f"room {s.assigned_room} is {room.room_type}"
                )
        return ConstraintResult(
            constraint_id   = "H5",
            constraint_name = "Room Type Match",
            passed          = len(violations) == 0,
            violations      = violations,
        )

    # ── H6 — Teacher availability ─────────────────────────────────────────────

    def _check_h6(self, committed: List[CourseSession]) -> ConstraintResult:
        violations: List[str] = []
        for s in committed:
            if s.assigned_slot is None:
                continue
            teacher = self._teachers.get(s.teacher_id)
            if teacher and s.assigned_slot not in teacher.available_slots:
                violations.append(
                    f"Teacher {s.teacher_id} is not available at {s.assigned_slot} "
                    f"(assigned to {s.session_id})"
                )
        return ConstraintResult(
            constraint_id   = "H6",
            constraint_name = "Teacher Availability",
            passed          = len(violations) == 0,
            violations      = violations,
        )
