"""Provider-neutral adapter derived from the Butler Academy API module."""

from dataclasses import dataclass


GEMINI_PROVIDER = "Gemini"
OPENAI_PROVIDER = "OpenAI"
PROVIDER_OPTION_KEY = "ai_provider_option"
DIALOGUE_MODEL = "client-dialogue"
AUTHORING_MODEL = "scenario-authoring"
GEMINI_DIALOGUE_MODEL = "gemini-3.5-flash-lite"
OPENAI_DIALOGUE_MODEL = "gpt-5.6-terra"

_provider = OPENAI_PROVIDER
_gemini_client = None
_openai_client = None


@dataclass
class ModelResponse:
    text: str

    @property
    def parts(self):
        return [self.text] if self.text else []


def selected_provider() -> str:
    import streamlit as st

    selected = st.session_state.get(PROVIDER_OPTION_KEY, OPENAI_PROVIDER)
    return selected if selected in {GEMINI_PROVIDER, OPENAI_PROVIDER} else OPENAI_PROVIDER


def provider_name() -> str:
    return _provider


def render_provider_options() -> str:
    import streamlit as st

    return st.radio(
        "AI provider",
        [OPENAI_PROVIDER, GEMINI_PROVIDER],
        horizontal=True,
        key=PROVIDER_OPTION_KEY,
        help=(
            "Supports learner interactions, synthetic-client replies and educator-led "
            "scenario drafting. Authored scenario state remains deterministic."
        ),
    )


def configure(provider: str, api_key: str) -> None:
    """Configure one provider without persisting or displaying its API key."""

    global _provider, _gemini_client, _openai_client
    if provider == OPENAI_PROVIDER:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The OpenAI SDK is not installed.") from exc
        _openai_client = OpenAI(api_key=api_key)
    elif provider == GEMINI_PROVIDER:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("The Google Gen AI SDK is not installed.") from exc
        _gemini_client = genai.Client(api_key=api_key)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
    _provider = provider


def configure_selected_provider() -> tuple[bool, str]:
    """Configure the selected provider from Streamlit secrets."""

    from modules.app_secrets import get_secret

    global _provider
    provider = selected_provider()
    _provider = provider
    secret_name = "OPENAI_API_KEY" if provider == OPENAI_PROVIDER else "GEMINI_API_KEY"
    api_key = get_secret(secret_name)
    if not api_key:
        return False, f"Add {secret_name} to .streamlit/secrets.toml to enable AI interactions."
    try:
        configure(provider, api_key)
    except (RuntimeError, ValueError):
        return False, "The selected AI provider could not be configured."
    return True, f"{provider} interaction support is enabled."


class GenerativeModel:
    """Compatibility interface used by the SLT dialogue layer."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate_content(self, contents, generation_config=None):
        if self.model_name not in {DIALOGUE_MODEL, AUTHORING_MODEL}:
            raise ValueError(f"Unsupported model role: {self.model_name}")

        authoring = self.model_name == AUTHORING_MODEL

        if _provider == OPENAI_PROVIDER:
            if _openai_client is None:
                raise RuntimeError("OpenAI has not been configured with an API key.")
            text_config = {"verbosity": "low"}
            if (
                generation_config
                and generation_config.get("response_mime_type") == "application/json"
            ):
                response_schema = generation_config.get("response_schema")
                if response_schema:
                    text_config["format"] = {
                        "type": "json_schema",
                        "name": "slt_interaction_evaluation",
                        "strict": True,
                        "schema": response_schema,
                    }
                else:
                    text_config["format"] = {"type": "json_object"}
            response = _openai_client.responses.create(
                model=OPENAI_DIALOGUE_MODEL,
                input=str(contents),
                reasoning={"effort": "low"},
                text=text_config,
                max_output_tokens=7000 if authoring else 350,
                store=False,
            )
            return ModelResponse(text=response.output_text or "")

        if _gemini_client is None:
            raise RuntimeError("Gemini has not been configured with an API key.")
        return _gemini_client.models.generate_content(
            model=GEMINI_DIALOGUE_MODEL,
            contents=contents,
            config=generation_config,
        )
