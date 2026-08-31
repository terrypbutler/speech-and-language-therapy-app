# Speech and Language Therapy Simulation Studio

This app is the Speech and Language Therapy adaptation of the latest Nurse Simulation Studio architecture (source version `308db39`, 30 August 2026).

It supports supervised, formative rehearsal with entirely fictional clients. Communication, participation, consent, assent, safety and scenario consequences are deterministic and educator-authored. OpenAI is the primary optional AI provider, with Gemini available as an alternative. AI may interpret learner wording and phrase a bounded client response; it cannot create assessment findings, diagnoses, recommendations, consent or competence decisions.

## Run locally

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

The compatibility entry point `slt_app.py` also opens the current Studio.

## Included fictional cases

- Supported conversation after stroke
- Reported swallowing difficulty and safe escalation
- Child-centred language assessment conversation
- Voice impact and shared goal setting

Each case includes a learner prebrief, SLT workspace, deterministic pathway, client dialogue, time-based cues, educator rubric, structured debrief and learner-safe export.

## Optional AI interactions

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add an `OPENAI_API_KEY`, a `GEMINI_API_KEY`, or both. Without a configured key, the Studio uses authored action matching, replies and non-verbal cues.

OpenAI requests use the Responses API with structured JSON outputs and `store=False`. Never enter identifiable client information.

## Test

```powershell
py -m unittest discover -s tests -v
py .\sample_slt_clients\validate_cases.py
```

## External scenario library

An optional published library can be configured with:

```toml
SCENARIO_LIBRARY_URL = "https://example.org/slt-scenario-library/library.json"
```

The Studio accepts HTTPS JSON only, limits its size, validates every scenario and falls back to its bundled development cases if the external library is unavailable or unsafe.

For one-click publishing from the password-protected scenario editor, configure `SCENARIO_EDITOR_PASSWORD`, `SCENARIO_GITHUB_REPOSITORY`, `SCENARIO_GITHUB_BRANCH`, `SCENARIO_GITHUB_DIRECTORY` and a fine-grained `SCENARIO_GITHUB_TOKEN` with repository contents write access. Never commit real secrets.

## Educational review before use

All bundled cases remain development fixtures. Before learner use, review them with SLT educators, relevant clinical specialists, people with lived experience, accessibility and inclusion reviewers, simulation leads and information-governance leads. Local policy, referral routes and escalation procedures must replace generic placeholders.
