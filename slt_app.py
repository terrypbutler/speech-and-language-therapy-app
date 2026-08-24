"""Marjon Speech and Language Therapy Simulation Studio — concept prototype."""

from __future__ import annotations

from html import escape
import json

import streamlit as st

from modules.slt_simulation_engine import (
    add_learner_dialogue,
    apply_action,
    case_by_id,
    end_session,
    learner_export,
    load_cases,
    new_session,
)


st.set_page_config(page_title="Marjon SLT Simulation Studio", page_icon="💬", layout="wide")


@st.cache_data
def get_cases():
    return load_cases()


CASES = get_cases()


def styles() -> None:
    st.markdown(
        """
        <style>
        :root {--ink:#172035;--muted:#607087;--purple:#5d3aa8;--blue:#176b87;--line:#dce2eb;}
        .block-container{max-width:1220px;padding-top:2rem;padding-bottom:4rem}
        [data-testid="stSidebar"]{border-right:1px solid var(--line)}
        .hero{padding:2.2rem;border-radius:22px;color:white;background:linear-gradient(125deg,#39236c,#5d3aa8 58%,#247b9b);box-shadow:0 16px 35px rgba(61,39,112,.18);margin-bottom:1.4rem}
        .hero small{letter-spacing:.12em;text-transform:uppercase;opacity:.82;font-weight:700}
        .hero h1{color:white;font-size:2.55rem;margin:.35rem 0 .5rem}.hero p{max-width:760px;font-size:1.08rem;margin:0;opacity:.94}
        .notice{border-left:5px solid #d97706;background:#fff8e8;padding:.85rem 1rem;border-radius:8px;margin:.8rem 0 1.4rem;color:#5d3b08}
        .client{padding:1.2rem 1.4rem;background:white;border:1px solid var(--line);border-radius:16px;margin-bottom:1rem}.client h2{margin:0 0 .35rem}
        .muted{color:var(--muted)}.transcript{border-left:3px solid var(--line);padding:.2rem 0 .2rem 1rem;margin:.65rem 0}.transcript.client-line{border-left-color:var(--purple)}.transcript.learner{border-left-color:var(--blue)}.transcript.cue{border-left-color:#d97706;background:#fffaf0;padding:.65rem 1rem;border-radius:0 8px 8px 0}.minute{color:var(--muted);font-size:.78rem;font-weight:600;text-transform:uppercase}
        div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:1rem;border-radius:14px}
        </style>
        """,
        unsafe_allow_html=True,
    )


def notice() -> None:
    st.markdown(
        """<div class="notice"><strong>Concept prototype:</strong> fictional clients and
        educator-authored responses only. Unofficial and not yet approved by Plymouth Marjon
        University, RCSLT, HCPC or a placement provider. It is not clinical guidance or a
        competence-assessment system.</div>""",
        unsafe_allow_html=True,
    )


def select_case(key: str) -> dict:
    selected = st.selectbox(
        "Select a fictional client",
        [case["case_id"] for case in CASES],
        format_func=lambda value: f"{case_by_id(CASES, value)['client']['display_name']} — {case_by_id(CASES, value)['title']}",
        key=key,
    )
    return case_by_id(CASES, selected)


def render_home() -> None:
    st.markdown(
        """<section class="hero"><small>Supervised professional rehearsal</small>
        <h1>Speech & Language Therapy Simulation Studio</h1>
        <p>A Plymouth Marjon concept prototype for practising accessible communication,
        safe professional decisions and reflective debriefing with fictional clients.</p></section>""",
        unsafe_allow_html=True,
    )
    notice()
    cols = st.columns(3)
    cols[0].metric("Fictional clients", len(CASES))
    cols[1].metric("Practice range", "Adult + child")
    cols[2].metric("Generated clinical facts", "None")
    st.subheader("Practice loop")
    for column, title, body in zip(
        st.columns(3),
        ("1 · Prepare", "2 · Rehearse", "3 · Debrief"),
        (
            "Choose a case and review its communication profile and visible information.",
            "Select authored SLT actions, speak to the client and respond to timed cues.",
            "Reflect with a prepared facilitator and export a learner-safe record.",
        ),
    ):
        with column:
            with st.container(border=True):
                st.markdown(f"### {title}")
                st.write(body)
    st.subheader("Prototype cases")
    for case in CASES:
        with st.container(border=True):
            left, right = st.columns([3, 1])
            left.markdown(f"#### {case['client']['display_name']} · {case['title']}")
            left.write(case["scenario"]["presenting_context"])
            left.caption(f"{case['setting'].title()} · {case['complexity'].title()}")
            right.metric("Suggested time", f"{case['estimated_duration_minutes']} min")


def render_library() -> None:
    st.title("Fictional client library")
    notice()
    case = select_case("library_case")
    client = case["client"]
    st.markdown(
        f"""<div class="client"><h2>{escape(client['display_name'])}</h2>
        <div class="muted">{escape(client['age_group'].title())} · {escape(client['pronouns'])} ·
        {escape(case['setting'].title())} · {escape(case['complexity'].title())}</div></div>""",
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Learner context")
        st.write(case["scenario"]["presenting_context"])
        st.markdown("**Visible at the start**")
        for cue in case["scenario"]["visible_at_start"]:
            st.markdown(f"- {cue}")
        st.markdown("**Communication profile**")
        for item in client["communication_profile"]:
            st.markdown(f"- {item}")
    with right:
        st.subheader("Learning outcomes")
        for item in case["learning"]["outcomes"]:
            st.markdown(f"- {item}")
        st.markdown("**Indicative learning domains**")
        for item in case["learning"]["indicative_domains"]:
            st.markdown(f"- {item}")
        st.caption("These domains are illustrative and are not a claim of curriculum or regulatory alignment.")


def ensure_session(case: dict, learner_name: str) -> dict:
    session = st.session_state.get("slt_simulation")
    if session is None or session.get("case_id") != case["case_id"]:
        session = new_session(case, learner_name)
        st.session_state.slt_simulation = session
    return session


def render_transcript(session: dict) -> None:
    st.subheader("Interaction")
    for item in session["transcript"]:
        css = "client-line"
        if item["role"].startswith("learner"):
            css = "learner"
        elif item["role"] == "cue":
            css = "cue"
        st.markdown(
            f"""<div class="transcript {css}"><div class="minute">Minute {item['minute']} · {escape(str(item['speaker']))}</div>
            <div>{escape(str(item['text']))}</div></div>""",
            unsafe_allow_html=True,
        )


def render_client_state(case: dict, session: dict, facilitator_mode: bool) -> None:
    client = case["client"]
    state = session["state"]
    st.markdown(
        f"""<div class="client"><h2>{escape(client['display_name'])}</h2>
        <div class="muted">{escape(client['age_group'].title())} · prefers “{escape(client['preferred_address'])}” · {escape(case['setting'].title())}</div></div>""",
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    cols[0].metric("Scenario time", f"{state['elapsed_minutes']} min")
    cols[1].metric("Actions completed", len(session["action_log"]))
    cols[2].metric("Status", session["status"].title())
    with st.expander("Brief and communication profile"):
        st.write(case["scenario"]["presenting_context"])
        for item in client["communication_profile"]:
            st.markdown(f"- {item}")
    with st.expander("Visible information", expanded=True):
        for cue in [*case["scenario"]["visible_at_start"], *state.get("revealed_cues", [])]:
            st.markdown(f"- {cue}")
    if facilitator_mode:
        with st.expander("Facilitator-only view"):
            st.json(state)
            st.markdown("**Expected discussion points**")
            for item in case["facilitator_only"]["expected_points"]:
                st.markdown(f"- {item}")
            st.markdown("**Pause triggers**")
            for item in case["facilitator_only"]["pause_triggers"]:
                st.markdown(f"- {item}")


def render_simulation() -> None:
    st.title("Run SLT simulation")
    notice()
    setup, name_col = st.columns([2, 1])
    with setup:
        case = select_case("simulation_case")
    with name_col:
        learner_name = st.text_input("Learner name", value="Student SLT")
    facilitator_mode = st.sidebar.toggle("Facilitator mode", value=False)
    session = ensure_session(case, learner_name)
    reset, end, _ = st.columns([1, 1, 3])
    if reset.button("Restart case", use_container_width=True):
        st.session_state.slt_simulation = new_session(case, learner_name)
        st.rerun()
    if end.button("End simulation", type="primary", use_container_width=True, disabled=session["status"] == "ended"):
        end_session(session)
        st.rerun()
    left, right = st.columns([1.25, 1])
    with left:
        render_client_state(case, session, facilitator_mode)
    with right:
        st.subheader("Choose an SLT action")
        action_map = {item["action_id"]: item for item in case["allowed_actions"]}
        choice = st.selectbox(
            "Authored action", list(action_map),
            format_func=lambda value: action_map[value]["label"],
            disabled=session["status"] == "ended",
        )
        if st.button("Apply action · advances 2 minutes", type="primary", use_container_width=True, disabled=session["status"] == "ended"):
            result = apply_action(case, session, choice)
            if result.applied:
                st.rerun()
            st.warning(result.message)
        st.divider()
        st.subheader("Speak to the client")
        st.caption("Free text receives an authored neutral reply and cannot create assessment findings.")
        with st.form("slt_dialogue", clear_on_submit=True):
            dialogue = st.text_area("What would you say?", height=95, disabled=session["status"] == "ended")
            submitted = st.form_submit_button("Send · advances 1 minute", use_container_width=True, disabled=session["status"] == "ended")
        if submitted:
            result = add_learner_dialogue(case, session, dialogue)
            if result.applied:
                st.rerun()
            st.warning(result.message)
    st.divider()
    render_transcript(session)
    if session["status"] == "ended":
        st.success("Simulation ended. Open Debrief to reflect and export the session.")


def render_debrief() -> None:
    st.title("Structured debrief")
    notice()
    session = st.session_state.get("slt_simulation")
    if not session:
        st.info("Run a simulation first.")
        return
    case = case_by_id(CASES, session["case_id"])
    if session["status"] == "active":
        st.warning("The simulation is still active. You can still save reflection notes.")
    st.subheader(f"{case['client']['display_name']} · {case['title']}")
    for index, prompt in enumerate(case["debrief"]["prompts"]):
        saved = session.get("reflection", {}).get(prompt, "")
        value = st.text_area(prompt, value=saved, key=f"slt_reflection_{case['case_id']}_{index}")
        session.setdefault("reflection", {})[prompt] = value
    with st.expander("Review transcript"):
        render_transcript(session)
    export = learner_export(case, session)
    st.download_button(
        "Download learner-safe session JSON",
        data=json.dumps(export, indent=2, ensure_ascii=False),
        file_name=f"{case['case_id'].lower()}_session.json",
        mime="application/json",
    )
    st.caption("The export excludes facilitator-only state and makes no competence decision.")


def render_scope() -> None:
    st.title("Safety, governance and next steps")
    notice()
    st.markdown(
        """
        ### Included in this prototype

        - Three fictional SLT cases spanning adult communication, dysphagia safety and child language.
        - Deterministic prerequisites, timed cues and educator-authored dialogue.
        - Facilitator-only information, structured reflection and learner-safe export.

        ### Deliberately excluded

        - Diagnosis, standardised assessment scoring and treatment recommendations.
        - Food, drink or texture recommendations and unsupervised oral trials.
        - Automated marking, grading or competence decisions.
        - Real client information or integration with clinical records.

        ### Required before teaching use

        Marjon SLT educators and relevant placement, safeguarding, dysphagia,
        accessibility, information-governance and simulation leads must review the cases.
        Local procedures and approved learning outcomes must replace prototype wording.
        """
    )


styles()
with st.sidebar:
    st.markdown("## 💬 Marjon SLT Studio")
    st.caption("Unofficial deterministic concept · v0.1")
    page = st.radio("Navigation", ["Home", "Client library", "Run simulation", "Debrief", "Safety & scope"], label_visibility="collapsed")
    st.divider()
    st.caption("Entirely fictional training data. No real client records.")

if page == "Home":
    render_home()
elif page == "Client library":
    render_library()
elif page == "Run simulation":
    render_simulation()
elif page == "Debrief":
    render_debrief()
else:
    render_scope()
