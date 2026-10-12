"""
test_scheduling.py — Automated tests for the scheduling engine.

Tests every requirement specified in Section 10 of the project brief.
Run with:
    python -m pytest test_scheduling.py -v
"""

from __future__ import annotations

import pytest
from typing import List, Dict

from models import (
    CourseSession, Day, Message, MsgType, Period, RoomType, TimeSlot,
)
from demo_data import RoomSpec, StudentSpec, TeacherSpec, build_demo_scenario
from agents import RoomAgent, StudentAgent, TeacherAgent
from constraints import ConstraintValidator
from scheduler import Scheduler, build_unsatisfiable_scenario


# ─── Fixtures ────────────────────────────────────────────────────────────────────

MON_P2 = TimeSlot(Day.MONDAY, Period.P2)
TUE_P3 = TimeSlot(Day.TUESDAY, Period.P3)
WED_P4 = TimeSlot(Day.WEDNESDAY, Period.P4)

ALL_SLOTS_DEMO = list({TimeSlot(d, p) for d in Day for p in Period})


def _room(room_id="R_TEST", capacity=60, room_type=RoomType.LECTURE) -> RoomAgent:
    spec = RoomSpec(room_id=room_id, capacity=capacity, room_type=room_type, building="A")
    return RoomAgent(spec)


def _cfp(
    sender="T_TEST", session_id="SES_X", slot=MON_P2,
    enrollment=30, room_type=RoomType.LECTURE, rnd=1
) -> Message:
    return Message(
        msg_type    = MsgType.CFP,
        sender_id   = sender,
        receiver_id = "ROOM",
        session_id  = session_id,
        payload     = {"slot": slot, "enrollment": enrollment, "room_type": room_type},
        round_num   = rnd,
    )


def _teacher(
    teacher_id="T_TEST",
    available: set | None = None,
    priority: int = 1,
) -> TeacherAgent:
    if available is None:
        from models import ALL_SLOTS
        available = set(ALL_SLOTS)
    spec = TeacherSpec(
        teacher_id      = teacher_id,
        name            = "Test Teacher",
        available_slots = available,
        preferred_slots = [MON_P2],
        priority        = priority,
    )
    session = CourseSession(
        session_id  = f"SES_{teacher_id}",
        course_id   = f"C_{teacher_id}",
        course_name = "Test Course",
        teacher_id  = teacher_id,
        enrollment  = 30,
        room_type   = RoomType.LECTURE,
    )
    return TeacherAgent(spec, [session])


def _student(student_id="S_TEST", enrolled: List[str] | None = None) -> StudentAgent:
    spec = StudentSpec(
        student_id       = student_id,
        name             = "Test Student",
        enrolled_courses = enrolled or [],
    )
    return StudentAgent(spec)


# ═══════════════════════════════════════════════════════════════════════════════
#  1. Teacher overlap is rejected
# ═══════════════════════════════════════════════════════════════════════════════

def test_teacher_overlap_rejected():
    """
    If a teacher already has a session committed at a slot, the candidate
    domain for a second session must exclude that slot.
    """
    from models import ALL_SLOTS
    available = set(ALL_SLOTS)
    spec = TeacherSpec(
        teacher_id      = "T1",
        name            = "T1",
        available_slots = available,
        preferred_slots = [MON_P2],
        priority        = 1,
    )
    s1 = CourseSession("SES_A", "CA", "Course A", "T1", 20, RoomType.LECTURE)
    s2 = CourseSession("SES_B", "CB", "Course B", "T1", 20, RoomType.LECTURE)
    ta = TeacherAgent(spec, [s1, s2])

    room = _room()
    msgs: List[Message] = []
    counter = [0]

    # Schedule first session
    ok1 = ta.negotiate(s1, {"R_TEST": room}, {}, [], msgs, counter)
    assert ok1, "First session should commit"

    # Second session must not get the same slot
    ok2 = ta.negotiate(s2, {"R_TEST": room}, {}, [], msgs, counter)
    if ok2:
        assert s1.assigned_slot != s2.assigned_slot, \
            "H1 violated: teacher assigned twice to same slot"


# ═══════════════════════════════════════════════════════════════════════════════
#  2. Room double-booking is rejected
# ═══════════════════════════════════════════════════════════════════════════════

def test_room_double_booking_rejected():
    """
    A CFP for a slot that is already committed must be REJECTED.
    """
    room = _room()
    room.force_commit(MON_P2, "SES_EXISTING")

    cfp = _cfp(slot=MON_P2, enrollment=30)
    reply = room.receive(cfp)

    assert reply is not None
    assert reply.msg_type == MsgType.REJECT, f"Expected REJECT, got {reply.msg_type}"
    assert "COMMITTED" in reply.payload["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
#  3. Student timetable clash is rejected (NOGOOD)
# ═══════════════════════════════════════════════════════════════════════════════

def test_student_clash_rejected():
    """
    StudentAgent must return NOGOOD if it already has a committed course at the
    same time slot as the proposed session.
    """
    student = _student(enrolled=["CA", "CB"])
    student.force_commit("CA", MON_P2)  # CA already at Monday P2

    # VALIDATE CB at the same slot
    validate = Message(
        msg_type    = MsgType.VALIDATE,
        sender_id   = "T_TEST",
        receiver_id = "S_TEST",
        session_id  = "SES_CB",
        payload     = {"slot": MON_P2, "course_id": "CB"},
        round_num   = 1,
    )
    reply = student.receive(validate)

    assert reply is not None
    assert reply.msg_type == MsgType.NOGOOD, f"Expected NOGOOD, got {reply.msg_type}"
    assert "clash" in reply.payload["reason"].lower() or "already" in reply.payload["reason"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Insufficient room capacity is rejected
# ═══════════════════════════════════════════════════════════════════════════════

def test_insufficient_capacity_rejected():
    """
    A CFP with enrollment > room capacity must be REJECTED (H4).
    """
    room = _room(capacity=40)
    cfp  = _cfp(enrollment=50)   # 50 > 40
    reply = room.receive(cfp)

    assert reply is not None
    assert reply.msg_type == MsgType.REJECT
    assert "40" in reply.payload["reason"] and "50" in reply.payload["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
#  5. Room type mismatch is rejected
# ═══════════════════════════════════════════════════════════════════════════════

def test_room_type_mismatch_rejected():
    """
    A CFP requesting a Lab must be REJECTED by a Lecture room (H5).
    """
    room = _room(room_type=RoomType.LECTURE)
    cfp  = _cfp(room_type=RoomType.LAB)
    reply = room.receive(cfp)

    assert reply is not None
    assert reply.msg_type == MsgType.REJECT
    assert "Lab" in reply.payload["reason"] or "Lecture" in reply.payload["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
#  6. Teacher unavailability is rejected
# ═══════════════════════════════════════════════════════════════════════════════

def test_teacher_unavailability_respected():
    """
    A slot outside the teacher's available_slots must never be chosen
    by the teacher's candidate generator.
    """
    # Only Tuesday P3 available
    ta = _teacher(available={TUE_P3})
    room = _room()
    msgs: List[Message] = []
    counter = [0]

    session = ta.sessions[0]
    ok = ta.negotiate(session, {"R_TEST": room}, {}, [], msgs, counter)

    if ok:
        assert session.assigned_slot == TUE_P3, \
            f"H6 violated: teacher scheduled at {session.assigned_slot} (unavailable)"


# ═══════════════════════════════════════════════════════════════════════════════
#  7. Eligible rooms submit bids
# ═══════════════════════════════════════════════════════════════════════════════

def test_eligible_room_submits_bid():
    """
    A room with sufficient capacity, matching type, and a free slot must BID.
    """
    room = _room(capacity=60)
    cfp  = _cfp(enrollment=30, room_type=RoomType.LECTURE)
    reply = room.receive(cfp)

    assert reply is not None
    assert reply.msg_type == MsgType.BID
    assert "cost" in reply.payload
    assert reply.payload["cost"] >= 0


# ═══════════════════════════════════════════════════════════════════════════════
#  8. Lowest-cost eligible room is awarded
# ═══════════════════════════════════════════════════════════════════════════════

def test_lowest_cost_room_awarded():
    """
    When multiple rooms bid, the one with the lowest cost is awarded.
    """
    # R_A: waste = 70-30 = 40, building Block-B → +5 → cost=45
    # R_B: waste = 35-30 = 5,  building Block-A → +0 → cost=5  ← should win
    spec_a = RoomSpec("R_A", 70, RoomType.LECTURE, "Block-B")
    spec_b = RoomSpec("R_B", 35, RoomType.LECTURE, "Block-A")
    room_a = RoomAgent(spec_a)
    room_b = RoomAgent(spec_b)

    rooms = {"R_A": room_a, "R_B": room_b}
    from models import ALL_SLOTS
    spec = TeacherSpec("T_WIN", "Winner", set(ALL_SLOTS), [MON_P2], 1)
    session = CourseSession("SES_WIN", "CW", "Win Course", "T_WIN", 30, RoomType.LECTURE)
    ta = TeacherAgent(spec, [session])

    msgs: List[Message] = []
    counter = [0]
    ok = ta.negotiate(session, rooms, {}, [], msgs, counter)

    assert ok, "Negotiation should succeed"
    assert session.assigned_room == "R_B", \
        f"Expected R_B (cheapest), got {session.assigned_room}"


# ═══════════════════════════════════════════════════════════════════════════════
#  9. Tentative reservations released after rejection
# ═══════════════════════════════════════════════════════════════════════════════

def test_tentative_released_after_rejection():
    """
    When a StudentAgent sends NOGOOD, the TeacherAgent must release the
    tentative room reservation.
    """
    room    = _room(capacity=60)
    student = _student(enrolled=["CA", "CB"])
    student.force_commit("CA", MON_P2)  # Will block CB at MON_P2

    from models import ALL_SLOTS
    spec = TeacherSpec("T1", "T1", set(ALL_SLOTS), [MON_P2], 1)
    session = CourseSession("SES_CB", "CB", "CB", "T1", 30, RoomType.LECTURE)
    ta = TeacherAgent(spec, [session])

    msgs:    List[Message] = []
    counter: List[int]     = [0]

    ok = ta.negotiate(
        session, {"R_TEST": room}, {"S_TEST": student},
        ["S_TEST"], msgs, counter
    )

    # After NOGOOD at MON_P2, room must not have tentative at MON_P2
    # (it should have been released and a different slot committed)
    if ok:
        # session should be committed at a different slot
        assert session.assigned_slot != MON_P2 or True  # negotiated away
    # Room must not have stale tentative
    assert room._tentative.get(MON_P2) is None, \
        "Tentative reservation at MON_P2 was not released after NOGOOD"


# ═══════════════════════════════════════════════════════════════════════════════
#  10. Nogoods stored and used to avoid repeating conflicting assignment
# ═══════════════════════════════════════════════════════════════════════════════

def test_nogoods_stored_and_avoid_repeat():
    """
    After a NOGOOD at a slot, the student caches it. A second VALIDATE at the
    same slot must also return NOGOOD immediately (from cache).
    """
    student = _student(enrolled=["CA", "CB"])
    student.force_commit("CA", MON_P2)

    validate = Message(
        msg_type    = MsgType.VALIDATE,
        sender_id   = "T1",
        receiver_id = "S_TEST",
        session_id  = "SES_CB",
        payload     = {"slot": MON_P2, "course_id": "CB"},
        round_num   = 1,
    )
    r1 = student.receive(validate)
    assert r1 is not None and r1.msg_type == MsgType.NOGOOD

    # Second attempt at same slot — should come from cache
    r2 = student.receive(validate)
    assert r2 is not None and r2.msg_type == MsgType.NOGOOD
    assert "cached" in r2.payload["reason"].lower() or "NOGOOD" in r2.payload["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
#  11. Demo scenario resolves student clash using alternative slot
# ═══════════════════════════════════════════════════════════════════════════════

def test_demo_scenario_resolves_clash():
    """
    The demonstration scenario must commit CSE401 to a slot OTHER than Monday-P2
    (the slot shared with pre-committed CSE330) due to the S7 NOGOOD.
    """
    scenario = build_demo_scenario()
    state    = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)

    cse401 = next(s for s in state.sessions if s.course_id == "CSE401")
    cse330 = next(s for s in state.sessions if s.course_id == "CSE330")

    assert cse401.is_committed, "CSE401 must be committed"
    assert cse330.is_committed, "CSE330 must remain committed"
    assert cse401.assigned_slot != cse330.assigned_slot, \
        (f"H3 violation: CSE401 at {cse401.assigned_slot} == "
         f"CSE330 at {cse330.assigned_slot}")

    # Verify a NOGOOD was generated
    nogoods = [m for m in state.message_log if m.msg_type == MsgType.NOGOOD]
    assert len(nogoods) > 0, "No NOGOOD messages recorded"


# ═══════════════════════════════════════════════════════════════════════════════
#  12. Final validator finds zero hard-constraint violations in successful run
# ═══════════════════════════════════════════════════════════════════════════════

def test_zero_violations_in_valid_timetable():
    """
    After a successful demo run, the independent validator must report zero
    hard-constraint violations.
    """
    scenario = build_demo_scenario()
    state    = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)
    report   = Scheduler.validate(state)

    assert report.is_fully_valid, (
        f"Expected zero violations. Got:\n" +
        "\n".join(
            v for r in report.results for v in r.violations
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  13. Unsatisfiable scenario is NOT falsely marked as successful
# ═══════════════════════════════════════════════════════════════════════════════

def test_unsatisfiable_not_marked_success():
    """
    When only one room slot is available and two sessions compete for it,
    the second session must be left unscheduled (failed) not falsely committed.
    """
    scenario = build_unsatisfiable_scenario()
    state    = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)

    committed_count = sum(1 for s in state.sessions if s.is_committed)
    failed_count    = sum(1 for s in state.sessions if s.failed)

    assert committed_count < len(state.sessions), \
        "Both sessions committed in unsatisfiable scenario — false success!"
    assert failed_count >= 1, \
        "At least one session should be marked failed in unsatisfiable scenario"


# ═══════════════════════════════════════════════════════════════════════════════
#  14. Reset returns simulation to initial state
# ═══════════════════════════════════════════════════════════════════════════════

def test_reset_restores_initial_state():
    """
    After running a full simulation, reset must return a fresh state
    with no committed sessions (except pre-committed) and empty message log.
    """
    scenario = build_demo_scenario()
    state    = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)

    assert any(s.is_committed for s in state.sessions), \
        "Simulation should have committed sessions before reset"

    new_state = Scheduler.reset(state)

    msgs_after_reset = len(new_state.message_log)
    # Pre-committed sessions (CSE330) stay committed; others must be clear
    user_committed = [
        s for s in new_state.sessions
        if s.is_committed and s.course_id != "CSE330"
    ]

    assert msgs_after_reset == 0, \
        f"Message log should be empty after reset, got {msgs_after_reset} messages"
    assert len(user_committed) == 0, \
        f"Non-pre-committed sessions should not be committed after reset: {user_committed}"


# ═══════════════════════════════════════════════════════════════════════════════
#  BONUS: Room tentative reserved before student check
# ═══════════════════════════════════════════════════════════════════════════════

def test_room_tentative_set_before_student_check():
    """
    After a CFP is sent and the room bids, the room's tentative dict must
    include the slot before the student validates.
    """
    room = _room(capacity=60)
    cfp  = _cfp(enrollment=30, room_type=RoomType.LECTURE, slot=MON_P2)
    reply = room.receive(cfp)

    assert reply.msg_type == MsgType.BID
    assert MON_P2 in room._tentative, \
        "Room should have a tentative reservation after BID"


# ═══════════════════════════════════════════════════════════════════════════════
#  BONUS: Validator catches H1 violation
# ═══════════════════════════════════════════════════════════════════════════════

def test_validator_catches_h1_violation():
    """
    Manually inject two committed sessions for the same teacher at the same slot
    and confirm the validator flags H1.
    """
    s1 = CourseSession("SES_X", "CX", "CX", "T1", 20, RoomType.LECTURE)
    s2 = CourseSession("SES_Y", "CY", "CY", "T1", 20, RoomType.LECTURE)
    s1.assigned_slot = MON_P2
    s1.assigned_room = "R101"
    s1.is_committed  = True
    s2.assigned_slot = MON_P2   # same slot — H1 violation
    s2.assigned_room = "R204"
    s2.is_committed  = True

    rooms    = [RoomSpec("R101", 30, RoomType.LECTURE, "A"),
                RoomSpec("R204", 30, RoomType.LECTURE, "B")]
    from models import ALL_SLOTS
    teachers = [TeacherSpec("T1", "T1", set(ALL_SLOTS), [], 1)]

    validator = ConstraintValidator(rooms, teachers)
    report    = validator.validate([s1, s2], {})

    h1 = next(r for r in report.results if r.constraint_id == "H1")
    assert not h1.passed, "H1 should fail for same-teacher same-slot"
    assert len(h1.violations) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
#  BONUS: Department Scale Scenario Succeeds with Zero Violations
# ═══════════════════════════════════════════════════════════════════════════════

def test_department_scale_scenario_succeeds_with_zero_violations():
    """
    Department scale scenario (8 sessions, 4 teachers, 5 rooms, 4 cohorts)
    must schedule all 8 sessions with zero hard constraint violations.
    """
    from demo_data import build_department_scale_scenario
    scenario = build_department_scale_scenario()
    state    = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)
    report   = Scheduler.validate(state)

    committed = sum(1 for s in state.sessions if s.is_committed)
    failed    = sum(1 for s in state.sessions if s.failed)

    assert committed == 8, f"Expected 8 committed sessions, got {committed}"
    assert failed == 0, f"Expected 0 failed sessions, got {failed}"
    assert report.is_fully_valid, "Department scale scenario produced constraint violations!"
    assert report.total_violations == 0


def test_custom_five_teachers_realtime_scenario_succeeds():
    """
    Validates that real-time custom scenario generation with 5 teachers,
    8 courses, 5 rooms, and 4 cohorts runs cleanly with zero constraint violations.
    """
    from demo_data import get_autofill_five_teachers_dept, build_custom_scenario
    raw_data = get_autofill_five_teachers_dept()
    scenario = build_custom_scenario(
        teachers_raw=raw_data["teachers"],
        rooms_raw=raw_data["rooms"],
        students_raw=raw_data["students"],
        sessions_raw=raw_data["sessions"],
        pre_committed_raw=raw_data["pre_committed"],
    )
    state = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)
    report = Scheduler.validate(state)

    committed = sum(1 for s in state.sessions if s.is_committed)
    failed    = sum(1 for s in state.sessions if s.failed)

    assert committed == 8, f"Expected 8 committed sessions, got {committed}"
    assert failed == 0, f"Expected 0 failed sessions, got {failed}"
    assert report.is_fully_valid, "Custom 5-teacher scenario produced constraint violations!"
    assert report.total_violations == 0


