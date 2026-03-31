import re
import textwrap

from openai import OpenAI


openai_client = OpenAI()


def _fallback_header(text: str) -> str:
    """Create a compact deterministic fallback header if LLM call fails."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return "Academic Document"
    return f"Academic Document Summary: {cleaned[:220]}"


def create_header(text: str, llm_client=None, model: str = "gpt-4o-mini", max_tokens: int = 300, retries: int = 2) -> str:
    prompt = textwrap.dedent(
        f"""
        Create one concise factual header for this academic document.
        Requirements:
        - 1 short paragraph, no bullets
        - Include key identifiers (course code, department, school, policy/program names) when present
        - No personal pronouns
        - Max 200 words

        Document start:
        ---
        {text}
        ---
        """
    )

    client = llm_client or openai_client
    for attempt in range(1, retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.2,
            )
            content = completion.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception as e:
            print(f"Header generation attempt {attempt}/{retries} failed: {e}")

    return _fallback_header(text)
