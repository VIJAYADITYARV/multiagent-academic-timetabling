# Agent-Based University Scheduling Simulator

> **A Decentralized Negotiation Approach to Timetabling**  
> Fundamentals of AI — University Case Study

## Overview

This application demonstrates a fully functional multi-agent system that generates university timetables through autonomous agent negotiation. Three types of agents — **TeacherAgent**, **RoomAgent**, and **StudentAgent** — exchange formal messages following the **Contract Net Protocol (CNP)** and **Asynchronous Backtracking (ABT)** to satisfy all scheduling constraints.

---

## Quick Start & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/VIJAYADITYARV/multiagent-academic-timetabling.git
cd multiagent-academic-timetabling
```

### 2. Environment Setup (Recommended)
```bash
# Create a virtual environment
python -m venv venv

# Activate it:
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Web Dashboard
```bash
streamlit run app.py
```
> The dashboard will automatically launch at **http://localhost:8501**.

### 5. Run Verification & Test Suite
```bash
pytest test_scheduling.py -v
```

---

## File Structure

```
multiagent/
├── app.py              # Streamlit dashboard (UI)
├── scheduler.py        # Top-level simulation engine
├── agents.py           # StudentAgent, TeacherAgent, RoomAgent classes
├── constraints.py      # Independent hard-constraint validator (H1–H6)
├── models.py           # Data types: TimeSlot, CourseSession, Message, enums
├── demo_data.py        # Deterministic sample dataset and scenario builders
├── test_scheduling.py  # 14 automated tests (+ 2 bonus)
├── requirements.txt
└── README.md
```

---

## Architecture

### Agent Types

| Agent | Count | Key Responsibility |
|-------|-------|-------------------|
| **TeacherAgent** | 3 | Initiates CFP, selects room bids, validates with students, commits or backtracks |
| **RoomAgent** | 4 | Evaluates CFPs against capacity/type/occupancy, returns BID or REJECT |
| **StudentAgent** | 3 | Validates proposed slots against enrolled courses, returns ACCEPT or NOGOOD |

### Protocols

#### Contract Net Protocol (CNP)

```
TeacherAgent  ──CFP──►  RoomAgent(s)
              ◄──BID──
              ──AWARD──► (winner)
              ──RELEASE──► (losers)
              ──VALIDATE──► StudentAgent(s)
              ◄──ACCEPT / NOGOOD──
              ──COMMIT / RELEASE──► (based on student response)
```

#### Asynchronous Backtracking (ABT)

- Agents are assigned priorities: T1 (3) > T2 (2) > T3 (1)
- Higher-priority teachers commit first; lower-priority agents update their **agent-view**
- On conflict: record a **nogood**, release tentative reservation, try next candidate slot
- Cached nogoods prevent revisiting known-bad assignments

### Constraint Model (DisCSP)

For each session `i`: `x_i = (t_i, r_i)` where `t_i ∈ T`, `r_i ∈ R`

| Code | Constraint | Enforced By |
|------|-----------|-------------|
| H1 | Teacher non-overlap | TeacherAgent (candidate filter) |
| H2 | Room non-overlap | RoomAgent (CFP handler) |
| H3 | Student non-overlap | StudentAgent (VALIDATE handler) |
| H4 | Room capacity ≥ enrollment | RoomAgent (CFP handler) |
| H5 | Room type match | RoomAgent (CFP handler) |
| H6 | Teacher availability | TeacherAgent (candidate filter) |

---

## Demonstration Scenario

### Load and Run

1. Open `http://localhost:8501`
2. Click **📦 Load Demo Scenario** in the sidebar
3. Click **⚡ Run Full Simulation**
4. Navigate through tabs to inspect results

### Canonical Conflict-Resolution Sequence

This is the exact sequence specified in the project brief:

| Step | Event |
|------|-------|
| 1 | T1 negotiates CSE401 (60 students). First candidate: Monday P2 |
| 2 | R101 (capacity 50, occupied by CSE330) **REJECTs** — already committed |
| 3 | R204 (capacity 70, free) submits **BID** with cost 10 |
| 4 | T1 provisionally awards R204 |
| 5 | Student group S7 (enrolled in both CSE401 and CSE330) sends **NOGOOD** — clash at Monday P2 |
| 6 | T1 **RELEASEs** R204 tentative reservation, records nogood for Monday P2 |
| 7 | T1 proposes next candidate (Tuesday P3) |
| 8 | No room/student conflicts — all agents **ACCEPT** |
| 9 | T1 commits CSE401 to Tuesday P3 in R204 |

### Step-by-Step Observation

Use **⏭️ Next Negotiation Step** to process one session at a time and observe:
- Message flow in the **💬 Negotiation Timeline** tab
- Agent state changes in the **🤖 Agent Monitor** tab
- Timetable updates in the **📅 Timetable** tab

---

## Scenarios

| Button | Description |
|--------|-------------|
| Load Demo Scenario | Main 5-course conflict-and-resolution scenario |
| Load Conflict Scenario | Same as demo (conflict is the demo) |
| Load Unsatisfiable Scenario | 2 lab sessions compete for 1 slot — provably fails |
| Run Full Simulation | Execute entire negotiation automatically |
| Next Negotiation Step | Process one session at a time |
| Run Validation | Independently validate H1–H6 after scheduling |
| Reset Simulation | Restore initial state, clear all messages and assignments |

---

## Sample Data

### Rooms

| Room | Capacity | Type | Building |
|------|----------|------|----------|
| R101 | 50 | Lecture | Block-A |
| R204 | 70 | Lecture | Block-B |
| R305 | 40 | Lecture | Block-A |
| LAB1 | 35 | Lab | Block-C |

### Teachers

| ID | Name | Availability | Priority |
|----|------|-------------|----------|
| T1 | Prof. Arora | All except Fri P5-P8 | 3 (highest) |
| T2 | Dr. Mehra | Tue–Fri all | 2 |
| T3 | Dr. Kapoor | Mon–Fri P1-P4 only | 1 |

### Student Groups

| ID | Group | Enrolled In |
|----|-------|-------------|
| S7 | 3rd Year Core | CSE401, CSE330 ← canonical conflict pair |
| S2 | 2nd Year | CSE202, MAT101L |
| S5 | Final Year | CSE330, CSE501 |

### Sessions

| Session | Course | Teacher | Students |
|---------|--------|---------|---------|
| SES_CSE401 | Advanced Algorithms | T1 | 60 |
| SES_CSE330 | Operating Systems | T2 | 55 |
| SES_CSE501 | Machine Learning | T1 | 45 |
| SES_CSE202 | Data Structures | T3 | 38 |
| SES_MAT101L | Discrete Math Lab | T3 | 30 |

---

## Soft Constraints & Utility

| Code | Description | Default Weight |
|------|-------------|---------------|
| S1 | Teacher-preferred time windows | 3.0 |
| S3a | Avoid extreme periods (P1, P8) | 1.5 |
| S3b | Penalise 3+ consecutive teaching hours | 1.0 |

Utility = Σ(weight × score). Hard constraints are evaluated first; utility ranks only feasible candidates.

---

## Deviations from Case Study

| Item | Specified | Implemented |
|------|-----------|-------------|
| S2 (idle gaps) | Minimize student idle gaps | Weight defined but not computed mid-run (student schedules finalized at commit time) |
| ABT distributed execution | True network distribution | Sequential simulation with explicit message objects and separate agent state |
| S4 (inter-building travel) | Minimize travel | Building preference captured in room cost (+5 penalty for off-campus) |

These deviations are documented rather than silently omitted.

---

## Troubleshooting

**`No module named streamlit`** → Run `pip install -r requirements.txt`  
**Port already in use** → `streamlit run app.py --server.port 8502`  
**Tests fail with import errors** → Ensure you run from the `multiagent/` directory  
