
#!/usr/bin/env python3
"""
image_prompt.py
----------------
Send an image + a text prompt to an OpenAI vision model and print the answer.

Usage (CLI):
    python image_prompt.py --image path/to/picture.jpg --prompt "What is shown?"
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Union

import openai

# ----------------------------------------------------------------------
# Load the OpenAI API key (from env var or .env file)
# ----------------------------------------------------------------------
def _load_api_key() -> str:
    """Return the OpenAI API key from the environment."""
    # Try loading a .env file if python‑dotenv is installed
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass  # .env not required

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OpenAI API key not found. Set the OPENAI_API_KEY environment variable "
            "or place it in a .env file."
        )
    return key


# ----------------------------------------------------------------------
# Core function – send image + prompt to the model
# ----------------------------------------------------------------------
def get_image_response(
    image_path: Union[str, Path],
    user_prompt: str,
    model: str = "GPT‑4 Turbo Vision",          # or "gpt-4-vision-preview"
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """
    Calls the OpenAI vision endpoint and returns the raw response dict.

    Parameters
    ----------
    image_path : str or Path
        Local path to the image file.
    user_prompt : str
        The textual question / instruction for the model.
    model : str, optional
        Model name (default: gpt-4o-mini).
    temperature : float, optional
        Sampling temperature (default: 0.7).
    max_tokens : int, optional
        Maximum tokens for the answer (default: 1024).

    Returns
    -------
    dict
        Full JSON response from the API.
    """
    # ---- 1️⃣ Load & base64‑encode the image ----
    img_path = Path(image_path).expanduser().resolve()
    if not img_path.is_file():
        raise FileNotFoundError(f"Image not found: {img_path}")

    with img_path.open("rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # ---- 2️⃣ Build the message payload ----
    system_msg = {
        "role": "system",
        "content": "You are a helpful assistant that can understand images and answer questions about them.",
    }

    user_msg = {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}"
                },
            },
            {"type": "text", "text": user_prompt},
        ],
    }

    # ---- 3️⃣ Call the OpenAI API ----
    client = openai.OpenAI(api_key=_load_api_key())

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[system_msg, user_msg],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except openai.OpenAIError as exc:
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    return response.dict()


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send an image and a text prompt to an OpenAI vision model."
    )
    parser.add_argument(
        "-i",
        "--image",
        required=True,
        help="Path to the image file (e.g., ./cat.jpg).",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        required=True,
        help="Text prompt describing what you want to know about the image.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="gpt-4o-mini",
        choices=["gpt-4o-mini", "gpt-4-vision-preview"],
        help="OpenAI model to use (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens in the answer (default: 1024).",
    )
    args = parser.parse_args()

    try:
        resp = get_image_response(
            image_path=args.image,
            user_prompt=args.prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract the assistant's textual reply (first choice)
    try:
        answer = resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        answer = json.dumps(resp, indent=2)  # fallback: dump whole response

    print("\n=== Model response ===\n")
    print(answer)


if __name__ == "__main__":
    main()
