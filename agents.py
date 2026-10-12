"""
agents.py — Student, Teacher, and Room agent classes.

Each agent:
  • maintains independent state
  • makes decisions through its own methods
  • communicates exclusively via explicit Message objects
  • enforces its own constraint set
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from models import (
    AgentState, Day, Message, MsgType, Period, RoomType,
    TimeSlot, CourseSession, ALL_SLOTS,
)
from demo_data import RoomSpec, StudentSpec, TeacherSpec


# ═══════════════════════════════════════════════════════════════════════════════
#  ROOM AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class RoomAgent:
    """
    Manages a single physical room.

    Decision flow (Contract Net):
      CFP → evaluate eligibility → BID or REJECT
      AWARD → mark tentative
      RELEASE → clear tentative
      COMMIT → mark committed
    """

    def __init__(self, spec: RoomSpec) -> None:
        self.room_id:   str      = spec.room_id
        self.capacity:  int      = spec.capacity
        self.room_type: RoomType = spec.room_type
        self.building:  str      = spec.building

        # slot → committed session_id
        self._committed: Dict[TimeSlot, str]  = {}
        # slot → tentative session_id
        self._tentative: Dict[TimeSlot, str]  = {}

        self.state:        AgentState = AgentState.IDLE
        self.last_action:  str        = "Initialized"
        self.msgs_sent:    int        = 0
        self.msgs_received:int        = 0
        self.log:          List[str]  = []

    # ── Public snapshot (for UI) ─────────────────────────────────────────────

    def occupancy_info(self) -> str:
        committed = [f"{slot}→{sid}" for slot, sid in self._committed.items()]
        tentative = [f"{slot}→{sid}(T)" for slot, sid in self._tentative.items()]
        return "; ".join(committed + tentative) or "Free"

    def is_available(self, slot: TimeSlot) -> bool:
        return slot not in self._committed and slot not in self._tentative

    def committed_slots(self) -> Dict[TimeSlot, str]:
        return dict(self._committed)

    # ── Pre-populate committed slot (for CSE330 scenario setup) ─────────────

    def force_commit(self, slot: TimeSlot, session_id: str) -> None:
        self._committed[slot] = session_id
        self._log(f"Force-committed {session_id} at {slot}")

    # ── Message handler (entry point for all incoming messages) ─────────────

    def receive(self, msg: Message) -> Optional[Message]:
        self.msgs_received += 1
        self._log(f"← {msg.msg_type} from {msg.sender_id} for {msg.session_id}")

        if msg.msg_type == MsgType.CFP:
            return self._handle_cfp(msg)
        elif msg.msg_type == MsgType.AWARD:
            return self._handle_award(msg)
        elif msg.msg_type == MsgType.RELEASE:
            return self._handle_release(msg)
        elif msg.msg_type == MsgType.COMMIT:
            return self._handle_commit(msg)
        return None

    # ── CFP handling ─────────────────────────────────────────────────────────

    def _handle_cfp(self, msg: Message) -> Message:
        slot       = msg.payload["slot"]
        enrollment = msg.payload["enrollment"]
        room_type  = msg.payload["room_type"]
        session_id = msg.session_id

        # H2 — Room non-overlap
        if slot in self._committed:
            reason = (f"Room {self.room_id} already COMMITTED at {slot} "
                      f"to {self._committed[slot]}")
            return self._reject(msg, reason)

        if slot in self._tentative:
            reason = (f"Room {self.room_id} TENTATIVELY reserved at {slot} "
                      f"for {self._tentative[slot]}")
            return self._reject(msg, reason)

        # H4 — Room capacity
        if self.capacity < enrollment:
            reason = (f"Capacity {self.capacity} < required {enrollment}")
            return self._reject(msg, reason)

        # H5 — Room type
        if self.room_type != room_type:
            reason = (f"Room type {self.room_type} ≠ required {room_type}")
            return self._reject(msg, reason)

        # Eligible — mark tentative and bid
        self._tentative[slot] = session_id
        cost = self._compute_cost(enrollment)
        self.last_action = f"BID for {session_id} at {slot} (cost={cost})"
        self.state = AgentState.NEGOTIATING
        self._log(self.last_action)

        reply = Message(
            msg_type    = MsgType.BID,
            sender_id   = self.room_id,
            receiver_id = msg.sender_id,
            session_id  = session_id,
            payload     = {"room_id": self.room_id, "cost": cost, "slot": slot,
                           "capacity": self.capacity},
            round_num   = msg.round_num,
        )
        self.msgs_sent += 1
        return reply

    def _compute_cost(self, enrollment: int) -> int:
        """
        Lower is better.
        Base wasted-capacity cost + building preference bonus.
        """
        waste = self.capacity - enrollment
        building_bonus = 0 if self.building == "Block-A" else 5
        return waste + building_bonus

    # ── AWARD handling ───────────────────────────────────────────────────────

    def _handle_award(self, msg: Message) -> None:
        slot       = msg.payload["slot"]
        session_id = msg.session_id
        # tentative already set during CFP; just confirm
        if self._tentative.get(slot) == session_id:
            self.last_action = f"AWARD accepted for {session_id} at {slot}"
            self._log(self.last_action)
        self.msgs_sent += 0  # no reply needed
        return None

    # ── RELEASE handling ─────────────────────────────────────────────────────

    def _handle_release(self, msg: Message) -> None:
        slot       = msg.payload["slot"]
        session_id = msg.session_id
        if self._tentative.get(slot) == session_id:
            del self._tentative[slot]
            self.last_action = f"Released tentative reservation for {session_id} at {slot}"
            self.state = AgentState.IDLE
            self._log(self.last_action)
        return None

    # ── COMMIT handling ──────────────────────────────────────────────────────

    def _handle_commit(self, msg: Message) -> None:
        slot       = msg.payload["slot"]
        session_id = msg.session_id
        # Move from tentative → committed
        if self._tentative.get(slot) == session_id:
            del self._tentative[slot]
        self._committed[slot] = session_id
        self.state = AgentState.COMMITTED
        self.last_action = f"COMMITTED {session_id} at {slot}"
        self._log(self.last_action)
        return None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _reject(self, msg: Message, reason: str) -> Message:
        self.last_action = f"REJECT {msg.session_id}: {reason}"
        self._log(self.last_action)
        reply = Message(
            msg_type    = MsgType.REJECT,
            sender_id   = self.room_id,
            receiver_id = msg.sender_id,
            session_id  = msg.session_id,
            payload     = {"reason": reason},
            round_num   = msg.round_num,
        )
        self.msgs_sent += 1
        return reply

    def _log(self, text: str) -> None:
        self.log.append(f"[{self.room_id}] {text}")

    def reset(self) -> None:
        """Clear all reservations (keep forced pre-committed state)."""
        self._committed.clear()
        self._tentative.clear()
        self.state = AgentState.IDLE
        self.last_action = "Reset"
        self.msgs_sent = 0
        self.msgs_received = 0
        self.log.clear()


# ═══════════════════════════════════════════════════════════════════════════════
#  STUDENT AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class StudentAgent:
    """
    Represents a student cohort enrolled in multiple courses.

    Validates VALIDATE messages from TeacherAgents:
      • H3 (student non-overlap) — checks against already-committed slots.
      • Stores nogoods so it will not re-accept a known bad slot.
      • Returns ACCEPT or NOGOOD.
    """

    def __init__(self, spec: StudentSpec) -> None:
        self.student_id:      str        = spec.student_id
        self.name:            str        = spec.name
        self.enrolled_courses: List[str] = list(spec.enrolled_courses)

        # course_id → committed TimeSlot
        self._schedule: Dict[str, TimeSlot] = {}

        # set of (session_id, slot) that have been rejected (nogoods)
        self._nogoods: Set[Tuple[str, TimeSlot]] = set()

        self.state:         AgentState = AgentState.IDLE
        self.last_action:   str        = "Initialized"
        self.msgs_sent:     int        = 0
        self.msgs_received: int        = 0
        self.log:           List[str]  = []

    # ── Public helpers ───────────────────────────────────────────────────────

    def enrolled_in(self, course_id: str) -> bool:
        return course_id in self.enrolled_courses

    def schedule_info(self) -> str:
        return "; ".join(f"{c}@{s}" for c, s in self._schedule.items()) or "Empty"

    def nogood_count(self) -> int:
        return len(self._nogoods)

    # ── Pre-populate committed course (for CSE330 scenario setup) ────────────

    def force_commit(self, course_id: str, slot: TimeSlot) -> None:
        self._schedule[course_id] = slot
        self._log(f"Force-committed {course_id} at {slot}")

    # ── Message handler ──────────────────────────────────────────────────────

    def receive(self, msg: Message) -> Optional[Message]:
        self.msgs_received += 1
        self._log(f"← {msg.msg_type} from {msg.sender_id} for {msg.session_id}")

        if msg.msg_type == MsgType.VALIDATE:
            return self._handle_validate(msg)
        elif msg.msg_type == MsgType.COMMIT:
            return self._handle_commit(msg)
        elif msg.msg_type == MsgType.RELEASE:
            # teacher released a tentative — no action needed from student side
            pass
        return None

    # ── VALIDATE handling ────────────────────────────────────────────────────

    def _handle_validate(self, msg: Message) -> Message:
        course_id  = msg.payload["course_id"]
        slot: TimeSlot = msg.payload["slot"]
        session_id = msg.session_id

        # Only respond if enrolled
        if course_id not in self.enrolled_courses:
            return None  # not our concern

        # Check nogood cache
        if (session_id, slot) in self._nogoods:
            reason = (f"Student {self.student_id} has a cached NOGOOD for "
                      f"{session_id} at {slot}")
            return self._nogood(msg, reason)

        # H3 — Student non-overlap
        for enrolled_course, committed_slot in self._schedule.items():
            if enrolled_course == course_id:
                continue
            if committed_slot == slot:
                reason = (
                    f"Student {self.student_id} is already committed to "
                    f"{enrolled_course} at {slot} — clash with {course_id}"
                )
                self._nogoods.add((session_id, slot))
                return self._nogood(msg, reason)

        # Passed — respond ACCEPT
        self.last_action = f"ACCEPT {course_id} at {slot}"
        self.state = AgentState.NEGOTIATING
        self._log(self.last_action)

        reply = Message(
            msg_type    = MsgType.ACCEPT,
            sender_id   = self.student_id,
            receiver_id = msg.sender_id,
            session_id  = session_id,
            payload     = {"slot": slot, "course_id": course_id},
            round_num   = msg.round_num,
        )
        self.msgs_sent += 1
        return reply

    # ── COMMIT handling ──────────────────────────────────────────────────────

    def _handle_commit(self, msg: Message) -> None:
        course_id = msg.payload["course_id"]
        slot: TimeSlot = msg.payload["slot"]
        if course_id in self.enrolled_courses:
            self._schedule[course_id] = slot
            self.state = AgentState.COMMITTED
            self.last_action = f"Committed {course_id} at {slot} to personal schedule"
            self._log(self.last_action)
        return None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _nogood(self, msg: Message, reason: str) -> Message:
        self.last_action = f"NOGOOD for {msg.session_id}: {reason}"
        self.state = AgentState.IDLE
        self._log(self.last_action)
        reply = Message(
            msg_type    = MsgType.NOGOOD,
            sender_id   = self.student_id,
            receiver_id = msg.sender_id,
            session_id  = msg.session_id,
            payload     = {"reason": reason, "slot": msg.payload["slot"]},
            round_num   = msg.round_num,
        )
        self.msgs_sent += 1
        return reply

    def _log(self, text: str) -> None:
        self.log.append(f"[{self.student_id}] {text}")

    def reset(self) -> None:
        self._schedule.clear()
        self._nogoods.clear()
        self.state = AgentState.IDLE
        self.last_action = "Reset"
        self.msgs_sent = 0
        self.msgs_received = 0
        self.log.clear()


# ═══════════════════════════════════════════════════════════════════════════════
#  TEACHER AGENT
# ═══════════════════════════════════════════════════════════════════════════════

# Soft-constraint weights (configurable)
WEIGHTS = {
    "preferred_slot":   3.0,   # S1
    "no_idle_gap":      2.0,   # S2
    "not_extreme":      1.5,   # S3  avoid P1 / P8
    "no_consecutive_3": 1.0,   # S3  penalise 3+ consecutive
}


class TeacherAgent:
    """
    Orchestrates negotiation for a set of CourseSession objects.

    Implements:
      • Contract Net Protocol (CFP / BID / AWARD / RELEASE / COMMIT)
      • Asynchronous Backtracking (nogoods, agent-view, priority-based backtrack)
    """

    def __init__(
        self,
        spec:     TeacherSpec,
        sessions: List[CourseSession],
        weights:  Dict[str, float] = WEIGHTS,
    ) -> None:
        self.teacher_id:     str              = spec.teacher_id
        self.name:           str              = spec.name
        self.priority:       int              = spec.priority
        self.available_slots: Set[TimeSlot]   = set(spec.available_slots)
        self.preferred_slots: List[TimeSlot]  = list(spec.preferred_slots)
        self.sessions:       List[CourseSession] = sessions
        self.weights:        Dict[str, float] = weights

        # agent-view: slot → session_id for higher-priority teachers
        self._agent_view: Dict[TimeSlot, str] = {}
        # committed slots owned by this teacher
        self._my_slots: Dict[TimeSlot, str]   = {}
        # nogoods: session_id → set of bad TimeSlots
        self._nogoods: Dict[str, Set[TimeSlot]] = {}

        self.state:         AgentState = AgentState.IDLE
        self.last_action:   str        = "Initialized"
        self.msgs_sent:     int        = 0
        self.msgs_received: int        = 0
        self.log:           List[str]  = []

    # ── Public helpers ───────────────────────────────────────────────────────

    def nogood_count(self) -> int:
        return sum(len(v) for v in self._nogoods.values())

    def assignment_info(self) -> str:
        parts = []
        for s in self.sessions:
            if s.is_committed:
                parts.append(f"{s.course_id}@{s.assigned_slot}/{s.assigned_room}")
            elif s.tentative_slot:
                parts.append(f"{s.course_id}@{s.tentative_slot}(T)")
        return "; ".join(parts) or "None"

    # ── Pre-populate committed slot (agent-view / own slot) ──────────────────

    def force_commit_session(self, session: CourseSession) -> None:
        """Called during scenario setup for CSE330 pre-commitment."""
        self._my_slots[session.assigned_slot] = session.session_id
        session.is_committed = True
        self._log(f"Force-committed {session.session_id} at {session.assigned_slot}")

    def update_agent_view(self, slot: TimeSlot, session_id: str) -> None:
        """Higher-priority teachers push their assignments here."""
        self._agent_view[slot] = session_id

    # ── Candidate domain generation ──────────────────────────────────────────

    def _candidate_slots(self, session: CourseSession) -> List[TimeSlot]:
        """
        Return available TimeSlots in descending utility order.

        Filters:
          H1 — exclude own committed/tentative slots
          H6 — exclude teacher-unavailable slots
          Nogoods — exclude previously rejected slots
        """
        bad_slots = (
            set(self._my_slots.keys())
            | {s.tentative_slot for s in self.sessions if s.tentative_slot}
            | self._nogoods.get(session.session_id, set())
        )

        candidates = [
            slot for slot in ALL_SLOTS
            if slot in self.available_slots and slot not in bad_slots
        ]

        # Score each candidate
        scored = [(self._utility(slot, session), slot) for slot in candidates]
        scored.sort(key=lambda x: -x[0])   # descending utility
        return [slot for _, slot in scored]

    def _utility(self, slot: TimeSlot, session: CourseSession) -> float:
        """
        U_a(v) = Σ weight_k * score_k(v)
        Higher is better.
        """
        score = 0.0
        w = self.weights

        # S1 — preferred slot
        if slot in self.preferred_slots:
            score += w["preferred_slot"]

        # S3 — avoid extreme periods (P1, P8)
        if slot.period not in (Period.P1, Period.P8):
            score += w["not_extreme"]

        # S3 — penalise 3rd consecutive period on same day
        same_day_periods = sorted(
            [s.period.index for s, sid in self._my_slots.items()
             if s.day == slot.day],
            key=lambda p: p
        )
        if self._would_create_3consecutive(slot.period.index, same_day_periods):
            score -= w["no_consecutive_3"]

        return score

    @staticmethod
    def _would_create_3consecutive(new_idx: int, existing: List[int]) -> bool:
        combined = sorted(set(existing) | {new_idx})
        for i in range(len(combined) - 2):
            if combined[i+1] == combined[i]+1 and combined[i+2] == combined[i]+2:
                return True
        return False

    # ── Negotiate one session (called by Scheduler) ──────────────────────────

    def negotiate(
        self,
        session:       CourseSession,
        room_agents:   Dict[str, "RoomAgent"],
        student_agents: Dict[str, "StudentAgent"],
        enrolled_students: List[str],
        message_log:   List[Message],
        round_counter: List[int],
    ) -> bool:
        """
        Run full CNP + ABT loop for one session.
        Returns True if successfully committed, False if exhausted.
        """
        candidates = self._candidate_slots(session)
        self._log(f"Starting negotiation for {session.session_id} "
                  f"({len(candidates)} candidate slots)")

        for slot in candidates:
            round_counter[0] += 1
            rnd = round_counter[0]
            self.state = AgentState.NEGOTIATING

            # ── Step 1: Contract Net — CFP to all rooms ──────────────────
            bids   : List[Message] = []
            rejects: List[Message] = []

            for room_agent in room_agents.values():
                cfp = Message(
                    msg_type    = MsgType.CFP,
                    sender_id   = self.teacher_id,
                    receiver_id = room_agent.room_id,
                    session_id  = session.session_id,
                    payload     = {
                        "slot":       slot,
                        "enrollment": session.enrollment,
                        "room_type":  session.room_type,
                    },
                    round_num = rnd,
                )
                message_log.append(cfp)
                self.msgs_sent += 1
                self._log(f"→ CFP to {room_agent.room_id} for {session.session_id} at {slot}")

                reply = room_agent.receive(cfp)
                if reply:
                    message_log.append(reply)
                    self.msgs_received += 1
                    if reply.msg_type == MsgType.BID:
                        bids.append(reply)
                    else:
                        rejects.append(reply)

            if not bids:
                self._log(f"No bids received for {session.session_id} at {slot} — skip slot")
                self._add_nogood(session.session_id, slot)
                # Release any tentatives that may have been set (shouldn't happen but guard)
                continue

            # ── Step 2: Award lowest-cost bid ────────────────────────────
            bids.sort(key=lambda b: b.payload["cost"])
            winning_bid = bids[0]
            winning_room_id = winning_bid.payload["room_id"]
            winning_room = room_agents[winning_room_id]

            # Award winner
            award = Message(
                msg_type    = MsgType.AWARD,
                sender_id   = self.teacher_id,
                receiver_id = winning_room_id,
                session_id  = session.session_id,
                payload     = {"slot": slot, "room_id": winning_room_id},
                round_num   = rnd,
            )
            message_log.append(award)
            self.msgs_sent += 1
            winning_room.receive(award)

            # Release losers
            for bid in bids[1:]:
                rel = Message(
                    msg_type    = MsgType.RELEASE,
                    sender_id   = self.teacher_id,
                    receiver_id = bid.payload["room_id"],
                    session_id  = session.session_id,
                    payload     = {"slot": slot},
                    round_num   = rnd,
                )
                message_log.append(rel)
                self.msgs_sent += 1
                room_agents[bid.payload["room_id"]].receive(rel)

            # Tentative on session
            session.tentative_slot = slot
            session.tentative_room = winning_room_id
            self.last_action = (f"Tentative: {session.session_id} at {slot} "
                                f"in {winning_room_id}")

            # ── Step 3: Validate with Student Agents (H3 + ABT) ──────────
            student_conflict = False
            conflict_reason  = ""

            for student_id in enrolled_students:
                student_agent = student_agents.get(student_id)
                if student_agent is None:
                    continue

                validate_msg = Message(
                    msg_type    = MsgType.VALIDATE,
                    sender_id   = self.teacher_id,
                    receiver_id = student_id,
                    session_id  = session.session_id,
                    payload     = {"slot": slot, "course_id": session.course_id},
                    round_num   = rnd,
                )
                message_log.append(validate_msg)
                self.msgs_sent += 1

                reply = student_agent.receive(validate_msg)
                if reply:
                    message_log.append(reply)
                    self.msgs_received += 1
                    if reply.msg_type == MsgType.NOGOOD:
                        student_conflict = True
                        conflict_reason = reply.payload["reason"]
                        break

            if student_conflict:
                # ── ABT: release room and record nogood ───────────────────
                self._log(f"NOGOOD from student for {session.session_id} at {slot}: "
                          f"{conflict_reason}")
                self._add_nogood(session.session_id, slot)
                session.tentative_slot = None
                session.tentative_room = None

                rel = Message(
                    msg_type    = MsgType.RELEASE,
                    sender_id   = self.teacher_id,
                    receiver_id = winning_room_id,
                    session_id  = session.session_id,
                    payload     = {"slot": slot},
                    round_num   = rnd,
                )
                message_log.append(rel)
                self.msgs_sent += 1
                winning_room.receive(rel)

                backtrack_msg = Message(
                    msg_type    = MsgType.BACKTRACK,
                    sender_id   = self.teacher_id,
                    receiver_id = self.teacher_id,
                    session_id  = session.session_id,
                    payload     = {"bad_slot": slot, "reason": conflict_reason},
                    round_num   = rnd,
                )
                message_log.append(backtrack_msg)
                continue  # try next slot

            # ── Step 4: All hard constraints passed — COMMIT ──────────────
            self._my_slots[slot] = session.session_id
            session.assigned_slot = slot
            session.assigned_room = winning_room_id
            session.tentative_slot = None
            session.tentative_room = None
            session.is_committed   = True
            self.state = AgentState.COMMITTED
            self.last_action = (f"COMMITTED {session.session_id} at {slot} "
                                f"in {winning_room_id}")
            self._log(self.last_action)

            # Commit room
            commit_room = Message(
                msg_type    = MsgType.COMMIT,
                sender_id   = self.teacher_id,
                receiver_id = winning_room_id,
                session_id  = session.session_id,
                payload     = {"slot": slot},
                round_num   = rnd,
            )
            message_log.append(commit_room)
            self.msgs_sent += 1
            winning_room.receive(commit_room)

            # Notify students of commitment
            for student_id in enrolled_students:
                student_agent = student_agents.get(student_id)
                if student_agent is None:
                    continue
                commit_student = Message(
                    msg_type    = MsgType.COMMIT,
                    sender_id   = self.teacher_id,
                    receiver_id = student_id,
                    session_id  = session.session_id,
                    payload     = {"slot": slot, "course_id": session.course_id},
                    round_num   = rnd,
                )
                message_log.append(commit_student)
                self.msgs_sent += 1
                student_agent.receive(commit_student)

            # Broadcast committed slot to lower-priority teachers (ABT)
            # (handled by Scheduler after this call)

            commit_self = Message(
                msg_type    = MsgType.COMMIT,
                sender_id   = self.teacher_id,
                receiver_id = "SYSTEM",
                session_id  = session.session_id,
                payload     = {"slot": slot, "room_id": winning_room_id,
                               "utility": self._utility(slot, session)},
                round_num   = rnd,
            )
            message_log.append(commit_self)
            return True

        # Exhausted all candidates
        session.failed = True
        self.state = AgentState.FAILED
        self.last_action = (f"FAILED to schedule {session.session_id} — "
                            f"no feasible slot found")
        self._log(self.last_action)

        fail_msg = Message(
            msg_type    = MsgType.REJECT,
            sender_id   = self.teacher_id,
            receiver_id = "SYSTEM",
            session_id  = session.session_id,
            payload     = {"reason": "Domain exhausted — no feasible slot"},
            round_num   = round_counter[0],
        )
        message_log.append(fail_msg)
        return False

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _add_nogood(self, session_id: str, slot: TimeSlot) -> None:
        self._nogoods.setdefault(session_id, set()).add(slot)

    def _log(self, text: str) -> None:
        self.log.append(f"[{self.teacher_id}] {text}")

    def reset(self) -> None:
        self._agent_view.clear()
        self._my_slots.clear()
        self._nogoods.clear()
        self.state = AgentState.IDLE
        self.last_action = "Reset"
        self.msgs_sent = 0
        self.msgs_received = 0
        self.log.clear()
