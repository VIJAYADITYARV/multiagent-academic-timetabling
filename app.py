"""
app.py — Decentralized Multi-Agent University Scheduling Simulator.

Architecture & Interface:
  • Enterprise dark obsidian aesthetic (zero AI-cliché gradients or emojis)
  • Clean typographic status badges and monospace protocol telemetry
  • Live message bus replay (FIPA Contract Net Protocol + Asynchronous Backtracking)
  • Dynamic agent resource cards and weekly master timetable matrix
  • Independent verification engine for Hard Constraints H1–H6
"""

from __future__ import annotations

import time
from collections import Counter
import pandas as pd
import streamlit as st

from models import Day, MsgType, Period, RoomType, ALL_DAYS, ALL_PERIODS
from demo_data import build_demo_scenario, build_department_scale_scenario
from scheduler import (
    Scheduler, SimulationState,
    build_unsatisfiable_scenario, build_conflict_scenario,
)

# ─── Page configuration ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Multi-Agent Timetabling Protocol",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Academic Editorial Design System (Cream, Burgundy & Pastel Accents) ─────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;0,800;1,500&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #2D2426;
}

.stApp {
    background-color: #FAF7F2;
    background-image: 
        radial-gradient(circle at 10% 8%, rgba(255, 255, 255, 0.95) 0%, transparent 50%),
        radial-gradient(circle at 90% 92%, rgba(243, 237, 226, 0.85) 0%, transparent 55%);
    min-height: 100vh;
}

/* ── Academic Top Navigation Bar ── */
.academic-navbar {
    background: #FFFFFF;
    border: 1px solid #EAE2D5;
    border-top: 4px solid #6B1D2F;
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(107, 29, 47, 0.05), 0 1px 4px rgba(0,0,0,0.03);
    transition: all 0.3s ease;
}

.academic-navbar:hover {
    box-shadow: 0 6px 26px rgba(107, 29, 47, 0.08);
}

.navbar-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.navbar-crest {
    width: 44px;
    height: 44px;
    background: #FCECEF;
    border: 1.5px solid #F5CBD3;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6B1D2F;
    font-weight: 800;
    box-shadow: 0 2px 8px rgba(107, 29, 47, 0.08);
}

.navbar-super {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #8C2B42;
    text-transform: uppercase;
    margin-bottom: 2px;
}

.navbar-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #1C1617;
    letter-spacing: -0.02em;
    line-height: 1.2;
}

.navbar-sub {
    font-size: 0.8rem;
    color: #6E6265;
    margin-top: 2px;
}

.navbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
}

.navbar-badge-scenario {
    background: #FDF4F5;
    color: #6B1D2F;
    border: 1px solid #F5CCD3;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}

.navbar-status-pill {
    background: #EBF7EE;
    color: #166534;
    border: 1px solid #BBF7D0;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
}

.nav-pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #166534;
    border-radius: 50%;
    display: inline-block;
    animation: dotPulse 2s infinite;
}

@keyframes dotPulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 101, 52, 0.6); }
    70% { transform: scale(1.15); box-shadow: 0 0 0 6px rgba(22, 101, 52, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 101, 52, 0); }
}

/* ── Animation Flows & Keyframes ── */
@keyframes slideUpFade {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes softBreathing {
    0%, 100% { border-color: #EAE2D5; box-shadow: 0 2px 8px rgba(107, 29, 47, 0.04); }
    50% { border-color: #8C2B42; box-shadow: 0 4px 16px rgba(107, 29, 47, 0.14); }
}

@keyframes ribbonPulse {
    0%, 100% { border-left-color: #6B1D2F; }
    50% { border-left-color: #B23B55; }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #F4EFE6 !important;
    border-right: 1px solid #E5DCD0 !important;
}

[data-testid="stSidebar"] hr {
    border-color: #E2D7C8 !important;
    margin: 16px 0 !important;
}

.sidebar-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #8C2B42;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.sidebar-brand {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.18rem;
    font-weight: 700;
    color: #4A121F;
    letter-spacing: -0.01em;
    margin-bottom: 2px;
}

.sidebar-sub {
    font-size: 0.75rem;
    color: #6E6265;
    margin-bottom: 16px;
}

/* Sidebar Buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: #FFFFFF;
    color: #2D2426;
    border: 1px solid #E0D5C5;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 9px 14px;
    letter-spacing: 0.01em;
    transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 6px;
    text-align: left;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #6B1D2F !important;
    color: #FFFFFF !important;
    border-color: #6B1D2F !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(107, 29, 47, 0.22) !important;
}

[data-testid="stSidebar"] .stButton > button:active {
    transform: translateY(0);
}

/* ── Section Titles ── */
.sec-header {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #4A121F;
    margin: 18px 0 12px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.sec-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #EBE3D7;
}

/* ── Agent Cards ── */
.agent-card {
    background: #FFFFFF;
    border: 1px solid #EAE2D5;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 12px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(107, 29, 47, 0.03);
    position: relative;
}

.agent-card:hover {
    transform: translateY(-2px);
    border-color: #8C2B42;
    box-shadow: 0 6px 18px rgba(107, 29, 47, 0.09);
}

.agent-card.active {
    border-color: #8C2B42;
    background: #FFFDF9;
    animation: softBreathing 3s infinite;
}

.agent-card.committed {
    border-color: #A7F3D0;
    background: #F8FCF9;
}

.agent-card.failed {
    border-color: #FECACA;
    background: #FEF8F8;
}

.agent-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.agent-type {
    font-size: 0.68rem;
    font-weight: 700;
    color: #8C2B42;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.agent-name {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #1C1617;
    line-height: 1.3;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.pill-idle        { background: #F4EFEB; color: #6E6265; border: 1px solid #E2D9CC; }
.pill-negotiating { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
.pill-committed   { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.pill-failed      { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }

/* ── Protocol Message Feed (Pastel & Cream) ── */
.msg-bubble {
    background: #FFFFFF;
    border: 1px solid #EAE2D5;
    border-radius: 8px;
    padding: 11px 14px;
    margin-bottom: 8px;
    font-size: 0.83rem;
    transition: all 0.2s ease;
    box-shadow: 0 1px 4px rgba(0,0,0,0.02);
    animation: slideUpFade 0.25s ease-out;
}

.msg-bubble:hover {
    border-color: #8C2B42;
    background: #FFFDFB;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(107, 29, 47, 0.06);
}

.msg-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
    font-size: 0.74rem;
}

.badge-tag {
    font-size: 0.66rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 5px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Pastel Badge Palette */
.badge-CFP       { background: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; }
.badge-BID       { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.badge-REJECT    { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
.badge-AWARD     { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
.badge-RELEASE   { background: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; }
.badge-VALIDATE  { background: #FAF5FF; color: #6B21A8; border: 1px solid #E9D5FF; }
.badge-ACCEPT    { background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }
.badge-NOGOOD    { background: #FFF7ED; color: #9A3412; border: 1px solid #FED7AA; }
.badge-BACKTRACK { background: #FDF4FF; color: #86198F; border: 1px solid #F5D0FE; }
.badge-COMMIT    { background: #FCECEF; color: #6B1D2F; border: 1px solid #F5CBD3; }

.msg-actors {
    color: #5E5255;
    font-weight: 500;
}

.msg-actors strong {
    color: #1C1617;
}

.msg-details {
    color: #3E3436;
    font-size: 0.8rem;
    line-height: 1.45;
    font-family: 'JetBrains Mono', monospace;
    background: #FAF7F2;
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid #EFE8DC;
    margin-top: 4px;
}

/* ── Banner ── */
.telemetry-banner {
    background: #FFFFFF;
    border: 1px solid #EAE2D5;
    border-left: 4px solid #6B1D2F;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(107, 29, 47, 0.04);
    animation: ribbonPulse 4s infinite ease-in-out;
}

/* ── Constraint Badges ── */
.badge-pass {
    background: #ECFDF5;
    color: #065F46;
    border: 1px solid #A7F3D0;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    text-transform: uppercase;
}

.badge-fail {
    background: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FECACA;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    text-transform: uppercase;
}

/* ── Boxes ── */
.status-box {
    background: #FFFFFF;
    border: 1px solid #EAE2D5;
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 0.85rem;
    margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.status-box.success {
    border-left: 4px solid #10B981;
    background: #F6FCF8;
    color: #065F46;
}

.status-box.error {
    border-left: 4px solid #EF4444;
    background: #FEF7F7;
    color: #991B1B;
}

.status-box.info {
    border-left: 4px solid #6B1D2F;
    background: #FDF9FA;
    color: #4A121F;
}

/* ── Typography & Tables ── */
p, span, li, div {
    color: #2D2426;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', Georgia, serif;
    color: #1C1617 !important;
}

strong, b {
    color: #1C1617 !important;
}

/* Streamlit Tabs */
[data-baseweb="tab-list"] {
    gap: 12px !important;
    border-bottom: 1.5px solid #EAE2D5 !important;
    background: transparent !important;
}

[data-baseweb="tab"] {
    color: #6E6265 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    background: transparent !important;
    border: none !important;
    padding: 10px 18px !important;
    transition: all 0.2s ease !important;
}

[data-baseweb="tab"]:hover {
    color: #6B1D2F !important;
}

[data-baseweb="tab"][aria-selected="true"] {
    color: #6B1D2F !important;
    font-weight: 700 !important;
    border-bottom: 2.5px solid #6B1D2F !important;
}

/* Streamlit Metrics */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #EAE2D5;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(107, 29, 47, 0.03);
    transition: all 0.2s ease;
}

[data-testid="stMetric"]:hover {
    border-color: #8C2B42;
    box-shadow: 0 4px 14px rgba(107, 29, 47, 0.07);
}

[data-testid="stMetricLabel"] {
    color: #8C2B42 !important;
    font-size: 0.73rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

[data-testid="stMetricValue"] {
    color: #1C1617 !important;
    font-weight: 700 !important;
    font-size: 1.7rem !important;
    font-family: 'Playfair Display', Georgia, serif !important;
}

/* Streamlit Expanders */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #EAE2D5 !important;
    border-radius: 8px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.02) !important;
}

[data-testid="stExpander"] summary {
    background-color: #FAF7F2 !important;
    color: #1C1617 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}

[data-testid="stExpander"] summary:hover {
    background-color: #F6F0E6 !important;
    color: #6B1D2F !important;
}

[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #1C1617 !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background-color: #FFFFFF !important;
    border-top: 1px solid #EAE2D5 !important;
    padding: 16px 20px !important;
}

/* Tables High-Contrast Cream & Burgundy */
table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 16px 0 !important;
    font-size: 0.85rem !important;
    background: #FFFFFF !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    border: 1px solid #EAE2D5 !important;
}

table th {
    background-color: #F7EFEF !important;
    color: #541221 !important;
    font-weight: 700 !important;
    border: 1px solid #EBDADF !important;
    padding: 11px 15px !important;
    text-align: left !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}

table td {
    background-color: #FFFFFF !important;
    color: #2D2426 !important;
    border: 1px solid #EDE5D8 !important;
    padding: 10px 15px !important;
    line-height: 1.55 !important;
}

table tr:nth-child(even) td {
    background-color: #FAF7F2 !important;
}

table tr:hover td {
    background-color: #FDF4F5 !important;
    color: #1C1617 !important;
}

/* Captions and Code blocks */
.stCaption, [data-testid="stCaptionContainer"], p.stCaption {
    color: #6E6265 !important;
    font-size: 0.82rem !important;
}

pre {
    background-color: #FAF7F2 !important;
    border: 1px solid #EAE2D5 !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
    color: #1C1617 !important;
}

code:not(pre code) {
    background-color: #FCECEF !important;
    color: #6B1D2F !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    border: 1px solid #F5CBD3 !important;
}

/* Buttons in Main Area (Playback) */
.stButton > button {
    background: #FFFFFF;
    color: #2D2426;
    border: 1px solid #DDD3C4;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 16px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

.stButton > button:hover {
    background: #6B1D2F !important;
    color: #FFFFFF !important;
    border-color: #6B1D2F !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(107, 29, 47, 0.2) !important;
}

/* Streamlit Header & Toolbar */
header[data-testid="stHeader"],
[data-testid="stHeader"],
header,
.stAppHeader {
    background-color: #FAF7F2 !important;
    background: #FAF7F2 !important;
    border-bottom: 1px solid #EAE2D5 !important;
}

.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
}

/* ── Force Sidebar Always Visible & Expanded ── */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: none !important;
    min-width: 270px !important;
    max-width: 300px !important;
    position: relative !important;
    height: auto !important;
}

[data-testid="stSidebar"][aria-expanded="false"] {
    display: block !important;
    margin-left: 0 !important;
    transform: translateX(0) !important;
    width: 270px !important;
    min-width: 270px !important;
}

/* Hide the sidebar collapse/expand toggle arrow button */
[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarNavCollapseButton"],
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


# ─── State Management ────────────────────────────────────────────────────────

def _init():
    defaults = {
        "sim":           None,
        "replay_idx":    0,
        "is_playing":    False,
        "anim_speed":    1.2,
        "scenario_name": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


def sim() -> SimulationState | None:
    return st.session_state.sim


def _load(scenario: dict, name: str):
    state = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)
    Scheduler.validate(state)
    st.session_state.sim = state
    st.session_state.replay_idx = 0
    st.session_state.is_playing = False
    st.session_state.scenario_name = name


# ─── Sidebar Navigation ──────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
<div style="padding: 6px 0 16px;">
  <div class="sidebar-title">ACADEMIC GOVERNANCE</div>
  <div class="sidebar-brand">Autonomous Timetabling</div>
  <div class="sidebar-sub">Multi-Agent Constraint Satisfaction</div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">Benchmark Scenarios</div>', unsafe_allow_html=True)

    if st.button("Demo — Conflict Resolution"):
        _load(build_demo_scenario(), "Demo Benchmark (Conflict & Resolution)")
        st.rerun()

    if st.button("Conflict Benchmark (CSE401)"):
        _load(build_conflict_scenario(), "Conflict Benchmark (CSE401 vs CSE330)")
        st.rerun()

    if st.button("Stress Test (Unsatisfiable)"):
        _load(build_unsatisfiable_scenario(), "Stress Test (Unsatisfiable Domain)")
        st.rerun()

    if st.button("Scale Benchmark (Full Department)"):
        _load(build_department_scale_scenario(), "Scale Benchmark (Full Department)")
        st.rerun()

    if st.button("Reset Simulation"):
        if st.session_state.sim is not None:
            if "Unsatisfiable" in st.session_state.scenario_name:
                _load(build_unsatisfiable_scenario(), "Stress Test (Unsatisfiable Domain)")
            elif "Scale" in st.session_state.scenario_name:
                _load(build_department_scale_scenario(), "Scale Benchmark (Full Department)")
            else:
                _load(build_demo_scenario(), "Demo Benchmark (Conflict & Resolution)")
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-title">Playback Controls</div>', unsafe_allow_html=True)

    s = sim()
    total_msgs = len(s.message_log) if s else 0
    idx = st.session_state.replay_idx

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Back Step", disabled=(idx == 0 or s is None)):
            st.session_state.replay_idx = max(0, idx - 1)
            st.rerun()
    with col_b2:
        if st.button("Next Step", disabled=(s is None or idx >= total_msgs)):
            st.session_state.replay_idx = min(total_msgs, idx + 1)
            st.rerun()

    if s:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Reset Stream"):
                st.session_state.replay_idx = 0
                st.session_state.is_playing = False
                st.rerun()
        with col_c2:
            if st.button("Skip to End"):
                st.session_state.replay_idx = total_msgs
                st.session_state.is_playing = False
                st.rerun()

        play_label = "Pause Stream" if st.session_state.is_playing else "Auto Stream (1.2s)"
        if st.button(play_label):
            st.session_state.is_playing = not st.session_state.is_playing
            st.rerun()

        pct = int((idx / total_msgs * 100)) if total_msgs else 0
        st.markdown(f"""
<div style="margin-top:12px; font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#64748b;">
  Stream Index: {idx}/{total_msgs} ({pct}%)
</div>
""", unsafe_allow_html=True)
        st.progress(pct / 100)

    st.markdown("---")
    st.markdown("""
<div style="font-size:0.75rem; color:#6E6265; line-height:1.65; background:#FAF7F2; padding:12px 14px; border-radius:8px; border:1px solid #EAE2D5;">
  <strong style="color:#6B1D2F; letter-spacing:0.04em;">THEORETICAL FOUNDATIONS:</strong><br/>
  &bull; FIPA Contract Net Protocol<br/>
  &bull; Asynchronous Backtracking (ABT)<br/>
  &bull; Domain Nogood Filtering<br/>
  &bull; Hard Constraints H1–H6
</div>
""", unsafe_allow_html=True)


# ─── Academic Top Navigation Bar ─────────────────────────────────────────────

active_scen = st.session_state.scenario_name or "Demo Benchmark (Conflict & Resolution)"
s_state = sim()
if s_state is not None:
    if s_state.validation_report and s_state.validation_report.is_fully_valid:
        status_label = "SCHEDULE VERIFIED"
        status_pill_style = "background:#EBF7EE; color:#166534; border:1px solid #BBF7D0;"
        dot_color = "#166534"
    elif any(sess.failed for sess in s_state.sessions):
        status_label = "DOMAIN EXHAUSTED"
        status_pill_style = "background:#FEF2F2; color:#991B1B; border:1px solid #FECACA;"
        dot_color = "#991B1B"
    else:
        status_label = "COUNCIL ACTIVE"
        status_pill_style = "background:#FEF3C7; color:#92400E; border:1px solid #FCD34D;"
        dot_color = "#92400E"
else:
    status_label = "AWAITING SELECTION"
    status_pill_style = "background:#FAF6F0; color:#6E6265; border:1px solid #E2D9CC;"
    dot_color = "#8C7E82"

st.markdown(f"""
<div class="academic-navbar">
  <div class="navbar-left">
    <div class="navbar-crest">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6B1D2F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
        <path d="M6 12v5c3 3 9 3 12 0v-5"/>
      </svg>
    </div>
    <div>
      <div class="navbar-super">FACULTY OF COMPUTING &bull; ACADEMIC TIMETABLING COUNCIL</div>
      <div class="navbar-title">Autonomous Academic Timetabling System</div>
      <div class="navbar-sub">Peer-to-Peer Agent Negotiation &bull; FIPA Contract Net Protocol &bull; Asynchronous Backtracking</div>
    </div>
  </div>
  <div class="navbar-right">
    <div class="navbar-badge-scenario">{active_scen}</div>
    <div class="navbar-status-pill" style="{status_pill_style}">
      <span class="nav-pulse-dot" style="background-color: {dot_color};"></span>
      <span>{status_label}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

if sim() is None:
    st.markdown("""
<div class="status-box info" style="padding: 34px; text-align: center; border-left-color: #6B1D2F;">
  <div style="font-family:'Playfair Display',Georgia,serif; font-size: 1.25rem; font-weight: 700; color: #4A121F; margin-bottom: 6px;">
    System Initialization Required
  </div>
  <div style="color: #6E6265; font-size: 0.88rem; max-width: 600px; margin: 0 auto; line-height: 1.55;">
    Select <strong>Demo — Conflict Resolution</strong> or any benchmark in the sidebar to initialize the multi-agent system.
  </div>
</div>
""", unsafe_allow_html=True)
    st.stop()


# ─── Navigation Tabs ─────────────────────────────────────────────────────────

tab_stream, tab_matrix, tab_verify, tab_metrics, tab_arch = st.tabs([
    "Protocol Stream",
    "Master Matrix",
    "Constraint Verification",
    "Telemetry & Analytics",
    "System Architecture",
])

s          = sim()
idx        = st.session_state.replay_idx
all_msgs   = s.message_log
shown_msgs = all_msgs[:idx]
total_msgs = len(all_msgs)

# Reconstruct agent states up to the current replay index
active_teachers = set()
active_rooms    = set()
active_students = set()
committed_sessions: dict[str, tuple] = {}

for m in shown_msgs:
    if m.msg_type == MsgType.CFP:
        active_teachers.add(m.sender_id)
    elif m.msg_type == MsgType.BID:
        active_rooms.add(m.sender_id)
    elif m.msg_type in (MsgType.NOGOOD, MsgType.ACCEPT):
        active_students.add(m.sender_id)
    elif m.msg_type == MsgType.COMMIT and m.receiver_id == "SYSTEM":
        committed_sessions[m.session_id] = (
            m.payload.get("slot"), m.payload.get("room_id")
        )

last_msg = shown_msgs[-1] if shown_msgs else None


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1: PROTOCOL STREAM (LIVE NEGOTIATION)
# ═════════════════════════════════════════════════════════════════════════════

with tab_stream:

    # Top Status Bar
    if last_msg is None:
        st.markdown("""
<div class="telemetry-banner" style="border-left-color: #6B1D2F;">
  <span style="font-family:'Playfair Display',Georgia,serif; font-size:0.88rem; color:#6B1D2F; font-weight:700;">
    STREAM READY &nbsp;&bull;&nbsp; PROTOCOL INITIALIZED
  </span><br/>
  <span style="font-size:0.86rem; color:#2D2426;">
    Step through with <strong>Next Step</strong> or toggle <strong>Auto Stream</strong> to observe peer-to-peer agent bargaining and constraint propagation.
  </span>
</div>
""", unsafe_allow_html=True)
    else:
        t = last_msg.msg_type.value
        border_colors = {
            "CFP": "#4F46E5", "BID": "#059669", "REJECT": "#DC2626", "AWARD": "#D97706",
            "RELEASE": "#475569", "ACCEPT": "#16A34A", "NOGOOD": "#EA580C",
            "BACKTRACK": "#9333EA", "COMMIT": "#6B1D2F", "VALIDATE": "#7C3AED",
        }
        bcolor = border_colors.get(t, "#6B1D2F")

        desc_map = {
            "CFP":       f"Teacher <strong>{last_msg.sender_id}</strong> broadcasts Call For Proposals for <strong>{last_msg.session_id}</strong> at slot <strong>{last_msg.payload.get('slot','?')}</strong>",
            "BID":       f"Room <strong>{last_msg.sender_id}</strong> submits BID with operational cost <strong>{last_msg.payload.get('cost','?')}</strong> (Capacity & RoomType verified)",
            "REJECT":    f"Room <strong>{last_msg.sender_id}</strong> REJECTS proposal — reason: <em>{last_msg.payload.get('reason','')[:120]}</em>",
            "AWARD":     f"Teacher <strong>{last_msg.sender_id}</strong> AWARDS room <strong>{last_msg.payload.get('room_id','?')}</strong> (Lowest cost bid selected; tentative hold initiated)",
            "RELEASE":   f"Teacher <strong>{last_msg.sender_id}</strong> RELEASES tentative hold on room <strong>{last_msg.payload.get('room_id', last_msg.receiver_id)}</strong>",
            "VALIDATE":  f"Teacher <strong>{last_msg.sender_id}</strong> submits slot <strong>{last_msg.payload.get('slot','?')}</strong> to cohort <strong>{last_msg.receiver_id}</strong> for clash verification",
            "ACCEPT":    f"Student cohort <strong>{last_msg.sender_id}</strong> ACCEPTS slot — Hard Constraint H3 satisfied (No overlapping sessions)",
            "NOGOOD":    f"Student cohort <strong>{last_msg.sender_id}</strong> issues NOGOOD constraint: <em>{last_msg.payload.get('reason','')[:120]}</em>",
            "BACKTRACK": f"Teacher <strong>{last_msg.sender_id}</strong> executes BACKTRACK — records nogood constraint and prunes slot domain",
            "COMMIT":    f"Immutable assignment committed: <strong>{last_msg.session_id}</strong> → <strong>{last_msg.payload.get('slot','?')}</strong> in room <strong>{last_msg.payload.get('room_id','?')}</strong>",
        }
        detail_desc = desc_map.get(t, f"{t}: {last_msg.sender_id} → {last_msg.receiver_id}")

        st.markdown(f"""
<div class="telemetry-banner" style="border-left-color: {bcolor};">
  <div style="font-family:'Playfair Display',Georgia,serif; font-size:0.8rem; color:{bcolor}; font-weight:700; margin-bottom:3px;">
    STREAM STEP {idx} OF {total_msgs} &nbsp;&bull;&nbsp; ROUND {last_msg.round_num} &nbsp;&bull;&nbsp; [{t}]
  </div>
  <div style="font-size:0.88rem; color:#1C1617; line-height:1.5;">
    {detail_desc}
  </div>
</div>
""", unsafe_allow_html=True)

    # 3-Column Grid: Teachers | Message Bus | Rooms & Students
    col_t, col_bus, col_rs = st.columns([1, 1.4, 1.1])

    # 1. Teachers Column
    with col_t:
        st.markdown('<div class="sec-header">Teacher Agents</div>', unsafe_allow_html=True)
        for tid, ta in s.teacher_agents.items():
            t_active = tid in active_teachers
            t_committed = [sess for sess in ta.sessions if sess.session_id in committed_sessions]
            t_failed    = [sess for sess in ta.sessions if sess.failed]

            if t_committed and len(t_committed) == len(ta.sessions):
                state_str, pill_cls, card_cls = "Committed", "pill-committed", "committed"
            elif t_active:
                state_str, pill_cls, card_cls = "Negotiating", "pill-negotiating", "active"
            elif t_failed:
                state_str, pill_cls, card_cls = "Exhausted", "pill-failed", "failed"
            else:
                state_str, pill_cls, card_cls = "Idle", "pill-idle", ""

            committed_lines = ""
            for sess in t_committed:
                slot_info, room_info = committed_sessions.get(sess.session_id, ("?", "?"))
                committed_lines += f"<div style='color:#059669; font-size:0.74rem; font-family:\"JetBrains Mono\",monospace;'>✓ [{sess.course_id}] {slot_info} | {room_info}</div>"

            active_notice = ""
            if last_msg and last_msg.sender_id == tid:
                active_notice = f"<div style='color:#8C2B42; font-size:0.73rem; font-family:\"JetBrains Mono\",monospace; margin-top:4px;'>Active Session: {last_msg.session_id}</div>"

            nogood_total = sum(len(v) for v in ta._nogoods.values())

            st.markdown(f"""
<div class="agent-card {card_cls}">
  <div class="agent-header">
    <span class="agent-type">PRIORITY {ta.priority}</span>
    <span class="status-pill {pill_cls}">{state_str}</span>
  </div>
  <div class="agent-name">{ta.name}</div>
  <div style="font-size:0.73rem; color:#6E6265; font-family:'JetBrains Mono',monospace; margin:4px 0 6px;">
    Assigned: {', '.join(x.course_id for x in ta.sessions)}
  </div>
  {committed_lines}
  {active_notice}
  <div style="margin-top:6px; font-size:0.72rem; color:#8C7E82; font-family:'JetBrains Mono',monospace;">
    Nogoods Learned: {nogood_total}
  </div>
</div>
""", unsafe_allow_html=True)

    # 2. Message Bus Feed Column
    with col_bus:
        st.markdown('<div class="sec-header">Message Bus Telemetry</div>', unsafe_allow_html=True)

        if not shown_msgs:
            st.markdown("""
<div style="border: 1.5px dashed #E0D5C5; background: #FAF7F2; border-radius: 8px; padding: 26px; text-align: center; color: #7A6E71; font-size:0.8rem;">
  <strong>AWAITING PROTOCOL ACTIVITY</strong><br/>
  Use playback controls in sidebar to stream messages
</div>
""", unsafe_allow_html=True)
        else:
            visible_window = list(reversed(shown_msgs[-35:]))
            feed_html = ""
            for m in visible_window:
                m_type = m.msg_type.value
                slot_val = m.payload.get("slot", "")
                room_val = m.payload.get("room_id", "")
                cost_val = m.payload.get("cost", "")
                crs_val  = m.payload.get("course_id", "")
                rsn_val  = m.payload.get("reason", "")

                details = []
                if slot_val: details.append(f"slot: {slot_val}")
                if room_val: details.append(f"room: {room_val}")
                if crs_val:  details.append(f"course: {crs_val}")
                if cost_val != "": details.append(f"cost: {cost_val}")
                if rsn_val:  details.append(f"reason: {rsn_val[:85]}")

                detail_text = " • ".join(details)

                feed_html += f"""
<div class="msg-bubble">
  <div class="msg-meta">
    <span class="badge-tag badge-{m_type}">{m_type}</span>
    <span class="msg-actors"><strong>{m.sender_id}</strong> &rarr; <strong>{m.receiver_id}</strong></span>
    <span style="color:#8C7E82; margin-left:auto; font-size:0.7rem;">R{m.round_num}</span>
  </div>
  <div class="msg-details">{detail_text}</div>
</div>
"""
            st.markdown(feed_html, unsafe_allow_html=True)

    # 3. Rooms and Students Column
    with col_rs:
        st.markdown('<div class="sec-header">Room Resource Agents</div>', unsafe_allow_html=True)
        for rid, ra in s.room_agents.items():
            r_committed = {}
            r_tentative = {}
            for m in shown_msgs:
                if m.msg_type == MsgType.COMMIT and m.receiver_id == rid:
                    r_committed[str(m.payload.get("slot",""))] = m.session_id
                elif m.msg_type == MsgType.AWARD and m.receiver_id == rid:
                    r_tentative[str(m.payload.get("slot",""))] = m.session_id
                elif m.msg_type == MsgType.RELEASE and m.receiver_id == rid:
                    r_tentative.pop(str(m.payload.get("slot","")), None)

            if r_committed:
                state_str, pill_cls, card_cls = "Committed", "pill-committed", "committed"
            elif r_tentative or (rid in active_rooms):
                state_str, pill_cls, card_cls = "Holding", "pill-negotiating", "active"
            else:
                state_str, pill_cls, card_cls = "Idle", "pill-idle", ""

            hold_html = ""
            for sl, sid in r_committed.items():
                hold_html += f"<div style='color:#059669; font-size:0.73rem; font-family:\"JetBrains Mono\",monospace;'>✓ {sid} @ {sl}</div>"
            for sl, sid in r_tentative.items():
                hold_html += f"<div style='color:#B45309; font-size:0.73rem; font-family:\"JetBrains Mono\",monospace;'>⏳ HOLD {sid} @ {sl}</div>"

            st.markdown(f"""
<div class="agent-card {card_cls}">
  <div class="agent-header">
    <span class="agent-type">{ra.room_type} // CAP {ra.capacity}</span>
    <span class="status-pill {pill_cls}">{state_str}</span>
  </div>
  <div class="agent-name">{ra.room_id}</div>
  <div style="font-size:0.72rem; color:#6E6265; font-family:'JetBrains Mono',monospace; margin-bottom:4px;">
    {ra.building}
  </div>
  {hold_html}
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="sec-header" style="margin-top:16px;">Student Cohort Agents</div>', unsafe_allow_html=True)
        if not s.student_agents:
            st.markdown("""
<div style="color:#8C7E82; font-size:0.76rem; font-family:'JetBrains Mono',monospace; padding:6px 0;">
  [No cohort constraints in this scenario]
</div>
""", unsafe_allow_html=True)
        for sid_key, sa in s.student_agents.items():
            stud_schedule = {}
            stud_nogoods  = 0
            for m in shown_msgs:
                if m.msg_type == MsgType.COMMIT and m.receiver_id == sid_key:
                    stud_schedule[m.payload.get("course_id","")] = str(m.payload.get("slot",""))
                elif m.msg_type == MsgType.NOGOOD and m.sender_id == sid_key:
                    stud_nogoods += 1

            if stud_schedule:
                state_str, pill_cls, card_cls = "Committed", "pill-committed", "committed"
            elif sid_key in active_students:
                state_str, pill_cls, card_cls = "Validating", "pill-negotiating", "active"
            else:
                state_str, pill_cls, card_cls = "Idle", "pill-idle", ""

            sched_lines = ""
            for crs, sl in stud_schedule.items():
                sched_lines += f"<div style='color:#059669; font-size:0.73rem; font-family:\"JetBrains Mono\",monospace;'>✓ {crs} @ {sl}</div>"

            st.markdown(f"""
<div class="agent-card {card_cls}">
  <div class="agent-header">
    <span class="agent-type">COHORT</span>
    <span class="status-pill {pill_cls}">{state_str}</span>
  </div>
  <div class="agent-name">{sa.name}</div>
  <div style="font-size:0.72rem; color:#6E6265; font-family:'JetBrains Mono',monospace; margin:2px 0 4px;">
    Enrolled: {', '.join(sa.enrolled_courses)}
  </div>
  {sched_lines}
  <div style="margin-top:4px; font-size:0.72rem; color:#8C7E82; font-family:'JetBrains Mono',monospace;">
    Clashes Prevented: {stud_nogoods}
  </div>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2: MASTER MATRIX (TIMETABLE)
# ═════════════════════════════════════════════════════════════════════════════

with tab_matrix:
    st.markdown('<div class="sec-header">Weekly Schedule Matrix — Committed Assignments</div>', unsafe_allow_html=True)

    committed_at_idx = {sid for sid, _ in committed_sessions.items()}
    grid = {p.value: {d.value: "" for d in ALL_DAYS} for p in ALL_PERIODS}

    for sess in s.sessions:
        if sess.session_id in committed_at_idx and sess.assigned_slot:
            slot = sess.assigned_slot
            day_k = slot.day.value
            per_k = slot.period.value
            grid[per_k][day_k] = (
                f"{sess.course_id}\n"
                f"{sess.teacher_id} | {sess.assigned_room} ({sess.enrollment} seats)"
            )

    if not any(any(v for v in row.values()) for row in grid.values()):
        st.markdown("""
<div class="status-box info">
  No sessions committed at current replay index. Advance playback to observe scheduled matrix.
</div>
""", unsafe_allow_html=True)
    else:
        df_tt = pd.DataFrame(grid).T
        df_tt.index.name = "Period"
        ordered_cols = [d.value for d in ALL_DAYS if d.value in df_tt.columns]
        df_tt = df_tt[ordered_cols]
        st.dataframe(df_tt, use_container_width=True, height=420)

    unscheduled = [sess for sess in s.sessions if not sess.is_committed and sess.session_id not in committed_at_idx]
    if unscheduled:
        st.markdown('<div class="sec-header">Unallocated Sessions</div>', unsafe_allow_html=True)
        for sess in unscheduled:
            tag = "DOMAIN EXHAUSTED" if sess.failed else "PENDING ALLOCATION"
            st.markdown(f"""
<div class="status-box error" style="margin-bottom:6px;">
  <strong>[{tag}]</strong> {sess.session_id} ({sess.course_name}) &nbsp;•&nbsp; 
  Teacher: {sess.teacher_id} &nbsp;•&nbsp; Required: {sess.room_type} (Cap {sess.enrollment})
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 3: CONSTRAINT VERIFICATION (H1–H6)
# ═════════════════════════════════════════════════════════════════════════════

with tab_verify:
    st.markdown('<div class="sec-header">Hard Constraint Verification Engine (H1–H6)</div>', unsafe_allow_html=True)

    if s.validation_report is None:
        st.markdown('<div class="status-box info">Validator uninitialized.</div>', unsafe_allow_html=True)
    else:
        report = s.validation_report
        if report.is_fully_valid:
            st.markdown("""
<div class="status-box success">
  <strong>MATHEMATICAL PROOF VERIFIED:</strong> All formal hard constraints H1–H6 pass with zero violations across all committed sessions.
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="status-box error">
  <strong>VIOLATIONS DETECTED:</strong> {report.total_violations} constraint violation(s) present.
</div>
""", unsafe_allow_html=True)

        for r in report.results:
            badge_markup = f'<span class="{"badge-pass" if r.passed else "badge-fail"}">{"PASS" if r.passed else "FAIL"}</span>'
            with st.expander(f"{r.constraint_id}: {r.constraint_name}"):
                st.markdown(badge_markup, unsafe_allow_html=True)
                desc_map = {
                    "H1": "Teacher Non-Overlap: An instructor cannot be assigned to multiple sessions during the same period.",
                    "H2": "Room Non-Overlap: A classroom/lab cannot host multiple sessions concurrently.",
                    "H3": "Cohort Non-Overlap: A student group cannot have overlapping scheduled sessions.",
                    "H4": "Room Capacity: Venue seating capacity must be greater than or equal to course enrollment.",
                    "H5": "Room Type Compatibility: Specialized courses (e.g. Computer Labs) require matching facility classification.",
                    "H6": "Instructor Availability: Assigned slots must adhere to stated instructor working hours.",
                }
                st.markdown(f'<div style="color:#cbd5e1; font-size:0.83rem; margin:8px 0 10px; line-height:1.5;">{desc_map.get(r.constraint_id, "")}</div>', unsafe_allow_html=True)
                if r.passed:
                    st.markdown("<span style='color:#34d399; font-size:0.8rem; font-family:\"JetBrains Mono\",monospace;'>Status: Verified compliant (0 violations)</span>", unsafe_allow_html=True)
                else:
                    for v in r.violations:
                        st.error(v)

        st.markdown('<div class="sec-header">Final Session Assignment Registry</div>', unsafe_allow_html=True)
        registry = [
            {"Session": ss.session_id, "Course": ss.course_name,
             "Teacher": ss.teacher_id, "Slot": str(ss.assigned_slot),
             "Room": ss.assigned_room, "Enrollment": ss.enrollment,
             "RoomType": str(ss.room_type), "Outcome": "COMMITTED"}
            for ss in s.sessions if ss.is_committed
        ] + [
            {"Session": ss.session_id, "Course": ss.course_name,
             "Teacher": ss.teacher_id, "Slot": "—", "Room": "—",
             "Enrollment": ss.enrollment, "RoomType": str(ss.room_type),
             "Outcome": "FAILED (UNSATISFIABLE)"}
            for ss in s.sessions if ss.failed
        ]
        if registry:
            st.dataframe(pd.DataFrame(registry), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 4: TELEMETRY & ANALYTICS
# ═════════════════════════════════════════════════════════════════════════════

with tab_metrics:
    st.markdown('<div class="sec-header">Simulation Telemetry & Metrics</div>', unsafe_allow_html=True)

    stats = s.stats
    c1, c2, c3, c4 = st.columns(4)

    sched_count   = sum(1 for ss in s.sessions if ss.is_committed)
    failed_count  = sum(1 for ss in s.sessions if ss.failed)
    unsched_count = sum(1 for ss in s.sessions if not ss.is_committed)

    c1.metric("Committed Sessions", sched_count)
    c2.metric("Failed / Unscheduled", unsched_count)
    c3.metric("Negotiation Rounds", stats.negotiation_rounds)
    c4.metric("Messages Exchanged", len(s.message_log))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Cohort Validations", stats.proposals_accepted)
    c6.metric("Proposals Rejected", stats.proposals_rejected)
    c7.metric("Nogood Constraints", stats.nogoods_generated)
    viol_total = s.validation_report.total_violations if s.validation_report else 0
    c8.metric("Hard Violations", viol_total)

    st.markdown("---")

    type_counts = Counter(m.msg_type.value for m in s.message_log)
    df_types = pd.DataFrame([{"Type": k, "Count": v} for k, v in type_counts.most_common()])

    try:
        import plotly.express as px
        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            st.markdown('<div class="sec-header">Message Distribution by Protocol Type</div>', unsafe_allow_html=True)
            fig1 = px.bar(
                df_types, x="Type", y="Count", color="Type",
                color_discrete_map={
                    "CFP":"#6366F1","BID":"#10B981","REJECT":"#EF4444",
                    "AWARD":"#F59E0B","RELEASE":"#94A3B8","ACCEPT":"#059669",
                    "NOGOOD":"#EA580C","BACKTRACK":"#A855F7",
                    "COMMIT":"#6B1D2F","VALIDATE":"#8B5CF6",
                },
                template="plotly_white"
            )
            fig1.update_layout(
                showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                font=dict(color="#1C1617", family="Plus Jakarta Sans, sans-serif")
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_ch2:
            st.markdown('<div class="sec-header">Instructor Pedagogical Utility per Session</div>', unsafe_allow_html=True)
            util_data = []
            for sess in s.sessions:
                if sess.is_committed:
                    ta = s.teacher_agents.get(sess.teacher_id)
                    if ta and sess.assigned_slot:
                        u = ta._utility(sess.assigned_slot, sess)
                        util_data.append({"Session": sess.course_id, "Utility": round(u, 2)})
            if util_data:
                fig2 = px.bar(
                    pd.DataFrame(util_data), x="Session", y="Utility",
                    color="Utility",
                    color_continuous_scale=[[0, "#FCECEF"], [0.5, "#9E2A47"], [1, "#6B1D2F"]],
                    template="plotly_white"
                )
                fig2.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                    font=dict(color="#1C1617", family="Plus Jakarta Sans, sans-serif")
                )
                st.plotly_chart(fig2, use_container_width=True)
    except ImportError:
        st.dataframe(df_types, use_container_width=True)

    st.markdown('<div class="sec-header">Agent Telemetry Ledger</div>', unsafe_allow_html=True)
    agent_rows = []
    for tid, ta in s.teacher_agents.items():
        agent_rows.append({
            "Agent": ta.name, "Classification": "Teacher",
            "Priority": str(ta.priority), "Total Sessions": len(ta.sessions),
            "Committed": sum(1 for sess in ta.sessions if sess.is_committed),
            "Nogoods Learned": ta.nogood_count(),
            "Outbound Messages": ta.msgs_sent, "Inbound Messages": ta.msgs_received,
        })
    for rid, ra in s.room_agents.items():
        agent_rows.append({
            "Agent": ra.room_id, "Classification": f"Room ({ra.room_type})",
            "Priority": "—", "Total Sessions": "—",
            "Committed": len(ra._committed),
            "Nogoods Learned": "—",
            "Outbound Messages": ra.msgs_sent, "Inbound Messages": ra.msgs_received,
        })
    st.dataframe(pd.DataFrame(agent_rows), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 5: SYSTEM ARCHITECTURE
# ═════════════════════════════════════════════════════════════════════════════

with tab_arch:
    st.markdown(r"""
### Multi-Agent Protocol Specification

#### 1. FIPA Contract Net Protocol (CNP) Flow
```
Teacher (Manager)                Room (Contractor)           Student (Cohort)
       |                                |                            |
       |--- CFP(session, slot) -------->|                            |
       |<-- BID(cost) / REJECT ---------|                            |
       |                                |                            |
       |--- AWARD (tentative hold) ---->|                            |
       |                                |                            |
       |--- VALIDATE(cohort, slot) --------------------------------->|
       |<-- ACCEPT / NOGOOD(conflict) ------------------------------|
       |                                |                            |
[ACCEPT]-- COMMIT --------------------->|--------------------------->|
[NOGOOD]-- RELEASE (clear hold) ------->|                            |
       (Teacher learns Nogood, backtracks to next candidate slot)
```

---

#### 2. Protocol Primitives

| Message Type | Semantics & Pre-Conditions | Post-Conditions |
|:---|:---|:---|
| **CFP** | Teacher initiates negotiation for slot $T$ | Rooms evaluate local constraints H2, H4, H5 |
| **BID** | Room verifies capacity, type, and availability | Computes resource efficiency cost ($C = \text{cap} - \text{enroll}$) |
| **REJECT** | Room fails H2, H4, or H5 constraint check | Informs teacher of failure reason; teacher prunes room |
| **AWARD** | Teacher selects room with $\min(\text{cost})$ | Room places tentative hold on slot $T$ |
| **VALIDATE** | Teacher checks cohort availability | Student agent inspects personal schedule |
| **ACCEPT** | Cohort has no conflicting commitments (H3 satisfied) | Ready for final commitment |
| **NOGOOD** | Cohort detects schedule collision | Teacher logs $(T, \text{reason})$ in nogood set |
| **RELEASE** | Cohort rejected tentative assignment | Room releases tentative hold; slot becomes available |
| **BACKTRACK** | Teacher advances search pointer to next ranked slot | Re-initiates CFP round with pruned domain |
| **COMMIT** | Both room and students agree | Immutable assignment logged in all agent databases |
""")


# ─── Bottom Auto-Play Ticker (Renders AFTER UI is drawn) ─────────────────────

if st.session_state.is_playing and sim() is not None:
    total = len(sim().message_log)
    if st.session_state.replay_idx < total:
        time.sleep(st.session_state.anim_speed)
        st.session_state.replay_idx += 1
        st.rerun()
    else:
        st.session_state.is_playing = False
        st.rerun()
