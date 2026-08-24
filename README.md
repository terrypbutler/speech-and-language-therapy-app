# Speech and Language Therapy Simulation Studio

An unofficial Plymouth Marjon concept prototype for supervised SLT education
using entirely fictional clients and deterministic, educator-authored scenarios.

## Run locally

```powershell
py -m pip install -r requirements.txt
py -m streamlit run slt_app.py
```

## Validate and test

```powershell
py .\sample_slt_clients\validate_cases.py
py -m unittest discover -s tests -v
```

## Included cases

- Supported conversation after a fictional stroke
- Reported swallowing difficulty and safe escalation
- Child-centred language assessment conversation

This is not clinical guidance, an approved curriculum or a competence-assessment
system. Marjon SLT educators and relevant placement, dysphagia, safeguarding,
accessibility and information-governance leads must review it before teaching use.
