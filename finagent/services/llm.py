import json

from finagent.core.config import get_settings


class NarrativeService:
    """OpenAI Responses API adapter with a deterministic no-key fallback."""

    def __init__(self):
        self.settings = get_settings()

    def synthesize(self, ticker: str, evidence: list[dict], fallback: str) -> str:
        if not self.settings.openai_api_key:
            return fallback
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.responses.create(
            model=self.settings.openai_model,
            instructions=(
                "You are an institutional equity research analyst. Use only supplied evidence. "
                "State uncertainty, distinguish facts from inference, and never promise returns."
            ),
            input=f"Ticker: {ticker}\nEvidence: {json.dumps(evidence, default=str)}\nWrite a concise investment thesis.",
        )
        return response.output_text
