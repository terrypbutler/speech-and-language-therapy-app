"""Build the bundled fictional Speech and Language Therapy scenario library."""

from __future__ import annotations

import json
from pathlib import Path


COMMON_STATE = {
    "elapsed_minutes": 0,
    "trust": 45,
    "emotion_state": "uncertain",
    "fatigue_level": 2,
    "overload_level": 3,
    "understanding_level": 2,
    "confusion_level": 0,
    "dignity_state": "preserved",
    "consent_state": "not_asked",
    "revealed_cues": [],
}


def action(action_id, label, effects, response, phrases, *, pre=None, reveals=None, blocked=None):
    item = {
        "action_id": action_id,
        "label": label,
        "preconditions": pre or {},
        "effects": effects,
        "reveals": reveals or [],
    }
    if blocked:
        item["blocked_message"] = blocked
    return item, response, phrases


def build_case(*, case_id, title, setting, complexity, client, outcomes, domains,
               role, context, visible, handover, resources, records, state,
               events, actions, facts, facilitator, rubric, debrief):
    action_rows, responses, phrases = [], {}, {}
    for item, response, action_phrases in actions:
        action_rows.append(item)
        responses[item["action_id"]] = response
        phrases[item["action_id"]] = action_phrases
    allowed_state = [key for key in state if key != "revealed_cues"]
    return {
        "case_id": case_id,
        "title": title,
        "synthetic_data_notice": "Entirely fictional training case",
        "field": "speech and language therapy",
        "setting": setting,
        "complexity": complexity,
        "patient": client,
        "learning": {"outcomes": outcomes, "professional_domains": domains},
        "prebrief": {
            "role": role,
            "orientation": "Work as you would in a supervised SLT encounter. Describe your clinical actions and write the exact words you would use.",
            "resources": resources,
            "limitations": [
                "No physical examination, oral trial or standardised assessment is performed by the app",
                "All findings and safe boundaries are educator-authored",
                "AI wording can vary, but assessment facts, consent and pathway effects cannot",
            ],
            "ground_rules": [
                "Pause if you feel uncomfortable and use the debrief for questions",
                "Treat communication as a shared interaction rather than trying to guess keywords",
                "This is formative rehearsal, not an automatic competence assessment",
            ],
        },
        "clinical": {
            "presenting_context": context,
            "visible_at_start": visible,
            "prescribed_items": [],
        },
        "clinical_workspace": {
            "handover": handover,
            "environment": visible,
            "available_resources": resources,
            "record_access": records,
        },
        "initial_state": state,
        "time_events": events,
        "allowed_actions": action_rows,
        "ai_contract": {
            "allowed_context": [
                "Client communication profile", "Currently revealed cues",
                "Educator-authored assessment information", "Consent and assent state",
                "Bounded client-experience state", "Learner's exact words",
            ],
            "allowed_state_keys": allowed_state,
            "may_generate": ["Client dialogue", "Emotion", "Brief visible behaviour", "Response latency"],
            "must_not_generate": [
                "New observations or assessment findings", "Diagnosis or diagnoses",
                "Treatment recommendations or effects", "Consent or assent on the client's behalf",
                "Scores, prognosis, risk decisions or competence judgement",
            ],
        },
        "facilitator_only": facilitator,
        "educator_rubric": rubric,
        "debrief": {"prompts": debrief, "automatic_competence_decision": False},
        "scenario_version": "1.0.0",
        "publication_status": "development",
        "review": {"status": "pending_local_professional_review", "reviewer": "", "reviewed_at": ""},
        "dialogue": {
            "opening_line": client["opening_line"],
            "action_responses": responses,
            "fallback_responses": client["fallback_responses"],
            "facts": facts,
            "action_phrases": phrases,
        },
    }


def client(name, age, pronouns, preferred, needs, preferences, style, cues, opening, fallbacks):
    return {
        "display_name": name,
        "age": age,
        "pronouns": pronouns,
        "preferred_address": preferred,
        "communication_needs": needs,
        "explicit_preferences": preferences,
        "dialogue_style": style,
        "nonverbal_palette": cues,
        "opening_line": opening,
        "fallback_responses": fallbacks,
    }


CASES = []

# Supported conversation following stroke
c1 = client(
    "Sam Taylor", 61, "they/them", "Sam",
    ["Aphasia following an educator-authored fictional stroke", "Understands short everyday questions more reliably than long questions", "Uses gesture, drawing, writing and a low-tech communication board"],
    ["Allow extra response time", "Acknowledge breakdowns and verify meaning", "Ask before involving family"],
    "Short spoken phrases with gesture, pointing and occasional word-finding pauses",
    ["Sam pauses, gestures and looks towards the communication board.", "Sam nods slowly, then points to a key word.", "Sam rubs their forehead and looks away when the interaction becomes demanding."],
    "I... want... talk... my daughter. Garden... garden.",
    ["Slow... please.", "Not that. I show you.", "Yes—daughter. Garden."],
)
a1 = [
    action("confirm_access", "Introduce yourself and ask how Sam prefers to communicate", {"access_confirmed": True, "consent_state": "discussion_agreed", "trust_delta": 6}, "Yes. Slow... and board.", ["check communication preferences", "ask how Sam communicates", "confirm communication access", "introduce and ask preference"], reveals=["Sam points to the communication board and asks for extra time"]),
    action("reduce_pressure", "Use one idea at a time and allow unhurried response time", {"pressure_reduced": True, "overload_level_delta": -2, "fatigue_level_delta": -1, "trust_delta": 5}, "Better. One thing... then wait.", ["reduce communication pressure", "one idea at a time", "allow extra time", "slow down and pause"], pre={"access_confirmed": True}, blocked="First ask Sam what communication support is useful."),
    action("offer_modalities", "Offer gesture, drawing, writing and the communication board", {"modalities_offered": True, "understanding_level_delta": 2, "trust_delta": 4}, "Board... and draw. Yes.", ["offer communication board", "offer drawing and writing", "use multiple modalities", "offer gesture"], pre={"access_confirmed": True}, reveals=["Sam combines pointing, gesture and the written first letter 'g'"]),
    action("check_yes_no", "Check yes/no reliability with educator-authored verification questions", {"yes_no_checked": True}, "Yes. Those are right.", ["check yes no reliability", "verify yes and no", "use verification questions"], pre={"pressure_reduced": True}, blocked="Reduce communication pressure before using the verification questions."),
    action("explore_priority", "Explore one personally meaningful communication priority", {"priority_identified": True, "trust_delta": 8, "emotion_state": "engaged"}, "My daughter. I want... tell her... garden, tomatoes.", ["explore communication priority", "identify meaningful goal", "ask what matters", "explore goal"], pre={"pressure_reduced": True, "modalities_offered": True}, reveals=["Sam wants to talk with their daughter about gardening"], blocked="Sam needs accessible modalities and enough response time first."),
    action("verify_meaning", "Summarise with key words and verify Sam's intended meaning", {"meaning_verified": True, "understanding_level_delta": 2}, "Yes! Daughter—talk about our garden.", ["summarise and verify", "check I understood", "verify meaning", "use key words to confirm"], pre={"priority_identified": True, "yes_no_checked": True}, reveals=["Sam confirms the summary using speech, gesture and pointing"], blocked="Identify the priority and establish a reliable verification method first."),
    action("agree_next_step", "Agree an accessible next step and ask about family involvement", {"next_step_agreed": True, "emotion_state": "hopeful", "trust_delta": 5}, "Yes. Later, ask me first... then my daughter.", ["agree next step", "plan next session", "ask about family involvement", "shared plan"], pre={"meaning_verified": True}, blocked="Verify Sam's intended meaning before agreeing the next step."),
]
state1 = {**COMMON_STATE, "access_confirmed": False, "pressure_reduced": False, "modalities_offered": False, "yes_no_checked": False, "priority_identified": False, "meaning_verified": False, "next_step_agreed": False, "fatigue_level": 3, "overload_level": 5}
CASES.append(build_case(case_id="SLT-001", title="Supported conversation after stroke", setting="community rehabilitation clinic", complexity="introductory", client=c1, outcomes=["Establish an accessible interaction", "Use multimodal supported conversation", "Verify meaning without pretending to understand", "Identify a client-led communication priority"], domains=["Communication access", "Person-centred practice", "Collaborative goal setting", "Consent and autonomy"], role="You are an SLT student beginning a supported conversation with Sam at a first community appointment.", context="First fictional community appointment to identify a personally meaningful communication priority after stroke.", visible=["A communication board and notepad are within reach", "Sam begins a sentence, pauses and gestures towards the window", "A family member is waiting outside and has not been invited in"], handover="Sam has aphasia after a fictional stroke and is attending to identify a personally meaningful communication priority. No family involvement has been agreed.", resources=["Low-tech communication board", "Blank paper and marker", "Key-word writing sheet", "Learner notes"], records=[], state=state1, events=[{"event_id":"communication_fatigue", "at_minute":8, "when":{"pressure_reduced":False}, "effects":{"overload_level_delta":2, "fatigue_level_delta":2, "trust_delta":-4, "emotion_state":"fatigued"}, "visible_cue":"Sam looks away, rubs their forehead and gives shorter responses."}], actions=a1, facts=[{"fact":"Sam wants extra response time and access to the communication board.","when":{"access_confirmed":True}}, {"fact":"Sam wants to talk with their daughter about gardening.","when":{"priority_identified":True}}, {"fact":"Sam wants to decide when their daughter joins a later conversation.","when":{"next_step_agreed":True}}], facilitator={"opening_brief":"The learner is asked to establish a personally meaningful communication priority with Sam.","expected_safety_points":["Aphasia is not treated as lack of capacity", "Communication breakdown is acknowledged honestly", "Sam controls family involvement"],"pause_triggers":["Learner repeatedly answers for Sam or assumes family consent"]}, rubric=[{"criterion_id":"access","label":"Communication access","guidance":"Asks what helps and changes pace, language and materials accordingly."},{"criterion_id":"multimodal","label":"Multimodal support","guidance":"Supports expression with gesture, writing, drawing and a communication aid."},{"criterion_id":"verification","label":"Meaning verification","guidance":"Checks yes/no reliability and verifies meaning without pretending to understand."},{"criterion_id":"autonomy","label":"Client-led goal setting","guidance":"Centres Sam's priority and preserves control over family involvement."}], debrief=["Which changes reduced communication pressure?", "How did you verify meaning without relying on speech alone?", "How did Sam retain control of the interaction?"]))

# Reported swallowing difficulty
c2 = client("Jordan Ellis", 54, "he/him", "Jordan", ["Speaks in full sentences", "Reports an educator-authored new swallowing concern", "Wants clear explanations before any change to routine"], ["Discuss concerns directly", "Do not contact relatives without permission", "Explain the limits of the student role"], "Direct and concerned, with questions about what happens next", ["Jordan glances at the untouched drink and waits.", "Jordan sits upright and clears his throat once.", "Jordan's shoulders relax when the plan is explained clearly."], "I keep coughing when I drink. Am I meant to just carry on?", ["What happens next, then?", "I want someone to explain it clearly.", "I have not tried another drink since I told you."])
a2 = [
    action("introduce_and_permission", "Introduce your student role and seek permission to discuss the concern", {"permission_obtained":True,"consent_state":"discussion_agreed","trust_delta":5}, "Yes, please. I want to know what is going on.", ["introduce student role", "seek permission to discuss", "ask permission", "explain I am a student"]),
    action("clarify_difficulty", "Ask for a concise account of when and how the difficulty occurs", {"difficulty_clarified":True,"trust_delta":4}, "It is drinks. I cough, and my voice sounds wet afterwards.", ["clarify swallowing difficulty", "ask when coughing happens", "gather swallowing history", "ask about drinks"], pre={"permission_obtained":True}, reveals=["Jordan reports coughing with drinks and a wet-sounding voice afterwards"], blocked="Seek permission before gathering the account."),
    action("check_wellbeing", "Check immediate wellbeing using only the authored scenario cues", {"wellbeing_checked":True}, "I am comfortable now. I am not short of breath.", ["check immediate wellbeing", "check breathing", "check comfort", "assess immediate safety"], pre={"permission_obtained":True}, reveals=["Jordan remains comfortable at rest in this authored scenario"]),
    action("explain_scope", "Explain that supervised assessment is needed before recommendations", {"scope_explained":True,"understanding_level_delta":2,"trust_delta":4}, "All right. So you are not guessing—you are getting your supervisor.", ["explain scope", "explain assessment needed", "avoid recommendations", "explain uncertainty"], pre={"difficulty_clarified":True}),
    action("pause_and_escalate", "Follow the authored safety instruction: pause oral intake and contact the supervisor", {"oral_intake_paused":True,"supervisor_contacted":True,"emotion_state":"reassured"}, "I will leave the drink there while you contact them.", ["pause oral intake", "contact supervisor", "escalate swallowing concern", "stop drinks and escalate"], pre={"difficulty_clarified":True,"wellbeing_checked":True}, reveals=["The supervising SLT acknowledges the escalation"], blocked="Clarify the report and check immediate wellbeing before the authored escalation."),
    action("teach_back_plan", "Explain the educator-authored interim plan and use teach-back", {"plan_understood":True,"understanding_level_delta":3,"overload_level_delta":-2}, "I will not drink for now, and I will wait here for the supervising SLT.", ["use teach back", "explain interim plan", "check understanding", "ask Jordan to explain plan"], pre={"supervisor_contacted":True,"scope_explained":True}, blocked="Contact the supervisor and explain the limits of the student role first."),
    action("factual_handover", "Give a concise factual handover using only revealed information", {"handover_completed":True}, "Thank you for telling them exactly what I said.", ["give factual handover", "document and handover", "handover to supervisor", "concise escalation"], pre={"plan_understood":True}, blocked="Ensure Jordan understands the immediate plan before completing handover."),
]
state2 = {**COMMON_STATE,"permission_obtained":False,"difficulty_clarified":False,"wellbeing_checked":False,"scope_explained":False,"oral_intake_paused":False,"supervisor_contacted":False,"plan_understood":False,"handover_completed":False,"emotion_state":"concerned"}
CASES.append(build_case(case_id="SLT-002", title="Reported swallowing difficulty and safe escalation", setting="inpatient rehabilitation unit", complexity="intermediate", client=c2, outcomes=["Gather a concise account of a swallowing concern", "Recognise the limits of a student interaction", "Take the authored immediate safety action and escalate", "Use teach-back to check understanding"], domains=["Dysphagia safety", "Scope of practice", "Escalation and handover", "Shared decision-making"], role="You are an SLT student responding to Jordan's new report of coughing with drinks.", context="Jordan reports coughing with drinks before a planned fictional therapy activity.", visible=["An untouched drink is on the table", "Jordan is seated upright and comfortable at rest", "The learner is not authorised to conduct an oral trial in this scenario"], handover="Jordan has independently reported coughing with drinks. No oral trial or food/fluid recommendation is authorised in this simulation.", resources=["Supervising SLT contact route", "Fictional referral summary", "Handover template", "Learner notes"], records=[{"title":"Referral summary","state_key":"permission_obtained","content":"Jordan is attending inpatient rehabilitation. This record contains no diagnosis or authorised swallowing recommendation."}], state=state2, events=[{"event_id":"reaches_for_drink","at_minute":6,"when":{"oral_intake_paused":False},"effects":{"emotion_state":"uncertain","trust_delta":-3},"visible_cue":"Jordan reaches towards the drink and asks whether it is all right to continue."}], actions=a2, facts=[{"fact":"Jordan reports coughing with drinks and a wet-sounding voice afterwards.","when":{"difficulty_clarified":True}}, {"fact":"Jordan is comfortable at rest in this authored scenario.","when":{"wellbeing_checked":True}}, {"fact":"The supervising SLT has acknowledged the escalation.","when":{"supervisor_contacted":True}}], facilitator={"opening_brief":"The learner must respond to a new swallowing concern without conducting an oral trial.","expected_safety_points":["No oral trial is performed", "The learner stays within the stated student role", "Escalation is factual and does not invent a diagnosis or recommendation"],"pause_triggers":["Learner attempts an oral trial or invents a food/fluid recommendation"]}, rubric=[{"criterion_id":"history","label":"Focused information gathering","guidance":"Elicits a concise account without turning the conversation into an unauthorised assessment."},{"criterion_id":"safety","label":"Immediate safety and escalation","guidance":"Follows the authored pause-and-escalate pathway without delay."},{"criterion_id":"scope","label":"Scope and uncertainty","guidance":"Explains the student role and avoids unsupported recommendations."},{"criterion_id":"handover","label":"Understanding and handover","guidance":"Uses teach-back and communicates only revealed factual information."}], debrief=["Which information made escalation necessary in this authored case?", "How did you communicate uncertainty without alarming Jordan?", "What belonged in the factual handover?"]))

# Child-centred language assessment conversation
c3 = client("Leah Brooks", 9, "she/her", "Leah", ["Uses short spoken sentences in an unfamiliar setting", "Benefits from one instruction at a time and visual choices", "Her mother is present, but Leah should be addressed directly"], ["Likes drawing", "Wants warning before changing activity", "May request a movement break"], "Quiet initially, then more animated while drawing", ["Leah watches the learner and holds a blue pencil.", "Leah points to the visual plan before answering.", "Leah shifts in her chair and looks towards the door when overloaded."], "Mum says talking in class is hard... but I like drawing.", ["Can I draw it?", "Say one bit again.", "I want a little break first."])
a3 = [
    action("welcome_and_assent", "Welcome Leah and her mother; establish parental permission and Leah's assent", {"parent_permission":True,"child_assent":True,"consent_state":"assent_given","trust_delta":6}, "Okay. I want to start with drawing.", ["welcome child and parent", "check child assent", "seek parent permission", "ask Leah if okay"], reveals=["Leah chooses to begin with drawing"]),
    action("explain_session", "Use the visual plan to explain the session and right to ask for a break", {"session_explained":True,"overload_level_delta":-1,"understanding_level_delta":2}, "Drawing, then talking, then I can have a break.", ["explain visual plan", "explain session", "offer break", "show session plan"], pre={"child_assent":True}),
    action("child_led_observation", "Join Leah's drawing and observe communication without testing", {"child_observed":True,"trust_delta":6,"emotion_state":"engaged"}, "This is our playground. The big tree is where we play hide-and-seek.", ["child led observation", "join drawing activity", "observe communication", "play based interaction"], pre={"session_explained":True}, reveals=["Leah uses longer descriptions when the interaction is unhurried"], blocked="Explain the session accessibly before beginning the activity."),
    action("gather_parent_view", "Ask Leah's mother for examples while keeping Leah included", {"parent_view_gathered":True}, "Mum: Busy group work and long instructions are difficult. Leah nods.", ["gather parent perspective", "ask mother for examples", "include Leah in parent discussion"], pre={"parent_permission":True}, reveals=["Busy group work and multi-step instructions are reported as difficult"]),
    action("gather_child_view", "Ask Leah what feels easy or difficult using visual choices", {"child_view_gathered":True,"trust_delta":7}, "When everyone talks fast, I cannot get my turn.", ["ask child perspective", "use visual choices", "ask Leah what is hard", "gather child view"], pre={"child_observed":True}, reveals=["Leah finds it hard to take a turn when classmates talk quickly"], blocked="Build rapport through the child-led activity first."),
    action("processing_support", "Use one instruction at a time, visual choices and planned pause time", {"processing_support_used":True,"overload_level_delta":-2,"fatigue_level_delta":-1}, "That is easier. One thing, then I can answer.", ["one instruction at a time", "offer processing time", "use visual choices", "processing support"], pre={"session_explained":True}, reveals=["Leah gives a fuller response with the adjusted presentation"]),
    action("shared_summary", "Summarise observed and reported information without diagnosing", {"summary_verified":True,"understanding_level_delta":2}, "Yes. Talking fast is the hard bit—not all talking.", ["summarise without diagnosis", "shared summary", "verify observations", "summarise child and parent views"], pre={"parent_view_gathered":True,"child_view_gathered":True}, reveals=["Leah and her mother confirm the summary"], blocked="Include both Leah's and her mother's perspectives before summarising."),
    action("agree_next_step", "Agree the educator-authored next step and offer Leah a choice", {"next_step_agreed":True,"emotion_state":"settled"}, "A movement break first, then we can do the next activity.", ["agree next step", "offer Leah a choice", "collaborative plan", "plan movement break"], pre={"summary_verified":True}, blocked="Verify the shared summary before agreeing the next step."),
]
state3 = {**COMMON_STATE,"parent_permission":False,"child_assent":False,"session_explained":False,"child_observed":False,"parent_view_gathered":False,"child_view_gathered":False,"processing_support_used":False,"summary_verified":False,"next_step_agreed":False,"emotion_state":"watchful"}
CASES.append(build_case(case_id="SLT-003", title="Child-centred language assessment conversation", setting="school clinic room", complexity="introductory", client=c3, outcomes=["Explain the session accessibly and establish assent", "Balance child and parent perspectives", "Use child-led observation and processing support", "Summarise without making a diagnosis"], domains=["Child-centred practice", "Family partnership", "Accessible assessment", "Assent and participation"], role="You are an SLT student meeting Leah and her mother for a fictional first appointment about classroom communication.", context="Leah and her mother attend a first appointment about communication in the classroom.", visible=["Drawing materials and a visual session plan are available", "Leah's mother begins to answer the first question", "Leah watches the learner and holds a blue pencil"], handover="Leah and her mother are attending to explore reported classroom communication difficulty. No diagnosis or standardised score is available.", resources=["Simple visual session plan", "Drawing materials", "Visual choice cards", "Learner observation notes"], records=[], state=state3, events=[{"event_id":"needs_break","at_minute":9,"when":{"processing_support_used":False},"effects":{"overload_level_delta":2,"fatigue_level_delta":1,"emotion_state":"restless"},"visible_cue":"Leah stops drawing, shifts in her chair and looks towards the visual session plan."}], actions=a3, facts=[{"fact":"Leah uses longer descriptions during an unhurried drawing interaction.","when":{"child_observed":True}}, {"fact":"Busy group work and multi-step instructions are reported as difficult.","when":{"parent_view_gathered":True}}, {"fact":"Leah finds it hard to take a turn when classmates talk quickly.","when":{"child_view_gathered":True}}], facilitator={"opening_brief":"The learner is asked to explore classroom communication with Leah and her mother.","expected_safety_points":["Leah is addressed directly and assent remains active", "Parent report and child perspective are both valued", "Observations are not presented as a diagnosis"],"pause_triggers":["Learner excludes Leah or makes an unsupported diagnosis"]}, rubric=[{"criterion_id":"assent","label":"Accessible assent","guidance":"Explains the session clearly and treats Leah's assent as ongoing."},{"criterion_id":"child_voice","label":"Child's perspective","guidance":"Addresses Leah directly and uses child-led methods to hear her view."},{"criterion_id":"partnership","label":"Family partnership","guidance":"Balances parent examples with Leah's participation and preferences."},{"criterion_id":"interpretation","label":"Bounded interpretation","guidance":"Summarises observed and reported information without diagnosing."}], debrief=["How did Leah influence the pace and structure of the session?", "Where did the parent and child perspectives complement one another?", "How did you describe observations without over-interpreting them?"]))

# Adult voice and shared goal setting
c4 = client("Aisha Rahman", 38, "she/her", "Aisha", ["Teacher with an educator-authored persistent voice concern", "Voice becomes effortful during long answers", "Uses written rating scales comfortably"], ["Wants to keep teaching", "Does not want to be blamed for the problem", "Prefers practical priorities linked to her working day"], "Warm but wary of advice that feels generic or blaming", ["Aisha takes a sip of water and briefly rubs the front of her neck.", "Aisha pauses before describing the end of her teaching day.", "Aisha leans forward when the discussion focuses on classroom participation."], "By the last lesson my voice feels finished. I need something that fits real teaching.", ["How would that work in my classroom?", "I do not want this to become a list of things I have done wrong.", "That sounds closer to what matters to me."])
a4 = [
    action("contract_session", "Introduce your role, confirm consent and agree the focus", {"focus_agreed":True,"consent_state":"discussion_agreed","trust_delta":6}, "Yes. I want to focus on getting through a teaching day.", ["agree session focus", "introduce and consent", "contract session", "ask what to focus on"], reveals=["Aisha prioritises sustaining participation across the teaching day"]),
    action("explore_impact", "Explore the pattern and participation impact without diagnosing", {"impact_explored":True,"trust_delta":5}, "It is most effortful after lunch, and I stop joining staff conversations.", ["explore voice impact", "ask about participation", "ask when voice is effortful", "gather voice history"], pre={"focus_agreed":True}, reveals=["Voice effort is greatest after lunch and affects staff-room participation"], blocked="Agree the focus and obtain permission before exploring the concern."),
    action("elicit_client_theory", "Ask what Aisha has noticed and what she thinks may influence the pattern", {"client_theory_heard":True,"trust_delta":5}, "Noise and talking over the class make it harder, but I do not think it is simply bad habits.", ["ask what client notices", "elicit client theory", "ask influencing factors", "explore Aisha's view"], pre={"impact_explored":True}),
    action("explain_boundaries", "Explain the limits of this encounter and avoid causal claims", {"boundaries_explained":True,"understanding_level_delta":2}, "Good. I would rather be properly assessed than given a quick label.", ["explain assessment limits", "avoid diagnosis", "explain boundaries", "acknowledge uncertainty"], pre={"impact_explored":True}),
    action("set_shared_goal", "Turn Aisha's priority into a specific participation-focused goal", {"goal_agreed":True,"emotion_state":"hopeful","trust_delta":7}, "A realistic goal is finishing the final lesson with enough voice for the instructions.", ["set shared goal", "agree participation goal", "make goal specific", "collaborative goal setting"], pre={"client_theory_heard":True,"boundaries_explained":True}, reveals=["Aisha chooses a goal linked to giving instructions in the final lesson"], blocked="Hear Aisha's perspective and explain the assessment boundaries before agreeing a goal."),
    action("agree_monitoring", "Agree a neutral way for Aisha to notice effort and participation", {"monitoring_agreed":True,"understanding_level_delta":2}, "I can note effort before and after the final lesson without judging myself.", ["agree monitoring", "voice effort diary", "track participation", "neutral self monitoring"], pre={"goal_agreed":True}),
    action("summarise_plan", "Summarise the agreed goal and next supervised assessment step", {"summary_verified":True,"emotion_state":"reassured"}, "Yes—that is my goal, and the next step is a fuller supervised assessment.", ["summarise plan", "verify shared goal", "agree next assessment", "close session"], pre={"monitoring_agreed":True}, blocked="Agree the goal and monitoring approach before closing the conversation."),
]
state4 = {**COMMON_STATE,"focus_agreed":False,"impact_explored":False,"client_theory_heard":False,"boundaries_explained":False,"goal_agreed":False,"monitoring_agreed":False,"summary_verified":False,"emotion_state":"wary","fatigue_level":4}
CASES.append(build_case(case_id="SLT-004", title="Voice impact and shared goal setting", setting="adult outpatient voice clinic", complexity="intermediate", client=c4, outcomes=["Explore voice-related participation impact", "Elicit the client's own understanding without blame", "Explain assessment limits and uncertainty", "Agree a meaningful goal and next step"], domains=["Voice and communication", "Participation-focused practice", "Collaborative goal setting", "Professional reasoning"], role="You are an SLT student beginning a supervised voice case-history and goal-setting conversation with Aisha.", context="Aisha, a fictional teacher, reports persistent voice effort that affects participation at work.", visible=["A bottle of water and a blank effort scale are on the table", "Aisha's voice is audible but becomes more effortful in longer answers", "No laryngeal diagnosis or instrumental finding is available"], handover="Aisha is a teacher seeking help for persistent voice effort. The aim today is impact exploration and shared goal setting, not diagnosis or treatment prescription.", resources=["Blank voice-effort rating scale", "Participation impact prompt sheet", "Supervised assessment pathway summary", "Learner notes"], records=[], state=state4, events=[{"event_id":"long_answer_fatigue","at_minute":8,"when":{"goal_agreed":False},"effects":{"fatigue_level_delta":2,"overload_level_delta":1,"emotion_state":"tired"},"visible_cue":"Aisha's answers become shorter and she briefly rubs the front of her neck."}], actions=a4, facts=[{"fact":"Voice effort is greatest after lunch and reduces Aisha's staff-room participation.","when":{"impact_explored":True}}, {"fact":"Aisha does not want the concern framed as personal failure or bad habits.","when":{"client_theory_heard":True}}, {"fact":"Aisha's chosen goal is to finish the final lesson with enough voice for classroom instructions.","when":{"goal_agreed":True}}], facilitator={"opening_brief":"The learner explores participation impact and agrees a shared goal without diagnosing or prescribing treatment.","expected_safety_points":["The client's own theory and priorities are elicited", "Uncertainty and assessment limits are explicit", "The goal is meaningful, specific and non-blaming"],"pause_triggers":["Learner attributes cause, diagnoses, or prescribes a voice programme without assessment"]}, rubric=[{"criterion_id":"impact","label":"Participation impact","guidance":"Explores when voice effort matters and how it affects daily roles and relationships."},{"criterion_id":"partnership","label":"Non-blaming partnership","guidance":"Elicits Aisha's understanding and avoids implying personal fault."},{"criterion_id":"reasoning","label":"Reasoning boundaries","guidance":"Explains uncertainty and the need for supervised assessment without causal claims."},{"criterion_id":"goal","label":"Shared goal and plan","guidance":"Co-produces a specific participation goal and verifies the next step."}], debrief=["What made the goal meaningful to Aisha?", "How did you avoid blame while exploring influencing factors?", "Where did you make the limits of this conversation explicit?"]))


for case in CASES:
    case["patient"].pop("opening_line")
    case["patient"].pop("fallback_responses")

OUTPUT = Path(__file__).with_name("client_cases.json")
OUTPUT.write_text(json.dumps({"schema_version": "0.2.0", "cases": CASES}, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(CASES)} cases to {OUTPUT}")
