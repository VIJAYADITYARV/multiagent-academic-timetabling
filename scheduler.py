"""
scheduler.py — Top-level simulation engine.

Owns all agent instances, orchestrates negotiation in priority order,
maintains the global message log, and exposes a step-by-step interface
for the Streamlit dashboard.

This module contains no Streamlit imports and can be used/tested standalone.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

from models import (
    CourseSession, Day, Message, MsgType, Period, TimeSlot,
)
from demo_data import (
    RoomSpec, StudentSpec, TeacherSpec,
    build_demo_scenario, PRE_COMMITTED,
)
from agents import RoomAgent, StudentAgent, TeacherAgent
from constraints import ConstraintValidator, ValidationReport


# ─── Simulation state ────────────────────────────────────────────────────────────

@dataclass
class SimulationStats:
    negotiation_rounds:   int = 0
    proposals_accepted:   int = 0
    proposals_rejected:   int = 0
    nogoods_generated:    int = 0
    conflicts_resolved:   int = 0
    scheduled_sessions:   int = 0
    unscheduled_sessions: int = 0
    failed_sessions:      int = 0
    total_sessions:       int = 0


class SimulationState:
    """
    Encapsulates the complete mutable state of a scheduling run.
    Passed into Streamlit session state so reruns do not repeat work.
    """

    def __init__(self) -> None:
        self.is_initialized:  bool = False
        self.is_complete:     bool = False

        # Agents
        self.room_agents:    Dict[str, RoomAgent]    = {}
        self.student_agents: Dict[str, StudentAgent] = {}
        self.teacher_agents: Dict[str, TeacherAgent] = {}

        # Sessions (ordered by teacher priority then session index)
        self.sessions: List[CourseSession] = []

        # Enrollment map: course_id → [student_ids]
        self.course_students: Dict[str, List[str]] = {}

        # Message log (all messages ever exchanged)
        self.message_log: List[Message] = []

        # Round counter (shared mutable list so agents can increment it)
        self._round_counter: List[int] = [0]

        # Step iterator for step-by-step mode
        self._pending_sessions: List[CourseSession] = []
        self._step_index: int = 0

        # Validation report (set after validate() call)
        self.validation_report: Optional[ValidationReport] = None

        # Stats
        self.stats: SimulationStats = SimulationStats()

        # Scenario specs (for reset)
        self._rooms_spec:    List[RoomSpec]    = []
        self._teachers_spec: List[TeacherSpec] = []
        self._students_spec: List[StudentSpec] = []

        # Scenario type
        self.scenario_name: str = ""


# ─── Scheduler ───────────────────────────────────────────────────────────────────

class Scheduler:
    """
    Creates all agents from scenario specs, then drives negotiation.
    Exposes both full-run and step-by-step interfaces.
    """

    # ── Initialization ────────────────────────────────────────────────────────

    @staticmethod
    def build_from_scenario(scenario: dict) -> SimulationState:
        """Instantiate agents and set up pre-committed occupancy."""
        state = SimulationState()

        rooms_spec    = scenario["rooms"]
        teachers_spec = scenario["teachers"]
        students_spec = scenario["students"]
        sessions      = scenario["sessions"]
        pre_committed = scenario.get("pre_committed", [])

        state._rooms_spec    = rooms_spec
        state._teachers_spec = teachers_spec
        state._students_spec = students_spec

        # ── Room agents ──────────────────────────────────────────────────
        for spec in rooms_spec:
            state.room_agents[spec.room_id] = RoomAgent(spec)

        # ── Student agents ───────────────────────────────────────────────
        for spec in students_spec:
            state.student_agents[spec.student_id] = StudentAgent(spec)

        # ── Session list ─────────────────────────────────────────────────
        state.sessions = sessions

        # ── Course → students map ─────────────────────────────────────────
        for spec in students_spec:
            for course_id in spec.enrolled_courses:
                state.course_students.setdefault(course_id, []).append(spec.student_id)

        # ── Teacher agents (with their sessions) ──────────────────────────
        teacher_sessions: Dict[str, List[CourseSession]] = {}
        for ses in sessions:
            teacher_sessions.setdefault(ses.teacher_id, []).append(ses)

        for spec in teachers_spec:
            ta = TeacherAgent(spec, teacher_sessions.get(spec.teacher_id, []))
            state.teacher_agents[spec.teacher_id] = ta

        # ── Pre-commit occupancy (CSE330 at Monday P2) ────────────────────
        for pc in pre_committed:
            session_id = pc["session_id"]
            slot       = pc["slot"]
            room_id    = pc["room_id"]

            # Commit room
            state.room_agents[room_id].force_commit(slot, session_id)

            # Commit teacher session
            ses = next((s for s in sessions if s.session_id == session_id), None)
            if ses:
                ses.assigned_slot = slot
                ses.assigned_room = room_id
                ses.is_committed  = True
                teacher = state.teacher_agents.get(ses.teacher_id)
                if teacher:
                    teacher.force_commit_session(ses)

            # Commit student schedules
            course_id = next(
                (s.course_id for s in sessions if s.session_id == session_id), None
            )
            if course_id:
                for student_id, student in state.student_agents.items():
                    if student.enrolled_in(course_id):
                        student.force_commit(course_id, slot)

        # ── ABT agent-view propagation ─────────────────────────────────────
        # Higher-priority teachers broadcast committed slots to lower-priority ones
        sorted_teachers = sorted(
            state.teacher_agents.values(),
            key=lambda t: -t.priority
        )
        for i, high_teacher in enumerate(sorted_teachers):
            for low_teacher in sorted_teachers[i+1:]:
                for slot, sid in high_teacher._my_slots.items():
                    low_teacher.update_agent_view(slot, sid)

        # ── Pending sessions (sorted by teacher priority, then session order) ─
        state._pending_sessions = Scheduler._order_sessions(
            sessions, state.teacher_agents
        )
        state.stats.total_sessions = len(sessions)
        state.is_initialized = True
        state.scenario_name  = "Demo Scenario"

        return state

    @staticmethod
    def _order_sessions(
        sessions: List[CourseSession],
        teacher_agents: Dict[str, TeacherAgent],
    ) -> List[CourseSession]:
        """
        Return unscheduled sessions sorted by teacher priority (desc),
        then original order.  Pre-committed sessions are excluded.
        """
        def priority_key(s: CourseSession) -> int:
            ta = teacher_agents.get(s.teacher_id)
            return -(ta.priority if ta else 0)

        return [
            s for s in sorted(sessions, key=priority_key)
            if not s.is_committed
        ]

    # ── Full run ──────────────────────────────────────────────────────────────

    @staticmethod
    def run_full(state: SimulationState, max_rounds: int = 500) -> None:
        """Schedule every pending session (or up to max_rounds)."""
        while state._pending_sessions and state._round_counter[0] < max_rounds:
            Scheduler._schedule_next(state)
        state.is_complete = True
        Scheduler._refresh_stats(state)

    # ── Step-by-step ──────────────────────────────────────────────────────────

    @staticmethod
    def step(state: SimulationState) -> Optional[str]:
        """
        Schedule ONE pending session.
        Returns a human-readable description of what happened,
        or None if there is nothing left to do.
        """
        if not state._pending_sessions:
            state.is_complete = True
            Scheduler._refresh_stats(state)
            return None

        session = state._pending_sessions[0]
        success = Scheduler._schedule_next(state)
        Scheduler._refresh_stats(state)

        if success:
            return (f"✅ Committed {session.session_id} ({session.course_name}) "
                    f"→ {session.assigned_slot} in {session.assigned_room}")
        else:
            return (f"❌ Failed to schedule {session.session_id} "
                    f"({session.course_name}) — domain exhausted")

    # ── Internal scheduling step ──────────────────────────────────────────────

    @staticmethod
    def _schedule_next(state: SimulationState) -> bool:
        """Pop and negotiate the next pending session."""
        if not state._pending_sessions:
            return False

        session = state._pending_sessions.pop(0)
        if session.is_committed:
            return True   # already committed (pre-committed)

        teacher_agent = state.teacher_agents.get(session.teacher_id)
        if teacher_agent is None:
            return False

        enrolled_students = state.course_students.get(session.course_id, [])

        success = teacher_agent.negotiate(
            session          = session,
            room_agents      = state.room_agents,
            student_agents   = state.student_agents,
            enrolled_students= enrolled_students,
            message_log      = state.message_log,
            round_counter    = state._round_counter,
        )

        # After committing, propagate new slot to lower-priority teachers (ABT)
        if success:
            slot = session.assigned_slot
            for ta in state.teacher_agents.values():
                if ta.teacher_id != teacher_agent.teacher_id:
                    if ta.priority < teacher_agent.priority:
                        ta.update_agent_view(slot, session.session_id)

        return success

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def validate(state: SimulationState) -> ValidationReport:
        validator = ConstraintValidator(
            rooms    = state._rooms_spec,
            teachers = state._teachers_spec,
        )
        student_courses = {
            sid: list(agent.enrolled_courses)
            for sid, agent in state.student_agents.items()
        }
        report = validator.validate(state.sessions, student_courses)
        state.validation_report = report
        return report

    # ── Stats refresh ─────────────────────────────────────────────────────────

    @staticmethod
    def _refresh_stats(state: SimulationState) -> None:
        stats = state.stats
        stats.total_sessions       = len(state.sessions)
        stats.scheduled_sessions   = sum(1 for s in state.sessions if s.is_committed)
        stats.failed_sessions      = sum(1 for s in state.sessions if s.failed)
        stats.unscheduled_sessions = sum(1 for s in state.sessions if not s.is_committed)
        stats.negotiation_rounds   = state._round_counter[0]

        # Count messages by type
        stats.proposals_accepted = sum(
            1 for m in state.message_log if m.msg_type == MsgType.ACCEPT
        )
        stats.proposals_rejected = sum(
            1 for m in state.message_log
            if m.msg_type in (MsgType.REJECT, MsgType.NOGOOD)
        )
        stats.nogoods_generated = sum(
            1 for m in state.message_log if m.msg_type == MsgType.NOGOOD
        )
        stats.conflicts_resolved = sum(
            ta.nogood_count() for ta in state.teacher_agents.values()
            if any(
                s.is_committed for s in ta.sessions
                if ta.nogood_count() > 0
            )
        )

    # ── Reset ─────────────────────────────────────────────────────────────────

    @staticmethod
    def reset(state: SimulationState) -> SimulationState:
        """Return a fresh SimulationState from the same scenario."""
        scenario = build_demo_scenario()
        new_state = Scheduler.build_from_scenario(scenario)
        return new_state


# ─── Unsatisfiable scenario ───────────────────────────────────────────────────────

def build_unsatisfiable_scenario() -> dict:
    """
    Construct a scenario that is provably unsatisfiable.
    Single room LAB-ONLY with 1 slot, 2 lab sessions competing.
    """
    from demo_data import RoomSpec, TeacherSpec, StudentSpec
    from models import ALL_SLOTS

    slot = TimeSlot(Day.MONDAY, Period.P1)

    rooms = [
        RoomSpec(
            room_id   = "LAB_ONLY",
            capacity  = 50,
            room_type = RoomType.LAB,
            building  = "Block-X",
        )
    ]

    teachers = [
        TeacherSpec(
            teacher_id      = "TX",
            name            = "Prof. X",
            available_slots = {slot},
            preferred_slots = [slot],
            priority        = 2,
        ),
        TeacherSpec(
            teacher_id      = "TY",
            name            = "Prof. Y",
            available_slots = {slot},
            preferred_slots = [slot],
            priority        = 1,
        ),
    ]

    sessions = [
        CourseSession(
            session_id  = "SES_LAB_A",
            course_id   = "LABA",
            course_name = "Lab A",
            teacher_id  = "TX",
            enrollment  = 20,
            room_type   = RoomType.LAB,
        ),
        CourseSession(
            session_id  = "SES_LAB_B",
            course_id   = "LABB",
            course_name = "Lab B",
            teacher_id  = "TY",
            enrollment  = 20,
            room_type   = RoomType.LAB,
        ),
    ]

    return {
        "rooms":         rooms,
        "teachers":      teachers,
        "students":      [],
        "sessions":      sessions,
        "pre_committed": [],
    }


def build_conflict_scenario() -> dict:
    """
    Scenario with deliberate overlapping enrollments but a resolvable solution.
    Used by the 'Load Conflict Scenario' button.
    """
    from demo_data import build_demo_scenario
    return build_demo_scenario()




# ─── Import guard ─────────────────────────────────────────────────────────────────

from models import RoomType   # noqa: E402 — needed for unsatisfiable scenario
